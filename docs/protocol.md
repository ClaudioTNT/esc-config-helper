# Serial protocol notes

These notes describe the packet format that VESC firmware uses over USB serial.
They were checked by reading the default branch of the firmware source
(vedderb/bldc) on 2026-11-14. This project does not copy firmware code. Other
transports, such as CAN forwarding, are not covered here.

## Frame layout

| Field      | Short frame              | Long frame               |
| ---------- | ------------------------ | ------------------------ |
| Start byte | `0x02`                   | `0x03`                   |
| Length     | 1 byte                   | 2 bytes, big-endian      |
| Payload    | 1 to 255 bytes           | 256 to 512 bytes         |
| CRC        | 2 bytes, high byte first | 2 bytes, high byte first |
| Stop byte  | `0x03`                   | `0x03`                   |

The sender uses a short frame for payloads up to 255 bytes. The parser also
accepts a long frame whose length is exactly 255. The 512-byte limit is the
firmware default; builds can change it.

## Checksum

CRC-16/XMODEM: polynomial `0x1021`, initial value `0x0000`, no reflection, no
final XOR. The check value for the ASCII bytes `123456789` is `0x31C3`.

The CRC covers the payload only. The start byte, length, CRC, and stop byte are
not included.

## Firmware version

- Request payload: one byte, `0x00` (`COMM_FW_VERSION`). The whole frame is
  `02 01 00 00 00 03`.
- Reply payload: byte 0 is the command ID (`0x00`), byte 1 is the major version,
  and byte 2 is the minor version. Later bytes hold more data, such as a
  hardware name, which the probe does not read.

## Where the facts come from

In `vedderb/bldc`, default branch:

- `comm/packet.c`: frame layout, length rules, CRC placement, stop byte
- `util/crc.c`: CRC-16 table and update rule
- `comm/packet.h`: default payload limit
- `datatypes.h`: the command ID enum, where `COMM_FW_VERSION` is the first entry
- `comm/commands.c`: how the firmware reads the request and writes the reply

## Not covered

- Transports other than USB serial.
- Firmware versions other than the default branch as checked on 2026-11-14.
