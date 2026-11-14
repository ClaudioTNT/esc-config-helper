# Troubleshooting

This is a starting point, not a full manual. Use it together with the VESC
Project documentation and the instructions that came with your motor and
controller.

## Before you change anything

- Secure the motor and its load. Lift the wheel or remove the propeller first.
- Change one setting at a time, and write down the old value.
- Start with low current limits and raise them only after the basics work.
- This project does not write settings to a controller. Make changes in the
  official VESC Tool, then use `esc-helper check` on a copy of your settings to
  catch obvious mistakes.

## The controller does nothing when powered on

- Measure the voltage at the controller's input terminals while it is under
  load, not only at the battery.
- Check the connectors, switch, and fuse.
- Look at the minimum input voltage setting (`esc-helper explain l_min_vin`).
  If the battery voltage is below it, the controller will not drive the motor.

## The motor does not turn, or it stutters at start

- Check the phase wiring. A swapped pair of phase wires can make the motor
  vibrate or spin the wrong way.
- Check the sensor wiring (Hall sensors or an encoder) and that the sensor mode
  matches what is actually connected.
- Run the motor detection routine in the official VESC Tool with the motor free
  to turn.
- Check that the current limits are not set close to zero.

## Power cuts out or drops under load

- The battery may be reaching its cutoff. Check the battery cutoff settings
  (`esc-helper explain l_battery_cut_start`).
- The controller or motor may be hot. Temperature derating lowers the current
  limit as temperature rises.
- The current limits may be too low for the load.

## The controller or motor overheats

- Lower the motor current limit, reduce the load, or improve airflow and
  heatsinking.
- Check the temperature derating settings (`esc-helper explain l_temp_fet_start`).

## Braking feels wrong, or the voltage rises when braking

- Regenerative braking pushes energy back into the battery, which can raise
  the input voltage. Check the maximum input voltage setting.
- Check the braking current limits, which are negative numbers.

## Confirming the USB connection

`esc-helper probe COM3` asks the controller for its firmware version.
It only reads. It needs `pyserial` (`python -m pip install pyserial`).
