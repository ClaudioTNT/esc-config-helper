import unittest
from pathlib import Path

from esc_config_helper.checks import ERROR, WARNING, check_settings, load_settings

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def messages(findings):
    return [finding.message for finding in findings]


class CheckTests(unittest.TestCase):
    def test_good_example_has_no_findings(self):
        findings = check_settings(load_settings(str(EXAMPLES / "settings_ok.json")))
        self.assertEqual(findings, [])

    def test_mistakes_example_is_flagged(self):
        findings = check_settings(load_settings(str(EXAMPLES / "settings_with_mistakes.json")))
        text = " ".join(messages(findings))
        self.assertIn("Minimum input voltage must be lower", text)
        self.assertIn("Battery cut-off end must be lower", text)
        self.assertIn("Controller derating must start below", text)
        self.assertIn("should be negative", text)
        self.assertIn("Motor poles should be", text)
        self.assertIn("Absolute current limit", text)
        self.assertIn("must be a number", text)
        self.assertIn("Did you mean l_current_max", text)
        self.assertIn("Set by motor detection", text)
        self.assertTrue(any(finding.level == ERROR for finding in findings))

    def test_reversed_battery_cut_is_an_error(self):
        findings = check_settings({"l_battery_cut_start": 39, "l_battery_cut_end": 42})
        self.assertEqual([finding.level for finding in findings], [ERROR])

    def test_limits_in_the_right_order_pass(self):
        findings = check_settings({"l_min_vin": 36, "l_max_vin": 60})
        self.assertEqual(findings, [])

    def test_rating_option_flags_current_above_the_rating(self):
        self.assertEqual(check_settings({"l_current_max": 40}), [])
        findings = check_settings({"l_current_max": 40}, max_motor_current=35)
        self.assertEqual([finding.level for finding in findings], [ERROR])

    def test_booleans_are_not_numbers(self):
        findings = check_settings({"l_current_max": True})
        self.assertEqual([finding.level for finding in findings], [ERROR])

    def test_odd_pole_count_is_a_warning(self):
        findings = check_settings({"si_motor_poles": 7})
        self.assertEqual([finding.level for finding in findings], [WARNING])

    def test_even_pole_count_passes(self):
        self.assertEqual(check_settings({"si_motor_poles": 14}), [])

    def test_braking_current_with_the_wrong_sign_is_an_error(self):
        findings = check_settings({"l_current_min": 10})
        self.assertEqual([finding.level for finding in findings], [ERROR])


if __name__ == "__main__":
    unittest.main()
