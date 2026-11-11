"""Power only for the physically verified purifier. No automatic commands."""
from homeassistant.components.switch import SwitchEntity

from . import DOMAIN
from .entity import PanasonicEntity
from .fridge_protocol import FRIDGE_SWITCHES


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PanasonicFridgeFeature(coordinator, device, key, label, icon)
                        for device in coordinator.client.devices if device.kind == 'fridge'
                        for key, (label, icon) in FRIDGE_SWITCHES.items()])
    async_add_entities([PanasonicPower(coordinator, device, 'power')
                        for device in coordinator.client.devices
                        if device.kind == 'purifier' and device.model == 'F-75C5PJD'])
    extras = []
    for device in coordinator.client.devices:
        if device.kind != 'purifier' or device.model != 'F-75C5PJD':
            continue
        status = coordinator.data.get(device.uid, {}).get('status', {})
        for key, label in {'nanoe': 'NanoeX', 'childLock': '童锁', 'led': '指示灯', 'lcdSwitch': '显示屏', 'uvSterilization': '等离子体'}.items():
            if status.get(key) in (0, 1):
                extras.append(PanasonicBoolean(coordinator, device, key, label))
    async_add_entities(extras)
    async_add_entities([PanasonicAuxHeat(coordinator, device, 'aux_heat_control')
                        for device in coordinator.client.devices if device.kind == 'ac'])
    async_add_entities([PanasonicAcNanoe(coordinator, device, 'ac_nanoe_control')
                        for device in coordinator.client.devices if device.kind == 'ac'])
    async_add_entities([PanasonicAcLamp(coordinator, device, 'ac_lamp_control')
                        for device in coordinator.client.devices if device.kind == 'ac'])
    async_add_entities([PanasonicAcSleep(coordinator, device, 'ac_sleep_control')
                        for device in coordinator.client.devices if device.kind == 'ac'])
    async_add_entities([PanasonicAcPowerful(coordinator, device, key, mode, label)
                        for device in coordinator.client.devices if device.kind == 'ac'
                        for key, mode, label in (('ac_powerful_control', 67, '强智暖'), ('ac_powerful_cool_control', 66, '强智冷'))])
    async_add_entities([PanasonicAcSoftCool(coordinator, device, 'ac_soft_cool_control')
                        for device in coordinator.client.devices if device.kind == 'ac'])


class PanasonicFridgeFeature(PanasonicEntity, SwitchEntity):
    _attr_extra_state_attributes = {'控制验证': '候选控制，待用户手动实机验收'}

    def __init__(self, coordinator, device, key, label, icon):
        super().__init__(coordinator, device, key + '_fridge_control')
        self.field = key
        self._attr_name = label
        self._attr_icon = icon

    @property
    def available(self):
        value = self.coordinator.data.get(self.device.uid, {}).get('status', {}).get(self.field)
        return super().available and type(value) is int and value in (0, 1)

    @property
    def is_on(self):
        return {0: False, 1: True}.get(self.coordinator.data.get(self.device.uid, {}).get('status', {}).get(self.field))

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_set_fridge_controls(self.device, {self.field: 1})

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_fridge_controls(self.device, {self.field: 0})


class PanasonicAcSoftCool(PanasonicEntity, SwitchEntity):
    _attr_name = '柔湿制冷'
    _attr_icon = 'mdi:snowflake'
    _attr_extra_state_attributes = {'控制验证': '字段及取值为候选，待制冷季手动验收'}

    @property
    def available(self):
        s = self.coordinator.data.get(self.device.uid, {}).get('status', {})
        return super().available and s.get('runStatus') == 48 and s.get('runMode') == 66 and s.get('coolEx') == 1 and s.get('cool') in (0, 1)

    @property
    def is_on(self):
        return {0: False, 1: True}.get(self.coordinator.data.get(self.device.uid, {}).get('status', {}).get('cool'))

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_set_ac_controls(self.device, {'cool': 1})

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_ac_controls(self.device, {'cool': 0})


class PanasonicAcPowerful(PanasonicEntity, SwitchEntity):
    _attr_icon = 'mdi:weather-windy'
    _attr_extra_state_attributes = {'控制验证': '强智暖状态已对照；写入与强智冷待用户手动验收'}

    def __init__(self, coordinator, device, key, mode, label):
        super().__init__(coordinator, device, key)
        self.expected_mode = mode
        self._attr_name = label

    @property
    def available(self):
        s = self.coordinator.data.get(self.device.uid, {}).get('status', {})
        return super().available and s.get('runStatus') == 48 and s.get('runMode') == self.expected_mode and s.get('highCool') in (0, 1)

    @property
    def is_on(self):
        s = self.coordinator.data.get(self.device.uid, {}).get('status', {})
        return {0: False, 1: True}.get(s.get('highCool')) if s.get('runMode') == self.expected_mode else False

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_set_ac_controls(self.device, {'highCool': 1})

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_ac_controls(self.device, {'highCool': 0})


class PanasonicAcSleep(PanasonicEntity, SwitchEntity):
    _attr_name = '睡眠'
    _attr_icon = 'mdi:weather-night'
    _attr_extra_state_attributes = {'控制验证': '状态已对照，控制待用户手动验收'}

    @property
    def available(self):
        s = self.coordinator.data.get(self.device.uid, {}).get('status', {})
        return super().available and s.get('runStatus') == 48 and s.get('sleep') in (0, 1)

    @property
    def is_on(self):
        return {0: False, 1: True}.get(self.coordinator.data.get(self.device.uid, {}).get('status', {}).get('sleep'))

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_set_ac_controls(self.device, {'sleep': 1})

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_ac_controls(self.device, {'sleep': 0})


class PanasonicAcLamp(PanasonicEntity, SwitchEntity):
    _attr_name = '显示灯光'
    _attr_icon = 'mdi:lightbulb-outline'
    _attr_extra_state_attributes = {'控制验证': '状态已对照，控制待用户手动验收'}

    @property
    def available(self):
        return super().available and self.coordinator.data.get(self.device.uid, {}).get('status', {}).get('lamp') in (0, 1)

    @property
    def is_on(self):
        return {0: True, 1: False}.get(self.coordinator.data.get(self.device.uid, {}).get('status', {}).get('lamp'))

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_set_ac_controls(self.device, {'lamp': 0})

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_ac_controls(self.device, {'lamp': 1})


class PanasonicAcNanoe(PanasonicEntity, SwitchEntity):
    _attr_name = 'NanoeX'
    _attr_icon = 'mdi:air-filter'
    _attr_extra_state_attributes = {'控制验证': '状态已对照，控制待用户手动验收'}

    @property
    def available(self):
        s = self.coordinator.data.get(self.device.uid, {}).get('status', {})
        return super().available and s.get('runStatus') == 48 and s.get('nanoe') in (0, 1)

    @property
    def is_on(self):
        return {0: False, 1: True}.get(self.coordinator.data.get(self.device.uid, {}).get('status', {}).get('nanoe'))

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_set_ac_controls(self.device, {'nanoe': 1})

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_ac_controls(self.device, {'nanoe': 0})


class PanasonicAuxHeat(PanasonicEntity, SwitchEntity):
    _attr_name = '辅热'
    _attr_icon = 'mdi:radiator'
    _attr_extra_state_attributes = {'控制验证': '状态已对照，控制待用户手动验收'}

    @property
    def available(self):
        s = self.coordinator.data.get(self.device.uid, {}).get('status', {})
        return super().available and s.get('runStatus') == 48 and s.get('runMode') == 67 and s.get('elecHeat') in (0, 1)

    @property
    def is_on(self):
        return {0: False, 1: True}.get(self.coordinator.data.get(self.device.uid, {}).get('status', {}).get('elecHeat'))

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_set_ac_controls(self.device, {'elecHeat': 1})

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_ac_controls(self.device, {'elecHeat': 0})


class PanasonicPower(PanasonicEntity, SwitchEntity):
    _attr_name = '电源'
    _attr_icon = 'mdi:air-purifier'

    @property
    def is_on(self):
        value = self.coordinator.data.get(self.device.uid, {}).get('status', {}).get('runSta')
        return {0: False, 1: True}.get(value)

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_set_power(self.device, 1)

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_power(self.device, 0)


class PanasonicBoolean(PanasonicEntity, SwitchEntity):
    _attr_icon = 'mdi:tune'
    _attr_extra_state_attributes = {'控制验证': '待用户手动实机验证'}

    def __init__(self, coordinator, device, key, label):
        super().__init__(coordinator, device, key + '_control')
        self.field = key
        self._attr_name = label

    @property
    def available(self):
        status = self.coordinator.data.get(self.device.uid, {}).get('status', {})
        value = status.get(self.field)
        return (super().available and value in (0, 1) and
                (self.field != 'uvSterilization' or (status.get('runSta') == 1 and status.get('runM') == 1)))

    @property
    def is_on(self):
        value = self.coordinator.data.get(self.device.uid, {}).get('status', {}).get(self.field)
        return {0: False, 1: True}.get(value)

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_set_purifier_controls(self.device, {self.field: 1})

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_purifier_controls(self.device, {self.field: 0})
