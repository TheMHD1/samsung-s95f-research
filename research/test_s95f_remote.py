import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('s95f_remote', Path(__file__).with_name('s95f-remote.py'))
remote = importlib.util.module_from_spec(spec)
spec.loader.exec_module(remote)


class RemoteSafetyTests(unittest.TestCase):
    def test_protocol_receipts_do_not_expose_tokens_or_raw_data(self):
        self.assertEqual(remote.classify_receipt({'event': 'ms.channel.connect',
                         'data': {'token': 'private-secret'}}), 'ms.channel.connect')
        self.assertEqual(remote.classify_receipt({'event': 'private-secret',
                         'data': {'token': 'private-secret'}}), 'other-event')
        self.assertEqual(remote.classify_receipt({'event': 'ms.error',
                         'data': {'message': 'unrecognized method value : ms.remote.control'}}),
                         'method-rejected')
        self.assertEqual(remote.classify_receipt({'event': 'ms.error',
                         'data': {'message': 'private-secret'}}), 'server-error')
        self.assertEqual(remote.classify_receipt({'event': 'ms.channel.unauthorized'}), 'unauthorized')
        self.assertEqual(remote.classify_receipt([]), 'malformed-event')

    def test_receipt_window_is_bounded_and_restores_socket_timeout(self):
        class Socket:
            def __init__(self):
                self.timeout = 10
                self.reads = 0
            def gettimeout(self):
                return self.timeout
            def settimeout(self, value):
                self.timeout = value
            def recv(self):
                self.reads += 1
                return '{"event":"private-event","data":{"token":"secret"}}'
        connection = Socket()
        tv = type('TV', (), {'connection': connection})()
        with patch.object(remote.time, 'monotonic', return_value=0):
            self.assertEqual(remote.collect_receipts(tv), ['other-event'] * 16)
        self.assertEqual(connection.reads, 16)
        self.assertEqual(connection.timeout, 10)
        with self.assertRaises(ValueError):
            remote.collect_receipts(tv, duration=4)

    def test_receipt_error_stops_after_one_frame(self):
        class Socket:
            def gettimeout(self):
                return 10
            def settimeout(self, _):
                pass
            def recv(self):
                return '{"event":"ms.error","data":{"message":"unrecognized method value : ms.remote.control"}}'
        tv = type('TV', (), {'connection': Socket()})()
        self.assertEqual(remote.collect_receipts(tv), ['method-rejected'])

    def test_short_press_releases_once_without_long_hold(self):
        calls = []
        class TV:
            def send_key(self, key, **options):
                calls.append((key, options))
        with patch.object(remote.time, 'sleep') as sleep:
            remote.send_allowed_key(TV(), 'KEY_MENU', 'press-release')
        self.assertEqual(calls, [('KEY_MENU', {'cmd': 'Press', 'key_press_delay': 0}),
                                 ('KEY_MENU', {'cmd': 'Release', 'key_press_delay': 0})])
        sleep.assert_called_once_with(0.15)

    def test_alternate_input_excludes_power_and_unknown_keys(self):
        for key in ('KEY_POWER', 'KEY_FACTORY', 'unknown'):
            with self.assertRaises(ValueError):
                remote.send_allowed_key(None, key, 'press-release')

    def test_correct_identity(self):
        remote.check_model({'device': {'modelName': remote.MODEL}})

    def test_wrong_identity(self):
        with self.assertRaises(RuntimeError):
            remote.check_model({'device': {'modelName': 'Other TV'}})

    def test_missing_identity(self):
        with self.assertRaises(RuntimeError):
            remote.check_model({})

    def test_token(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'token'
            path.write_text('123456789')
            path.chmod(0o600)
            self.assertEqual(remote.read_token(path), '123456789')

    def test_missing_token(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                remote.read_token(Path(directory) / 'missing')

    def test_insecure_permission(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'token'
            path.write_text('123456789')
            path.chmod(0o644)
            with self.assertRaises(RuntimeError):
                remote.read_token(path)

    def test_symlink_token(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'target'
            target.write_text('123456789')
            target.chmod(0o600)
            path = Path(directory) / 'link'
            path.symlink_to(target)
            with self.assertRaises(OSError):
                remote.read_token(path)

    def test_invalid_tokens(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'token'
            for value in ('', 'not-a-token', '1' * 1025):
                path.write_text(value)
                path.chmod(0o600)
                with self.assertRaises(RuntimeError):
                    remote.read_token(path)

    def test_no_service_menu_keys(self):
        self.assertNotIn('KEY_FACTORY', remote.KEYS)
        self.assertNotIn('KEY_3SPEED', remote.KEYS)

    def test_browser_reported(self):
        remote.require_reported_browser([{'appId': remote.BROWSER_ID}])

    def test_browser_query_missing(self):
        for apps in (None, [], [{'appId': 'some-other-app'}], [{'name': 'Internet'}]):
            with self.assertRaises(RuntimeError):
                remote.require_reported_browser(apps)

    def test_browser_query_malformed(self):
        with self.assertRaises(RuntimeError):
            remote.require_reported_browser({'appId': remote.BROWSER_ID})

    def test_diagnostics_is_local_and_fixed(self):
        self.assertEqual(remote.DIAGNOSTICS_URL, 'http://198.51.100.10:8851/')

    def test_sdk_browser_exact_entry(self):
        remote.require_sdk_browser("\t'Internet'\t 'org.tizen.browser'\n[exit:0]\n")

    def test_sdk_browser_not_guessed_or_ambiguous(self):
        for output in ("[exit:0]", "org.tizen.browser\n[exit:0]", "'Other' 'org.tizen.browser'\n[exit:0]",
                       "'Internet' 'org.tizen.browser'\n[exit:1]", "'Internet' 'org.tizen.browser.fake'\n[exit:0]"):
            with self.assertRaises(RuntimeError):
                remote.require_sdk_browser(output)


if __name__ == '__main__':
    unittest.main()
