from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN


class PanasonicEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, device, key):
        super().__init__(coordinator)
        self.device = device
        self.key = key
        self._attr_unique_id = f'{device.uid}_{key}'
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.uid)}, name=device.name,
            manufacturer='Panasonic', model=device.model)

    @property
    def available(self):
        return (super().available and self.coordinator.data.get(self.device.uid, {}).get('online', False))

    @property
    def raw(self):
        return self.coordinator.data.get(self.device.uid, {}).get('status', {}).get(self.key)
