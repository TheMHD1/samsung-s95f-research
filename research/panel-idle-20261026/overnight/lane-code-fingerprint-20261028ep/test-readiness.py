#!/usr/bin/env python3
"""Only host files and fake cached metadata responses; never loads root adapter."""
import copy
import hashlib
import json
import subprocess
import tempfile
import types
from pathlib import Path

D = Path(__file__).resolve().parent
checks = 0
commands = []

def need(ok, why):
    global checks
    checks += 1
    if not ok:
        raise ValueError(why)

def reject(fn):
    try:
        fn()
    except (ValueError, KeyError, TypeError, OSError):
        need(True, 'refusal')
        return
    raise ValueError('unexpected acceptance')

def load(name):
    path = D / name
    module = types.ModuleType(name)
    module.__file__ = str(path)
    exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
    return module

w = load('run-once.py')
p = load('prepare-readiness.py')

class Root:
    def __init__(self, mode='good', mutation=None):
        self.mode, self.mutation, self.calls = mode, mutation, 0
    def root(self, command, record, path):
        self.calls += 1
        commands.append(command)
        need(len(command.encode()) <= 8192, 'command bound')
        need(subprocess.run(['sh', '-n'], input=command.encode(), capture_output=True).returncode == 0, 'shell syntax only')
        need(not any(token in command for token in ['ioctl', 'dotnet', 'usbreset', 'input_keyevent', '--execute', 'MODE2']), 'cached metadata only')
        if self.mutation:
            self.mutation()
        if self.mode == 'throw':
            raise OSError('mock ambiguous metadata only')
        if self.mode == 'oversize':
            return 'x' * 65537
        if self.mode == 'holders':
            return 'FDCENSUS expected=120 missing=0 holders=1 errors=0\nEP_CURRENT_READY\n'
        if self.mode == 'malformed':
            return 'EP_CURRENT_READY\n'
        return 'FDCENSUS expected=120 missing=0 holders=0 errors=0\nEP_CURRENT_READY\n'

with tempfile.TemporaryDirectory(prefix='ep-readiness-host-') as td:
    base = Path(td)
    identity = {'boot': w.BOOT, 'sysfsRealpath': '/sys/devices/platform/usb/usb7/7-1',
                'sysfsStat': '42:1234', 'busnum': '7', 'devnum': '57',
                'deviceNode': '/dev/bus/usb/007/057', 'nodeStat': 'bd:338:12345',
                'descriptorsSha256': w.sha(bytes.fromhex(w.DESCRIPTORS)),
                'configuration': '1', 'authorized': '1', 'runtimeStatus': 'active',
                'interfaceNumber': '02', 'alternate': '0', 'interfaceClass': 'ff',
                'interfaceSubClass': '00', 'interfaceProtocol': '00'}
    note = base / 'phase.txt'
    note_raw = b'SYNTHETIC HOST TEST: prior exact pending read pair ended Ready; not actual target readiness.'
    note.write_bytes(note_raw)
    identity_path = base / 'identity.json'
    identity_raw = json.dumps(identity).encode()
    identity_path.write_bytes(identity_raw)
    evidence_raw = {str(note): note_raw, str(identity_path): identity_raw}
    evidence = [{'path': path, 'sha256': w.sha(raw)} for path, raw in evidence_raw.items()]
    value = p.candidate(w, identity, note, note_raw, evidence)
    root = Root()
    result = p.prepare(base / 'valid', value, w, root, evidence_raw)
    need(result['accepted'] and result['vendorTransfers'] == 0 and root.calls == 1, 'one ordinary metadata call')
    admitted, raw = w.load_readiness(Path(result['readiness']), result['sha256'])
    need(admitted['identity'] == identity and admitted['endpointQueueProof'] is False and len(admitted['evidence']) == 4, 'strict final readiness')
    need(Path(result['readiness']).stat().st_mode & 0o777 == 0o600, 'private decision mode')
    need((base / 'valid').stat().st_mode & 0o777 == 0o700, 'private directory mode')
    for key in w.META_KEYS:
        bad = copy.deepcopy(value)
        bad['identity'][key] += ';arbitrary'
        root = Root()
        reject(lambda: p.prepare(base / ('bad-' + key), bad, w, root, evidence_raw))
        need(root.calls == 0, 'unsafe identity rejected before root')
    for field, replacement in [('accepted', False), ('interfaceUnbound', False), ('noHolders', False), ('endpointQueueProof', True), ('schema', 'wrong')]:
        bad = copy.deepcopy(value)
        bad[field] = replacement
        root = Root()
        reject(lambda: p.prepare(base / field, bad, w, root, evidence_raw))
        need(root.calls == 0, 'refused premise before root')
    for mode in ['throw', 'oversize', 'holders', 'malformed']:
        root = Root(mode)
        out = base / mode
        reject(lambda: p.prepare(out, value, w, root, evidence_raw))
        need(root.calls == 1 and not (out / 'readiness.json').exists(), 'refusal no accepted decision or retry')
    root = Root(mutation=lambda: note.write_bytes(b'changed after initial admission'))
    reject(lambda: p.prepare(base / 'drift', value, w, root, evidence_raw))
    need(root.calls == 1 and not (base / 'drift/readiness.json').exists(), 'post-observation evidence drift refused')
    note.write_bytes(note_raw)
    root = Root()
    reject(lambda: p.prepare(base / 'valid', value, w, root, evidence_raw))
    need(root.calls == 0, 'no output reuse')
    for text in ['{}', '{"accepted":true,"accepted":false}', '{"a":NaN}']:
        reject(lambda: w.validate_readiness(w.strict_json(text)))
    reject(lambda: p.candidate(w, identity, note, b'short', evidence))
    reject(lambda: p.candidate(w, identity, note, note_raw, evidence * 2))
    link = base / 'alias'
    link.symlink_to(note)
    reject(lambda: p.read_regular(link, 4096))
    reject(lambda: p.read_regular(note, 1))
    wrong = copy.deepcopy(evidence_raw)
    wrong[str(note)] += b'x'
    root = Root()
    reject(lambda: p.prepare(base / 'wrong-hash', value, w, root, wrong))
    need(root.calls == 0, 'unbound evidence never calls root')

for script in ['prepare-readiness.py', 'run-once.py']:
    dry = subprocess.run(['python3', '-B', str(D / script)], check=True, capture_output=True)
    need(json.loads(dry.stdout)['targetOperations'] == 0, 'dry default no target operation')
print(json.dumps({'checksPassed': checks, 'commandsSyntaxChecked': len(commands), 'maximumCommandBytes': max(map(lambda s: len(s.encode()), commands)), 'targetOperations': 0, 'networkOperations': 0}))
