#!/usr/bin/env python3
"""Offline failure/identity fixtures; no TV connection or root execution."""
import base64
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('factory_observer', HERE / 'snapshot-factory-backend.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
MAPPING = '''00010000-00155000 r-xp 00000000 b3:1a 1 /usr/bin/TIFSDaemon
00165000-00166000 rw-p 00145000 b3:1a 1 /usr/bin/TIFSDaemon
47590000-47593000 r-xp 00000000 b3:1a 2 /usr/lib/libvideo-misc.so.0.1.0
475a3000-475a4000 rw-p 00003000 b3:1a 2 /usr/lib/libvideo-misc.so.0.1.0
10000000-1000f000 r-xp 00000000 b3:1b 3 /prd/usr/lib/libvideo-ft-control-impl-sec.so.0.1.0
1001e000-10020000 rw-p 0000e000 b3:1b 3 /prd/usr/lib/libvideo-ft-control-impl-sec.so.0.1.0
20000000-20001000 rw-p 00000000 00:00 0
'''.strip()


def response(reads=None, *, end_start=1203, bad_hash=False, changed_maps=False):
    fields = {'UTC': 'Mon Oct 26 16:00:00 UTC 2026'}
    for suffix in ('', '_END'):
        tail = ['S'] + ['0'] * 18 + [str(end_start if suffix else 1203)]
        fields.update({'BOOT'+suffix: '00000000-0000-4000-8000-000000000000',
            'PID'+suffix: '1085', 'EXE'+suffix: '/usr/bin/TIFSDaemon',
            'STAT'+suffix: '1085 (TIFSDaemon) ' + ' '.join(tail),
            'UPTIME'+suffix: '50000.00 200000.00',
            'MAPS'+suffix: MAPPING + ('\n20002000-20003000 rw-p 00000000 00:00 0' if suffix and changed_maps else '')})
        for key, (remote, _, sha) in module.SOURCES.items():
            fields['HASH_'+key+suffix] = ('0'*64 if key == 'impl' and bad_hash else sha) + '  ' + remote
    for key, words in (reads or {}).items():
        raw = b''.join(word.to_bytes(4, 'little') for word in words)
        fields['READ_'+key] = base64.b64encode(raw).decode()
    stdout = ''.join('@@ ' + key + '\n' + value + '\n' for key, value in fields.items())
    payload = {'model': 'QN77S95FAFXZC', 'authenticated': True, 'uid': 0, 'euid': 0,
               'root_persistence': 'host-assisted', 'global_system_files_unchanged_at_acquisition': True,
               'commands': [{'exit_code': 0, 'timed_out': False, 'stdout': stdout, 'stderr': ''}]}
    return subprocess.CompletedProcess([], 0, json.dumps(payload), '')


class ReaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.contract = module.static_contract()
        self.capture = module.Capture(Path(self.temp.name) / 'result.json', self.contract)

    def identity(self):
        with patch.object(module.subprocess, 'run', return_value=response()):
            self.capture.stage('identity', {})

    def test_metadata_validates_load_bias(self):
        self.identity()
        self.assertEqual(self.capture.biases, {'tifs': 0, 'wrapper': 0, 'impl': 0x10000000})

    def test_pid_reuse_rejected(self):
        with patch.object(module.subprocess, 'run', return_value=response(end_start=1204)):
            with self.assertRaisesRegex(ValueError, 'Process lifetime'):
                self.capture.stage('identity', {})

    def test_wrong_source_hash_rejected(self):
        with patch.object(module.subprocess, 'run', return_value=response(bad_hash=True)):
            with self.assertRaisesRegex(ValueError, 'Installed source hash'):
                self.capture.stage('identity', {})

    def test_changed_maps_rejected(self):
        with patch.object(module.subprocess, 'run', return_value=response(changed_maps=True)):
            with self.assertRaisesRegex(ValueError, 'Mappings changed'):
                self.capture.stage('identity', {})

    def test_unmapped_read_refused_before_transport(self):
        self.identity()
        with patch.object(module.subprocess, 'run') as run:
            with self.assertRaisesRegex(ValueError, 'Unmapped'):
                self.capture.stage('read', {'bad': (0x30000000, 1)})
            run.assert_not_called()

    def test_short_read_retained_and_rejected(self):
        self.identity()
        with patch.object(module.subprocess, 'run', return_value=response({'value': [1]})):
            with self.assertRaisesRegex(ValueError, 'Incomplete memory read'):
                self.capture.stage('read', {'value': (0x20000000, 2)})
        saved = json.loads(self.capture.path.read_text())
        self.assertIn('response', saved['stages'][-1])
        self.assertFalse(saved['accepted'])

    def test_full_pair_and_cleanup_free_capture(self):
        words = {'wrapper_global': [0x20000010, 0x20000100],
                 'diagnosis_got': [0x47590fd9], 'instance_global': [0x20000200],
                 'method_got': [0x1000aa54]}
        with patch.object(module, 'HERE', Path(self.temp.name)), \
             patch.object(module.sys, 'argv', ['snapshot-factory-backend.py', '--run']), \
             patch.object(module.subprocess, 'run', side_effect=[response(), response(words),
                          response({**words, 'slot': [0x1000c0e4]})]) as run:
            module.main()
        results = [p for p in Path(self.temp.name).glob('factory-backend-runtime-*.json')]
        saved = json.loads(results[0].read_text())
        self.assertTrue(saved['accepted'])
        self.assertEqual(saved['summary']['memory_bytes_read'], 44)
        self.assertFalse(saved['summary']['capture_invoked_factory_function'])
        self.assertEqual(run.call_count, 3)
        for call in run.call_args_list:
            self.assertIn('--persistent-only', call.args[0])
            self.assertLess(len(call.args[0][-1].encode()), 7500)


if __name__ == '__main__':
    unittest.main()
