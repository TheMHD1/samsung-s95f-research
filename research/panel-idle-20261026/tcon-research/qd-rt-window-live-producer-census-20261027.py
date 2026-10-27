#!/usr/bin/env python3
"""Hash-gated, bounded image-0 RT-window producer census."""
import hashlib
from pathlib import Path

P=Path('${S95F_EVIDENCE_ROOT}/panel-idle-20261026/overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin')
H='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0'
def need(x,m):
 if not x: raise ValueError(m)
b=P.read_bytes(); need(hashlib.sha256(b).hexdigest()==H,'source hash')
i=b[:0x40000]
need([n for n in range(len(i)) if i.startswith((0x47010000).to_bytes(4,'little'),n)]==[0xf198,0x3ce50,0x3e3d4],'fixed-root literal census')
# Canonical image-0 VA=stored-file offset minus 0x200.  The accessor returns
# the word at stored 0xf198; the live checker calls it then forms +0x240a.
need(i[0xf194:0xf19a]==bytes.fromhex('004870470000'),'root accessor bytes')
need(i[0x216d4:0x216f4]==bytes.fromhex('10b5edf75dfd044642f20a40005d00f0010030b10aa0dff73ff80d491020eaf7'),'live reader bytes')
# Known non-live producers are configuration/reset block destinations, not
# individual direct stores.  The retained table checker establishes both.
need(int.from_bytes(i[0x3ce50:0x3ce54],'little')==0x47010000,'AP_RTP second destination')
need(int.from_bytes(i[0x3e3d4:0x3e3d8],'little')==0x47010000,'reset scatter destination')
# Exhaustive halfword-aligned Thumb-2 BL census in the image-0 file region.
def sx(v,n): return v-(1<<n) if v&(1<<(n-1)) else v
calls=[]
for f in range(0x200,len(i)-3,2):
 a=int.from_bytes(i[f:f+2],'little'); c=int.from_bytes(i[f+2:f+4],'little')
 if a&0xf800==0xf000 and c&0xd000==0xd000 and c&0x1000:
  s=(a>>10)&1; j1=(c>>13)&1; j2=(c>>11)&1; q1=1^(j1^s); q2=1^(j2^s)
  off=sx((s<<24)|(q1<<23)|(q2<<22)|((a&0x3ff)<<12)|((c&0x7ff)<<1),25)
  if ((f-0x200+4+off)&0xffffffff)==0xef94: calls.append(f-0x200)
need(len(calls)==91,'accessor direct-call count')
need(calls.count(0x214d6)==1,'live-reader accessor caller')
# The sole direct immediate construction of +0x240a is in that caller and its
# next use is LDRB, not STR*.  Computed-offset/opaque-copy paths remain out.
pat=bytes.fromhex('42f20a40005d')
need([n for n in range(len(i)) if i.startswith(pat,n)]==[0x216dc],'240a immediate load pattern')
print('PASS accessor_calls=91; direct +240a constructor=VA214dc load-only')
