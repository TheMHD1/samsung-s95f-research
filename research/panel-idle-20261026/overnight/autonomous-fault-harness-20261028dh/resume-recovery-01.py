#!/usr/bin/env python3
"""Finish recovery after accepted onset; never replay the observation or key."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent

def load(path, pin, name):
    if hashlib.sha256(path.read_bytes()).hexdigest() != pin: raise ValueError(name + ' source changed')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    original = HERE / 'menu-onset-01'
    capture = json.loads((original / 'controller-capture/result.json').read_text())
    record = json.loads((original / 'result.json').read_text())
    if not (capture['nativeAccepted'] and capture['transportAccepted'] and capture['softwareOnsetObserved']):
        raise ValueError('accepted completed onset required')
    if 'recovery' in record or record['error'] != 'ValueError: Apps navigation failed; MODE2 withheld':
        raise ValueError('this continuation applies only before any recovery request')
    out = HERE / 'onset-01-recovery-continuation'
    out.mkdir(mode=0o700)
    result = {'schema': 'autonomous-recovery-continuation-v1', 'accepted': False,
              'fault_replays': 0, 'maximum_mode2_requests': 1,
              'physical_state': 'unobserved', 'owner_response_required': False,
              'original_trial_remains_rejected': True}
    try:
        gates = load(BASE / 'recovery-quickpath-20261027bv/recover.py',
                     '4fddc3f6e933a19b15ba208e1ffc029ccd7df323c66cdb7ae24157f374e64a0f', 'continuation_gates')
        helper = load(HERE / 'run-deadline-mode2.py',
                      'a838433923e0a6bce7a8c6b3ef810c2d4703d3a5a1061f436f93d4c7e63c5551', 'continuation_helper')
        result['apps'] = gates.apps_gate(out)
        gates.public_gate(out)
        result['mode2'] = helper.execute(out / 'mode2', helper.contract())
        result['accepted'] = True
    except Exception as error:
        result['error'] = type(error).__name__ + ': ' + str(error)
        raise
    finally:
        (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'accepted': result['accepted'], 'fault_replays': 0,
                      'mode2_requests': 1, 'physical_state': 'unobserved'}))

if __name__ == '__main__': main()
