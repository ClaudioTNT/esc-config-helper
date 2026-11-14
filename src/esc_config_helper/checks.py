"""Checks for a settings file.

These catch mistakes the firmware accepts without complaint: reversed limits,
sign errors, and misspelled names. A clean result does not mean the settings
suit your motor, and the checks do not replace the official VESC Tool.
"""

from __future__ import annotations

import difflib
import json
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Tuple

from .settings import SETTINGS, get_setting

ERROR = "error"
WARNING = "warning"
INFO = "info"

# (lower key, higher key, message). The first value must be lower than the second.
ORDERED_PAIRS = (
    (
        "l_min_vin",
        "l_max_vin",
        "Minimum input voltage must be lower than maximum input voltage.",
    ),
    (
        "l_battery_cut_end",
        "l_battery_cut_start",
        "Battery cut-off end must be lower than its start. Reversed, the current reduction becomes a sudden step.",
    ),
    (
        "l_temp_fet_start",
        "l_temp_fet_end",
        "Controller derating must start below the cut-off temperature.",
    ),
    (
        "l_temp_motor_start",
        "l_temp_motor_end",
        "Motor derating must start below the cut-off temperature.",
    ),
    (
        "l_min_erpm",
        "l_max_erpm",
        "Reverse speed limit must be lower than the forward speed limit.",
    ),
)

# (key, rule, message). The rule returns True when the value is acceptable.
SIGN_RULES = (
    ("l_current_max", lambda v: v >= 0, "Motor current limit (driving) should not be negative."),
    ("l_current_min", lambda v: v <= 0, "Motor current limit (braking) should be negative."),
    ("l_abs_current_max", lambda v: v > 0, "Absolute current limit should be a positive number."),
    ("l_in_current_max", lambda v: v >= 0, "Battery current limit (driving) should not be negative."),
    ("l_in_current_min", lambda v: v <= 0, "Battery current limit (braking) should be negative."),
    ("l_watt_max", lambda v: v >= 0, "Power limit (driving) should not be negative."),
    ("l_watt_min", lambda v: v <= 0, "Power limit (braking) should be negative."),
    ("l_max_erpm", lambda v: v > 0, "Forward speed limit should be positive."),
    ("l_min_erpm", lambda v: v < 0, "Reverse speed limit should be negative."),
)

DETECTED_KEYS = ("foc_motor_r", "foc_motor_l", "foc_motor_flux_linkage")


@dataclass(frozen=True)
class Finding:
    level: str
    message: str
    keys: Tuple[str, ...] = ()


def load_settings(path: str) -> Dict[str, Any]:
    """Read a settings file: a JSON object that maps setting names to values."""
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("the settings file must be a JSON object of name: value pairs")
    return data


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def check_settings(
    values: Mapping[str, Any],
    *,
    max_motor_current: Optional[float] = None,
    max_battery_current: Optional[float] = None,
) -> List[Finding]:
    """Return the problems found in a settings mapping. An empty list means none."""
    findings: List[Finding] = []
    numbers: Dict[str, float] = {}
    for key, value in values.items():
        if _is_number(value):
            numbers[key] = float(value)
        else:
            findings.append(Finding(ERROR, f"{key} must be a number.", (key,)))

    for low, high, message in ORDERED_PAIRS:
        if low in numbers and high in numbers and numbers[low] >= numbers[high]:
            findings.append(Finding(ERROR, message, (low, high)))

    for key, rule, message in SIGN_RULES:
        if key in numbers and not rule(numbers[key]):
            findings.append(Finding(ERROR, message, (key,)))

    absolute = numbers.get("l_abs_current_max")
    if absolute is not None and absolute > 0:
        for key in ("l_current_max", "l_current_min"):
            if key in numbers and abs(numbers[key]) > absolute:
                findings.append(
                    Finding(
                        WARNING,
                        f"Absolute current limit ({absolute:g} A) is below {key} "
                        f"({numbers[key]:g} A), so the controller can fault before that limit applies.",
                        ("l_abs_current_max", key),
                    )
                )

    poles = numbers.get("si_motor_poles")
    if poles is not None:
        if poles <= 0:
            findings.append(Finding(ERROR, "Motor poles must be a positive number.", ("si_motor_poles",)))
        elif poles != int(poles) or int(poles) % 2:
            findings.append(
                Finding(
                    WARNING,
                    "Motor poles should be a whole, even number. The controller halves it to get pole pairs.",
                    ("si_motor_poles",),
                )
            )

    if max_motor_current is not None and numbers.get("l_current_max", 0) > max_motor_current:
        findings.append(
            Finding(
                ERROR,
                f"l_current_max ({numbers['l_current_max']:g} A) is above the motor current rating "
                f"you entered ({max_motor_current:g} A).",
                ("l_current_max",),
            )
        )
    if max_battery_current is not None and numbers.get("l_in_current_max", 0) > max_battery_current:
        findings.append(
            Finding(
                ERROR,
                f"l_in_current_max ({numbers['l_in_current_max']:g} A) is above the battery current "
                f"rating you entered ({max_battery_current:g} A).",
                ("l_in_current_max",),
            )
        )

    detected = [key for key in DETECTED_KEYS if key in values]
    if detected:
        findings.append(
            Finding(
                INFO,
                "Set by motor detection, not by hand: " + ", ".join(detected)
                + ". Run motor detection in VESC Tool instead of typing values in.",
                tuple(detected),
            )
        )

    known = [setting.key for setting in SETTINGS]
    for key in values:
        if get_setting(key) is not None:
            continue
        match = difflib.get_close_matches(key, known, n=1)
        if match:
            findings.append(
                Finding(WARNING, f"{key} is not a known setting name. Did you mean {match[0]}?", (key,))
            )
        else:
            findings.append(Finding(INFO, f"{key} is not in this tool's notes yet.", (key,)))

    return findings
