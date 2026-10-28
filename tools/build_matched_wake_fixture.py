#!/usr/bin/env python3
"""Build a bounded GJ scientific projection from separately held private inputs."""
import argparse,base64,hashlib,json,re,struct
from pathlib import Path

def data(b):return {'bytes':len(b),'base64':base64.b64encode(b).decode(),'sha256':hashlib.sha256(b).hexdigest()}
def build(source):
 p=source/'panel-idle-20261026/overnight/matched-saver-limit-trial-20261028gj'
 def load(n):return json.loads((p/n).read_bytes())
 def raw(w,key='raw'):
  b=base64.b64decode(w[key],validate=True)
  if len(b)!=w.get('count',w.get('bytes')):raise ValueError('source extent')
  if 'sha256'in w and hashlib.sha256(b).hexdigest()!=w['sha256']:raise ValueError('source hash')
  return b
 def project(folder):
  j=load(folder+'/native.receipt.json');r=load(folder+'/result.json')
  if j['accepted']is not True or r['cleanup']!='STAGE_ABSENT':raise ValueError('private accepted result')
  packed=raw({'raw':j['rows']['rawBase64'],'bytes':58*j['rows']['count'],'sha256':j['rows']['sha256']})
  def capture(c):
   out=[]
   for i,w in enumerate(c['windows']):
    if w['name']in {'R','M','C','N','H'}:out.append(dict(data(raw(w)),name=w['name'],beforeUs=c['transfers'][2*i][4],afterUs=c['transfers'][2*i+1][5]))
   return {'role':c['role'],'cycle':c['cycle'],'windows':out}
  native={k:j[k]for k in ['accepted','phase','released','closed','terminal','headers','bulks','inputs','writes','retries','threshold','cyclesStarted','cleanCycles','quiescentCycles','startUs','endUs']}
  projected=b''.join(packed[i:i+46]+packed[i+54:i+58]for i in range(0,len(packed),58));native.update(projection=dict(data(projected),recordBytes=50,count=j['rows']['count']),retained=[capture(c)for c in j['retained']],controls={c['role']:data(raw(c['windows'][0]))for c in j['controls']if c['role']in {'prearm-R','armed-R','prerestore-R','restored-R'}},intervention=j['intervention'])
  rings=[]
  for name,key in [('baseline-ring.bin','baselineRing'),('post-ring.bin','postRing')]:
   b=(p/folder/name).read_bytes()
   if len(b)!=15372 or hashlib.sha256(b).hexdigest()!=j[key]['sha256']:raise ValueError('ring sidecar')
   rings.append(b)
  before,post=rings;lo=struct.unpack_from('<I',before)[0];hi=struct.unpack_from('<I',post)[0]
  if not 0<=lo<=hi<=15360:raise ValueError('this bounded endpoint candidate')
  if before[12:12+lo]!=post[12:12+lo]or before[12+hi:]!=post[12+hi:]:raise ValueError('outside backing changed')
  candidate=post[12+lo:12+hi];header=re.findall(rb'\[RTP:NORMAL\]\[(\d+)\]',candidate)
  if len(header)!=1:raise ValueError('single typed header')
  details=[]
  for m in re.finditer(rb'\[RTP\s+(\d+)\]RGB:(\d+) x:\s*(\d+) y:\s*(\d+)/c:\s*(\d+)/diff:\s*(\d+)/m:(NORMAL)\n',candidate):
   ordinal,rgb,x,y,b,diff=map(int,m.groups()[:6]);details.append({'ordinal':ordinal,'rgb':rgb,'x':x,'y':y,'b':b,'diff':diff,'mode':'NORMAL','conditional12bitACandidates':sorted(set(v for v in [b+diff,b-diff]if 0<=v<=4095))})
  event=b'rtp_act_736\n';events=candidate.count(event)
  if events and not candidate.endswith(event*events):raise ValueError('suffix placement')
  return {'native':native,'workflow':{'wrapperUiOperations':r['wrapperUiOperations'],'nativeInvocations':r['nativeInvocations'],'keyExposureQualified':r['keyExposureQualified'],'cleanup':r['cleanup']},'ring':{'baselineCursors':list(struct.unpack_from('<III',before)),'postCursors':list(struct.unpack_from('<III',post)),'candidateBytes':len(candidate),'normalInvocationCounter':int(header[0]),'details':details,'baselineEvent736Lines':before[12:].count(event),'postEvent736Lines':post[12:].count(event),'candidateEvent736Lines':events,'eventSuffix':data(candidate[-12*events:]if events else b''),'outsideCandidateDataUnchanged':True,'chronologicalDeltaProven':False,'lapCountProven':False,'sharedEpochProven':False,'twoLinesMeanTwoInvocations':False}}
 def transaction(folder):
  j=load(folder+'/native.receipt.json');r=load(folder+'/result.json');w={x['name']:x for x in j['windows']}
  return {'accepted':j['accepted'],'phase':j['protocolPhase'],'released':j['released'],'closed':j['closed'],'headers':j['headersSent'],'bulks':j['bulkTransfers'],'readbackVerified':j['readbackVerified'],'limitMayHaveChanged':j['limitMayHaveChanged'],'cleanup':r['cleanup'],'windows':{k:data(raw(w[k],'base64'))for k in ['baseline-R','fresh-R','readback-R']}}
 final=load('validation-capture/native.receipt.json');fr=load('validation-capture/result.json');selected={'start-R','end-R','M','C','start-N','end-N','X','Y','RGB','B','Diff'}
 finalProjection={'accepted':final['accepted'],'phase':final['protocolPhase'],'released':final['released'],'closed':final['closed'],'headers':final['headersSent'],'bulks':final['bulkTransfers'],'writes':final['writes'],'uiOperations':final['uiOperations'],'cleanup':fr['cleanup'],'windows':{w['name']:data(raw(w,'base64'))for w in final['windows']if w['name']in selected}}
 f={'schema':'public-matched-wake-contrast-v1','notice':'Bounded scientific projection. Dynamic P4/P8 words, identity, full rings/OEM instructions and authenticated receipts are withheld. Public verification checks the projection, not omitted original transport. Different reference/UI history and c4 publication coupling prevent pure-threshold causality.','source':{'workstream':'matched-saver-limit-trial-20261028gj','rowProjection':'58-byte row[0:46]+row[54:58] removes dynamic P4/P8','sameUsbInstanceForContrast':'private-evidence premise; identifying fields omitted'},'set200':transaction('set-01'),'raised200':project('raised-capture-01'),'restore40':transaction('restore-01'),'control40':project('forty-capture-01'),'finalValidation':finalProjection,'sequence':{'fixedSet':1,'fixedRestore':1,'stockMode2At40':2,'stockMode2At200':0,'ghFault200RecoveryUsed':False,'finalCachedUi':'Apps+saver+CSFS'},'physicalPictureObserved':False,'actualFpProven':False,'executingPcProven':False,'matchedAllHistoryProven':False,'thresholdPreventionEstablished':False,'rootCauseFixEstablished':False,'originalTransportProvenanceReplayed':False}
 from verify_matched_wake_contrast import verify
 verify(f);return f
if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--source',type=Path,required=True);a.add_argument('--output',type=Path,required=True);x=a.parse_args();x.output.write_text(json.dumps(build(x.source),indent=2,sort_keys=True)+'\n')
