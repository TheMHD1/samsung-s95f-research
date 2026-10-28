#!/usr/bin/env python3
"""Build the sixth bounded scientific projection from explicit private FH inputs.
Original receipts are intentionally absent from a public clone. The standalone
verify_logger_reconciliation.py needs only the resulting public fixture.
"""
import argparse,base64,hashlib,json
from pathlib import Path

def build(source):
    root=source/'panel-idle-20261026/overnight/combined-event-trial-20261028fh'
    def load(relative):return json.loads((root/relative).read_bytes())
    def data(raw):return {'bytes':len(raw),'base64':base64.b64encode(raw).decode(),'sha256':hashlib.sha256(raw).hexdigest()}
    a=load('capture-01/native.receipt.json');r=load('logger-restore-01/native.receipt.json');v=load('final-eb-validation/native.receipt.json');completed=load('parent-completed-checkpoint.json')
    if (root/'capture-01/result.json').exists()or a['accepted']is not False:raise ValueError('original workflow refusal')
    if a['error']!='InvalidOperationException: C geometry/category/selector':raise ValueError('original semantic refusal')
    def raw(w,key):
        b=base64.b64decode(w[key],validate=True)
        if 'sha256'in w and hashlib.sha256(b).hexdigest()!=w['sha256']:raise ValueError('private source window hash')
        if 'count'in w and w['count']!=len(b):raise ValueError('private source complete count')
        return b
    def selected(c):
        out=[]
        for i,w in enumerate(c['windows']):
            if w['name']not in {'R','M','C','H'}:continue
            b=raw(w,'raw');t=c['transfers'][2*i:2*i+2]
            out.append(dict(data(b),name=w['name'],beforeUs=t[0][4],afterUs=t[1][5]))
        return {'role':c['role'],'cycle':c['cycle'],'windows':out}
    rows=base64.b64decode(a['rows']['rawBase64'],validate=True)
    if len(rows)!=18*58 or hashlib.sha256(rows).hexdigest()!=a['rows']['sha256']:raise ValueError('source rows')
    projected=b''.join(rows[i:i+46]+rows[i+54:i+58]for i in range(0,len(rows),58))
    original={k:a[k]for k in ['accepted','phase','released','closed','headers','bulks','inputs','writes','retries','threshold','restoreAttempted','loggerMayRemain','cyclesStarted','cleanCycles','quiescentCycles','startUs','endUs']}
    original.update(errorClass='C geometry/category/selector',wrapperAccepted=False,projection=dict(data(projected),recordBytes=50,count=18),controls={c['role']:data(raw(c['windows'][0],'raw'))for c in a['controls']if c['role']in {'prearm-R','armed-R'}},retained=[selected(c)for c in a['retained']])
    restore={k:r[k]for k in ['accepted','phase','released','closed','headers','bulks','inputs','writes','retries','restore','restoreAttempted','loggerMayRemain','thresholdWrites','arms','uiOperations','resets','startUs','endUs']}
    restore['windows']=[dict(data(raw(c['windows'][0],'rawBase64')),name=c['windows'][0]['name'])for c in r['retained']if c['windows']]
    restore['pairBracketsUs']=[[c['transfers'][0]['beforeUs'],c['transfers'][-1]['afterUs']]for c in r['retained']]
    final={k:v[k]for k in ['accepted','protocolPhase','released','closed','headersSent','bulkTransfers','writes','uiOperations','physicalPictureObserved']}
    final['windows']={w['name']:data(raw(w,'base64'))for w in v['windows']if w['name']in {'start-R','end-R','M','C','start-N','end-N'}}
    f={'schema':'public-logger-refusal-restoration-v1','notice':'Typed scientific projection only: original private authenticated envelopes, device/binding/readiness identity, pointer windows, ring text and OEM instructions are withheld. Known native phase does not make the original workflow accepted. FM pre-write Clean prevents attributing Clean to logger-off. Final software validation and cached UI are not optical evidence. Public verification does not claim original transport provenance.','source':{'workstream':'panel-idle-20261026/overnight/combined-event-trial-20261028fh','captures':['capture-01','logger-restore-01','final-eb-validation'],'rowProjection':'Original58-byte row[0:46]+[54:58], removing both dynamic pointer fields.'},'originalRefusal':original,'restoration':restore,'finalValidation':final,'finalCachedUi':{'apps':True,'saver':True,'physicalPictureObserved':False},'resetsInSequence':completed['rebootsOrMode2'],'thresholdWritesInSequence':completed['thresholdWrites'],'cleanStateCausedByLoggerRestore':False,'physicalPictureObserved':False,'rootCauseFixEstablished':False}
    from verify_logger_reconciliation import verify
    verify(f);return f
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.write_text(json.dumps(build(a.source),indent=2,sort_keys=True)+'\n')
