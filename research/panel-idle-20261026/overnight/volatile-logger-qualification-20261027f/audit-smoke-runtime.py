#!/usr/bin/env python3
"""Authenticate and replay one finite logger qualification, entirely offline."""
import base64
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import struct
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
BUILD = BASE / 'managed-usb-secondary-logger-smoke'
RUN = HERE / 'logger-smoke-once'
# Filled only after independent review of the replacement wrapper.
REVIEWED_MANIFEST = '150189300d1fb78507e8dcad330cc1ca2ebbef05617d5741506a062986445b8b'


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    prior_path = BASE / 'rt-onset-memory-20261027c/audit-runtime.py'
    need(sha(prior_path.read_bytes()) ==
         'ef6819eae26c9b4e0210edf8ebf0470993a2030b9b6a1489c0877bd282724704',
         'pinned raw-envelope validator')
    prior = load_module('raw_validator', prior_path)
    raw = (RUN / 'record.json').read_bytes()
    record = prior.strict_json(raw)
    uploads = prior.root_calls(record)
    need(all(c['remote_timeout_seconds'] == 45 and
             c['host_timeout_limit_seconds'] == 75 for c in record['calls']),
         'reviewed outer transport margins')
    manifest_raw = (BUILD / 'build-manifest.json').read_bytes()
    manifest = json.loads(manifest_raw)
    need(sha(manifest_raw) == record['manifest_sha256'] == REVIEWED_MANIFEST,
         'independently reviewed manifest identity')
    need(record['deployment_script_sha256'] == sha((BUILD / 'run-once.py').read_bytes()) ==
         manifest['wrapper_sha256'], 'wrapper identity')
    names = {'ManagedUsbSecondaryLoggerSmoke.' + suffix
             for suffix in ('dll', 'deps.json', 'runtimeconfig.json')}
    need(set(uploads) == names, 'exact upload inventory')
    for name, row in manifest['files'].items():
        payload = (BUILD / name).read_bytes()
        need(row == {'size': len(payload), 'sha256': sha(payload)}, 'build ' + name)
        if name.startswith('bin/'):
            need(base64.b64decode(uploads[Path(name).name], validate=True) == payload,
                 'uploaded bytes ' + name)
    adapter = manifest['root_adapter']
    need(sha((BUILD / adapter['path']).read_bytes()) == adapter['sha256'] ==
         record['root_adapter_sha256'], 'margin adapter identity')
    wrapper = load_module('qualification_wrapper', BUILD / 'run-once.py')

    class Replay:
        index = 0
        final = None

        def save(self, path, value):
            self.final = value
            path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')

        def root(self, command, value, path):
            need(self.index < len(record['calls']), 'no extra root call')
            call = record['calls'][self.index]
            need(command == call['command'], 'exact command replay ' + str(self.index))
            self.index += 1
            value['calls'].append(call)
            return call['response']['commands'][0]['stdout']

    replay = Replay()
    fake_spec = SimpleNamespace(loader=SimpleNamespace(exec_module=lambda _: None))
    with tempfile.TemporaryDirectory(prefix='logger-smoke-audit-') as temporary:
        output = Path(temporary) / 'replayed'
        argv = ['run-once.py', '--execute', '--manifest-sha256', sha(manifest_raw),
                '--output', str(output)]
        with patch.object(wrapper.importlib.util, 'spec_from_file_location', return_value=fake_spec), \
             patch.object(wrapper.importlib.util, 'module_from_spec', return_value=replay), \
             patch.object(wrapper.uuid, 'uuid4', return_value=SimpleNamespace(hex=record['remote_stage'].rsplit('-', 1)[1])), \
             patch.object(sys, 'argv', argv), contextlib.redirect_stdout(io.StringIO()):
            wrapper.main()
        need(replay.index == len(record['calls']) and replay.final == record,
             'complete command and record replay')
        for path in output.iterdir():
            if path.name != 'record.json':
                need(path.read_bytes() == (RUN / path.name).read_bytes(),
                     'reconstructed artifact ' + path.name)

    active = [c for c in record['calls'] if 'ACTIVE_LOGGER_SMOKE_BEGIN' in c['command']]
    need(len(active) == 1 and active[0]['command'].count(' --execute') == 1,
         'one native invocation')
    selftest_calls = [c for c in record['calls']
                      if 'LOGGER_SMOKE_SELFTEST_BEGIN' in c['command']]
    need(len(selftest_calls) == 1 and
         record['calls'].index(selftest_calls[0]) < record['calls'].index(active[0]),
         'separately completed target selftest precedes execution')
    selftest_stdout = (RUN / 'selftest.stdout.txt').read_text()
    need(selftest_stdout == selftest_calls[0]['response']['commands'][0]['stdout'],
         'raw selftest stdout')
    wrapper.parse_selftest_stdout(selftest_stdout)
    stdout = (RUN / 'stdout.txt').read_text()
    need(stdout == active[0]['response']['commands'][0]['stdout'] and
         sha(stdout.encode()) == record['helper_stdout_sha256'], 'raw active stdout')
    outcome, helper_exit, _ = wrapper.parse_execute_stdout(stdout)
    wrapper.validate_outcome(outcome, helper_exit)
    need(outcome['Accepted'] is True, 'accepted qualification required for this audit')
    expected = [
        ('callbacks', 64), ('baseline-ring', 15372), ('prearm-rt', 64),
        ('arm', 2), ('armed-rt', 64), ('restore', 2),
        ('restored-rt', 64), ('post-ring', 15372)]
    for index, (name, count) in enumerate(expected):
        head, data = outcome['Steps'][2*index:2*index+2]
        write = name in ('arm', 'restore')
        pending = 'ExpectingWritePayload' if write else 'ExpectingReadIn'
        need(head['Name'] == name + '-header' and head['Direction'] == 'OUT' and
             head['Expected'] == head['Count'] == 12 and
             head['Before'] == 'ReadyForHeader' and head['After'] == pending,
             'header phase ' + name)
        need(data['Name'] == name + ('-payload' if write else '-data') and
             data['Direction'] == ('OUT' if write else 'IN') and
             data['Expected'] == data['Count'] == count and
             data['Before'] == pending and data['After'] == 'ReadyForHeader',
             'data phase ' + name)
        need(head['Errno'] == data['Errno'] == 0 and
             not head.get('Error') and not data.get('Error'), 'clean transfers ' + name)
    need(not outcome['Errors'], 'no native errors')
    gates = [struct.unpack_from('<H', (RUN / name).read_bytes(), 6)[0]
             for name in ('prearm-rt.bin', 'armed-rt.bin', 'restored-rt.bin')]
    need(gates == [0, 1, 0], 'actual gate readbacks')
    markers = {row['Name']: row['AtMs'] for row in outcome['Markers']}
    hold = markers['observe-end'] - markers['observe-start']
    need(3000 <= hold <= 6000, 'bounded observation')
    need(record['cleanup_deferred'] is False and record['cleanup_stdout'] == 'STAGE_ABSENT\n' ==
         record['calls'][-1]['response']['commands'][0]['stdout'], 'verified stage cleanup')
    before = (RUN / 'baseline-ring.bin').read_bytes()
    after = (RUN / 'post-ring.bin').read_bytes()
    headers = [list(struct.unpack_from('<III', data)) for data in (before, after)]
    need(all(max(row[:2]) <= 0x3c00 and row[2] in (0, 1) for row in headers),
         'ring header structural bounds')
    changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    report = dict(schema='finite-logger-runtime-audit-v1', status='PASS',
                  record_sha256=sha(raw), manifest_sha256=sha(manifest_raw),
                  exact_command_and_artifact_replay=True, root_calls=len(record['calls']),
                  exact_bulk_transfers=16, gate_readbacks=gates,
                  hold_ms=hold, ring_headers=headers, changed_ring_bytes=len(changed),
                  baseline_ring_sha256=sha(before), post_ring_sha256=sha(after),
                  cleanup='STAGE_ABSENT', physical_picture_observed=False,
                  initiating_event_captured=False, repair_established=False)
    (HERE / 'runtime-audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        retained = {}
        if RUN.exists():
            for path in sorted(RUN.iterdir()):
                if path.is_file():
                    raw = path.read_bytes()
                    retained[path.name] = {'size': len(raw), 'sha256': sha(raw)}
        failure = dict(schema='finite-logger-audit-refusal-v1',
                       status='NOT_ACCEPTED', reason=type(exc).__name__ + ': ' + str(exc),
                       retained_files=retained, restoration_proved_by_this_audit=False,
                       further_controller_io_authorized_by_this_audit=False,
                       manual_failure_analysis_required=True, repair_established=False)
        (HERE / 'runtime-audit-refusal.json').write_text(json.dumps(failure, indent=2) + '\n')
        print(json.dumps(failure, indent=2))
        raise SystemExit(1)

