#!/usr/bin/env python3
"""Retain fresh cached identity/census and explicit parent protocol premise only."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
B = HERE.parent
ROOT = B / 'managed-ui-tab-launch/root-with-margin.py'
ROOT_SHA = 'bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a'
WRAPPERS = {
    'fu': ('combined-live-trigger-adapter-20261028fu/run-once.py', 'fu-combined-live-event-readiness-decision-v1'),
}

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def load(path, digest, name):
    raw = path.read_bytes()
    if sha(raw) != digest:
        raise ValueError(name + ' frozen source identity')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--wrapper', required=True, choices=WRAPPERS)
    cli.add_argument('--wrapper-sha256', required=True)
    cli.add_argument('--preparation', required=True, type=Path)
    cli.add_argument('--preparation-sha256', required=True)
    cli.add_argument('--manifest-sha256', required=True)
    cli.add_argument('--execute', action='store_true')
    cli.add_argument('--identity', required=True, type=Path)
    cli.add_argument('--phase-note', required=True, type=Path)
    cli.add_argument('--evidence', action='append', default=[], type=Path)
    cli.add_argument('--output', required=True, type=Path)
    args = cli.parse_args()
    relative, schema = WRAPPERS[args.wrapper]
    wrapper = load(B / relative, args.wrapper_sha256, 'fu_readiness_wrapper')
    manifest, _ = wrapper.build_manifest()
    manifest_raw = wrapper.manifest_bytes(manifest)
    if sha(manifest_raw) != args.manifest_sha256 or manifest_raw != (B / 'combined-live-trigger-adapter-20261028fu/deployment-manifest.json').read_bytes():
        raise ValueError('sealed derivative manifest')
    preparation = load(B / 'combined-live-trigger-adapter-20261028fu/prepare-live.py', manifest['sources']['prepare-live.py']['sha256'], 'fu_preparation_certificate')
    preparation.load_certificate(args.preparation, args.preparation_sha256, args.manifest_sha256)
    identity = json.loads(args.identity.read_text())
    note_raw = args.phase_note.read_bytes()
    statement = note_raw.decode().strip()
    if not 40 <= len(statement) <= 4096:
        raise ValueError('explicit bounded parent phase premise')
    paths = [args.phase_note, args.identity, args.preparation, *args.evidence]
    if len(paths) > 32 or len(set(paths)) != len(paths):
        raise ValueError('bounded distinct evidence')
    evidence = []
    for path in paths:
        if not path.is_absolute() or path.is_symlink() or not path.is_file():
            raise ValueError('ordinary absolute evidence')
        evidence.append({'path': str(path), 'sha256': sha(path.read_bytes())})
    candidate = {'schema': schema, 'accepted': True, 'identity': identity,
                 'interfaceUnbound': True, 'noHolders': True,
                 'closedWorldVendorOutLineage': {'accepted': True, 'statement': statement,
                                                'evidenceSha256': sha(note_raw)},
                 'evidence': evidence, 'endpointQueueProof': False}
    if not args.execute:
        print(json.dumps({'mode': 'dry', 'manifestSha256': args.manifest_sha256, 'targetOperations': 0, 'preparationValidated': True}))
        return
    args.output.mkdir(mode=0o700)
    root = load(ROOT, ROOT_SHA, 'fu_readiness_root')
    record = {'schema': 'fu-fresh-cached-readiness-v1', 'calls': []}
    text = root.root('set -eu\n' + wrapper.metadata_body(identity, 'FU_CURRENT_READY'),
                     record, args.output / 'metadata-root.json')
    (args.output / 'metadata.txt').write_text(text)
    census = wrapper.parse_metadata(text, 'FU_CURRENT_READY')
    (args.output / 'census-summary.json').write_text(json.dumps(census, indent=2) + '\n')
    # Bind the fresh observation as well as the historical phase evidence.
    for name in ['metadata.txt', 'census-summary.json']:
        path = args.output / name
        candidate['evidence'].append({'path': str(path), 'sha256': sha(path.read_bytes())})
    if len(candidate['evidence']) > 32:
        raise ValueError('evidence limit after cached observations')
    path = args.output / 'readiness.json'
    raw = (json.dumps(candidate, indent=2, sort_keys=True) + '\n').encode()
    path.write_bytes(raw)
    wrapper.load_readiness(path, sha(raw))
    for reference in candidate['evidence']:
        if sha(Path(reference['path']).read_bytes()) != reference['sha256']:
            raise ValueError('evidence changed after decision')
    print(json.dumps({'accepted': True, 'readiness': str(path), 'sha256': sha(raw),
                      'census': census, 'vendorTransfers': 0, 'endpointQueueProof': False}))

if __name__ == '__main__':
    main()
