#!/usr/bin/env python3
from pathlib import Path
import json,struct
from inspect_archive import parse
P=Path(__file__).resolve().parent
prefix=Path('${S95F_EVIDENCE_ROOT}/panel-idle-20261026/overnight/samsung-official-T-RSMFAKUC-0090-msd-prefix.bin').read_bytes()
size=1493538434
base=parse(prefix,size)
variants=[('truncated',prefix[:25],size),('magic',b'X'+prefix[1:],size),('member-end',prefix,size-1)]
for name,offset,value,fmt in [('excess-count',18,0xffffffff,'<I'),('payload-gap',46,base['sections'][1]['offset']+1,'<Q'),('zero-payload-size',34,0,'<Q'),('header-count',202,0,'<I')]:
 b=bytearray(prefix);struct.pack_into(fmt,b,offset,value);variants.append((name,b,size))
for name,offset in [('encrypted-header-crc',238),('header-marker',242),('header-ciphertext',258)]:
 b=bytearray(prefix);b[offset]^=1;variants.append((name,b,size))
rejected=[]
for name,data,length in variants:
 try:parse(data,length)
 except (ValueError,struct.error,UnicodeDecodeError):rejected.append(name)
 else:raise RuntimeError('malformed input accepted: '+name)
output={'host_only':True,'retained_prefix_pass':True,'malformed_rejections':rejected,'target_calls':0,'signature_validation':False}
print(json.dumps(output,sort_keys=True,indent=2))
