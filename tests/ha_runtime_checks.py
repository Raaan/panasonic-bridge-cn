"""Run in an isolated HA environment. Cloud calls and credentials are mocked."""
import asyncio
import hashlib
import importlib
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch

import homeassistant.bootstrap

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
PREFIX = 'custom_components.panasonic_home_readonly'
integration = importlib.import_module(PREFIX)
flow_module = importlib.import_module(PREFIX + '.config_flow')
client_module = importlib.import_module(PREFIX + '.client')
platforms = {name: importlib.import_module(PREFIX + '.' + name)
             for name in ('sensor', 'binary_sensor', 'switch', 'climate', 'select', 'number')}


class RuntimeTests(unittest.IsolatedAsyncioTestCase):
    def entry(self):
        return SimpleNamespace(entry_id='synthetic-entry', unique_id='synthetic-account-hash',
                               title='松下智家（本地验证）',
                               data={'username': 'synthetic-account', 'password': 'synthetic-password'})

    def hass(self):
        async def executor(func, *args):
            return func(*args)
        return SimpleNamespace(data={}, async_add_executor_job=executor,
                               config_entries=SimpleNamespace(
                                   async_forward_entry_setups=AsyncMock(),
                                   async_unload_platforms=AsyncMock(return_value=True),
                                   async_update_entry=Mock()))

    async def test_setup_and_unload_do_not_control_devices(self):
        hass, entry = self.hass(), self.entry()
        client = SimpleNamespace(login=Mock(), devices=[object()], set_power=Mock())
        coordinator = SimpleNamespace(async_config_entry_first_refresh=AsyncMock())
        with patch.object(integration, 'Client', return_value=client), \
             patch.object(integration, 'PanasonicCoordinator', return_value=coordinator):
            self.assertTrue(await integration.async_setup_entry(hass, entry))
        client.login.assert_called_once_with('synthetic-account', 'synthetic-password')
        client.set_power.assert_not_called()
        coordinator.async_config_entry_first_refresh.assert_awaited_once()
        hass.config_entries.async_forward_entry_setups.assert_awaited_once()
        self.assertIs(hass.data[integration.DOMAIN][entry.entry_id], coordinator)
        self.assertTrue(await integration.async_unload_entry(hass, entry))
        self.assertNotIn(entry.entry_id, hass.data[integration.DOMAIN])

    async def test_failed_unload_retains_coordinator(self):
        hass, entry = self.hass(), self.entry()
        coordinator = object()
        hass.data[integration.DOMAIN] = {entry.entry_id: coordinator}
        hass.config_entries.async_unload_platforms.return_value = False
        self.assertFalse(await integration.async_unload_entry(hass, entry))
        self.assertIs(hass.data[integration.DOMAIN][entry.entry_id], coordinator)

    async def test_setup_failure_does_not_expose_credentials(self):
        hass, entry = self.hass(), self.entry()
        client = SimpleNamespace(login=Mock(side_effect=RuntimeError('synthetic-password')), devices=[])
        with patch.object(integration, 'Client', return_value=client):
            with self.assertRaises(integration.ConfigEntryNotReady) as error:
                await integration.async_setup_entry(hass, entry)
        self.assertNotIn('synthetic-password', str(error.exception))
        self.assertNotIn(entry.entry_id, hass.data[integration.DOMAIN])
        hass.config_entries.async_forward_entry_setups.assert_not_awaited()

    async def test_pending_login_is_reused_without_another_login(self):
        hass, entry = self.hass(), self.entry()
        client = SimpleNamespace(login=Mock(), devices=[object()])
        hass.data[integration.DOMAIN] = {'pending_' + entry.unique_id: client}
        coordinator = SimpleNamespace(async_config_entry_first_refresh=AsyncMock())
        with patch.object(integration, 'Client') as constructor, \
             patch.object(integration, 'PanasonicCoordinator', return_value=coordinator):
            self.assertTrue(await integration.async_setup_entry(hass, entry))
        constructor.assert_not_called()
        client.login.assert_not_called()

    async def test_all_platforms_create_entities_without_commands(self):
        devices = [client_module.Device('synthetic-' + kind, 'synthetic-' + kind + '-uid', kind, model, kind)
                   for kind, model in (('purifier', 'F-75C5PJD'), ('ac', 'AirconCommon-2024-01'), ('fridge', 'Fridge-19'))]
        status = {'runSta': 1, 'airVo': 2, 'runM': 1, 'nanoe': 1, 'uvSterilization': 0,
                  'childLock': 0, 'led': 1, 'lcdSwitch': 1}
        commands = {name: AsyncMock() for name in ('async_set_power', 'async_set_purifier_controls',
                    'async_set_ac_controls', 'async_set_fridge_controls')}
        coordinator = SimpleNamespace(client=SimpleNamespace(devices=devices), last_update_success=True,
            data={d.uid: {'online': True, 'status': status if d.kind == 'purifier' else {}} for d in devices}, **commands)
        hass = self.hass()
        entry = self.entry()
        hass.data[integration.DOMAIN] = {entry.entry_id: coordinator}
        entities = []
        for module in platforms.values():
            await module.async_setup_entry(hass, entry, entities.extend)
        self.assertGreater(len(entities), 20)
        for command in commands.values():
            command.assert_not_awaited()
        self.assertEqual(len({e.unique_id for e in entities}), len(entities))

    def make_flow(self, entry, entries):
        flow = flow_module.PanasonicFlow()
        flow.hass = self.hass()
        flow.hass.config_entries.async_entries = lambda domain: entries
        flow._get_reconfigure_entry = lambda: entry
        flow.async_update_reload_and_abort = Mock(return_value={'reason': 'reconfigure_successful'})
        flow.async_show_form = lambda **kwargs: kwargs
        flow.async_abort = lambda **kwargs: kwargs
        return flow

    async def test_reconfigure_preserves_old_data_until_successful_update(self):
        entry = self.entry()
        flow = self.make_flow(entry, [entry])
        client = SimpleNamespace(login=Mock(return_value=[object()]))
        with patch.object(flow_module, 'Client', return_value=client):
            result = await flow.async_step_reconfigure({'username': 'new-synthetic-account', 'password': 'new-synthetic-password'})
        self.assertEqual(result['reason'], 'reconfigure_successful')
        update = flow.async_update_reload_and_abort.call_args.kwargs
        self.assertEqual(update['unique_id'], hashlib.sha256(b'new-synthetic-account').hexdigest())
        self.assertEqual(entry.data['password'], 'synthetic-password')

    async def test_failed_reconfigure_preserves_credentials(self):
        entry = self.entry()
        flow = self.make_flow(entry, [entry])
        client = SimpleNamespace(login=Mock(side_effect=RuntimeError('new-synthetic-password')))
        with patch.object(flow_module, 'Client', return_value=client):
            result = await flow.async_step_reconfigure({'username': 'new-synthetic-account', 'password': 'new-synthetic-password'})
        self.assertEqual(result['errors']['base'], 'cannot_connect')
        flow.async_update_reload_and_abort.assert_not_called()
        self.assertEqual(entry.data['password'], 'synthetic-password')

    async def test_readback_failure_never_resends_power_command(self):
        coordinator = object.__new__(integration.PanasonicCoordinator)
        coordinator._command_lock = asyncio.Lock()
        coordinator.hass = self.hass()
        coordinator.client = SimpleNamespace(set_power=Mock())
        coordinator.data = {'synthetic-uid': {'status': {'runSta': 0}}}
        coordinator.async_request_refresh = AsyncMock()
        device = SimpleNamespace(uid='synthetic-uid')
        with patch.object(integration.asyncio, 'sleep', new=AsyncMock()):
            with self.assertRaises(integration.HomeAssistantError):
                await coordinator.async_set_power(device, 1)
        coordinator.client.set_power.assert_called_once_with(device, 1)
        coordinator.async_request_refresh.assert_awaited_once()


if __name__ == '__main__':
    unittest.main(verbosity=2)
