"""Command-line tool: esc-helper."""

from __future__ import annotations

import argparse
import difflib
import sys
from typing import Optional, Sequence

from . import __version__
from .checks import ERROR, WARNING, check_settings, load_settings
from .probe import ProbeError, read_firmware_version
from .protocol import FrameError, decode_packet, encode_packet
from .settings import GROUPS, SETTINGS, get_setting


def _parse_hex(text: str) -> bytes:
    cleaned = text.replace(" ", "").replace(":", "").replace("-", "")
    return bytes.fromhex(cleaned)


def _format_hex(data: bytes) -> str:
    return " ".join(f"{byte:02x}" for byte in data)


def _cmd_explain(args: argparse.Namespace) -> int:
    if args.key is None:
        for group in GROUPS:
            print(group)
            for setting in SETTINGS:
                if setting.group == group:
                    print(f"  {setting.key:<26} {setting.title}")
            print()
        return 0

    setting = get_setting(args.key)
    if setting is None:
        print(f"'{args.key}' is not in the notes yet.", file=sys.stderr)
        match = difflib.get_close_matches(args.key, [s.key for s in SETTINGS], n=1)
        if match:
            print(f"Did you mean {match[0]}?", file=sys.stderr)
        return 1

    print(setting.title)
    print(f"  key:  {setting.key}")
    if setting.unit:
        print(f"  unit: {setting.unit}")
    print()
    print(setting.explanation)
    if setting.note:
        print()
        print(f"Note: {setting.note}")
    return 0


def _cmd_check(args: argparse.Namespace) -> int:
    try:
        values = load_settings(args.file)
    except (OSError, ValueError) as exc:
        print(f"Could not read {args.file}: {exc}", file=sys.stderr)
        return 2

    findings = check_settings(
        values,
        max_motor_current=args.max_motor_current,
        max_battery_current=args.max_battery_current,
    )
    if not findings:
        print("No problems found. That does not mean these settings suit your motor.")
        return 0

    for finding in findings:
        print(f"{finding.level.upper():<8} {finding.message}")
    errors = sum(1 for finding in findings if finding.level == ERROR)
    warnings = sum(1 for finding in findings if finding.level == WARNING)
    print()
    print(f"{errors} error(s), {warnings} warning(s).")
    return 1 if errors else 0


def _cmd_probe(args: argparse.Namespace) -> int:
    try:
        version = read_firmware_version(args.port, timeout=args.timeout)
    except ProbeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Firmware version {version}")
    return 0


def _cmd_frame(args: argparse.Namespace) -> int:
    print(_format_hex(encode_packet(_parse_hex(" ".join(args.hex)))))
    return 0


def _cmd_decode(args: argparse.Namespace) -> int:
    try:
        payload = decode_packet(_parse_hex(" ".join(args.hex)))
    except FrameError as exc:
        print(f"Not a valid frame: {exc}", file=sys.stderr)
        return 1
    print(_format_hex(payload))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="esc-helper",
        description="Plain-language notes and read-only checks for VESC motor controller settings. Unofficial.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    explain = commands.add_parser("explain", help="explain a setting, or list them all")
    explain.add_argument("key", nargs="?", help="setting name, for example l_min_vin")
    explain.set_defaults(func=_cmd_explain)

    check = commands.add_parser("check", help="check a settings file (JSON) for mistakes")
    check.add_argument("file", help="JSON file that maps setting names to values")
    check.add_argument("--max-motor-current", type=float, metavar="A", help="your motor's current rating")
    check.add_argument("--max-battery-current", type=float, metavar="A", help="your battery's current rating")
    check.set_defaults(func=_cmd_check)

    probe = commands.add_parser("probe", help="ask a controller for its firmware version (read-only)")
    probe.add_argument("port", help="serial port, for example COM3")
    probe.add_argument("--timeout", type=float, default=2.0, help="seconds to wait for a reply")
    probe.set_defaults(func=_cmd_probe)

    frame = commands.add_parser("frame", help="wrap payload bytes (hex) in a VESC frame")
    frame.add_argument("hex", nargs="+", help="payload bytes in hex, for example 00 or 0a 1b")
    frame.set_defaults(func=_cmd_frame)

    decode = commands.add_parser("decode", help="check a frame (hex) and print its payload")
    decode.add_argument("hex", nargs="+", help="whole frame in hex, for example 02 01 00 00 00 03")
    decode.set_defaults(func=_cmd_decode)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
