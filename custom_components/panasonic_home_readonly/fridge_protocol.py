"""Fridge-19 candidate controls; GET confirmed, SET awaiting manual validation."""
FRIDGE_SWITCHES = {
    'quickFreeze': ('速冻', 'mdi:snowflake'),
    'quickicing': ('快速制冰', 'mdi:ice-pop'),
    'icingStop': ('制冰停止', 'mdi:pause-circle-outline'),
    'freshFrozen': ('新鲜冻结', 'mdi:food-variant'),
    'ecoNaviSet': ('节能导航', 'mdi:leaf'),
    'nanoe': ('NanoeX', 'mdi:air-filter'),
}
FRIDGE_TEMPERATURES = {
    'PCTempSet': ('冷藏设定温度', 2, 7),
    'SCS1TempSet': ('变温室设定温度', -3, 4),
    'FCTempSet': ('冷冻设定温度', -23, -17),
}
OFFICIAL_FRIDGE19_FIELDS = (
    'PCTempSet', 'FCTempSet', 'SCS1TempSet', 'SCS2TempSet', 'SCB1TempSet', 'SCB2TempSet',
    'quickFreeze', 'vacation', 'quickicing', 'icingStop', 'icingDeice', 'ecoNaviSet',
    'RAModeCur', 'SAModeCur', 'silver', 'preservation', 'nanoe', 'freshFrozen',
    'smartHumi', 'autoIcing', 'WCModeCur', 'SCB1ModeCur', 'SCB2ModeCur', 'zhencaiSet',
)


def build_fridge_params(current, changes):
    if len(changes) != 1 or set(changes) - (FRIDGE_SWITCHES.keys() | FRIDGE_TEMPERATURES.keys()):
        raise ValueError('Only one supported fridge feature per request')
    key, value = next(iter(changes.items()))
    if type(value) is not int:
        raise ValueError('Invalid switch value')
    if key in FRIDGE_SWITCHES and (value not in (0, 1) or type(current.get(key)) is not int or current[key] not in (0, 1)):
        raise ValueError('Feature not present in fresh state')
    if key in FRIDGE_TEMPERATURES:
        _, low, high = FRIDGE_TEMPERATURES[key]
        if not low <= value <= high:
            raise ValueError('Temperature outside manufacturer range')
    limits = {key: (low, high) for key, (_, low, high) in FRIDGE_TEMPERATURES.items()}
    for field, (low, high) in limits.items():
        if type(current.get(field)) is not int or not low <= current[field] <= high:
            raise ValueError('Unknown temperature state; refusing write')
    if any(k in current and type(current[k]) is not int for k in OFFICIAL_FRIDGE19_FIELDS):
        raise ValueError('Unrecognized fridge field type')
    params = {k: current.get(k, 0) for k in OFFICIAL_FRIDGE19_FIELDS}
    params.update(changes)
    # Match the manufacturer's feature page: these options are mutually exclusive.
    if value == 1 and key == 'quickicing':
        params.update(icingStop=0, freshFrozen=0)
    elif value == 1 and key in ('icingStop', 'freshFrozen'):
        params['quickicing'] = 0
    params['isTodoLimit'] = 1
    return params
