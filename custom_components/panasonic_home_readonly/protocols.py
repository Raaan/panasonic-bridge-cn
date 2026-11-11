"""AC parameters for the AirconCommon-2024-01 protocol.

Enumeration reference from another unit:
https://bbs.hassbian.com/forum.php?mod=viewthread&page=5&tid=17153
The current model has been checked on hardware. Requests use top-level identity
fields and params. A failed command is not retried through another endpoint.
"""
AC_MODES = {'cool': 66, 'heat': 67, 'dry': 68}
AC_FANS = {'自动': 65, '20%': 49, '40%': 50, '60%': 52, '80%': 54, '100%': 55}
AC_VERTICAL = {'自动扫风': 70, '位置1': 65, '位置2': 68, '位置3': 67, '位置4': 69, '位置5': 66}
AC_HORIZONTAL = {'自动扫风': 64, '位置1': 66, '位置2': 108, '位置3': 67, '位置4': 87, '位置5': 65}
AC_WRITABLE = frozenset({
    'runMode', 'runStatus', 'setTemperature', 'windSet',
    'forceRunning', 'remoteForbidMode', 'remoteMode', 'setHumidity',
    'exchangeWindSet', 'portraitWindSet', 'orientationWindSet', 'nanoeG',
    'nanoe', 'ecoMode', 'muteMode', 'powerful', 'powerfulMode', 'thermoMode',
    'buzzer', 'autoRunMode', 'runForbidden', 'sleep', 'lamp', 'elecHeat', 'highCool', 'cool',
})


def build_ac_params(current, changes):
    """Preserve fresh known controls. Never copy sensors, identities or resets."""
    if (current.get('runStatus') not in (48, 49)
            or current.get('runMode') not in AC_MODES.values()
            or current.get('windSet') not in AC_FANS.values()
            or type(current.get('setTemperature')) not in (int, float)
            or not 16 <= current['setTemperature'] <= 30):
        raise ValueError('Device does not match the observed new-protocol family')
    if not changes or len(changes) > 2 or set(changes) - {'runStatus', 'runMode', 'setTemperature', 'windSet', 'elecHeat', 'portraitWindSet', 'orientationWindSet', 'nanoe', 'lamp', 'sleep', 'highCool', 'cool'}:
        raise ValueError('Unsupported AC control')
    for key, value in changes.items():
        if type(value) is not int:
            raise ValueError('Control value must be an integer')
        if key == 'runStatus' and value not in (48, 49):
            raise ValueError('Invalid power value')
        if key == 'runMode' and value not in AC_MODES.values():
            raise ValueError('Invalid mode')
        if key == 'windSet' and value not in AC_FANS.values():
            raise ValueError('Invalid fan')
        if key == 'setTemperature' and not 16 <= value <= 30:
            raise ValueError('Temperature outside conservative UI range')
        if key == 'elecHeat' and (value not in (0, 1) or current.get('runStatus') != 48 or current.get('runMode') != 67 or current.get('elecHeat') not in (0, 1)):
            raise ValueError('Auxiliary heating requires a fresh heating state')
        if key == 'nanoe' and (value not in (0, 1) or current.get('runStatus') != 48 or current.get('nanoe') not in (0, 1)):
            raise ValueError('NanoeX requires a fresh running state')
        if key == 'lamp' and (value not in (0, 1) or current.get('lamp') not in (0, 1)):
            raise ValueError('Lamp requires a fresh state')
        if key == 'sleep' and (value not in (0, 1) or current.get('runStatus') != 48 or current.get('sleep') not in (0, 1)):
            raise ValueError('Sleep requires a fresh running state')
        if key == 'highCool' and (value not in (0, 1) or current.get('runStatus') != 48 or current.get('runMode') not in (66, 67) or current.get('highCool') not in (0, 1)):
            raise ValueError('Powerful mode requires fresh heating or cooling state')
        if key == 'cool' and (value not in (0, 1) or current.get('runStatus') != 48 or current.get('runMode') != 66 or current.get('cool') not in (0, 1) or current.get('coolEx') != 1):
            raise ValueError('Soft cooling requires a fresh supported cooling state')
        if key == 'portraitWindSet' and (value not in AC_VERTICAL.values() or current.get('runStatus') != 48):
            raise ValueError('Unsupported vertical direction')
        if key == 'orientationWindSet' and (value not in AC_HORIZONTAL.values() or current.get('runStatus') != 48):
            raise ValueError('Unsupported horizontal direction')
    params = {k: v for k, v in current.items() if k in AC_WRITABLE and type(v) in (int, float)}
    params.update(changes)
    return params
