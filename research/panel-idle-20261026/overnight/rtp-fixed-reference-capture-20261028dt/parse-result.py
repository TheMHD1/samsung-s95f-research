#!/usr/bin/env python3
"""Strict offline fixed DM capture parser. Transport acceptance is not atomicity."""
import base64,hashlib,json,struct
SPECS=[('start-R',0x47012400,256),('M',0x470004a0,68),('C',0x47000bc0,16),('start-N',0x4700ba28,36),('D',0x4700a60a,48),('X',0x47011000,96),('Y',0x47011400,96),('RGB',0x47011800,96),('B',0x47011c00,96),('Diff',0x47012000,96),('fixed-top-candidate',0x47015354,104),('fixed-bottom-candidate',0x47016264,104),('end-N',0x4700ba28,36),('end-R',0x47012400,256)]
FIELDS={'packingQualified','bindingChecks','schema','protocolPhase','device','opened','claimed','released','closed','accepted','headersSent','bulkTransfers','writes','uiOperations','atomicSnapshot','physicalPictureObserved','steps','windows','errors'}
def need(ok,why):
 if not ok:raise ValueError(why)
def integer(v):return type(v)is int and 0<=v<2**63
def sha(b):return hashlib.sha256(b).hexdigest()
def strict_json(s):
 def pairs(rows):
  out={}
  for k,v in rows:need(k not in out,'duplicate JSON field');out[k]=v
  return out
 return json.loads(s,object_pairs_hook=pairs,parse_constant=lambda s:(_ for _ in()).throw(ValueError('nonfinite')))
def binding_checks(rows):
 need(type(rows)is list and len(rows)==3,'three binding checks')
 def node(n):
  need(type(n)is dict and set(n)=={'return','errno','mask','mode','inode','devMajor','devMinor'},'native node fields')
  need(type(n['return'])is int and n['return'] in [-1,0] and all(type(n[k])is int and 0<=n[k]<2**64 for k in ['errno','mask','mode','inode','devMajor','devMinor']),'native node types')
 def typed(n,t):return n['return']==0 and n['errno']==0 and n['mask']&0x103==0x103 and n['mode']&0xf000==t and n['inode']>0
 def kernel(k,own):
  need(type(k)is dict and set(k)=={'return','errno','name','interface','rawBase64','sha256'},'kernel driver fields')
  need(type(k['return'])is int and type(k['errno'])is int and type(k['interface'])is int and k['interface']==2,'kernel driver types/interface')
  need(type(k['rawBase64'])is str and type(k['sha256'])is str,'kernel driver encoding')
  raw=base64.b64decode(k['rawBase64'],validate=True)
  need(len(raw)==260 and base64.b64encode(raw).decode()==k['rawBase64'] and sha(raw)==k['sha256'] and struct.unpack_from('<I',raw)[0]==2,'kernel driver bytes/hash')
  if own:
   need(k['return']==0 and k['errno']==0 and k['name']=='usbfs' and raw[4:10]==b'usbfs\0' and raw[10:]==bytes(250),'kernel usbfs name')
  else:need(k['return']==-1 and k['errno']==61 and k['name']is None and raw[4:]==bytes(256),'kernel preclaim ENODATA')
 for i,c in enumerate(rows):
  need(type(c)is dict and set(c)=={'stage','ownClaim','localFdMatches','link','follow','canonical','kernel'},'binding check fields')
  need(c['stage']==['before-open','unclaimed-fd','claimed-fd'][i] and c['ownClaim']is(i==2) and c['localFdMatches']is(i>0),'binding stage/ownership')
  for name in ['link','follow','canonical']:node(c[name])
  need(typed(c['canonical'],0x4000),'canonical usbfs directory')
  if i<2:
   need(all(c[k]['return']==-1 and c[k]['errno']==2 for k in ['link','follow']),'positive preclaim absence')
   if i==0:need(c['kernel']is None,'no preopen GETDRIVER')
   else:kernel(c['kernel'],False)
  else:
   kernel(c['kernel'],True)
   need(typed(c['link'],0xa000) and typed(c['follow'],0x4000),'owned native link/directory')
   need(all(c['follow'][k]==c['canonical'][k] for k in ['inode','devMajor','devMinor']),'owned canonical device/inode')
def decode_fixed(raw):
 need(type(raw)is bytes and len(raw)==104,'fixed candidate extent')
 values=[]
 for at in range(0,102,6):
  word,tail=struct.unpack_from('<IH',raw,at)
  values.extend((word&4095,(word>>12)&4095,(word>>24)|((tail&15)<<8),tail>>4))
 return {str(x):values[x-568] for x in (570,571,622,623,624,625,632,633)}
def parse_native(text):
 need(type(text)is str and len(text.encode('utf8'))<=24576,'receipt bound')
 n=strict_json(text);need(type(n)is dict and set(n)==FIELDS,'native fields');binding_checks(n['bindingChecks'])
 need(n['schema']=='dt-rtp-fixed-reference-v1' and n['protocolPhase']=='ReadyForHeader' and n['errors']==[],'terminal')
 need(type(n['device'])is int and 1<=n['device']<=127,'device')
 for k in ('opened','claimed','released','closed','accepted','packingQualified'):need(n[k]is True,'success '+k)
 for k in ('atomicSnapshot','physicalPictureObserved'):need(n[k]is False,'claim '+k)
 for k,v in [('headersSent',14),('bulkTransfers',28),('writes',0),('uiOperations',0)]:need(type(n[k])is int and n[k]==v,'count '+k)
 need(type(n['steps'])is list and len(n['steps'])==28,'steps');last=0
 for i,(name,address,length) in enumerate(SPECS):
  for j in (0,1):
   s=n['steps'][2*i+j];need(type(s)is dict and set(s)=={'name','direction','expected','count','errno','beforeUs','afterUs','before','after'},'step fields')
   need(s['name']==name+('-header' if j==0 else '-data') and s['direction']==('OUT' if j==0 else 'IN'),'step order')
   want=12 if j==0 else length
   need(type(s['expected'])is int and type(s['count'])is int and s['expected']==s['count']==want and type(s['errno'])is int and s['errno']==0,'exact count/error')
   need(s['before']==('ReadyForHeader' if j==0 else 'ExpectingIn') and s['after']==('ExpectingIn' if j==0 else 'ReadyForHeader'),'step phase')
   need(integer(s['beforeUs']) and integer(s['afterUs']) and last<=s['beforeUs']<=s['afterUs'],'time order');last=s['afterUs']
 need(last-n['steps'][0]['beforeUs']<=40_000_000,'pair span')
 need(type(n['windows'])is list and len(n['windows'])==14,'window count');raws=[];d={};brackets={}
 for i,(w,(name,address,size)) in enumerate(zip(n['windows'],SPECS)):
  need(type(w)is dict and set(w)=={'name','address','bytes','sha256','base64'},'window fields')
  need(w['name']==name and type(w['address'])is int and w['address']==address and type(w['bytes'])is int and w['bytes']==size,'window spec')
  need(type(w['base64'])is str and type(w['sha256'])is str,'window encoding');b=base64.b64decode(w['base64'],validate=True)
  need(base64.b64encode(b).decode()==w['base64'] and len(b)==size and sha(b)==w['sha256'],'raw extent/hash')
  d[name]=b;raws.append((name+'.bin',b,sha(b)));brackets[name]={'headerBeforeUs':n['steps'][2*i]['beforeUs'],'dataAfterUs':n['steps'][2*i+1]['afterUs']}
 half=lambda b,o:struct.unpack_from('<H',b,o)[0]
 need(struct.unpack_from('<I',d['M'],64)[0]==0x20010000 and half(d['M'],6)==2880 and half(d['M'],8)==1920 and half(d['M'],32)==0 and struct.unpack_from('<3H',d['C'])==(2160,1920,2880),'packing qualification')
 context={'xBase':half(d['M'],32),'packedBytes':half(d['M'],6),'lanes':half(d['M'],8),'rootMatches':struct.unpack_from('<I',d['M'],64)[0]==0x20010000,'geometryMatches':struct.unpack_from('<3H',d['C'])==(2160,1920,2880),'aa':half(d['M'],10),'ac':half(d['M'],12),'selectorC7':d['C'][7],'publicationBoundMirror':half(d['M'],42)}
 counters=lambda b:{'ordinals':list(struct.unpack_from('<6I',b)),'sourceCounts':list(struct.unpack_from('<6H',b,24))}
 state=lambda b:{'stop':half(b,0),'fault':half(b,10),'ordinaryGate':half(b,14),'alternateLimit':half(b,0xc4),'mode1RecordLatch':half(b,0x90)}
 columns={k:struct.unpack('<48H',d[k]) for k in ('X','Y','RGB','B','Diff')}
 tuples=[{'index':i,'x':columns['X'][i],'y':columns['Y'][i],'rgb':columns['RGB'][i],'b':columns['B'][i],'absoluteDifferenceOrMode6Zero':columns['Diff'][i]} for i in range(48)]
 interpretation={'schema':'dt-rtp-fixed-reference-interpretation-v1','transportAccepted':True,'sourceContext':context,'fixedReferenceCandidates':{'top':decode_fixed(d['fixed-top-candidate']),'bottom':decode_fixed(d['fixed-bottom-candidate'])},'fixedReferenceIdentityAtFaultProven':False,'startR':state(d['start-R']),'endR':state(d['end-R']),'startN':counters(d['start-N']),'endN':counters(d['end-N']),'rBytesEqual':d['start-R']==d['end-R'],'nBytesEqual':d['start-N']==d['end-N'],'readBrackets':brackets,'candidateTuples':tuples,'descriptorRawHalfwords':list(struct.unpack('<24H',d['D'])),'atomicSnapshot':False,'recordEpochProven':False,'actualFixedABranchProven':False,'physicalPictureObserved':False,'limitations':['source labels conditional on selected running layout','same bracket values do not prove atomicity or no intervening resets','five sequential column arrays may mix epochs/types or partially cleared data','B sample and unsigned difference do not generally recover selected A or its sign','D and current metadata are not a direct B ring header','no bus alias assumed for CPU20253002 ring','fixed payload has no header/epoch/channel tag; matching candidates do not prove historical A branch']}
 return n,raws,interpretation
if __name__=='__main__':
 import sys
 from pathlib import Path
 n,r,i=parse_native(Path(sys.argv[1]).read_text());print(json.dumps(i,sort_keys=True))
