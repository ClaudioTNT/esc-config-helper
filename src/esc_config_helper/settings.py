"""Plain-language notes for VESC motor controller settings.

Each entry was checked against the VESC firmware source (vedderb/bldc, default
branch, checked 2026-11-14) for its name, unit, sign convention, and what the
firmware does with it. Firmware defaults are left out on purpose: hardware
definitions change them, so read the values for your hardware in VESC Tool.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

GROUPS = (
    "Current",
    "Power",
    "Voltage",
    "Battery cut-off",
    "Temperature",
    "Speed",
    "Motor",
    "Set by motor detection",
)


@dataclass(frozen=True)
class Setting:
    key: str
    title: str
    group: str
    unit: str
    explanation: str
    note: str = ""


SETTINGS = (
    Setting(
        key="l_current_max",
        title="Motor current limit (driving)",
        group="Current",
        unit="A",
        explanation=(
            "The most current the controller will send into the motor while it drives, "
            "in amps. More current gives more torque and more heat."
        ),
        note=(
            "Keep it within what the motor, wiring and connectors can take. "
            "The controller also lowers this limit as its temperature rises."
        ),
    ),
    Setting(
        key="l_current_min",
        title="Motor current limit (braking)",
        group="Current",
        unit="A",
        explanation=(
            "The most current the controller will push back into the motor while braking. "
            "Braking current is entered as a negative number."
        ),
        note="A positive value here is almost always a sign mistake.",
    ),
    Setting(
        key="l_abs_current_max",
        title="Absolute current limit",
        group="Current",
        unit="A",
        explanation=(
            "A hard limit on the size of the motor current in either direction. "
            "If the current goes above it, the controller raises a fault."
        ),
        note=(
            "Enter a positive number. Keep it at or above the other motor current limits, "
            "or the fault will trigger before they apply."
        ),
    ),
    Setting(
        key="l_in_current_max",
        title="Battery current limit (driving)",
        group="Current",
        unit="A",
        explanation="The most current the controller will draw from the battery while driving, in amps.",
        note="The battery and its protection must handle this current. Check the battery's discharge rating.",
    ),
    Setting(
        key="l_in_current_min",
        title="Battery current limit (braking)",
        group="Current",
        unit="A",
        explanation=(
            "The most current the controller will send back into the battery while braking. "
            "Enter it as a negative number."
        ),
        note="Many batteries limit charging current. Check the battery's charge rating before raising this.",
    ),
    Setting(
        key="l_watt_max",
        title="Power limit (driving)",
        group="Power",
        unit="W",
        explanation=(
            "The most power the controller will draw from the battery while driving, in watts. "
            "It converts this to a battery current using the measured input voltage."
        ),
        note="This is battery-side power, not the power delivered at the motor shaft.",
    ),
    Setting(
        key="l_watt_min",
        title="Power limit (braking)",
        group="Power",
        unit="W",
        explanation=(
            "The most power the controller will return to the battery while braking, in watts. "
            "Enter it as a negative number."
        ),
    ),
    Setting(
        key="l_min_vin",
        title="Minimum input voltage",
        group="Voltage",
        unit="V",
        explanation=(
            "If the battery voltage stays below this value for long enough, the controller "
            "trips a fault and stops driving the motor."
        ),
        note="The value is for the whole pack, not per cell.",
    ),
    Setting(
        key="l_max_vin",
        title="Maximum input voltage",
        group="Voltage",
        unit="V",
        explanation=(
            "If the battery voltage stays above this value for long enough, the controller "
            "trips an over-voltage fault. Braking can push the voltage up."
        ),
        note=(
            "The value is for the whole pack. The hardware definition can limit the value "
            "you enter."
        ),
    ),
    Setting(
        key="l_battery_cut_start",
        title="Battery cut-off start",
        group="Battery cut-off",
        unit="V",
        explanation=(
            "The pack voltage where the controller starts reducing battery current, to protect "
            "the battery. Above this voltage the limit is not reduced."
        ),
        note=(
            "Must be higher than the cut-off end. The firmware does not check this, and a "
            "reversed pair turns the gradual reduction into a sudden step."
        ),
    ),
    Setting(
        key="l_battery_cut_end",
        title="Battery cut-off end",
        group="Battery cut-off",
        unit="V",
        explanation=(
            "The pack voltage where battery current is reduced to zero. Between the start and "
            "end voltages, the limit ramps down."
        ),
        note="The value is for the whole pack. The controller uses a filtered voltage reading.",
    ),
    Setting(
        key="l_temp_fet_start",
        title="Controller temperature derating start",
        group="Temperature",
        unit="degrees C",
        explanation=(
            "The temperature where the controller starts lowering its current limit, to protect "
            "the power transistors. The limit falls gradually from here to the cut-off temperature."
        ),
        note="Must be lower than the cut-off temperature. Hardware definitions set their own starting values.",
    ),
    Setting(
        key="l_temp_fet_end",
        title="Controller temperature cut-off",
        group="Temperature",
        unit="degrees C",
        explanation="The temperature where the current limit reaches zero and the controller trips a fault.",
        note="Must be higher than the derating start.",
    ),
    Setting(
        key="l_temp_motor_start",
        title="Motor temperature derating start",
        group="Temperature",
        unit="degrees C",
        explanation=(
            "The motor temperature where the controller starts lowering its current limit. "
            "The limit falls gradually to the cut-off temperature."
        ),
        note="Must be lower than the motor cut-off temperature.",
    ),
    Setting(
        key="l_temp_motor_end",
        title="Motor temperature cut-off",
        group="Temperature",
        unit="degrees C",
        explanation="The motor temperature where the controller trips a fault and stops driving the motor.",
        note="Must be higher than the motor derating start.",
    ),
    Setting(
        key="l_max_erpm",
        title="Forward speed limit",
        group="Speed",
        unit="ERPM",
        explanation=(
            "The highest forward speed the controller allows, in electrical RPM. "
            "Mechanical RPM is electrical RPM divided by the pole pairs."
        ),
        note="Exceeding it can trip an overspeed fault. Enter a positive number.",
    ),
    Setting(
        key="l_min_erpm",
        title="Reverse speed limit",
        group="Speed",
        unit="ERPM",
        explanation=(
            "The highest reverse speed the controller allows, in electrical RPM. "
            "Enter it as a negative number."
        ),
    ),
    Setting(
        key="si_motor_poles",
        title="Motor poles",
        group="Motor",
        unit="poles",
        explanation=(
            "The number of magnets in the motor, not the number of pole pairs. The controller "
            "halves it to get the pole pairs it uses to convert electrical speed into mechanical speed."
        ),
        note="Use your motor's magnet count. A wrong value makes speed readings wrong.",
    ),
    Setting(
        key="motor_type",
        title="Motor type",
        group="Motor",
        unit="",
        explanation=(
            "How the controller drives the motor. 0 is BLDC, 1 is DC, and 2 is FOC. "
            "FOC is the firmware default."
        ),
        note="Motor detection can also set this value.",
    ),
    Setting(
        key="sensor_mode",
        title="Position sensor mode",
        group="Motor",
        unit="",
        explanation=(
            "For the BLDC driver: 0 is sensorless, 1 is sensored (for example Hall sensors), "
            "and 2 is hybrid. FOC uses its own foc_sensor_mode setting instead."
        ),
        note="Match this to how the sensor is actually wired.",
    ),
    Setting(
        key="foc_motor_r",
        title="Motor resistance",
        group="Set by motor detection",
        unit="ohm",
        explanation="The motor's phase resistance. Motor detection measures it.",
        note="Do not type in a number from a datasheet. Run motor detection in VESC Tool instead.",
    ),
    Setting(
        key="foc_motor_l",
        title="Motor inductance",
        group="Set by motor detection",
        unit="H",
        explanation=(
            "The motor's inductance, measured by motor detection. It is stored in henries, "
            "not microhenries."
        ),
        note="Do not type in a value by hand. Run motor detection in VESC Tool instead.",
    ),
    Setting(
        key="foc_motor_flux_linkage",
        title="Motor flux linkage",
        group="Set by motor detection",
        unit="Wb",
        explanation=(
            "How strongly the motor's magnets link with its windings. Motor detection measures "
            "it, in webers."
        ),
        note="Do not type in a value by hand. Run motor detection in VESC Tool instead.",
    ),
)

_BY_KEY = {setting.key: setting for setting in SETTINGS}


def get_setting(key: str) -> Optional[Setting]:
    """Return the note for a setting name, or None if the tool does not cover it yet."""
    return _BY_KEY.get(key)
