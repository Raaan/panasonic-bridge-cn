"""Bounded publication scanner. Findings contain locations, never matched data."""
from dataclasses import dataclass
import ipaddress
from pathlib import Path
import re


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    rule: str


SYNTHETIC_MACS = {'000000000000', 'aabbccddeeff', '112233445566'}
PATTERNS = {
    'private-key': r'-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?' + r'PRIVATE KEY-----',
    'jwt': r'eyJ[A-Za-z0-9_-]{10,}\.' + r'[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+',
    'github-token': r'(?:gh[pousr]_' + r'[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})',
    'phone-number': r'(?<![A-Za-z0-9])(?:\+?86[ -]?)?1[3-9]\d{9}(?![A-Za-z0-9])',
    'personal-path': r'(?i)(?:[a-z]:[\\/](?:users|panasonichomecontrol)[\\/]|/(?:home|users)/[^/\s]+/|\\\\[a-z0-9][a-z0-9._-]*\\[a-z0-9$][a-z0-9$._-]*)',
    'credential-url': r'https?://[^\s/:@]+:[^\s/@]+@',
}
FORBIDDEN_SUFFIXES = {'.apk', '.dex', '.vmdk', '.vmem', '.log', '.db', '.sqlite', '.pfx', '.p12', '.key'}
FORBIDDEN_NAMES = {'secrets.yaml', 'configuration.yaml', 'automations.yaml', 'scripts.yaml', '.env'}


def scan_text(content, path='<memory>'):
    findings = []

    def add(position, rule):
        findings.append(Finding(path, content.count('\n', 0, position) + 1, rule))

    for rule, pattern in PATTERNS.items():
        for match in re.finditer(pattern, content):
            add(match.start(), rule)
    for match in re.finditer(r'(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])', content):
        try:
            address = ipaddress.IPv4Address(match.group())
        except ipaddress.AddressValueError:
            continue
        if not address.is_loopback:
            add(match.start(), 'network-address')
    mac_patterns = (r'(?i)(?<![\da-f])(?:[\da-f]{2}[:-]){5}[\da-f]{2}(?![\da-f])',
                    r'(?i)\b[\da-f]{12}(?=_[0-9]{4}_)')
    for pattern in mac_patterns:
        for match in re.finditer(pattern, content):
            normalized = re.sub('[:-]', '', match.group()).lower()
            if normalized not in SYNTHETIC_MACS:
                add(match.start(), 'device-mac')
    for match in re.finditer(r'(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b', content):
        domain = match.group().split('@')[1].lower()
        if domain not in {'example.com', 'example.org'} and not domain.endswith(('.invalid', '.example')):
            add(match.start(), 'email-address')
    return findings


def scan_tree(root):
    root = Path(root)
    findings = []
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root)
        if any(part in {'__pycache__', '.git'} for part in relative.parts):
            continue
        if path.is_symlink():
            findings.append(Finding(relative.as_posix(), 0, 'symlink'))
            continue
        if not path.is_file():
            continue
        name = relative.as_posix()
        if (path.suffix.lower() in FORBIDDEN_SUFFIXES or path.name in FORBIDDEN_NAMES
                or path.name.startswith('.env.') or '.storage' in relative.parts
                or path.name.endswith('.credential.xml') or path.name.startswith('.panasonic-')):
            findings.append(Finding(name, 0, 'private-or-binary-file'))
        try:
            content = path.read_text(encoding='utf-8-sig')
        except UnicodeError:
            findings.append(Finding(name, 0, 'unexpected-binary'))
            continue
        findings.extend(scan_text(content, name))
    return findings


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    findings = scan_tree(root)
    if findings:
        raise SystemExit('\n'.join(f'{f.path}:{f.line}: {f.rule}' for f in findings))
    print('PASS: bounded privacy scan; no matching values printed.')
