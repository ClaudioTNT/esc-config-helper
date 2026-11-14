import contextlib
import io
import unittest
from pathlib import Path

from esc_config_helper.cli import main

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


class CliTests(unittest.TestCase):
    def test_frame_prints_the_firmware_request(self):
        code, out, _ = run(["frame", "00"])
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "02 01 00 00 00 03")

    def test_decode_prints_the_payload(self):
        code, out, _ = run(["decode", "02 01 00 00 00 03"])
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "00")

    def test_decode_accepts_unquoted_hex_bytes(self):
        code, out, _ = run(["decode", "02", "01", "00", "00", "00", "03"])
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "00")

    def test_decode_reports_a_bad_frame(self):
        code, _, err = run(["decode", "020100000004"])
        self.assertEqual(code, 1)
        self.assertIn("Not a valid frame", err)

    def test_explain_one_setting(self):
        code, out, _ = run(["explain", "l_min_vin"])
        self.assertEqual(code, 0)
        self.assertIn("Minimum input voltage", out)

    def test_explain_suggests_a_close_name(self):
        code, _, err = run(["explain", "l_min_vn"])
        self.assertEqual(code, 1)
        self.assertIn("l_min_vin", err)

    def test_explain_without_a_name_lists_settings(self):
        code, out, _ = run(["explain"])
        self.assertEqual(code, 0)
        self.assertIn("l_current_max", out)

    def test_check_passes_the_good_example(self):
        code, out, _ = run(["check", str(EXAMPLES / "settings_ok.json")])
        self.assertEqual(code, 0)
        self.assertIn("No problems found", out)

    def test_check_fails_the_mistakes_example(self):
        code, out, _ = run(["check", str(EXAMPLES / "settings_with_mistakes.json")])
        self.assertEqual(code, 1)
        self.assertIn("error(s)", out)

    def test_check_uses_the_motor_rating(self):
        code, _, _ = run(["check", str(EXAMPLES / "settings_ok.json"), "--max-motor-current", "30"])
        self.assertEqual(code, 1)

    def test_check_reports_a_missing_file(self):
        code, _, err = run(["check", str(EXAMPLES / "missing.json")])
        self.assertEqual(code, 2)
        self.assertIn("Could not read", err)


if __name__ == "__main__":
    unittest.main()
