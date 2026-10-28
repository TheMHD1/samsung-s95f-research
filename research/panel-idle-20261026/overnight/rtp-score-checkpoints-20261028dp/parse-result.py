#!/usr/bin/env python3
"""Strict offline DP checkpoint decoder; no root/network/TV operations."""
from pathlib import Path
import base64,copy,hashlib,json,struct,types,sys
HERE=Path(__file__).resolve().parent
PARENT_SHA='38264b8463db7f8add0e1f39c84726baed19ea17f46e3b3037307592ede30ddc'
SCHEMA='managed-usb-rt-synchronized-key-dp-v1'
SIZE=34;MAX=80;LIMIT=24576
FULL=['R','M','C','P','N','H','L','R']
def need(ok,s):
 if not ok:raise ValueError(s)
def sha(b):return hashlib.sha256(b).hexdigest()
def load_parent():
 p=HERE/'parent-synchronized-parser.py';b=p.read_bytes();need(sha(b)==PARENT_SHA,'pinned DF synchronized parser');m=types.ModuleType('frozen_df_parser');m.__file__=str(p);exec(compile(b,str(p),'exec'),m.__dict__);return m
def rt(b):
 t=tuple(struct.unpack_from('<H',b,o)[0]for o in (0,10,14))
 return 0 if t==(0,0,1) else 1 if t==(1,0x1001,0) else 2
def parse_native(text):
 need(type(text)is str and len(text.encode('utf8'))<=LIMIT,'exclusive receipt bound');p=load_parent();n=p.strict_json(text)
 need(type(n)is dict and n.get('schema')==SCHEMA and 'scoreCheckpoints'in n,'DP schema/checkpoints');need(type(n.get('device'))is int and 1<=n['device']<=127 and n.get('bindingQualified')is True and 'bindingChecks'not in n,'qualified native binding/device without large success audit')
 c=n['scoreCheckpoints'];need(type(c)is dict and set(c)=={'schema','recordBytes','count','rawBase64','sha256'},'checkpoint fields')
 need(c['schema']=='dp-score-checkpoints-v1' and type(c['recordBytes'])is int and c['recordBytes']==SIZE,'packed schema/size')
 need(type(c['count'])is int and 0<=c['count']<=MAX,'checkpoint count');need(type(c['rawBase64'])is str and type(c['sha256'])is str,'packed encoding')
 raw=base64.b64decode(c['rawBase64'],validate=True);need(len(raw)==SIZE*c['count'] and base64.b64encode(raw).decode()==c['rawBase64'] and sha(raw)==c['sha256'],'packed extent/hash/canonical encoding')
 projected=copy.deepcopy(n);projected.pop('scoreCheckpoints');projected.pop('device');projected.pop('bindingQualified');projected['schema']=p.SCHEMA
 _,summaries,files,gc,q=p.parse_native(json.dumps(projected,separators=(',',':')));need(gc==[],'exclusive receipt has no diagnostic rows')
 start=p.integer(n['startUs'],'startUs');end=p.integer(n['endUs'],'endUs',start);span=end-start
 complete=[x for x in n['retained'] if [w['name']for w in x['windows']]==FULL and len(x['transfers'])==16]
 full_transition=any(x['role']=='transition'for x in complete)
 need(c['count']==n['cleanCyclesCompleted']+int(full_transition) and c['count']<=n['cyclesStarted'],'one checkpoint per full completed cycle, no baseline duplication')
 rows=[];last=0
 for i in range(c['count']):
  b=raw[i*SIZE:(i+1)*SIZE];startstate=b[0]>>4;endstate=b[0]&15;selector=b[1]
  need(startstate==0 and endstate==(1 if full_transition and i==c['count']-1 else 0),'exact clean/transition checkpoint classification')
  beforefp,afterfp=struct.unpack_from('<HH',b,2);a0=struct.unpack_from('<I',b,6)[0];q0=struct.unpack_from('<H',b,10)[0];history=list(struct.unpack_from('<4H',b,12));ordinal=struct.unpack_from('<I',b,20)[0];publication_bound=struct.unpack_from('<H',b,32)[0]
  hb,ha=struct.unpack_from('<2I',b,24);need(last<=hb<=ha<=span,'checkpoint H time/order/bounds');last=ha
  rows.append({'cycleIndex':i+1,'startRtClassification':'Clean','endRtClassification':'Faulted'if endstate==1 else'Clean','selectorC7':selector,'startAlternateThreshold':beforefp,'endAlternateThreshold':afterfp,'a0U32':a0,'a0Low16':a0&65535,'q0U16':q0,'history0U16x4':history,'recordOrdinal0U32':ordinal,'publicationBoundMirror':publication_bound,'publicationBoundMirrorIsActualFpProven':False,'hReadBracket':{'headerBeforeUs':start+hb,'dataAfterUs':start+ha},'startEndRtExactTimesRetained':False,'a0Low16Above40':(a0&65535)>40,'cleanRBrackets':endstate==0})
 # Recompute every compact byte against each retained full raw cycle, including
 # duplicate trigger-baseline/last-clean references without counting them again.
 for cap in complete:
  ci=cap['cycleIndex'];need(type(ci)is int and 1<=ci<=c['count'],'retained full cycle checkpoint index');w=[base64.b64decode(x['rawBase64'],validate=True)for x in cap['windows']];t=cap['transfers'];b=bytearray(SIZE)
  b[0]=(rt(w[0])<<4)|rt(w[7]);b[1]=w[2][7];b[2:4]=w[0][0xc4:0xc6];b[4:6]=w[7][0xc4:0xc6];b[6:10]=w[5][4:8];b[10:12]=w[5][28:30];b[12:20]=w[5][40:48];b[20:24]=w[4][0:4];b[32:34]=w[1][42:44]
  struct.pack_into('<2I',b,24,t[10]['beforeUs']-start,t[11]['afterUs']-start)
  need(bytes(b)==raw[(ci-1)*SIZE:ci*SIZE],'retained source bytes and exact H bracket match compact checkpoint')
 q['scoreCheckpoints']={'schema':'dp-score-checkpoint-interpretation-v1','count':c['count'],'recordBytes':SIZE,'rows':rows,'cleanBracketA0Low16Above40Cycles':[x['cycleIndex']for x in rows if x['cleanRBrackets']and x['a0Low16Above40']],'physicalPictureObserved':False,'everyComparatorCallObserved':False,'missingAbove40WitnessExcludesCrossing':False,'mode1AndThresholdSelectionStillSourceConditional':True,'limitations':['250ms nominal sequential polling, not a callback trace','H state lies inside full read-pair bracket; no exact device sampling timestamp','M publication-bound mirror and Nordinal0 were read earlier sequentially in same cycle; no compact M/N pair timestamp, source count or R pair times retained','H may change/reset between reads; matching clean R brackets do not prove atomicity or no transient fault','partial transition retains original H/N raw context without inventing a full checkpoint','A0 low16 above40 is a sampled counterfactual witness, not complete predicate inputs or emitted light']}
 files.append(('score-checkpoints.bin',raw,sha(raw)))
 return n,summaries,files,[],q
if __name__=='__main__':
 n,c,r,g,q=parse_native(Path(sys.argv[1]).read_text());print(json.dumps(q,sort_keys=True))
