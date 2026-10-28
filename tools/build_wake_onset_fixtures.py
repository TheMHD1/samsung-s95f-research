#!/usr/bin/env python3
"""Project explicit private GC/GF scientific fields; originals are not in a public clone.
Run only with a separately held evidence root. Offline public verification needs
only the two generated fixtures, never an authenticated transport or OEM binary.
"""
import argparse,base64,hashlib,json,re,struct
from pathlib import Path

def data(b):return {'bytes':len(b),'base64':base64.b64encode(b).decode(),'sha256':hashlib.sha256(b).hexdigest()}
def build(source,name):
    leaf={'GC':'wake-window-trial-20261028gc','GF':'live-saver-wake-trial-20261028gf'}[name]
    p=source/'panel-idle-20261026/overnight'/leaf
    j=json.loads((p/'capture-01/native.receipt.json').read_bytes());result=json.loads((p/'capture-01/result.json').read_bytes())
    if not j['accepted'] or not result['protocolAccepted'] or result['cleanup']!='STAGE_ABSENT':raise ValueError('private original acceptance')
    def raw(w):
        b=base64.b64decode(w['raw'],validate=True)
        if len(b)!=w['count']:raise ValueError('private raw extent')
        return b
    rows=base64.b64decode(j['rows']['rawBase64'],validate=True)
    if len(rows)!=58*j['rows']['count']or hashlib.sha256(rows).hexdigest()!=j['rows']['sha256']:raise ValueError('private packed source')
    def selected(c):
        windows=[]
        for i,w in enumerate(c['windows']):
            if w['name']not in {'R','M','C','N','H'}:continue
            t=c['transfers'][2*i:2*i+2]
            windows.append(dict(data(raw(w)),name=w['name'],beforeUs=t[0][4],afterUs=t[1][5]))
        return {'role':c['role'],'cycle':c['cycle'],'windows':windows}
    rings=[]
    for fn,meta in [('baseline-ring.bin',j['baselineRing']),('post-ring.bin',j['postRing'])]:
        b=(p/'capture-01'/fn).read_bytes()
        if len(b)!=15372 or hashlib.sha256(b).hexdigest()!=meta['sha256']:raise ValueError('private ring hash')
        rings.append(b)
    before,post=rings;b0,b1=struct.unpack_from('<I',before)[0],struct.unpack_from('<I',post)[0]
    if not 0<=b0<=b1<=15360:raise ValueError('this bounded no-wrap endpoint candidate')
    candidate=post[12+b0:12+b1]
    if before[12:12+b0]!=post[12:12+b0]or before[12+b1:]!=post[12+b1:]:raise ValueError('outside candidate changed')
    header=re.findall(rb'\[RTP:NORMAL\]\[(\d+)\]',candidate)
    if len(header)!=1:raise ValueError('typed header')
    pattern=rb'\[RTP\s+(\d+)\]RGB:(\d+) x:\s*(\d+) y:\s*(\d+)/c:\s*(\d+)/diff:\s*(\d+)/m:(NORMAL)\n'
    detailrows=[]
    for match in re.finditer(pattern,candidate):
        ordinal,rgb,x,y,b,diff=map(int,match.groups()[:6])
        detailrows.append({'ordinal':ordinal,'rgb':rgb,'x':x,'y':y,'b':b,'diff':diff,'mode':'NORMAL','conditional12bitACandidates':sorted(set(v for v in [b+diff,b-diff]if 0<=v<=4095))})
    decoded=json.loads((p/'live-analysis/decoded.json').read_bytes());ring=decoded['ring']
    if detailrows!=ring['candidateRows'if name=='GC'else'detailRows']:raise ValueError('raw detail projection vs independent frozen analysis')
    projection=b''.join(rows[i:i+46]+rows[i+54:i+58]for i in range(0,len(rows),58))
    native={k:j[k]for k in ['accepted','phase','released','closed','terminal','headers','bulks','inputs','writes','retries','threshold','cyclesStarted','cleanCycles','quiescentCycles','startUs','endUs']}
    native.update(projection=dict(data(projection),recordBytes=50,count=j['rows']['count']),retained=[selected(c)for c in j['retained']],controls={c['role']:data(raw(c['windows'][0]))for c in j['controls']if c['role']in {'prearm-R','armed-R','prerestore-R','restored-R'}},intervention=j['intervention'])
    event=b'rtp_act_736\n';events=candidate.count(event)
    if events and not candidate.endswith(event*events):raise ValueError('paired exact suffix')
    ringprojection={'baselineCursors':list(struct.unpack_from('<III',before)),'postCursors':list(struct.unpack_from('<III',post)),'candidateBytes':len(candidate),'normalInvocationCounter':int(header[0]),'details':detailrows,'baselineEvent736Lines':before[12:].count(event),'postEvent736Lines':post[12:].count(event),'candidateEvent736Lines':events,'eventSuffix':data(candidate[-len(event)*events:]if events else b''),'outsideCandidateDataUnchanged':True,'chronologicalDeltaProven':False,'lapCountProven':False,'sharedEpochProven':False,'twoLinesMeanTwoInvocations':False}
    f={'schema':'public-wake-onset-projection-v1','case':name,'notice':'Bounded scientific projection. Dynamic P4/P8 pointer words, device identity, raw rings/OEM instructions and authenticated receipts are withheld. Public verification checks this projection; it does not replay omitted original transport. All fields are sequential observations, not atomic controller snapshots.','source':{'workstream':leaf,'originalRowBytes':58,'projection':'row[0:46]+row[54:58] removes both dynamic pointers'},'native':native,'workflow':{'wrapperUiOperations':result['wrapperUiOperations'],'nativeInvocations':result['nativeInvocations'],'keyExposureQualified':result['keyExposureQualified'],'cleanup':result['cleanup']},'ring':ringprojection,'physicalPictureObserved':False,'actualFpProven':False,'executingPcProven':False,'selectedAProven':False,'keyConsumptionProven':False,'forYouTransitionProven':False,'rootCauseFixEstablished':False,'thresholdPreventionEstablished':False,'originalTransportProvenanceReplayed':False}
    from verify_wake_onset import verify
    verify(f);return f
if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--source',type=Path,required=True);a.add_argument('--output-directory',type=Path,required=True);x=a.parse_args()
    for case in ['GC','GF']:(x.output_directory/('wake-'+case.lower()+'.json')).write_text(json.dumps(build(x.source,case),indent=2,sort_keys=True)+'\n')
