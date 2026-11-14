import unittest

from esc_config_helper.probe import FirmwareVersion, ProbeError, parse_firmware_version, read_firmware_version
from esc_config_helper.protocol import encode_packet, firmware_version_request

REPLY = encode_packet(bytes([0, 3, 7]) + b"HW")


class FakeConnection:
    """Stands in for a serial port. Returns canned bytes and records writes."""

    def __init__(self, incoming=b""):
        self.incoming = bytearray(incoming)
        self.written = []
        self.closed = False

    def write(self, data):
        self.written.append(bytes(data))
        return len(data)

    def read(self, size):
        chunk = bytes(self.incoming[:size])
        del self.incoming[:size]
        return chunk

    def close(self):
        self.closed = True


class ProbeTests(unittest.TestCase):
    def test_reads_version_and_sends_only_the_request(self):
        connection = FakeConnection(REPLY)
        version = read_firmware_version("TEST", connection=connection)
        self.assertEqual(version, FirmwareVersion(3, 7))
        self.assertEqual(str(version), "3.7")
        self.assertEqual(connection.written, [firmware_version_request()])
        self.assertFalse(connection.closed)

    def test_skips_other_frames_before_the_reply(self):
        connection = FakeConnection(encode_packet(bytes([4, 1, 2])) + REPLY)
        self.assertEqual(read_firmware_version("TEST", connection=connection), FirmwareVersion(3, 7))

    def test_times_out_without_a_reply(self):
        with self.assertRaises(ProbeError):
            read_firmware_version("TEST", timeout=0.05, connection=FakeConnection())

    def test_rejects_a_short_reply(self):
        with self.assertRaises(ProbeError):
            parse_firmware_version(bytes([0, 3]))

    def test_unusable_port_gives_probe_error(self):
        # With or without pyserial installed, a port that does not exist must
        # raise ProbeError rather than a raw library exception.
        with self.assertRaises(ProbeError):
            read_firmware_version("NO-SUCH-PORT", timeout=0.05)


if __name__ == "__main__":
    unittest.main()
