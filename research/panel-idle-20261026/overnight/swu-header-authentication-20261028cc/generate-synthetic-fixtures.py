#!/usr/bin/env python3
"""Host-only synthetic signing fixture producer. Never reads target plaintext.

All output .bin files are synthetic and public test data. The generated private
keys sign synthetic test bytes only and are not trust anchors for real firmware.
CRC anchors use Python zlib, independently of the C# bitwise implementation.
"""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import zlib

HERE=Path(__file__).resolve().parent
OUT=HERE/'fixtures'
MAGIC=b'Tizen Software Upgrade Tree Binary Format ver. 1.9\0'


def need(ok,why):
    if not ok:raise ValueError(why)


def run(args,data=None):
    result=subprocess.run(args,input=data,capture_output=True,timeout=10)
    need(result.returncode==0,'host openssl fixture command')
    return result.stdout


def crc(data):return zlib.crc32(data)&0xffffffff


def solve_affine(function,target):
    base=function(0)
    columns=[function(1<<i)^base for i in range(32)]
    rows=[]
    for bit in range(32):
        mask=sum(((value>>bit)&1)<<i for i,value in enumerate(columns))
        rows.append([mask,((target^base)>>bit)&1])
    pivots=[];at=0
    for col in range(32):
        pivot=next((i for i in range(at,32) if (rows[i][0]>>col)&1),None)
        if pivot is None:continue
        rows[at],rows[pivot]=rows[pivot],rows[at]
        for i in range(32):
            if i!=at and ((rows[i][0]>>col)&1):rows[i][0]^=rows[at][0];rows[i][1]^=rows[at][1]
        pivots.append(col);at+=1
    need(all(mask or not result for mask,result in rows),'affine CRC target solvable')
    answer=sum(rows[i][1]<<column for i,column in enumerate(pivots))
    need(function(answer)==target,'independent affine CRC solution')
    return answer


def main():
    OUT.mkdir(exist_ok=True)
    # Keys persist only as explicitly synthetic test assets so rerunning fixture
    # generation reproduces exact signed bytes and independently fixed CRCs.
    for name in ('synthetic-only-private.pem','synthetic-only-wrong-private.pem'):
        path=OUT/name
        if not path.exists():
            run(['openssl','genpkey','-algorithm','RSA','-pkeyopt','rsa_keygen_bits:2048','-out',str(path)])
    for src,dst in [('synthetic-only-private.pem','synthetic-public.pem'),('synthetic-only-wrong-private.pem','synthetic-wrong-public.pem')]:
        raw=run(['openssl','rsa','-in',str(OUT/src),'-RSAPublicKey_out'])
        (OUT/dst).write_bytes(raw)
    pem=(OUT/'synthetic-public.pem').read_bytes();wrong_pem=(OUT/'synthetic-wrong-public.pem').read_bytes()
    key_crc=crc(pem)
    anchor={'pemBytes':len(pem),'pemSha256':hashlib.sha256(pem).hexdigest(),'pemCrc32':f'{key_crc:08x}',
            'rsaBits':2048,'signatureBytes':256}
    wrong_anchor={'pemBytes':len(wrong_pem),'pemSha256':hashlib.sha256(wrong_pem).hexdigest(),
                  'pemCrc32':f'{crc(wrong_pem):08x}','rsaBits':2048,'signatureBytes':256}
    fixtures=[]
    def tree(length):
        body_length=length-262-len(MAGIC)-4-1-4
        need(body_length>=5,'synthetic extent')
        body=struct.pack('<IB',35,0)+bytes((i*17+3)%251 for i in range(body_length-5))
        return bytearray(MAGIC+struct.pack('<I',1)+b'\x01'+struct.pack('<I',body_length)+body)
    def sign(signed,identifier=key_crc,declared=256):
        signature=run(['openssl','dgst','-sha512','-sign',str(OUT/'synthetic-only-private.pem')],bytes(signed))
        need(len(signature)==256,'synthetic RSA signature size')
        return struct.pack('<IH',identifier,declared)+signature+bytes(signed)
    def retain(name,selected,pad,accepted=True,reason='None',form=None,anchor_name='primary'):
        raw=selected+bytes([pad])*pad if pad else selected
        need(len(raw)==4032,'fixed raw fixture count')
        path=OUT/(name+'.bin');path.write_bytes(raw)
        expected_crc=crc(selected)
        n=raw[-1];tail=1<=n<=16 and raw[-n:]==bytes([n])*n
        matches=int(crc(raw)==expected_crc)+int(tail and crc(raw[:-n])==expected_crc)
        if accepted:need(matches==1,'exactly one CRC-fitting valid representation')
        fixtures.append({'name':name,'path':path.name,'sha256':hashlib.sha256(raw).hexdigest(),
                         'rawBytes':len(raw),'plaintextCrc32':f'{expected_crc:08x}','ouiOnlyCrc32':f'{crc(selected[262:]):08x}',
                         'accepted':accepted,'reason':reason,'representation':form or ('CanonicalPkcs7' if pad else 'Raw4032'),
                         'paddingBytes':pad,'selectedBytes':len(selected),'anchor':anchor_name})
        return raw
    # Every canonical pad count; each is independently signed and CRC-anchored.
    padded=[]
    for n in range(1,17):
        padded.append(retain(f'pkcs7-{n:02}',sign(tree(4032-n)),n))
    retain('raw-no-padding',sign(tree(4032)),0)
    # Authenticated, already-unpadded raw streams can end in every apparent
    # padding pattern. The whole-stream CRC must keep all their bytes intact.
    for n in range(1,17):
        signed=tree(4032);signed[-n:]=bytes([n])*n
        retain(f'raw-padding-looking-{n:02}',sign(signed),0)
    original=sign(tree(4032))
    changed=bytearray(original);changed[6]^=1
    retain('wrong-signature',bytes(changed),0,False,'SignatureInvalid')
    changed=bytearray(original);changed[-17]^=1
    retain('wrong-signed-remainder',bytes(changed),0,False,'SignatureInvalid')
    changed=bytearray(original);changed[:4]=struct.pack('<I',crc(wrong_pem))
    retain('wrong-key-valid-prefix',bytes(changed),0,False,'SignatureInvalid',anchor_name='wrong')
    changed=bytearray(original);changed[:4]=struct.pack('<I',key_crc^1)
    retain('wrong-key-crc',bytes(changed),0,False,'PublicKeyCrc')
    changed=bytearray(original);changed[4:6]=struct.pack('<H',257)
    retain('wrong-signature-count',bytes(changed),0,False,'SignatureLength')
    signed=tree(4032)
    signature=run(['openssl','dgst','-sha256','-sign',str(OUT/'synthetic-only-private.pem')],bytes(signed))
    retain('wrong-digest-sha256',struct.pack('<IH',key_crc,256)+signature+bytes(signed),0,False,'SignatureInvalid')
    signature=run(['openssl','dgst','-sha512','-sign',str(OUT/'synthetic-only-private.pem'),
                   '-sigopt','rsa_padding_mode:pss','-sigopt','rsa_pss_saltlen:0'],bytes(signed))
    retain('wrong-rsa-padding-pss',struct.pack('<IH',key_crc,256)+signature+bytes(signed),0,False,'SignatureInvalid')
    # Signed malformed framing: a real RSA verification succeeds before the
    # bounded structural rejection, isolating the parser from authenticity.
    malformed=[('bad-magic',0,lambda b:b.__setitem__(0,b[0]^1),'TreeMagic'),
               ('huge-root-count',0,lambda b:b.__setitem__(slice(51,55),b'\xff'*4),'RootCount'),
               ('presence-two',0,lambda b:b.__setitem__(55,2),'PresenceCanonical'),
               ('descriptor-oversized',0,lambda b:b.__setitem__(slice(56,60),b'\xff'*4),'DescriptorExtent'),
               ('descriptor-too-small',0,lambda b:b.__setitem__(slice(56,60),struct.pack('<I',4)),'DescriptorExtent'),
               ('unknown-tag',0,lambda b:b.__setitem__(slice(60,64),struct.pack('<I',0xffffffff)),'UnsupportedTag'),
               ('mandatory-two',0,lambda b:b.__setitem__(64,2),'MandatoryCanonical'),
               ('crc-leaf-wrong-size',0,lambda b:b.__setitem__(slice(60,64),struct.pack('<I',18)),'LeafExtent'),
               ('rsa-leaf-wrong-size',0,lambda b:b.__setitem__(slice(60,64),struct.pack('<I',16)),'LeafExtent'),
               ('trailing-with-zero-roots',0,lambda b:b.__setitem__(slice(51,55),struct.pack('<I',0)),'TrailingBytes')]
    for name,pad,mutate,reason in malformed:
        signed=tree(4032-pad);mutate(signed);retain(name,sign(signed),pad,False,reason)
    # Canonical known leaf/absent-root shapes, with many absent roots as public
    # filler so the fixed aggregate length is preserved without trailing data.
    for tag in (18,16):
        body=struct.pack('<IBI',tag,1,0) if tag==18 else struct.pack('<IBIH',tag,1,2,0)
        head=b'\x01'+struct.pack('<I',len(body))+body
        absent=4032-262-51-4-len(head)
        signed=MAGIC+struct.pack('<I',1+absent)+head+b'\0'*absent
        retain('known-leaf-'+str(tag),sign(signed),0)
    # Deliberately CRC-ambiguous synthetic bytes: one fixed point for appending
    # a canonical byte01. No RSA/framing validity is required: selection must
    # reject ambiguity BEFORE using either interpretation.
    fixed=solve_affine(lambda c:zlib.crc32(b'\x01',c)^c,0)
    prefix=bytes(4027)
    patch=solve_affine(lambda n:crc(prefix+struct.pack('<I',n)),fixed)
    ambiguous=prefix+struct.pack('<I',patch)+b'\x01'
    need(crc(ambiguous)==crc(ambiguous[:-1])==fixed,'ambiguous whole/trim CRC collision')
    path=OUT/'ambiguous-crc.bin';path.write_bytes(ambiguous)
    fixtures.append({'name':'ambiguous-crc','path':path.name,'sha256':hashlib.sha256(ambiguous).hexdigest(),
                     'rawBytes':4032,'plaintextCrc32':f'{fixed:08x}','accepted':False,
                     'reason':'RepresentationAmbiguous','anchor':'primary'})
    # Pin every generated asset (including explicitly synthetic private keys)
    # so tests and reproduction never silently accept changed fixtures.
    assets={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='manifest.json'}
    (OUT/'manifest.json').write_text(json.dumps({'schema':'synthetic-only-swu-authentication-fixtures-v1',
        'actualPlaintextUsed':False,'crcProducer':'Python zlib.crc32','signer':'host OpenSSL RSA PKCS1 SHA512',
        'primary':anchor,'wrong':wrong_anchor,'fixtures':fixtures,'assets':assets},indent=2,sort_keys=True)+'\n')
    print(json.dumps({'syntheticFixtures':len(fixtures),'actualPlaintextUsed':False,'targetOperations':0}))

if __name__=='__main__':main()
