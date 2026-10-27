#!/usr/bin/env python3
"""Host-only fixed-input and operation validator. No target IO or library load."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import zlib

HERE = Path(__file__).resolve().parent
RESEARCH = HERE.parents[1]
PREFIX = RESEARCH.parent / 'panel-idle-20261026/overnight/samsung-official-T-RSMFAKUC-0090-msd-prefix.bin'
MANIFEST = json.loads((HERE / 'input-manifest.json').read_text())
ELFS = {
    'target-file-acquisition-02/libteec.so': '926840c9e7b26c59d8cb9d4ab5ae274e62b11efdbf14831b0a4d81d3de720f70',
    'target-file-acquisition-02/libteec_trustware.so': '0574261e6291fb3f28bf8a254c0610c9177e132a6afd0bc7418826173555db81',
    'target-file-acquisition-03/SWUCoreTV': 'b8de9e31bf6e74cf9a1f3cfd2598658d978a4edd88b36d1c2f10129ccc8a2697',
    'target-file-acquisition-03/libSWUProductionConfig.so': 'c6af8346f4643f2cf50e996682611ece7ad6ff8999274570023561d1a97879f0',
    'target-file-acquisition-04/libteec_trustware_common.so': '353104729c40d6f1eff4f07b96f8a14466dd98efddb21a9cb7d14752351dd139',
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def validate_prefix(data):
    require(len(data) == 65494, 'fixed retained prefix size')
    require(data[:6] == b'MSDU11', 'MSDU11')
    require(struct.unpack_from('<I', data, 18)[0] == 9, 'nine clear sections')
    rows = [struct.unpack_from('<IQQ', data, 22 + 20*i) for i in range(9)]
    require([r[0] for r in rows] == list(range(1001, 1010)), 'IDs')
    require(rows[0][1] == 4290, 'first payload boundary')
    require(all(a[1]+a[2] == b[1] for a,b in zip(rows,rows[1:])), 'adjacency')
    require(rows[-1][1]+rows[-1][2] == 1493538434, 'member end')
    require(struct.unpack_from('<I', data, 202)[0] == 1, 'header count')
    require(struct.unpack_from('<QIB', data, 206) == (234,4056,15), 'header descriptor')
    require(data[219:234] == b'T-RSMFAKUC-0090', 'target label')
    require(data[242:250] == b'Salted__', 'marker')
    envelope, cipher = data[234:4290], data[258:4290]
    require(len(cipher) == 4032 and len(cipher)%16 == 0, 'bounded ciphertext')
    require(zlib.crc32(cipher)&0xffffffff == struct.unpack_from('<I',data,238)[0] == 0xefed4e54, 'cipher CRC')
    require(hashlib.sha256(cipher).hexdigest() == MANIFEST['ciphertext']['sha256'], 'cipher hash')
    require(hashlib.sha256(envelope).hexdigest() == MANIFEST['envelope']['sha256'], 'fixed envelope hash')
    require(hashlib.sha256(data).hexdigest() == MANIFEST['retained_prefix']['sha256'], 'fixed prefix hash')
    return {'prefix_bytes':len(data), 'envelope_bytes':len(envelope),
            'ciphertext_bytes':len(cipher), 'salt_bytes':8, 'salt_value_omitted':True,
            'ciphertext_crc32':'efed4e54', 'plaintext_validated':False}


def malformed(data):
    cases = [('truncated_prefix',data[:-1]), ('oversized_prefix',data+b'\0')]
    for name,offset in [('magic',0),('section_id',22),('section_size',34),
                        ('section_offset',46),('header_count',202),('header_offset',206),
                        ('header_size',214),('label_length',218),('label',219),
                        ('wrapper_word',234),('wrapper_crc',238),('marker',242),
                        ('salt',250),('ciphertext',258)]:
        variant=bytearray(data); variant[offset]^=1; cases.append((name,variant))
    rejected=[]
    for name,variant in cases:
        try:
            validate_prefix(variant)
        except (ValueError,struct.error):
            rejected.append(name)
        else:
            raise ValueError('malformed input accepted: '+name)
    return rejected


def frame_verification():
    expected = [
        [0,0x01010d0d,0x11111110,416,0,0x33333330,8,0,0,1,0,1,0x201,0,0],
        [0,0x00020e0d,0x11111110,4032,0,0x22222220,4032,0,0,0,0,0,0,0,0],
        [0,0x0000020e,0x22222220,65536,0,0,0,0,0,0,0,0,0,0,0],
    ]
    # Executable is the local host-only mock built from the owned test source.
    output=subprocess.run([str(HERE/'host-test')],check=True,capture_output=True,text=True).stdout
    lines=output.splitlines()
    for i,words in enumerate(expected):
        require(lines[i] == f'frame{i}='+struct.pack('<15I',*words).hex(), 'golden frame '+str(i))
    require(lines[-1].startswith('PASS:'),'host mock result')
    return [{'command':i,'bytes':60,'hex':struct.pack('<15I',*w).hex()} for i,w in enumerate(expected)]


def main():
    data=PREFIX.read_bytes()
    report=validate_prefix(data)
    report['malformed_cases_rejected']=malformed(data)
    report['elf_hashes_verified']={}
    for relative,expected in ELFS.items():
        raw=(RESEARCH/relative).read_bytes()
        require(hashlib.sha256(raw).hexdigest()==expected,'ELF pin '+relative)
        require(raw[:6]==b'\x7fELF\x01\x01','ELF32 LE '+relative)
        report['elf_hashes_verified'][relative]=expected
    report['golden_frames_synthetic_addresses']=frame_verification()
    report['target_library_loaded']=False
    report['target_calls']=0
    report['prototype_execution_qualified']=False
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
