#!/usr/bin/env python3
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parent.parent
P=R/'overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin'
SHA='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0'
# Stored-file ranges; linked VA = file - 0x200.
S={'f7_dispatch':(0x1eee4,0x1efc6,'bdf186399bea803b7ec43d700238ad147607d89e43f56233ba1bc3a9edb2917e'),'sample':(0x1fcb0,0x1fd42,'53dbe8995e8a470fb77846aa0ebdaf2cdce4335637f3d8f2f16d3ea684153a3b'),'rt_action':(0x1fe8c,0x1fef0,'12aa6be9eca0380b00f67cf1e41a39de41e2f3e2648506287867fc4b91ce2e49')}
b=P.read_bytes()
if len(b)!=0x500000 or hashlib.sha256(b).hexdigest()!=SHA: raise SystemExit('profile mismatch')
o={}
for n,(a,z,w) in S.items():
 g=hashlib.sha256(b[a:z]).hexdigest()
 if g!=w: raise SystemExit(n+' mismatch')
 o[n]={'file':hex(a),'va':hex(a-0x200),'sha256':g}
print(json.dumps({'profile_sha256':SHA,'address_rule':'VA=FILE-0x200','slices':o},indent=2,sort_keys=True))
