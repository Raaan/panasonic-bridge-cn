"""Offline packaging checks; never reads credentials or calls the network.

This bounded pattern scan is not a guarantee that all sensitive data is absent.
"""
import ast
import hashlib
import json
from pathlib import Path
import re
import ssl
from privacy_scan import scan_tree

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / 'custom_components' / 'panasonic_home_readonly'
errors = []
errors.extend(f'{f.path}:{f.line}: {f.rule}' for f in scan_tree(ROOT))
for path in sorted(ROOT.rglob('*')):
    if not path.is_file() or '__pycache__' in path.parts or '.git' in path.parts:
        continue
    relative = path.relative_to(ROOT).as_posix()
    forbidden = {'.apk', '.dex', '.vmdk', '.vmem', '.log', '.db', '.sqlite', '.pfx', '.p12', '.key'}
    if path.suffix.lower() in forbidden or path.name in {'secrets.yaml', 'configuration.yaml', 'automations.yaml', 'scripts.yaml'}:
        errors.append(f'Forbidden publication file: {relative}')
    try:
        content = path.read_text(encoding='utf-8-sig')
    except UnicodeError:
        errors.append(f'Unexpected binary file: {relative}')
        continue
    if path.suffix == '.py':
        ast.parse(content, filename=relative)
    if path.suffix == '.json':
        json.loads(content)
    # Regex strings are assembled so the checker does not flag its own source.
    patterns = {
        'private key': r'-----BEGIN (?:RSA |EC |OPENSSH )?' + r'PRIVATE KEY-----',
        'JWT': r'eyJ[A-Za-z0-9_-]{10,}\.' + r'[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+',
        'GitHub token': r'(?:gh[pousr]_' + r'[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})',
        'private IPv4': r'\b(?:192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3})\b',
        'Windows personal path': r'[A-Za-z]:\\' + r'(?:Users|PanasonicHomeControl)\\',
    }
    for label, pattern in patterns.items():
        if re.search(pattern, content):
            errors.append(f'{label}: {relative}')

manifest = json.loads((COMPONENT / 'manifest.json').read_text(encoding='utf-8'))
if manifest['domain'] != 'panasonic_home_readonly' or manifest['version'] != '0.5.0':
    errors.append('Unexpected domain/version migration in review package')
baseline = json.loads((ROOT / 'docs' / 'baseline-files.json').read_text(encoding='utf-8'))
for item in baseline:
    path = COMPONENT / item['file']
    if item['file'] != 'manifest.json' and hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
        errors.append(f'Runtime source differs from server: {item["file"]}')
certificate = COMPONENT / 'panasonic-cloud.pem'
der = ssl.PEM_cert_to_DER_cert(certificate.read_text(encoding='ascii'))
fingerprint = hashlib.sha256(der).hexdigest()
if fingerprint != 'a03226da8dd2ef0ea7e390232eed88d27d36c9e1a3208439f20a4c37eec35948':
    errors.append('Unexpected certificate fingerprint')
if errors:
    raise SystemExit('\n'.join(errors))
print(f'PASS: {len(baseline)} baseline files; Python/JSON syntax; bounded sensitive-pattern scan; certificate fingerprint.')
print('Manual provenance, privacy, HA runtime and physical device review remain separate.')
