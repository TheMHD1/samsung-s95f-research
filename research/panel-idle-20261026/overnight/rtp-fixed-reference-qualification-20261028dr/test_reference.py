"""Meaningful synthetic boundary/packing tests; never opens a device."""
import unittest
from reference_model import (unpack_group, lane_from_x, window, decode_window,
                             amplitude_candidates, CANDIDATE_X)


def pack_lanes(values):
    # Independent bitstream construction, not the decoder's word/tail decomposition.
    return sum(v << (12 * i) for i, v in enumerate(values)).to_bytes(3 * len(values) // 2, "little")


class ReferenceTests(unittest.TestCase):
    def test_golden_mixed_nibbles(self):
        self.assertEqual(unpack_group(bytes.fromhex("23614589c7ab")), (0x123, 0x456, 0x789, 0xABC))

    def test_every_bit_at_each_lane(self):
        for lane in range(4):
            for bit in range(12):
                expected = [0] * 4
                expected[lane] = 1 << bit
                self.assertEqual(unpack_group(pack_lanes(expected)), tuple(expected))
        self.assertEqual(unpack_group(b"\xff" * 6), (4095,) * 4)

    def test_bad_group_sizes(self):
        for length in (0, 1, 4, 5, 7, 8):
            with self.assertRaises(ValueError):
                unpack_group(bytes(length))

    def test_window_mapping_and_no_extra_header(self):
        self.assertEqual(window("top")["bus"], 0x47015354)
        self.assertEqual(window("bottom")["bus"], 0x47016264)
        self.assertEqual(window("top")["header_hex"], "010100005453014768000000")
        self.assertEqual(window("bottom", 120)["header_hex"], "010100006462014778000000")
        self.assertEqual(window("top")["decode_bytes"], 102)
        self.assertEqual(window("top", 120)["decode_bytes"], 120)

    def test_each_selected_lane_and_tail_ignored(self):
        values = [(i * 73 + 29) & 4095 for i in range(1920)]
        packed = pack_lanes(values)
        for kind in ("top", "bottom"):
            for length in (104, 120):
                raw = packed[852:852 + length]
                expected = {x: values[x] for x in CANDIDATE_X}
                self.assertEqual(decode_window(raw, kind=kind, length=length), expected)
                if length == 104:
                    self.assertEqual(decode_window(raw[:102] + b"\xff\xff", kind=kind), expected)

    def test_short_extra_malformed_and_drift(self):
        for size in (0, 96, 102, 103, 105, 120):
            with self.assertRaises(ValueError):
                decode_window(bytes(size), kind="top")
        for args in (("ring", 104), ("top", 160), ("bottom", 102)):
            with self.assertRaises(ValueError):
                window(*args)
        with self.assertRaises(ValueError):
            decode_window(bytes(104), kind="top", xbase=1)

    def test_coordinate_wrap_and_amplitude_ambiguity(self):
        self.assertEqual(lane_from_x(4, 65530), 10)
        for x, base in ((1920, 0), (1, 2), (-1, 0), (65536, 0)):
            with self.assertRaises(ValueError):
                lane_from_x(x, base)
        self.assertEqual(amplitude_candidates(491, 1370), [1861])
        self.assertEqual(amplitude_candidates(600, 500), [100, 1100])
        self.assertEqual(amplitude_candidates(4000, 200), [3800])
        for b, diff in ((4096, 0), (0, -1)):
            with self.assertRaises(ValueError):
                amplitude_candidates(b, diff)


if __name__ == "__main__":
    unittest.main()
