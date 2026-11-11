"""Offline protocol/security tests. No credentials or network calls are used."""
import importlib
import json
from pathlib import Path
import ssl
import io
import sys
import types
import unittest
import tempfile
import os
from unittest.mock import patch

ROOT = Path(__file__).parent / 'custom_components' / 'panasonic_home_readonly'
package = types.ModuleType('panasonic_readonly_test')
package.__path__ = [str(ROOT)]
sys.modules[package.__name__] = package
client = importlib.import_module(package.__name__ + '.client')
transport = importlib.import_module(package.__name__ + '.transport')
protocols = importlib.import_module(package.__name__ + '.protocols')
calibration = importlib.import_module(package.__name__ + '.calibration')
purifier_protocol = importlib.import_module(package.__name__ + '.purifier_protocol')

ROWS = [
    {'deviceId': 'AABBCCDDEEFF_0810_75c5pjd', 'params': {
        'devSubTypeId': '75C5PJD', 'deviceMNO': 'F-75C5PJD'}},
    {'deviceId': '112233445566_0900_aircon', 'params': {
        'devSubTypeId': 'AirconCommon-2024-01', 'deviceMNO': 'CS-JM35K410Q'}},
]


class FakeTransport:
    def __init__(self):
        self.calls = []

    def post(self, endpoint, params, ssid=None):
        self.calls.append((endpoint, params, ssid))
        if endpoint == 'UsrGetToken': return {'token': 'fake-challenge'}
        if endpoint == 'UsrLogin':
            return {'usrId': 'fake-user', 'familyId': 1, 'realFamilyId': 1, 'ssId': 'fake-session'}
        if endpoint == 'UsrGetBindDevInfo': return {'devList': ROWS}
        if endpoint == transport.GET: return {'runSta': 1, 'airVo': 2, 'password': 'do-not-expose'}
        if endpoint == transport.AC_GET:
            return {'runStatus': 49, 'runMode': 66, 'setTemperature': 27, 'windSet': 49, 'inhaleTemperature': 128}
        raise AssertionError('Unexpected endpoint')


class ReadonlyTests(unittest.TestCase):
    def test_extended_payload_is_bounded_and_preserves_unrelated_fields(self):
        for change in ({'runM': 0}, {'runM': 3}, {'uvSterilization': 1}, {'runM': 1, 'airVo': 2}):
            payload = purifier_protocol.build_changes(change)
            self.assertTrue(all(v == change.get(k, 255) for k, v in payload.items()))
            self.assertEqual(payload['runSta'], 255)
        for change in ({'runM': 4}, {'runM': True}, {'uvSterilization': 2},
                       {'runM': 0, 'airVo': 2}, {'runSta': 1}, {'runM': 1, 'airVo': 5}):
            with self.assertRaises(ValueError):
                purifier_protocol.build_changes(change)

    def test_complete_status_rejects_stale_basics_and_unknown_mode(self):
        raw = dict(runSta='1', runM='0', airVo='1', nanoe='0', uvSterilization='0')
        live = dict(runSta=1, airVo=1, nanoe=0)
        self.assertEqual(purifier_protocol.full_status(raw, live)['runM'], 0)
        with self.assertRaises(ValueError):
            purifier_protocol.full_status(raw, {**live, 'nanoe': 1})
        with self.assertRaises(ValueError):
            purifier_protocol.full_status({**raw, 'runM': '255'}, live)

    def test_plasma_refuses_noncustom_or_unsynchronized_state_before_set(self):
        adapter = client.Client(FakeTransport())
        adapter.login('test', 'test')
        sends = []
        adapter.transport.set_purifier_extended = lambda *args: sends.append(args)
        for status in ({'runSta': 1}, {'runSta': 0, 'runM': 1, 'uvSterilization': 0},
                       {'runSta': 1, 'runM': 2, 'uvSterilization': 1}):
            adapter.status = lambda device, s=status: s
            with self.assertRaises(transport.CloudError):
                adapter.set_purifier_controls(adapter.devices[0], {'uvSterilization': 0})
        self.assertFalse(sends)

    def test_verified_models_and_category(self):
        rows = ROWS + [{**ROWS[0], 'deviceId': 'AABBCCDDEEFF_0830_75c5pjd'},
                       {**ROWS[1], 'params': {**ROWS[1]['params'], 'deviceMNO': 'unknown'}}]
        self.assertEqual([d.kind for d in client.supported_devices(rows)], ['purifier', 'ac'])

    def test_only_login_discovery_get_and_unscaled_ac(self):
        fake = FakeTransport()
        adapter = client.Client(fake)
        devices = adapter.login('example-user', 'example-password')
        self.assertEqual(adapter.status(devices[0]), {'runSta': 1, 'airVo': 2})
        self.assertEqual(adapter.status(devices[1])['inhaleTemperature'], 128)
        self.assertEqual(adapter.status(devices[1])['runStatus'], 49)
        self.assertTrue(all('Set' not in endpoint for endpoint, _, _ in fake.calls))
        self.assertEqual(fake.calls[-1][1]['usrId'], 'fake-user')

    def test_ac_protocol_does_not_depend_on_display_model(self):
        for model in ('CS-JM35K410Q/CU-JM35K410Q', None):
            row = {**ROWS[1], 'params': {**ROWS[1]['params'], 'deviceMNO': model}}
            devices = client.supported_devices([row])
            self.assertEqual(len(devices), 1)
            self.assertEqual(devices[0].kind, 'ac')
        row = {**ROWS[1], 'params': {**ROWS[1]['params'], 'devSubTypeId': 'different-protocol'}}
        self.assertEqual(client.supported_devices([row]), [])
        row = {**ROWS[1], 'params': {**ROWS[1]['params'], 'devSubTypeId': 'AirconCommon-2024-01-extra'}}
        self.assertEqual(len(client.supported_devices([row])), 1)

    def test_set_endpoint_rejected_before_network(self):
        api = transport.Transport(ROOT / 'panasonic-cloud.pem')
        for endpoint in ['ADevSetStatusNeedsAP', 'ACDevSetStatusInfoAW', 'Unapproved']:
            with self.assertRaises(transport.CloudError):
                api.post(endpoint, {})

    def test_tls_and_no_environment_proxy(self):
        api = transport.Transport(ROOT / 'panasonic-cloud.pem')
        https = next(h for h in api.opener.handlers if isinstance(h, transport.urllib.request.HTTPSHandler))
        self.assertEqual(https._context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(https._context.check_hostname)
        self.assertFalse(https._context.verify_flags & ssl.VERIFY_X509_STRICT)
        self.assertFalse(any(isinstance(h, transport.urllib.request.ProxyHandler) and h.proxies
                             for h in api.opener.handlers))

    def test_redirect_rejected(self):
        with self.assertRaises(transport.CloudError):
            transport.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://elsewhere.invalid')

    def test_failure_hides_private_response(self):
        class Broken:
            def post(self, *args, **kwargs): raise ValueError('example-password fake-session')
        with self.assertRaises(transport.CloudError) as caught:
            client.Client(Broken()).login('example-user', 'example-password')
        self.assertNotIn('example-password', str(caught.exception))
        self.assertIsNone(caught.exception.__cause__)

    def test_unique_ids_do_not_expose_device_id(self):
        device = client.supported_devices(ROWS)[0]
        self.assertNotIn('AABBCC', device.uid)
        self.assertEqual(len(device.uid), 64)
        self.assertEqual(len(client.supported_devices(ROWS + ROWS)), 2)

    def test_only_purifier_switch_control_platform(self):
        manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['requirements'], [])
        self.assertTrue((ROOT / 'switch.py').exists())
        self.assertTrue((ROOT / 'climate.py').exists())
        for platform in ('fan.py', 'button.py'):
            self.assertFalse((ROOT / platform).exists())

    def test_power_payload_only_changes_runsta(self):
        api = transport.Transport(ROOT / 'panasonic-cloud.pem')
        calls = []
        api._request = lambda endpoint, params, ssid: calls.append((endpoint, params))
        for value in (0, 1):
            api.set_purifier_power(ROWS[0]['deviceId'], 'fake-user', 'fake-session', value)
            endpoint, params = calls[-1]
            self.assertEqual(endpoint, 'ADevSetStatusNeedsAP')
            self.assertEqual(params['runSta'], value)
            self.assertTrue(all(params[k] == 255 for k in transport.POWER_SKIP))
            self.assertEqual(len(params), 13)
        before = len(calls)
        for value in (2, True, '0'):
            with self.assertRaises(transport.CloudError):
                api.set_purifier_power(ROWS[0]['deviceId'], 'fake', 'fake', value)
        with self.assertRaises(transport.CloudError):
            api.set_purifier_power(ROWS[1]['deviceId'], 'fake', 'fake', 0)
        self.assertEqual(len(calls), before)

    def test_client_blocks_aircon_control(self):
        api = client.Client(FakeTransport())
        api.login('test', 'test')
        with self.assertRaises(transport.CloudError):
            api.set_power(api.devices[1], 0)

    def test_ac_preserves_controls_without_sensors_or_resets(self):
        baseline = {'runStatus': 49, 'runMode': 66, 'setTemperature': 27, 'windSet': 49,
                    'nanoe': 1, 'inhaleTemperature': 128, 'outsideTemperature': 128,
                    'filterReset': 1, 'alarmCode': '0200', 'token': 'secret'}
        params = protocols.build_ac_params(baseline, {'setTemperature': 26})
        self.assertEqual(params, {'runStatus': 49, 'runMode': 66, 'setTemperature': 26,
                                  'windSet': 49, 'nanoe': 1})

    def test_ac_rejects_old_protocol_and_unsupported_changes(self):
        baseline = {'runStatus': 49, 'runMode': 66, 'setTemperature': 27, 'windSet': 49}
        for change in ({'runStatus': 0}, {'runMode': 3}, {'setTemperature': 52},
                       {'windSet': 10}, {'filterReset': 1}, {'runStatus': True}):
            with self.assertRaises(ValueError): protocols.build_ac_params(baseline, change)
        with self.assertRaises(ValueError):
            protocols.build_ac_params({**baseline, 'runStatus': 1}, {'runStatus': 48})

    def test_ac_request_uses_exact_candidate_endpoint_and_top_identity(self):
        api = transport.Transport(ROOT / 'panasonic-cloud.pem')
        captured = []
        class Opener:
            def open(self, request, timeout):
                captured.append(request)
                return io.BytesIO(b'{"results":{"todoId":1}}')
        api.opener = Opener()
        baseline = {'runStatus': 49, 'runMode': 66, 'setTemperature': 27, 'windSet': 49}
        api.set_ac_controls(ROWS[1]['deviceId'], 'fake', 'fake-session', baseline, {'runStatus': 48})
        self.assertEqual(len(captured), 1)
        request = captured[0]
        self.assertTrue(request.full_url.endswith('/ACDevSetStatusNewProtocol'))
        body = json.loads(request.data)
        self.assertEqual(body['usrId'], 'fake')
        self.assertEqual(body['params']['runStatus'], 48)
        self.assertEqual(body['params']['setTemperature'], 27)
        self.assertNotIn('usrId', body['params'])
        self.assertEqual(request.get_header('Xtoken'), 'SSID=fake-session')

    def test_ac_command_is_not_retried(self):
        api = transport.Transport(ROOT / 'panasonic-cloud.pem')
        attempts = []
        class Broken:
            def open(self, request, timeout):
                attempts.append(request)
                raise OSError('mock failure')
        api.opener = Broken()
        baseline = {'runStatus': 49, 'runMode': 66, 'setTemperature': 27, 'windSet': 49}
        with self.assertRaises(transport.CloudError):
            api.set_ac_controls(ROWS[1]['deviceId'], 'fake', 'fake', baseline, {'runStatus': 48})
        self.assertEqual(len(attempts), 1)

    def test_purifier_aux_control_does_not_change_power(self):
        api = transport.Transport(ROOT / 'panasonic-cloud.pem')
        calls = []
        api._request = lambda endpoint, params, ssid: calls.append(params)
        for field in ('nanoe', 'childLock', 'led', 'lcdSwitch'):
            api.set_purifier_controls(ROWS[0]['deviceId'], 'fake', 'fake', {field: 1})
            params = calls[-1]
            self.assertEqual(params['runSta'], 255)
            self.assertEqual(params[field], 1)
            self.assertTrue(all(params[k] == 255 for k in transport.POWER_SKIP if k != field))
        before = len(calls)
        for change in ({'airVo': 5}, {'nanoe': 1, 'childLock': 1}, {'nanoe': 2}):
            with self.assertRaises(transport.CloudError):
                api.set_purifier_controls(ROWS[0]['deviceId'], 'fake', 'fake', change)
        self.assertEqual(len(calls), before)

    def test_fan_speed_payload_changes_one_field_and_rejects_modes(self):
        api = transport.Transport(ROOT / 'panasonic-cloud.pem')
        calls = []
        api._request = lambda endpoint, params, ssid: calls.append(params)
        for speed in (2, 3, 4):
            api.set_purifier_controls(ROWS[0]['deviceId'], 'fake', 'fake', {'airVo': speed})
            params = calls[-1]
            self.assertEqual(params['airVo'], speed)
            self.assertEqual(params['runSta'], 255)
            self.assertTrue(all(params[k] == 255 for k in transport.POWER_SKIP if k != 'airVo'))
        before = len(calls)
        for speed in (0, 1, 5, 255, True, '2'):
            with self.assertRaises(transport.CloudError):
                api.set_purifier_controls(ROWS[0]['deviceId'], 'fake', 'fake', {'airVo': speed})
        self.assertEqual(len(calls), before)

    def test_fan_speed_requires_fresh_running_custom_baseline(self):
        fake = FakeTransport()
        adapter = client.Client(fake)
        adapter.login('test', 'test')
        sends = []
        fake.set_purifier_controls = lambda *args: sends.append(args[-1])
        for status in ({'runSta': 0, 'airVo': 2}, {'runSta': 1, 'airVo': 1},
                       {'runSta': 1, 'airVo': 5}, {'runSta': 1, 'airVo': '2'}):
            adapter.status = lambda device, s=status: s
            with self.assertRaises(transport.CloudError):
                adapter.set_purifier_controls(adapter.devices[0], {'airVo': 3})
        self.assertFalse(sends)
        adapter.status = lambda device: {'runSta': 1, 'airVo': 2, 'runM': 1}
        adapter.set_purifier_controls(adapter.devices[0], {'airVo': 3})
        self.assertEqual(sends, [{'airVo': 3}])

    def test_aux_control_requires_known_current_state(self):
        api = client.Client(FakeTransport())
        api.login('test', 'test')
        with self.assertRaises(transport.CloudError):
            api.set_purifier_controls(api.devices[0], {'childLock': 1})

    def test_calibration_excludes_credentials_and_identifiers(self):
        data = {'runSta': 1, 'airVo': 2, 'nanoe': 3, 'usrId': 123456, 'deviceId': 98765,
                'familyId': 999, 'token': 123, 'SSID': 456, 'mac': 789,
                'password': 'secret', 'nested': {'secret': 1}, 'name': 'private',
                'bad_float': float('nan'), 'childLock': 0}
        self.assertEqual(calibration.safe_numeric_status(data),
                         {'runSta': 1, 'airVo': 2, 'nanoe': 3, 'childLock': 0})

    def test_calibration_is_opt_in_and_private(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            calibration.write_if_enabled({'runSta': 0}, root)
            self.assertFalse((root / '.panasonic-calibration-safe.json').exists())
            (root / '.panasonic-calibration-enabled').touch()
            calibration.write_if_enabled({'runSta': 0, 'usrId': 123}, root)
            data = json.loads((root / '.panasonic-calibration-safe.json').read_text())
            self.assertEqual(data['status'], {'runSta': 0})
            self.assertIn('sampled_at', data)

    def test_calibration_structure_never_copies_unknown_text_or_identities(self):
        raw = {'usrId': 'secret-account', 'password': 'secret-password',
               'mode': 'private-unknown-text', 'nanoeX': True, 'airVo': '2',
               'description': 'private-description', 'nested': {'mode': 'gentle'},
               'status': {'runMode': 'gentle', 'deviceId': 'private-id',
                          'plasma': 'on', 'data': {'preset': 'custom'}}}
        structure = calibration.safe_structure(raw)
        encoded = json.dumps(structure)
        self.assertNotIn('private', encoded)
        self.assertNotIn('secret', encoded)
        self.assertNotIn('usrId', encoded)
        self.assertNotIn('deviceId', encoded)
        self.assertEqual(structure['mode'], {'type': 'string'})
        self.assertEqual(structure['nested'], {'type': 'object'})
        self.assertEqual(structure['nanoeX']['value'], True)
        self.assertEqual(structure['airVo']['value'], '2')
        self.assertEqual(structure['status']['fields']['runMode']['value'], 'gentle')

    def test_calibration_structure_bounds_protocol_scalars_and_recursion(self):
        for value in ('123456', '256', '-1', 9999, 2.5, float('nan'), ['on']):
            self.assertNotIn('value', calibration.safe_structure({'mode': value})['mode'])
        nested = {'data': {'data': {'data': {'data': {'plasma': 'on'}}}}}
        text = json.dumps(calibration.safe_structure(nested))
        self.assertNotIn('plasma', text)
        self.assertLessEqual(len(calibration.safe_structure({f'field{i}': i for i in range(200)})), 100)

    def test_discovery_diagnostic_is_opt_in_and_sanitizes_json(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / '.panasonic-discovery-safe.json'
            raw = json.dumps({'runMode': 2, 'plasma': 1, 'runM': '3', 'uvSterilization': '0',
                              'usrId': '123', 'token': 'secret', 'numericBad': '99999999999999999999',
                              'description': 'private-data', 'data': {'roomId': 456, 'mode': 'gentle'}})
            calibration.write_discovery_if_enabled(raw, root)
            self.assertFalse(target.exists())
            (root / '.panasonic-discovery-enabled').touch()
            calibration.write_discovery_if_enabled(raw, root)
            result = json.loads(target.read_text())
            self.assertEqual(result['status'], {'runMode': 2, 'plasma': 1, 'runM': 3, 'uvSterilization': 0})
            self.assertNotIn('secret', target.read_text())
            self.assertNotIn('private-data', target.read_text())
            self.assertNotIn('roomId', target.read_text())
            calibration.write_discovery_if_enabled(None, root)
            self.assertEqual(json.loads(target.read_text())['input_type'], 'NoneType')

    def test_discovery_request_consumed_once_and_expired_requests_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            flag = root / '.panasonic-discovery-request'
            self.assertFalse(calibration.consume_discovery_request(root))
            flag.touch()
            self.assertTrue(calibration.consume_discovery_request(root))
            self.assertFalse(flag.exists())
            self.assertFalse(calibration.consume_discovery_request(root))
            flag.touch()
            os.utime(flag, (1, 1))
            self.assertFalse(calibration.consume_discovery_request(root))
            self.assertFalse(flag.exists())

    def test_discovery_refresh_reuses_session_without_auth_or_set(self):
        fake = FakeTransport()
        adapter = client.Client(fake)
        adapter.login('test', 'test')
        fake.calls.clear()
        with patch.object(client, 'consume_discovery_request', side_effect=[True, False]), \
             patch.object(client, 'write_discovery_if_enabled') as writer:
            adapter.status(adapter.devices[0])
            adapter.status(adapter.devices[0])
        self.assertEqual([call[0] for call in fake.calls], [transport.GET, 'UsrGetBindDevInfo', 'UsrGetBindDevInfo', transport.GET, 'UsrGetBindDevInfo'])
        self.assertEqual(writer.call_count, 1)
        self.assertEqual(adapter.session['ssId'], 'fake-session')

    def test_discovery_refresh_failure_never_breaks_regular_status_or_retries(self):
        fake = FakeTransport()
        adapter = client.Client(fake)
        adapter.login('test', 'test')
        fake.calls.clear()
        original = fake.post
        def fail(endpoint, *args):
            if endpoint == 'UsrGetBindDevInfo':
                fake.calls.append((endpoint, {}, None))
                raise RuntimeError('private-error')
            return original(endpoint, *args)
        fake.post = fail
        with patch.object(client, 'consume_discovery_request', side_effect=[True, False]):
            self.assertEqual(adapter.status(adapter.devices[0])['airVo'], 2)
            self.assertEqual(adapter.status(adapter.devices[0])['airVo'], 2)
        self.assertEqual([call[0] for call in fake.calls], [transport.GET, 'UsrGetBindDevInfo', 'UsrGetBindDevInfo', transport.GET, 'UsrGetBindDevInfo'])

    def test_error_details_only_show_safe_metadata(self):
        error = transport.CloudError('private-test-password', stage='UsrLogin', reason='cloud', code='3004')
        self.assertEqual(error.safe_detail, 'UsrLogin / cloud / 3004')
        error = transport.CloudError('secret', stage='private-test-password', code='secret')
        self.assertEqual(error.safe_detail, 'transport / cloud')

    def test_odm_read_probe_one_get_without_auth_retry_or_set(self):
        fake = FakeTransport()
        adapter = client.Client(fake)
        adapter.login('test', 'test')
        fake.calls.clear()
        with patch.object(client, 'consume_odm_request', side_effect=[True, False]), \
             patch.object(client, 'write_odm_probe') as writer:
            self.assertEqual(adapter.status(adapter.devices[0])['airVo'], 2)
            self.assertEqual(adapter.status(adapter.devices[0])['airVo'], 2)
        self.assertEqual([x[0] for x in fake.calls], [transport.GET, transport.ODM_GET, 'UsrGetBindDevInfo', transport.GET, 'UsrGetBindDevInfo'])
        writer.assert_called_once_with(detail='unconfirmed')
        api = transport.Transport(ROOT / 'panasonic-cloud.pem')
        with self.assertRaises(transport.CloudError):
            api.post('ADevSetStatusODM', {})

    def test_odm_probe_result_cannot_leak_error_text_or_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            flag = root / '.panasonic-odm-read-request'
            flag.touch()
            self.assertTrue(calibration.consume_odm_request(root))
            self.assertFalse(calibration.consume_odm_request(root))
            calibration.write_odm_probe({'runM': '2', 'usrId': '123', 'token': 'secret'},
                                        detail='private-password', root=root)
            text = (root / '.panasonic-odm-probe-safe.json').read_text()
            self.assertNotIn('private-password', text)
            self.assertNotIn('secret', text)
            self.assertNotIn('usrId', text)
            self.assertEqual(json.loads(text)['status'], {'runM': 2})


if __name__ == '__main__': unittest.main()
