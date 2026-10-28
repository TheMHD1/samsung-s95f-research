#!/usr/bin/env python3
"""Host-only selected-package and prior W byte checks."""
from pathlib import Path
import hashlib,json,struct
P=Path(__file__).resolve().parent;B=P.parents[1]
def need(b,s):
 if not b:raise ValueError(s)
def sha(b):return hashlib.sha256(b).hexdigest()
pkg=(B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes();need(sha(pkg)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','package pin')
source=json.loads((P/'source-anchors.json').read_text())
for r in source['ranges']:
 start=int(r['file_offset'],16);n=int(r['end_exclusive'],16)-int(r['VA'],16);need(sha(pkg[start:start+n])==r['sha256'],r['name'])
init=pkg[0x182200:0x182200+826];need(sha(init)=='c50e438b4882c04e62542fa718cda662b56c3ea0930e20d54944a949e2e3afbf','packaged initializer')
wpath=B/'ap-exco-input-snapshot-20261027w/capture-once/ordinary-ap-exco-prefix.bin';w=wpath.read_bytes();need(len(w)==824 and sha(w)=='0f7884892da5714a9adcb97cdc033c4d5b24201b1ac570dabcc6771c01a7e271','W ordinary pin')
fields={'ca':0xca,'cc':0xcc,'ce':0xce,'debounce_e0':0xe0,'e6':0xe6,'enable_2cc':0x2cc,'mask_2ce':0x2ce,'AG_bound0':0x2d0,'AP_code0':0x2d2,'AG_bound1':0x2d4,'AP_code1':0x2d6,'value_2fc':0x2fc,'counter_300':0x300,'counter_302':0x302}
read=lambda b:{k:struct.unpack_from('<H',b,i)[0]for k,i in fields.items()}
a,z=read(init),read(w);need([a[k]for k in ['ca','cc','ce','debounce_e0','enable_2cc','mask_2ce']]==[1,1,0,30,1,2],'initializer control fields');need(all(a[k]==z[k] for k in ['enable_2cc','mask_2ce','AG_bound0','AP_code0','AG_bound1','AP_code1']),'W agrees disabled bit0');need(z['e6']==1 and z['value_2fc']==0,'W first-only selector condition')
print(json.dumps({'schema':'df-upstream-byte-verification-v1','target_operations':0,'package_sha256':sha(pkg),'source_function_ranges_verified':len(source['ranges']),'initializer':{'file_offset':'0x182200','bytes':826,'sha256':sha(init),'fields':a},'W_ordinary':{'path':str(wpath.relative_to(B)),'bytes':len(w),'sha256':sha(w),'fields':z},'bit0_frame_branch_enabled_in_both':False,'W_is_DH_contemporaneous':False,'running_code_fully_attested':False},indent=2))
