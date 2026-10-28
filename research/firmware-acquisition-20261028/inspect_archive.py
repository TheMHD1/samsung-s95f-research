#!/usr/bin/env python3
"""Offline clear-directory bounds and opaque interval hashes; no decryption."""
from pathlib import Path
import hashlib,json,struct,zlib
P=Path(__file__).resolve().parent
def need(ok,msg):
 if not ok:raise ValueError(msg)
def digest_range(f,start,size):
 f.seek(start);h=hashlib.sha256();left=size
 while left:
  b=f.read(min(left,4*1024*1024));need(bool(b),'truncated interval');h.update(b);left-=len(b)
 return h.hexdigest()
def parse(prefix,member_size):
 need(len(prefix)>=26 and prefix[:6]==b'MSDU11','magic/minimum')
 raw_word,raw_u64,count=struct.unpack_from('<IQI',prefix,6)
 need(0<count<=64 and 22+20*count+4<=len(prefix),'section bounds');pos=22;rows=[]
 for _ in range(count):
  tag,offset,size=struct.unpack_from('<IQQ',prefix,pos);pos+=20
  need(size>0 and offset<=member_size and size<=member_size-offset,'payload range')
  rows.append({'id':tag,'offset':offset,'bytes':size,'end':offset+size})
 n,=struct.unpack_from('<I',prefix,pos);pos+=4;need(0<n<=16,'header count');headers=[]
 for _ in range(n):
  need(pos+13<=len(prefix),'header descriptor bounds');offset,size,length=struct.unpack_from('<QIB',prefix,pos);pos+=13
  need(0<length<=128 and pos+length<=len(prefix),'label bounds');name=prefix[pos:pos+length].decode('ascii');pos+=length
  need(size>=24 and offset<=len(prefix) and size<=len(prefix)-offset,'complete header bounds');need(prefix[offset+8:offset+16]==b'Salted__','header marker')
  plain_crc,encrypted_crc=struct.unpack_from('<II',prefix,offset);cipher=prefix[offset+24:offset+size]
  need(zlib.crc32(cipher)==encrypted_crc,'header encrypted CRC')
  headers.append({'label':name,'offset':offset,'bytes':size,'end':offset+size,'ciphertext_bytes':len(cipher),'ciphertext_sha256':hashlib.sha256(cipher).hexdigest(),'wrapper_plaintext_crc32_unverified':f'{plain_crc:08x}','wrapper_encrypted_crc32':f'{encrypted_crc:08x}','encrypted_crc32_verified':True,'plaintext_crc32_verified':False})
 need(headers[0]['offset']==pos and headers[-1]['end']==rows[0]['offset'],'header adjacency')
 need(all(x['end']==y['offset'] for x,y in zip(rows,rows[1:])) and rows[-1]['end']==member_size,'payload contiguity/member end')
 return {'magic':'MSDU11','raw_word_at_6_unverified':f'{raw_word:08x}','raw_u64_at_10_semantics_unassigned':raw_u64,'clear_descriptor_bytes':pos,'encrypted_headers':headers,'sections':rows,'member_bytes':member_size,'payload_names_unassigned':True,'payload_plaintext_crc_not_available':True,'signature_verified':False}
def main():
 results=[]
 for label in ['T-RSMFAKUC-0090','TB-RSWF4AKUC-0090']:
  file=P/(label+'-upgrade.msd');size=file.stat().st_size
  with file.open('rb') as f:
   prefix=f.read(65494);item=parse(prefix,size)
   for row in item['sections']:row['distributed_interval_sha256']=digest_range(f,row['offset'],row['bytes'])
  item.update({'path':file.name,'label':label});results.append(item)
 output={'target_calls':0,'decryption_attempted':False,'payload_code_executed':False,'full_members_available':True,'containers':results}
 (P/'clear-directory-and-section-hashes.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps({'containers':len(results),'sections':[len(x['sections']) for x in results],'all_interval_bounds_and_encrypted_header_crcs_pass':True}))
if __name__=='__main__':main()
