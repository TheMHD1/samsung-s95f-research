#!/usr/bin/env python3
"""Independent fixed FA review checks. Pure models/source/retained inputs only."""
from pathlib import Path
import base64,hashlib,json,re,struct,types,subprocess,sys
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent.parent;B=D.parent;P=B/'volatile-limit-dynamic-profile-20261028dv';E=B/'selective-endpoint-limit-design-20261028ez';checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(ok,label):
 global checks
 if not ok:raise ValueError(label)
 checks+=1
def reject(f):
 try:f()
 except(ValueError,TypeError,KeyError):need(True,'rejection');return
 raise ValueError('unexpected acceptance')
def load(p,n):
 m=types.ModuleType(n);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
def section(s,a,z):return s[s.index(a):s.index(z,s.index(a))]
model=load(E/'profile_model.py','independent_ez');p=load(D/'parse-result.py','independent_fa');old=load(P/'parse-result.py','independent_dv')
s=(D/'Program.cs').read_text();prev=(P/'Program.cs').read_text()
# Exact pure admission delta, preserving all native IO/binding/phase/cleanup code.
for a,z in [('    const int TimeoutMs','    sealed class Outcome'),('    static void GuardPair','    static byte[] ReadCachedDescriptors'),('    static byte[] ReadCachedDescriptors','    sealed class FakeClock')]:need(section(s,a,z)==section(prev,a,z),'unchanged '+a.strip())
need(section(s,'    static int Main','\n}')==section(prev,'    static int Main','\n}').replace('dv-','fa-'),'same fixed action Main')
need(section(s,'    [DllImport("libc.so.6",EntryPoint="open",SetLastError=true)] static extern int ReceiptOpen','    static int Main')==section(prev,'    [DllImport("libc.so.6",EntryPoint="open",SetLastError=true)] static extern int ReceiptOpen','    static int Main').replace('researcher-limit-dv-','researcher-limit-fa-'),'same exclusive receipt')
need(section(s,'    static bool DynamicR','    // Fixed exact image')==section(prev,'    static bool DynamicR','    static void GuardModel'),'same exclusions/uint arithmetic')
for a,z in [('def binding_checks(','def parse_native('),('def parse_native(',None)]:
 before=(P/'parse-result.py').read_text();after=(D/'parse-result.py').read_text();before=before[before.index(a):]if z is None else section(before,a,z);after=after[after.index(a):]if z is None else section(after,a,z);need(before.replace('dv-fixed-limit','fa-fixed-limit')==after,'same accepted receipt validation '+a)
# Independent arithmetic avoids using either model's endpoint implementation.
def endpoint(t):
 product=((2075+15*((t-24)&0xffffffff))*195)&0xffffffff
 v=(product>>7)&0xffff
 return 3800 if v>3800 else max(3000,v)
image=sorted({endpoint(t)for t in range(4096)});table=list(map(int,re.search(r'AlternateEndpointImage=\{([^}]+)\}',s).group(1).split(',')))
need(len(image)==72 and table==image and set(image)==p.ALTERNATE_ENDPOINT_IMAGE==model.ALTERNATE_ENDPOINT_IMAGE,'independent exact72 image equals native/parser/model')
need(sha(b''.join(struct.pack('<H',v)for v in image))=='a61417913462d9b4c45d39431dbf6b662c84238e4f3b6585ac24c75654eabc53','image digest')
need([t for t in range(4096)if endpoint(t)==3138]==[23],'EX alternate3138 unique priorT23')
need([t for t in range(4096)if endpoint(t)==3161]==[24],'EX ordinary3161 currentT24')
X=B/'limit-rechallenge-trial-20261028ex/preparation-01/baseline';r=(X/'start-R.bin').read_bytes();end=(X/'end-R.bin').read_bytes();m=(X/'M.bin').read_bytes();c=(X/'C.bin').read_bytes()
need(r==end,'actual EX stable pair');reject(lambda:old.guard_r(r,40));p.guard_r(r,40);p.validate_candidate_context(m,c,r);p.validate_transaction_pair(r,end,40,40,p.PROFILE);need(True,'actual EX model/context admitted without source edits')
for limit in (40,200):
 base=bytearray(r);struct.pack_into('<H',base,0xc4,limit);base=bytes(base)
 for value in image:
  x=bytearray(base);struct.pack_into('<H',x,0xbc,value);p.guard_r(bytes(x),limit);need(True,'each exact image value admitted at fixed action')
 for value in [0,500,2999,3002,3139,3200,3799,3801,4095,65535]:
  if value in image:continue
  x=bytearray(base);struct.pack_into('<H',x,0xbc,value);reject(lambda:p.guard_r(bytes(x),limit))
 for at,value in [(0x20,3138),(0x98,4096),(0x96,25),(0x94,2076),(0xb6,16),(0xb8,196),(0xba,3801),(0x2c,2999),(0,1),(0xe,0),(6,1),(0xac,255),(0xac,256),(0xca,2)]:
  x=bytearray(base);struct.pack_into('<H',x,at,value);reject(lambda:p.guard_r(bytes(x),limit))
 for at,value in [(0xbc,3161),(0x98,25)]:
  x=bytearray(base);struct.pack_into('<H',x,at,value);reject(lambda:p.validate_transaction_pair(base,bytes(x),limit,limit,p.PROFILE))
 # Alternative endpoint unchanged but bounded echo may vary; action is fixed.
 x=bytearray(base);struct.pack_into('<H',x,0xc4,200 if limit==40 else 40);struct.pack_into('<H',x,0xac,254);p.validate_transaction_pair(base,bytes(x),limit,200 if limit==40 else 40,p.PROFILE);need(True,'only fixed action with bounded echo change')
for offset,value in [(10,1),(12,1),(56,0),(38,3138)]:
 x=bytearray(m)
 if offset==56:x[offset]=value
 else:struct.pack_into('<H',x,offset,value)
 reject(lambda:p.validate_candidate_context(bytes(x),c,r))
# Confirm actual instruction identity and source fields, not comments alone.
asset=B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin';raw=asset.read_bytes();need(sha(raw)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','selected package pin')
for row in json.loads((D/'model-source-proof.json').read_text())['sourceRanges']:
 a=int(row['fileOffset'],16);need(sha(raw[a:a+row['bytes']])==row['sha256'],'machine source '+row['va'])
need(raw[0x38c3c:0x38c40].hex()=='b8f57a6f' and raw[0x38c42:0x38c46].hex()=='4ff01908','reference r8 fallback exact bytes')
need(struct.unpack_from('<f',raw,0x38aec+0x200)[0]==1/16,'literal power-of-two scale at image0 VA38aec')
proof={'schema':'fa-independent-review-checks-v1','checksPassed':checks,'allowedImageCount':72,'currentRange':[0,4095],'EXOrdinary':3161,'EXCurrentDiagnostic':24,'EXAlternate':3138,'EXAlternateUniquePreimage':23,'frozenDVRefusalPreserved':True,'nativeIOInvoked':False,'targetOperations':0,'rootCalls':0,'networkOperations':0}
print(json.dumps(proof,sort_keys=True))
