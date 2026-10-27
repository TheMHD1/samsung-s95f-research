#!/usr/bin/env python3
"""No-network shell failure tests for the bounded HDMI binding reader."""
from pathlib import Path
import importlib.util
import shlex
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).with_name('read-hdmi-control-binding.py')
spec = importlib.util.spec_from_file_location('hdmi_binding_test_subject', SOURCE)
subject = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)
COMMAND = subject.module.COMMAND

def function(name):
    start = COMMAND.index(name+'() {\n')
    end = COMMAND.index('\n}\n', start)+3
    return COMMAND[start:end]+'\n'

class ReaderShellTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='hdmi-binding-tests-')
        self.root = Path(self.tmp.name)
        self.maps = self.root/'maps'
        self.maps.write_text('10000000-10001000 rw-p 00000000 00:00 0\n')
        self.data = self.root/'bytes'

    def tearDown(self):
        self.tmp.cleanup()

    def shell(self, suffix, *, payload=b'\x01\x02\x03\x04', dd_status=0):
        self.data.write_bytes(payload)
        definitions = function('mapok')+function('u32')
        definitions = definitions.replace('/proc/$P/maps', shlex.quote(str(self.maps)))
        script = ('set -euo pipefail\nP=706\n'+definitions+
                  'dd() { /bin/cat '+shlex.quote(str(self.data))+'; return '+str(dd_status)+'; }\n'+suffix)
        return subprocess.run(['bash', '-c', script], capture_output=True, text=True, timeout=5)

    def test_mapped_aligned_four_octets_decode_little_endian(self):
        r = self.shell('u32 268435456')
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, '67305985', ''))

    def test_full_unsigned_word(self):
        r = self.shell('u32 268435456', payload=b'\xff'*4)
        self.assertEqual((r.returncode, r.stdout), (0, '4294967295'))

    def test_partial_and_excess_reads_are_rejected(self):
        for length in (0, 1, 2, 3, 5, 8):
            with self.subTest(length=length):
                r = self.shell('if u32 268435456; then exit 99; else exit 0; fi', payload=b'\x01'*length)
                self.assertEqual((r.returncode, r.stdout), (0, ''))

    def test_reader_pipeline_failure_is_rejected_even_with_four_bytes(self):
        r = self.shell('if u32 268435456; then exit 99; else exit 0; fi', dd_status=1)
        self.assertEqual((r.returncode, r.stdout), (0, ''))

    def test_bad_ranges_rejected_when_errexit_is_suppressed_by_conditional(self):
        cases = [(0, 4), (-4, 4), (268435457, 4), (268435456, 0),
                 (268435456, 3), (268439552, 4), (268439548, 8),
                 (4294967292, 4), (4294967296, 4)]
        for address, size in cases:
            with self.subTest(address=address, size=size):
                r = self.shell(f'if mapok {address} {size}; then exit 99; else exit 0; fi')
                self.assertEqual(r.returncode, 0, r.stderr)

    def test_map_end_is_exclusive_but_read_can_end_at_boundary(self):
        r = self.shell('mapok 268439548 4')
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_unreadable_mapping_rejected(self):
        self.maps.write_text('10000000-10001000 ---p 00000000 00:00 0\n')
        r = self.shell('if u32 268435456; then exit 99; else exit 0; fi')
        self.assertEqual((r.returncode, r.stdout), (0, ''))

    def test_malformed_non_32_bit_map_not_used(self):
        self.maps.write_text('1000000-10001000 rw-p 00000000 00:00 0\n')
        r = self.shell('if mapok 268435456 4; then exit 99; else exit 0; fi')
        self.assertEqual(r.returncode, 0, r.stderr)

if __name__ == '__main__':
    unittest.main()
