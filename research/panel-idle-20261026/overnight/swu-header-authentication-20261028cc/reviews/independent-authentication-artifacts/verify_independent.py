#!/usr/bin/env python3
"""Read-only source/anchor/fixture verification. No target, root or network calls."""
import hashlib,json,re,struct,zlib
from pathlib import Path
from cryptography.hazmat.primitives import serialization,hashes
from cryptography.hazmat.primitives.asymmetric import padding as rsa_padding
from cryptography.exceptions import InvalidSignature
from elftools.elf.elffile import ELFFile
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB

HERE=Path(__file__).resolve().parent
CC=HERE.parents[1]
SPEC=CC.parent/'swu-header-validation-20261027bx'
PUBLIC=CC.parent/'swu-public-key-20261028cc/itemsPublicRSAKey.txt'
CORE=Path('${S95F_EVIDENCE_ROOT}/research-20261027-external/target-file-acquisition-03/SWUCoreTV')
checks=0

def need(ok,message):
 global checks
 if not ok:raise ValueError(message)
 checks+=1

def sha(data):return hashlib.sha256(data).hexdigest()
MAGIC=b'Tizen Software Upgrade Tree Binary Format ver. 1.9\0'
TAGS={1,2,7,10,11,14,16,18,19,21,25,35,53,55,56,57,58,59,60,61,62}

def frame(data):
 if len(data)<55:return 'Truncated'
 if data[:51]!=MAGIC:return 'TreeMagic'
 count=struct.unpack_from('<I',data,51)[0];at=55
 if count>len(data)-at:return 'RootCount'
 for _ in range(count):
  if at>=len(data):return 'Truncated'
  present=data[at];at+=1
  if present>1:return 'PresenceCanonical'
  if not present:continue
  if at+4>len(data):return 'Truncated'
  n=struct.unpack_from('<I',data,at)[0];at+=4
  if n<5 or n>len(data)-at:return 'DescriptorExtent'
  body=data[at:at+n];at+=n;tag=struct.unpack_from('<I',body)[0]
  if tag not in TAGS:return 'UnsupportedTag'
  if body[4]>1:return 'MandatoryCanonical'
  if tag==18 and n!=9:return 'LeafExtent'
  if tag==16 and (n<11 or struct.unpack_from('<H',body,9)[0]!=n-11):return 'LeafExtent'
 return 'None' if at==len(data) else 'TrailingBytes'

def classify(raw,pem,pin,crc):
 n=raw[-1];canonical=1<=n<=16 and raw[-n:]==bytes([n])*n
 candidates=[raw]
 if canonical:candidates.append(raw[:-n])
 selected=[c for c in candidates if zlib.crc32(c)==crc]
 if len(selected)==2:return 'RepresentationAmbiguous',None
 if not selected:return 'RepresentationCrcMismatch',None
 plain=selected[0]
 if struct.unpack_from('<I',plain)[0]!=int(pin['pemCrc32'],16):return 'PublicKeyCrc',plain
 if struct.unpack_from('<H',plain,4)[0]!=256:return 'SignatureLength',plain
 key=serialization.load_pem_public_key(pem)
 try:key.verify(plain[6:262],plain[262:],rsa_padding.PKCS1v15(),hashes.SHA512())
 except InvalidSignature:return 'SignatureInvalid',plain
 return frame(plain[262:]),plain


def main():
 source=(CC/'HeaderAuthentication.cs').read_bytes()
 need(sha(source)=='a9797c9dda6f66ed6cc2e764117915ac115b4f36db7796f8bb921be00ddce5cf','frozen pure source')
 inventory=json.loads((CC/'source-inventory.json').read_text())['files']
 for filename,meta in inventory.items():
  data=(CC/filename).read_bytes();need(len(data)==meta['bytes'] and sha(data)==meta['sha256'],'complete frozen source inventory '+filename)
 provenance=json.loads((CC/'provenance.json').read_text())
 for rel,digest in provenance['source_spec_inputs'].items():need(sha((CC/rel).read_bytes())==digest,'input provenance '+rel)
 host=json.loads((CC/'host-verification.json').read_text())
 need(sha((CC/'bin/Release/net6.0/HeaderAuthentication.dll').read_bytes())==host['libraryDllSha256'],'frozen compiled library')
 need(sha((CC/'fixtures/manifest.json').read_bytes())==host['fixtureManifestSha256'],'frozen fixture manifest')
 for text in ['System.IO','Console.','DllImport','Process.','System.Net','File.','Directory.','ITeec','TEEC_']:
  need(text not in source.decode(),'pure source boundary '+text)
 public=PUBLIC.read_bytes();need(len(public)==426 and sha(public)=='ebf12ab9d4ef069e1a6030b8c3b117894746637715270f7e3d37d3cd737f71a3','actual public file exact pin')
 need(zlib.crc32(public)==0x860be2ed,'actual public file CRC independently zlib')
 key=serialization.load_pem_public_key(public);need(key.key_size==2048,'actual RSA2048')
 need(len(MAGIC)==51,'exact format magic')
 core=CORE.read_bytes();need(sha(core)=='b8de9e31bf6e74cf9a1f3cfd2598658d978a4edd88b36d1c2f10129ccc8a2697','exact Core input')
 with CORE.open('rb') as stream:
  elf=ELFFile(stream);segments=[s for s in elf.iter_segments() if s['p_type']=='PT_LOAD']
  def read(address,n):
   for segment in segments:
    if segment['p_vaddr']<=address and address+n<=segment['p_vaddr']+segment['p_filesz']:
     off=segment['p_offset']+address-segment['p_vaddr'];return core[off:off+n]
   raise ValueError('unmapped Core anchor')
  anchors=json.loads((SPEC/'byte-anchors.json').read_text())['anchors']
  for anchor in anchors:
   n=anchor['bytes'];expected=bytes.fromhex(anchor['hex']);need(len(expected)==n and read(int(anchor['address'],16),n)==expected,'retained byte anchor '+anchor['role'])
  need(read(0x40b384,51)==MAGIC,'Core magic actual bytes')
  dis=Cs(CS_ARCH_ARM,CS_MODE_THUMB);dis.skipdata=True
  lines=[]
  for address,n,label in [(0x1d66a6,160,'prefix read / signature remainder attachment'),(0x327c0c,96,'digest selector2 constructs SHA512 sink'),(0x327e4c,60,'PKCS1 numeric padding and digest'),(0x3281c0,112,'verify and exact success1'),(0x36c828,36,'SHA512 sink init'),(0x246476,20,'encoder padding formula'),(0x2a0df2,28,'body tag and full-consumption check')]:
   lines.append(label)
   for ins in dis.disasm(read(address,n),address):lines.append(f'{ins.address:08x} {ins.bytes.hex():10s} {ins.mnemonic} {ins.op_str}')
  (HERE/'independent-core-excerpts.txt').write_text('\n'.join(lines)+'\n')
 firmware=Path('${S95F_EVIDENCE_ROOT}/firmware-acquisition-20261028/T-RSMFAKUC-0090-upgrade.msd')
 with firmware.open('rb') as stream:prefix=stream.read(65494)
 need(sha(prefix)=='01821f40cf70841649c856090e23b35be6173659fb54be11f3b661a3e37bf92d','retained main firmware prefix identity')
 need(struct.unpack_from('<II',prefix,234)==(0xcbcf1d91,0xefed4e54),'actual main wrapper CRC anchors')
 need(prefix[242:250]==b'Salted__' and zlib.crc32(prefix[258:4290])==0xefed4e54,'actual encrypted wrapper frame/CRC; no decryption')
 manifest=json.loads((CC/'fixtures/manifest.json').read_text());need(not manifest['actualPlaintextUsed'],'synthetic-only manifest')
 for filename,meta in manifest['assets'].items():
  data=(CC/'fixtures'/filename).read_bytes();need(len(data)==meta['bytes'] and sha(data)==meta['sha256'],'all synthetic asset pins '+filename)
 factory=json.loads((SPEC/'descriptor-factory.json').read_text());need({x['tag'] for x in factory}==TAGS,'known21 factory tags')
 results=[]
 for row in manifest['fixtures']:
  raw=(CC/'fixtures'/row['path']).read_bytes();need(len(raw)==4032 and sha(raw)==row['sha256'],'fixture bytes '+row['name'])
  pem=(CC/'fixtures'/('synthetic-public.pem' if row['anchor']=='primary' else 'synthetic-wrong-public.pem')).read_bytes()
  reason,selected=classify(raw,pem,manifest[row['anchor']],int(row['plaintextCrc32'],16))
  need(reason==row['reason'],'independent Python crypto/framing '+row['name'])
  need((reason=='None')==row['accepted'],'independent acceptance '+row['name'])
  if row['accepted']:
   need(len(selected)==row['selectedBytes'],'selected representation extent')
   need(zlib.crc32(selected[262:])!=int(row['plaintextCrc32'],16),'whole CRC differs from signed-remainder-only CRC')
  results.append({'name':row['name'],'reason':reason,'accepted':reason=='None'})
 actual_master_failures=0
 for row in manifest['fixtures']:
  raw=(CC/'fixtures'/row['path']).read_bytes()
  reason,_=classify(raw,public,{'pemCrc32':'860be2ed'},0xcbcf1d91)
  need(reason!='None','actual Master rejects every synthetic fixture')
  actual_master_failures+=1
 result={'schema':'cc-independent-offline-review-v1','checks':checks,'frozen_inventory_files_verified':len(inventory),'byte_anchors_verified':len(anchors),'actual_public_pem_bytes':len(public),'actual_public_pem_crc32':'860be2ed','actual_public_rsa_bits':key.key_size,'signature_bytes':256,'actual_main_wrapper_plaintext_crc32':'cbcf1d91','actual_main_encrypted_crc32':'efed4e54','synthetic_fixtures_independently_reclassified':len(results),'accepted_synthetic':sum(x['accepted'] for x in results),'rejected_synthetic':sum(not x['accepted'] for x in results),'actual_master_refuses_synthetic_fixtures':actual_master_failures,'fixture_results':results,'target_operations':0,'actual_plaintext_used':False,'full_schema_validated':False,'metadata_published':False}
 (HERE/'independent-verification.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k!='fixture_results'},indent=2))

if __name__=='__main__':main()
