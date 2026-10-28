#!/usr/bin/env python3
"""One fixed ddr.init firmware decryption; no installation, no retry."""
import argparse,base64,hashlib,importlib.util,json,os,re,shlex,struct,zlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
B=HERE.parent
ADAPTER=B/'managed-ui-tab-launch/root-with-margin.py'
ADAPTER_SHA='bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a'
BOOT='00000000-0000-4000-8000-000000000000'
DOTNET_SHA='e5840c05c567183295f0bb37e3b28613618cec5e0c8c08a44a400672a1c73310'
STAGE='/tmp/swu-section-20261028ck'
CF=B/'swu-item-schema-20261028cf/private/section-descriptors.json'
CF_SHA='f7946a96e36bff095ea20e28b4aaea1e40901b3005f863188d2e05b0ff8a4ee8'
SOURCES=['Core.cs','Native.cs','Program.cs','PrivateRawSink.cs','SectionStream.cs','IntegrationTests.cs','SwuSectionTarget.csproj','NuGet.Config','run-once.py']
PAYLOAD={n:HERE/'bin/Release/net6.0'/n for n in ['SwuSectionTarget.dll','SwuSectionTarget.deps.json','SwuSectionTarget.runtimeconfig.json']}
PAYLOAD.update({n:HERE/'private'/n for n in ['ciphertext.bin','section-plan.bin']})
def need(ok,why):
 if not ok:raise ValueError(why)
def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,o):p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');p.chmod(0o600)
def host_plan():
 raw=CF.read_bytes();need(sha(raw)==CF_SHA,'frozen schema plan drift')
 r=next(x for x in json.loads(raw) if x['id']==1008)
 plan=PAYLOAD['section-plan.bin'].read_bytes();cipher=PAYLOAD['ciphertext.bin'].read_bytes()
 expected=struct.pack('<8sIQQI8s32s',b'SWUSEC01',r['id'],r['cipher_bytes'],r['expected_original_bytes'],r['expected_output_crc32'],bytes.fromhex(r['salt_bytes']['hex']),bytes.fromhex(r['cipher_sha256']))
 need(plan==expected and len(cipher)==166416 and sha(cipher)==r['cipher_sha256'],'fixed plan/cipher drift')
 need(r['ciphertext_sha512_rsa_verified'] and r['cmd0_p2']==[0,1] and r['cmd0_p3']==[1,513] and not r['compression_present'] and not r['patch_present'],'metadata scope')
 return r
def manifest():
 host_plan();paths=[HERE/n for n in SOURCES]+list(PAYLOAD.values())
 return {'schema':'swu-fixed-section-deployment-v1','boot':BOOT,'stage':STAGE,'section':1008,'schema_plan_sha256':CF_SHA,'root_adapter_sha256':ADAPTER_SHA,'target_dotnet_sha256':DOTNET_SHA,'files':{str(p.relative_to(HERE)):{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in paths},'scope':'One decrypt-only TEEC sequence, fixed166416 ciphertext, private raw quarantine; host strict16-byte padding/original166400 CRC validation; no firmware installation or UI/power control.'}
def guard():return f'set -eu\ntest "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\ntest "$(sha256sum /usr/bin/dotnet | cut -d " " -f1)" = {DOTNET_SHA}\n'
def stage_guard():return f'test ! -L {STAGE}\ntest -d {STAGE}\ntest "$(stat -c "%u:%g:%a" {STAGE})" = 0:0:700\n'
def exact(names):
 s=stage_guard()
 for n in sorted(names):
  p=STAGE+'/'+n;s+=f'test ! -L {p}\ntest -f {p}\ntest "$(stat -c "%u:%g:%a" {p})" = 0:0:600\n'
  if n in PAYLOAD:
   raw=PAYLOAD[n].read_bytes();s+=f'test "$(wc -c < {p})" = {len(raw)}\ntest "$(sha256sum {p} | cut -d " " -f1)" = {sha(raw)}\n'
 s+='count=0\n'+f'for path in {STAGE}/* {STAGE}/.[!.]* {STAGE}/..?*; do\n'+'[ -e "$path" ] || [ -L "$path" ] || continue\n'+f'case "${{path##*/}}" in {"|".join(sorted(names))}) count=$((count+1));; *) exit 91;; esac\ndone\ntest "$count" = {len(names)}\n'
 return s
def validate_raw(raw,r):
 need(len(raw)==166416,'raw extent');need(raw[-16:]==bytes([16])*16,'strict PKCS7 16')
 plain=raw[:-16];need(len(plain)==r['expected_original_bytes']==166400,'original extent')
 need(zlib.crc32(plain)==r['expected_output_crc32'],'original-item CRC')
 return plain
def parse_status(text):
 m=re.fullmatch(r'RUN_EXIT=([0-9]+)\nSTDOUT_BEGIN\n(.*?)STDOUT_END\nSTDERR_BEGIN\n(.*?)STDERR_END\n',text,re.S);need(m is not None,'native framing unknown; no retry')
 rows=[s for s in m[2].splitlines() if not s.startswith('[GC_INFO]')]
 need(int(m[1])==0 and m[3]=='' and len(rows)==1 and rows[0].startswith('SWU_SECTION_RAW '),'native result rejected; no retry')
 fields=dict(p.split('=',1) for p in rows[0].split()[1:])
 expected={'accepted':'1','first_failure':'None','code':'0x00000000','origin':'0xffffffff','calls0':'1','updates':'3','finals':'1','cipher':'166416','raw':'166416','confirmed':'166416','eof':'1','digest':'1','closed':'1','released':'3','finalized':'1','wiped':'1','raw_complete':'1','guards':'9','payload_validated':'0','firmware_written':'0'}
 need(fields==expected,'native counters rejected; no retry');return fields
def execute(out,digest):
 os.umask(0o077);mp=HERE/'deployment-manifest.json';need(sha(mp.read_bytes())==digest and json.loads(mp.read_text())==manifest(),'deployment identity')
 need(sha(ADAPTER.read_bytes())==ADAPTER_SHA,'root adapter identity');need(out.is_absolute() and not out.exists(),'fresh output')
 out.mkdir(parents=True,mode=0o700);(out/'runner-at-run.py').write_bytes(Path(__file__).read_bytes());(out/'deployment-manifest.json').write_bytes(mp.read_bytes())
 spec=importlib.util.spec_from_file_location('ci_root',ADAPTER);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 record={'schema':'swu-fixed-section-run-v1','calls':[],'invocations':0,'retries':0,'target_operation_state':'not_dispatched'}
 def call(cmd,label):save(out/'record.json',record);result=mod.root(cmd,record,out/(label+'.json'));save(out/'record.json',record);return result
 call(guard()+f'test ! -e {STAGE}\ntest ! -L {STAGE}\numask 077\nmkdir {STAGE}\nchmod 700 {STAGE}\n','stage')
 for name,p in PAYLOAD.items():
  raw=p.read_bytes();remote=STAGE+'/'+name
  call(guard()+stage_guard()+f'test ! -e {remote}\ntest ! -L {remote}\numask 077\n: > {remote}\nchmod 600 {remote}\n','create-'+name)
  for at in range(0,len(raw),3072):
   chunk=base64.b64encode(raw[at:at+3072]).decode();cmd=guard()+stage_guard()+f'test ! -L {remote}\ntest -f {remote}\ntest "$(wc -c < {remote})" = {at}\n'+f"printf '%s' '{chunk}' | base64 -d >> {remote}\n"
   call(cmd,f'upload-{name}-{at:06d}')
 record.update(invocations=1,target_operation_state='inflight_or_unknown');save(out/'record.json',record)
 cmd=guard()+exact(PAYLOAD)+f'umask 077\nset +e\n/usr/bin/dotnet {STAGE}/SwuSectionTarget.dll > {STAGE}/stdout.txt 2> {STAGE}/stderr.txt\nrun_exit=$?\nset -e\ntest "$(wc -c < {STAGE}/stdout.txt)" -le 4096\ntest "$(wc -c < {STAGE}/stderr.txt)" -le 2048\nprintf "RUN_EXIT=%s\\n" "$run_exit"\nprintf "STDOUT_BEGIN\\n"\ncat {STAGE}/stdout.txt\nprintf "STDOUT_END\\nSTDERR_BEGIN\\n"\ncat {STAGE}/stderr.txt\nprintf "STDERR_END\\n"\n'
 text=call(cmd,'invoke-once');(out/'diagnostic.txt').write_text(text);fields=parse_status(text);record['target_operation_state']='completed_raw';save(out/'record.json',record)
 names=set(PAYLOAD)|{'stdout.txt','stderr.txt','raw-output.bin'}
 pieces=[];expected_hash=None
 for at in range(0,166416,24576):
  index=at//24576
  cmd=guard()+exact(names)+f'test "$(wc -c < {STAGE}/raw-output.bin)" = 166416\nsha256sum {STAGE}/raw-output.bin\ndd if={STAGE}/raw-output.bin bs=24576 skip={index} count=1 2>/dev/null | base64\nsha256sum {STAGE}/raw-output.bin\n'
  text=call(cmd,f'fetch-private-raw-{index:03d}');lines=text.splitlines();need(len(lines)>=3 and re.fullmatch(r'[0-9a-f]{64}  '+re.escape(STAGE+'/raw-output.bin'),lines[0]) and lines[-1]==lines[0],'private fetch framing')
  digest=lines[0].split()[0]
  if expected_hash is None:expected_hash=digest
  need(digest==expected_hash,'raw file drift')
  chunk=base64.b64decode(''.join(lines[1:-1]),validate=True);need(len(chunk)==min(24576,166416-at),'private fetch chunk extent');pieces.append(chunk)
 raw=b''.join(pieces);need(sha(raw)==expected_hash,'private fetch digest')
 (out/'raw-output.bin').write_bytes(raw);plain=validate_raw(raw,host_plan());(out/'ddr.init').write_bytes(plain)
 result={'accepted':True,'section':1008,'cipher_bytes':166416,'raw_bytes':166416,'original_bytes':166400,'padding_bytes':16,'strict_padding_validated':True,'original_crc_validated':True,'ciphertext_rsa_verified':True,'native':fields,'firmware_written':False,'ui_or_panel_control':False,'retries':0}
 save(out/'result.json',result)
 cmd=guard()+exact(names)+'rm -- '+' '.join(shlex.quote(STAGE+'/'+n) for n in sorted(names))+f'\nrmdir -- {STAGE}\ntest ! -e {STAGE}\ntest ! -L {STAGE}\nprintf "STAGE_REMOVED\\n"\n'
 need(call(cmd,'cleanup')=='STAGE_REMOVED\n','cleanup result');save(out/'cleanup.json',{'stage_removed':True,'calls':len(record['calls'])});print(json.dumps({k:v for k,v in result.items() if k!='native'}))
def main():
 p=argparse.ArgumentParser();p.add_argument('--write-manifest',action='store_true');p.add_argument('--execute',action='store_true');p.add_argument('--manifest-sha256');p.add_argument('--output',type=Path);a=p.parse_args()
 if a.write_manifest:need(not a.execute,'exclusive action');save(HERE/'deployment-manifest.json',manifest());print(sha((HERE/'deployment-manifest.json').read_bytes()));return
 if a.execute:need(a.output is not None and a.manifest_sha256 is not None,'execution anchors');execute(a.output,a.manifest_sha256)
 else:print(json.dumps({'dry_run':True,'section':1008,'files':len(manifest()['files'])}))
if __name__=='__main__':main()
