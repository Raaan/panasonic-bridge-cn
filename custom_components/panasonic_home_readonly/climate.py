"""Manual-test climate entity for the observed new-protocol AC values."""
from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.exceptions import HomeAssistantError

from . import DOMAIN
from .entity import PanasonicEntity
from .protocols import AC_MODES, AC_FANS


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PanasonicClimate(coordinator, device, 'climate')
                        for device in coordinator.client.devices if device.kind == 'ac'])


class PanasonicClimate(PanasonicEntity, ClimateEntity):
    _attr_name = '空调'
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = 16
    _attr_max_temp = 30
    _attr_target_temperature_step = 1
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.COOL, HVACMode.HEAT, HVACMode.DRY]
    _attr_fan_modes = list(AC_FANS)
    _attr_supported_features = (ClimateEntityFeature.TARGET_TEMPERATURE
                                | ClimateEntityFeature.FAN_MODE
                                | ClimateEntityFeature.TURN_ON
                                | ClimateEntityFeature.TURN_OFF)
    _attr_extra_state_attributes = {'控制验证': '待用户手动实机验证'}

    @property
    def status(self):
        return self.coordinator.data.get(self.device.uid, {}).get('status', {})

    @property
    def hvac_mode(self):
        if self.status.get('runStatus') == 49:
            return HVACMode.OFF
        if self.status.get('runStatus') == 48:
            return next((HVACMode(mode) for mode, code in AC_MODES.items()
                         if code == self.status.get('runMode')), None)
        return None

    @property
    def target_temperature(self):
        value = self.status.get('setTemperature')
        return value if type(value) in (int, float) and 16 <= value <= 30 else None

    @property
    def current_temperature(self):
        # The inhaleTemperature encoding is not verified. In particular 128 is
        # not a plausible room reading. Never invent a scaling rule or room temp.
        return None

    @property
    def fan_mode(self):
        return next((name for name, value in AC_FANS.items()
                     if value == self.status.get('windSet')), None)

    async def async_set_hvac_mode(self, hvac_mode):
        if hvac_mode == HVACMode.OFF:
            await self.async_turn_off()
        elif hvac_mode in AC_MODES:
            await self.coordinator.async_set_ac_controls(
                self.device, {'runStatus': 48, 'runMode': AC_MODES[hvac_mode]})
        else:
            raise HomeAssistantError('此模式未列入已核对的候选协议')

    async def async_turn_on(self):
        await self.coordinator.async_set_ac_controls(self.device, {'runStatus': 48})

    async def async_turn_off(self):
        await self.coordinator.async_set_ac_controls(self.device, {'runStatus': 49})

    async def async_set_temperature(self, **kwargs):
        value = kwargs.get(ATTR_TEMPERATURE)
        if type(value) not in (int, float) or not 16 <= value <= 30 or value != int(value):
            raise HomeAssistantError('请输入16至30之间的整数温度')
        await self.coordinator.async_set_ac_controls(self.device, {'setTemperature': int(value)})

    async def async_set_fan_mode(self, fan_mode):
        if fan_mode not in AC_FANS:
            raise HomeAssistantError('未支持的风速')
        await self.coordinator.async_set_ac_controls(self.device, {'windSet': AC_FANS[fan_mode]})
