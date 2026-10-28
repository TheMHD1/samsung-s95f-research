#!/usr/bin/env python3
"""Host-only retained-source byte checks; no target operations."""
from pathlib import Path
import hashlib,json,struct
P=Path(__file__).resolve().parent;B=P.parent
q=B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin'
def sha(b):return hashlib.sha256(b).hexdigest()
def need(b,s):
 if not b:raise ValueError(s)
b=q.read_bytes();need(sha(b)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','package identity');im=b[0x40200:0x60200]
anchors={}
for name,va,h in [('ordinal_bound',0xc5fe,'9449098888426bd8'),('separate_capacity',0xc64c,'b0f5007f2bd2'),('array0',0xc662,'05f5805020f81210'),('array1',0xc672,'05f5a05020f81180'),('array2',0xc682,'05f5c05020f81190'),('array3',0xc692,'05f5e05020f81170'),('array4',0xc6a2,'05f5005020f811a0'),('count_after_bound_bypass',0xc6de,'13e0')]:
 x=bytes.fromhex(h);need(im[va:va+len(x)]==x,name);anchors[name]={'image':1,'address':hex(va),'address_domain':'selected-image1-linked-code','file_offset':hex(va+0x40200),'bytes':x.hex(),'sha256':sha(x)}
need(struct.unpack_from('<I',im,0xc850)[0]==0x200004ca,'formatter bound mirror literal')
header=bytes.fromhex('02010000c424014702000000');need(struct.unpack('<III',header)==(0x102,0x470124c4,2),'fixed target/address/length');need(201<512,'capacity')
refs=['volatile-logger-qualification-20261027f/reviewed-helper/Program.cs','firmware-rtp-producer-20261028df/capture/Program.cs','onset-trial-20261028cb/operand-analysis/prevention-experiment-readiness.md','autonomous-fault-harness-20261028dh/menu-onset-01/controller-capture/retained-00-trigger_baseline-cycle001-00-R.bin']
print(json.dumps({'schema':'dj-source-byte-qualification-v1','target_operations':0,'package_sha256':sha(b),'anchors':anchors,'five_array_u16_capacity':512,'limit200_permitted_indices':[0,200],'permitted_entry_count':201,'electrical_safety_proven':False,'running_code_fully_attested':False,'retained_inputs':[{'path':r,'sha256':sha((B/r).read_bytes()),'bytes':len((B/r).read_bytes())}for r in refs]},indent=2))
