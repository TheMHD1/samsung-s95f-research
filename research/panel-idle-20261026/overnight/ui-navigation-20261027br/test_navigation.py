import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('navigation', HERE / 'navigate.py')
nav = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nav)


class NavigationTests(unittest.TestCase):
    def test_fixed_actions(self):
        self.assertEqual(nav.LOCAL_KEYSYMS['wake'], 'XF86AudioRaiseVolume')
        self.assertEqual(nav.LOCAL_KEYSYMS['home'], 'XF86Home')
        self.assertEqual(nav.KEYS['wake'], 'KEY_VOLUP')
        self.assertEqual(nav.TARGETS['apps'], 'd/apps.tab')
        self.assertEqual(nav.TARGETS['for-you'], 'd/ug.tab@ForYou')

    def test_key_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            ok = subprocess.CompletedProcess([], 0, b'{"connected":true,"key_sent":"KEY_VOLUP","protocol_receipts":[]}', b'')
            with patch.object(nav, 'run_process', return_value=ok):
                value = nav.ws_key_action('wake', out, 'test')
            self.assertEqual(value['key'], 'KEY_VOLUP')
            self.assertFalse(value['execution_confirmed'])

    def test_local_key_contract(self):
        class Adapter:
            def root(self, command, record, output):
                self.command = command
                self.record = record
                self.output = output
                return 'LOCAL_KEY_DOWN_EXIT=0\nLOCAL_KEY_UP_EXIT=0\n'
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            source = Adapter()
            value = nav.local_key_action('wake', out, source, 'test')
        self.assertIn("input_keyevent XF86AudioRaiseVolume down", source.command)
        self.assertTrue(source.command.startswith('set -eu\n'))
        self.assertLess(source.command.index('test -x /usr/bin/input_keyevent'),
                        source.command.index('input_keyevent XF86AudioRaiseVolume down'))
        self.assertLess(source.command.index('sha256sum /usr/bin/input_keyevent'),
                        source.command.index('input_keyevent XF86AudioRaiseVolume down'))
        self.assertIn('sleep 0.15', source.command)
        self.assertIn("input_keyevent XF86AudioRaiseVolume up", source.command)
        self.assertLess(source.command.index('down >/dev/null'), source.command.index('sleep 0.15'))
        self.assertLess(source.command.index('sleep 0.15'), source.command.index('up >/dev/null'))
        self.assertEqual(value['down_exit_code'], 0)
        self.assertEqual(value['up_exit_code'], 0)
        self.assertEqual(value['hold_milliseconds'], 150)

    def test_page_refusal_condition(self):
        before = {'screensaver_windows_present': True, 'csfs_window_present': True}
        self.assertTrue(before['screensaver_windows_present'])

    def test_apps_plan_stops_at_target(self):
        snapshots = iter([
            {'screensaver_windows_present': False, 'csfs_window_present': True,
             'cached_current_tab': 'd/ug.tab@ForYou'},
            {'screensaver_windows_present': False, 'csfs_window_present': True,
             'cached_current_tab': 'd/ug.tab@ForYou'},
            {'screensaver_windows_present': False, 'csfs_window_present': True,
             'cached_current_tab': 'd/ug.tab@ForYou'},
            {'screensaver_windows_present': False, 'csfs_window_present': True,
             'cached_current_tab': 'd/ug.tab@ForYou'},
            {'screensaver_windows_present': False, 'csfs_window_present': True,
             'cached_current_tab': 'd/ug.tab@Live'},
            {'screensaver_windows_present': False, 'csfs_window_present': True,
             'cached_current_tab': 'd/apps.tab'},
        ])
        sent = []
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            with patch.object(nav, 'command_snapshot', side_effect=lambda *args: next(snapshots)), \
                 patch.object(nav, 'one_key', side_effect=lambda action, *args: sent.append(action) or {'key': action}):
                value = nav.normal_page_navigation('apps', 'local', out, object(), next(snapshots))
        self.assertTrue(value['cached_target_match'])
        self.assertEqual(sent, ['right', 'up', 'up', 'right', 'right'])

    def test_apps_first_right_live_branch(self):
        before = {'screensaver_windows_present': False, 'csfs_window_present': True,
                  'cached_current_tab': 'd/ug.tab@ForYou'}
        live = {'screensaver_windows_present': False, 'csfs_window_present': True,
                'cached_current_tab': 'd/ug.tab@Live'}
        apps = {'screensaver_windows_present': False, 'csfs_window_present': True,
                'cached_current_tab': 'd/apps.tab'}
        sent = []
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(nav, 'command_snapshot', side_effect=[live, apps]), \
                 patch.object(nav, 'one_key', side_effect=lambda action, *args: sent.append(action) or {'key': action}):
                value = nav.normal_page_navigation('apps', 'local', Path(temp), object(), before)
        self.assertTrue(value['cached_target_match'])
        self.assertEqual(sent, ['right', 'right'])

    def test_navigation_stops_on_ambiguity(self):
        before = {'screensaver_windows_present': False, 'csfs_window_present': True,
                  'cached_current_tab': 'd/ug.tab@Live'}
        bad = {'screensaver_windows_present': False, 'csfs_window_present': True,
               'cached_current_tab': 'd/ug.tab@ForYou'}
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(nav, 'command_snapshot', return_value=bad), \
                 patch.object(nav, 'one_key', return_value={'key': 'right'}):
                with self.assertRaisesRegex(ValueError, 'unexpected'):
                    nav.normal_page_navigation('apps', 'local', Path(temp), object(), before)


if __name__ == '__main__':
    unittest.main()
