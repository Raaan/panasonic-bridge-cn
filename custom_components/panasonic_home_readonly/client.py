"""HA client for the locally validated Panasonic transport.

Protocol derived from tools/home_control/panasonic.py and
tools/probe_set_endpoints.py in the handoff project. Explicit controls use
separate target-checked methods; discovery and status polling do not send SET.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from .purifier_protocol import full_status, build_changes
from .fridge_protocol import FRIDGE_SWITCHES

from .transport import AC_GET, GET, ODM_GET, CloudError, Transport, gen_token, md5
from .calibration import (write_if_enabled, write_discovery_if_enabled, consume_discovery_request,
                          consume_odm_request, write_odm_probe)

PURIFIER_FIELDS = ('runSta', 'airVo', 'nanoe', 'pm25C', 'humidityC', 'tempC',
                   'filterRemind', 'filClRemain', 'filExRemain', 'childLock', 'filterTL', 'led', 'lcdSwitch')
AC_FIELDS = ('runStatus', 'runMode', 'setTemperature', 'inhaleTemperature',
             'outsideTemperature', 'windSet', 'muteMode', 'nanoe', 'nanoeG')
FRIDGE_FIELDS = ('PCTempSet', 'PCTempCur', 'FCTempSet', 'FCTempCur',
                 'SCS1TempSet', 'SCS1TempCur')


@dataclass(frozen=True)
class Device:
    device_id: str
    uid: str
    kind: str
    model: str
    name: str


def supported_devices(rows):
    devices = []
    counts = {'purifier': 0, 'ac': 0, 'fridge': 0}
    for row in rows:
        if not isinstance(row, dict):
            continue
        identifier = row.get('deviceId', '')
        params = row.get('params') or {}
        if not isinstance(identifier, str) or not isinstance(params, dict):
            continue
        parts = identifier.split('_')
        if len(parts) != 3 or gen_token(identifier) is None:
            continue
        subtype = str(params.get('devSubTypeId', '')).upper().replace('-', '')
        model = params.get('deviceMNO')
        if parts[1] == '0810' and subtype.startswith('75C5PJD') and model == 'F-75C5PJD':
            kind, label = 'purifier', '松下净化器'
        elif parts[1] == '0900' and subtype.startswith('AIRCONCOMMON202401'):
            # The confirmed GET protocol is identified by category/subtype.
            # deviceMNO is display metadata and may differ from the indoor-unit
            # model on its label. Never use it to infer control enums or scaling.
            model = model if isinstance(model, str) and model else 'AirconCommon-2024-01'
            kind, label = 'ac', '松下空调'
        elif parts[1] == '0100' and subtype == 'FRIDGE19':
            kind, label, model = 'fridge', '松下冰箱', 'Fridge-19'
        else:
            continue
        uid = hashlib.sha256(identifier.encode()).hexdigest()
        if any(d.uid == uid for d in devices):
            continue
        counts[kind] += 1
        devices.append(Device(identifier, uid, kind, model, f'{label} {counts[kind]}'))
    return devices


class Client:
    def __init__(self, transport=None):
        self.transport = transport or Transport(Path(__file__).with_name('panasonic-cloud.pem'))
        self.session = None
        self.devices = []

    def login(self, username, password):
        stage = 'UsrGetToken'
        try:
            token = self.transport.post('UsrGetToken', {'usrId': username})['token']
            derived = md5(md5(md5(password) + username) + token)
            stage = 'UsrLogin'
            self.session = self.transport.post('UsrLogin', {
                'telId': '00:00:00:00:00:00', 'checkFailCount': 0,
                'usrId': username, 'pwd': derived})
            s = self.session
            stage = 'UsrGetBindDevInfo'
            rows = self.transport.post('UsrGetBindDevInfo', {
                'usrId': s['usrId'], 'familyId': s['familyId'],
                'realFamilyId': s['realFamilyId']}, s['ssId']).get('devList', [])
            self.devices = supported_devices(rows)
            for device in self.devices:
                if device.kind == 'purifier':
                    row = next(row for row in rows if isinstance(row, dict) and row.get('deviceId') == device.device_id)
                    try:
                        write_discovery_if_enabled((row.get('params') or {}).get('statusAll'))
                    except (OSError, ValueError):
                        pass  # optional diagnostics never change login/polling
        except CloudError:
            self.session = None
            raise
        except Exception:
            self.session = None
            raise CloudError('登录或设备发现失败；未记录账号、会话或云端响应', stage=stage, reason='response') from None
        return self.devices

    def status(self, device):
        if not self.session:
            raise CloudError('需要在集成中重新登录')
        try:
            endpoint = GET if device.kind == 'purifier' else AC_GET
            identity = {'usrId': self.session['usrId'], 'deviceId': device.device_id,
                        'token': gen_token(device.device_id)}
            raw = (self.transport.get_fridge_status(identity, self.session['ssId'])
                   if device.kind == 'fridge' else
                   self.transport.post(endpoint, identity, self.session['ssId']))
            if device.kind == 'purifier':
                # Disabled by default. This stores only safe numeric fields,
                # never identities, raw responses or credentials.
                try:
                    write_if_enabled(raw)
                except (OSError, ValueError):
                    pass  # diagnostics must never break normal status polling
                try:
                    if consume_discovery_request():
                        s = self.session
                        rows = self.transport.post('UsrGetBindDevInfo', {
                            'usrId': s['usrId'], 'familyId': s['familyId'],
                            'realFamilyId': s['realFamilyId']}, s['ssId']).get('devList', [])
                        row = next((row for row in rows if isinstance(row, dict)
                                    and row.get('deviceId') == device.device_id), {})
                        write_discovery_if_enabled((row.get('params') or {}).get('statusAll'))
                except Exception:
                    pass  # consumed request: never retry, relogin or disrupt polling
                try:
                    if consume_odm_request():
                        try:
                            probe = self.transport.post(ODM_GET, identity, self.session['ssId'])
                            write_odm_probe(probe)
                        except CloudError as error:
                            write_odm_probe(detail=error.safe_detail)
                        except Exception:
                            write_odm_probe(detail='unconfirmed')
                except Exception:
                    pass  # optional single GET never changes normal polling
            fields = (FRIDGE_FIELDS if device.kind == 'fridge' else
                      PURIFIER_FIELDS if device.kind == 'purifier' else AC_FIELDS)
            result = {key: raw[key] for key in fields if type(raw.get(key)) in (int, float)}
            if device.kind == 'fridge':
                result.update({k: raw[k] for k in FRIDGE_SWITCHES if type(raw.get(k)) is int and raw[k] in (0, 1)})
            if device.kind == 'ac' and type(raw.get('elecHeat')) is int and raw['elecHeat'] in (0, 1):
                result['elecHeat'] = raw['elecHeat']
            if device.kind == 'ac':
                result.update({k: raw[k] for k in ('portraitWindSet', 'orientationWindSet', 'lamp', 'sleep', 'highCool', 'cool', 'coolEx') if type(raw.get(k)) is int})
            if device.kind == 'purifier':
                try:
                    s = self.session
                    rows = self.transport.post('UsrGetBindDevInfo', {'usrId': s['usrId'],
                        'familyId': s['familyId'], 'realFamilyId': s['realFamilyId']}, s['ssId']).get('devList', [])
                    row = next(row for row in rows if isinstance(row, dict) and row.get('deviceId') == device.device_id)
                    cached = (row.get('params') or {}).get('statusAll')
                    if isinstance(cached, str):
                        import json
                        cached = json.loads(cached)
                    checked = full_status(cached, result)
                    result.update({k: checked[k] for k in ('runM', 'uvSterilization')})
                except Exception:
                    pass  # preserve realtime basics; unavailable controls never use stale extras
            return result
        except Exception:
            raise CloudError('设备状态查询失败；未自动重登或发送控制') from None

    def set_fridge_controls(self, device, changes):
        if device.kind != 'fridge' or device.model != 'Fridge-19' or device not in self.devices or not self.session:
            raise CloudError('冰箱目标或会话不可用')
        identity = {'usrId': self.session['usrId'], 'deviceId': device.device_id,
                    'token': gen_token(device.device_id)}
        current = self.transport.get_fridge_status(identity, self.session['ssId'])
        return self.transport.set_fridge_controls(identity, self.session['ssId'], current, changes)

    def set_power(self, device, value):
        if device.kind != 'purifier' or device.model != 'F-75C5PJD' or device not in self.devices:
            raise CloudError('该设备没有已验证的控制能力')
        if not self.session:
            raise CloudError('会话不可用，请先重新加载集成')
        # Called exclusively by explicit HA power switch actions. Never relogin
        # or retry a command; all non-power fields retain the verified 255 value.
        return self.transport.set_purifier_power(
            device.device_id, self.session['usrId'], self.session['ssId'], value)

    def set_ac_controls(self, device, changes):
        if device.kind != 'ac' or device not in self.devices or not self.session:
            raise CloudError('空调控制会话或目标不可用')
        identity = {'usrId': self.session['usrId'], 'deviceId': device.device_id,
                    'token': gen_token(device.device_id)}
        # Fresh baseline only: no stale fallback and no copying read-only sensors.
        current = self.transport.post(AC_GET, identity, self.session['ssId'])
        trace_marker = Path('/config/.panasonic-lamp-trace-request')
        trace_path = Path('/config/.panasonic-lamp-trace.json')
        trace = changes.keys() == {'lamp'} and trace_marker.is_file()
        if trace:
            try:
                trace_marker.unlink()
            except OSError:
                trace = False
        try:
            response = self.transport.set_ac_controls(device.device_id, self.session['usrId'],
                                                      self.session['ssId'], current, changes)
        except Exception:
            if trace:
                try:
                    import json
                    trace_path.write_text(json.dumps({'before': current.get('lamp'), 'requested': changes['lamp'], 'result': 'error'}))
                except OSError:
                    pass
            raise
        if trace:
            try:
                import json
                safe = {'before': current.get('lamp'), 'requested': changes['lamp'], 'result': 'accepted',
                        'response_keys': sorted(k for k in response if k in ('todoId', 'result', 'status'))}
                trace_path.write_text(json.dumps(safe))
            except OSError:
                pass
        return response

    def set_purifier_controls(self, device, changes):
        if (device.kind != 'purifier' or device.model != 'F-75C5PJD'
                or device not in self.devices or not self.session):
            raise CloudError('净化器控制会话或目标不可用')
        if set(changes) & {'runM', 'uvSterilization'}:
            build_changes(changes)
            current = self.status(device)
            if current.get('runSta') != 1 or 'runM' not in current or 'uvSterilization' not in current:
                raise CloudError('完整状态未同步或设备未开机，未发送控制')
            if 'uvSterilization' in changes and current['runM'] != 1:
                raise CloudError('等离子体仅在自定义模式可调')
            return self.transport.set_purifier_extended(device.device_id, self.session['usrId'], self.session['ssId'], changes)
        if len(changes) != 1 or set(changes) - {'nanoe', 'childLock', 'led', 'lcdSwitch', 'airVo'}:
            raise CloudError('此功能尚未开放')
        current = self.status(device)
        if 'airVo' in changes:
            if (type(current.get('runSta')) is not int or current['runSta'] != 1
                    or current.get('runM') != 1
                    or type(current.get('airVo')) is not int or current['airVo'] not in (2, 3, 4)):
                raise CloudError('请先在官方 App 启动自定义模式，风速控件才可使用')
        elif any(type(current.get(key)) is not int or current[key] not in (0, 1) for key in changes):
            raise CloudError('该功能未返回已知布尔状态，拒绝猜测编码')
        return self.transport.set_purifier_controls(device.device_id, self.session['usrId'],
                                                    self.session['ssId'], changes)
