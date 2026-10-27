#!/usr/bin/env python3
"""Read the known uImage slot, verify legacy header+payload CRC, never write TV storage."""
from pathlib import Path
import base64,hashlib,json,struct,subprocess,zlib
B=Path(__file__).resolve().parent
A=B.parents[1]/'root-access/s95f-access.py'
REMOTE='/dev/mmcblk0p6'
def root(cmd):
 r=subprocess.run(['python3',str(A),'root','--timeout','25','--command',cmd],capture_output=True,text=True,timeout=50,check=True)
 c=json.loads(r.stdout)['commands'][0]
 if c['exit_code'] or c['timed_out']:raise RuntimeError('Remote read failed')
 return c['stdout']
h=(B/'kernel-pair-header.bin').read_bytes()[:64]
magic,hcrc,stamp,size,load,entry,dcrc=struct.unpack('>7I',h[:28])
assert magic==0x27051956 and 0<size<20*1024*1024
hh=bytearray(h);hh[4:8]=bytes(4)
assert zlib.crc32(hh)==hcrc
n=size+64;chunks=[]
for i in range((n+131071)//131072):
 data=base64.b64decode(root(f'dd if={REMOTE} bs=131072 skip={i} count=1 2>/dev/null | base64'))
 if len(data)!=131072:raise RuntimeError('Short block')
 chunks.append(data)
 if i%16==0:print('copied chunk',i,flush=True)
data=b''.join(chunks)[:n]
assert len(data)==n and data[:64]==h and zlib.crc32(data[64:])==dcrc
(B/'kernel-uImage.bin').write_bytes(data)
(B/'kernel-Image.bin').write_bytes(data[64:])
manifest={'remote':REMOTE,'partition_name':'uImage','named_symlink_points_other_zero_header_slot':True,'total_size':n,'payload_size':size,'sha256':hashlib.sha256(data).hexdigest(),'payload_sha256':hashlib.sha256(data[64:]).hexdigest(),'header_crc_valid':True,'payload_crc_valid':True,'uimage_name':h[32:64].split(bytes(1))[0].decode(),'load':hex(load),'entry':hex(entry),'read_only':True,'running_build':'T-RSMFAKUC-0090-REL-202607141953','running_kernel':'5.4.261','qualification':'Header/version and paired active root slot agree; no running-text hash comparison yet.'}
(B/'kernel-image-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest),flush=True)
