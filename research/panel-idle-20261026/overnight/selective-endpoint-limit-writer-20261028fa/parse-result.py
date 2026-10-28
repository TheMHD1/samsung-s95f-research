#!/usr/bin/env python3
"""Strict offline DV receipt parser. No target access."""
from pathlib import Path
import base64,hashlib,json,re,struct
HERE=Path(__file__).resolve().parent
PROFILE=bytes.fromhex('[encoded-payload-omitted]')
NATIVE_FIELDS={'bindingChecks','device','schema','action','protocolPhase','stage','opened','claimed','released','closed','writeAttempted','writeTransportComplete','readbackVerified','limitMayHaveChanged','accepted','physicalPictureObserved','rootCauseFixEstablished','headersSent','bulkTransfers','steps','windows','errors'}
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
STATIC={'base':2075,'reference':24,'coefficient':15,'scale':195,'floor':3000,'cap':3800,'b_lower':500}
THERMAL_HALFWORDS=(0x20,0x98,0xbc)
ECHO_HALFWORD=0xac

def need(ok,why):
 if not ok:raise ValueError(why)
def u16(raw,offset):return struct.unpack_from('<H',raw,offset)[0]
def scaled_temperature(raw_u16):
 need(type(raw_u16)is int and 0<=raw_u16<=65535,'raw getter u16')
 return raw_u16//16

def scaled_reference(raw_u16):
 ref=scaled_temperature(raw_u16)
 return 25 if ref>4000 else ref

def endpoint(base,reference,temp,coefficient,scale,floor,cap):
 for v in [base,reference,temp,coefficient,scale,floor,cap]:need(type(v)is int and 0<=v<=65535,'u16 operands')
 # ARM sub/MLA/MUL wrap at32bits. UBFX selects bits7..22, not arbitrary division.
 delta=(temp-reference)&0xffffffff
 mla=(base+coefficient*delta)&0xffffffff
 product=(mla*scale)&0xffffffff
 candidate=(product>>7)&65535
 # Actual branch first caps; only the non-capped branch applies the minimum.
 output=cap if candidate>cap else max(floor,candidate)
 return {'deltaU32':delta,'mlaU32':mla,'productU32':product,'extractedU16':candidate,'endpoint':output}

def endpoint_observations(raw):
 """Compute against shared diagnostics; neither endpoint is assumed freshly updated."""
 need(type(raw)is bytes and len(raw)==256,'R256')
 need(u16(raw,0x94)==STATIC['base']and u16(raw,0x96)==STATIC['reference'],'fixed base/reference mirrors')
 temp=u16(raw,0x98);need(temp<=4095,'temperature mirror source range')
 echo=u16(raw,ECHO_HALFWORD);need(echo<=254,'own protocol echo range / zero high byte')
 out={'temperature':temp,'echo':echo,'modes':{}}
 for name,at,co,sc,ca,fl in [('normal',0x20,0xae,0xb0,0xb2,0x2e),('alternate',0xbc,0xb6,0xb8,0xba,0x2c)]:
  need((u16(raw,co),u16(raw,sc),u16(raw,ca),u16(raw,fl))==(STATIC['coefficient'],STATIC['scale'],STATIC['cap'],STATIC['floor']),'fixed coefficient/scale/cap/floor '+name)
  calc=endpoint(STATIC['base'],STATIC['reference'],temp,STATIC['coefficient'],STATIC['scale'],STATIC['floor'],STATIC['cap'])
  need(STATIC['b_lower']<calc['endpoint']<=4095 and STATIC['floor']<=calc['endpoint']<=STATIC['cap'],'bounded B endpoint '+name)
  out['modes'][name]={'actual':u16(raw,at),'model':calc,'matchesSharedDiagnostics':u16(raw,at)==calc['endpoint']}
 return out

ALTERNATE_ENDPOINT_IMAGE=frozenset(endpoint(2075,24,t,15,195,3000,3800)['endpoint'] for t in range(4096))

def profile_prediction(raw):
 """Restrictive ordinary-current / alternate finite-preimage admission."""
 out=endpoint_observations(raw)
 need(out['modes']['normal']['matchesSharedDiagnostics'],'source-model endpoint normal')
 actual=out['modes']['alternate']['actual']
 need(actual in ALTERNATE_ENDPOINT_IMAGE,'alternate endpoint exact finite source image')
 out['modes']['alternate']['hasFiniteSourcePreimage']=True
 return out

def pairwise_thermal_stable(before,after):
 need(type(before)is bytes and type(after)is bytes and len(before)==len(after)==256,'R pair')
 return all(u16(before,o)==u16(after,o)for o in THERMAL_HALFWORDS)

# Design-only composition with the previous exact profile, not a native writer.
def legacy_historical_byte(i):return 0x86<=i<0x8a or 0x8c<=i<0x8e or 0x90<=i<0x94 or 0xa2<=i<0xa4
ADDITIONAL_MODEL_BYTES=frozenset(i+j for i in (*THERMAL_HALFWORDS,ECHO_HALFWORD)for j in [0,1])
def validate_candidate_r(raw,expected_limit,frozen_profile):
 need(type(raw)is bytes and len(raw)==256 and type(frozen_profile)is bytes and len(frozen_profile)==256,'R/profile extent')
 need(expected_limit in [40,200],'fixed action limit')
 for i,v in enumerate(raw):
  if not legacy_historical_byte(i) and i not in ADDITIONAL_MODEL_BYTES|{0xc4,0xc5,0xca}:need(v==frozen_profile[i],'remaining exact profile byte '+str(i))
 need(raw[0xca]<=1,'legacy observed selector domain')
 need(u16(raw,0)==u16(raw,10)==u16(raw,6)==0 and u16(raw,14)==1,'clean gate/logger')
 need(u16(raw,0xc4)==expected_limit and u16(raw,0x30)==u16(raw,0xc0)==200,'fixed action/normal limits')
 need(u16(raw,0x9e)==1 and all(u16(raw,o)==0 for o in [0x4a,0x4e,0x9a,0x9c]),'unchanged alternative gates/latches')
 return profile_prediction(raw)

def validate_candidate_context(m,c,r):
 need(type(m)is bytes and len(m)==68 and type(c)is bytes and len(c)==16,'M/C extents')
 need(struct.unpack_from('<I',m,64)[0]==0x20010000 and u16(m,10)==0 and u16(m,12)==2 and m[56]==1,'root/mode/scan')
 need([u16(m,o)for o in [22,24,26,28]]==[500,0,500,0] and u16(m,40)==500,'fixed directional/lower thresholds')
 need(u16(m,38)==u16(r,0x20),'M current ordinary endpoint mirror agreement')
 need(struct.unpack_from('<3H',c)==(2160,1920,2880) and c[6]==92 and c[7]<=1 and c[8]==3,'unchanged geometry/profile/selector')

def validate_transaction_pair(before,after,old_limit,new_limit,frozen_profile):
 validate_candidate_r(before,old_limit,frozen_profile);validate_candidate_r(after,new_limit,frozen_profile)
 need(before[0xca]==after[0xca],'legacy selector stable')
 need(pairwise_thermal_stable(before,after),'thermal tuple stable in one bounded write transaction')
 for i in range(256):
  if not legacy_historical_byte(i) and i not in {0xc4,0xac,0xad}:need(before[i]==after[i],'unchanged nonstatus byte '+str(i))
def guard_r(b,expected):validate_candidate_r(b,expected,PROFILE)
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
def parse_native(text):
 need(type(text)is str and len(text.encode())<=24576,'stdout bound')
 rows=[];gc=[]
 for s in text.splitlines():
  if s.startswith('[GC_INFO]'):need(False,'console telemetry forbidden in private structured receipt')
  else:need(s.startswith('{') and s.endswith('}'),'row framing');rows.append(strict_json(s))
 need(len(rows)==1,'one native row');n=rows[0];need(type(n)is dict and set(n)==NATIVE_FIELDS,'native fields')
 need(type(n['device'])is int and 1<=n['device']<=127,'device binding')
 binding_checks(n['bindingChecks'])
 need(n['schema']=='fa-fixed-limit-v1' and n['action'] in ['set40to200','restore200to40'],'schema/action')
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
 validate_transaction_pair(d['baseline-R'],d['fresh-R'],old,old,PROFILE)
 validate_transaction_pair(d['fresh-R'],d['readback-R'],old,new,PROFILE)
 cb=d['callbacks'];need(struct.unpack_from('<8I',cb,12)==(0x2945d,0x293d1,0x294fb,0,0,0x28b85,0x28cf1,0x294f5),'callback tuple')
 m,c=d['pre-M'],d['pre-C'];need(struct.unpack_from('<I',m,64)[0]==0x20010000 and half(m,10)==0 and half(m,12)==2 and m[56]==1,'mode/root/scan')
 need([half(m,i) for i in [22,24,26,28,40]]==[500,0,500,0,500] and half(m,38)==half(d['baseline-R'],0x20),'numeric profile / validated ordinary endpoint mirror')
 need(struct.unpack_from('<3H',c)==(2160,1920,2880) and c[6]==92 and c[7]<=1 and c[8]==3,'C geometry/selector')
 return n,raws,gc
if __name__=='__main__':
 import sys
 n,raws,gc=parse_native(Path(sys.argv[1]).read_text());print(json.dumps({'accepted':True,'action':n['action'],'headersSent':7,'bulkTransfers':14,'physicalPictureObserved':False,'rootCauseFixEstablished':False}))
