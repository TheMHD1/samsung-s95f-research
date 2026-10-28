#!/usr/bin/env python3
"""Central one-shot kernel extraction, private TLS output, no firmware install."""
import argparse,base64,hashlib,importlib.util,json,os,re,shlex,sys,threading,time
from pathlib import Path
import extraction
HERE=Path(__file__).resolve().parent;B=HERE.parent
TARGET=HERE/'target-1005';TRANSPORT=B/'swu-stream-transport-20261028cj';PRIVATE=HERE/'private/run-1005'
ADAPTER=B/'swu-stream-root-20261028cp/root-with-margin.py';ADAPTER_SHA='be9c5362fa40b52be2b824e6cc3e11013bdaafd44b1710f010bbccebac2bdc55'
BOOT='00000000-0000-4000-8000-000000000000';DOTNET_SHA='e5840c05c567183295f0bb37e3b28613618cec5e0c8c08a44a400672a1c73310'
STAGE='/tmp/swu-stream-20261028cq';ITEM=1005
PAYLOAD={n:TARGET/'bin/Release/net6.0'/n for n in ['SwuStreamTarget.dll','SwuStreamTarget.deps.json','SwuStreamTarget.runtimeconfig.json']}
PAYLOAD.update({n:TARGET/'private'/n for n in ['section-plan.bin','tls-config.json']})
def need(ok,why):
 if not ok:raise ValueError(why)
def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,obj):p.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n');p.chmod(0o600)
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def manifest():
 r=extraction.section(ITEM);need(PAYLOAD['section-plan.bin'].read_bytes()==extraction.binary_plan(r),'binary schema plan binding')
 paths=[Path(__file__),HERE/'extraction.py',ADAPTER,TRANSPORT/'section_server.py']+list(TARGET.glob('*.cs'))+list(TARGET.glob('*.csproj'))+[TARGET/'NuGet.Config']+list(PAYLOAD.values())+[PRIVATE/n for n in ['server-key.pem','server-cert.pem','connection-private.json','listener-port.json']]
 need(sha(ADAPTER.read_bytes())==ADAPTER_SHA,'root adapter drift')
 return {'schema':'swu-kernel-stream-deployment-v1','section':ITEM,'boot':BOOT,'stage':STAGE,'files':{str(p):{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(set(paths))},'scope':'One decrypt-only kernel item over certificate-pinned nonce-authenticated TLS.100sec native120remote150host. No firmware installation or UI/panel operations; no retries.'}
def guard():return f'set -eu\ntest "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\ntest "$(sha256sum /usr/bin/dotnet | cut -d " " -f1)" = {DOTNET_SHA}\n'
def stage_guard():return f'test ! -L {STAGE}\ntest -d {STAGE}\ntest "$(stat -c "%u:%g:%a" {STAGE})" = 0:0:700\n'
def exact(names):
 s=stage_guard()
 for n in sorted(names):
  remote=STAGE+'/'+n;s+=f'test ! -L {remote}\ntest -f {remote}\ntest "$(stat -c "%u:%g:%a" {remote})" = 0:0:600\n'
  if n in PAYLOAD:
   data=PAYLOAD[n].read_bytes();s+=f'test "$(wc -c < {remote})" = {len(data)}\ntest "$(sha256sum {remote} | cut -d " " -f1)" = {sha(data)}\n'
 s+='count=0\n'+f'for path in {STAGE}/* {STAGE}/.[!.]* {STAGE}/..?*; do\n'+'[ -e "$path" ] || [ -L "$path" ] || continue\n'+f'case "${{path##*/}}" in {"|".join(sorted(names))}) count=$((count+1));; *) exit 91;; esac\ndone\ntest "$count" = {len(names)}\n';return s
def parse_native(text):
 m=re.fullmatch(r'RUN_EXIT=([0-9]+)\nSTDOUT_BEGIN\n(.*?)STDOUT_END\nSTDERR_BEGIN\n(.*?)STDERR_END\n',text,re.S);need(m is not None,'native framing unknown, never retry')
 rows=[s for s in m[2].splitlines() if not s.startswith('[GC_INFO]')];need(int(m[1])==0 and m[3]=='' and len(rows)==1 and rows[0].startswith('SWU_STREAM_RAW '),'native rejected, never retry')
 parts=rows[0].split()[1:];need(len(parts)==len(set(p.split('=',1)[0] for p in parts)),'duplicate native field');f=dict(p.split('=',1) for p in parts)
 expected={'accepted':'1','first_failure':'None','code':'0x00000000','origin':'0xffffffff','calls0':'1','updates':'56','finals':'1','cipher':'3661840','raw':'3661840','confirmed':'3661840','eof':'1','digest':'1','closed':'1','released':'3','finalized':'1','wiped':'1','raw_complete':'1','guards':'62','cleanup_failures':'0','first_cleanup':'None','backend_exception':'0','ownership_uncertain':'0','payload_validated':'0','firmware_written':'0'}
 need(set(f)==set(expected)|{'elapsed_ms'},'native field set');need(all(f[k]==v for k,v in expected.items()) and f['elapsed_ms'].isdigit() and int(f['elapsed_ms'])<100000,'native counters/deadline');return f
def execute(out,digest):
 os.umask(0o077);mp=HERE/'deployment-1005.json';need(sha(mp.read_bytes())==digest and json.loads(mp.read_text())==manifest(),'deployment drift');need(out.is_absolute() and not out.exists(),'fresh private output')
 out.mkdir(parents=True,mode=0o700);(out/'runner-at-run.py').write_bytes(Path(__file__).read_bytes());(out/'deployment.json').write_bytes(mp.read_bytes())
 r=extraction.section(ITEM);root=load(ADAPTER,'co_fixed_root');record={'schema':'swu-kernel-stream-run-v1','calls':[],'invocations':0,'retries':0,'target_operation_state':'not_dispatched'}
 def call(cmd,label):save(out/'record.json',record);text=root.root(cmd,record,out/(label+'.json'));save(out/'record.json',record);return text
 call(guard()+f'test ! -e {STAGE}\ntest ! -L {STAGE}\numask 077\nmkdir {STAGE}\nchmod 700 {STAGE}\n','stage')
 for name,p in PAYLOAD.items():
  data=p.read_bytes();remote=STAGE+'/'+name
  call(guard()+stage_guard()+f'test ! -e {remote}\ntest ! -L {remote}\numask 077\n: > {remote}\nchmod 600 {remote}\n','create-'+name)
  for at in range(0,len(data),3072):
   chunk=base64.b64encode(data[at:at+3072]).decode();call(guard()+stage_guard()+f'test ! -L {remote}\ntest -f {remote}\ntest "$(wc -c < {remote})" = {at}\n'+f"printf '%s' '{chunk}' | base64 -d >> {remote}\n",f'upload-{name}-{at:06d}')
 server=load(TRANSPORT/'section_server.py','co_tls_server');client=json.loads(PAYLOAD['tls-config.json'].read_text());connection=json.loads((PRIVATE/'connection-private.json').read_text());need(client['certificate_sha256']==connection['certificate_sha256'] and client['nonce_hex']==connection['nonce_hex'],'private connection binding')
 ready=threading.Event();state={}
 def notify(info):state['ready']=info;ready.set()
 def serve():
  try:
   config=server.ServerConfig(source_path='${S95F_EVIDENCE_ROOT}/firmware-acquisition-20261028/T-RSMFAKUC-0090-upgrade.msd',source_offset=r['offset'],cipher_bytes=r['cipher_bytes'],cipher_sha256=r['cipher_sha256'],maximum_output_bytes=r['cipher_bytes'],certificate_path=str(PRIVATE/'server-cert.pem'),private_key_path=str(PRIVATE/'server-key.pem'),nonce=bytes.fromhex(client['nonce_hex']),output_directory=str(out/'transport'),bind_ipv4=client['server_ipv4'],port=client['server_port'],io_timeout_seconds=10,total_timeout_seconds=90)
   state['server_result']=server.serve(config,notify);save(out/'transport-result.json',state['server_result'])
  except Exception:state['host_server_exception']=True
  finally:ready.set()
 thread=threading.Thread(target=serve,name='fixed-kernel-tls',daemon=True);thread.start();need(ready.wait(5) and state.get('ready')=={'host':client['server_ipv4'],'port':client['server_port']},'host listener unavailable before invoke; stage retained')
 record.update(invocations=1,target_operation_state='inflight_or_unknown');save(out/'record.json',record)
 cmd=guard()+exact(PAYLOAD)+f'umask 077\nset +e\n/usr/bin/dotnet {STAGE}/SwuStreamTarget.dll > {STAGE}/stdout.txt 2> {STAGE}/stderr.txt\nrun_exit=$?\nset -e\ntest "$(wc -c < {STAGE}/stdout.txt)" -le 4096\ntest "$(wc -c < {STAGE}/stderr.txt)" -le 2048\nprintf "RUN_EXIT=%s\\n" "$run_exit"\nprintf "STDOUT_BEGIN\\n"\ncat {STAGE}/stdout.txt\nprintf "STDOUT_END\\nSTDERR_BEGIN\\n"\ncat {STAGE}/stderr.txt\nprintf "STDERR_END\\n"\n'
 text=call(cmd,'invoke-once');(out/'diagnostic.txt').write_text(text);fields=parse_native(text);thread.join(2);need(not thread.is_alive(),'server completion unknown')
 sr=state.get('server_result',{});need(sr.get('status')=='raw_complete' and sr.get('raw_complete') is True and sr.get('error_code')==0 and sr.get('cipher_bytes')==r['cipher_bytes'] and sr.get('raw_bytes')==r['cipher_bytes'] and sr.get('connections_accepted')==1,'server completion rejected')
 record['target_operation_state']='completed_raw';save(out/'record.json',record)
 result=extraction.validate_and_copy(out/'transport/raw-complete.bin',out/'seret.bin',r);result.update(accepted=True,native=fields,source_trial=out.name,firmware_written=False,retries=0);save(out/'result.json',result)
 names=set(PAYLOAD)|{'stdout.txt','stderr.txt'};cmd=guard()+exact(names)+'rm -- '+' '.join(shlex.quote(STAGE+'/'+n) for n in sorted(names))+f'\nrmdir -- {STAGE}\ntest ! -e {STAGE}\ntest ! -L {STAGE}\nprintf "STAGE_REMOVED\\n"\n';need(call(cmd,'cleanup')=='STAGE_REMOVED\n','cleanup unknown');save(out/'cleanup.json',{'stage_removed':True,'calls':len(record['calls'])})
 print(json.dumps({'accepted':True,'section':ITEM,'original_bytes':result['bytes'],'strict_padding_validated':True,'original_crc_validated':True,'elapsed_ms':int(fields['elapsed_ms']),'firmware_written':False}))
def main():
 p=argparse.ArgumentParser();p.add_argument('--write-manifest',action='store_true');p.add_argument('--execute',action='store_true');p.add_argument('--manifest-sha256');p.add_argument('--output',type=Path);a=p.parse_args()
 if a.write_manifest:need(not a.execute,'exclusive mode');save(HERE/'deployment-1005.json',manifest());print(sha((HERE/'deployment-1005.json').read_bytes()));return
 if a.execute:need(a.output is not None and a.manifest_sha256 is not None,'execution anchors');execute(a.output,a.manifest_sha256)
 else:print(json.dumps({'dry':True,'section':ITEM,'files':len(manifest()['files'])}))
if __name__=='__main__':main()
