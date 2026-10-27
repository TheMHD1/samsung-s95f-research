#!/usr/bin/env python3
"""One bounded Apps-selected stock-panel recovery for an observed black panel.

Dry by default.  Live mode has three gates: normal UI navigation reports Apps,
public service getters are not busy, then one unchanged stock MODE2 helper is
invoked.  It deliberately sends no wake key after MODE2; the physical picture
must be confirmed separately by the owner.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
NAV = BASE / 'ui-navigation-20261027br' / 'navigate.py'
# Re-pinned only after the normal-key navigation implementation was reviewed.
NAV_SHA = '74b60a9611f35a76d272b33677f773cc955838c2c6dda2c3565c371cc9d4d530'
ADAPTER = BASE / 'managed-ui-tab-launch' / 'root-with-margin.py'
ADAPTER_SHA = 'bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a'
MODE2 = BASE / 'managed-tcon-power-cycle-once' / 'run-power-cycle-once.py'
MODE2_SHA = '5c7ec5d3581e349d7f91669977123497147777e573fbdefd8a9b6f96dcf3cb75'
BOOT = '00000000-0000-4000-8000-000000000000'
APPS = 'd/apps.tab'


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def pinned(path, expected, name):
    need(path.is_file() and sha(path) == expected, name + ' identity mismatch')


def load_adapter():
    pinned(ADAPTER, ADAPTER_SHA, 'root adapter')
    spec = importlib.util.spec_from_file_location('quickpath_adapter', ADAPTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(argv, output, label):
    done = subprocess.run(argv, capture_output=True, timeout=120)
    (output / (label + '.stdout.txt')).write_bytes(done.stdout)
    (output / (label + '.stderr.txt')).write_bytes(done.stderr)
    save(output / (label + '.result.json'), {
        'argv': [str(value) for value in argv], 'exit_code': done.returncode,
    })
    return done


def apps_gate(output, runner=NAV, runner_sha=NAV_SHA):
    pinned(runner, runner_sha, 'navigation runner')
    nav_output = output / 'navigate-apps'
    done = run(['python3', str(runner), 'apps', '--execute', '--output', str(nav_output)],
               output, 'navigate')
    need(done.returncode == 0, 'Apps navigation failed; MODE2 withheld')
    result_path = nav_output / 'result.json'
    need(result_path.is_file(), 'Apps navigation result missing; MODE2 withheld')
    result = json.loads(result_path.read_text())
    need(result.get('action') == 'apps' and result.get('cached_target_match') is True and
         result.get('after', {}).get('cached_current_tab') == APPS,
         'Apps was not the cached current tab; MODE2 withheld')
    return result


def public_gate(output, adapter_module=None):
    module = adapter_module or load_adapter()
    record = {'schema': 'recovery-quickpath-public-gate-v1', 'calls': [],
              'scope': 'read-only public reject checks; not a global maintenance proof'}
    command = (
        'set -eu\n'
        f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n'
        'cat /proc/sys/kernel/random/boot_id\ncat /proc/uptime\n'
        'vconftool get memory/enterprise/swupgrade/working_status\n'
        'dbus-send --system --print-reply --reply-timeout=1500 '
        '--dest=org.tizen.system.deviced /Org/Tizen/System/DeviceD/Display '
        'org.tizen.system.deviced.display.GetPowerState\n'
        'dbus-send --system --print-reply --reply-timeout=1500 '
        '--dest=org.tizen.system.deviced /Org/Tizen/System/DeviceD/Display '
        'org.tizen.system.deviced.display.GetScreenState\n'
        'dbus-send --system --print-reply --reply-timeout=1000 '
        '--dest=org.tizen.system.deviced /Org/Tizen/System/DeviceD/Display '
        'org.tizen.system.deviced.display.BurnInProtectionInProgress\n'
        'cat /proc/uptime\n')
    text = module.root(command, record, output / 'public-gate.json')
    (output / 'public-gate.txt').write_text(text)
    int_values = re.findall(r'^\s+int32 ([0-9]+)\s*$', text, re.M)
    accepted = ('memory/enterprise/swupgrade/working_status, value = 0 (Int32)' in text and
                'string "lcdon"' in text and int_values == ['1', '0'])
    save(output / 'public-gate-summary.json', {
        'accepted': accepted, 'upgrade_working_status': 0 if accepted else None,
        'power_state': 'lcdon' if accepted else None,
        'screen_state': 1 if accepted else None,
        'burn_in_protection_in_progress': 0 if accepted else None,
        'limitations': 'These public values are reject signals only, not panel-light or global-maintenance proof.',
    })
    need(accepted, 'public reject checks are not in the required state; MODE2 withheld')
    return text


def mode2(output, helper=MODE2, helper_sha=MODE2_SHA):
    pinned(helper, helper_sha, 'stock MODE2 helper')
    result_path = output / 'mode2.json'
    done = run(['python3', str(helper), '--run', '--reviewed', '--output', str(result_path)],
               output, 'mode2')
    need(done.returncode == 0, 'stock MODE2 helper failed; no retry')
    need(result_path.is_file(), 'stock MODE2 result missing; no retry')
    result = json.loads(result_path.read_text())
    need(result.get('accepted') is True and result.get('cleanup_confirmed') is True,
         'stock MODE2 was not accepted/cleaned; no retry')
    return result


def dry():
    return {
        'schema': 'recovery-quickpath-dry-v1', 'execute_required': True,
        'steps': ['normal-key navigation to Apps', 'cached Apps verification',
                  'public reject checks', 'one fixed stock MODE2'],
        'max_stock_MODE2': 1, 'automatic_retries': 0, 'wake_key_after_MODE2': False,
        'controller_vendor_reads': 0, 'firmware_or_protection_changes': 0,
        'physical_picture_observed': False,
        'physical_result_required_after_MODE2': True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not args.execute:
        need(args.output is None, '--output requires --execute')
        print(json.dumps(dry(), separators=(',', ':')))
        return
    need(args.output is not None and args.output.is_absolute(), 'fresh absolute --output required')
    need(not args.output.exists(), 'output must not already exist')
    args.output.mkdir(parents=True, mode=0o700)
    save(args.output / 'intent.json', dict(dry(), execute=True,
         operational_scope='Owner-observed persistent black only; not a preventive reset service.'))
    navigation = apps_gate(args.output)
    public_gate(args.output)
    recovery = mode2(args.output)
    final = {'schema': 'recovery-quickpath-result-v1', 'navigation': navigation,
             'mode2_accepted': True, 'mode2_cleanup_confirmed': True,
             'mode2_classification': recovery.get('execution', {}).get('result'),
             'physical_picture_observed': False,
             'recovery_inferred': False,
             'next_step': 'Owner confirms whether the physical picture returned and remains visible.'}
    save(args.output / 'result.json', final)
    print(json.dumps(final, separators=(',', ':')))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('Stopped: ' + type(exc).__name__ + ': ' + str(exc), file=sys.stderr)
        sys.exit(1)
