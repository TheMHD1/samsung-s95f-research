#!/usr/bin/env python3
"""Zero-I/O wrapper phase tests using a local fake root transport."""
import argparse
import base64
import importlib.util
import json
from pathlib import Path
import tempfile

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('ui_tab_wrapper', HERE / 'run-once.py')
ui = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ui)


def need(ok, why):
    if not ok:
        raise ValueError(why)


class FakeRoot:
    def __init__(self, mode=None):
        self.mode = mode
        self.commands = []

    @staticmethod
    def save(path, record):
        path.write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')

    def root(self, command, record, record_path):
        self.commands.append(command)
        record.setdefault('calls', []).append({
            'command': command, 'fake': True,
            'response': {'authenticated': True, 'commands': [{'exit_code': 0}]}})
        self.save(record_path, record)
        if 'PRIVATE_STAGE_READY' in command:
            return ui.BOOT + '\n123.45 678.90\nPRIVATE_STAGE_READY\n'
        if 'PRIVATE_STAGE_ABSENT' in command:
            return 'PRIVATE_STAGE_ABSENT\n'
        if '/usr/bin/dotnet' in command and ' --apps-key\n' in command:
            mode = 'apps-key'
            option, page, entry_point = ui.MODE
            need(command.count('/usr/bin/dotnet') == 2,
                 'one dotnet executable check and one invocation')
            need(command.rstrip().endswith(option), 'fixed option is final command')
            outcome = {
                'schema': 'managed-apps-key-launch-v1', 'mode': mode,
                'request': {'application_id': 'com.samsung.tv.csfs',
                            'switch_page_key': 'switch_page', 'switch_page_value': page,
                            'entry_point_key': 'entry_point', 'entry_point_value': entry_point,
                            'operation_set': False, 'no_raise_window_set': False},
                'expected_boot_id': ui.BOOT, 'boot_id_before': ui.BOOT,
                'boot_id_after': ui.BOOT, 'boot_matched_before': True,
                'boot_matched_after': True, 'uptime_before': '124.00 679.00',
                'uptime_after': '124.01 679.01', 'architecture': 'Arm',
                'pointer_bytes': 4, 'little_endian': True, 'abi_accepted': True,
                'request_constructed': True, 'send_attempted': True,
                'send_returned': True, 'handle_disposed': True, 'exception': None,
                'target_operations': 1, 'physical_picture_observed': False,
                'execution_confirmed': False}
            return json.dumps(outcome, separators=(',', ':')) + '\n'
        return 'FAKE_OK\n'


def main():
    staged = {name: (HERE / 'bin/Release/net6.0' / name).read_bytes()
              for name in ui.REMOTE_NAMES}
    manifest_raw = b'{"fake":"manifest"}\n'
    original = ui.load_contract
    ui.load_contract = lambda ignored: (manifest_raw, {'schema': ui.SCHEMA}, staged)
    try:
        with tempfile.TemporaryDirectory(prefix='ui-tab-wrapper-test-') as temporary:
            root = Path(temporary)
            prep_dir = root / 'prepare'
            fake_prepare = FakeRoot()
            ui.prepare(argparse.Namespace(manifest_sha256='0' * 64, output=prep_dir),
                       fake_prepare)
            prepared = prep_dir / 'prepared.json'
            need(prepared.is_file(), 'prepared record')
            need(all(' --apps-key\n' not in command
                     for command in fake_prepare.commands), 'prepare has no UI invocation')

            fake_send = FakeRoot('apps-key')
            output = root / 'send-apps-key'
            ui.send(argparse.Namespace(prepared=prepared, output=output,
                                       apps_key=True), fake_send)
            need(len(fake_send.commands) == 1, 'one root call per send')
            result = json.loads((output / 'result.json').read_text())
            need(result['send_returned'] is True and result['target_operations'] == 1,
                 'send result apps-key')

            fake_cleanup = FakeRoot()
            cleanup_dir = root / 'cleanup'
            ui.cleanup(argparse.Namespace(prepared=prepared, output=cleanup_dir), fake_cleanup)
            need(len(fake_cleanup.commands) == 1 and
                 '/usr/bin/dotnet' not in fake_cleanup.commands[0],
                 'cleanup has no managed invocation')
            need(json.loads((cleanup_dir / 'result.json').read_text())['stage_absent'] is True,
                 'cleanup result')
    finally:
        ui.load_contract = original
    print(json.dumps({'fakeRootTestsPassed': 7,
                      'prepareUiInvocations': 0,
                      'sendRootCalls': {'apps-key': 1},
                      'cleanupManagedInvocations': 0,
                      'targetOperations': 0}, separators=(',', ':')))


if __name__ == '__main__':
    main()
