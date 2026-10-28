#!/usr/bin/env python3
"""Read-only independent DX package/manifest/sample/parser checks; no root imports."""
import base64,copy,hashlib,importlib.util,json,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent.parent;B=D.parent;checks=0
EXPECTED={'deployment-manifest.json':'c4d51611cf638f0ac4e9e3003c3b72ee592f460df19ed6138ce57ae7e6e92fac','run-once.py':'0ab205eb9204c14b049dacb1b936f4e263c1fa7a8b6c2c457e0e8c3d8a2199e0','parse-result.py':'70efd3096ec5b1cef37fabd74f3e6c3fb63ca72d847bd79500bdb31d74c9dd05','Program.cs':'885518cb0f3327c3b532ad542e2a97546daee9ee0586eb8f335a258086258b45','bin/Release/net6.0/CodeFingerprint.dll':'35967b789654aa9eca6eeeafb87196f655e84fc9bd208557be8a21d0446c387d','host-build-checkpoint.json':'e5afadc7c0a722f14062441c5ea5cd65abc56fd806bd9276e1d1f825eb175ab4','source-inventory.json':'9be78b2fcd8b8340b00fab5ba85008a63142acbaec121107b941dd64d564140f'}
def sha(b):return hashlib.sha256(b).hexdigest()
def need(ok,why):
 global checks
 checks+=1
 if not ok:raise ValueError(why)
def load(name,file):
 spec=importlib.util.spec_from_file_location(name,file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def reject(fn):
 try:fn()
 except (ValueError,TypeError,KeyError):need(True,'rejected');return
 raise ValueError('mutation unexpectedly accepted')
for name,pin in EXPECTED.items():need(sha((D/name).read_bytes())==pin,'final pin '+name)
inv=json.loads((D/'source-inventory.json').read_text());need(len(inv['files'])==21,'21 frozen files')
for f in inv['files']:
 b=(D/f['path']).read_bytes();need(len(b)==f['bytes'] and sha(b)==f['sha256'],'inventory '+f['path'])
p=load('dx_independent_parser',D/'parse-result.py');w=load('dx_independent_wrapper',D/'run-once.py')
manifest,payload=w.build_manifest();serialized=w.manifest_bytes(manifest)
need(serialized==(D/'deployment-manifest.json').read_bytes(),'exact regenerated manifest')
need(set(payload)=={'CodeFingerprint.dll','CodeFingerprint.deps.json','CodeFingerprint.runtimeconfig.json'} and sum(map(len,payload.values()))==52881,'exact staged three payload files/bytes')
need(manifest['nativeInvocations']==1 and manifest['retries']==manifest['writes']==manifest['wrapperUiOperations']==manifest['recoveryOperations']==0,'fixed no-write action surface')
need(manifest['rootTimeoutSeconds']==45 and manifest['hostTimeoutSeconds']==75 and manifest['rootResponseCap']==65536 and manifest['structuredReceiptCap']==24576,'deadline/framing bounds')
asset=(B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes();need(sha(asset)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','selected firmware')
plan=json.loads((B/'code-alias-qualification-20261028dw/fixed-read-plan.json').read_text())
fixture=json.loads((D/'fixture.json').read_text());native,raw,interpret=p.parse_native(json.dumps(fixture))
need(len(raw)==4 and sum(len(b)for _,b,_ in raw)==64 and interpret['sampledCodeMatch']is True,'exact sampled extent')
for i,win in enumerate(plan['windows']):
 address=int(win['busAddress'],16);va=int(win['linkedVa'],16);off=int(win['fileOffset'],16);data=asset[off:off+16]
 need(off==0x40200+va and address==0x46000000+va and 0<va and va+16<=0x20000 and address%4==0,'source image/bank/bounded interval')
 need(struct.pack('<III',0x101,address,16).hex()==win['headerLittleEndianHex'],'independent wire header')
 need(raw[i][1]==data and raw[i][2]==sha(data)==win['expectedSha256'],'source/fixture exact16B')
 # Substitute other bank at same VA while recomputing all self-declared hashes.
 for replacement in [asset[0x200+va:0x200+va+16],bytes(16),data[::-1]]:
  changed=copy.deepcopy(fixture);changed['windows'][i]['base64']=base64.b64encode(replacement).decode();changed['windows'][i]['sha256']=sha(replacement);reject(lambda:p.parse_native(json.dumps(changed)))
 # Keep hashes internally valid but relabel fixed address/name/claimed execution qualification.
 for key,value in [('address',address+0x1000000),('address',True),('bytes',True),('name',plan['windows'][(i+1)%4]['name'])]:
  changed=copy.deepcopy(fixture);changed['windows'][i][key]=value;reject(lambda:p.parse_native(json.dumps(changed)))
for key in ['wholeRunningImageAttested','executableWriteQualified','atomicSnapshot','physicalPictureObserved']:
 changed=copy.deepcopy(fixture);changed[key]=True;reject(lambda:p.parse_native(json.dumps(changed)))
for index in range(8):
 changed=copy.deepcopy(fixture);changed['steps'][index]['count']=None;reject(lambda:p.parse_native(json.dumps(changed)))
 changed=copy.deepcopy(fixture);changed['steps'][index]['afterUs']=changed['steps'][index]['beforeUs']-1;reject(lambda:p.parse_native(json.dumps(changed)))
for value in [True,0,128,-1]:
 changed=copy.deepcopy(fixture);changed['device']=value;reject(lambda:p.parse_native(json.dumps(changed)))
for field in ('inode','devMajor','devMinor'):
 changed=copy.deepcopy(fixture);changed['bindingChecks'][2]['follow'][field]+=1;reject(lambda:p.parse_native(json.dumps(changed)))
changed=copy.deepcopy(fixture);changed['bindingChecks'][2]['kernel']['interface']=1;reject(lambda:p.parse_native(json.dumps(changed)))
reject(lambda:p.parse_native(json.dumps(fixture).replace('"accepted": true','"accepted": true, "accepted": true',1)))
reject(lambda:p.parse_native(json.dumps(fixture)+'\n[GC_INFO] diagnostic'))
need(all(interpret[k]is False for k in ('wholeRunningImageAttested','activeInstructionFetchProven','executableWriteQualified','atomicSnapshot','physicalPictureObserved')),'interpretation narrow claims')
need((D/'NativeBinding.cs').read_bytes()==(B/'rtp-record-capture-20261028dm/NativeBinding.cs').read_bytes(),'binding byte-identical reviewed DM')
old=(B/'rtp-record-capture-20261028dm/Program.cs').read_text();new=(D/'Program.cs').read_text()
need(old[old.index(' sealed class Controller'):old.index(' static Outcome Run')]==new[new.index(' sealed class Controller'):new.index(' static Outcome Run')],'transport controller byte-identical reviewed DM')
print(json.dumps({'accepted':True,'checks':checks,'frozenInventoryFiles':21,'payloadBytes':sum(map(len,payload.values())),'manifestSha256':sha(serialized),'targetRootNetworkOperations':0,'sampledBytes':64,'wholeRunningImageAttested':False,'executableWriteQualified':False}))
