"""Certificate replacement must fail before a transport can send credentials."""
import importlib
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / 'custom_components' / 'panasonic_home_readonly'
package = types.ModuleType('certificate_review_test')
package.__path__ = [str(ROOT)]
sys.modules[package.__name__] = package
transport = importlib.import_module(package.__name__ + '.transport')


class CertificateTests(unittest.TestCase):
    def test_replacement_is_rejected_before_creating_context(self):
        with patch.object(transport.ssl, 'PEM_cert_to_DER_cert', return_value=b'synthetic-replacement'), \
             patch.object(transport.ssl, 'create_default_context') as context, \
             patch.object(transport.urllib.request, 'build_opener') as opener:
            with self.assertRaises(transport.CloudError) as error:
                transport.Transport(ROOT / 'panasonic-cloud.pem')
            self.assertEqual(error.exception.safe_detail, 'transport / certificate')
            context.assert_not_called()
            opener.assert_not_called()

    def test_malformed_certificate_does_not_leak_contents(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'synthetic.pem'
            path.write_text('synthetic-private-fixture', encoding='ascii')
            with self.assertRaises(transport.CloudError) as error:
                transport.Transport(path)
            self.assertNotIn('synthetic-private-fixture', str(error.exception))
            self.assertEqual(error.exception.safe_detail, 'transport / certificate')

    def test_missing_certificate_returns_safe_error(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(transport.CloudError) as error:
                transport.Transport(Path(root) / 'missing.pem')
            self.assertNotIn(root, str(error.exception))

    def test_non_ascii_certificate_returns_safe_error(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'synthetic.pem'
            path.write_bytes(bytes([255, 254, 253]))
            with self.assertRaises(transport.CloudError):
                transport.Transport(path)


if __name__ == '__main__':
    unittest.main()
