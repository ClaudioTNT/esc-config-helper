import unittest

from esc_config_helper.settings import GROUPS, SETTINGS, get_setting


class GlossaryTests(unittest.TestCase):
    def test_keys_are_unique(self):
        keys = [setting.key for setting in SETTINGS]
        self.assertEqual(len(keys), len(set(keys)))

    def test_every_entry_has_text_and_a_known_group(self):
        for setting in SETTINGS:
            with self.subTest(key=setting.key):
                self.assertTrue(setting.title)
                self.assertTrue(setting.explanation)
                self.assertIn(setting.group, GROUPS)

    def test_text_is_plain_ascii(self):
        # Keep the notes ASCII so they print correctly in any Windows console.
        for setting in SETTINGS:
            with self.subTest(key=setting.key):
                self.assertTrue(setting.explanation.isascii())
                self.assertTrue(setting.note.isascii())

    def test_lookup(self):
        self.assertEqual(get_setting("l_min_vin").unit, "V")
        self.assertIsNone(get_setting("not_a_setting"))

    def test_settings_the_checks_use_are_documented(self):
        for key in (
            "l_min_vin", "l_max_vin", "l_battery_cut_start", "l_battery_cut_end",
            "l_temp_fet_start", "l_temp_fet_end", "l_temp_motor_start", "l_temp_motor_end",
            "l_current_max", "l_current_min", "l_abs_current_max", "l_in_current_max",
            "l_in_current_min", "l_watt_max", "l_watt_min", "l_max_erpm", "l_min_erpm",
            "si_motor_poles", "motor_type", "sensor_mode",
            "foc_motor_r", "foc_motor_l", "foc_motor_flux_linkage",
        ):
            with self.subTest(key=key):
                self.assertIsNotNone(get_setting(key))


if __name__ == "__main__":
    unittest.main()
