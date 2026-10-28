import hashlib
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import uuid
import platform_partitions as p

SMALL=4*1024*1024
PROFILE=[('pltf_t.img',1048576,524288),('prd_t.img',1572864,524288)]
def image():
    raw=bytearray(SMALL);raw[510:512]=b'\x55\xaa';raw[450]=0xee;struct.pack_into('<II',raw,454,1,SMALL//512-1)
    table=bytearray(16384)
    for i,(name,offset,size) in enumerate(PROFILE):
        e=bytearray(128);e[:16]=uuid.UUID(p.LINUX_GUID).bytes_le;e[16:32]=uuid.UUID(int=i+1).bytes_le;struct.pack_into('<QQQ',e,32,offset//512,(offset+size)//512-1,0);data=name.encode('utf-16-le');e[56:56+len(data)]=data;table[i*128:(i+1)*128]=e
    total=SMALL//512
    for current,other,array in [(1,total-1,2),(total-1,1,total-33)]:
        h=bytearray(struct.pack('<8sIIIIQQQQ16sQIII',b'EFI PART',0x10000,92,0,0,current,other,34,total-34,uuid.UUID(int=3).bytes_le,array,128,128,p.crc(table)))
        struct.pack_into('<I',h,16,p.crc(h));raw[current*512:current*512+92]=h;raw[array*512:array*512+16384]=table
    raw[1048576:1048576+17]=b'VDFS2007synthetic'
    return raw

def accepted(sha,**updates):
    row=dict(section=1001,name='platform.img',bytes=SMALL,sha256=sha,ciphertext_rsa_verified=True,strict_padding_validated=True,original_crc_validated=True,installed=False);row.update(updates)
    return json.dumps({'schema':'s95f-private-firmware-extraction-v1','items':[row]}).encode()

class Tests(unittest.TestCase):
    def test_primary(self):
        h,rows=p.primary(image()[:1048576],SMALL);self.assertEqual([(r['name'],r['offset'],r['bytes']) for r in rows],PROFILE)
    def test_header_crc(self):
        raw=image();raw[560]^=1
        with self.assertRaisesRegex(ValueError,'header CRC'):p.primary(raw[:1048576],SMALL)
    def test_entry_crc(self):
        raw=image();raw[1080]^=1
        with self.assertRaisesRegex(ValueError,'entry CRC'):p.primary(raw[:1048576],SMALL)
    def test_mbr(self):
        raw=image();raw[450]=0x83
        with self.assertRaises(ValueError):p.primary(raw[:1048576],SMALL)
    def test_prefix_truncation(self):
        with self.assertRaises(ValueError):p.primary(image()[:17000],SMALL)
    def test_overlap_with_valid_crc(self):
        raw=image();struct.pack_into('<QQ',raw,1024+128+32,2048,3071);table=raw[1024:17408];struct.pack_into('<I',raw,512+88,p.crc(table));struct.pack_into('<I',raw,512+16,0);struct.pack_into('<I',raw,512+16,p.crc(raw[512:604]))
        with self.assertRaisesRegex(ValueError,'partition overlap'):p.primary(raw[:1048576],SMALL)
    def test_complete_backup(self):
        with tempfile.TemporaryFile() as f:
            f.write(image());f.flush();self.assertEqual(len(p.complete_gpt(f.fileno(),SMALL)['partitions']),2)
    def test_backup_mismatch(self):
        raw=image();raw[-512+56]^=1;struct.pack_into('<I',raw,len(raw)-512+16,0);struct.pack_into('<I',raw,len(raw)-512+16,p.crc(raw[-512:-512+92]))
        with tempfile.TemporaryFile() as f:
            f.write(raw);f.flush()
            with self.assertRaisesRegex(ValueError,'header mismatch'):p.complete_gpt(f.fileno(),SMALL)
    def test_acceptance_requires_all_gates(self):
        for change in [{'strict_padding_validated':False},{'ciphertext_rsa_verified':False},{'original_crc_validated':1},{'installed':True}]:
            raw=accepted('0'*64,**change)
            with patch.object(p,'EXPECTED_BYTES',SMALL):
                with self.assertRaises(ValueError):p.accepted_record(raw,hashlib.sha256(raw).hexdigest())
    def test_duplicate_inventory_key(self):
        raw=b'{"schema":"s95f-private-firmware-extraction-v1","schema":"other","items":[]}'
        with self.assertRaises(ValueError):p.accepted_record(raw,hashlib.sha256(raw).hexdigest())
    def test_synthetic_extract(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent=Path(tmp);source=parent/'platform.img';source.write_bytes(image());source.chmod(0o600);inv=parent/'inventory.json';raw=accepted(hashlib.sha256(source.read_bytes()).hexdigest());inv.write_bytes(raw)
            out=parent/'partitions'
            with patch.multiple(p,IMAGE=source,INVENTORY=inv,OUTPUT=out,EXPECTED_BYTES=SMALL,PROFILE=PROFILE):
                result=p.extract(hashlib.sha256(raw).hexdigest());self.assertEqual(len(result['partitions']),2)
                for name,offset,size in PROFILE:
                    self.assertEqual((out/name).read_bytes(),source.read_bytes()[offset:offset+size]);self.assertEqual((out/name).stat().st_mode&0o777,0o600)
                with self.assertRaisesRegex(ValueError,'fresh output'):p.extract(hashlib.sha256(raw).hexdigest())
    def test_actual_provisional_primary(self):
        h,rows=p.primary((p.HERE/'private/prefix-00000000-00100000.bin').read_bytes());self.assertEqual([(r['name'],r['offset'],r['bytes']) for r in rows],p.PROFILE);self.assertEqual(h['header_crc32'],0x7c23616a);self.assertEqual(h['entry_crc32'],0xeb9c31ce)

if __name__=='__main__':unittest.main()
