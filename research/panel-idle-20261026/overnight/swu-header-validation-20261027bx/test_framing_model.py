#!/usr/bin/env python3
"""Synthetic public host fixtures only; never a real decrypted header."""
import json,struct,zlib
import framing_model as m
p32=lambda n:struct.pack('<I',n)
p16=lambda n:struct.pack('<H',n)
if zlib.crc32(b'123456789')&0xffffffff!=0xcbf43926:raise RuntimeError('CRC32 KAT')
key=m.PublicKeyAnchor(0x12345678,32)
prefix=p32(key.crc32)+p16(key.signature_bytes)+b'PUBLIC-SYNTHETIC-SIGNATURE-1234567'[:32]
def record(tag,body,mandatory=1):
 b=p32(tag)+bytes([mandatory])+body
 return b'\1'+p32(len(b))+b
def tree(entries):return prefix+m.MAGIC+p32(len(entries))+b''.join(entries)
def run(data,anchor=key):return m.model_unpadded(data,zlib.crc32(data)&0xffffffff,anchor)
valid=tree([record(18,p32(0x76543210)),record(16,p32(2)+p16(3)+b'abc'),b'\0'])
assert run(valid)['root_count']==3
assert run(valid)['records'][0]['leaf_layout_checked']
assert not run(valid)['signature_authenticity_validated']
assert not run(valid)['metadata_published']
rejected=[]
def reject(name,fn,code):
 try:fn()
 except m.Rejected as e:
  assert str(e)==code,(name,str(e),code);rejected.append(name)
 else:raise AssertionError(name+' accepted')
reject('wrong-whole-stream-crc',lambda:m.model_unpadded(valid,0,key),'PlaintextCrc')
reject('body-only-crc-not-whole-plaintext',lambda:m.model_unpadded(valid,zlib.crc32(valid[len(prefix):])&0xffffffff,key),'PlaintextCrc')
reject('missing-public-key-pin',lambda:run(valid,None),'PublicKeyPinAbsent')
reject('key-id-mismatch',lambda:run(valid,m.PublicKeyAnchor(0,32)),'PublicKeyCrc')
reject('signature-size-mismatch',lambda:run(valid,m.PublicKeyAnchor(key.crc32,31)),'SignatureLength')
reject('zero-key-signature-extent',lambda:run(valid,m.PublicKeyAnchor(key.crc32,0)),'PublicKeyAnchor')
reject('truncated-prefix',lambda:run(valid[:5]),'PlaintextExtent')
reject('oversized-plaintext',lambda:run(valid+b'\0'*4032),'PlaintextExtent')
wrong=bytearray(valid);wrong[len(prefix)]=0
reject('magic-changed',lambda:run(wrong),'TreeMagic')
reject('huge-root-count',lambda:run(prefix+m.MAGIC+p32(0xffffffff)),'RootCount')
reject('noncanonical-presence',lambda:run(tree([b'\2'])),'PresenceCanonical')
reject('truncated-length',lambda:run(tree([b'\1\0\0'])),'Truncated')
reject('body-underflow',lambda:run(tree([b'\1'+p32(4)+p32(18)])),'DescriptorMinimum')
reject('body-overrun',lambda:run(tree([b'\1'+p32(0xffffffff)+b'12345'])),'Truncated')
reject('unknown-tag',lambda:run(tree([record(0x1234,b'')])),'UnsupportedDescriptorTag')
reject('noncanonical-mandatory',lambda:run(tree([record(18,p32(0),2)])),'MandatoryCanonical')
reject('crc-leaf-too-short',lambda:run(tree([record(18,b'123')])),'Truncated')
reject('crc-leaf-extra',lambda:run(tree([record(18,b'12345')])),'TrailingBytes')
reject('rsa-leaf-signature-overrun',lambda:run(tree([record(16,p32(2)+p16(5)+b'ab')])),'Truncated')
reject('rsa-leaf-extra',lambda:run(tree([record(16,p32(2)+p16(1)+b'ab')])),'TrailingBytes')
reject('document-extra',lambda:run(valid+b'\0'),'TrailingBytes')
for n in range(1,17):assert m.strict_padding_bytes(b'A'*(32-n)+bytes([n])*n)==n
reject('padding-zero',lambda:m.strict_padding_bytes(b'A'*31+b'\0'),'PaddingValue')
reject('padding-too-large',lambda:m.strict_padding_bytes(b'A'*31+b'\x11'),'PaddingValue')
reject('padding-inconsistent',lambda:m.strict_padding_bytes(b'A'*30+b'\1\2'),'PaddingPattern')
reject('padding-unaligned',lambda:m.strict_padding_bytes(b'A'*17),'PaddingExtent')
reject('fixed-output-size',lambda:m.model_fixed_padded(b'A'*32,key),'CipherOutputExtent')
# Correctly padded4032B still needs exact fixed plaintext CRC; no heuristic acceptance.
reject('fixed-output-wrong-crc',lambda:m.model_fixed_padded(b'A'*4031+b'\1',key),'PlaintextCrc')
print(json.dumps({'host_only':True,'target_calls':0,'actual_plaintext_used':False,'synthetic_framing_successes':1,'strict_padding_successes':16,'malformed_rejections':len(rejected),'rejected':rejected,'full_schema_validated':False,'signature_authenticity_validated':False,'metadata_published':False},indent=2))
