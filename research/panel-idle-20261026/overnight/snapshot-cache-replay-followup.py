#!/usr/bin/env python3
"""Preserve the local replay/branch-read phase; never contact TV or overwrite evidence."""
from pathlib import Path
import argparse
import ast
import datetime
import hashlib
import json
import os
import tempfile
import types

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / 'overnight/cache-replay-followup-evidence-manifest.json'
PRIOR = BASE / 'overnight/pqe-policy-followup-evidence-manifest.json'
PRIOR_SHA = '775f470de4109b6fc66996fc0408f431fcac94ea424068a3dddd71ae8ff534af'
HELPER = BASE / 'overnight/snapshot-pqe-policy-followup.py'
HELPER_SHA = '74b7e31cab42fa23938aefb32544b1d7111511e33b14cd49d3459cd78c08a43b'
READER_SHA = '84ff5138a7c4551b932b10360eb6b98d806dc2ef385497b4ec2f7123d6c27acb'
TEST_SHA = '750195a7a6f691cb209046406cb47301378cde2e5d6bc1942c2f3fae92bf8df6'
CAPTURE_SHA = 'cbe095e744204e89d855996f5fa8d66bb7226966146723679a0b93ed0faa57c8'
ARCHIVE = BASE / 'overnight/pqe-branch-reader-reviews/84ff5138a7c4551b-750195a7a6f6'
STEM = BASE / 'overnight/pqe-branch-baseline-20261026T181903Z'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def definitions(path, raw):
    module = types.ModuleType('frozen_local_definitions')
    module.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def arithmetic_definitions(path, raw):
    # Exact source is hash-pinned before this call. Load only its pure arithmetic
    # functions, without requiring the disassembler imports used by its CLI.
    required = {'require', 'u32', 's32', 'mul32', 'trunc_div', 'magic_signed_div',
                'weber_formula', 'auto_power_off', 'final_clamp'}
    nodes = [node for node in ast.parse(raw, filename=str(path)).body
             if isinstance(node, ast.FunctionDef) and node.name in required]
    require({node.name for node in nodes} == required, 'Arithmetic definitions missing')
    module = types.ModuleType('frozen_local_arithmetic')
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), module.__dict__)
    return module


def helpers():
    raw = HELPER.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == HELPER_SHA, 'Historical helper changed')
    return definitions(HELPER, raw)


def verify_prior(h):
    record, fingerprint = h.checked_json(PRIOR)
    require(fingerprint['sha256'] == PRIOR_SHA and len(record['files']) == 81,
            'Previous snapshot identity changed')
    h.verify_rows(record['files'])
    historical = h.previous_snapshots()
    require(record['previous_snapshots'] == historical, 'Historical snapshot chain differs')
    return {'path': str(PRIOR.relative_to(BASE)), **fingerprint,
            'files_verified': 81, 'earlier_snapshots': historical}


def build_payload(h):
    previous = verify_prior(h)
    names = [
        'snapshot-cache-replay-followup.py', 'cache-replay-and-branch-state-progress.md',
        'cache-replay-followup-review.md', 'pqe-branch-baseline-independent-review.md',
        'pqe-branch-baseline.py', 'pqe-branch-baseline-tests.py',
    ]
    paths = {BASE / 'overnight' / name for name in names}
    paths.update([PRIOR, HELPER])
    names = [
        'qd-kernel-output-replay.md', 'qd-kernel-output-replay-reproduce.py',
        'qd-kernel-output-replay.disasm',
        'qd-resume-record-replay.md', 'qd-resume-record-reproduce.py',
        'qd-onecommand-buffer-dataflow.md', 'qd-onecommand-buffer-reproduce.py',
        'qd-onecommand-buffer-reproduced.disasm',
        'qd-rosem-cache-lifecycle.md', 'qd-rosem-cache-lifecycle-reproduce.py',
        'qd-mute-concurrency.md', 'qd-mute-concurrency-proof.sh',
    ]
    paths.update(BASE / 'tcon-research' / name for name in names)
    paths.update(BASE / 'binaries' / name for name in ['libave.so.0.1', 'qdf_tcon.ko'])

    archive_manifest = ARCHIVE / 'manifest.json'
    archive, archive_id = h.checked_json(archive_manifest)
    require(ARCHIVE.is_dir() and not ARCHIVE.is_symlink(), 'Invalid review archive')
    require(set(archive['files']) == {'pqe-branch-baseline.py',
            'pqe-branch-baseline-tests.py', 'remote-read-command.sh'}, 'Archive payload set')
    entries = {p.name for p in ARCHIVE.iterdir()}
    if '__pycache__' in entries:
        cache = ARCHIVE / '__pycache__'
        require(cache.is_dir() and not cache.is_symlink(), 'Invalid bytecode directory')
        entries.remove('__pycache__')
    require(entries == {'manifest.json', *archive['files']}, 'Unexpected archive entry')
    parsed = {archive_manifest: archive_id}
    paths.add(archive_manifest)
    for name, expected in archive['files'].items():
        require(Path(name).name == name and h.identity(ARCHIVE / name) == expected,
                'Archive bytes differ')
        paths.add(ARCHIVE / name)
    for name, expected_sha in [('pqe-branch-baseline.py', READER_SHA),
                               ('pqe-branch-baseline-tests.py', TEST_SHA)]:
        expected = archive['files'][name]
        require(expected['sha256'] == expected_sha and
                h.identity(BASE / 'overnight' / name) == expected, 'Active reviewed bytes differ')
    reader_path = BASE / 'overnight/pqe-branch-baseline.py'
    reader_id, reader_raw = h.read_stable(reader_path, retain=True)
    require(reader_id['sha256'] == READER_SHA, 'Reader changed before local validation')
    reader = definitions(reader_path, reader_raw)

    capture_path = Path(str(STEM) + '.json')
    record, capture_id = h.checked_json(capture_path)
    parsed[capture_path] = capture_id
    require(capture_id['sha256'] == CAPTURE_SHA, 'Actual capture changed')
    intent_path = Path(str(STEM) + '.intent.json')
    intent, intent_id = h.checked_json(intent_path)
    parsed[intent_path] = intent_id
    require(intent['archive'] == str(ARCHIVE) and intent['physical_state'] == 'unobserved',
            'Intent qualification changed')
    require(intent['hashes'] == {'pqe-branch-baseline.py': READER_SHA,
                                 'pqe-branch-baseline-tests.py': TEST_SHA}, 'Intent source hashes')
    command = record['command'].encode()
    command_id = {'bytes': len(command), 'sha256': hashlib.sha256(command).hexdigest()}
    require(command_id == archive['files']['remote-read-command.sh'] and
            command.decode() == reader.build_command(), 'Command bytes changed')
    require(intent['command_sha256'] == command_id['sha256'] and
            intent['command_bytes'] == record['command_bytes'] == archive['command_bytes'] == 4661,
            'Intent/command lengths differ')
    require(record['accepted'] is True and record['physical_state'] == 'unobserved' and
            record['atomic'] is False and record['contract'] == reader.static_contract(),
            'Capture qualification/contract changed')
    transport = record['transport']
    require(transport['exit_code'] == 0 and transport['stderr'] == '', 'Controller status changed')
    response = json.loads(transport['stdout'])
    require(len(response['commands']) == 1 and response['commands'][0]['command'] == record['command'],
            'Nested command differs')
    require(reader.validate_response(response, record['contract']) == record['summary'],
            'Raw capture does not validate to saved summary')

    model_path = Path(str(STEM) + '.conditional-model.json')
    model, model_id = h.checked_json(model_path)
    parsed[model_path] = model_id
    require(model['input_record_sha256'] == CAPTURE_SHA and
            model['current_branch_inferred'] is False and model['physical_state'] == 'unobserved',
            'Conditional model provenance/qualification differs')
    arithmetic_path = BASE / 'tcon-research/qd-final-duty-reproduce.py'
    arithmetic_id, arithmetic_raw = h.read_stable(arithmetic_path, retain=True)
    require(arithmetic_id['sha256'] == model['model_source_sha256'] ==
            '5287b7caf0ff4c9d1c52abf0f67783c36b2052e12de126f8a4d2ac206512d4f0',
            'Conditional arithmetic source differs')
    arithmetic = arithmetic_definitions(arithmetic_path, arithmetic_raw)
    state = record['summary']['branch_state']
    f8, fc = state['sources_00f8_00fc']
    scale, auto = state['gain_autodim_02a4_02a8']
    gain = record['summary']['decoded']['weber_gain']['words'][0]
    candidate = arithmetic.weber_formula(fc, f8, state['weight_0098'], gain, scale)
    working, count = arithmetic.auto_power_off(fc, candidate, auto, state['auto_power_off_count'])
    final = arithmetic.final_clamp(working, state['model_0188_control_018c'][0])
    require([candidate, working, count, final] == [model['conditional_candidate'],
            model['conditional_auto_power_off_working'], model['conditional_count'],
            model['conditional_final_clamp_result']], 'Conditional calculation differs')
    require(model['captured_working_values'] == record['summary']['decoded']['qd_working_duty']['words']
            and model['captured_backend_cache'] == record['summary']['decoded']['backend_cache']['words'][0],
            'Conditional record copied observations differ')
    for suffix in ['.json', '.intent.json', '.driver.stdout', '.driver.stderr', '.conditional-model.json']:
        paths.add(Path(str(STEM) + suffix))
    files = []
    for path in sorted(paths):
        fingerprint = h.identity(path)
        if path in parsed:
            require(fingerprint == parsed[path], f'Parsed input changed: {path}')
        files.append({'path': str(path.relative_to(BASE)), **fingerprint})
    h.verify_rows(files)
    require(verify_prior(h) == previous, 'Historical inputs changed during validation')
    return {'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'goal_complete': False, 'repair_deployed': False,
            'physical_picture_state': 'unobserved', 'root_status': 'host-assisted; not untethered',
            'previous_snapshot': previous,
            'capture': {'path': str(capture_path.relative_to(BASE)), 'accepted': True,
                        'physical_state': 'unobserved', 'atomic': False, **capture_id},
            'actual_actions': ['Offline RE, local reproduction and review',
                               'One finite read-only branch-state baseline'],
            'not_performed': ['Display/power/factory control or target getter/setter/ioctl',
                              'Service restart, cache forcing, firmware/kernel patch',
                              'Physical recovery/prevention validation'],
            'qualification': 'Hashes preserve bounded evidence and reviewed source revisions, not physical truth or fault causality. Conditional model is not branch execution. Historical reports retain earlier scope. Generated bytecode and mutable CURRENT navigation excluded.',
            'files': files}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--check-only', action='store_true')
    modes.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    h = helpers()
    if args.verify_only:
        record, fingerprint = h.checked_json(OUT)
        require(record['goal_complete'] is False and record['repair_deployed'] is False,
                'Unsupported completion/repair claim')
        require(record['previous_snapshot'] == verify_prior(h), 'Previous anchors changed')
        h.verify_rows(record['files'])
        print(json.dumps({'verified': True, 'files': len(record['files']), **fingerprint}))
        return
    require(not OUT.exists() and not OUT.is_symlink(), 'Snapshot destination already exists')
    payload = build_payload(h)
    if args.check_only:
        print(json.dumps({'check_only': True, 'files': len(payload['files']),
                          'capture_accepted': payload['capture']['accepted']}))
        return
    descriptor, temporary = tempfile.mkstemp(prefix='.cache-replay-snapshot-', dir=OUT.parent)
    try:
        with os.fdopen(descriptor, 'w') as stream:
            json.dump(payload, stream, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, OUT)
        parent = os.open(OUT.parent, os.O_DIRECTORY)
        try:
            os.fsync(parent)
        finally:
            os.close(parent)
    finally:
        os.unlink(temporary)
    print(json.dumps({'path': str(OUT), 'files': len(payload['files']), **h.identity(OUT)}))


if __name__ == '__main__':
    main()
