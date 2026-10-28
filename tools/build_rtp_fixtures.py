#!/usr/bin/env python3
"""Build a whitelisted scientific subset from retained files; no device/network code."""
import argparse
import json
from pathlib import Path

DP_KEYS = ('schema','scoreCheckpoints','intervention','observationAccepted','terminalReason',
           'protocolPhase','opened','claimed','released','closed','accepted','onsetObserved',
           'onsetMissed','physicalPictureObserved','busContentsAltered','writes','retries',
           'cyclesStarted','cleanCyclesCompleted','cleanCyclesDiscarded','bulkTransfers',
           'headersSent','inputsCompleted','startUs','deadlineUs','endUs','overshootUs','retained')
DM_KEYS = ('schema','protocolPhase','opened','claimed','released','closed','accepted',
           'headersSent','bulkTransfers','writes','uiOperations','atomicSnapshot',
           'physicalPictureObserved','steps','windows','errors')


def build(source):
    base=source/'panel-idle-20261026/overnight/volatile-limit-trial-20261028dk'
    def load(name, keys):
        raw=(base/name/'native.receipt.json').read_bytes()
        if len(raw)>24576:raise ValueError('native receipt bound')
        value=json.loads(raw)
        return {key:value[key] for key in keys}
    result={'schema':'public-rtp-dp40-dm-fixture-v1',
            'notice':'Whitelisted bounded controller windows/checkpoints, monotonic times, counters and source provenance only. No boot/device/binding/authentication/network state. Private transport/readiness was reviewed separately and is not reauthenticated by this fixture. Sequential source-compatible data do not prove record epoch, historical fixed-A branch, physical light state, or prevention.',
            'source':{'workstream':'panel-idle-20261026/overnight/volatile-limit-trial-20261028dk',
                      'captures':['score-baseline-01','record-baseline-01','record-fault-01'],
                      'selected_asset_sha256':'bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0',
                      'image1_file_offset_formula':'VA+0x40200',
                      'function_vas':{'formatter':'0xc5d0','comparator':'0xbbbc','unpacker':'0xbd58','predicate':'0x1e68','fixed_dispatch':'0xb7ec'}},
            'dp40':load('score-baseline-01',DP_KEYS),
            'dmBaseline':load('record-baseline-01',DM_KEYS),
            'dmFault':load('record-fault-01',DM_KEYS)}
    # Verify the entire subset before writing it; only this strict schema is emitted.
    from verify_rtp import verify
    verify(result)
    return result


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--source',type=Path,required=True)
    cli.add_argument('--output',type=Path,required=True)
    args=cli.parse_args()
    args.output.write_text(json.dumps(build(args.source),indent=2,sort_keys=True)+'\n')
