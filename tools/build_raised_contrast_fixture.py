#!/usr/bin/env python3
"""Build a bounded scientific projection from fixed local EX captures only."""
import argparse,base64,hashlib,json
from pathlib import Path

def build(source):
    b=source/'panel-idle-20261026/overnight/limit-rechallenge-trial-20261028ex'
    def load(name):
        raw=(b/name/'native.receipt.json').read_bytes()
        if len(raw)>24576:raise ValueError('native receipt bound')
        return json.loads(raw)
    def data(raw):
        return {'bytes':len(raw),'base64':base64.b64encode(raw).decode(),'sha256':hashlib.sha256(raw).hexdigest()}
    def observe(name):
        n=load(name);s=n['scoreCheckpoints'];raw=base64.b64decode(s['rawBase64'],validate=True)
        if s['recordBytes']!=58 or s['count']!=56 or len(raw)!=58*56 or hashlib.sha256(raw).hexdigest()!=s['sha256']:raise ValueError('source checkpoint layout')
        # Preserve original bytes 0..45 and 54..57. Omit dynamic pointers 46..53.
        projected=b''.join(raw[i:i+46]+raw[i+54:i+58] for i in range(0,len(raw),58))
        keys=('terminalReason','accepted','observationAccepted','onsetObserved','protocolPhase','released','closed','writes','retries','physicalPictureObserved','cyclesStarted','cleanCyclesCompleted','quiescentCyclesCompleted','headersSent','bulkTransfers','startUs','endUs')
        r={k:n[k]for k in keys};r['projection']=dict(data(projected),recordBytes=50,count=56)
        r['retained']=[]
        for c in n['retained']:
            selected=[]
            for i,w in enumerate(c['windows']):
                if w['name'] not in {'R','M','C','H'}:continue
                raw=base64.b64decode(w['rawBase64'],validate=True)
                if hashlib.sha256(raw).hexdigest()!=w['sha256'] or len(raw)!=w['expected'] or w['count']!=len(raw)or w['complete']is not True:raise ValueError('source window')
                t=c['transfers'][2*i:2*i+2]
                selected.append(dict(data(raw),name=w['name'],beforeUs=t[0]['beforeUs'],afterUs=t[1]['afterUs']))
            r['retained'].append({'role':c['role'],'cycle':c['cycleIndex'],'windows':selected})
        return r
    def snapshot(name):
        n=load(name);keys=('accepted','protocolPhase','released','closed','writes','uiOperations','headersSent','bulkTransfers','physicalPictureObserved')
        r={k:n[k]for k in keys};r['windows']={w['name']:data(base64.b64decode(w['base64'],validate=True))for w in n['windows']if w['name']in {'start-R','end-R','M','C','start-N','end-N'}}
        for w in n['windows']:
            if w['name']in r['windows']and(r['windows'][w['name']]['sha256']!=w['sha256']or r['windows'][w['name']]['bytes']!=w['bytes']):raise ValueError('source snapshot')
        return r
    def writer(name):
        n=load(name);keys=('action','accepted','protocolPhase','released','closed','writeAttempted','writeTransportComplete','readbackVerified','headersSent','bulkTransfers','rootCauseFixEstablished','physicalPictureObserved')
        r={k:n[k]for k in keys};r['windows']={w['name']:data(base64.b64decode(w['base64'],validate=True))for w in n['windows']if w['name']in {'fresh-R','readback-R'}}
        for w in n['windows']:
            if w['name']in r['windows']and(r['windows'][w['name']]['sha256']!=w['sha256']or r['windows'][w['name']]['bytes']!=w['bytes']):raise ValueError('source writer window')
        return r
    f={'schema':'public-raised-restored-contrast-v1','notice':'Distinct sequential software exposures, not a matched optical prevention experiment. Compact rows retain instrument-classified R brackets, not unretained full R. Their fields were read sequentially, not atomically. Projection removes both dynamic pointers. Callback instructions, authenticated transport, device, boot, binding and network metadata are omitted. Comparison threshold and publication cap both change. No actual FP selection, historical comparator call, physical picture or permanent fix is established.',
       'source':{'workstream':'panel-idle-20261026/overnight/limit-rechallenge-trial-20261028ex','captures':['raised-01/set','raised-01/onset','raised-01/post-tables','restore-01','control-01/onset','explicit-control-01'],'projection':'Per original58-byte row, concatenate source bytes[0:46] and[54:58]; omit pointer bytes[46:54]. Little endian. Distinct source layouts ER/EY share this projection.'},
       'set200':writer('raised-01/set'),'raised200':observe('raised-01/onset'),'post200':snapshot('raised-01/post-tables'),'restore40':writer('restore-01'),'firstControl40':observe('control-01/onset'),'explicitControl40':snapshot('explicit-control-01')}
    from verify_raised_contrast import verify
    verify(f);return f

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    a.output.write_text(json.dumps(build(a.source),indent=2,sort_keys=True)+'\n')
