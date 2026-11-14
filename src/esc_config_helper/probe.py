"""Read-only probe: ask a connected controller for its firmware version.

Only the firmware-version request is sent. It is one command byte and changes
nothing on the controller. Opening a real serial port needs pyserial, which is
optional: python -m pip install pyserial
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from .protocol import COMM_FW_VERSION, FrameParser, firmware_version_request

# USB serial ports generally ignore the baud rate, but pyserial needs one.
BAUD_RATE = 115200


class ProbeError(RuntimeError):
    """The controller did not answer the way the probe expects."""


@dataclass(frozen=True)
class FirmwareVersion:
    major: int
    minor: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}"


def parse_firmware_version(payload: bytes) -> FirmwareVersion:
    """Read the version from a firmware-version reply payload.

    Byte 0 is the command ID, byte 1 is the major version, and byte 2 is the
    minor version. Later bytes hold more data that this tool does not read yet.
    """
    if len(payload) < 3 or payload[0] != COMM_FW_VERSION:
        raise ProbeError("reply is not a firmware-version reply")
    return FirmwareVersion(major=payload[1], minor=payload[2])


def read_firmware_version(port_name: str, timeout: float = 2.0, connection=None) -> FirmwareVersion:
    """Send a firmware-version request and wait for the reply.

    Pass an open connection to use something other than a serial port, such as
    in tests. Otherwise the port is opened here and closed again.
    """
    owns_connection = connection is None
    if owns_connection:
        connection = _open_serial(port_name)
    try:
        connection.write(firmware_version_request())
        parser = FrameParser()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for payload in parser.feed(connection.read(64)):
                if payload and payload[0] == COMM_FW_VERSION:
                    return parse_firmware_version(payload)
        raise ProbeError(f"no firmware-version reply within {timeout:g} seconds")
    finally:
        if owns_connection:
            connection.close()


def _open_serial(port_name: str):
    try:
        import serial  # pyserial, optional
    except ImportError as exc:
        raise ProbeError("pyserial is needed for the probe: python -m pip install pyserial") from exc
    try:
        return serial.Serial(port_name, baudrate=BAUD_RATE, timeout=0.1)
    except Exception as exc:  # pyserial raises several exception types
        raise ProbeError(f"could not open {port_name}: {exc}") from exc
