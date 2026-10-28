#!/usr/bin/env python3
"""Fixed retained-input host analysis. Never loads OEM code or calls the TV.
Private tree/section descriptors only; public result contains no salts/signatures.
"""
from pathlib import Path
import collections,hashlib,json,os,stat,zlib
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import padding,utils
from item_schema import parse_ouit,items,reconcile_numeric_directory

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
RAW=Path('/home/researcher/.local/state/s95f-live-trials/swu-ce-01/authenticated-header-raw.bin')
RAW_SHA='cd4f7bfdfa35044091cdc35d5b0ecabf92609c0a1eb10326e1a61402ef4375b2'
PEM=HERE.parent/'swu-public-key-20261028cc/itemsPublicRSAKey.txt'
PEM_SHA='ebf12ab9d4ef069e1a6030b8c3b117894746637715270f7e3d37d3cd737f71a3'
ACQ=ROOT/'firmware-acquisition-20261028'
MSD=ACQ/'T-RSMFAKUC-0090-upgrade.msd'
MSD_SHA='790584c7a91391bc6e9964c8f1c4649c225d2f9e6aeffabfc5e58e8a64fb7fc3'

def require(ok,code):
 if not ok:raise ValueError(code)
def encoded(v):
 if isinstance(v,bytes):return {'hex':v.hex(),'bytes':len(v)}
 if isinstance(v,dict):return {k:encoded(x) for k,x in v.items()}
 if isinstance(v,(list,tuple)):return [encoded(x) for x in v]
 return v
def private_write(path,value):
 # No symlink following and no overly broad permissions even briefly.
 fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW,0o600)
 try:
  os.fchmod(fd,0o600)
  with os.fdopen(fd,'w',closefd=False) as f:json.dump(encoded(value),f,indent=2);f.write('\n')
 finally:os.close(fd)
def main():
 raw=RAW.read_bytes();pem=PEM.read_bytes()
 require(len(raw)==4032 and hashlib.sha256(raw).hexdigest()==RAW_SHA,'RawPin')
 require(len(pem)==426 and hashlib.sha256(pem).hexdigest()==PEM_SHA,'PemPin')
 require(raw[-5:]==b'\x05'*5,'Padding')
 plain=raw[:-5];key=serialization.load_pem_public_key(pem)
 require(key.key_size==2048,'KeySize')
 require(zlib.crc32(plain)&0xffffffff==0xcbcf1d91,'PlaintextCrc')
 keyid=zlib.crc32(pem)&0xffffffff
 require(int.from_bytes(plain[:4],'little')==keyid,'HeaderKeyId')
 require(int.from_bytes(plain[4:6],'little')==256,'HeaderSignatureSize')
 # Exact candidate0's digest2, independently traced to SHA512; no digest search.
 key.verify(plain[6:262],plain[262:],padding.PKCS1v15(),hashes.SHA512())
 tree=parse_ouit(plain[262:]);require(tree['wire_schema_complete'],'WireSchema')
 directory=json.loads((ACQ/'clear-directory-and-section-hashes.json').read_text())['containers'][0]['sections']
 reconciled=reconcile_numeric_directory(tree,[{'id':d['id'],'offset':d['offset'],'length':d['bytes']} for d in directory])
 require(len(reconciled)==9 and all(r['clear_length_equals_processed_size'] for r in reconciled),'NumericDirectory')
 index={x['item_id']:x for x in items(tree)};plans=[];counts=collections.Counter()
 def walk(d):
  if d is None:return
  counts[d['tag']]+=1
  for x in d.get('children',[]):walk(x)
 for root in tree['roots']:walk(root)
 whole=hashlib.sha256()
 with MSD.open('rb') as f:
  require(os.fstat(f.fileno()).st_size==1493538434,'MsdSize')
  whole.update(f.read(4290))
  for rec in directory:
   require(f.tell()==rec['offset'],'DirectoryContinuity')
   item=index[rec['id']]
   require([x['tag'] for x in item['children'] if x is not None]==[10,7,19],'ItemShape')
   partition,processing,group=item['children']
   require([x['tag'] for x in processing['children'] if x is not None]==[18,14,16],'ProcessingShape')
   crc,aes,rsa=processing['children']
   require(len(aes['salt_bytes'])==8 and aes['processed_size']==rec['bytes'],'AesExtent')
   require(rsa['public_key_id']==keyid and len(rsa['signature_bytes'])==256,'SectionPublicKeyBinding')
   left=rec['bytes'];sha=hashlib.sha256();digest=hashlib.sha512();cipher_crc=0
   while left:
    block=f.read(min(left,4*1024*1024));require(bool(block),'SectionTruncated')
    whole.update(block);sha.update(block);digest.update(block);cipher_crc=zlib.crc32(block,cipher_crc);left-=len(block)
   require(sha.hexdigest()==rec['distributed_interval_sha256'],'SectionSha256')
   key.verify(rsa['signature_bytes'],digest.digest(),padding.PKCS1v15(),utils.Prehashed(hashes.SHA512()))
   signature_ok=True
   plans.append({'id':rec['id'],'name_bytes':partition['string_bytes'],'name':partition['string_bytes'].decode('ascii'),'group_id':group['group_id'],
    'offset':rec['offset'],'cipher_bytes':rec['bytes'],'expected_original_bytes':item['original_size'],
    'cipher_sha256':sha.hexdigest(),'cipher_rsa_scope':{'stage':'ciphertext','relative_offset':0,'bytes':rec['bytes'],'hash':'SHA512','padding':'PKCS1v15','source_addresses':['0x236324','0x2363ec','0x236404','0x2365f4','0x236a62','0x236a6a']},
    'output_crc_scope':{'stage':'original_item_bytes','relative_offset':0,'bytes':item['original_size'],'padding_included':False,'algorithm':'CRC-32/ISO-HDLC','normal_polynomial':'0x04c11db7','reflected_polynomial':'0xedb88320','initial_xor':'0xffffffff','final_xor':'0xffffffff','reflect_input':True,'reflect_output':True,'source_addresses':['0x29e670','0x29e67a','0x356be4','0x1ecef0','0x1ecf52','0x1ed1fe','0x1ed268','0x1f4a40','0x203f04','0x18f298','0x1fcfc0','0x109e68','0x1ffb76','0x1ffbb0']},
    'processing_tags':[18,14,16],'compression_present':False,'patch_present':False,
    'expected_aes_padding_bytes':rec['bytes']-item['original_size'],'padding_validation_required':True,
    'master_binding':{'target_path':'/usr/share/org.tizen.tv.swu/itemsAESPassphraseEncrypted.txt','bytes':416,'sha256':'d8af420d63b9cb2643783c56ce7396a5fd4d809e48df0bd321781cfd025e8220','selector':False,'plaintext_key_exported':False},
    'public_key_binding':{'local_path':str(PEM),'bytes':426,'sha256':PEM_SHA,'key_bits':2048},
    'expected_output_crc32':crc['crc32'],'salt_bytes':aes['salt_bytes'],'aes_processed_size':aes['processed_size'],
    'rsa_public_key_id':rsa['public_key_id'],'rsa_signature_bytes':rsa['signature_bytes'],
    'ciphertext_sha512_rsa_verified':signature_ok,'ciphertext_crc32_equals_tag18':cipher_crc&0xffffffff==crc['crc32'],
    'inherited_crypto_info':[1,2,1,2],'crypto_info_order':['mode','keySize','derive','rsa_hash_algorithm'],'engine_type':0,'crypt_type':1,'decrypt':0,'passphrase_encrypted':1,'cmd0_p2':[0,1],'cmd0_p3':[1,0x201],
    'input_msd_binding':{'local_path':str(MSD),'bytes':1493538434,'sha256':MSD_SHA},
    'authenticated_header_binding':{'local_path':str(RAW),'raw_bytes':4032,'raw_sha256':RAW_SHA,'selected_bytes':4027,'signed_span_offset':262,'signed_span_bytes':3765},
    'payload_plaintext_validated':False,'execution_qualified':False})
  require(f.read(1)==b'' and whole.hexdigest()==MSD_SHA,'WholeMsdSha256')
 private=HERE/'private';private.mkdir(mode=0o700,exist_ok=True)
 require(stat.S_ISDIR(private.lstat().st_mode) and not private.is_symlink(),'PrivateDirectory')
 os.chmod(private,0o700)
 private_write(private/'parsed-header.json',tree);private_write(private/'numeric-reconciliation.json',reconciled)
 private_write(private/'section-descriptors.json',plans)
 public={'raw_sha256':RAW_SHA,'selected_bytes':4027,'padding_bytes':5,'signed_span_offset':262,'signed_span_bytes':3765,
  'header_crc_verified':True,'header_RSA_SHA512_PKCS1_verified_independently_here':True,
  'descriptor_count':tree['descriptor_count'],'root_count':len(tree['roots']),'tag_counts':dict(counts),
  'wire_schema_complete':tree['wire_schema_complete'],'full_schema_validated':False,
  'numeric_ids':[p['id'] for p in plans],'all_nine_processed_sizes_equal_clear_intervals':True,
  'all_nine_original_sizes_are_processed_minus_16':all(p['expected_original_bytes']==p['cipher_bytes']-16 for p in plans),
  'ciphertext_signature_verified_count':sum(p['ciphertext_sha512_rsa_verified'] for p in plans),
  'ciphertext_crc32_equals_tag18_count':sum(p['ciphertext_crc32_equals_tag18'] for p in plans),
  'whole_msd_sha256_verified':MSD_SHA,'all_salts_eight_bytes':True,'all_section_signatures_256_bytes':True,
  'payload_plaintext_validated':False,'metadata_published':False,'TV_calls':0}
 (HERE/'authenticated-structure-summary.json').write_text(json.dumps(public,indent=2)+'\n')
 print(json.dumps(public,indent=2))
if __name__=='__main__':main()
