from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfTemperature
from . import DOMAIN
from .entity import PanasonicEntity
from .fridge_protocol import FRIDGE_TEMPERATURES


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([FridgeTemperature(coordinator, device, key, label, low, high)
                        for device in coordinator.client.devices if device.kind == 'fridge'
                        for key, (label, low, high) in FRIDGE_TEMPERATURES.items()])


class FridgeTemperature(PanasonicEntity, NumberEntity):
    _attr_mode = NumberMode.BOX
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = 'temperature'
    _attr_extra_state_attributes = {'控制验证': '范围依据官方说明书，写入待用户手动实机验收'}

    def __init__(self, coordinator, device, key, label, low, high):
        super().__init__(coordinator, device, key + '_temperature_control')
        self.field = key
        self._attr_name = label
        self._attr_native_min_value = low
        self._attr_native_max_value = high

    @property
    def native_value(self):
        return self.coordinator.data.get(self.device.uid, {}).get('status', {}).get(self.field)

    async def async_set_native_value(self, value):
        if type(value) not in (int, float) or not self.native_min_value <= value <= self.native_max_value or value != int(value):
            raise ValueError('温度不在官方允许范围内')
        await self.coordinator.async_set_fridge_controls(self.device, {self.field: int(value)})
