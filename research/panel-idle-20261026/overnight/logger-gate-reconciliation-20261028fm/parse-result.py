#!/usr/bin/env python3
"""Strict FM success parser. Native refusals remain refusals; no transport calls."""
import base64,hashlib,json,sys
def need(v,m):
 if not v:raise ValueError(m)
def integer(v):return type(v)is int
def pairs(items):
 d={}
 for k,v in items:need(k not in d,'duplicate field');d[k]=v
 return d
def strict(s):return json.loads(s,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
def half(b,n):return int.from_bytes(b[n:n+2],'little')
def rt(b):
 need(half(b,0xc4)==40,'threshold40');t=half(b,0),half(b,10),half(b,14)
 need(t in [(0,0,1),(0,0,0),(1,4097,0)],'known RT');return { (0,0,1):'Clean',(0,0,0):'Quiescent',(1,4097,0):'Faulted'}[t]
def logger(b,g):
 need(len(b)==256 and half(b,6)==g,'full logger gate');rt(b)
 need(half(b,0x30)==200 and half(b,0xc0)==200 and half(b,0x9e)==1,'R profile')
 need(all(half(b,n)==0 for n in [0x4a,0x4e,0x9a,0x9c]),'alternative gates')
def context(m,c):
 need(len(m)==68 and int.from_bytes(m[64:68],'little')==0x20010000 and half(m,10)==0 and half(m,12)==2 and m[56]in (0,1),'M context')
 need(len(c)==16 and (half(c,0),half(c,2),half(c,4))==(2160,1920,2880)and c[6]==92 and c[7]<=1 and c[8]in (0,3),'C geometry/finite subtype')
def parse_native(raw):
 need(type(raw)is str and len(raw.encode())<=24576,'receipt bound');v=strict(raw)
 expected={'schema','accepted','restore','restoreAttempted','loggerMayRemain','phase','device','bindingQualified','opened','claimed','released','closed','headers','bulks','inputs','writes','retries','thresholdWrites','arms','uiOperations','resets','startUs','endUs','wholeDeadlineUs','retained','physicalPictureObserved','atomicContextProven'}
 need(type(v)is dict and set(v)==expected,'success exact fields')
 need(v['schema']=='logger-gate-reconciliation-fm-v1' and v['accepted']is True,'native refusal preserved')
 for k in ['bindingQualified','opened','claimed','released','closed']:need(v[k]is True,'lifecycle '+k)
 for k in ['loggerMayRemain','physicalPictureObserved','atomicContextProven']:need(v[k]is False,'limit '+k)
 for k in ['retries','thresholdWrites','arms','uiOperations','resets']:need(integer(v[k])and v[k]==0,'zero '+k)
 need(integer(v['device'])and 1<=v['device']<=127 and v['phase']=='ReadyForHeader','device/phase')
 need(all(integer(v[k])and v[k]>=0 for k in ['startUs','endUs','wholeDeadlineUs']),'clock types')
 need(v['startUs']<=v['endUs']<=v['wholeDeadlineUs']==v['startUs']+30000000,'clock budget')
 written=v['restore']=='readback-zero';need(written or v['restore']=='already-zero-no-write','restore status')
 need(v['restoreAttempted']is written,'restore flag')
 for k,n in [('headers',5 if written else 4),('bulks',10 if written else 8),('inputs',4),('writes',1 if written else 0)]:need(integer(v[k])and v[k]==n,'exact '+k)
 roles=['fresh-M','fresh-C','fresh-R']+(['restore']if written else[])+['fresh-R'];specs={'M':('0x470004a0',68),'C':('0x47000bc0',16),'R':('0x47012400',256)}
 need(type(v['retained'])is list and len(v['retained'])==len(roles),'retention count');windows=[];last=v['startUs'];headers=bulks=0
 for index,(cap,role)in enumerate(zip(v['retained'],roles)):
  need(type(cap)is dict and set(cap)=={'role','cycleIndex','windows','transfers'} and cap['role']==role and type(cap['cycleIndex'])is int and cap['cycleIndex']==0,'capture fields')
  need(type(cap['windows'])is list and type(cap['transfers'])is list and len(cap['transfers'])==2,'capture arrays')
  write=role=='restore'
  if write:need(cap['windows']==[],'write has no raw readback');name='logger';length=2
  else:
   need(len(cap['windows'])==1,'one window');w=cap['windows'][0];name=role[-1];address,length=specs[name]
   fields={'name','address','expected','count','complete','rawBase64','sha256'}|({'observedRtState'}if name=='R'else set())
   need(type(w)is dict and set(w)==fields and w['name']==name and w['address']==address and integer(w['expected'])and w['expected']==length and integer(w['count'])and w['count']==length and w['complete']is True,'window shape')
   b=base64.b64decode(w['rawBase64'],validate=True);need(len(b)==length and base64.b64encode(b).decode()==w['rawBase64']and hashlib.sha256(b).hexdigest()==w['sha256'],'raw extent/hash');windows.append((name,b))
   if name=='R':
    mirror=w['observedRtState'];need(type(mirror)is dict and all(integer(mirror.get(k))for k in ['stop','fault','ordinaryGate']),'RT mirror types')
    need(mirror=={'stop':half(b,0),'fault':half(b,10),'ordinaryGate':half(b,14),'classification':rt(b)},'RT mirror')
  for j,t in enumerate(cap['transfers']):
   need(type(t)is dict and set(t)=={'name','direction','expected','count','errno','beforeUs','afterUs'},'transfer exact')
   n=12 if j==0 else length;tn=('logger-header'if j==0 else'restore-payload')if write else name+('-header'if j==0 else'-data')
   need(t['name']==tn and t['direction']==('OUT'if j==0 or write else'IN')and all(integer(t[k])for k in ['expected','count','errno','beforeUs','afterUs']),'transfer types')
   need(t['expected']==t['count']==n and t['errno']==0 and last<=t['beforeUs']<=t['afterUs']<=v['endUs'],'complete ordered pair');last=t['afterUs'];bulks+=1
  headers+=1
 context(windows[0][1],windows[1][1]);logger(windows[2][1],1 if written else 0);logger(windows[3][1],0)
 need(headers==v['headers']and bulks==v['bulks'],'recomputed counts')
 return v,[],{'accepted':True,'terminalKnownPhase':True,'restoredOriginalZero':True,'restoreOnly':True,'thresholdWrites':0,'uiOperations':0,'atomicContextProven':False}
if __name__=='__main__':print(json.dumps(parse_native(open(sys.argv[1]).read())[2],sort_keys=True))
