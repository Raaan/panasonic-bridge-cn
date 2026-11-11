from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass

from . import DOMAIN
from .entity import PanasonicEntity


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PanasonicRunning(coordinator, device, 'runSta')
                        for device in coordinator.client.devices if device.kind == 'purifier'])
    async_add_entities([PanasonicAuxHeat(coordinator, device, 'elecHeat')
                        for device in coordinator.client.devices if device.kind == 'ac'])


class PanasonicAuxHeat(PanasonicEntity, BinarySensorEntity):
    _attr_name = '辅热状态'
    _attr_icon = 'mdi:radiator'

    @property
    def is_on(self):
        return {0: False, 1: True}.get(self.raw)


class PanasonicRunning(PanasonicEntity, BinarySensorEntity):
    _attr_name = '运行'
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    @property
    def is_on(self):
        return {0: False, 1: True}.get(self.raw)
