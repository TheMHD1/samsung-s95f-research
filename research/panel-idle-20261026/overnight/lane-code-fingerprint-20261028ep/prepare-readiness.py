#!/usr/bin/env python3
"""Fixed EP cached metadata/census preparation; dry by default, no vendor I/O."""
import argparse
import hashlib
import json
import re
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent

def need(ok, why):
    if not ok:
        raise ValueError(why)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def read_regular(path, cap):
    need(path.is_absolute() and not path.is_symlink() and path.is_file(), 'absolute ordinary evidence file')
    with path.open('rb') as source:
        raw = source.read(cap + 1)
    need(len(raw) <= cap, 'bounded evidence file')
    return raw

def load_wrapper(digest):
    need(type(digest) is str and re.fullmatch('[0-9a-f]{64}', digest), 'wrapper digest')
    path = HERE / 'run-once.py'
    raw = path.read_bytes()
    need(sha(raw) == digest, 'reviewed wrapper pin')
    wrapper = types.ModuleType('ep_readiness_wrapper')
    wrapper.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), wrapper.__dict__)
    return wrapper

def candidate(wrapper, identity, note_path, note_raw, evidence):
    statement = note_raw.decode('utf8').strip()
    need(40 <= len(statement) <= 4096, 'explicit bounded central first-header premise')
    need(1 <= len(evidence) <= 30 and len({row['path'] for row in evidence}) == len(evidence), 'bounded distinct evidence')
    value = {'schema': 'ep-lane-code-fingerprint-readiness-decision-v1', 'accepted': True,
             'identity': identity, 'interfaceUnbound': True, 'noHolders': True,
             'closedWorldVendorOutLineage': {'accepted': True, 'statement': statement,
                                           'evidenceSha256': sha(note_raw)},
             'evidence': evidence, 'endpointQueueProof': False}
    # Validate every shell-interpolated identity field before loading/calling a
    # root adapter. This is an in-memory check, not an accepted decision file.
    wrapper.validate_readiness(value)
    need(str(note_path) in {r['path'] for r in evidence}, 'phase note evidence')
    return value

def prepare(output, value, wrapper, root, evidence_bytes):
    wrapper.validate_readiness(value)
    need(output.is_absolute() and not output.exists() and not output.is_symlink(), 'fresh private output')
    for row in value['evidence']:
        need(row['path'] in evidence_bytes and sha(evidence_bytes[row['path']]) == row['sha256'], 'evidence bytes binding')
    output.mkdir(mode=0o700)
    record = {'schema': 'ep-fresh-cached-readiness-v1', 'calls': []}
    command = 'set -eu\n' + wrapper.metadata_body(value['identity'], 'EP_CURRENT_READY')
    need(len(command.encode()) <= 8192, 'ordinary metadata command cap')
    text = root.root(command, record, output / 'metadata-root.json')
    need(type(text) is str and len(text.encode()) <= 65536, 'ordinary metadata response cap')
    metadata = output / 'metadata.txt'
    metadata.write_text(text)
    metadata.chmod(0o600)
    census = wrapper.parse_metadata(text, 'EP_CURRENT_READY')
    census_path = output / 'census-summary.json'
    census_path.write_text(json.dumps(census, indent=2) + '\n')
    census_path.chmod(0o600)
    # Existing evidence remains required; cached observations supplement rather
    # than manufacture the centrally supplied pending-pair/first-header premise.
    value = {**value, 'evidence': [*value['evidence'], *[
        {'path': str(p), 'sha256': sha(p.read_bytes())} for p in [metadata, census_path]] ]}
    wrapper.validate_readiness(value)
    for row in value['evidence']:
        need(sha(read_regular(Path(row['path']), 8 * 1024 * 1024)) == row['sha256'], 'evidence changed after observation')
    raw = (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()
    need(len(raw) <= 32768, 'readiness byte cap')
    path = output / 'readiness.json'
    path.write_bytes(raw)
    path.chmod(0o600)
    wrapper.load_readiness(path, sha(raw))
    return {'accepted': True, 'readiness': str(path), 'sha256': sha(raw), 'census': census,
            'vendorTransfers': 0, 'endpointQueueProof': False, 'rootCalls': 1}

def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--execute', action='store_true')
    cli.add_argument('--wrapper-sha256')
    cli.add_argument('--manifest-sha256')
    cli.add_argument('--identity', type=Path)
    cli.add_argument('--phase-note', type=Path)
    cli.add_argument('--evidence', action='append', default=[], type=Path)
    cli.add_argument('--output', type=Path)
    args = cli.parse_args()
    if not args.execute:
        print(json.dumps({'schema': 'ep-readiness-dry-v1', 'targetOperations': 0, 'vendorTransfers': 0, 'rootCalls': 0}))
        return
    need(args.identity is not None and args.phase_note is not None and args.output is not None, 'local evidence and fresh output required')
    wrapper = load_wrapper(args.wrapper_sha256)
    manifest, _ = wrapper.build_manifest()
    need(args.manifest_sha256 == wrapper.sha(wrapper.manifest_bytes(manifest)), 'reviewed manifest pin')
    identity_raw = read_regular(args.identity, 32768)
    identity = wrapper.strict_json(identity_raw)
    paths = [args.identity, args.phase_note, *args.evidence]
    need(len(paths) <= 30 and len(set(paths)) == len(paths), 'bounded distinct evidence paths')
    raw_by_path = {str(p): read_regular(p, 8 * 1024 * 1024) for p in paths}
    note_raw = raw_by_path[str(args.phase_note)]
    need(len(note_raw) <= 4096, 'phase note byte cap')
    evidence = [{'path': str(p), 'sha256': sha(raw_by_path[str(p)])} for p in paths]
    value = candidate(wrapper, identity, args.phase_note, note_raw, evidence)
    # This module is loaded only after all local hashes, identity and premise
    # validation. Source authors/tests supply mocks and never reach this line.
    root = wrapper.load_pinned(wrapper.ROOT, wrapper.ROOT_SHA, 'ep_readiness_root')
    need(root.REMOTE_TIMEOUT_SECONDS == 45 and root.HOST_TIMEOUT_SECONDS == 75 and root.MAX_COMMAND == 8192 and root.MAX_RESPONSE == 65536, 'root bounds')
    print(json.dumps(prepare(args.output, value, wrapper, root, raw_by_path)))

if __name__ == '__main__':
    main()
