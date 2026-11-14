# esc-config-helper

Plain-language notes and read-only checks for VESC motor controller settings.

> **Unofficial.** This project is not made by, or affiliated with, the VESC
> Project. VESC is a registered trademark of Benjamin Vedder. The project
> contains no VESC code. It describes VESC settings and the serial protocol,
> which were checked against the public firmware source.

## What it does

- `esc-helper explain` gives a plain-language note on a setting: its unit, what
  it does, and what to watch for.
- `esc-helper check` looks through a settings file for mistakes the firmware
  would accept without complaint: reversed limits, sign errors, and misspelled
  names.
- `esc-helper probe` asks a connected controller for its firmware version. It
  only reads.
- `esc-helper frame` and `esc-helper decode` build and check raw serial frames,
  which helps when debugging.

## What it does not do yet

- It does not write settings to a controller. Make changes in the official VESC
  Tool.
- It does not read VESC Tool's own configuration files. Settings files are plain
  JSON, described below.
- It has no graphical interface.
- It has been tested with unit tests only, not with a real controller.

## Install

Requires Python 3.9 or newer.

```bash
python -m pip install -e .
```

The firmware-version probe also needs pyserial:

```bash
python -m pip install pyserial
```

## Use

```bash
esc-helper explain
```

```bash
esc-helper explain l_battery_cut_start
```

```bash
esc-helper check examples/settings_with_mistakes.json
```

```bash
esc-helper check examples/settings_with_mistakes.json --max-motor-current 35
```

```bash
esc-helper probe COM3
```

## Settings files

A settings file is a JSON object that maps setting names to numbers:

```json
{
  "l_current_max": 40,
  "l_current_min": -40
}
```

The files in `examples/` are for trying the checker. Their values are not
recommendations for any motor.

## What the checks cover

- Voltage and temperature limits in the wrong order.
- Battery cut-off start and end reversed.
- Braking limits and speed limits with the wrong sign.
- An absolute current limit below a normal current limit.
- An odd pole count.
- Names that look like typos.
- Your own current ratings, if you pass `--max-motor-current` or
  `--max-battery-current`.

A clean result does not mean the settings suit your motor.

## How the facts were checked

On 2026-11-14, the setting names, units, sign conventions, and serial framing
were checked by reading the default branch of the VESC firmware source
(vedderb/bldc). Nothing was run on hardware. Firmware versions differ, and
hardware definitions change default values, so check your own firmware and
hardware. The details are in [docs/protocol.md](docs/protocol.md).

## Safety

- Secure the motor and its load before changing settings.
- Change one setting at a time, and write down the old value.
- Make changes in the official VESC Tool, after reading its documentation.
- Do not treat a clean `check` result as proof that a setting is safe.

See [docs/troubleshooting.md](docs/troubleshooting.md) for common symptoms.

## Development

```bash
python -m unittest discover -s tests
```

## Project layout

- `src/esc_config_helper/`: the package
- `tests/`: unit tests
- `examples/`: sample settings files
- `docs/`: troubleshooting and protocol notes

## Status

Version 0.1.0. Early and small. Ideas for later: importing VESC Tool
configuration files, a simple interface, and more setting notes.

## License

MIT. See [LICENSE](LICENSE).
