"""Opt-in numeric snapshots for user-operated protocol calibration only."""
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import time

PRIVATE_KEY = re.compile(r'token|ssid|session|auth|password|pwd|secret|user|usr|family|device|serial|uid|id$|^sn$|mac|tel|mobile|address|room|location|name|mail|key', re.I)
PROTOCOL_KEYS = {'runsta', 'airvo', 'nanoe', 'nanoex', 'nanoeg', 'plasma',
                 'plasmaswitch', 'runmode', 'mode', 'workmode', 'operatingmode',
                 'controlmode', 'preset', 'presetmode', 'scenemode', 'sleepmode',
                 'gentlemode', 'disinfectionmode', 'sterilizationmode', 'fanspeed',
                 'runm', 'uvsterilization', 'autocare', 'autocarerun'}
CONTAINERS = {'params', 'status', 'state', 'data', 'result', 'results', 'settings'}
ENUM_TEXT = {'true', 'false', 'on', 'off', 'auto', 'smart', 'gentle', 'custom',
             'disinfection', 'sterilization', 'low', 'medium', 'high', 'turbo',
             '智能托管', '轻柔', '自定义', '消毒', '低', '中', '高', '急速'}


def public_key(key):
    return (isinstance(key, str)
            and re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,39}', key)
            and not PRIVATE_KEY.search(key))


def safe_structure(raw, depth=0):
    """Field names/types, plus strictly allowlisted small protocol scalars.

    Unknown string contents, arrays, identities and arbitrary nested objects
    are never copied. This diagnoses omissions without dumping a response.
    """
    fields = {}
    for key, value in list(raw.items())[:100]:
        if not public_key(key):
            continue
        kind = {str: 'string', int: 'integer', float: 'number', bool: 'boolean',
                dict: 'object', list: 'array', type(None): 'null'}.get(type(value), 'other')
        item = {'type': kind}
        if key.lower() in PROTOCOL_KEYS:
            if type(value) is bool or (type(value) is int and 0 <= value <= 255):
                item['value'] = value
            elif type(value) is str and (value in ENUM_TEXT
                    or (re.fullmatch(r'[0-9]{1,3}', value) and int(value) <= 255)):
                item['value'] = value
        if type(value) is dict and key.lower() in CONTAINERS and depth < 3:
            item['fields'] = safe_structure(value, depth + 1)
        fields[key] = item
    return fields


def safe_numeric_status(raw):
    return {key: value for key, value in raw.items()
            if public_key(key)
            and ((type(value) is int and -(2**63) <= value < 2**63)
                 or (type(value) is float and math.isfinite(value)))}


def write_if_enabled(raw, root=Path('/config')):
    root = Path(root)
    if not (root / '.panasonic-calibration-enabled').is_file():
        return
    destination = root / '.panasonic-calibration-safe.json'
    temporary = destination.with_suffix('.tmp')
    payload = {'sampled_at': datetime.now(timezone.utc).isoformat(),
               'status': safe_numeric_status(raw),
               'structure': safe_structure(raw)}
    with temporary.open('w', encoding='utf-8') as file:
        temporary.chmod(0o600)
        json.dump(payload, file, ensure_ascii=True, allow_nan=False)
    temporary.replace(destination)


def write_discovery_if_enabled(raw, root=Path('/config')):
    """Inspect only statusAll from normal discovery, with a separate opt-in."""
    root = Path(root)
    if not (root / '.panasonic-discovery-enabled').is_file():
        return
    input_type = type(raw).__name__
    if isinstance(raw, str) and len(raw) <= 1000000:
        try:
            raw = json.loads(raw)
        except ValueError:
            raw = None
    state = raw if isinstance(raw, dict) else {}
    numeric_strings = {key: int(value) for key, value in state.items()
                       if public_key(key) and type(value) is str
                       and re.fullmatch(r'-?[0-9]{1,19}', value)
                       and -(2**63) <= int(value) < 2**63}
    payload = {'sampled_at': datetime.now(timezone.utc).isoformat(),
               'source': 'UsrGetBindDevInfo.statusAll', 'input_type': input_type,
               'status': {**safe_numeric_status(state), **numeric_strings},
               'structure': safe_structure(state)}
    destination = root / '.panasonic-discovery-safe.json'
    temporary = destination.with_suffix('.tmp')
    with temporary.open('w', encoding='utf-8') as file:
        temporary.chmod(0o600)
        json.dump(payload, file, ensure_ascii=True, allow_nan=False)
    temporary.replace(destination)


def consume_discovery_request(root=Path('/config')):
    """Consume one fresh local read request before any network operation."""
    request = Path(root) / '.panasonic-discovery-request'
    try:
        age = time.time() - request.stat().st_mtime
        request.unlink()
    except FileNotFoundError:
        return False
    return -1 <= age <= 180


def consume_odm_request(root=Path('/config')):
    request = Path(root) / '.panasonic-odm-read-request'
    try:
        age = time.time() - request.stat().st_mtime
        request.unlink()
    except FileNotFoundError:
        return False
    return -1 <= age <= 180


def write_odm_probe(raw=None, detail=None, root=Path('/config')):
    """Called only after consuming one explicit local read request."""
    raw = raw if isinstance(raw, dict) else {}
    strings = {k: int(v) for k, v in raw.items() if public_key(k) and type(v) is str
               and re.fullmatch(r'-?[0-9]{1,19}', v) and -(2**63) <= int(v) < 2**63}
    payload = {'sampled_at': datetime.now(timezone.utc).isoformat(),
               'source': 'ADevGetStatusODM', 'result': 'error' if detail else 'received',
               'status': {**safe_numeric_status(raw), **strings}, 'structure': safe_structure(raw)}
    # Caller may supply only CloudError.safe_detail or the fixed fallback.
    if detail:
        payload['detail'] = detail if re.fullmatch(r'ADevGetStatusODM / (cloud|tls|network|response|http|certificate)( / [0-9]{1,8})?', detail) else 'unconfirmed'
    destination = Path(root) / '.panasonic-odm-probe-safe.json'
    temporary = destination.with_suffix('.tmp')
    with temporary.open('w', encoding='utf-8') as file:
        temporary.chmod(0o600)
        json.dump(payload, file, ensure_ascii=True, allow_nan=False)
    temporary.replace(destination)
