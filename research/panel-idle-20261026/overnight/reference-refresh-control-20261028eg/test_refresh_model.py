#!/usr/bin/env python3
import unittest
from refresh_model import snapshot, synchronize

class RefreshTests(unittest.TestCase):
    def test_stable_selector_does_not_rearm(self):
        for selector in (0, 1, 2, 255):
            for counter in (0, 1, 2, 3, 65535):
                self.assertEqual(synchronize(selector, counter, selector), (selector, counter))

    def test_edges_seed_or_cancel(self):
        for mirror in (0, 1, 2, 255, 256, 65535):
            for selector in (0, 1, 2, 255):
                if mirror != selector:
                    self.assertEqual(synchronize(mirror, 65535, selector), (selector, int(selector != 0)))

    def test_two_events_are_not_a_top_bottom_guarantee(self):
        for rows, expected in [((0, 0), ('top', 'top')), ((2159, 2159), ('bottom', 'bottom')),
                               ((0, 2159), ('top', 'bottom')), ((2159, 0), ('bottom', 'top'))]:
            mirror, counter = synchronize(0, 0, 1)
            kinds = []
            for row in rows:
                counter, kind = snapshot(counter, 1, 1, row, 2160)
                kinds.append(kind)
            self.assertEqual((mirror, counter, tuple(kinds)), (1, 0, expected))
            self.assertEqual(snapshot(counter, 1, 1, 0, 2160), (0, None))

    def test_nonboundary_does_not_consume_slot(self):
        for row in (1, 100, 2158, 2160, 65535):
            self.assertEqual(snapshot(1, 1, 1, row, 2160), (1, None))

    def test_entry_guards(self):
        self.assertEqual(snapshot(1, 1, 0, 0, 2160), (1, None))
        self.assertEqual(snapshot(0, 1, 1, 0, 2160), (0, None))
        self.assertEqual(snapshot(1, 0, 1, 0, 2160), (1, None))
        self.assertEqual(snapshot(1, 2, 255, 2159, 2160), (2, 'bottom'))

    def test_widths_wrap_and_height_boundaries(self):
        self.assertEqual(snapshot(65535, 1, 1, 0, 2160), (0, 'top'))
        self.assertEqual(snapshot(3, 1, 1, 1, 2160), (0, None))
        self.assertEqual(snapshot(1, 1, 1, 65535, 0), (1, None))
        self.assertEqual(snapshot(1, 1, 1, 0, 1), (2, 'top'))
        for args in [(-1, 1, 1, 0, 2160), (65536, 1, 1, 0, 2160),
                     (1, 256, 1, 0, 2160), (1, 1, True, 0, 2160),
                     (1, 1, 1, 65536, 2160), (1, 1, 1, 0, 65536)]:
            with self.assertRaises(ValueError):
                snapshot(*args)
        with self.assertRaises(ValueError):
            synchronize(0, 0, True)

if __name__ == '__main__':
    unittest.main()
