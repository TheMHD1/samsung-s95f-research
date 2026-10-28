#!/usr/bin/env python3
"""One Apps-selected stock recovery after a completed DT reference fault capture."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct

B = Path(__file__).resolve().parent.parent

def load(path, pin, name):
    if hashlib.sha256(path.read_bytes()).hexdigest() != pin:
        raise ValueError(name + ' frozen source')
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj

def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--capture', required=True, type=Path)
    cli.add_argument('--output', required=True, type=Path)
    args = cli.parse_args()
    parser = load(B / 'rtp-fixed-reference-capture-20261028dt/parse-result.py',
                  '85e6d0783dc0455d4002e6e0332e23eed15d7d8b21c5ece3b3443c5529428b47', 'dk_dt_recovery_parser')
    n, raws, interpretation = parser.parse_native((args.capture / 'native.receipt.json').read_text())
    result = json.loads((args.capture / 'result.json').read_text())
    if not (result['accepted'] and result['manifestSha256'] == 'ed1e1594f3dc23528c69894c21a19c214593a0ae12c0dd20ec5ceebc9fda4d80'
            and result['headersSent'] == 14 and result['bulkTransfers'] == 28
            and result['cleanup'] == 'STAGE_ABSENT'):
        raise ValueError('completed exact DT capture required')
    expected = []
    for name, raw, digest in raws:
        if (args.capture / name).read_bytes() != raw:
            raise ValueError('DT capture raw binding')
        expected.append({'name': name, 'bytes': len(raw), 'sha256': digest})
    if result['rawFiles'] != expected:
        raise ValueError('DT wrapper raw inventory')
    start = (args.capture / 'start-R.bin').read_bytes()
    end = (args.capture / 'end-R.bin').read_bytes()
    if start != end or [struct.unpack_from('<H', start, i)[0] for i in (0, 10, 14)] != [1, 0x1001, 0]:
        raise ValueError('stable captured fault required')
    gates = load(B / 'recovery-quickpath-20261027bv/recover.py',
                 '4fddc3f6e933a19b15ba208e1ffc029ccd7df323c66cdb7ae24157f374e64a0f', 'dk_recovery_gates')
    nav = load(B / 'ui-navigation-20261027br/navigate.py',
               '74b60a9611f35a76d272b33677f773cc955838c2c6dda2c3565c371cc9d4d530', 'dk_recovery_nav')
    helper = load(B / 'autonomous-fault-harness-20261028dh/run-deadline-mode2.py',
                  'a838433923e0a6bce7a8c6b3ef810c2d4703d3a5a1061f436f93d4c7e63c5551', 'dk_stock_recovery')
    args.output.mkdir(mode=0o700)
    record = {'accepted': False, 'mode2_invocations': 0, 'threshold_writes': 0,
              'physical_picture_observed': False, 'automatic_retries': 0}
    root = gates.load_adapter()
    try:
        current = nav.command_snapshot(root, args.output, 'before')
        record['before'] = current
        if current['cached_current_tab'] == 'd/ug.tab@Live':
            nav.one_key('right', 'local', args.output, root, 'live-right')
            record['after_right'] = nav.command_snapshot(root, args.output, 'after-right')
        gate_dir = args.output / 'recovery-gates'
        gate_dir.mkdir(mode=0o700)
        record['apps_preparation'] = gates.apps_gate(gate_dir)
        gates.public_gate(gate_dir)
        record['mode2_invocations'] = 1
        record['recovery'] = helper.execute(args.output / 'mode2', helper.contract())
        record['final'] = nav.command_snapshot(root, args.output, 'final')
        record['accepted'] = record['recovery']['accepted'] and record['final']['cached_current_tab'] == 'd/apps.tab'
    except Exception as error:
        record['error'] = type(error).__name__ + ': ' + str(error)
        raise
    finally:
        (args.output / 'result.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({'accepted': record['accepted'], 'mode2_invocations': record['mode2_invocations'],
                      'threshold_writes': 0, 'physical_picture_observed': False}))

if __name__ == '__main__':
    main()
