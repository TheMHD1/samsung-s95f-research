#!/usr/bin/env python3
"""Whitelist the separate reversible-limit comparison; reads retained files only."""
import argparse,json
from pathlib import Path
from build_rtp_fixtures import DP_KEYS

DV_KEYS=('schema','action','protocolPhase','stage','opened','claimed','released','closed',
         'writeAttempted','writeTransportComplete','readbackVerified','limitMayHaveChanged',
         'accepted','physicalPictureObserved','rootCauseFixEstablished','headersSent',
         'bulkTransfers','errors','steps')

def build(source):
    base=source/'panel-idle-20261026/overnight/volatile-limit-trial-20261028dk'
    def load(name):
        raw=(base/name/'native.receipt.json').read_bytes()
        if len(raw)>24576:raise ValueError('receipt bound')
        return json.loads(raw)
    def writer(name):
        n=load(name);r={k:n[k]for k in DV_KEYS}
        # This window contains OEM instructions. Preserve extent, not the bytes
        # or their digest; callback admission remains separately reviewed evidence.
        r['windows']=[{'name':'callbacks','bytes':64,'rawOmitted':True}if w['name']=='callbacks'else w for w in n['windows']]
        return r
    def observer(name):
        n=load(name);return {k:n[k]for k in DP_KEYS}
    f={'schema':'public-rtp-limit-comparison-v1',
       'notice':'Separate reversible RAM-limit experiment. Both limit200 and restored40 observations stayed clean. No score above40 was observed at200, so prevention is unproven. Whitelisted bounded arrays, counts and monotonic times only; no authentication, boot, device, binding or network metadata. OEM callback bytes are omitted. Sequential reads are not atomic snapshots; physical picture was not observed.',
       'source':{'workstream':'panel-idle-20261026/overnight/volatile-limit-trial-20261028dk',
                 'captures':['dv-set-01','dv-observation-01','dv-restore-01','dv-rechallenge-01'],
                 'writeAddress':'0x470124c4','writeBytes':2,
                 'writeHeaderHex':'02010000c424014702000000'},
       'set200':writer('dv-set-01'),'observe200':observer('dv-observation-01'),
       'restore40':writer('dv-restore-01'),'rechallenge40':observer('dv-rechallenge-01')}
    from verify_limit_rtp import verify
    verify(f);return f

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.write_text(json.dumps(build(a.source),indent=2,sort_keys=True)+'\n')
