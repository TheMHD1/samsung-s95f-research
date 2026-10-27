#!/usr/bin/env python3
"""One stock action using unchanged reviewed helpers and the old collector.

This host orchestration adds no native collector, memory window, command,
retry, or parser relaxation. It stops after the old collector terminates;
post-action X requires a separate lifecycle evidence decision.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
B = HERE.parent
SOURCE = B / 'sleep-investigation-20261027a/stock-mode2-experiment.py'
LABEL = 'stock-rt-av-20261027'
DEST = HERE / 'bracket'
BOOT = '00000000-0000-4000-8000-000000000000'
PREFLIGHT = '''set -eu
test "$(cat /proc/sys/kernel/random/boot_id)" = 00000000-0000-4000-8000-000000000000
cat /proc/uptime
vconftool get memory/enterprise/swupgrade/working_status
dbus-send --system --print-reply --reply-timeout=1500 --dest=org.tizen.system.deviced /Org/Tizen/System/DeviceD/Display org.tizen.system.deviced.display.GetPowerState
dbus-send --system --print-reply --reply-timeout=1500 --dest=org.tizen.system.deviced /Org/Tizen/System/DeviceD/Display org.tizen.system.deviced.display.GetScreenState
dbus-send --system --print-reply --reply-timeout=1000 --dest=org.tizen.system.deviced /Org/Tizen/System/DeviceD/Display org.tizen.system.deviced.display.BurnInProtectionInProgress
test "$(cat /sys/bus/usb/devices/7-1/idVendor)" = 04e8
test "$(cat /sys/bus/usb/devices/7-1/idProduct)" = 2001
test "$(cat /sys/bus/usb/devices/7-1/bcdDevice)" = 0250
test "$(cat /sys/bus/usb/devices/7-1/bConfigurationValue)" = 1
for n in 0 1 2; do test ! -L /sys/bus/usb/devices/7-1:1.$n/driver; done
cat /proc/uptime
echo DISPATCH_PREFLIGHT_COMPLETE
'''


def require(value, message):
    if not value:
        raise ValueError(message)


def save(name, value):
    (DEST / name).write_text(json.dumps(value, indent=2) + '\n')


def main():
    require(sys.argv[1:] == ['--run', '--reviewed'], 'exact one-shot invocation required')
    spec = importlib.util.spec_from_file_location('unchanged_stock_bracket', SOURCE)
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    old.identities()
    require(not DEST.exists(), 'trial already exists; never repeat')
    require(not (B / (LABEL + '.onset')).exists(), 'capture already exists')
    pre = json.loads((HERE / 'pre-x/result.json').read_text())
    require(pre['transport_accepted'] and pre['native_accepted'], 'baseline rejected')
    require(pre['terminal_reason'] == 'AlreadyFaulted' and pre['cleanup'] == 'STAGE_ABSENT',
            'baseline not cleanly faulted')
    initial = pre['retained_captures'][0]
    baseline_time = initial['last_us'] / 1e6
    require(initial['rt_states'] == ['Faulted'], 'baseline state mismatch')
    DEST.mkdir(mode=0o700)
    old.LABEL, old.DEST = LABEL, DEST
    save('intent.json', {
        'question': 'Delayed RT state after one positively observed stock lifecycle',
        'physical_state': 'unobserved', 'power_requests_maximum': 1,
        'unchanged_orchestrator_source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'unchanged_helper_pins': old.PINS, 'baseline_last_uptime': baseline_time,
        'maximum_baseline_age_seconds_at_dispatch': 600,
        'maintenance_race': 'residual update scheduling race accepted; no atomic idle claim',
        'channel_acceptance': 'AU independent lifecycle rules; whole AVOC rejection preserved',
        'post_action_X': 'withheld pending offline lifecycle and cleanup audit',
        'retry': False, 'recovery_inferred': False,
    })
    module = old.load_status()
    attempted = False
    with (DEST / 'capture.client.stdout').open('xb') as out, (DEST / 'capture.client.stderr').open('xb') as err:
        capture = subprocess.Popen([
            'python3', str(B / 'observed-hdmi-onset-capture.py'), LABEL,
            '--run', '--reviewed'], stdin=subprocess.DEVNULL, stdout=out, stderr=err)
        try:
            deadline = time.monotonic() + 55
            launch_path = B / (LABEL + '.onset') / 'launch-root-response.json'
            while True:
                require(capture.poll() is None, 'collector ended before action')
                require(time.monotonic() < deadline, 'collector launch deadline')
                try:
                    launch = json.loads(launch_path.read_text())
                except (FileNotFoundError, json.JSONDecodeError):
                    launch = {}
                if launch:
                    command = launch['commands'][0]['command']
                    module.validate_response(launch, command)
                    targets = re.findall(r'-- ([0-9]+\.[0-9]+)\) >', command)
                    require(len(targets) == 1, 'collector target ambiguous')
                    target = float(targets[0])
                    time.sleep(13)
                    break
                time.sleep(.25)
            end = target + 60
            ready = old.readiness(module, 'readiness-before-preflight')
            require(end - ready > 43, 'insufficient trace time')
            require(0 <= ready - baseline_time < 600, 'baseline too old or clock reversed')
            preflight = module.root(PREFLIGHT, {'calls': []}, DEST / 'dispatch-preflight.json')
            require('memory/enterprise/swupgrade/working_status, value = 0 (Int32)' in preflight,
                    'upgrade busy or untyped')
            require(re.findall(r'^   string "([^"\n]+)"$', preflight, re.M) == ['lcdon'],
                    'power state mismatch')
            require(re.findall(r'^   int32 (-?[0-9]+)$', preflight, re.M) == ['1', '0'],
                    'screen or maintenance state mismatch')
            require(preflight.rstrip().endswith('DISPATCH_PREFLIGHT_COMPLETE'), 'preflight incomplete')
            status = old.helper('pre-status', 'managed-tcon-status-read/run-status-read.py', end)
            require(status['execution']['result']['kernel_output_changed_from_sentinel'] is True,
                    'status sentinel unchanged')
            pin = old.helper('pre-pin', 'managed-errpin-cdev/run-errpin-cdev-input-once.py', end)
            require(pin['execution']['result']['value'] == 1, 'fault pin not asserted')
            old.helper('pre-duty', 'managed-tcon-duty-read/run-duty-read-v2.py', end)
            ready = old.readiness(module, 'readiness-before-power')
            require(end - ready > 30 and ready - baseline_time < 600, 'dispatch outside finite bracket')
            attempted = True
            save('dispatch.json', {'attempted': True, 'at_most_one': True, 'ready_uptime': ready,
                                  'baseline_age_seconds': ready - baseline_time})
            old.helper('mode2', 'managed-tcon-power-cycle-once/run-power-cycle-once.py', end)
            old.helper('post-status', 'managed-tcon-status-read/run-status-read.py', end)
            old.helper('post-pin', 'managed-errpin-cdev/run-errpin-cdev-input-once.py', end)
            old.helper('post-duty', 'managed-tcon-duty-read/run-duty-read-v2.py', end)
        finally:
            capture.wait(timeout=180)
            save('bracket-exit.json', {
                'mode2_dispatch_attempted': attempted, 'collector_exit': capture.returncode,
                'sequence_exception': repr(sys.exc_info()[1]), 'post_action_X_executed': False,
                'physical_state': 'unobserved', 'recovery_inferred': False,
                'next_step': 'Independent raw lifecycle and guarded cleanup audit, no automatic action',
            })


if __name__ == '__main__':
    main()
