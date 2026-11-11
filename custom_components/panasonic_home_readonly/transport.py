"""Transport reused from the local handoff tools; TLS validated, no redirects.
Only authentication, discovery and validated read endpoints are permitted.
The original SET allowance has been removed. No automatic network calls at import.
"""
import hashlib
import json
import ssl
from pathlib import Path
from .protocols import build_ac_params
from .purifier_protocol import build_changes
from .fridge_protocol import build_fridge_params
import urllib.error
import urllib.request
BASE = 'https://app.psmartcloud.com/App/'
GET = 'ADevGetStatusNeedsAP'
AC_GET = 'ACDevGetStatusInfoAW'
ODM_GET = 'ADevGetStatusODM'  # bounded read-only candidate; no ODM SET allowed
PURIFIER_SET = 'ADevSetStatusNeedsAP'
AC_SET = 'ACDevSetStatusNewProtocol'
POWER_SKIP = ('airVo', 'nanoe', 'led', 'dust', 'gas', 'sensiTVOC',
              'childLock', 'lcdSwitch', 'fliterRemind')

class CloudError(RuntimeError):
    """Safe diagnostic containing no raw server response."""

    def __init__(self, message, *, stage='transport', reason='cloud', code=None):
        super().__init__(message)
        stages = {'transport', 'UsrGetToken', 'UsrLogin', 'UsrGetBindDevInfo', GET, AC_GET, ODM_GET, PURIFIER_SET, AC_SET}
        reasons = {'cloud', 'tls', 'network', 'response', 'http', 'certificate'}
        stage = stage if stage in stages else 'transport'
        reason = reason if reason in reasons else 'cloud'
        code = str(code) if type(code) in (int, str) and str(code).isdigit() and len(str(code)) <= 8 else None
        self.safe_detail = f'{stage} / {reason}' + (f' / {code}' if code else '')


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise CloudError('服务器重定向已拒绝；未向新地址转发凭据')


class Transport:
    def set_fridge_controls(self, identity, ssid, current, changes):
        parts = identity['deviceId'].split('_')
        if len(parts) != 3 or parts[1] != '0100':
            raise ValueError('Unsupported fridge target')
        params = build_fridge_params(current, changes)
        request = urllib.request.Request(BASE + 'FDevSetStatusInfo',
            data=json.dumps({'id': 1, **identity, 'params': params}).encode(), headers={
                'User-Agent': 'SmartApp', 'Content-Type': 'application/json',
                'Cookie': 'SSID=' + ssid, 'xtoken': 'SSID=' + ssid})
        try:
            with self.opener.open(request, timeout=15) as response:
                data = json.load(response)
            if not isinstance(data.get('results'), dict):
                raise ValueError('Missing results')
            return data['results']
        except Exception:
            raise CloudError('冰箱请求未确认；未自动重试') from None

    def get_fridge_status(self, identity, ssid):
        request = urllib.request.Request(BASE + 'FDevGetStatusInfo',
            data=json.dumps({'id': 1, **identity}).encode(), headers={
                'User-Agent': 'SmartApp', 'Content-Type': 'application/json',
                'Cookie': 'SSID=' + ssid})
        try:
            with self.opener.open(request, timeout=15) as response:
                data = json.load(response)
            if not isinstance(data.get('results'), dict):
                raise ValueError('Missing results')
            return data['results']
        except Exception:
            raise CloudError('冰箱只读查询失败；未自动重试') from None

    def __init__(self, certificate):
        context = ssl.create_default_context(cafile=str(certificate))
        # Python >=3.13 enables X509_STRICT. The exact legacy certificate the
        # user already trusts lacks modern CA constraints. Scope compatibility
        # to that certificate and this connection; retain CERT_REQUIRED and
        # hostname verification, expiry checks, modern TLS defaults and no redirects.
        fingerprint = hashlib.sha256(ssl.PEM_cert_to_DER_cert(
            Path(certificate).read_text(encoding='ascii'))).hexdigest()
        if fingerprint == 'a03226da8dd2ef0ea7e390232eed88d27d36c9e1a3208439f20a4c37eec35948':
            context.verify_flags &= ~ssl.VERIFY_X509_STRICT
        self.opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}), NoRedirect(), urllib.request.HTTPSHandler(context=context))

    def post(self, endpoint, params, ssid=None):
        if endpoint not in {'UsrGetToken', 'UsrLogin', 'UsrGetBindDevInfo', GET, AC_GET, ODM_GET}:
            raise CloudError('端点不在适配器允许列表中')
        return self._request(endpoint, params, ssid)

    def set_purifier_power(self, device_id, usr_id, ssid, value):
        return self.set_purifier_controls(device_id, usr_id, ssid, {'runSta': value})

    def set_purifier_extended(self, device_id, usr_id, ssid, changes):
        parts = device_id.split('_')
        if len(parts) != 3 or parts[1] != '0810':
            raise ValueError('Unsupported target')
        params = build_changes(changes)
        return self._request(PURIFIER_SET, {'usrId': usr_id, 'deviceId': device_id,
                             'token': gen_token(device_id), **params}, ssid)

    def set_purifier_controls(self, device_id, usr_id, ssid, changes):
        parts = device_id.split('_')
        if (len(parts) != 3 or parts[1] != '0810' or len(changes) != 1
                or set(changes) - {'runSta', 'nanoe', 'childLock', 'led', 'lcdSwitch', 'airVo'}
                or any(type(v) is not int or v not in ((2, 3, 4) if k == 'airVo' else (0, 1))
                       for k, v in changes.items())):
            raise CloudError('净化器控制参数不在允许范围内')
        params = {'usrId': usr_id, 'deviceId': device_id, 'token': gen_token(device_id),
                  **{key: 255 for key in POWER_SKIP}, 'runSta': 255, **changes}
        return self._request(PURIFIER_SET, params, ssid)

    def _request(self, endpoint, params, ssid):
        headers = {'User-Agent': 'SmartApp', 'Content-Type': 'application/json'}
        if ssid:
            headers['Cookie'] = 'SSID=' + ssid
        if endpoint in (AC_GET, AC_SET):
            headers.update({'xtoken': 'SSID=' + ssid,
                            'Origin': 'https://app.psmartcloud.com',
                            'X-Requested-With': 'XMLHttpRequest'})
            if endpoint == AC_SET:
                body = {'id': 200, **params}
            else:
                body = {'id': 100, **params}
        else:
            body = {'id': 1, 'uiVersion': 4.0, 'params': params}
        request = urllib.request.Request(BASE + endpoint, headers=headers,
            data=json.dumps(body).encode())
        try:
            with self.opener.open(request, timeout=15) as response:
                body = json.load(response)
        except urllib.error.HTTPError as error:
            raise CloudError('云端 HTTP 错误', stage=endpoint, reason='http', code=error.code) from None
        except (OSError, ValueError) as error:
            underlying = getattr(error, 'reason', error)
            reason = 'tls' if isinstance(underlying, ssl.SSLError) else ('response' if isinstance(error, ValueError) else 'network')
            raise CloudError('连接或响应验证失败；未自动重试', stage=endpoint, reason=reason) from None
        if not isinstance(body, dict) or not isinstance(body.get('results'), dict):
            error = body.get('error') if isinstance(body, dict) else None
            code = error.get('code') if isinstance(error, dict) else None
            raise CloudError('云端未返回有效结果', stage=endpoint, reason='cloud', code=code)
        return body['results']

    def set_ac_controls(self, device_id, usr_id, ssid, current, changes):
        parts = device_id.split('_')
        if len(parts) != 3 or parts[1] != '0900':
            raise CloudError('不允许控制此设备')
        params = build_ac_params(current, changes)
        # This model physically confirmed lamp control only when the NewProtocol
        # params contained the lamp field alone. Keep all existing validation.
        if set(changes) == {'lamp'}:
            params = {'lamp': changes['lamp']}
        elif changes == {'runStatus': 49}:
            # Candidate power-off fix: do not resend unrelated settings that can
            # interfere with this device's single-action NewProtocol requests.
            params = {'runStatus': 49}
        return self._request(AC_SET, {'deviceId': device_id, 'usrId': usr_id,
                                    'token': gen_token(device_id), 'params': params}, ssid)


def md5(value):
    return hashlib.md5(value.encode()).hexdigest().upper()

def gen_token(device_id: str) -> str | None:
    parts = device_id.split("_")
    if len(parts) != 3:
        return None
    mac, category, suffix = parts[0].upper(), parts[1].upper(), parts[2]
    inner = hashlib.sha512(
        (mac[6:] + "_" + category + "_" + mac[:6]).encode()
    ).hexdigest()
    return hashlib.sha512((inner + "_" + suffix).encode()).hexdigest()
