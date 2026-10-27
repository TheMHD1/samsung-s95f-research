import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('quick_recover', HERE / 'recover.py')
RECOVER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RECOVER)


class FakeDone:
    def __init__(self, code=0):
        self.returncode = code
        self.stdout = b''
        self.stderr = b''


class RecoveryTests(unittest.TestCase):
    def test_dry_never_has_side_effects(self):
        plan = RECOVER.dry()
        self.assertEqual(plan['max_stock_MODE2'], 1)
        self.assertEqual(plan['automatic_retries'], 0)
        self.assertFalse(plan['wake_key_after_MODE2'])

    def test_failed_navigation_withholds_mode2(self):
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw)
            with patch.object(RECOVER, 'run', return_value=FakeDone(1)):
                with self.assertRaisesRegex(ValueError, 'MODE2 withheld'):
                    RECOVER.apps_gate(output, runner=Path(__file__), runner_sha=RECOVER.sha(Path(__file__)))
            self.assertFalse((output / 'mode2.json').exists())

    def test_public_gate_rejects_busy_or_wrong_shape(self):
        class Adapter:
            def root(self, command, record, path):
                path.write_text('{}\n')
                return ('boot\n1 1\nmemory/enterprise/swupgrade/working_status, value = 1 (Int32)\n'
                        'string "lcdon"\n   int32 1\n   int32 0\n')
        with tempfile.TemporaryDirectory() as raw:
            with self.assertRaisesRegex(ValueError, 'MODE2 withheld'):
                RECOVER.public_gate(Path(raw), Adapter())

    def test_public_gate_accepts_only_the_expected_public_values(self):
        class Adapter:
            def root(self, command, record, path):
                path.write_text('{}\n')
                return ('boot\n1 1\nmemory/enterprise/swupgrade/working_status, value = 0 (Int32)\n'
                        'string "lcdon"\n   int32 1\n   int32 0\n2 2\n')
        with tempfile.TemporaryDirectory() as raw:
            RECOVER.public_gate(Path(raw), Adapter())
            summary = json.loads((Path(raw) / 'public-gate-summary.json').read_text())
            self.assertTrue(summary['accepted'])

    def test_mode2_is_exactly_one_process_on_success(self):
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw)
            helper = output / 'helper.py'
            helper.write_text('stub')
            calls = []
            def fake_run(argv, out, label):
                calls.append(argv)
                (out / 'mode2.json').write_text(json.dumps({'accepted': True, 'cleanup_confirmed': True}))
                return FakeDone(0)
            with patch.object(RECOVER, 'run', side_effect=fake_run):
                RECOVER.mode2(output, helper=helper, helper_sha=RECOVER.sha(helper))
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0][2:4], ['--run', '--reviewed'])


if __name__ == '__main__':
    unittest.main()
