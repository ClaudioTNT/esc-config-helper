import binascii
import unittest

from esc_config_helper.protocol import (
    FrameError,
    FrameParser,
    crc16,
    decode_packet,
    encode_packet,
    firmware_version_request,
)


class CrcTests(unittest.TestCase):
    def test_standard_check_value(self):
        # CRC-16/XMODEM check value for the ASCII digits "123456789".
        self.assertEqual(crc16(b"123456789"), 0x31C3)

    def test_matches_binascii_crc_hqx(self):
        # binascii.crc_hqx uses the same polynomial and no reflection.
        data = bytes(range(0, 256, 7))
        self.assertEqual(crc16(data), binascii.crc_hqx(data, 0))


class EncodeDecodeTests(unittest.TestCase):
    def test_firmware_version_request_bytes(self):
        self.assertEqual(firmware_version_request(), bytes.fromhex("020100000003"))

    def test_short_round_trip(self):
        payload = bytes([4, 1, 2, 3])
        frame = encode_packet(payload)
        self.assertEqual(frame[0], 0x02)
        self.assertEqual(frame[1], len(payload))
        self.assertEqual(decode_packet(frame), payload)

    def test_255_bytes_still_uses_short_frame(self):
        payload = b"\x00" * 255
        frame = encode_packet(payload)
        self.assertEqual(frame[0], 0x02)
        self.assertEqual(decode_packet(frame), payload)

    def test_256_bytes_uses_long_frame(self):
        payload = bytes(range(256))
        frame = encode_packet(payload)
        self.assertEqual(frame[0], 0x03)
        self.assertEqual(int.from_bytes(frame[1:3], "big"), 256)
        self.assertEqual(decode_packet(frame), payload)

    def test_512_bytes_is_the_largest_frame(self):
        payload = bytes(i % 251 for i in range(512))
        frame = encode_packet(payload)
        self.assertEqual(frame[0], 0x03)
        self.assertEqual(decode_packet(frame), payload)

    def test_513_bytes_is_rejected_by_encoder(self):
        with self.assertRaises(ValueError):
            encode_packet(b"\x00" * 513)

    def test_corrupted_payload_is_rejected(self):
        frame = bytearray(encode_packet(b"\x00\x01\x02"))
        frame[2] ^= 0x01
        with self.assertRaises(FrameError):
            decode_packet(bytes(frame))

    def test_bad_stop_byte_is_rejected(self):
        frame = bytearray(encode_packet(b"\x00"))
        frame[-1] = 0x00
        with self.assertRaises(FrameError):
            decode_packet(bytes(frame))

    def test_extra_bytes_are_rejected(self):
        with self.assertRaises(FrameError):
            decode_packet(encode_packet(b"\x00\x01") + b"\x00")

    def test_long_frame_length_above_limit_is_rejected(self):
        # Start byte 0x03 and a length of 513, which is above the 512-byte limit.
        frame = bytes([0x03, 0x02, 0x01]) + b"\x00" * 513 + b"\x00\x00\x03"
        with self.assertRaises(FrameError):
            decode_packet(frame)

    def test_long_frame_length_below_255_is_rejected(self):
        frame = bytes([0x03, 0x00, 0x64]) + b"\x00" * 100 + b"\x00\x00\x03"
        with self.assertRaises(FrameError):
            decode_packet(frame)

    def test_unknown_start_byte_is_rejected(self):
        with self.assertRaises(FrameError):
            decode_packet(b"\x07\x01\x00\x00\x00\x03")

    def test_empty_payload_is_rejected_by_encoder(self):
        with self.assertRaises(ValueError):
            encode_packet(b"")


class FrameParserTests(unittest.TestCase):
    def test_reads_frames_fed_one_byte_at_a_time_after_noise(self):
        stream = b"\xff\x13" + encode_packet(b"\x00\x05\x06") + encode_packet(b"\x00\x01")
        parser = FrameParser()
        found = []
        for i in range(len(stream)):
            found.extend(parser.feed(stream[i:i + 1]))
        self.assertEqual(found, [b"\x00\x05\x06", b"\x00\x01"])

    def test_waits_for_the_rest_of_a_frame(self):
        frame = encode_packet(b"\x00\x09\x09")
        parser = FrameParser()
        self.assertEqual(parser.feed(frame[:3]), [])
        self.assertEqual(parser.feed(frame[3:]), [b"\x00\x09\x09"])

    def test_skips_a_long_header_with_an_impossible_length(self):
        valid = encode_packet(b"\x00\x0a")
        parser = FrameParser()
        self.assertEqual(parser.feed(b"\x03\xff\xff" + valid), [b"\x00\x0a"])


if __name__ == "__main__":
    unittest.main()
