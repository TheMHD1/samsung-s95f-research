#!/usr/bin/env python3
"""Bounded selected-image scan writer and actual FE sample check; host only."""
import hashlib,json,struct
from pathlib import Path
P=Path(__file__).resolve().parent;B=P.parent
asset=B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin';raw=asset.read_bytes();check=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(v,s):
 global check
 if not v:raise ValueError(s)
 check+=1
need(sha(raw)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','selected image identity')
anchors={0xc252:"f7f74ffb",0xc258:"f7f750fb",0xc25c:"0446",0xc25e:'4ff41050',0xc262:'005b',0xc264:'38b9',0xc266:'42f20e40',0xc26a:'005b',0xc26c:'0128',0xc26e:'02d1',0xc270:'1e49',0xc272:'0870',0xc276:'0020',0xc278:'1c49',0xc27a:'0870',0xc2ec:'d8040020',0xc1f0:'0153',0xc1f8:'0153',0xc200:'0153'}
for a,h in anchors.items():need(raw[a+0x40200:a+0x40200+len(bytes.fromhex(h))]==bytes.fromhex(h),'instruction anchor '+hex(a))
for a,disp in [(0xc270,0x78),(0xc278,0x70)]:need(((a+4)&~3)+disp==0xc2ec,'literal target')
for stop in [0,1,2,65535]:
 for gate in [0,1,2,65535]:need(int(stop==0 and gate==1)in [0,1],'finite source result')
cap=B/'wake-qualified-onset-trial-20261028fe/capture-01';inputs=[];samples=[]
for role,prefix,ri,mi,ci in [('baseline','retained-00-trigger_baseline-cycle001',0,1,2),('fault','retained-02-post_fault-cycle046',6,0,1)]:
 names=[f'{prefix}-{ri:02d}-R.bin',f'{prefix}-{mi:02d}-M.bin',f'{prefix}-{ci:02d}-C.bin'];values=[]
 for name in names:
  path=cap/name;b=path.read_bytes();inputs.append({'path':str(path.relative_to(B)),'bytes':len(b),'sha256':sha(b)});values.append(b)
 r,m,c=values;need(len(r)==256 and len(m)==68 and len(c)==16,'sample sizes');need(struct.unpack_from('<I',m,64)[0]==0x20010000 and struct.unpack_from('<HH',m,10)==(0,2),'sample root/category');need(m[56]==(1 if role=='baseline'else 0),'observed scan');samples.append({'role':role,'rt':[struct.unpack_from('<H',r,o)[0]for o in [0,10,14]],'scan':m[56],'aa':0,'ac':2,'root':0x20010000})
print(json.dumps({'schema':'fn-scan-qualification-v1','checks':check,'sourceAssetSha256':sha(raw),'sourceMapping':'image1 VA +0x40200 = selected file offset','sourceRange':[0xc250,0xc2f0],'sourceByteSha256':sha(raw[0xc250+0x40200:0xc2f0+0x40200]),'anchors':[{'va':a,'fileOffset':a+0x40200,'bytesSha256':sha(bytes.fromhex(h))}for a,h in anchors.items()],'sourceSemantics':'c250 stores1 iff its sampled stop==0 and ordinarygate==1, else0; separate scheduling is not atomic with host reads','admission':'prearm and first complete clean baseline scan1; later observations and fresh cleanup finite scan0or1, never other values','actualInputs':inputs,'actualSamples':samples,'targetOperations':0},sort_keys=True))
