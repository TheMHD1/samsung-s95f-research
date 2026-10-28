#!/usr/bin/env python3
"""One unattended Apps/header-to-Live onset capture and separate bounded recovery."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
BASE = HERE.parent

def load(path, pin, name):
    if hashlib.sha256(path.read_bytes()).hexdigest() != pin: raise ValueError(name + ' source identity')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def run(args, out, name, timeout=180):
    p = subprocess.run(args, capture_output=True, timeout=timeout)
    (out / (name + '.stdout')).write_bytes(p.stdout)
    (out / (name + '.stderr')).write_bytes(p.stderr)
    if p.returncode: raise ValueError(name + ' exit ' + str(p.returncode))
    return p

def main():
    out = HERE / 'menu-onset-01'
    out.mkdir(mode=0o700)
    record = {'schema': 'autonomous-menu-onset-trial-v1', 'accepted': False,
              'physical_state': 'unobserved', 'owner_response_required': False,
              'fault_observer_invocations': 0, 'maximum_recovery_mode2': 1,
              'firmware_threshold_or_protection_changes': 0, 'automatic_retries': 0}
    trace_started = False
    try:
        gates = load(BASE / 'recovery-quickpath-20261027bv/recover.py',
                     '4fddc3f6e933a19b15ba208e1ffc029ccd7df323c66cdb7ae24157f374e64a0f', 'dh_gates')
        nav = load(BASE / 'ui-navigation-20261027br/navigate.py',
                   '74b60a9611f35a76d272b33677f773cc955838c2c6dda2c3565c371cc9d4d530', 'dh_nav')
        root = gates.load_adapter()
        record['apps_preparation'] = gates.apps_gate(out)
        def apps(summary):
            if summary['cached_current_tab'] != 'd/apps.tab' or summary['screensaver_windows_present'] or not summary['csfs_window_present']:
                raise ValueError('Apps/CSFS/header context lost')
        for i in range(2):
            nav.one_key('up', 'local', out, root, 'header-' + str(i+1))
            apps(nav.command_snapshot(root, out, 'after-header-' + str(i+1)))
        readiness = HERE / 'onset-readiness-01/readiness.json'
        pin = 'bb23151f8901a8642708d14550fda6427763c86e4ca7b5ccfa16cb5d7a2dcf14'
        if hashlib.sha256(readiness.read_bytes()).hexdigest() != pin: raise ValueError('readiness changed')
        run(['python3', '-B', str(HERE / 'kernel-trace.py'), 'start', '--output', str(out / 'kernel-trace')], out, 'trace-start')
        trace_started = True
        try:
            record['fault_observer_invocations'] = 1
            run(['python3', '-B', str(BASE / 'firmware-rtp-producer-20261028df/capture/run-once.py'),
                 '--execute', '--manifest-sha256', 'ace348b57b15d27feca2bb67b88c4663535c2c72754b2cbb9ac51c88a3cc85c2',
                 '--readiness', str(readiness), '--readiness-sha256', pin,
                 '--output', str(out / 'controller-capture')], out, 'onset', timeout=240)
            record['capture'] = json.loads((out / 'controller-capture/result.json').read_text())
        finally:
            if trace_started:
                try:
                    run(['python3', '-B', str(HERE / 'kernel-trace.py'), 'stop', '--output', str(out / 'kernel-trace')], out, 'trace-stop')
                    record['kernel_trace'] = json.loads((out / 'kernel-trace/result.json').read_text())
                except Exception as error:
                    record['trace_stop_error'] = str(error)
        try:
            run(['python3', '-B', str(HERE / 'passive-log-capture.py'), 'ave-menu-onset-01', '--seconds', '30'], out, 'ave-log')
            record['ave_log'] = json.loads((HERE / 'ave-menu-onset-01/result.json').read_text())
        except Exception as error:
            record['ave_log_error'] = str(error)
        record['after_onset_ui'] = nav.command_snapshot(root, out, 'after-onset')
        capture = record['capture']
        if capture.get('softwareOnsetObserved') is True and capture.get('nativeAccepted') is True:
            # Known local topology: a single Right from Live selects Apps. The
            # old page-navigation helper rejects Live as an initial context.
            if record['after_onset_ui']['cached_current_tab'] == 'd/ug.tab@Live':
                nav.one_key('right', 'local', out, root, 'live-to-apps')
                record['after_right_ui'] = nav.command_snapshot(root, out, 'after-right')
            recovery_gates = out / 'recovery-gates'
            recovery_gates.mkdir(mode=0o700)
            record['apps_recovery_preparation'] = gates.apps_gate(recovery_gates)
            gates.public_gate(recovery_gates)
            helper = load(HERE / 'run-deadline-mode2.py',
                          'a838433923e0a6bce7a8c6b3ef810c2d4703d3a5a1061f436f93d4c7e63c5551', 'dh_recovery')
            record['recovery'] = helper.execute(out / 'recovery-mode2', helper.contract())
            record['final_ui'] = nav.command_snapshot(root, out, 'final')
        record['accepted'] = capture.get('transportAccepted') is True and capture.get('trialQualified') is True
        record['interpretation'] = 'software fault/recovery experiment only; no physical-light measurement or prevention fix'
    except Exception as error:
        record['error'] = type(error).__name__ + ': ' + str(error)
        raise
    finally:
        (out / 'result.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({'accepted': record['accepted'],
                      'software_onset_observed': record['capture']['softwareOnsetObserved'],
                      'recovery_request_completed': record.get('recovery', {}).get('accepted', False),
                      'physical_state': 'unobserved', 'owner_response_required': False}))

if __name__ == '__main__': main()
