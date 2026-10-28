#!/usr/bin/env python3
"""Strict offline DN receipt parser. No target access."""
from pathlib import Path
import base64,hashlib,json,re,struct
HERE=Path(__file__).resolve().parent
PROFILE=bytes.fromhex('[encoded-payload-omitted]')
NATIVE_FIELDS={'device','schema','action','protocolPhase','stage','opened','claimed','released','closed','writeAttempted','writeTransportComplete','readbackVerified','limitMayHaveChanged','accepted','physicalPictureObserved','rootCauseFixEstablished','headersSent','bulkTransfers','steps','windows','errors'}
def need(ok,why):
 if not ok:raise ValueError(why)
def sha(b):return hashlib.sha256(b).hexdigest()
def strict_json(s):
 def pairs(items):
  d={}
  for k,v in items:need(k not in d,'duplicate key');d[k]=v
  return d
 return json.loads(s,object_pairs_hook=pairs,parse_constant=lambda s:(_ for _ in ()).throw(ValueError('nonfinite')))
def integer(v):return type(v)is int and 0<=v<2**63
def half(b,i):return struct.unpack_from('<H',b,i)[0]
def dynamic(i):return 0x86<=i<0x8a or 0x8c<=i<0x8e or 0x90<=i<0x94 or 0xa2<=i<0xa4
def guard_r(b,expected):
 need(len(b)==256,'R extent')
 for i,v in enumerate(b):
  if not dynamic(i) and i not in {0xc4,0xc5,0xca}:need(v==PROFILE[i],'R profile '+str(i))
 need(b[0xca]<=1,'R selector domain')
 need(half(b,0)==half(b,10)==half(b,6)==0 and half(b,14)==1,'clean gate/logger')
 need(half(b,0xc4)==expected and half(b,0x30)==half(b,0xc0)==200,'threshold')
 need(half(b,0x9e)==1 and all(half(b,i)==0 for i in [0x4a,0x4e,0x9a,0x9c]),'alternative gates/latches')
def parse_native(text):
 need(type(text)is str and len(text.encode())<=24576,'stdout bound')
 rows=[];gc=[]
 for s in text.splitlines():
  if s.startswith('[GC_INFO]'):need(False,'console telemetry forbidden in private structured receipt')
  else:need(s.startswith('{') and s.endswith('}'),'row framing');rows.append(strict_json(s))
 need(len(rows)==1,'one native row');n=rows[0];need(type(n)is dict and set(n)==NATIVE_FIELDS,'native fields')
 need(type(n['device'])is int and 1<=n['device']<=127,'device binding')
 need(n['schema']=='dn-fixed-limit-v1' and n['action'] in ['set40to200','restore200to40'],'schema/action')
 for k in ['opened','claimed','released','closed','writeAttempted','writeTransportComplete','readbackVerified','accepted']:need(n[k]is True,'accepted field '+k)
 for k in ['physicalPictureObserved','rootCauseFixEstablished','limitMayHaveChanged']:need(n[k]is False,'claim field '+k)
 need(n['protocolPhase']=='ReadyForHeader' and n['stage']=='complete' and n['errors']==[],'terminal')
 need(type(n['headersSent'])is int and n['headersSent']==7 and type(n['bulkTransfers'])is int and n['bulkTransfers']==14,'counts')
 order=[('callbacks',64),('baseline-R',256),('pre-M',68),('pre-C',16),('fresh-R',256),('write',2),('readback-R',256)]
 need(type(n['steps'])is list and len(n['steps'])==14,'step count');last=0
 for j,(name,size) in enumerate(order):
  for k in range(2):
   s=n['steps'][j*2+k];need(type(s)is dict and set(s)=={'name','direction','expected','count','errno','beforeUs','afterUs','before','after'},'step fields')
   write=name=='write';want=name+('-header' if k==0 else '-payload' if write else '-data');pending='ExpectingWritePayload' if write else 'ExpectingReadIn'
   need(s['name']==want and s['direction']==('OUT' if k==0 or write else 'IN'),'step order/direction')
   need(type(s['expected'])is int and s['expected']==(12 if k==0 else size) and type(s['count'])is int and s['count']==s['expected'] and type(s['errno'])is int and s['errno']==0,'exact count/errno')
   need(s['before']==('ReadyForHeader' if k==0 else pending) and s['after']==(pending if k==0 else 'ReadyForHeader'),'phase')
   need(integer(s['beforeUs']) and integer(s['afterUs']) and last<=s['beforeUs']<=s['afterUs'],'time order');last=s['afterUs']
 need(n['steps'][-1]['afterUs']-n['steps'][0]['beforeUs']<=40_000_000,'whole deadline')
 need(type(n['windows'])is list and len(n['windows'])==6,'window count');raws=[];d={}
 for w,(name,size) in zip(n['windows'],[x for x in order if x[0]!='write']):
  need(type(w)is dict and set(w)=={'name','bytes','sha256','base64'},'window fields');need(w['name']==name and type(w['bytes'])is int and w['bytes']==size,'window name/size')
  need(type(w['base64'])is str and type(w['sha256'])is str,'window encoding types');b=base64.b64decode(w['base64'],validate=True)
  need(base64.b64encode(b).decode()==w['base64'] and len(b)==size and sha(b)==w['sha256'],'window bytes/hash');d[name]=b;raws.append((name+'.bin',b,sha(b)))
 old,new=(40,200) if n['action']=='set40to200' else (200,40)
 for name in ['baseline-R','fresh-R']:guard_r(d[name],old)
 guard_r(d['readback-R'],new)
 need(d['baseline-R'][0xca]==d['fresh-R'][0xca],'selector preflight stable')
 for i in range(256):
  if not dynamic(i) and i!=0xc4:need(d['fresh-R'][i]==d['readback-R'][i],'nonstatus change '+str(i))
 cb=d['callbacks'];need(struct.unpack_from('<8I',cb,12)==(0x2945d,0x293d1,0x294fb,0,0,0x28b85,0x28cf1,0x294f5),'callback tuple')
 m,c=d['pre-M'],d['pre-C'];need(struct.unpack_from('<I',m,64)[0]==0x20010000 and half(m,10)==0 and half(m,12)==2 and m[56]==1,'mode/root/scan')
 need([half(m,i) for i in [22,24,26,28,38,40]]==[500,0,500,0,3183,500],'numeric profile')
 need(struct.unpack_from('<3H',c)==(2160,1920,2880) and c[6]==92 and c[7]<=1 and c[8]==3,'C geometry/selector')
 return n,raws,gc
if __name__=='__main__':
 import sys
 n,raws,gc=parse_native(Path(sys.argv[1]).read_text());print(json.dumps({'accepted':True,'action':n['action'],'headersSent':7,'bulkTransfers':14,'physicalPictureObserved':False,'rootCauseFixEstablished':False}))
