#!/usr/bin/env python3
"""Assemble the reviewed native pins and finite detached wrapper, offline."""
from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
NATIVE_SHA = '316d92b64be47767cb8461d4cbde30b9446d901060b2de798da605d9f1c8131c'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def need(ok, why):
    if not ok:
        raise ValueError(why)


def main():
    raw = (HERE / 'native-build-manifest.json').read_bytes()
    need(sha(raw) == NATIVE_SHA, 'independently cleared native manifest')
    native = json.loads(raw)
    for group in ('files', 'offline_files'):
        for name, row in native[group].items():
            data = (HERE / name).read_bytes()
            need(row == dict(size=len(data), sha256=sha(data)), name)
    rows = {}
    for name in ('run-once.py', 'root-with-margin.py', 'build-wrapper.py',
                 'test-wrapper.py', 'README-qualified.md'):
        data = (HERE / name).read_bytes()
        rows[name] = dict(size=len(data), sha256=sha(data))
    manifest = dict(schema='usb-fixed-secondary-logger-onset-qualified-build-v1',
                    native_manifest_sha256=NATIVE_SHA, local_files=rows,
                    parent_wrapper_sha256='eeb852c8e1b9a0d2611abc17e853ad2ee834f4e42712b2810bf8309eda5e59ca',
                    root_adapter_sha256='bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a',
                    transport=dict(remote_seconds=45, host_seconds=75,
                                   max_command_bytes=8192, max_response_bytes=65536),
                    execution=dict(detached=True, new_session=True, setsid_force_fork=True,
                                   actual_supervisor_handshake_seconds=1,
                                   supervisor_survival_recheck_seconds=0.2,
                                   inherited_fds_closed_above=2,
                                   script_as_data=True, ready_deadline_seconds=8,
                                   post_ready_root_silence_seconds=22, completion_deadline_seconds=65,
                                   max_stdout_bytes=50000, max_stderr_bytes=2048,
                                   automatic_ui=False, retries=0, kill=False),
                    target_operations_during_build=0)
    path = HERE / 'build-manifest.json'
    path.write_text(json.dumps(manifest, indent=2) + '\n')
    wrapper = HERE / 'run-once.py'
    dry = subprocess.run(['python3', str(wrapper)], capture_output=True, text=True)
    need(dry.returncode == 0 and json.loads(dry.stdout)['target_operations'] == 0,
         'dry default')
    with tempfile.TemporaryDirectory(prefix='onset-wrapper-check-') as temporary:
        output = Path(temporary) / 'refused'
        wrong = subprocess.run(['python3', str(wrapper), '--execute', '--manifest-sha256',
                                '0'*64, '--output', str(output)], capture_output=True)
        need(wrong.returncode != 0 and not output.exists(), 'wrong pin before output/stage')
        spec = importlib.util.spec_from_file_location('onset_syntax', wrapper)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        script = Path(temporary) / 'supervisor.sh'
        script.write_bytes(module.supervisor('/tmp/researcher-usb-onset-'+'0'*32))
        checked = subprocess.run(['/bin/sh', '-n', str(script)], capture_output=True)
        need(checked.returncode == 0, 'supervisor syntax')
        parent_spec = importlib.util.spec_from_file_location(
            'qualified_parent_syntax', HERE.parent / 'managed-usb-secondary-logger-smoke/run-once.py')
        parent = importlib.util.module_from_spec(parent_spec)
        parent_spec.loader.exec_module(parent)
        launch = module.launch_command('/tmp/researcher-usb-onset-'+'0'*32, 'true\n', parent)
        launch_checked = subprocess.run(['/bin/sh', '-n'], input=launch,
                                        capture_output=True, text=True)
        need(launch_checked.returncode == 0 and len(launch.encode()) <= 8192,
             'qualified launcher syntax and bound')
    expected = dict(count=19, status='PASS', target_operations=0, tests=[
        'qualified-launcher-source-contract', 'local-qualified-launcher-lifecycle',
        'accepted-detached-ready-grace', 'selftest-size-variation-accepted',
        'selftest-oversize-and-fixed-fields-refused', 'ambiguous-launch-safe-stop',
        'invalid-actual-supervisor-handshake-refused',
        'early-prearm-reject-retained', 'invalid-ready-refused',
        'oversized-output-refused', 'nonempty-launch-diagnostic-retained',
        'launcher-mismatch-refused',
        'stale-ready-refused', 'stale-probe-refused', 'child-mismatch-refused',
        'cmdline-mismatch-refused', 'completion-absent-retained',
        'ready-binding-mismatch-retained', 'cleanup-residue-retained'])
    results = []
    for flags in ([], ['-O']):
        run = subprocess.run(['python3', *flags, str(HERE / 'test-wrapper.py')],
                             capture_output=True, text=True)
        need(run.returncode == 0 and run.stderr == '' and json.loads(run.stdout) == expected,
             'exact wrapper integration result ' + repr(flags))
        results.append(dict(flags=flags, exit_code=run.returncode, result=expected))
    manifest['wrapper_test_results'] = results
    path.write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(dict(status='PASS', native_manifest_sha256=NATIVE_SHA,
                          manifest_sha256=sha(path.read_bytes()),
                          target_operations=0, dry_default=True,
                          bad_manifest_refused=True, supervisor_syntax=True,
                          launcher_syntax=True, wrapper_tests=19)))


if __name__ == '__main__':
    main()
