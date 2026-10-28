#!/usr/bin/env python3
"""Pure offline source/options audit. Imports parsers only, never runners."""
from pathlib import Path
import base64,hashlib,importlib.util,json,struct
HERE=Path(__file__).resolve().parent;B=HERE.parent
checks=0

def need(v,why):
 global checks
 checks+=1
 if not v:raise ValueError(why)
def sha(b):return hashlib.sha256(b).hexdigest()
def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def main():
 pins=json.loads((HERE/'input-pins.json').read_bytes())
 for row in pins['files']:
  data=(B/row['path']).read_bytes();need(len(data)==row['bytes']and sha(data)==row['sha256'],'input '+row['path'])
 dv=load(B/'volatile-limit-dynamic-profile-20261028dv/parse-result.py','dv_eu_parser')
 er=load(B/'rtp-quiescent-checkpoints-20261028er/parse-result.py','er_eu_parser')
 runs=[]
 for name,old,new in [('dv-set-01',40,200),('dv-restore-01',200,40)]:
  d=B/'volatile-limit-trial-20261028dk'/name
  n,files,gc=dv.parse_native((d/'native.receipt.json').read_text())
  need(n['accepted']and n['device']==60 and n['headersSent']==7 and n['bulkTransfers']==14,'actual accepted writer')
  for filename,data,digest in files:need((d/filename).read_bytes()==data and sha(data)==digest,'writer exact raw '+filename)
  result=json.loads((d/'result.json').read_bytes());record=json.loads((d/'record.json').read_bytes())
  need(result['accepted']and result['cleanup']=='STAGE_ABSENT'and result['nativeInvocations']==1 and result['retries']==0,'writer wrapper acceptance')
  need(record['cleanup_required']is False and record['native_invocations']==1,'writer completion record')
  r0=(d/'baseline-R.bin').read_bytes();r1=(d/'readback-R.bin').read_bytes();mm=(d/'pre-M.bin').read_bytes();c=(d/'pre-C.bin').read_bytes()
  need(dv.half(r0,0xc4)==old and dv.half(r1,0xc4)==new,'actual old/new')
  runs.append(dict(name=name,accepted=True,oldLimit=old,newLimit=new,device=60,headers=7,bulks=14,cleanup='STAGE_ABSENT',temperature=dv.half(r0,0x98),ordinaryUpper=dv.half(r0,0x20),alternateUpper=dv.half(r0,0xbc),selectorC7=c[7],aa=dv.half(mm,10),ac=dv.half(mm,12)))
 d=B/'quiescent-onset-trial-20261028es/trial-01/recovery-validation';r=(d/'start-R.bin').read_bytes();mm=(d/'M.bin').read_bytes();c=(d/'C.bin').read_bytes();n=json.loads((d/'native.receipt.json').read_bytes());result=json.loads((d/'result.json').read_bytes())
 need(n['accepted']and n['device']==63 and n['protocolPhase']=='ReadyForHeader'and n['released']and n['closed'],'USB63 completed predecessor')
 need(result['cleanup']=='STAGE_ABSENT'and(d/'end-R.bin').read_bytes()==r,'USB63cleanstablecleanup')
 reasons={}
 for name,fn in [('R',lambda:dv.guard_r(r,40)),('context',lambda:dv.validate_candidate_context(mm,c,r))]:
  try:fn()
  except ValueError as e:reasons[name]=str(e)
 need(reasons=={'R':'source-model endpoint normal','context':'root/mode/scan'},'last USB63 not DVadmission')
 need(dv.half(mm,10)==0 and dv.half(mm,12)==1 and dv.half(r,0x20)==3200 and dv.half(r,0xbc)==3138 and dv.half(r,0x98)==23,'mode6endpointcounterexample')
 ex=B/'limit-rechallenge-trial-20261028ex/preparation-01/baseline';xr=(ex/'start-R.bin').read_bytes();xm=(ex/'M.bin').read_bytes();xc=(ex/'C.bin').read_bytes()
 xn=json.loads((ex/'native.receipt.json').read_bytes());xresult=json.loads((ex/'result.json').read_bytes())
 need(xn['accepted']and xn['device']==63 and xn['protocolPhase']=='ReadyForHeader'and xn['released']and xn['closed']and xresult['cleanup']=='STAGE_ABSENT','EX accepted predecessor')
 dv.validate_candidate_context(xm,xc,xr);need(dv.half(xm,12)==2 and xm[56]==1,'EX full context PASS')
 xreason=None
 try:dv.guard_r(xr,40)
 except ValueError as e:xreason=str(e)
 need(xreason=='source-model endpoint alternate','EX restrictive alternate mismatch')
 need([dv.half(xr,o)for o in [0x20,0x98,0xbc,0xac,0xc4]]==[3161,24,3138,3,40],'EX exact endpoint tuple')
 es=B/'quiescent-onset-trial-20261028es/trial-01/onset/native.receipt.json';en,_,files,_,q=er.parse_native(es.read_text());rows=q['scoreCheckpoints']['rows']
 need(en['accepted']and en['onsetObserved']and len(rows)==28 and en['quiescentCyclesCompleted']==2,'actual ERfault retained')
 maximum=max(x['a0Low16']for x in rows);need(maximum==40,'compactmaximum40')
 post=next(x for x in en['retained']if x['role']=='post-fault');hw=next(x for x in post['windows']if x['name']=='H');h=base64.b64decode(hw['rawBase64'],validate=True);postscore=struct.unpack_from('<I',h,4)[0]
 need(postscore==48 and all(x['startAlternateThreshold']==x['endAlternateThreshold']==40 for x in rows),'postH48/unchanged40')
 # Minimal native/parser derivative contracts; no source is edited here.
 source=(B/'volatile-limit-dynamic-profile-20261028dv/Program.cs').read_text()
 for token in ['02010000c424014702000000','int old=restore?200:40,value=restore?40:200','Half(m,10)==0&&Half(m,12)==2','c[7]<=1','Half(r,0x30)==200&&Half(r,0xc0)==200','GuardPair(baseline,fresh)','GuardPair(fresh,after)']:
  need(token in source,'fixed DV source '+token)
 ercs=(B/'rtp-quiescent-checkpoints-20261028er/Program.cs').read_text();need('gate == 0 && Half(value, 0xc4) == 40' in ercs,'ER40 Q guard')
 for name in ['parse-result.py','transport-parser.py']:
  text=(B/'rtp-quiescent-checkpoints-20261028er'/name).read_text();need('==40' in text.replace(' ',''),'ER lower/outer40 Q guard')
 def state(stop,fault,gate,limit,expected=200):
  if limit!=expected:return 'UnexpectedLimit'
  return 'Clean'if(stop,fault,gate)==(0,0,1)else'Faulted'if(stop,fault,gate)==(1,0x1001,0)else'Quiescent'if(stop,fault,gate)==(0,0,0)else'Unexpected'
 for lim in [0,40,200,201,65535]:
  for triplet,want in [((0,0,1),'Clean'),((0,0,0),'Quiescent'),((1,0x1001,0),'Faulted'),((0,0x1001,0),'Unexpected')]:
   need(state(*triplet,lim)==(want if lim==200 else'UnexpectedLimit'),'fixed200classificationmodel')
 return dict(schema='eu-limit-rechallenge-options-audit-v1',checks=checks,inputFiles=len(pins['files']),actualWriterRuns=runs,freshEXBaseline=dict(contextPass=True,scan=1,aa=0,ac=2,temperature=24,ordinaryUpper=3161,alternateUpper=3138,sourceModelBothExpected=3161,passesFrozenDVRGuard=False,refusalReason=xreason,callbacksNotCapturedByEB=True),lastUSB63Snapshot=dict(clean=True,limit=40,aa=0,ac=1,temperature=23,ordinaryUpper=3200,alternateUpper=3138,passesDVAdmission=False,refusalReasons=reasons,phase='ReadyForHeader',released=True,closed=True,subsequentFreshHeaderBaselineNotAssumed=True),ES=dict(completeRows=28,quiescentRows=2,compactHMaximum=maximum,postfaultH=postscore,sampledCleanAbove40Witness=False,actualFpProven=False,actualUiDestinationProven=False),newFixed200ReaderImplemented=False,targetOperations=0,rootCalls=0,networkOperations=0)
if __name__=='__main__':print(json.dumps(main(),sort_keys=True,indent=2))
