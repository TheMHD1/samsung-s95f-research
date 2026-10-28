#!/usr/bin/env python3
"""Fixed private plan consistency check. Prints no salts/signatures/CRC values."""
from pathlib import Path
import hashlib,json,stat
R=Path(__file__).resolve().parent

def require(ok,code):
 if not ok:raise ValueError(code)

def main():
 p=R/'private/section-descriptors.json';raw=p.read_bytes();plans=json.loads(raw)
 require(type(plans)is list and len(plans)==9,'PlanCount')
 require([x['id'] for x in plans]==list(range(1001,1010)),'PlanIDs')
 expected_offset=4290
 for x in plans:
  require(x['offset']==expected_offset,'PlanContinuity');expected_offset+=x['cipher_bytes']
  require(x['name'].encode('ascii').hex()==x['name_bytes']['hex'],'NameEncoding')
  require(x['name_bytes']['bytes']==len(x['name']),'NameLength')
  require(x['salt_bytes']['bytes']==8 and len(bytes.fromhex(x['salt_bytes']['hex']))==8,'SaltLength')
  require(x['rsa_signature_bytes']['bytes']==256 and len(bytes.fromhex(x['rsa_signature_bytes']['hex']))==256,'SignatureLength')
  require(x['cipher_rsa_scope']['stage']=='ciphertext' and x['cipher_rsa_scope']['relative_offset']==0 and x['cipher_rsa_scope']['bytes']==x['cipher_bytes'],'RsaScope')
  require(x['output_crc_scope']['stage']=='original_item_bytes' and x['output_crc_scope']['relative_offset']==0 and x['output_crc_scope']['bytes']==x['expected_original_bytes'] and x['output_crc_scope']['padding_included'] is False,'CrcScope')
  require(x['cipher_bytes']==x['aes_processed_size'] and x['cipher_bytes']-x['expected_original_bytes']==16,'Lengths')
  require(x['processing_tags']==[18,14,16] and x['compression_present'] is False and x['patch_present'] is False,'ProcessingStages')
  require(x['ciphertext_sha512_rsa_verified'] is True and x['ciphertext_crc32_equals_tag18'] is False,'CipherChecks')
  require(x['inherited_crypto_info']==[1,2,1,2] and x['cmd0_p2']==[0,1] and x['cmd0_p3']==[1,513],'CryptoParams')
  require(x['master_binding']['bytes']==416 and x['master_binding']['selector'] is False and x['master_binding']['sha256']=='d8af420d63b9cb2643783c56ce7396a5fd4d809e48df0bd321781cfd025e8220','MasterBinding')
  require(x['payload_plaintext_validated'] is False and x['execution_qualified'] is False,'NoPromotion')
 require(expected_offset==1493538434,'MsdFinalExtent')
 require(stat.S_IMODE((R/'private').stat().st_mode)==0o700,'PrivateDirectoryMode')
 require(all(stat.S_IMODE(f.stat().st_mode)==0o600 for f in (R/'private').iterdir() if f.is_file()),'PrivateFileMode')
 print(json.dumps({'records':len(plans),'scope_and_binding_checks':'PASS','private_permissions':'0600 inside 0700','plan_bytes':len(raw),'plan_sha256':hashlib.sha256(raw).hexdigest(),'secret_values_printed':False}))
if __name__=='__main__':main()
