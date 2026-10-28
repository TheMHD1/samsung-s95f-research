#!/usr/bin/env python3
"""Pure host model of established Core framing. Not a target/plaintext runner.

No file IO, crypto calls, signature/key output or accepted-applicability result.
Caller owns private buffer lifetime/wiping. Python is not a wipe-qualified target.
"""
from dataclasses import dataclass
import struct
import zlib

MAGIC=b'Tizen Software Upgrade Tree Binary Format ver. 1.9\0'
CIPHER_BYTES=4032
WRAPPER_PLAINTEXT_CRC=0xcbcf1d91
# Factory switch 0x2a0888; RTTI/vtables retained in descriptor-factory.json.
TAGS={1:'OUUpgradeItemDesc',2:'OUGroupDesc',7:'OUDataProcessingDesc',10:'OUPartitionVersionDesc',11:'OUSWFileVersionDesc',14:'OUAESEncryptionDesc',16:'OURSAValidationDesc',18:'OUCRC32ValidationDesc',19:'OUGroupInfoDesc',21:'OUFirmwareVersionDesc',25:'OUSWImageVersionDesc',35:'OUMetadataDesc',53:'OUBDiffPatchDesc',55:'OUSecureDowngradeDesc',56:'OUWildcardInfoDesc',57:'OUXZCompressionDesc',58:'OUOSUpgradeDesc',59:'OUPostponeDesc',60:'OUMultiBDiffPatchDesc',61:'OUSWDeviceTypeDesc',62:'OUOSUpgradeBaseVersionDesc'}
class Rejected(ValueError):
    """Message is a fixed diagnostic code, never content-derived."""

def need(ok,code):
    if not ok:raise Rejected(code)

@dataclass(frozen=True)
class PublicKeyAnchor:
    """Must come from independently pinned selected PEM, not decrypted fields."""
    crc32:int
    signature_bytes:int

class Reader:
    def __init__(self,data):self.data=memoryview(data);self.at=0
    def take(self,count):
        need(0<=count<=len(self.data)-self.at,'Truncated')
        at=self.at;self.at+=count
        return self.data[at:self.at]
    def integer(self,count):
        view=self.take(count)
        return int.from_bytes(view,'little')
    def done(self):need(self.at==len(self.data),'TrailingBytes')

def strict_padding_bytes(data):
    """Strict host policy. Stock detectPadding returns0 on zero/invalid padding."""
    need(len(data)>=16 and len(data)%16==0,'PaddingExtent')
    n=data[-1]
    need(1<=n<=16,'PaddingValue')
    need(all(x==n for x in memoryview(data)[len(data)-n:]),'PaddingPattern')
    return n

def model_unpadded(data,expected_crc,key_anchor):
    """Only the established framing subset; authenticity remains false always."""
    need(6+len(MAGIC)+4<=len(data)<=CIPHER_BYTES,'PlaintextExtent')
    need(0<=expected_crc<=0xffffffff,'CrcAnchor')
    need(zlib.crc32(data)&0xffffffff==expected_crc,'PlaintextCrc')
    need(isinstance(key_anchor,PublicKeyAnchor),'PublicKeyPinAbsent')
    need(0<=key_anchor.crc32<=0xffffffff and 0<key_anchor.signature_bytes<=CIPHER_BYTES-6-len(MAGIC)-4,'PublicKeyAnchor')
    r=Reader(data)
    need(r.integer(4)==key_anchor.crc32,'PublicKeyCrc')
    declared=r.integer(2)
    need(declared==key_anchor.signature_bytes,'SignatureLength')
    # Stock reads expected-key signature extent, then compares declared length.
    r.take(key_anchor.signature_bytes)
    signed_begin=r.at
    need(r.take(len(MAGIC))==MAGIC,'TreeMagic')
    count=r.integer(4)
    # A root can be absent, which still consumes one presence byte.
    need(count<=len(r.data)-r.at,'RootCount')
    records=[]
    for index in range(count):
        present=r.integer(1)
        # Canonical boolean is a strict model policy; stock branches nonzero.
        need(present in (0,1),'PresenceCanonical')
        if not present:
            records.append({'index':index,'present':False});continue
        record_offset=r.at
        body_size=r.integer(4)
        need(body_size>=5,'DescriptorMinimum')
        body=Reader(r.take(body_size))
        tag=body.integer(4)
        need(tag in TAGS,'UnsupportedDescriptorTag')
        mandatory=body.integer(1)
        need(mandatory in (0,1),'MandatoryCanonical')
        details={'index':index,'present':True,'offset':record_offset,'body_bytes':body_size,'tag':tag,'type':TAGS[tag],'mandatory':bool(mandatory)}
        if tag==18:
            # Core serializer0x2a243c: commonflag + raw little-endian u32 CRC.
            body.integer(4);body.done();details['leaf_layout_checked']=True
        elif tag==16:
            # Core serializer0x2a7550: commonflag + u32 algorithm + u16 siglen + sig.
            body.integer(4);signature_size=body.integer(2)
            body.take(signature_size);body.done();details['leaf_layout_checked']=True
            details['signature_bytes']=signature_size
        else:
            # No guessed payload field names, values or nested interpretation.
            details['leaf_layout_checked']=False
        records.append(details)
    r.done()
    return {'framing_subset_checked':True,'full_schema_validated':False,'signature_authenticity_validated':False,'metadata_published':False,'signed_span_offset':signed_begin,'signed_span_bytes':len(data)-signed_begin,'root_count':count,'records':records}

def model_fixed_padded(data,key_anchor):
    """Fixed4032B raw command output model; no key pin means mandatory refusal."""
    need(len(data)==CIPHER_BYTES,'CipherOutputExtent')
    n=strict_padding_bytes(data)
    result=model_unpadded(memoryview(data)[:-n],WRAPPER_PLAINTEXT_CRC,key_anchor)
    result['padding_bytes']=n
    return result
