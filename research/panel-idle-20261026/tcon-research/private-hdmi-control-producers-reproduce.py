#!/usr/bin/env python3
"""Offline census for copied userspace producers of private HDMI CIDs."""
from pathlib import Path
import argparse, hashlib, json
from elftools.elf.elffile import ELFFile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
EXPECTED_MANIFEST_SHA='6ac980c13bc4318a77519fa2dbfada3346de05c73fc4d8765df2666196becba2'
CIDS=(0x00a009be,0x00a009bf)

def require(ok,msg):
    if not ok: raise ValueError(msg)

def user_elfs():
    found=[]
    for p in sorted((ROOT/'binaries').iterdir()):
        if not p.is_file() or p.read_bytes()[:4] != b'\x7fELF': continue
        with p.open('rb') as h:
            elf=ELFFile(h)
            if elf['e_type'] in ('ET_DYN','ET_EXEC') and elf['e_machine']=='EM_ARM':
                found.append((p,elf['e_type']))
    return found

def needed(elf):
    d=elf.get_section_by_name('.dynamic')
    if d is None:return []
    return sorted(x.needed for x in d.iter_tags('DT_NEEDED'))

def movw_movt_hits(data, base, cid):
    """Fast byte-exact census of standard ARM/Thumb MOVW+MOVT forms.

    The copied ARM userspace ELFs lack reliable mapping symbols.  This checks
    the documented encodings at all 4-byte ARM and 2-byte Thumb alignments;
    it intentionally does not pretend to cover arbitrary arithmetic synthesis.
    """
    low=cid & 0xffff; high=cid >> 16; out=[]
    for rd in range(16):
        armw=(0xe3000000 | (rd<<12) | low).to_bytes(4,'little')
        armt=(0xe3400000 | (rd<<12) | high).to_bytes(4,'little')
        pos=0
        while True:
            off=data.find(armw,pos)
            if off<0:break
            if off%4==0:
                scan=off+4
                while True:
                    noff=data.find(armt,scan,min(len(data),off+64))
                    if noff<0:break
                    if noff%4==0:
                        out.append((base+off,base+noff,'ARM-AL'))
                        break
                    scan=noff+1
            pos=off+1
        # Thumb MOVW T3, then MOVT T1.  CID low/high fields here make the
        # first halfwords f640/f2c0 and preserve the same Rd.
        mw=(0xf640).to_bytes(2,'little')+((0x1000 | (rd<<8) | (low&0xff))).to_bytes(2,'little')
        mt=(0xf2c0).to_bytes(2,'little')+((rd<<8 | high)).to_bytes(2,'little')
        pos=0
        while True:
            off=data.find(mw,pos)
            if off<0:break
            if off%2==0:
                scan=off+2
                while True:
                    noff=data.find(mt,scan,min(len(data),off+64))
                    if noff<0:break
                    if noff%2==0:
                        out.append((base+off,base+noff,'Thumb'))
                        break
                    scan=noff+1
            pos=off+1
    return out

def encoding_fixture():
    """Prove a misaligned decoy does not hide a later aligned MOVT."""
    cid=CIDS[0]; low=cid & 0xffff; high=cid >> 16
    armw=(0xe3000000 | low).to_bytes(4,'little')
    armt=(0xe3400000 | high).to_bytes(4,'little')
    arm=bytearray(24);arm[0:4]=armw;arm[5:9]=armt;arm[12:16]=armt
    require(movw_movt_hits(bytes(arm),0,cid)==[(0,12,'ARM-AL')],'ARM decoy fixture')
    thumbw=(0xf640).to_bytes(2,'little')+(0x10be).to_bytes(2,'little')
    thumbt=(0xf2c0).to_bytes(2,'little')+(0x00a0).to_bytes(2,'little')
    thumb=bytearray(24);thumb[0:4]=thumbw;thumb[5:9]=thumbt;thumb[10:14]=thumbt
    require(movw_movt_hits(bytes(thumb),0,cid)==[(0,10,'Thumb')],'Thumb decoy fixture')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--write-disassembly',action='store_true');args=ap.parse_args()
    encoding_fixture()
    inputs=user_elfs()
    manifest=[]; raw_hits=[]; synth_hits=[]; v4l_strings=[]; deps={}
    for path,etype in inputs:
        raw=path.read_bytes(); manifest.append({'name':path.name,'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'type':etype})
        for cid in CIDS:
            pos=raw.find(cid.to_bytes(4,'little'))
            if pos >= 0: raw_hits.append((path.name,cid,pos))
        with path.open('rb') as h:
            elf=ELFFile(h); deps[path.name]=needed(elf)
            for sec in elf.iter_sections():
                if not (sec['sh_flags'] & 4):continue
                for cid in CIDS:
                    for first,second,mode in movw_movt_hits(sec.data(),sec['sh_addr'],cid):
                        synth_hits.append((path.name,sec.name,first,second,cid,mode))
        if b'/dev/video' in raw or b'VIDIOC' in raw or b'v4l2' in raw or b'V4L2' in raw:
            v4l_strings.append(path.name)
    digest=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    require(digest==EXPECTED_MANIFEST_SHA,'userspace inventory/hash manifest')
    require(not raw_hits,'exact CID literal found')
    require(not synth_hits,'MOVW/MOVT CID construction found')
    require('libhdmi-control.so.0' in deps['avocd'],'known unacquired HDMI control dependency')
    require('libsource-api.so' in deps['tv-viewer'],'known unacquired source dependency')
    text='# Static copied-userspace CID census\n\n'
    text+=f'Manifest SHA-256: `{digest}`; entries: {len(manifest)}.\n\n'
    text+='## Inputs\n'+''.join(f"- `{x['name']}` {x['type']} {x['size']} B `{x['sha256']}`\n" for x in manifest)
    text+='\n## Results\n- Exact little-endian literals: none.\n- Same-register ARM-AL or Thumb MOVW/MOVT constructions within 64 bytes: none.\n'
    text+='- V4L2-adjacent byte strings occur in: '+(', '.join(v4l_strings) if v4l_strings else 'none')+'. They are not CID hits.\n'
    text+='\n## Relevant missing DT_NEEDED names\n- `avocd` requires `libhdmi-control.so.0`.\n- `tv-viewer` requires `libsource-api.so`.\n'
    out=HERE/'private-hdmi-control-producers-v2.disasm'
    if args.write_disassembly:
        with out.open('x') as h:h.write(text)
    else: require(out.read_text()==text,'saved census equality')
    print(f'PASS: {len(manifest)} copied ARM userspace ELFs; no exact private HDMI CID producer hit.')
    print('This bounded static absence does not cover unacquired DSOs, synthesized forms outside MOVW/MOVT, IPC, or live execution.')

if __name__=='__main__':main()
