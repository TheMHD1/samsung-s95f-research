#!/usr/bin/env python3
"""Strict offline zero-vendor diagnostic receipt parser; no driver-policy inference."""
import base64,hashlib,json,struct
FIELDS={'schema','device','interface','vendorHeaders','vendorBulkTransfers','vendorControlTransfers','opened','claimed','released','closed','accepted','driverPolicyEstablished','physicalPictureObserved','claimReturn','claimErrno','releaseReturn','releaseErrno','closeReturn','closeErrno','preDriver','postDriver','preKernelDriver','postKernelDriver','preFd','postFd','errors'}
def need(b,s):
 if not b:raise ValueError(s)
def sha(b):return hashlib.sha256(b).hexdigest()
def integer(v,a=0,b=2**64):return type(v)is int and a<=v<b
def strict_json(s):
 def pairs(rows):
  d={}
  for k,v in rows:need(k not in d,'duplicate key');d[k]=v
  return d
 return json.loads(s,object_pairs_hook=pairs,parse_constant=lambda s:(_ for _ in()).throw(ValueError('nonfinite')))
def unb64(s):
 need(type(s)is str,'base64 type');b=base64.b64decode(s,validate=True);need(base64.b64encode(b).decode()==s,'canonical base64');return b
def status(s,fd=False):
 need(type(s)is dict and set(s)=={'return','errno','mask','mode','rdevMajor','rdevMinor','inode'},'stat fields')
 for k in s:need(integer(s[k],-1 if k=='return' else 0),'stat integer '+k)
 need(s['return']in(-1,0) and (s['errno']==0 if s['return']==0 else s['errno']>0),'stat return/errno')
 if fd:need(s['return']==0 and s['mask']&1 and s['mode']&0xf000==0x2000 and s['rdevMajor']==189 and s['rdevMinor']==825,'fixed FD')
def snapshot(s):
 need(type(s)is dict and set(s)=={'beforeUs','afterUs','managed','nativeLink','noFollowStat','followStat'},'snapshot fields')
 need(integer(s['beforeUs'])and integer(s['afterUs'])and s['beforeUs']<=s['afterUs'],'snapshot time')
 need(type(s['managed'])is dict and set(s['managed'])=={'linkTarget','resolvedFinal','directoryExists','fileExists'},'managed fields')
 for k,v in s['managed'].items():
  need(type(v)is dict and set(v)=={'ok','value','error'}and type(v['ok'])is bool,'observation')
  need((v['error']is None and(v['value']is None or type(v['value'])is str))if v['ok']else(v['value']is None and type(v['error'])is str and 0<len(v['error'])<=4096),'observation value/error')
  if k.endswith('Exists')and v['ok']:need(v['value']in('True','False'),'exists literal')
 v=s['nativeLink'];need(type(v)is dict and set(v)=={'count','errno','target','rawBase64'},'readlink fields');need(integer(v['count'],-1,4097)and integer(v['errno'],0,4096),'readlink result');b=unb64(v['rawBase64']);need(len(b)==max(0,v['count']),'readlink extent');need((v['errno']>0 and v['target']is None)if v['count']<0 else(v['errno']==0 and(v['target']==b.decode('utf8',errors='replace')if v['count']<4096 else v['target']is None)),'readlink target/errno')
 status(s['noFollowStat']);status(s['followStat'])
def driver(v):
 need(type(v)is dict and set(v)=={'return','errno','name','rawBase64','sha256'},'driver fields');need(integer(v['return'],-1,1)and integer(v['errno'],0,4096),'driver result');b=unb64(v['rawBase64']);need(len(b)==260 and struct.unpack_from('<I',b)[0]==2 and sha(b)==v['sha256'],'driver raw ABI/hash');nul=b.find(b'\0',4);name=b[4:nul].decode('utf8',errors='replace')if v['return']==0 and nul>=4 else None;need(v['name']==name and(v['errno']==0 if v['return']==0 else v['errno']>0),'driver name/errno')
def parse_native(s):
 need(type(s)is str and len(s.encode())<=24576,'receipt bound');n=strict_json(s);need(type(n)is dict and set(n)==FIELDS,'native fields')
 need(n['schema']=='do-usb-owned-claim-diagnostic-v1'and type(n['device'])is int and n['device']==58 and type(n['interface'])is int and n['interface']==2,'schema/fixed instance')
 for k in ['vendorHeaders','vendorBulkTransfers','vendorControlTransfers','claimReturn','claimErrno','releaseReturn','releaseErrno','closeReturn','closeErrno']:need(type(n[k])is int and n[k]==0,'zero count/result '+k)
 for k in ['opened','claimed','released','closed','accepted']:need(n[k]is True,'lifecycle '+k)
 for k in ['driverPolicyEstablished','physicalPictureObserved']:need(n[k]is False,'unsupported claim '+k)
 need(n['errors']==[],'lifecycle errors');snapshot(n['preDriver']);snapshot(n['postDriver']);driver(n['preKernelDriver']);driver(n['postKernelDriver']);status(n['preFd'],True);status(n['postFd'],True)
 need(n['preDriver']['afterUs']<=n['postDriver']['beforeUs']and n['postDriver']['afterUs']-n['preDriver']['beforeUs']<=15_000_000,'diagnostic ordering/deadline')
 p=n['preDriver']['managed'];need(p['linkTarget']=={'ok':True,'value':None,'error':None}and p['directoryExists']=={'ok':True,'value':'False','error':None}and p['fileExists']=={'ok':True,'value':'False','error':None},'unbound precondition')
 return n
if __name__=='__main__':
 import sys
 from pathlib import Path
 n=parse_native(Path(sys.argv[1]).read_text());print(json.dumps({'accepted':True,'driverPolicyEstablished':False,'pre':n['preDriver'],'post':n['postDriver'],'kernelPre':n['preKernelDriver'],'kernelPost':n['postKernelDriver']}))
