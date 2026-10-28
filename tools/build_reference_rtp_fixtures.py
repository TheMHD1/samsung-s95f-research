#!/usr/bin/env python3
"""Whitelisted second-run scientific fixture builder; local file reads only."""
import argparse,json
from pathlib import Path
from build_rtp_fixtures import DP_KEYS,DM_KEYS
from verify_reference_rtp import verify


def build(source):
    base=source/'panel-idle-20261026/overnight/volatile-limit-trial-20261028dk'
    def load(name,keys):
        raw=(base/name/'native.receipt.json').read_bytes()
        if len(raw)>24576:raise ValueError('native receipt bound')
        value=json.loads(raw)
        return {k:value[k]for k in keys}
    fixture={'schema':'public-rtp-reference-fixture-v1',
             'notice':'Second, distinct unchanged-limit40 trial: last clean A0=28, postfault42. Only bounded controller/checkpoint bytes, monotonic times, counts and source identity are present. No auth/device/boot/binding/network metadata. Later sequential fixed-reference equality is conditional evidence, not historical-branch or physical-cause proof. The earlier38-to42 run remains separately published.',
             'source':{'workstream':'panel-idle-20261026/overnight/volatile-limit-trial-20261028dk',
                       'captures':['reference-baseline-01','reference-onset-01','reference-fault-01'],
                       'selected_asset_sha256':'bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0',
                       'image1_file_offset_formula':'VA+0x40200',
                       'function_vas':{'formatter':'0xc5d0','comparator':'0xbbbc','unpacker':'0xbd58','predicate':'0x1e68','fixed_dispatch':'0xb7ec'}},
             'dp40':load('reference-onset-01',DP_KEYS),
             'dtBaseline':load('reference-baseline-01',DM_KEYS+('packingQualified',)),
             'dtFault':load('reference-fault-01',DM_KEYS+('packingQualified',))}
    verify(fixture)
    return fixture


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--source',type=Path,required=True)
    cli.add_argument('--output',type=Path,required=True)
    args=cli.parse_args();args.output.write_text(json.dumps(build(args.source),indent=2,sort_keys=True)+'\n')
