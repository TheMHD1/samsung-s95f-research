#!/usr/bin/env python3
"""Offline retained CE audit. No root/target/network calls or plaintext/hash output."""
from pathlib import Path
import argparse,base64,hashlib,json,re,stat,struct,zipfile,zlib
from cryptography.hazmat.primitives import serialization,hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature
CE=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
ACQUISITION=CE.parents[2]/'firmware-acquisition-20261028'
checks=0

def need(ok,code):
 global checks
 if not ok:raise ValueError(code)
 checks+=1

def sha(data):return hashlib.sha256(data).hexdigest()
def file_sha(path):
 h=hashlib.sha256()
 with path.open('rb') as stream:
  for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()

def framing(signed):
 need(signed[:51]==b'Tizen Software Upgrade Tree Binary Format ver. 1.9\0','exact magic')
 count=struct.unpack_from('<I',signed,51)[0];at=55;present=0;leaves=0
 need(count<=len(signed)-at,'bounded root count')
 for _ in range(count):
  need(at<len(signed),'presence bounds');flag=signed[at];at+=1;need(flag in (0,1),'canonical presence')
  if not flag:continue
  present+=1;need(at+4<=len(signed),'length bounds');n=struct.unpack_from('<I',signed,at)[0];at+=4
  need(5<=n<=len(signed)-at,'body extent bounds');body=memoryview(signed)[at:at+n];at+=n;tag=struct.unpack_from('<I',body)[0]
  need(tag in {1,2,7,10,11,14,16,18,19,21,25,35,53,55,56,57,58,59,60,61,62},'source mapped outer tag');need(body[4] in (0,1),'canonical mandatory')
  if tag==18:need(n==9,'CRC leaf extent');leaves+=1
  if tag==16:need(n>=11 and struct.unpack_from('<H',body,9)[0]==n-11,'RSA leaf extent');leaves+=1
 need(at==len(signed),'exact selected signed remainder consumed')
 return count,present,leaves

def main(private):
 need(not private.is_symlink() and stat.S_IMODE(private.stat().st_mode)==0o700,'private directory0700')
 p=private/'authenticated-header-raw.bin';info=p.lstat()
 need(stat.S_ISREG(info.st_mode) and stat.S_IMODE(info.st_mode)==0o600 and info.st_nlink==1 and info.st_uid==private.stat().st_uid,'private raw regular0600 owner/link')
 raw=p.read_bytes();need(len(raw)==4032,'private raw4032')
 mb=(private/'deployment-manifest.json').read_bytes();need(sha(mb)=='041242c9551ba397385379ca4d21d293b3d3de9d9a6355d5528a8f46ce4223d0','reviewed manifest SHA')
 need(mb==(CE/'deployment-manifest.json').read_bytes(),'source/run manifest identical');m=json.loads(mb)
 for filename,meta in m['files'].items():
  data=(CE/filename).read_bytes();need(len(data)==meta['bytes'] and sha(data)==meta['sha256'],'reviewed18 files exact')
 runner=(private/'runner-at-run.py').read_bytes();need(sha(runner)=='ebecd87cab031f72f8a55314f7ba93b05a9782e887e744f058afebaa74746622' and runner==(CE/'run-once.py').read_bytes(),'reviewed at-run/source runner')
 rec=json.loads((private/'cleanup.json').read_text());need(rec['invocations']==1 and rec['retries']==0 and rec['native_exit']==0 and rec['target_operation_state']=='terminal_native_cleanup_reported','one completed native no retry')
 native=[];fetch=[];cleanup=[];staged={name:bytearray() for name in m['payload_names']}
 for i,c in enumerate(rec['calls']):
  cmd=c['command'];need(len(cmd.encode())==c['command_bytes']<=8192,'command cap')
  transport_stderr=c['transport_stderr']
  need(c['transport_exit']==0 and not c['host_timeout'] and transport_stderr['encoding']=='base64' and base64.b64decode(transport_stderr['data'],validate=True)==b'','transport completion')
  response=c['response'];need(response['authenticated'] is True and response['uid']==response['euid']==0,'authenticated response identity')
  rows=response['commands'];need(len(rows)==1 and rows[0]['command']==cmd,'single exact echo');row=rows[0]
  need(row['exit_code']==0 and row['stderr']=='' and row['timed_out'] is False,'target shell completion')
  need(not any(word in cmd for word in ['input_keyevent','SetPower','reboot','ftrace','vlogutil','run-power-cycle','/dev/bus/usb']),'no separate UI/controller/reset/collector')
  if '/usr/bin/dotnet '+m['stage']+'/SwuMetadataAdapter.dll > ' in cmd:native.append((i,row['stdout']))
  if 'PRIVATE_RAW_BASE64_BEGIN' in cmd:fetch.append((i,cmd,row['stdout']))
  if '\nrm -- ' in cmd:cleanup.append((i,cmd,row['stdout']))
  for encoded,path in re.findall(r"printf '%s' '([A-Za-z0-9+/=]+)' \| base64 -d >> ([^\n]+)",cmd):
   name=Path(path).name;need(name in staged and path==m['stage']+'/'+name,'fixed payload upload')
   chunk=base64.b64decode(encoded,validate=True);need(len(chunk)<=3072,'bounded upload');staged[name].extend(chunk)
 need(len(rec['calls'])==34 and len(native)==len(fetch)==len(cleanup)==1,'34 calls one native/fetch/cleanup')
 for filename,expected_count in [('invoke-once.json',32),('fetch-authenticated-private-header.json',33),('record.json',33)]:
  checkpoint=json.loads((private/filename).read_text());need(checkpoint['calls']==rec['calls'][:expected_count],'exact retained call-prefix checkpoint')
 need(native[0][0]<fetch[0][0]<cleanup[0][0],'invoke fetch cleanup order')
 for name,data in staged.items():
  source=CE/('header-envelope.bin' if name=='header-envelope.bin' else 'bin/Release/net6.0/'+name)
  need(bytes(data)==source.read_bytes(),'exact reconstructed uploaded bytes')
 diagnostic=(private/'diagnostic.txt').read_text();need(diagnostic==native[0][1],'exact saved native frame')
 frame=re.fullmatch(r'RUN_EXIT=0\nSTDOUT_BEGIN\n(.*?)STDOUT_END\nSTDERR_BEGIN\nSTDERR_END\n',diagnostic,re.S);need(frame is not None,'strict native frame empty stderr')
 lines=frame[1].splitlines();need(lines.count('SELECTOR result=0 value=0')==5,'five false-master checks')
 diag='SWU_METADATA_DIAGNOSTIC stage=quarantined result=0x00000000 origin=0x00000004 local=0 calls=1,1,1 counts=4032,0 observed=4032,0 closed=1 released=3 finalized=1 metadata_published=0'
 auth='SWU_HEADER_AUTH accepted=1 reason=None representation=CanonicalPkcs7 raw_bytes=4032 selected_bytes=4027 padding_bytes=5 root_count=12 present_roots=12 checked_leaves=0 signature_authenticity_validated=1 framing_subset_checked=1 full_schema_validated=0 metadata_published=0 private_raw_saved=1'
 need(lines.count(diag)==lines.count(auth)==1,'exact native sequence/auth/cleanup status')
 need(all(line in [diag,auth,'SELECTOR result=0 value=0'] or re.fullmatch(r'\[GC_INFO\] GC_(?:Start|End).*',line) for line in lines),'no other native content output')
 receipt=(private/'private-header-envelope.txt').read_text();need(receipt==fetch[0][2],'exact saved private fetch frame')
 match=re.fullmatch(r'PRIVATE_RAW_SHA256=([0-9a-f]{64})\nPRIVATE_RAW_BASE64_BEGIN\n([A-Za-z0-9+/=\n]+)PRIVATE_RAW_BASE64_END\n',receipt);need(match is not None,'strict private frame')
 decoded=base64.b64decode(''.join(match[2].split()),validate=True);need(decoded==raw and len(decoded)==4032 and sha(raw)==match[1],'exact decoded private count/hash/copy')
 need('0:0:600:4032' in fetch[0][1] and fetch[0][1].count('sha256sum '+m['stage']+'/authenticated-header-raw.bin')==2,'target mode size and before-after hash guards')
 need(sha(raw) in cleanup[0][1] and cleanup[0][2]=='STAGE_REMOVED\n' and 'rmdir '+m['stage'] in cleanup[0][1],'same private hash cleanup receipt')
 public=(CE.parent/'swu-public-key-20261028cc/itemsPublicRSAKey.txt').read_bytes()
 need(len(public)==426 and sha(public)=='ebf12ab9d4ef069e1a6030b8c3b117894746637715270f7e3d37d3cd737f71a3' and zlib.crc32(public)==0x860be2ed,'exact installed public-key pin')
 key=serialization.load_pem_public_key(public);need(key.key_size==2048,'RSA2048')
 n=raw[-1];need(1<=n<=16 and raw[-n:]==bytes([n])*n and n==5,'canonicalPKCS7 five-byte tail')
 need(zlib.crc32(raw)!=0xcbcf1d91 and zlib.crc32(raw[:-n])==0xcbcf1d91,'exactly one anchored whole CRC representation')
 selected=raw[:-n];need(len(selected)==4027 and struct.unpack_from('<IH',selected)==(0x860be2ed,256),'selected extent and prefix')
 signature=selected[6:262];signed=selected[262:]
 key.verify(signature,signed,padding.PKCS1v15(),hashes.SHA512());need(True,'independent actual SHA512 PKCS1 verification')
 need(zlib.crc32(signed)!=0xcbcf1d91,'whole CRC differs from signed-only CRC')
 roots,present,leaves=framing(signed);need((roots,present,leaves)==(12,12,0),'independent bounded roots match')
 invalid=[(signature,raw[262:],padding.PKCS1v15(),hashes.SHA512()),(signature,selected,padding.PKCS1v15(),hashes.SHA512()),(signature,signed[:-1],padding.PKCS1v15(),hashes.SHA512()),(signature,signed,padding.PKCS1v15(),hashes.SHA256()),(signature,signed,padding.PSS(mgf=padding.MGF1(hashes.SHA512()),salt_length=padding.PSS.MAX_LENGTH),hashes.SHA512()),(bytes([signature[0]^1])+signature[1:],signed,padding.PKCS1v15(),hashes.SHA512()),(signature,signed[:-1]+bytes([signed[-1]^1]),padding.PKCS1v15(),hashes.SHA512())]
 for sig,content,mode,digest in invalid:
  try:key.verify(sig,content,mode,digest)
  except InvalidSignature:need(True,'negative signature binding rejected')
  else:need(False,'invalid authentication accepted')
 summary=json.loads((private/'authentication-summary.json').read_text())
 need(summary=={'checkedLeaves':0,'fullSchemaValidated':False,'installedKeySignatureVerifiedIndependentlyOnHost':True,'installedKeySignatureVerifiedOnTv':True,'metadataPublished':False,'paddingBytes':5,'presentRoots':12,'rawBytes':4032,'representation':'CanonicalPkcs7','rootCount':12,'selectedBytes':4027},'summary independent agreement')
 result=json.loads((private/'result.json').read_text());need(result['sequence_completed'] and result['invocations']==1 and result['stage_removed'] and result['plaintext_saved_privately'] and result['signature_authenticity_validated'] and not result['metadata_validated'] and not result['full_schema_validated'] and not result['permanent_prevention'],'bounded result claims')
 main=ACQUISITION/'T-RSMFAKUC-0090-upgrade.msd';archive=ACQUISITION/'T-RSMFAKUC-0090_TB-RSWF4AKUC-0090.zip'
 need(main.stat().st_size==1493538434 and file_sha(main)=='790584c7a91391bc6e9964c8f1c4649c225d2f9e6aeffabfc5e58e8a64fb7fc3','full main MSD rehash')
 need(archive.stat().st_size==2439527748 and file_sha(archive)=='5891b5ac67157403a2cfa4541845cb68f4ddb263860f41bc874e41fb748d1f42','full official archive rehash')
 with main.open('rb') as stream:prefix=stream.read(65494)
 need(sha(prefix)=='01821f40cf70841649c856090e23b35be6173659fb54be11f3b661a3e37bf92d','known main prefix identity')
 need(prefix[234:4290]==(CE/'header-envelope.bin').read_bytes(),'deployed header exactly full main MSD interval')
 need(struct.unpack_from('<II',prefix,234)==(0xcbcf1d91,0xefed4e54) and prefix[242:250]==b'Salted__' and zlib.crc32(prefix[258:4290])==0xefed4e54,'encrypted wrapper CRC frame')
 with zipfile.ZipFile(archive) as bundle:
  member=[x for x in bundle.infolist() if x.filename=='T-RSMFAKUC-0090/image/upgrade.msd'];need(len(member)==1 and member[0].file_size==main.stat().st_size,'unique main archive member')
  with bundle.open(member[0]) as stream:prefix_from_archive=stream.read(65494)
  need(prefix_from_archive==prefix,'archive member/main/deployed prefix identical')
 out={'schema':'ce-target-authentication-independent-review-v1','checks':checks,'target_operations_by_reviewer':0,'retained_authenticated_shell_calls':len(rec['calls']),'native_invocations':1,'retries':0,'private_raw_regular0600':True,'private_directory0700':True,'private_raw_copy_sha_framing_matches':True,'raw_bytes':4032,'representation':'CanonicalPkcs7','padding_bytes':5,'selected_bytes':4027,'whole_plaintext_crc32':'cbcf1d91','installed_public_pem_bytes':426,'installed_public_pem_sha256':sha(public),'installed_public_pem_crc32':'860be2ed','rsa_bits':2048,'signature_bytes':256,'signed_span_begin':262,'signed_span_end_exclusive':4027,'signed_span_bytes':len(signed),'rsa_sha512_pkcs1_verified_independently':True,'negative_signature_bindings_rejected':len(invalid),'root_count':roots,'present_roots':present,'checked_leaves':leaves,'native_result_zero':True,'native_origin':4,'native_output_counts':[4032,0],'session_closed':True,'shared_released':3,'context_finalized':True,'stage_removed_receipt':True,'reviewed_dll_sha256':'4394d2e25a547ef6c096f67e552331880d3319819ff5087159d483a994aa4d3e','deployment_manifest_sha256':sha(mb),'runner_sha256':sha(runner),'full_archive_hash_reverified':True,'full_main_msd_hash_reverified':True,'deployed_encrypted_header_matches_archive_prefix':True,'full_schema_validated':False,'firmware_applicability_validated':False,'metadata_published':False,'private_plaintext_or_hash_reproduced':False}
 (OUT/'verification-summary.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--private-trial',type=Path,required=True);a=p.parse_args();main(a.private_trial)
