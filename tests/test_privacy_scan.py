"""Synthetic regression fixtures. No real user or network identity data."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

PATH = Path(__file__).resolve().parents[1] / 'tools' / 'privacy_scan.py'
spec = importlib.util.spec_from_file_location('privacy_review_test', PATH)
scanner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = scanner
spec.loader.exec_module(scanner)


class PrivacyScanTests(unittest.TestCase):
    def rules(self, text):
        return {f.rule for f in scanner.scan_text(text)}

    def test_rejects_rfc1918_ranges(self):
        for prefix in ('192' + '.168', '10' + '.2', '172' + '.16', '172' + '.31'):
            with self.subTest(prefix=prefix):
                self.assertIn('network-address', self.rules(prefix + '.3.4'))

    def test_allows_loopback(self):
        self.assertNotIn('network-address', self.rules('127' + '.0.0.1'))

    def test_detects_mac_and_device_identifier(self):
        mac = ':'.join(['02', '00', '00', '00', '00', '01'])
        self.assertIn('device-mac', self.rules(mac))
        self.assertIn('device-mac', self.rules(mac.replace(':', '') + '_0810_test'))

    def test_allows_only_declared_synthetic_macs(self):
        self.assertFalse(self.rules('AABBCCDDEEFF_0810_test 112233445566_0900_test'))
        self.assertFalse(self.rules(':'.join(['00'] * 6)))

    def test_detects_phone(self):
        self.assertIn('phone-number', self.rules('138' + '00000000'))

    def test_detects_email_but_allows_documentation_domain(self):
        self.assertIn('email-address', self.rules('person@' + 'mail.test'))
        self.assertNotIn('email-address', self.rules('person@example.com'))

    def test_detects_paths(self):
        for value in ('C:' + '\\Users\\Example\\file', '/home/' + 'example/file', '\\\\' + 'host\\share\\file'):
            self.assertIn('personal-path', self.rules(value))

    def test_detects_credentials_embedded_in_url(self):
        self.assertIn('credential-url', self.rules('https://' + 'person:example@example.invalid'))

    def test_detects_private_key(self):
        self.assertIn('private-key', self.rules('-----BEGIN ' + 'PRIVATE KEY-----'))

    def test_detects_access_token(self):
        self.assertIn('github-token', self.rules('ghp_' + 'a' * 36))

    def test_findings_do_not_contain_sensitive_value(self):
        value = '138' + '00000000'
        findings = scanner.scan_text('first line\n' + value, 'fixture.txt')
        self.assertEqual(findings[0].line, 2)
        self.assertNotIn(value, str(findings))

    def test_rejects_private_config_files(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / '.env'
            path.write_text('SYNTHETIC_FIXTURE=1', encoding='utf-8')
            self.assertIn('private-or-binary-file', {f.rule for f in scanner.scan_tree(root)})


if __name__ == '__main__':
    unittest.main()
