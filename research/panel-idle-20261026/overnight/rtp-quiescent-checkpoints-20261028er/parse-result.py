#!/usr/bin/env python3
"""Strict offline EM dense refresh checkpoint decoder; no root/network/TV operations."""
from pathlib import Path
import base64,copy,hashlib,json,struct,types,sys
HERE=Path(__file__).resolve().parent
PARENT_SHA='bd64e26963a622c82a3d03f776829e89bd82e66d31251e58808a3f4ef851a73a'
SCHEMA='managed-usb-rt-synchronized-key-er-v1'
SIZE=58;MAX=56;LIMIT=24576
FULL=['R','M','C','P','N','H','L','R']
def need(ok,s):
 if not ok:raise ValueError(s)
def sha(b):return hashlib.sha256(b).hexdigest()
def load_parent():
 p=HERE/'parent-synchronized-parser.py';b=p.read_bytes();need(sha(b)==PARENT_SHA,'pinned DF synchronized parser');m=types.ModuleType('frozen_df_parser');m.__file__=str(p);exec(compile(b,str(p),'exec'),m.__dict__);return m
def rt(b):
 t=tuple(struct.unpack_from('<H',b,o)[0]for o in (0,10,14))
 return 0 if t==(0,0,1) else 1 if t==(1,0x1001,0) else 3 if t==(0,0,0)and int.from_bytes(b[0xc4:0xc6],"little")==40 else 2
def parse_native(text):
 need(type(text)is str and len(text.encode('utf8'))<=LIMIT,'exclusive receipt bound');p=load_parent();n=p.strict_json(text)
 need(type(n)is dict and n.get('schema')==SCHEMA and 'scoreCheckpoints'in n,'EM schema/checkpoints');need(type(n.get('device'))is int and 1<=n['device']<=127 and n.get('bindingQualified')is True and 'bindingChecks'not in n,'qualified native binding/device without large success audit')
 c=n['scoreCheckpoints'];need(type(c)is dict and set(c)=={'schema','recordBytes','count','rawBase64','sha256'},'checkpoint fields')
 need(c['schema']=='er-quiescent-checkpoints-v1' and type(c['recordBytes'])is int and c['recordBytes']==SIZE,'packed schema/size')
 need(type(c['count'])is int and 0<=c['count']<=MAX,'checkpoint count');need(type(c['rawBase64'])is str and type(c['sha256'])is str,'packed encoding')
 raw=base64.b64decode(c['rawBase64'],validate=True);need(len(raw)==SIZE*c['count'] and base64.b64encode(raw).decode()==c['rawBase64'] and sha(raw)==c['sha256'],'packed extent/hash/canonical encoding')
 projected=copy.deepcopy(n);projected.pop('scoreCheckpoints');projected.pop('device');projected.pop('bindingQualified');projected['schema']=p.SCHEMA
 _,summaries,files,gc,q=p.parse_native(json.dumps(projected,separators=(',',':')));need(gc==[],'exclusive receipt has no diagnostic rows')
 start=p.integer(n['startUs'],'startUs');end=p.integer(n['endUs'],'endUs',start);span=end-start
 complete=[x for x in n['retained'] if [w['name']for w in x['windows']]==FULL and len(x['transfers'])==16]
 full_transition=any(x['role']=='transition'for x in complete)
 need(c['count']==n['cleanCyclesCompleted']+n['quiescentCyclesCompleted']+int(full_transition) and c['count']<=n['cyclesStarted'],'one checkpoint per full completed cycle, no baseline duplication')
 rows=[];last=0
 for i in range(c['count']):
  b=raw[i*SIZE:(i+1)*SIZE];startstate=b[0]>>4;endstate=b[0]&15;selector=b[1]
  need(startstate in(0,3)and(endstate==1 if full_transition and i==c['count']-1 else endstate in(0,3)),'exact clean/quiescent/transition checkpoint classification')
  need(i!=0 or(startstate==endstate==0),'first complete baseline must be clean')
  beforefp,afterfp=struct.unpack_from('<HH',b,2);a0=struct.unpack_from('<I',b,6)[0];q0=struct.unpack_from('<H',b,10)[0];history=list(struct.unpack_from('<4H',b,12));ordinal=struct.unpack_from('<I',b,20)[0];publication_bound=struct.unpack_from('<H',b,32)[0]
  taps=struct.unpack_from('<6H2I',b,34)
  hb,ha=struct.unpack_from('<2I',b,24);need(last<=hb<=ha<=span,'checkpoint H time/order/bounds');last=ha
  rows.append({'cycleIndex':i+1,'startRtClassification':'Clean'if startstate==0 else'Quiescent','endRtClassification':'Faulted'if endstate==1 else'Quiescent'if endstate==3 else'Clean','selectorC7':selector,'startAlternateThreshold':beforefp,'endAlternateThreshold':afterfp,'a0U32':a0,'a0Low16':a0&65535,'q0U16':q0,'history0U16x4':history,'recordOrdinal0U32':ordinal,'publicationBoundMirror':publication_bound,'publicationBoundMirrorIsActualFpProven':False,'hReadBracket':{'headerBeforeUs':start+hb,'dataAfterUs':start+ha},'mCpu4a2U16':taps[0],'mCpu4a4U16':taps[1],'mCpu4c2U16':taps[2],'mCpu4c4U16':taps[3],'endRRoot2460U16':taps[4],'endRRoot246eU16':taps[5],'capturedDynamicAPointerU32':taps[6],'capturedDynamicBPointerU32':taps[7],'startEndRtExactTimesRetained':False,'a0Low16Above40':(a0&65535)>40,'cleanRBrackets':startstate==endstate==0,'quiescentRBracketObserved':3 in(startstate,endstate),'endRRoot24caU16':struct.unpack_from('<H',b,54)[0],'endRRoot2468U16':struct.unpack_from('<H',b,56)[0]})
 need(sum(x['cleanRBrackets']for x in rows)==n['cleanCyclesCompleted'],'exact compact clean counter')
 need(sum(x['quiescentRBracketObserved']and x['endRtClassification']!='Faulted'for x in rows)==n['quiescentCyclesCompleted'],'exact compact quiescent counter')
 for x in rows:
  need((x['startRtClassification']!='Quiescent'or x['startAlternateThreshold']==40)and(x['endRtClassification']!='Quiescent'or x['endAlternateThreshold']==40),'Quiescent recognized only at40')
 # Recompute every compact byte against each retained full raw cycle, including
 # duplicate trigger-baseline/last-clean references without counting them again.
 for cap in complete:
  ci=cap['cycleIndex'];need(type(ci)is int and 1<=ci<=c['count'],'retained full cycle checkpoint index');w=[base64.b64decode(x['rawBase64'],validate=True)for x in cap['windows']];t=cap['transfers'];b=bytearray(SIZE)
  b[0]=(rt(w[0])<<4)|rt(w[7]);b[1]=w[2][7];b[2:4]=w[0][0xc4:0xc6];b[4:6]=w[7][0xc4:0xc6];b[6:10]=w[5][4:8];b[10:12]=w[5][28:30];b[12:20]=w[5][40:48];b[20:24]=w[4][0:4];b[32:34]=w[1][42:44]
  struct.pack_into('<2I',b,24,t[10]['beforeUs']-start,t[11]['afterUs']-start)
  for dest,src,off,length in ((34,1,2,2),(36,1,4,2),(38,1,0x22,2),(40,1,0x24,2),(42,7,0x60,2),(44,7,0x6e,2),(46,3,4,4),(50,3,8,4),(54,7,0xca,2),(56,7,0x68,2)):b[dest:dest+length]=w[src][off:off+length]
  need(bytes(b)==raw[(ci-1)*SIZE:ci*SIZE],'retained source bytes and exact H bracket match compact checkpoint')
 q['scoreCheckpoints']={'schema':'er-quiescent-checkpoint-interpretation-v1','count':c['count'],'recordBytes':SIZE,'maximumCheckpoints':MAX,'quiescentCyclesCompleted':n['quiescentCyclesCompleted'],'quiescentMeansCpuIdle':False,'observationDurationUs':2000000,'nominalPeriodUs':25000,'appendedLayout':'34:M4a2u16,36:M4a4u16,38:M4c2u16,40:M4c4u16,42:endR2460u16,44:endR246eu16,46:P494u32,50:P498u32;54:endR24caU16,56:endR2468U16; little-endian','rows':rows,'cleanBracketA0Low16Above40Cycles':[x['cycleIndex']for x in rows if x['cleanRBrackets']and x['a0Low16Above40']],'physicalPictureObserved':False,'everyComparatorCallObserved':False,'missingAbove40WitnessExcludesCrossing':False,'mode1AndThresholdSelectionStillSourceConditional':True,'limitations':['2s cooperative observation, at most56 checkpoints;25ms requested start-to-start period, no guaranteed sampling rate; higher polling load than EH, not a callback trace','M/P/endR taps are earlier/later sequential reads; no common sampling instant or per-tap brackets retained','captured dynamic pointer words establish no header, alias, epoch, active buffer or actual comparator branch','25ms requested polling can still miss the entire selector/counter event sequence; seed1 permits any two qualifying boundary events without distinct-buffer proof','H state lies inside full read-pair bracket; no exact device sampling timestamp','M publication-bound mirror and Nordinal0 were read earlier sequentially in same cycle; no compact M/N pair timestamp, source count or R pair times retained','H may change/reset between reads; matching clean R brackets do not prove atomicity or no transient fault','partial transition retains original H/N raw context without inventing a full checkpoint','A0 low16 above40 is a sampled counterfactual witness, not complete predicate inputs or emitted light']}
 q['workflowQualified']=q['trialQualified']
 q['quiescentObserved']=any(x['quiescentRBracketObserved']for x in rows)or any(w.get('observedRtState',{}).get('classification')=='Quiescent'for c0 in n['retained']for w in c0['windows'])
 q['rtObservationOutcome']='Faulted'if n['onsetObserved']else'QuiescentObserved'if q['quiescentObserved']else'CleanOnly'
 q['allRecordedCompleteCyclesClean']=n['quiescentCyclesCompleted']==0 and not n['onsetObserved']
 q['quiescentIsFaultOrPreventionProof']=False
 files.append(('score-checkpoints.bin',raw,sha(raw)))
 return n,summaries,files,[],q
if __name__=='__main__':
 n,c,r,g,q=parse_native(Path(sys.argv[1]).read_text());print(json.dumps(q,sort_keys=True))
