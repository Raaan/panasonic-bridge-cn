"""Panasonic cloud polling and explicit control with bounded read-back checks."""
from datetime import timedelta
import asyncio
import logging

from homeassistant.const import Platform
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import Client
from .transport import CloudError

DOMAIN = 'panasonic_home_readonly'
PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.SWITCH, Platform.CLIMATE, Platform.SELECT, Platform.NUMBER]
_LOGGER = logging.getLogger(__name__)


class PanasonicCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry, client):
        super().__init__(hass, _LOGGER, name='Panasonic status',
                         config_entry=entry, update_interval=timedelta(seconds=60))
        self.client = client
        self._command_lock = asyncio.Lock()

    async def async_set_fridge_controls(self, device, changes):
        async with self._command_lock:
            try:
                await self.hass.async_add_executor_job(self.client.set_fridge_controls, device, changes)
            except Exception:
                raise HomeAssistantError('冰箱请求未确认或参数不匹配；未自动重试') from None
            await asyncio.sleep(12)
            await self.async_request_refresh()
            observed = (self.data or {}).get(device.uid, {}).get('status', {})
            if any(observed.get(k) != v for k, v in changes.items()):
                raise HomeAssistantError('冰箱请求已提交一次但读回未确认；不会重发，请核对官方App和实体')

    async def async_set_power(self, device, value):
        async with self._command_lock:
            try:
                await self.hass.async_add_executor_job(self.client.set_power, device, value)
            except Exception:
                raise HomeAssistantError('净化器电源请求未确认，未自动重试；请查看状态或重新加载集成') from None
            await asyncio.sleep(3)
            await self.async_request_refresh()
            observed = (self.data or {}).get(device.uid, {}).get('status', {}).get('runSta')
            if observed != value:
                raise HomeAssistantError('已发送一次电源请求，但读回尚未确认；不会重发，请等待刷新并核对实体')

    async def async_set_ac_controls(self, device, changes):
        async with self._command_lock:
            try:
                await self.hass.async_add_executor_job(self.client.set_ac_controls, device, changes)
            except CloudError as error:
                raise HomeAssistantError(f'空调请求未确认（{error.safe_detail}），未重试或切换端点') from None
            except ValueError:
                raise HomeAssistantError('当前状态不匹配已实现的空调协议或参数越界，未发送命令') from None
            except Exception:
                raise HomeAssistantError('空调请求未确认，未重试或切换端点；请核对实体结果及协议') from None
            await asyncio.sleep(3)
            await self.async_request_refresh()
            observed = (self.data or {}).get(device.uid, {}).get('status', {})
            if any(observed.get(key) != value for key, value in changes.items()):
                if changes == {'runStatus': 49}:
                    # Read-only second confirmation for slow cloud/device sync.
                    # The command above is never sent again.
                    await asyncio.sleep(12)
                    await self.async_refresh()
                    observed = (self.data or {}).get(device.uid, {}).get('status', {})
                    if observed.get('runStatus') == 49:
                        return
                raise HomeAssistantError('空调请求已提交一次，但读回尚未确认；不会重发，请等待刷新并核对实体')

    async def async_set_purifier_controls(self, device, changes):
        async with self._command_lock:
            try:
                await self.hass.async_add_executor_job(self.client.set_purifier_controls, device, changes)
            except Exception:
                raise HomeAssistantError('净化器功能请求未确认，未自动重试；请核对设备状态') from None
            await asyncio.sleep(3)
            await self.async_request_refresh()
            observed = (self.data or {}).get(device.uid, {}).get('status', {})
            if any(observed.get(key) != value for key, value in changes.items()):
                raise HomeAssistantError('功能请求已提交一次，但读回尚未确认；不会重发，请等待刷新并核对实体')

    def _read(self):
        result = {}
        for device in self.client.devices:
            try:
                status = self.client.status(device)
                result[device.uid] = {'online': bool(status), 'status': status}
            except Exception:
                result[device.uid] = {'online': False, 'status': {}}
        if not any(value['online'] for value in result.values()):
            raise UpdateFailed('松下状态暂不可用；可重新加载集成重新登录')
        return result

    async def _async_update_data(self):
        return await self.hass.async_add_executor_job(self._read)


async def async_setup_entry(hass, entry):
    bucket = hass.data.setdefault(DOMAIN, {})
    client = bucket.pop('pending_' + entry.unique_id, None)
    try:
        if client is None:
            client = await hass.async_add_executor_job(Client)
            await hass.async_add_executor_job(client.login, entry.data['username'], entry.data['password'])
        if not client.devices:
            raise ConfigEntryNotReady('没有找到本地已验证型号')
    except Exception:
        raise ConfigEntryNotReady('松下登录暂不可用；凭据和响应未写入日志') from None
    coordinator = PanasonicCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    bucket[entry.entry_id] = coordinator
    if entry.title == '松下智家（只读）':
        hass.config_entries.async_update_entry(entry, title='松下智家（本地验证）')
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry):
    if await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id, None)
        return True
    return False
