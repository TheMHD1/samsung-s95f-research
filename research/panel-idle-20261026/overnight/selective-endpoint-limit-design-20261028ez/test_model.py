#!/usr/bin/env python3
"""Pure selective-endpoint model/source audit. No target or native binding."""
from pathlib import Path
import hashlib,importlib.util,json,struct
D=Path(__file__).resolve().parent;B=D.parent
checks=0
def check(v,s):
 global checks
 checks+=1
 if not v:raise ValueError(s)
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=load(D/'profile_model.py','ez_model');dv=load(B/'volatile-limit-dynamic-profile-20261028dv/parse-result.py','old_dv')
pins=json.loads((D/'input-pins.json').read_bytes())
for row in pins['files']:
 raw=(B/row['path']).read_bytes();check(len(raw)==row['bytes']and hashlib.sha256(raw).hexdigest()==row['sha256'],'input '+row['path'])
package=(B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes();proof=json.loads((B/'volatile-limit-dynamic-profile-20261028dv/model-source-proof.json').read_bytes())
for row in proof['sourceRanges']:
 a=int(row['fileOffset'],16);check(hashlib.sha256(package[a:a+row['bytes']]).hexdigest()==row['sha256'],'exact selected source '+row['va'])
# Whole function hash pins the instruction identity; exact two opcodes select r8.
check(package[0x200+0x38a3c:0x200+0x38a40].hex()=='b8f57a6f','CMP.W r8,#4000, not sl')
check(package[0x200+0x38a42:0x200+0x38a46].hex()=='4ff01908','MOV.W r8,#25, not sl')
by={}
for t in range(4096):
 v=m.endpoint(2075,24,t,15,195,3000,3800)['endpoint'];by.setdefault(v,[]).append(t);check(v in m.ALTERNATE_ENDPOINT_IMAGE,'source preimage admitted')
check(len(by)==72 and set(by)==m.ALTERNATE_ENDPOINT_IMAGE,'exact72finiteimage')
check(by[3138]==[23]and by[3161]==[24],'EX unique preimages')
for v in range(65536):check((v in m.ALTERNATE_ENDPOINT_IMAGE)==(v in by),'fullu16membershipiffsourcepreimage')
check(3200 not in by and 3139 not in by and 3000 in by and 3800 in by,'inrangegaps are not wildcard')
check(m.scaled_temperature(65535)==4095 and m.scaled_reference(65535)==25,'fallback reference only')
e=B/'limit-rechallenge-trial-20261028ex/preparation-01/baseline';r=(e/'start-R.bin').read_bytes();mm=(e/'M.bin').read_bytes();c=(e/'C.bin').read_bytes()
oldrefused=False
try:dv.guard_r(r,40)
except ValueError as err:oldrefused=str(err)=='source-model endpoint alternate'
check(oldrefused,'old DV refusal preserved')
m.validate_candidate_r(r,40,dv.PROFILE);m.validate_candidate_context(mm,c,r);m.validate_transaction_pair(r,(e/'end-R.bin').read_bytes(),40,40,dv.PROFILE);check(True,'actual EX R/context/pair admitted')
new=bytearray(r);new[0xc4:0xc6]=(200).to_bytes(2,'little');m.validate_transaction_pair(r,bytes(new),40,200,dv.PROFILE);check(True,'synthetic fixed-only action pair admitted')
for offset,value in [(0xbc,3200),(0xbc,3139),(0x20,3138),(0x98,4096),(0x96,25),(0xb6,16),(0,1),(0x0e,0),(6,1)]:
 x=bytearray(r);x[offset:offset+2]=value.to_bytes(2,'little');refused=False
 try:m.validate_candidate_r(bytes(x),40,dv.PROFILE)
 except ValueError:refused=True
 check(refused,'wrongprofile/fault/model refused '+str(offset))
for offset,value in [(0xbc,3161),(0x98,25)]:
 x=bytearray(r);x[offset:offset+2]=value.to_bytes(2,'little');refused=False
 try:m.validate_transaction_pair(r,bytes(x),40,40,dv.PROFILE)
 except ValueError:refused=True
 check(refused,'fresh endpoint/temperature drift refused')
x=bytearray(mm);x[12:14]=(1).to_bytes(2,'little');refused=False
try:m.validate_candidate_context(bytes(x),c,r)
except ValueError:refused=True
check(refused,'mode6 stillrefuses')
values=sorted(by);packed=b''.join(struct.pack('<H',v)for v in values)
print(json.dumps(dict(schema='ez-selective-endpoint-model-validation-v1',checksPassed=checks,inputFiles=len(pins['files']),alternateImage=values,alternateImageCardinality=72,alternateImageSha256=hashlib.sha256(packed).hexdigest(),currentTemperatureDomain=[0,4095],referenceFallbackAppliesTo='r8 reference, not sl current temperature',EXAdmitted=True,oldDVRefusalPreserved=True,arbitraryEndpointRange=False,targetOperations=0,rootCalls=0,networkOperations=0),sort_keys=True,indent=2))
