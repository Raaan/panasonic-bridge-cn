"""Observed F-75C5PJD enums and official skip template; no network calls."""
MODES = {'智能托管': 3, '轻柔': 0, '自定义': 1, '消毒': 2}
SPEEDS = {'低': 2, '中': 3, '高': 4}
SKIP_FIELDS = ('runSta', 'airVo', 'runM', 'dust', 'sensiOxy', 'sensiTVOC',
               'timeSet', 'nanoe', 'filExReset', 'uvSterilization', 'filClReset',
               'childLock', 'lcdSwitch', 'autoCare', 'res7', 'res8', 'res10',
               'res11', 'res12', 'res13', 'res14', 'res15', 'res16', 'res17',
               'led', 'gas', 'fliterRemind')


def full_status(raw, live):
    if not isinstance(raw, dict):
        raise ValueError('Missing complete state')
    values = {}
    for key, allowed in {'runSta': (0, 1), 'runM': range(4), 'airVo': range(6),
                         'nanoe': (0, 1), 'uvSterilization': (0, 1)}.items():
        value = raw.get(key)
        if type(value) is str and value.isascii() and value.isdigit() and len(value) <= 3:
            value = int(value)
        if type(value) is not int or value not in allowed:
            raise ValueError('Unknown complete state')
        values[key] = value
    if any(type(live.get(k)) is not int or values[k] != live[k] for k in ('runSta', 'airVo', 'nanoe')):
        raise ValueError('Cached state not synchronized')
    return values


def build_changes(changes):
    if changes.keys() == {'runM', 'airVo'}:
        valid = type(changes['runM']) is int and changes['runM'] == 1 and type(changes['airVo']) is int and changes['airVo'] in SPEEDS.values()
    elif len(changes) == 1 and set(changes) <= {'runM', 'uvSterilization'}:
        key, value = next(iter(changes.items()))
        valid = type(value) is int and value in (range(4) if key == 'runM' else (0, 1))
    else:
        valid = False
    if not valid:
        raise ValueError('Unsupported purifier change')
    return {**dict.fromkeys(SKIP_FIELDS, 255), **changes}
