#!/usr/bin/env python3
"""Autonomous Apps/public reject checks followed by one stock initialization."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
QUICK = HERE.parent / 'recovery-quickpath-20261027bv/recover.py'
QUICK_SHA = '4fddc3f6e933a19b15ba208e1ffc029ccd7df323c66cdb7ae24157f374e64a0f'
HELPER = HERE / 'run-deadline-mode2.py'
HELPER_SHA = 'a838433923e0a6bce7a8c6b3ef810c2d4703d3a5a1061f436f93d4c7e63c5551'

def load(path, pin, name):
    if hashlib.sha256(path.read_bytes()).hexdigest() != pin:
        raise ValueError(name + ' source changed')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    out = HERE / 'autonomous-baseline-01'
    out.mkdir(mode=0o700)
    record = {'schema': 'autonomous-menu-initialization-v1', 'accepted': False,
              'physical_state': 'unobserved', 'owner_response_required': False,
              'purpose': 'establish fresh stock-initialized menu/controller baseline',
              'maximum_stock_mode2_requests': 1, 'automatic_retries': 0}
    try:
        gates = load(QUICK, QUICK_SHA, 'initialization_gates')
        helper = load(HELPER, HELPER_SHA, 'initialization_mode2')
        record['navigation'] = gates.apps_gate(out)
        gates.public_gate(out)
        record['mode2'] = helper.execute(out / 'mode2', helper.contract())
        record['accepted'] = True
        record['interpretation'] = 'stock ioctl returned zero; controller state must be measured separately'
    except Exception as error:
        record['error'] = type(error).__name__ + ': ' + str(error)
        raise
    finally:
        (out / 'result.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({'accepted': record['accepted'], 'mode2': record['mode2'],
                      'physical_state': 'unobserved', 'owner_response_required': False}))

if __name__ == '__main__':
    main()
