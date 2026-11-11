from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import EntityCategory

from . import DOMAIN
from .client import AC_FIELDS, PURIFIER_FIELDS, FRIDGE_FIELDS
from .entity import PanasonicEntity

NAMES = {
    'PCTempSet': '冷藏设定温度', 'PCTempCur': '冷藏温度',
    'FCTempSet': '冷冻设定温度', 'FCTempCur': '冷冻温度',
    'SCS1TempSet': '温区1设定温度', 'SCS1TempCur': '温区1温度',
    'runSta': '运行状态（原始值）', 'airVo': '风量（原始值）', 'nanoe': 'nanoe（原始值）',
    'pm25C': 'PM2.5（原始值）', 'humidityC': '湿度（原始值）', 'tempC': '温度（原始值）',
    'filterRemind': '滤网提醒（原始值）', 'filClRemain': '滤网清洁余量（原始值）',
    'filExRemain': '滤网更换余量（原始值）', 'childLock': '童锁（原始值）',
    'filterTL': '滤网寿命（原始值）', 'runStatus': '运行状态（原始值）',
    'runMode': '运行模式（原始值）', 'setTemperature': '设定温度（原始值）',
    'inhaleTemperature': '吸入温度（原始值）', 'outsideTemperature': '室外温度（原始值）',
    'windSet': '风速设定（原始值）', 'muteMode': '静音（原始值）', 'nanoeG': 'nanoeG（原始值）',
    'led': '指示灯（原始值）', 'lcdSwitch': '显示屏（原始值）',
}


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        PanasonicRawSensor(coordinator, device, key)
        for device in coordinator.client.devices
        for key in (FRIDGE_FIELDS if device.kind == 'fridge' else PURIFIER_FIELDS if device.kind == 'purifier' else AC_FIELDS)
        if key not in ('led', 'lcdSwitch') or key in coordinator.data.get(device.uid, {}).get('status', {})
    ])


class PanasonicRawSensor(PanasonicEntity, SensorEntity):
    def __init__(self, coordinator, device, key):
        super().__init__(coordinator, device, key)
        self._attr_name = NAMES[key]
        self._attr_icon = 'mdi:information-outline'
        if device.kind == 'fridge':
            self._attr_native_unit_of_measurement = '°C'
            self._attr_device_class = 'temperature'
            self._attr_icon = 'mdi:thermometer'
        elif key == 'pm25C':
            self._attr_name = 'PM2.5'
            self._attr_native_unit_of_measurement = 'µg/m³'
            self._attr_icon = 'mdi:air-filter'
        else:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        return self.raw
