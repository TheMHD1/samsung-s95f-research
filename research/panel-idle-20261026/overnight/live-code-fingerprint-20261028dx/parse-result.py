#!/usr/bin/env python3
"""Strict offline fixed DM capture parser. Transport acceptance is not atomicity."""
import base64,hashlib,json,struct
SPECS=[('predicate', 1174413344, 16), ('selection', 1174453592, 16), ('tuple', 1174455760, 16), ('setter', 1174454752, 16)]
FINGERPRINTS=['df8983595b89547c2d3ff02d85bd71dbe68b8194f4387d2d457cfcc3f475e613', '5a10d80a33abe58fcc06cdbf1c5be96c1c0aa149cf502e813eb70777d51ffd40', 'd7a26d7d9da0971cb7f9cbf5a9c903d33a576a77161625f005eac3ca673d0ff9', '2567aab0b47ab0e15e46c63d2ccc0f14649d70d3789fc7a5b1d797174ff58291']
FIELDS={'sampledCodeMatch','wholeRunningImageAttested','executableWriteQualified','bindingChecks','schema','protocolPhase','device','opened','claimed','released','closed','accepted','headersSent','bulkTransfers','writes','uiOperations','atomicSnapshot','physicalPictureObserved','steps','windows','errors'}
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
def parse_native(text):
 need(type(text)is str and len(text.encode('utf8'))<=24576,'receipt bound')
 n=strict_json(text);need(type(n)is dict and set(n)==FIELDS,'native fields');binding_checks(n['bindingChecks'])
 need(n['schema']=='dx-code-fingerprint-v1' and n['protocolPhase']=='ReadyForHeader' and n['errors']==[],'terminal')
 need(type(n['device'])is int and 1<=n['device']<=127,'device')
 for k in ('opened','claimed','released','closed','accepted','sampledCodeMatch'):need(n[k]is True,'success '+k)
 for k in ('atomicSnapshot','physicalPictureObserved','wholeRunningImageAttested','executableWriteQualified'):need(n[k]is False,'claim '+k)
 for k,v in [('headersSent',4),('bulkTransfers',8),('writes',0),('uiOperations',0)]:need(type(n[k])is int and n[k]==v,'count '+k)
 need(type(n['steps'])is list and len(n['steps'])==8,'steps');last=0
 for i,(name,address,length) in enumerate(SPECS):
  for j in (0,1):
   s=n['steps'][2*i+j];need(type(s)is dict and set(s)=={'name','direction','expected','count','errno','beforeUs','afterUs','before','after'},'step fields')
   need(s['name']==name+('-header' if j==0 else '-data') and s['direction']==('OUT' if j==0 else 'IN'),'step order')
   want=12 if j==0 else length
   need(type(s['expected'])is int and type(s['count'])is int and s['expected']==s['count']==want and type(s['errno'])is int and s['errno']==0,'exact count/error')
   need(s['before']==('ReadyForHeader' if j==0 else 'ExpectingIn') and s['after']==('ExpectingIn' if j==0 else 'ReadyForHeader'),'step phase')
   need(integer(s['beforeUs']) and integer(s['afterUs']) and last<=s['beforeUs']<=s['afterUs'],'time order');last=s['afterUs']
 need(last-n['steps'][0]['beforeUs']<=40_000_000,'pair span')
 need(type(n['windows'])is list and len(n['windows'])==4,'window count');raws=[];d={};brackets={}
 for i,(w,(name,address,size)) in enumerate(zip(n['windows'],SPECS)):
  need(type(w)is dict and set(w)=={'name','address','bytes','sha256','base64'},'window fields')
  need(w['name']==name and type(w['address'])is int and w['address']==address and type(w['bytes'])is int and w['bytes']==size,'window spec')
  need(type(w['base64'])is str and type(w['sha256'])is str,'window encoding');b=base64.b64decode(w['base64'],validate=True)
  need(base64.b64encode(b).decode()==w['base64'] and len(b)==size and sha(b)==w['sha256'],'raw extent/hash')
  need(sha(b)==FINGERPRINTS[i],'selected image1 sampled code identity '+name)
  d[name]=b;raws.append((name+'.bin',b,sha(b)));brackets[name]={'headerBeforeUs':n['steps'][2*i]['beforeUs'],'dataAfterUs':n['steps'][2*i+1]['afterUs']}
 interpretation={'schema':'dx-code-fingerprint-interpretation-v1','transportAccepted':True,'sampledCodeMatch':True,'sampledBytes':64,'samples':[{'name':name,'busAddress':hex(address),'bytes':size,'sha256':FINGERPRINTS[i]}for i,(name,address,size)in enumerate(SPECS)],'readBrackets':brackets,'atomicSnapshot':False,'physicalPictureObserved':False,'wholeRunningImageAttested':False,'activeInstructionFetchProven':False,'executableWriteQualified':False,'limitations':['exact matches qualify only four sampled16-byte locations','source-qualified alias does not attest every executing instruction or caller','no executable writes, scratch ownership, cache visibility or hook installation/rollback qualification follows']}

 return n,raws,interpretation
if __name__=='__main__':
 import sys
 from pathlib import Path
 n,r,i=parse_native(Path(sys.argv[1]).read_text());print(json.dumps(i,sort_keys=True))
