#!/usr/bin/env python3
"""Bounded normal-UI navigation runner for the S95F.

Dry by default.  An execution performs one normal key or one prepared
AppControl request, then records the cached UI state.  It never touches the
controller USB, display power, settings, firmware, or kernel debugfs.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
REMOTE = BASE.parents[1] / 's95f-remote.py'
REMOTE_SHA = '18b07e0ebb37550cf07bd088dc46de3a598f587d481b971819df1a9043a300c2'
UI = BASE / 'managed-ui-tab-launch'
ADAPTER = UI / 'root-with-margin.py'
ADAPTER_SHA = 'bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a'
BOOT = '00000000-0000-4000-8000-000000000000'
INPUT_KEYEVENT_SHA = '7284ad5b0117a96a166a4fe327c6361bea998e5d2086a0e1a36d2a3477a87db9'
KEYS = {'wake': 'KEY_VOLUP', 'home': 'KEY_HOME', 'up': 'KEY_UP',
        'down': 'KEY_DOWN', 'left': 'KEY_LEFT', 'right': 'KEY_RIGHT',
        'enter': 'KEY_ENTER', 'back': 'KEY_RETURN'}
LOCAL_KEYSYMS = {'wake': 'XF86AudioRaiseVolume', 'home': 'XF86Home',
                 'up': 'Up', 'down': 'Down', 'left': 'Left', 'right': 'Right',
                 'enter': 'Return', 'back': 'XF86Back'}
TARGETS = {'apps': 'd/apps.tab', 'for-you': 'd/ug.tab@ForYou'}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def checked_paths():
    for path, expected in ((REMOTE, REMOTE_SHA), (ADAPTER, ADAPTER_SHA)):
        need(path.is_file() and digest(path) == expected, 'pinned source mismatch: ' + str(path))


def adapter():
    spec = importlib.util.spec_from_file_location('ui_navigation_adapter', ADAPTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def command_snapshot(mod, output, phase):
    record = {'schema': 'ui-navigation-snapshot-v1', 'phase': phase,
              'scope': 'cached normal UI state only; no controller/USB/power/settings request',
              'calls': []}
    command = ('set -eu\n' +
               f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n' +
               'cat /proc/sys/kernel/random/boot_id\ncat /proc/uptime\n'
               'vconftool get memory/eden/current_tab\n'
               'enlightenment_info -topvwins\ncat /proc/uptime\n')
    text = mod.root(command, record, output / (phase + '-snapshot.json'))
    (output / (phase + '-snapshot.txt')).write_text(text)
    saver = 'ScreenSaver.dll' in text or 'ScreenSaverContent.dll' in text
    csfs = '/opt/usr/apps/com.samsung.tv.csfs/bin/csfs.dll' in text
    tab = None
    prefix = 'memory/eden/current_tab, value = '
    for line in text.splitlines():
        if line.startswith(prefix):
            tab = line[len(prefix):].split(' (', 1)[0]
            break
    summary = {'screensaver_windows_present': saver, 'csfs_window_present': csfs,
               'cached_current_tab': tab, 'physical_picture_observed': False}
    save(output / (phase + '-summary.json'), summary)
    return summary


def run_process(argv, output, label):
    done = subprocess.run(argv, capture_output=True, timeout=90)
    (output / (label + '.stdout.txt')).write_bytes(done.stdout)
    (output / (label + '.stderr.txt')).write_bytes(done.stderr)
    result = {'argv': [str(part) for part in argv], 'exit_code': done.returncode}
    save(output / (label + '.result.json'), result)
    return done


def ws_key_action(action, output, label):
    done = run_process([str(REMOTE), '--key', KEYS[action]], output, 'key-' + label)
    need(done.returncode == 0, 'normal key client failed')
    try:
        value = json.loads(done.stdout.decode())
    except Exception as exc:
        raise ValueError('normal key result is not JSON') from exc
    need(value.get('key_sent') == KEYS[action] and value.get('connected') is True,
         'normal key result contract')
    return {'key': KEYS[action], 'protocol_receipts': value.get('protocol_receipts', []),
            'backend': 'ws', 'execution_confirmed': False}


def local_key_action(action, output, mod, label):
    """Send one stock keysym down/up pair; the up is attempted after a failed down."""
    keysym = LOCAL_KEYSYMS[action]
    record = {'schema': 'ui-navigation-local-key-v1', 'action': action,
              'keysym': keysym, 'backend': 'local', 'down_attempts': 1,
              'up_attempts': 1, 'automatic_retry': False, 'calls': []}
    quoted = shlex.quote(keysym)
    command = ('set -eu\n' +
               f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n' +
               'test -x /usr/bin/input_keyevent\n'
               f'test "$(sha256sum /usr/bin/input_keyevent | cut -d " " -f1)" = {INPUT_KEYEVENT_SHA}\n'
               'down_status=0\n'
               f'/usr/bin/input_keyevent {quoted} down >/dev/null 2>&1 || down_status=$?\n'
               'sleep 0.15\n'
               'up_status=0\n'
               f'/usr/bin/input_keyevent {quoted} up >/dev/null 2>&1 || up_status=$?\n'
               'printf "LOCAL_KEY_DOWN_EXIT=%s\\n" "$down_status"\n'
               'printf "LOCAL_KEY_UP_EXIT=%s\\n" "$up_status"\n')
    text = mod.root(command, record, output / ('local-key-' + label + '.json'))
    (output / ('local-key-' + label + '.txt')).write_text(text)
    match = re.fullmatch(r'LOCAL_KEY_DOWN_EXIT=([0-9]+)\nLOCAL_KEY_UP_EXIT=([0-9]+)\n', text)
    need(match is not None, 'local key result contract')
    down, up = (int(value) for value in match.groups())
    need(down == 0 and up == 0, 'stock key down/up failed')
    return {'key': keysym, 'backend': 'local', 'hold_milliseconds': 150,
            'down_exit_code': down,
            'up_exit_code': up, 'execution_confirmed': False}


def one_key(action, backend, output, mod, label):
    return (local_key_action(action, output, mod, label)
            if backend == 'local' else ws_key_action(action, output, label))


def require_navigation_context(summary):
    need(not summary['screensaver_windows_present'],
         'navigation refused while screensaver windows remain present')
    need(summary['csfs_window_present'], 'navigation refused because CSFS is absent')
    need(summary['cached_current_tab'] in set(TARGETS.values()),
         'navigation refused on an unexpected cached page')


def normal_page_navigation(target, backend, output, mod, before):
    """Use only the owner-verified normal-key topology, one observed step at a time."""
    steps = []
    state = before
    if state['screensaver_windows_present']:
        wake = one_key('wake', backend, output, mod, 'wake')
        state = command_snapshot(mod, output, 'after-wake')
        steps.append({'action': 'wake', 'key_result': wake, 'summary': state})
    require_navigation_context(state)
    if state['cached_current_tab'] == TARGETS[target]:
        return {'page': TARGETS[target], 'normal_key_steps': steps,
                'cached_target_match': True, 'no_op': True,
                'execution_confirmed': False}

    current = state['cached_current_tab']
    # These state trajectories were physically calibrated after recovery. They
    # remain conditional on the recorded tabs; any other result is terminal.
    plans = {
        'apps': {
            'd/ug.tab@Live': [('right', 'd/apps.tab')],
        },
        'for-you': {
            'd/apps.tab': [('up', 'd/apps.tab'), ('up', 'd/apps.tab'),
                           ('left', 'd/ug.tab@Live'), ('left', 'd/ug.tab@ForYou')],
            'd/ug.tab@Live': [('up', 'd/ug.tab@Live'), ('up', 'd/ug.tab@Live'),
                               ('left', 'd/ug.tab@ForYou')],
        },
    }
    def step(action, expected):
        nonlocal state
        index = len(steps) + 1
        key_result = one_key(action, backend, output, mod, f'{index:02d}-{action}')
        state = command_snapshot(mod, output, f'after-{index:02d}-{action}')
        row = {'action': action, 'expected_cached_tab': expected,
               'key_result': key_result, 'summary': state}
        steps.append(row)
        return state['cached_current_tab']

    # The first Right from For You has two owner-observed valid outcomes:
    # sidebar -> Home content (still For You), or header -> Live.  Branch
    # explicitly instead of treating valid progress as a fault.
    if target == 'apps' and current == 'd/ug.tab@ForYou':
        first = step('right', 'd/ug.tab@ForYou or d/ug.tab@Live or d/apps.tab')
        if first == TARGETS[target]:
            return {'page': TARGETS[target], 'normal_key_steps': steps,
                    'cached_target_match': True, 'no_op': False,
                    'execution_confirmed': False}
        if first == 'd/ug.tab@Live':
            plan = [('right', 'd/apps.tab')]
        elif first == 'd/ug.tab@ForYou':
            plan = [('up', 'd/ug.tab@ForYou'), ('up', 'd/ug.tab@ForYou'),
                    ('right', 'd/ug.tab@Live'), ('right', 'd/apps.tab')]
        else:
            raise ValueError('unexpected cached page or focus state; stopped')
    else:
        plan = plans[target].get(current)
    need(plan is not None, 'no verified normal-key path from current cached page')
    need(len(steps) + len(plan) <= 8, 'navigation key bound')
    for action, expected in plan:
        actual = step(action, expected)
        if actual == TARGETS[target]:
            return {'page': TARGETS[target], 'normal_key_steps': steps,
                    'cached_target_match': True, 'no_op': False,
                    'execution_confirmed': False}
        need(actual == expected and not state['screensaver_windows_present'] and
             state['csfs_window_present'], 'unexpected cached page or focus state; stopped')
    raise ValueError('bounded navigation plan ended without target')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['snapshot', *KEYS, *TARGETS])
    parser.add_argument('--backend', choices=('local', 'ws'), default='local',
                        help='key backend only; local is the stock input_keyevent utility')
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    checked_paths()
    dry = {'schema': 'ui-navigation-dry-v1', 'action': args.action,
           'execute_required': True, 'backend': args.backend,
           'key': LOCAL_KEYSYMS.get(args.action) if args.backend == 'local' else KEYS.get(args.action),
           'page': TARGETS.get(args.action), 'target_operations': 0,
           'controller_usb_power_settings_firmware_operations': 0,
           'physical_picture_observed': False, 'execution_confirmed': False,
           'retries': 0}
    if not args.execute:
        need(args.output is None, '--output requires --execute')
        print(json.dumps(dry, separators=(',', ':')))
        return
    need(args.output is not None and args.output.is_absolute(), 'fresh absolute --output required')
    need(not args.output.exists(), 'output must not exist')
    args.output.mkdir(parents=True)
    save(args.output / 'intent.json', dict(dry, execute=True))
    mod = adapter()
    before = command_snapshot(mod, args.output, 'before')
    if args.action == 'snapshot':
        result = {'action': 'snapshot', 'before': before, 'after': before,
                  'target_operations': 0, 'physical_picture_observed': False}
    elif args.action in KEYS:
        result = one_key(args.action, args.backend, args.output, mod, 'one')
        result['before'] = before
        result['after'] = command_snapshot(mod, args.output, 'after')
        result['target_operations'] = 1
    else:
        result = normal_page_navigation(args.action, args.backend, args.output, mod, before)
        result['before'] = before
        result['after'] = result['normal_key_steps'][-1]['summary'] if result['normal_key_steps'] else before
        result['target_operations'] = len(result['normal_key_steps'])
    result.update({'schema': 'ui-navigation-result-v1', 'action': args.action,
                   'physical_picture_observed': False,
                   'controller_usb_power_settings_firmware_operations': 0,
                   'retries': 0})
    save(args.output / 'result.json', result)
    print(json.dumps(result, separators=(',', ':')))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('Stopped: ' + type(exc).__name__ + ': ' + str(exc), file=sys.stderr)
        sys.exit(1)
