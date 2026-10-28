"""Private original-item promotion, independent of target and TLS implementations."""
from pathlib import Path
import hashlib,json,os,shutil,stat,struct,zlib
B=Path(__file__).resolve().parent.parent
PLAN=B/'swu-item-schema-20261028cf/private/section-descriptors.json'
PLAN_SHA='f7946a96e36bff095ea20e28b4aaea1e40901b3005f863188d2e05b0ff8a4ee8'
NAMES={1001:'platform.img',1002:'uImage',1003:'factory_peq.img',1004:'secos.bin',1005:'seret.bin',1006:'secos_drv.bin',1007:'dtb.bin',1008:'ddr.init',1009:'sign.bin'}
def need(ok,why):
 if not ok:raise ValueError(why)
def section(item):
 raw=PLAN.read_bytes();need(hashlib.sha256(raw).hexdigest()==PLAN_SHA,'schema plan drift');r=next(x for x in json.loads(raw) if x['id']==item)
 need(r['name']==NAMES[item] and r['cmd0_p2']==[0,1] and r['cmd0_p3']==[1,513] and r['ciphertext_sha512_rsa_verified'] and not r['compression_present'] and not r['patch_present'],'section scope')
 need(r['cipher_bytes']-r['expected_original_bytes']==16 and r['expected_aes_padding_bytes']==16 and r['padding_validation_required'],'fixed padding expectation');return r
def binary_plan(r):
 return struct.pack('<8sIQQI8s32s',b'SWUSEC01',r['id'],r['cipher_bytes'],r['expected_original_bytes'],r['expected_output_crc32'],bytes.fromhex(r['salt_bytes']['hex']),bytes.fromhex(r['cipher_sha256']))
def validate_and_copy(raw_path,destination,r):
 """Reads original scope once; validates padding before exclusive final copy promotion.

 Both input and destination remain private. Failure keeps an unaccepted partial,
 never an official-name file; no write or decryption retry occurs here.
 """
 raw_path=Path(raw_path);destination=Path(destination);before=raw_path.lstat()
 need(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size==r['cipher_bytes'],'raw file extent/type')
 need(not destination.exists() and not destination.is_symlink(),'fresh original destination')
 crc=0;digest=hashlib.sha256();remaining=r['expected_original_bytes']
 with raw_path.open('rb') as f:
  while remaining:
   chunk=f.read(min(1048576,remaining));need(bool(chunk),'early raw EOF');crc=zlib.crc32(chunk,crc);digest.update(chunk);remaining-=len(chunk)
  need(f.read(16)==bytes([16])*16 and f.read(1)==b'','strict PKCS7 and EOF')
  after=os.fstat(f.fileno());need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'raw identity drift')
 need(crc==r['expected_output_crc32'],'authenticated original-item CRC')
 temp=destination.with_name(destination.name+'.unaccepted-partial');fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
 copied=0;copied_hash=hashlib.sha256()
 try:
  with os.fdopen(fd,'wb') as out,raw_path.open('rb') as f:
   need(os.fstat(f.fileno()).st_ino==before.st_ino,'raw reopen identity');remaining=r['expected_original_bytes']
   while remaining:
    chunk=f.read(min(1048576,remaining));need(bool(chunk),'copy EOF');need(out.write(chunk)==len(chunk),'copy write count');copied_hash.update(chunk);copied+=len(chunk);remaining-=len(chunk)
   need(f.read(16)==bytes([16])*16 and f.read(1)==b'','copy padding drift');need(copied_hash.digest()==digest.digest(),'copy content drift');out.flush();os.fsync(out.fileno())
  # Link supplies exclusive promotion semantics: unlike rename it cannot replace
  # an existing destination. Both names are same private filesystem directory.
  os.link(temp,destination,follow_symlinks=False);temp.unlink()
 except Exception:raise
 return {'section':r['id'],'name':r['name'],'bytes':copied,'sha256':digest.hexdigest(),'ciphertext_rsa_verified':True,'strict_padding_validated':True,'original_crc_validated':True,'installed':False}
