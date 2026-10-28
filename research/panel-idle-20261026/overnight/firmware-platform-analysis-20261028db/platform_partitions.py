"""Offline GPT validation and fixed private extraction of accepted platform.img.
No mounts, subprocesses, OEM execution, target calls or network operations.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import struct
import uuid
import zlib

HERE=Path(__file__).resolve().parent
ROOT=Path('${S95F_EVIDENCE_ROOT}/firmware-extracted-20261028')
IMAGE=ROOT/'platform.img'
INVENTORY=ROOT/'extraction-inventory.json'
OUTPUT=HERE/'private/partitions'
EXPECTED_BYTES=1455423488
PROFILE=[('pltf_t.img',1048576,1391460352),('prd_t.img',1392508928,61865984)]
LINUX_GUID='00000000-0000-4000-8000-000000000000'

def need(ok,reason):
    if not ok:raise ValueError(reason)
def crc(data):return zlib.crc32(data)&0xffffffff
def exact(fd,offset,length):
    need(type(offset) is int and type(length) is int and offset>=0 and 0<length<=1048576,'read bounds')
    chunks=bytearray()
    while len(chunks)<length:
        piece=os.pread(fd,length-len(chunks),offset+len(chunks));need(bool(piece),'unexpected EOF');chunks.extend(piece)
    return bytes(chunks)
def header(sector,disk_bytes,current):
    need(len(sector)==512,'GPT sector size')
    sig,rev,size,stored,reserved,here,other,first,last,guid,entries,count,width,table_crc=struct.unpack_from('<8sIIIIQQQQ16sQIII',sector)
    need(sig==b'EFI PART' and rev==0x10000 and size==92 and reserved==0,'GPT header identity')
    copy=bytearray(sector[:size]);copy[16:20]=b'\0'*4;need(crc(copy)==stored,'GPT header CRC')
    disk_lbas=disk_bytes//512
    need(disk_bytes%512==0 and here==current and other==(disk_lbas-1 if current==1 else 1),'GPT header placement')
    need(first>=34 and first<=last<disk_lbas-1 and guid!=b'\0'*16,'GPT usable range/GUID')
    need(count==128 and width==128 and entries>0 and entries*512+count*width<=disk_bytes,'GPT entry table bounds')
    need((entries+32<=first if current==1 else last<entries and entries+32<=here),'GPT entry table overlap')
    return {'current_lba':here,'backup_lba':other,'first_usable_lba':first,'last_usable_lba':last,'disk_guid':str(uuid.UUID(bytes_le=guid)),'entries_lba':entries,'entry_count':count,'entry_bytes':width,'entry_crc32':table_crc,'header_crc32':stored,'disk_bytes':disk_bytes}
def table_rows(table,h):
    need(len(table)==h['entry_count']*h['entry_bytes'] and crc(table)==h['entry_crc32'],'GPT entry CRC')
    rows=[];guids=set()
    for i in range(h['entry_count']):
        e=table[i*128:(i+1)*128]
        if e[:16]==b'\0'*16:
            need(e==b'\0'*128,'nonempty unused entry');continue
        first,last,attrs=struct.unpack_from('<QQQ',e,32)
        need(h['first_usable_lba']<=first<=last<=h['last_usable_lba'],'partition extent')
        typ=str(uuid.UUID(bytes_le=e[:16]));guid=str(uuid.UUID(bytes_le=e[16:32]));need(e[16:32]!=b'\0'*16 and guid not in guids,'partition GUID');guids.add(guid)
        text=e[56:128].decode('utf-16-le');name,sep,tail=text.partition('\0');need(sep and not tail.strip('\0') and name and all(ord(x)>=32 for x in name),'partition name')
        rows.append({'index':i+1,'name':name,'type_guid':typ,'unique_guid':guid,'first_lba':first,'last_lba':last,'attributes':attrs,'offset':first*512,'bytes':(last-first+1)*512})
    ordered=sorted(rows,key=lambda r:r['offset'])
    need(all(a['offset']+a['bytes']<=b['offset'] for a,b in zip(ordered,ordered[1:])),'partition overlap')
    return rows

def primary(prefix,disk_bytes=EXPECTED_BYTES):
    prefix=bytes(prefix)
    need(len(prefix)>=17408 and prefix[510:512]==b'\x55\xaa','protective MBR')
    entry=prefix[446:462];need(entry[4]==0xee and struct.unpack_from('<I',entry,8)[0]==1 and struct.unpack_from('<I',entry,12)[0]==min(disk_bytes//512-1,0xffffffff) and prefix[462:510]==b'\0'*48,'protective MBR extent')
    h=header(prefix[512:1024],disk_bytes,1);offset=h['entries_lba']*512;length=h['entry_count']*h['entry_bytes'];need(offset+length<=len(prefix),'primary table not available')
    rows=table_rows(prefix[offset:offset+length],h)
    return h,rows

def complete_gpt(fd,disk_bytes=EXPECTED_BYTES):
    h,rows=primary(exact(fd,0,1048576),disk_bytes)
    backup=header(exact(fd,disk_bytes-512,512),disk_bytes,disk_bytes//512-1)
    for field in ['first_usable_lba','last_usable_lba','disk_guid','entry_count','entry_bytes','entry_crc32']:
        need(h[field]==backup[field],'primary/backup header mismatch')
    p=exact(fd,h['entries_lba']*512,16384);q=exact(fd,backup['entries_lba']*512,16384)
    need(p==q,'primary/backup table mismatch');need(table_rows(q,backup)==rows,'backup partition mismatch')
    return {'primary':h,'backup':backup,'partitions':rows}
def identity(fd):
    s=os.fstat(fd);return (s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def pairs(items):
    out={}
    for key,value in items:need(key not in out,'duplicate JSON key');out[key]=value
    return out

def accepted_record(inventory_bytes,inventory_sha):
    need(re.fullmatch('[0-9a-f]{64}',inventory_sha) and hashlib.sha256(inventory_bytes).hexdigest()==inventory_sha,'accepted inventory identity')
    need(len(inventory_bytes)<=1048576,'inventory bound')
    inv=json.loads(inventory_bytes,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('JSON constant')))
    need(inv['schema']=='s95f-private-firmware-extraction-v1','inventory schema')
    rows=[r for r in inv['items'] if r.get('name')=='platform.img'];need(len(rows)==1,'accepted platform item missing/duplicate');r=rows[0]
    need(r.get('section',r.get('id'))==1001 and type(r.get('bytes')) is int and r['bytes']==EXPECTED_BYTES,'accepted platform identity/count')
    need(all(r.get(k) is True for k in ['ciphertext_rsa_verified','strict_padding_validated','original_crc_validated']) and r.get('installed') is False,'platform validation not accepted')
    need(type(r.get('sha256')) is str and re.fullmatch('[0-9a-f]{64}',r['sha256']),'accepted image digest')
    return r

def extract(inventory_sha):
    os.umask(0o077);r=accepted_record(INVENTORY.read_bytes(),inventory_sha)
    need(not OUTPUT.exists() and not OUTPUT.is_symlink(),'fresh output only')
    fd=os.open(IMAGE,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        start=identity(fd);need(stat.S_ISREG(start[2]) and not start[2]&0o077 and start[3]==os.getuid() and start[4]==EXPECTED_BYTES,'private complete regular source')
        gpt=complete_gpt(fd,EXPECTED_BYTES)
        need([(x['name'],x['offset'],x['bytes']) for x in gpt['partitions']]==PROFILE and all(x['type_guid']==LINUX_GUID for x in gpt['partitions']),'fixed partition profile')
        whole=hashlib.sha256();cursor=0
        while cursor<EXPECTED_BYTES:
            block=exact(fd,cursor,min(1048576,EXPECTED_BYTES-cursor));whole.update(block);cursor+=len(block)
        need(whole.hexdigest()==r['sha256'] and identity(fd)==start,'complete accepted source hash/identity')
        need(stat.S_IMODE(OUTPUT.parent.stat().st_mode)==0o700,'private output parent')
        OUTPUT.mkdir(mode=0o700);copied=[]
        for name,offset,count in PROFILE:
            partial=OUTPUT/(name+'.partial');target=OUTPUT/name;out=os.open(partial,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
            digest=hashlib.sha256();at=0
            try:
                while at<count:
                    block=exact(fd,offset+at,min(1048576,count-at));digest.update(block);done=0
                    while done<len(block):
                        n=os.write(out,block[done:]);need(n>0,'partition write failure');done+=n
                    at+=len(block)
                os.fsync(out);need(os.fstat(out).st_size==count,'partition output count')
            finally:os.close(out)
            need(identity(fd)==start,'source changed while copying')
            os.link(partial,target,follow_symlinks=False);partial.unlink()
            copied.append({'name':name,'bytes':count,'offset':offset,'sha256':digest.hexdigest(),'source_accepted':True,'filesystem_authentication_claimed':False})
        need(identity(fd)==start,'final source drift')
        result={'schema':'fixed-platform-partitions-v1','inventory_sha256':inventory_sha,'source_sha256':r['sha256'],'source_bytes':EXPECTED_BYTES,'gpt':gpt,'partitions':copied,'mounted':False,'oem_code_executed':False}
        (OUTPUT/'partition-inventory.json').write_text(json.dumps(result,indent=2)+'\n');(OUTPUT/'partition-inventory.json').chmod(0o600)
        directory=os.open(OUTPUT,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        try:os.fsync(directory)
        finally:os.close(directory)
        return result
    finally:os.close(fd)

def main():
    p=argparse.ArgumentParser();p.add_argument('--extract',action='store_true');p.add_argument('--inventory-sha256');a=p.parse_args()
    if a.extract:
        need(a.inventory_sha256 is not None,'accepted inventory pin required');r=extract(a.inventory_sha256);print(json.dumps({'extracted':True,'partitions':len(r['partitions']),'bytes':sum(x['bytes'] for x in r['partitions']),'mounted':False}))
    else:
        h,rows=primary((HERE/'private/prefix-00000000-00100000.bin').read_bytes());print(json.dumps({'provisional':True,'primary_header_crc_valid':True,'entry_crc_valid':True,'partitions':rows}))
if __name__=='__main__':main()
