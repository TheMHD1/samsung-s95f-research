#!/usr/bin/env python3
"""Independent EB fixed package and synthetic gate-decoder checks, no target I/O."""
from pathlib import Path
import base64,copy,hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent.parent;B=D.parent;checks=0
PINS={'deployment-manifest.json':'e7df47861e25aca4df6fc18e82b646a53eada192451b9b16383c5b31a9f44a11','run-once.py':'886bdc05bb8eb5a255443f95a964f2bae947fc758b18ea0e4893f42c3e4ad9a8','parse-result.py':'e44f4c96989f895ec8ce8d1f72c9a1d8c1423a28cc1ec5358a885bd9f38d4523','source-inventory.json':'271061f8c60ee75f219b56217ac6dfcf3aa13616d67c3d4f54e46f655c13bdec','host-build-checkpoint.json':'03d21901ed7fe187791f4e116c9ec34a0c7d9df791b9affc4cb8af21dcc30e31','bin/Release/net6.0/RecordCapture.dll':'c9a9f6cddffd90e0771b2cc95d389365a9d58d11b4bfc57776b850956cfc4d3d'}
def need(ok,why):
 global checks
 checks+=1
 if not ok:raise ValueError(why)
def sha(b):return hashlib.sha256(b).hexdigest()
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def reject(fn):
 try:fn()
 except (ValueError,KeyError,TypeError):need(True,'rejected');return
 raise ValueError('negative unexpectedly accepted')
for name,pin in PINS.items():need(sha((D/name).read_bytes())==pin,'frozen '+name)
inv=json.loads((D/'source-inventory.json').read_text());need(len(inv['files'])==30,'30 frozen files')
for f in inv['files']:
 b=(D/f['path']).read_bytes();need(len(b)==f['bytes']and sha(b)==f['sha256'],'frozen inventory '+f['path'])
p=load(D/'parse-result.py','eb_independent_parser');w=load(D/'run-once.py','eb_independent_wrapper');man,payload=w.build_manifest()
need(w.manifest_bytes(man)==(D/'deployment-manifest.json').read_bytes(),'exact regenerated manifest')
need(set(payload)=={'RecordCapture.dll','RecordCapture.deps.json','RecordCapture.runtimeconfig.json'}and sum(map(len,payload.values()))==56459,'three fixed staged payloads')
need(man['nativeInvocations']==1 and man['retries']==man['wrapperUiOperations']==man['recoveryOperations']==0,'one shot no UI/recovery/retry')
parent=load(B/'rtp-fixed-reference-capture-20261028dt/parse-result.py','eb_parent_dt')
need([s for s in p.SPECS if s[0]not in ('primary-lane-gate','secondary-lane-gate')]==parent.SPECS,'unchanged14 DT windows')
need(p.SPECS[10:12]==[('primary-lane-gate',0x47010470,136),('secondary-lane-gate',0x4700cb94,68)],'new order/addresses/lengths')
need(sum(s[2]for s in p.SPECS)==1608,'fixed retained raw byte sum')
for name,address,length in p.SPECS:need(0x47000000<=address<address+length<=0x47020000 and len(struct.pack('<III',0x101,address,length))==12,'complete fixed wire interval')
need((D/'NativeBinding.cs').read_bytes()==(B/'rtp-fixed-reference-capture-20261028dt/NativeBinding.cs').read_bytes(),'native binding exact DT')
new=(D/'Program.cs').read_text();old=(B/'rtp-fixed-reference-capture-20261028dt/Program.cs').read_text()
def block(s):return s[s.index(' sealed class Controller'):s.index(' static Outcome Run')]
need(block(new)==block(old),'exact DT controller')
fixture=json.loads((D/'fixture.json').read_text());n,raws,i=p.parse_native(json.dumps(fixture));need(len(raws)==16 and i['localEligibilityOnly']is True and i['actualComparatorCallProven']is False,'accepted narrow16-window fixture')
for claim in ('historicalGateExecutionProven','gateBodyLiveFingerprinted','lanePhysicalMappingProven','atomicSnapshot','recordEpochProven','actualFixedABranchProven','physicalPictureObserved'):need(i[claim]is False,'narrow '+claim)
def raw(f,name):return bytearray(base64.b64decode(next(x for x in f['windows']if x['name']==name)['base64']))
def put(f,name,b):
 row=next(x for x in f['windows']if x['name']==name);row['base64']=base64.b64encode(b).decode();row['sha256']=sha(b)
# Exercise all68 indices with retained high bits, secondary extremes and source SB contexts.
for aa in (0,1,2,65535):
 for ac in (0,1,2,65535):
  for cc in (0,1,255):
   f=copy.deepcopy(fixture);m=raw(f,'M');struct.pack_into('<HH',m,10,aa,ac);m[44]=cc;put(f,'M',m)
   primary=[(0,1,2,3,0x100,0x101,0xfffe,0xffff)[k%8]for k in range(68)];secondary=bytes((0,1,255)[k%3]for k in range(68))
   put(f,'primary-lane-gate',struct.pack('<68H',*primary));put(f,'secondary-lane-gate',secondary)
   _,_,q=p.parse_native(json.dumps(f));need(len(q['laneGateSamples'])==68 and q['sourceContext']['aa']==aa and q['sourceContext']['ac']==ac and q['sourceContext']['secondaryOverrideByte4cc']==cc,'all retained source context')
   for k,row in enumerate(q['laneGateSamples']):
    expected=primary[k]%2==0 and (secondary[k]==0 or ((aa==1 or ac==1)and cc>0))
    need(row=={'lane':568+k,'primaryHalfword':primary[k],'primaryLowBit':primary[k]%2,'secondaryByte':secondary[k],'secondaryOverrideSB':(aa==1 or ac==1)and cc>0,'locallyAdmittedByCapturedTables':expected},'independent full halfword/byte decode and local formula')
for mode in range(6):
 f=copy.deepcopy(fixture);b=raw(f,'start-R');struct.pack_into('<H',b,16,mode);put(f,'start-R',b);need(p.parse_native(json.dumps(f))[2]['sourceContext']['operatingMode']==mode,'mode<6 is not category1')
for mode in (6,65535):
 f=copy.deepcopy(fixture);b=raw(f,'start-R');struct.pack_into('<H',b,16,mode);put(f,'start-R',b);reject(lambda:p.parse_native(json.dumps(f)))
for name,offset in [('M',64),('M',6),('M',8),('M',32),('C',0),('C',2),('C',4)]:
 f=copy.deepcopy(fixture);b=raw(f,name);b[offset]^=1;put(f,name,b);reject(lambda:p.parse_native(json.dumps(f)))
for name in ('primary-lane-gate','secondary-lane-gate'):
 for delta in (-1,1):
  f=copy.deepcopy(fixture);b=raw(f,name);b=b[:-1]if delta<0 else b+b'\0';put(f,name,b);reject(lambda:p.parse_native(json.dumps(f)))
for k in range(32):
 f=copy.deepcopy(fixture);f['steps'][k]['count']-=1;reject(lambda:p.parse_native(json.dumps(f)))
 f=copy.deepcopy(fixture);f['steps'][k]['after']='Unknown';reject(lambda:p.parse_native(json.dumps(f)))
for k in range(16):
 f=copy.deepcopy(fixture);f['windows'][k]['address']+=2;reject(lambda:p.parse_native(json.dumps(f)))
f=copy.deepcopy(fixture);f['windows'][10],f['windows'][11]=f['windows'][11],f['windows'][10];reject(lambda:p.parse_native(json.dumps(f)))
f=copy.deepcopy(fixture);f['bindingChecks'][2]['follow']['inode']+=1;reject(lambda:p.parse_native(json.dumps(f)))
need(len((D/'fixture.json').read_bytes())<=24576,'frozen fake receipt extent')
print(json.dumps({'accepted':True,'checks':checks,'inventoryFiles':30,'manifestSha256':sha(w.manifest_bytes(man)),'syntheticDecoderContexts':48,'syntheticLaneRowsChecked':3264,'rawBytes':1608,'payloadBytes':56459,'targetRootNetworkOperations':0,'localEligibilityOnly':True,'actualComparatorCallProven':False}))
