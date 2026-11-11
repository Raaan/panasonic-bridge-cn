"""Purifier mode/airflow and AC direction controls; no commands during setup."""
from homeassistant.components.select import SelectEntity
from homeassistant.exceptions import HomeAssistantError

from . import DOMAIN
from .entity import PanasonicEntity
from .purifier_protocol import MODES
from .protocols import AC_VERTICAL, AC_HORIZONTAL

FAN_SPEEDS = {'低': 2, '中': 3, '高': 4}


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PanasonicDirection(coordinator, device, key, label, options)
                        for device in coordinator.client.devices if device.kind == 'ac'
                        for key, label, options in (('portraitWindSet', '上下风向', AC_VERTICAL), ('orientationWindSet', '左右风向', AC_HORIZONTAL))])
    async_add_entities([PanasonicFanSpeed(coordinator, device, 'fan_speed_control')
                        for device in coordinator.client.devices
                        if device.kind == 'purifier' and device.model == 'F-75C5PJD'])
    async_add_entities([PanasonicMode(coordinator, device, 'mode_control')
                        for device in coordinator.client.devices
                        if device.kind == 'purifier' and device.model == 'F-75C5PJD'])


class PanasonicDirection(PanasonicEntity, SelectEntity):
    _attr_icon = 'mdi:swap-vertical'
    _attr_extra_state_attributes = {'控制验证': '当前型号已实现控制获维护者确认；其他型号需单独验证'}

    def __init__(self, coordinator, device, key, label, options):
        super().__init__(coordinator, device, key + '_control')
        self.field, self.options_map = key, options
        self._attr_name = label
        self._attr_options = list(options)

    @property
    def available(self):
        return super().available and self.coordinator.data.get(self.device.uid, {}).get('status', {}).get('runStatus') == 48

    @property
    def current_option(self):
        value = self.coordinator.data.get(self.device.uid, {}).get('status', {}).get(self.field)
        return next((name for name, code in self.options_map.items() if code == value), None)

    async def async_select_option(self, option):
        if option not in self.options_map:
            raise HomeAssistantError('未知风向')
        await self.coordinator.async_set_ac_controls(self.device, {self.field: self.options_map[option]})


class PanasonicFanSpeed(PanasonicEntity, SelectEntity):
    _attr_name = '风量'
    _attr_icon = 'mdi:fan'
    _attr_options = ['轻柔', *FAN_SPEEDS]
    _attr_extra_state_attributes = {
        '使用说明': '轻柔切换到轻柔模式；低中高切换到自定义模式',
        '控制验证': '当前型号已实现控制获维护者确认；其他型号需单独验证',
    }

    @property
    def available(self):
        status = self.coordinator.data.get(self.device.uid, {}).get('status', {})
        return (super().available and type(status.get('runSta')) is int
                and status['runSta'] == 1 and type(status.get('runM')) is int
                and status['runM'] in MODES.values())

    @property
    def current_option(self):
        status = self.coordinator.data.get(self.device.uid, {}).get('status', {})
        if status.get('runM') == 0:
            return '轻柔'
        if status.get('runM') != 1:
            return None
        value = status.get('airVo')
        return next((label for label, code in FAN_SPEEDS.items() if type(value) is int and code == value), None)

    async def async_select_option(self, option):
        if option == '轻柔':
            changes = {'runM': 0}
        elif option in FAN_SPEEDS:
            mode = self.coordinator.data.get(self.device.uid, {}).get('status', {}).get('runM')
            changes = {'airVo': FAN_SPEEDS[option]} if mode == 1 else {'runM': 1, 'airVo': FAN_SPEEDS[option]}
        else:
            raise HomeAssistantError('仅支持轻柔、低、中、高风量')
        await self.coordinator.async_set_purifier_controls(self.device, changes)


class PanasonicMode(PanasonicEntity, SelectEntity):
    _attr_name = '模式'
    _attr_icon = 'mdi:air-purifier'
    _attr_options = list(MODES)
    _attr_extra_state_attributes = {'控制验证': '当前型号已实现控制获维护者确认；其他型号需单独验证'}

    @property
    def available(self):
        status = self.coordinator.data.get(self.device.uid, {}).get('status', {})
        return super().available and status.get('runSta') == 1 and type(status.get('runM')) is int and status['runM'] in MODES.values()

    @property
    def current_option(self):
        value = self.coordinator.data.get(self.device.uid, {}).get('status', {}).get('runM')
        return next((label for label, code in MODES.items() if type(value) is int and code == value), None)

    async def async_select_option(self, option):
        if option not in MODES:
            raise HomeAssistantError('未知净化器模式')
        await self.coordinator.async_set_purifier_controls(self.device, {'runM': MODES[option]})
