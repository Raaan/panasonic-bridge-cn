"""Offline regression coverage for Fridge-19 bounds and coupled controls."""
import importlib
from pathlib import Path
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'custom_components' / 'panasonic_home_readonly'
package = types.ModuleType('fridge_review_test')
package.__path__ = [str(ROOT)]
sys.modules[package.__name__] = package
protocol = importlib.import_module(package.__name__ + '.fridge_protocol')


class FridgeProtocolTests(unittest.TestCase):
    def setUp(self):
        self.current = dict.fromkeys(protocol.OFFICIAL_FRIDGE19_FIELDS, 0)
        self.current.update(PCTempSet=4, SCS1TempSet=0, FCTempSet=-20)

    def test_switch_preserves_three_temperature_targets(self):
        result = protocol.build_fridge_params(self.current, {'ecoNaviSet': 1})
        for key in protocol.FRIDGE_TEMPERATURES:
            self.assertEqual(result[key], self.current[key])
        self.assertEqual(result['ecoNaviSet'], 1)
        self.assertEqual(result['isTodoLimit'], 1)
        self.assertEqual(len(result), 25)

    def test_quick_icing_clears_conflicting_modes(self):
        self.current.update(icingStop=1, freshFrozen=1)
        result = protocol.build_fridge_params(self.current, {'quickicing': 1})
        self.assertEqual((result['quickicing'], result['icingStop'], result['freshFrozen']), (1, 0, 0))

    def test_stop_and_fresh_frozen_clear_quick_icing(self):
        self.current['quickicing'] = 1
        for key in ('icingStop', 'freshFrozen'):
            with self.subTest(key=key):
                result = protocol.build_fridge_params(self.current, {key: 1})
                self.assertEqual(result['quickicing'], 0)
                self.assertEqual(result[key], 1)

    def test_switch_off_does_not_clear_other_modes(self):
        self.current['freshFrozen'] = 1
        result = protocol.build_fridge_params(self.current, {'quickicing': 0})
        self.assertEqual(result['freshFrozen'], 1)

    def test_temperature_limits(self):
        for key, (_, low, high) in protocol.FRIDGE_TEMPERATURES.items():
            for value in (low, high):
                with self.subTest(key=key, value=value):
                    self.assertEqual(protocol.build_fridge_params(self.current, {key: value})[key], value)
            for value in (low - 1, high + 1, True, 1.5):
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    protocol.build_fridge_params(self.current, {key: value})

    def test_missing_temperature_baseline_rejects_write(self):
        for key in protocol.FRIDGE_TEMPERATURES:
            current = self.current.copy()
            del current[key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                protocol.build_fridge_params(current, {'nanoe': 1})

    def test_unknown_switch_baseline_rejects_write(self):
        for value in (None, True, '0', 2):
            self.current['nanoe'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                protocol.build_fridge_params(self.current, {'nanoe': 1})

    def test_rejects_unknown_and_multiple_targets(self):
        for changes in ({}, {'unknown': 1}, {'nanoe': 1, 'ecoNaviSet': 1}, {'nanoe': True}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                protocol.build_fridge_params(self.current, changes)

    def test_does_not_copy_readonly_or_identity_fields(self):
        self.current.update(PCTempCur=6, deviceId='synthetic-device', token='synthetic-token')
        result = protocol.build_fridge_params(self.current, {'nanoe': 1})
        self.assertFalse({'PCTempCur', 'deviceId', 'token'} & result.keys())

    def test_missing_optional_field_uses_documented_zero_default(self):
        del self.current['vacation']
        result = protocol.build_fridge_params(self.current, {'nanoe': 1})
        self.assertEqual(result['vacation'], 0)


if __name__ == '__main__':
    unittest.main()
