#!/usr/bin/env python3
"""Strict FN receipt and separate ring binding; no target access or acceptance waiver."""
import base64,hashlib,json,struct
LIMIT=24576
SPECS={'R':256,'M':68,'C':16,'P':16,'N':36,'H':96,'L':64,'Ring':15372}
CYCLE=['R','M','C','P','N','H','L','R']
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def strict(raw):
 def pairs(xs):
  out={}
  for k,v in xs:need(k not in out,'duplicate JSON key');out[k]=v
  return out
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:need(False,'nonfinite JSON'))
def integer(x,lo=0,hi=2**63-1):return type(x)is int and lo<=x<=hi
def b64(v):
 need(type(v)is str,'base64 type');b=base64.b64decode(v,validate=True);need(base64.b64encode(b).decode()==v,'canonical base64');return b
def half(b,o):return struct.unpack_from('<H',b,o)[0]
def rt(b):
 need(len(b)==256 and half(b,0xc4)==40,'R fixed40')
 t=(half(b,0),half(b,10),half(b,14));need(t in [(0,0,1),(1,4097,0),(0,0,0)],'known RT');return {(0,0,1):0,(1,4097,0):1,(0,0,0):3}[t]
def logger(b,n):
 rt(b);need(half(b,6)==n,'exact logger gate');need(all(half(b,o)==v for o,v in [(0x30,200),(0xc0,200),(0x9e,1),(0x4a,0),(0x4e,0),(0x9a,0),(0x9c,0)]),'R context profile')
def context(m,c,initial=False):
 need(struct.unpack_from('<I',m,64)[0]==0x20010000 and half(m,10)==0 and half(m,12)==2 and m[56]in [0,1]and(not initial or m[56]==1),'M context')
 need([half(c,0),half(c,2),half(c,4),c[6]]==[2160,1920,2880,92]and c[7]<=1 and c[8]in [0,1,2,3,4]and(not initial or c[8]==3),'C context')
def capture(c,complete=True):
 need(type(c)is dict and set(c)=={'role','cycle','windows','transfers'},'capture fields');need(integer(c['cycle'],0,56),'capture cycle');need(type(c['windows'])is list and len(c['windows'])<=8 and type(c['transfers'])is list and len(c['transfers'])<=16,'capture capacities')
 raw=[];previous=None
 for w in c['windows']:
  need(type(w)is dict and set(w)=={'name','count','raw'}and w['name']in SPECS and integer(w['count'],-1,2**31-1),'window fields/count');r=b64(w['raw']);need(len(r)==max(0,min(w['count'],SPECS[w['name']])),'raw exact clampedcount');raw.append(r)
  if complete:need(w['count']==SPECS[w['name']],'full window')
 for i,t in enumerate(c['transfers']):
  need(type(t)is list and len(t)==7 and t[0]in ['OUT','IN'] and t[1]in [2,12,*SPECS.values()]and(t[2]is None or integer(t[2],-2**31,2**31-1))and integer(t[3],0,2**31-1),'transfer fields')
  for v in t[4:6]:need(v is None or integer(v),'timestamp')
  need(t[4]is None or t[5]is None or t[4]<=t[5],'pair timestamp order');need(t[6]is None or type(t[6])is str and len(json.dumps(t[6]).encode())<=128,'bounded error')
  if complete:
   need(previous is None or t[4]is not None and previous<=t[4],'transfer sequence ordering');previous=t[5]
  if complete:need(t[2]==t[1] and t[3]==0 and t[4]is not None and t[5]is not None and t[6]is None,'complete transfer')
 if raw:
  need(len(c['transfers'])==2*len(raw),'matching pair count')
  for i,w in enumerate(c['windows']):need(c['transfers'][2*i][0:2]==['OUT',12]and c['transfers'][2*i+1][0:2]==['IN',SPECS[w['name']]],'read pairs')
 return raw
def pack_row(c,data,start):
 r,m,cc,p,n,h,l,e=data;out=bytearray(58);out[0]=(rt(r)<<4)|rt(e);out[1]=cc[7];out[2:4]=r[0xc4:0xc6];out[4:6]=e[0xc4:0xc6];out[6:10]=h[4:8];out[10:12]=h[28:30];out[12:20]=h[40:48];out[20:24]=n[:4]
 for pos,t in [(24,c['transfers'][10][4]),(28,c['transfers'][11][5])]:need(integer(t-start,0,2**32-1),'H time delta');struct.pack_into('<I',out,pos,t-start)
 for pos,raw,at in [(32,m,42),(34,m,2),(36,m,4),(38,m,0x22),(40,m,0x24),(42,e,0x60),(44,e,0x6e),(54,e,0xca),(56,e,0x68)]:out[pos:pos+2]=raw[at:at+2]
 out[46:50]=p[4:8];out[50:54]=p[8:12];return bytes(out)
def key_exposure(v):
 """Derived only after strict protocol validation; optional R headers exclude cleanup."""
 out={'keyExposureQualified':False,'downBeganBeforeLaterOptionalR':False,'reason':'protocol_not_accepted','uiConsumptionProven':False,'keyCausalityEstablished':False,'physicalPictureObserved':False,'evidenceSource':'retained_optional_R_header_before_timestamps','candidateOptionalRHeaders':[],'witnessOptionalRHeader':None}
 if not v['accepted']:return out
 baseline=next(c for c in v['retained']if c['role']=='trigger-baseline')
 baseline_end=baseline['transfers'][-1][5];down=v['intervention']['calls'][0];down_before=down['beforeUs']
 out.update(baselineEndUs=baseline_end,downBeforeUs=down_before,sameNativeClock=True)
 successful=(down['phase']=='down'and down['started']is True and down['reaped']is True and down['timedOut']is False and type(down['exitCode'])is int and down['exitCode']==0 and 'error'not in down)
 if not successful:out['reason']='down_call_not_successful';return out
 if down_before<baseline_end:out['reason']='down_began_before_clean_baseline_end';return out
 candidates={}
 # Controls (prerestore/restored R) never enter this list. Duplicated last/current slots are deduplicated.
 for c in v['retained']:
  if c['cycle']<=baseline['cycle']:continue
  for i,w in enumerate(c['windows']):
   if w['name']=='R':
    stamp=c['transfers'][2*i][4];candidate={'cycle':c['cycle'],'windowIndex':i,'headerBeforeUs':stamp};candidates[(c['cycle'],i,stamp)]=candidate
 out['candidateOptionalRHeaders']=sorted(candidates.values(),key=lambda c:(c['headerBeforeUs'],c['cycle'],c['windowIndex']))
 later=[c for c in out['candidateOptionalRHeaders']if down_before<c['headerBeforeUs']]
 if not later:out['reason']='no_later_optional_R_header_after_down';return out
 out.update(keyExposureQualified=True,downBeganBeforeLaterOptionalR=True,reason='successful_down_before_later_optional_R_header',witnessOptionalRHeader=later[0]);return out
def parse_native(text):
 need(type(text)is str and len(text.encode())<=LIMIT and text.endswith('\n'),'bounded exclusive receipt');v=strict(text);need(type(v)is dict,'object')
 required={'schema','accepted','observationComplete','arm','restore','armAttempted','restoreAttempted','loggerMayRemain','phase','device','bindingQualified','opened','claimed','released','closed','terminal','headers','bulks','inputs','writes','retries','threshold','physicalPictureObserved','keyCausalityEstablished','startUs','endUs','wholeDeadlineUs','cyclesStarted','cleanCycles','quiescentCycles','rows','controls','retained','baselineRing','postRing'}
 allowed=required|{'bindingChecks','observationDeadlineUs','intervention','error','cleanupError','keyError'};need(required<=set(v)<=allowed,'receipt fields')
 need(v['schema']=='combined-event-checkpoints-fn-v1'and v['threshold']==40 and v['retries']==0 and v['physicalPictureObserved']is False and v['keyCausalityEstablished']is False,'family/scope')
 for k in ['accepted','observationComplete','armAttempted','restoreAttempted','loggerMayRemain','bindingQualified','opened','claimed','released','closed']:need(type(v[k])is bool,'bool '+k)
 for k in ['device','headers','bulks','inputs','writes','cyclesStarted','cleanCycles','quiescentCycles','retries','threshold']:need(integer(v[k],0,1000),'counter '+k)
 need(1<=v['device']<=127 and v['phase']in ['ReadyForHeader','ExpectingIn','ExpectingPayload','Unknown'],'device/phase')
 need(type(v['controls'])is list and len(v['controls'])<=10 and type(v['retained'])is list and len(v['retained'])<=3,'retention bound')
 rows=v['rows'];need(set(rows)=={'schema','recordBytes','count','rawBase64','sha256'}and rows['schema']=='fg-stockevent-checkpoints-v1'and rows['recordBytes']==58 and integer(rows['count'],0,56),'row fields');packed=b64(rows['rawBase64']);need(len(packed)==rows['count']*58 and sha(packed)==rows['sha256'],'row extent/hash')
 decoded=[]
 for i in range(rows['count']):
  b=packed[i*58:(i+1)*58];s,e=b[0]>>4,b[0]&15;need(s in [0,1,3]and e in [0,1,3]and half(b,2)==half(b,4)==40,'row state/limit');need(b[1]<=1,'selector domain');decoded.append({'cycle':i+1,'startRt':s,'endRt':e,'c7':b[1],'a0':struct.unpack_from('<I',b,6)[0],'selectorMirror':half(b,54),'referenceCounter':half(b,38)})
 if v['accepted']:
  need(v['observationComplete']and not v['loggerMayRemain'] and v['phase']=='ReadyForHeader'and all(v[k]is True for k in ['bindingQualified','opened','claimed','released','closed']),'accepted lifecycle')
  need(not(set(v)&{'error','cleanupError','keyError','bindingChecks'}),'accepted errors/refusal metadata')
  need(v['arm']=='readback-one'and v['restore']in ['readback-zero','already-zero-no-write'],'accepted logger outcome');need(v['armAttempted']and v['restoreAttempted']==(v['restore']=='readback-zero'),'write flags')
  need(all(integer(v.get(k))for k in ['startUs','endUs','wholeDeadlineUs','observationDeadlineUs']),'accepted clock fields');need(v['startUs']<=v['endUs']<=v['wholeDeadlineUs']==v['startUs']+40000000,'whole budget');need(1<=rows['count']==v['cyclesStarted']<=56,'complete row cycles');need(decoded[0]['startRt']==decoded[0]['endRt']==0,'fullclean first cycle')
  roles=['prearm-R','prearm-M','prearm-C','arm','armed-R','prerestore-M','prerestore-C','prerestore-R']+(['restore']if v['restoreAttempted']else[])+['restored-R'];need([c['role']for c in v['controls']]==roles,'control order')
  raw={}
  previous=v['startUs']
  for c in v['controls']:
   need(c['transfers']and previous<=c['transfers'][0][4]<=c['transfers'][-1][5]<=v['endUs'],'control clock range/order');previous=c['transfers'][-1][5]
   data=capture(c);raw[c['role']]=data
   if c['role']in ['arm','restore']:need(len(c['windows'])==0 and len(c['transfers'])==2 and[c['transfers'][i][0:2]for i in range(2)]==[['OUT',12],['OUT',2]],'fixed write pair')
   else:need(len(data)==1 and c['windows'][0]['name']==c['role'].split('-')[-1],'fixed control read')
  logger(raw['prearm-R'][0],0);need(rt(raw['prearm-R'][0])==0,'prearm clean');logger(raw['armed-R'][0],1);need(rt(raw['armed-R'][0])==0,'armed clean');context(raw['prearm-M'][0],raw['prearm-C'][0],True);context(raw['prerestore-M'][0],raw['prerestore-C'][0]);logger(raw['prerestore-R'][0],1 if v['restoreAttempted']else 0);logger(raw['restored-R'][0],0)
  need([c['role']for c in v['retained']]==['trigger-baseline','last-complete','current'],'retained order')
  for c in v['retained']:
   need(v['controls'][4]['transfers'][-1][5]<=c['transfers'][0][4]<=c['transfers'][-1][5]<=v['controls'][5]['transfers'][0][4],'retained within armed/readrestore interval')
   data=capture(c);need([w['name']for w in c['windows']]==CYCLE and 1<=c['cycle']<=rows['count'],'retained full cycle');context(data[1],data[2],c['cycle']==1);logger(data[0],1);logger(data[7],1);row=packed[(c['cycle']-1)*58:c['cycle']*58];need(row==pack_row(c,data,v['startUs']),'all58 retained row bytes binding')
  need(v['retained'][0]['cycle']==1 and v['retained'][1]['cycle']==v['retained'][2]['cycle']==rows['count'],'retention cycles')
  extra=12 if v['restoreAttempted']else 11;need(v['headers']==8*rows['count']+extra and v['bulks']==2*v['headers']and v['writes']==(2 if v['restoreAttempted']else 1)and v['inputs']==v['headers']-v['writes'],'total accounting')
  clean=sum(d['startRt']==d['endRt']==0 for d in decoded);q=sum(1 not in [d['startRt'],d['endRt']]and not d['startRt']==d['endRt']==0 for d in decoded);need(v['cleanCycles']==clean and v['quiescentCycles']==q,'separate clean/Q counts')
  if v['terminal']=='TransitionCaptured':need(1 in [decoded[-1]['startRt'],decoded[-1]['endRt']]and rows['count']>1,'terminal fault');need(all(1 not in [r['startRt'],r['endRt']]for r in decoded[:-1]),'no earlier fault')
  else:need(v['terminal']in ['TimeLimit','CycleLimit']and clean+q==rows['count'],'normal terminal')
  key=v.get('intervention');need(type(key)is dict and key['key']=='Left'and key['attempted']is True and key['completed']is True and 'error'not in key and key['physicalPictureObserved']is False and key['uiReceiptObserved']is False,'key scope');need(len(key['calls'])==2 and[k['phase']for k in key['calls']]==['down','up'],'one key pair')
  need(integer(key.get('armedUs'))and integer(key.get('endUs'))and v['retained'][0]['transfers'][-1][5]<=key['armedUs']<=key['endUs']<=v['endUs'],'key trigger/end ordering')
  previous=key['armedUs']
  need(set(key)=={'key','trigger','attempted','completed','armedUs','endUs','uiReceiptObserved','physicalPictureObserved','calls'}and key['trigger']=='first-full-clean-cycle','key state fields')
  for k in key['calls']:
   need(set(k)=={'phase','beforeUs','afterUs','exitCode','started','reaped','timedOut','stdoutBytes','stderrBytes'},'key call fields')
   need(integer(k.get('beforeUs'))and integer(k.get('afterUs'))and previous<=k['beforeUs']<=k['afterUs']<=key['endUs'],'key call ordering');previous=k['afterUs']
   need(k['started']is True and k['reaped']is True and k['timedOut']is False and integer(k['exitCode'],0,0)and integer(k['stdoutBytes'],0,4096)and integer(k['stderrBytes'],0,4096) and 'error'not in k,'key child completion')
  for label in ['baselineRing','postRing']:
   meta=v[label];need(set(meta)=={'complete','bytes','sha256','transfer'}and meta['complete']is True and meta['bytes']==15372,'full ring metadata');cap=meta['transfer'];need(cap['windows']==[{'name':'Ring','count':15372}],'ring withheld from receipt');need(len(cap['transfers'])==2 and [t[:2]for t in cap['transfers']]==[['OUT',12],['IN',15372]]and all(t[2]==t[1]and t[3]==0 and t[6]is None and integer(t[4])and integer(t[5])for t in cap['transfers']),'full ring pair');need(v['startUs']<=cap['transfers'][0][4]<=cap['transfers'][0][5]<=cap['transfers'][1][4]<=cap['transfers'][1][5]<=v['endUs'],'ring pair timestamps')
  need(v['baselineRing']['transfer']['transfers'][-1][5]<=v['controls'][0]['transfers'][0][4]and v['controls'][-1]['transfers'][-1][5]<=v['postRing']['transfer']['transfers'][0][4],'ring control ordering')
 exposure=key_exposure(v)
 return v,decoded,{'accepted':v['accepted'],'protocolAccepted':v['accepted'],'keyExposureQualified':exposure['keyExposureQualified'],'keyExposureReason':exposure['reason'],'downBeganBeforeLaterOptionalR':exposure['downBeganBeforeLaterOptionalR'],'keyExposure':exposure,'terminalKnownPhase':v['phase']=='ReadyForHeader'and v['released']and v['closed'],'loggerRestored':not v['loggerMayRemain'],'physicalPictureObserved':False,'eventArgumentsAreCallsites':False,'ringWrapExcluded':False}
def bind_rings(v,baseline,post):
 out={}
 for label,b in [('baselineRing',baseline),('postRing',post)]:
  m=v[label];need(type(b)is bytes and len(b)==m['bytes']and sha(b)==m['sha256'],'sidecar exact hash/length');need(len(b)==15372,'complete ring');w,r,f=struct.unpack_from('<III',b);need(w<=15360 and r<=15360,'cursor inclusive bound');out[label]={'write':w,'read':r,'flag':f,'sha256':sha(b),'bytes':len(b)}
 return out
