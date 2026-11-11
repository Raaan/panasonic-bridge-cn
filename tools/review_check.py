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
if manifest['domain'] != 'panasonic_home_readonly' or manifest['version'] != '0.5.1.dev0':
    errors.append('Unexpected domain/version migration in review package')
baseline = json.loads((ROOT / 'docs' / 'baseline-files.json').read_text(encoding='utf-8'))
change_record = json.loads((ROOT / 'docs' / 'source-changes.json').read_text(encoding='utf-8'))
changes = {item['file']: item for item in change_record['changes']}
for item in baseline:
    path = COMPONENT / item['file']
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != item['sha256']:
        change = changes.get(item['file'])
        if (change is None or change['baseline_sha256'] != item['sha256']
                or change['sha256'] != digest or not change.get('reason')):
            errors.append(f'Unrecorded change from runtime baseline: {item["file"]}')
for item in json.loads((ROOT / 'docs' / 'control-payload-baseline.json').read_text(encoding='utf-8')):
    content = (COMPONENT / item['file']).read_text(encoding='utf-8')
    functions = [node for node in ast.walk(ast.parse(content))
                 if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == item['function']]
    if len(functions) != 1 or hashlib.sha256(ast.get_source_segment(content, functions[0]).encode()).hexdigest() != item['sha256']:
        errors.append(f'Control/request method changed: {item["file"]}:{item["function"]}')
english = json.loads((COMPONENT / 'translations/en.json').read_text(encoding='utf-8'))
chinese = json.loads((COMPONENT / 'translations/zh-Hans.json').read_text(encoding='utf-8'))
def schema_paths(value, prefix=''):
    if isinstance(value, dict):
        return {path for key, item in value.items() for path in schema_paths(item, prefix + '/' + key)}
    return {prefix}
if schema_paths(english) != schema_paths(chinese) or '{detail}' not in english['config']['error']['cannot_connect']:
    errors.append('Configuration translations do not preserve schema/placeholders')
certificate = COMPONENT / 'panasonic-cloud.pem'
der = ssl.PEM_cert_to_DER_cert(certificate.read_text(encoding='ascii'))
fingerprint = hashlib.sha256(der).hexdigest()
if fingerprint != 'a03226da8dd2ef0ea7e390232eed88d27d36c9e1a3208439f20a4c37eec35948':
    errors.append('Unexpected certificate fingerprint')
if errors:
    raise SystemExit('\n'.join(errors))
print(f'PASS: {len(baseline)} baseline files with {len(changes)} recorded changes; unchanged control/request methods; translations; syntax; privacy scan; certificate fingerprint.')
print('Manual provenance, privacy, HA runtime and physical device review remain separate.')
