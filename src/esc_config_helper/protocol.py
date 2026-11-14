"""Byte-level framing for VESC serial packets.

A frame is a start byte, a length, the payload, a 2-byte CRC, and a stop byte.

- Payloads of up to 255 bytes use start byte 0x02 and a 1-byte length.
- Payloads of 256 to 512 bytes use start byte 0x03 and a 2-byte big-endian length.
- The CRC covers the payload only. It is sent high byte first.
- The stop byte is always 0x03.

This module builds and reads frames. It does not know what any command
means. The details were checked against the VESC firmware source; see
docs/protocol.md.
"""

from __future__ import annotations

START_SHORT = 0x02
START_LONG = 0x03
STOP_BYTE = 0x03

# Largest payload the firmware accepts by default (PACKET_MAX_PL_LEN).
# Firmware builds can change this.
MAX_PAYLOAD = 512

# The sender uses short frames up to 255 bytes. The parser also accepts a
# long frame whose length is exactly 255.
SHORT_MAX = 255
LONG_MIN = 255

# Command ID for the firmware version request (COMM_FW_VERSION).
COMM_FW_VERSION = 0

_HEADER_SIZE = {START_SHORT: 2, START_LONG: 3}


class FrameError(ValueError):
    """Raised when bytes do not form a valid VESC frame."""


def crc16(data: bytes) -> int:
    """CRC-16 used by VESC frames (CRC-16/XMODEM).

    Polynomial 0x1021, initial value 0, no bit reflection, no final XOR.
    """
    crc = 0
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def _layout(start: int, length_field: bytes) -> tuple[int, int]:
    """Return (header size, payload length) for a start byte, or raise FrameError."""
    if start == START_SHORT:
        length = length_field[0]
        if length == 0:
            raise FrameError("empty payload")
        return 2, length
    if start == START_LONG:
        length = int.from_bytes(length_field, "big")
        if not LONG_MIN <= length <= MAX_PAYLOAD:
            raise FrameError(f"long frame length {length} is out of range")
        return 3, length
    raise FrameError(f"unknown start byte 0x{start:02x}")


def encode_packet(payload: bytes) -> bytes:
    """Wrap a payload in a VESC frame."""
    payload = bytes(payload)
    if not payload:
        raise ValueError("payload must not be empty")
    if len(payload) <= SHORT_MAX:
        header = bytes([START_SHORT, len(payload)])
    elif len(payload) <= MAX_PAYLOAD:
        header = bytes([START_LONG]) + len(payload).to_bytes(2, "big")
    else:
        raise ValueError(f"payload too long: {len(payload)} bytes (limit {MAX_PAYLOAD})")
    checksum = crc16(payload).to_bytes(2, "big")
    return header + payload + checksum + bytes([STOP_BYTE])


def decode_packet(frame: bytes) -> bytes:
    """Return the payload of one complete frame, or raise FrameError."""
    frame = bytes(frame)
    if not frame:
        raise FrameError("frame too short")
    header_size = _HEADER_SIZE.get(frame[0])
    if header_size is None:
        raise FrameError(f"unknown start byte 0x{frame[0]:02x}")
    if len(frame) < header_size:
        raise FrameError("frame too short")
    header_size, length = _layout(frame[0], frame[1:header_size])
    expected = header_size + length + 3
    if len(frame) != expected:
        raise FrameError(f"expected {expected} bytes, got {len(frame)}")
    if frame[-1] != STOP_BYTE:
        raise FrameError("missing stop byte")
    payload = frame[header_size:header_size + length]
    received = int.from_bytes(frame[-3:-1], "big")
    if crc16(payload) != received:
        raise FrameError("CRC mismatch")
    return payload


class FrameParser:
    """Collects bytes from a serial port and returns complete payloads.

    Bytes that do not start a valid frame are skipped one at a time, so line
    noise or a corrupt frame does not stop later frames from being read. A
    start byte that happens to look like a valid frame start can make the
    parser wait for more bytes; the caller's timeout is the way out of that.
    """

    def __init__(self) -> None:
        self._buffer = bytearray()

    def feed(self, data: bytes) -> list[bytes]:
        self._buffer.extend(data)
        payloads: list[bytes] = []
        while self._buffer:
            header_size = _HEADER_SIZE.get(self._buffer[0])
            if header_size is None:
                del self._buffer[0]
                continue
            if len(self._buffer) < header_size:
                break
            try:
                header_size, length = _layout(self._buffer[0], bytes(self._buffer[1:header_size]))
            except FrameError:
                del self._buffer[0]
                continue
            total = header_size + length + 3
            if len(self._buffer) < total:
                break
            try:
                payloads.append(decode_packet(bytes(self._buffer[:total])))
            except FrameError:
                del self._buffer[0]
                continue
            del self._buffer[:total]
        return payloads


def firmware_version_request() -> bytes:
    """Frame that asks the controller for its firmware version. Read-only."""
    return encode_packet(bytes([COMM_FW_VERSION]))
