#!/usr/bin/env python3
"""Fixed FK single-read staging/receipt adapter. Default is zero-I/O dry output."""
import argparse,base64,hashlib,json,os,re,shlex,types
from pathlib import Path
HERE=Path(__file__).resolve().parent;B=HERE.parent
FK=B/'tcon-log-single-read-20261028fk'
CHECKPOINT_SHA='edf69678846b979d8e0be85e12745ce51e966d6bb0c0e9c96c11f152c180906c'
FK_INVENTORY_SHA='b59247fb9344d5ded74869a7dad1a1d5fdde5f1b73431bb882eb65a3081d3c2c'
PARSER_SHA='79b8b027891a9fdbaeeda1ba2d1bedc2cdbb3ad469b726c23ad3032207a1e43a'
ROOT=B/'managed-ui-tab-launch/root-with-margin.py'
ROOT_SHA='bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a'
BOOT='00000000-0000-4000-8000-000000000000';KERNEL='5.4.261'
MODULE='/lib/modules/5.4.261/kernel/soc/sdp_tcon.ko'
MODULE_SHA='9b7c1cb8e2bb8d11e5465a41fa402e71bd8d15a5dabd6b3d76de98a7a42549ee'
DOTNET_SHA='e5840c05c567183295f0bb37e3b28613618cec5e0c8c08a44a400672a1c73310'
TARGET='/sys/kernel/debug/tcon/tcon_micom_log'
STAGE='/tmp/tcon-log-single-read-20261028fk'
NAMES=['TconLogSingleRead'+s for s in ['.dll','.deps.json','.runtimeconfig.json']]
OUTPUTS=['read.receipt.json','native.stdout','native.stderr']
MAX_COMMAND=8192;MAX_RESPONSE=65536;RECEIPT_CAP=16384;STDOUT_CAP=4096;STDERR_CAP=2048
SOURCES=['run-once.py','test-host.py','verify-source.py','finalize.py','build-host.sh','README.md','input-pins.json','host-build-checkpoint.json']

def need(v,s):
 if not v:raise ValueError(s)
def sha(b):return hashlib.sha256(b).hexdigest()
def strict(raw):
 def pairs(items):
  v={}
  for k,x in items:need(k not in v,'duplicate JSON field');v[k]=x
  return v
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:need(False,'nonfinite JSON'))
def load_pinned(path,digest,name):
 b=path.read_bytes();need(sha(b)==digest,'local pin '+str(path));m=types.ModuleType(name);m.__file__=str(path);exec(compile(b,str(path),'exec'),m.__dict__);return m
def private_bytes(path,b):
 fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb')as f:f.write(b);f.flush();os.fsync(f.fileno())
def save(path,v):private_bytes(path,(json.dumps(v,sort_keys=True,indent=2)+'\n').encode())
def row(path):
 b=path.read_bytes();return {'bytes':len(b),'sha256':sha(b)}
def build_manifest():
 checkpoint=(FK/'host-build-checkpoint.json').read_bytes();need(sha(checkpoint)==CHECKPOINT_SHA,'sealed FK checkpoint')
 cp=strict(checkpoint);need(cp['schema']=='fk-host-build-checkpoint-v1'and cp['actualTargetReadPerformed']is False,'FK checkpoint scope')
 need(sha((FK/'source-inventory.json').read_bytes())==FK_INVENTORY_SHA,'sealed FK inventory')
 need(sha((FK/'parse-receipt.py').read_bytes())==PARSER_SHA,'FK parser pin')
 payload={}
 for r in cp['payload']:
  path=FK/r['path'];b=path.read_bytes();need(row(path)=={'bytes':r['bytes'],'sha256':r['sha256']},'FK payload pin');need(path.name in NAMES,'fixed payload names');payload[path.name]=b
 need(set(payload)==set(NAMES)and sum(map(len,payload.values()))==33431,'fixed three payloads/33431 bytes')
 for r in strict((HERE/'input-pins.json').read_bytes())['files']:
  need(row(B/r['path'])=={'bytes':r['bytes'],'sha256':r['sha256']},'external source pin '+r['path'])
 need(sha(ROOT.read_bytes())==ROOT_SHA,'root adapter pin')
 manifest={'schema':'fp-tcon-single-read-manifest-v1','fkCheckpointSha256':CHECKPOINT_SHA,'fkInventorySha256':FK_INVENTORY_SHA,'fkParserSha256':PARSER_SHA,'rootAdapterSha256':ROOT_SHA,'payload':{n:row(FK/'bin/Release/net6.0'/n)for n in NAMES},'sources':{n:row(HERE/n)for n in SOURCES},'fixedStage':STAGE,'fixedReceipt':'read.receipt.json','fixedTarget':TARGET,'count':4096,'nativeInvocations':1,'targetReadsMaximum':1,'retries':0,'rootTimeoutSeconds':45,'hostTimeoutSeconds':75,'commandCap':MAX_COMMAND,'rootResponseCap':MAX_RESPONSE,'receiptCap':RECEIPT_CAP,'stdoutCap':STDOUT_CAP,'stderrCap':STDERR_CAP,'remoteFilesMaximum':6,'loadedModuleBytesAttested':False,'copyCompletionAttested':False,'completeLogProven':False,'externalRtpProducerProven':False,'timeoutOrRollbackGuaranteed':False,'physicalPictureObserved':False}
 return manifest,payload
def manifest_bytes(v):return (json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
def prefix():return 'set -eu\numask 077\ntest "$(id -u)" = 0\ntest "$(id -g)" = 0\n'+f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n'
def dir_guard():return f'test ! -L {STAGE}\ntest -d {STAGE}\ntest "$(stat -c "%u:%g:%a" {STAGE})" = 0:0:700\n'
def file_guard(name,size=None):
 need(name in NAMES+OUTPUTS,'fixed ordinary file');p=STAGE+'/'+name
 s=f'test ! -L {p}\ntest -f {p}\ntest "$(stat -c "%u:%g:%a" {p})" = 0:0:600\n'
 if size is not None:s+=f'test "$(wc -c < {p})" = {size}\n'
 return s
def inventory(names):
 need(len(names)==len(set(names))and set(names)<=set(NAMES+OUTPUTS),'fixed inventory')
 cases='|'.join(shlex.quote(n)for n in sorted(names))or'__NO_ENTRY_ALLOWED__'
 return f'count=0\nfor item in {STAGE}/* {STAGE}/.[!.]* {STAGE}/..?*; do\n  test -e "$item" || test -L "$item" || continue\n  name=${{item##*/}}\n  case "$name" in {cases}) ;; *) exit 91 ;; esac\n  count=$((count+1))\ndone\ntest "$count" = {len(names)}\n'
def integrity(contents):
 s=dir_guard()+inventory(list(contents))
 for n,b in contents.items():s+=file_guard(n,len(b))+f'test "$(sha256sum {STAGE}/{n} | cut -d " " -f1)" = {sha(b)}\n'
 return s

def metadata_body():
 # Metadata and ordinary on-disk file contents only: never open/read TARGET here.
 s=f'test "$(uname -r)" = {KERNEL}\n'
 s+='fp_mount=$(awk \'$2=="/sys/kernel/debug" {print $1,$2,$3}\' /proc/mounts)\ntest "$fp_mount" = "debugfs /sys/kernel/debug debugfs"\n'
 s+='fp_module=$(awk \'$1=="sdp_tcon" {n++; if ($5!="Live") exit 92; print} END {if(n!=1) exit 93}\' /proc/modules)\n'
 for p in ['/sys/kernel/debug','/sys/kernel/debug/tcon']:
  s+=f'test ! -L {p}\ntest -d {p}\ntest "$(stat -c "%u:%g:%a" {p})" = 0:0:755\n'
 s+=f'test ! -L {TARGET}\ntest -f {TARGET}\ntest "$(stat -c "%u:%g:%a:%s" {TARGET})" = 0:0:644:0\n'
 s+=f'test ! -L {MODULE}\ntest -f {MODULE}\ntest "$(stat -c "%u:%g:%a:%s" {MODULE})" = 0:0:644:226262\n'
 s+=f'fp_module_sha=$(sha256sum {MODULE} | cut -d " " -f1)\ntest "$fp_module_sha" = {MODULE_SHA}\n'
 s+='echo FP_METADATA_BEGIN\ncat /proc/sys/kernel/random/boot_id\nuname -r\necho "$fp_mount"\necho "$fp_module"\n'
 for p in ['/sys/kernel/debug','/sys/kernel/debug/tcon']:s+=f'stat -c "%u:%g:%a" {p}\n'
 s+=f'stat -c "%u:%g:%a:%s" {TARGET}\nstat -c "%u:%g:%a:%s" {MODULE}\necho "$fp_module_sha"\necho FP_METADATA_END\n'
 return s

def parse_metadata(text):
 lines=text.splitlines();need(len(lines)==11 and lines[0]=='FP_METADATA_BEGIN'and lines[-1]=='FP_METADATA_END','fresh metadata framing')
 need(lines[1]==BOOT and lines[2]==KERNEL and lines[3]=='debugfs /sys/kernel/debug debugfs','fresh boot/kernel/debugfs mount')
 m=lines[4].split();need(len(m)in [6,7]and m[0]=='sdp_tcon'and m[1].isdigit()and m[2].isdigit()and m[4]=='Live'and re.fullmatch(r'0x[0-9a-f]+',m[5])is not None and(len(m)==6 or re.fullmatch(r'\([A-Z]+\)',m[6])is not None),'sdp_tcon unique listed Live')
 need(lines[5:9]==['0:0:755','0:0:755','0:0:644:0','0:0:644:226262']and lines[9]==MODULE_SHA,'fresh fixed path/module metadata/hash')
 return {'schema':'fp-runtime-metadata-v1','boot':lines[1],'kernel':lines[2],'moduleListedLive':True,'onDiskModuleSha256':lines[9],'onDiskModuleBytes':226262,'debugfsNodeMetadataQualified':True,'loadedModuleBytesAttested':False,'metadataSnapshotAtomic':False}

def split_run(text):
 at=text.find('FP_METADATA_END\n');need(at>=0,'immediate metadata missing');end=at+len('FP_METADATA_END\n');meta=parse_metadata(text[:end]);return meta,text[end:]
def parse_envelope(raw):
 need(type(raw)is str and len(raw.encode())<=MAX_RESPONSE,'terminal envelope bound')
 pattern=(r'FP_RUN_BEGIN\n([^\n]+)\n([^\n]+)\n([0-9]+)\n([01])\n'+r'([0-9]+)\n([0-9a-f]{64})\n'*3+r'FP_RUN_META_END\nRECEIPT_B64_BEGIN\n([A-Za-z0-9+/=\n]*)RECEIPT_B64_END\nSTDOUT_B64_BEGIN\n([A-Za-z0-9+/=\n]*)STDOUT_B64_END\nSTDERR_B64_BEGIN\n([A-Za-z0-9+/=\n]*)STDERR_B64_END\nFP_RUN_COMPLETE\n')
 m=re.fullmatch(pattern,raw);need(m is not None,'terminal framing');g=m.groups();need(g[0]==BOOT and re.fullmatch(r'[0-9]+\.[0-9]+ [0-9]+\.[0-9]+',g[1])is not None,'terminal boot/uptime');need(0<=int(g[2])<=255,'terminal exit')
 blobs=[]
 for i,cap in enumerate([RECEIPT_CAP,STDOUT_CAP,STDERR_CAP]):
  n=int(g[4+2*i]);digest=g[5+2*i];encoded=g[10+i].replace('\n','');b=base64.b64decode(encoded,validate=True)
  need(base64.b64encode(b).decode()==encoded and len(b)==n<=cap and sha(b)==digest,'terminal extent/hash/cap');blobs.append(b)
 present=g[3]=='1';need(present or blobs[0]==b'','missing receipt cannot contain bytes')
 return {'exitCode':int(g[2]),'receiptPresent':present,'boot':g[0],'uptime':g[1]},*blobs

def run_command(payload):
 s=prefix()+f'test "$(sha256sum /usr/bin/dotnet | cut -d " " -f1)" = {DOTNET_SHA}\n'+integrity(payload)+metadata_body()
 for n in OUTPUTS:s+=f'test ! -e {STAGE}/{n}\ntest ! -L {STAGE}/{n}\n'
 s+=f': > {STAGE}/native.stdout\n: > {STAGE}/native.stderr\nchmod 600 {STAGE}/native.stdout {STAGE}/native.stderr\ncd {STAGE}\nset +e\n/usr/bin/dotnet {STAGE}/{NAMES[0]} --execute > {STAGE}/native.stdout 2> {STAGE}/native.stderr\nfp_native_rc=$?\nset -e\n'
 for n,cap in [('native.stdout',STDOUT_CAP),('native.stderr',STDERR_CAP)]:s+=file_guard(n)+f'test "$(wc -c < {STAGE}/{n})" -le {cap}\n'
 s+=f'if test -e {STAGE}/read.receipt.json || test -L {STAGE}/read.receipt.json; then\n'+file_guard('read.receipt.json')+f'test "$(wc -c < {STAGE}/read.receipt.json)" -le {RECEIPT_CAP}\nfp_receipt_present=1\n'+inventory(NAMES+OUTPUTS)+'else\nfp_receipt_present=0\n'+inventory(NAMES+['native.stdout','native.stderr'])+'fi\n'
 s+='echo FP_RUN_BEGIN\ncat /proc/sys/kernel/random/boot_id\ncat /proc/uptime\necho "$fp_native_rc"\necho "$fp_receipt_present"\n'
 s+=f'if test "$fp_receipt_present" = 1; then\nwc -c < {STAGE}/read.receipt.json\nsha256sum {STAGE}/read.receipt.json | cut -d " " -f1\nelse\necho 0\necho {sha(b"")}\nfi\n'
 for n in ['native.stdout','native.stderr']:s+=f'wc -c < {STAGE}/{n}\nsha256sum {STAGE}/{n} | cut -d " " -f1\n'
 s+='echo FP_RUN_META_END\necho RECEIPT_B64_BEGIN\n'+f'if test "$fp_receipt_present" = 1; then base64 {STAGE}/read.receipt.json; fi\n'+'echo RECEIPT_B64_END\n'
 for n,label in [('native.stdout','STDOUT'),('native.stderr','STDERR')]:s+=f'echo {label}_B64_BEGIN\nbase64 {STAGE}/{n}\necho {label}_B64_END\n'
 return s+'echo FP_RUN_COMPLETE\n'

def execute(output,reviewed_manifest,payload,root,parser):
 need(output.is_absolute()and not output.exists()and not output.is_symlink(),'fresh absolute private output')
 output.mkdir(parents=True,mode=0o700);record_path=output/'record.json'
 private_bytes(output/'reviewed-manifest.json',reviewed_manifest)
 record={'schema':'fp-wrapper-record-v1','manifestSha256':sha(reviewed_manifest),'fixedStage':STAGE,'calls':[],'phase':'preflight','nativeInvocations':0,'nativeInvocationStatus':'not_started','readMayHaveOccurred':False,'retries':0,'cleanupRequired':True,'loadedModuleBytesAttested':False}
 save(record_path,record)
 def call(command):
  need(0<len(command.encode())<=MAX_COMMAND,'root command cap')
  text=root.root(command,record,record_path);need(type(text)is str and len(text.encode())<=MAX_RESPONSE,'root response cap');return text
 try:
  raw=call(prefix()+metadata_body());private_bytes(output/'metadata-pre.txt',raw.encode());save(output/'metadata-pre.json',parse_metadata(raw))
  record['phase']='staging';save(record_path,record)
  made=call(prefix()+f'test ! -e {STAGE}\ntest ! -L {STAGE}\nmkdir -m 700 {STAGE}\n'+dir_guard()+inventory([])+'echo FP_STAGE_CREATED\n');need(made=='FP_STAGE_CREATED\n','fresh stage creation receipt')
  for n in NAMES:
   b=payload[n];encoded=base64.b64encode(b).decode();used=0
   for at in range(0,len(encoded),4500):
    chunk=encoded[at:at+4500];extent=len(base64.b64decode(chunk,validate=True))
    init=f'test ! -e {STAGE}/{n}\ntest ! -L {STAGE}/{n}\n: > {STAGE}/{n}\nchmod 600 {STAGE}/{n}\n'if at==0 else''
    command=prefix()+dir_guard()+init+file_guard(n,used)+f'printf %s {shlex.quote(chunk)} | base64 -d >> {STAGE}/{n}\n'+file_guard(n,used+extent)+'echo FP_STAGED_CHUNK\n'
    need(call(command)=='FP_STAGED_CHUNK\n','staged chunk receipt');used+=extent
   need(used==len(b),'staged extent')
   need(call(prefix()+dir_guard()+file_guard(n,len(b))+f'test "$(sha256sum {STAGE}/{n} | cut -d " " -f1)" = {sha(b)}\necho FP_STAGED_FILE\n')=='FP_STAGED_FILE\n','staged file receipt')
  # Mark submission before the only command that may invoke FK. Never retry this call.
  record.update(phase='native',nativeInvocations=1,nativeInvocationStatus='inflight_or_unknown',readMayHaveOccurred=True);save(record_path,record)
  text=call(run_command(payload));private_bytes(output/'native-envelope.txt',text.encode())
  immediate,envelope=split_run(text);save(output/'metadata-immediate.json',immediate)
  terminal,receipt,stdout,stderr=parse_envelope(envelope)
  for n,b in [('read.receipt.json',receipt),('native.stdout',stdout),('native.stderr',stderr)]:private_bytes(output/n,b)
  record.update(nativeTerminal=terminal,nativeInvocationStatus='terminal_receipt_retained',phase='parse_receipt',artifacts={n:row(output/n)for n in OUTPUTS});save(record_path,record)
  need(terminal['receiptPresent'],'native receipt missing; stage retained; no retry')
  native,interpretation=parser.parse(receipt);save(output/'interpretation.json',interpretation)
  allocation=base64.b64decode(native['rawAllocationBase64'],validate=True);private_bytes(output/'allocation.bin',allocation);private_bytes(output/'returned-prefix.bin',allocation[:native['returnedPrefixBytes']])
  record.update(nativeInvocationStatus='one_completed',nativeAccepted=native['accepted'],readAttempted=native['readAttempted'],phase='native_terminal_checked');save(record_path,record)
  need(native['accepted']is True and terminal['exitCode']==0 and stderr==b'','native acquisition refused; original receipt and diagnostics retained; no retry')
  remote=dict(payload);remote.update({'read.receipt.json':receipt,'native.stdout':stdout,'native.stderr':stderr})
  # Every raw artifact and diagnostic is local before the final ordinary-file integrity check.
  need(call(prefix()+integrity(remote)+'echo FP_FINAL_INTEGRITY_OK\n')=='FP_FINAL_INTEGRITY_OK\n','final integrity receipt')
  record['phase']='cleanup';save(record_path,record)
  command=prefix()+integrity(remote)+'rm -- '+' '.join(STAGE+'/'+n for n in NAMES+OUTPUTS)+f'\nrmdir -- {STAGE}\ntest ! -e {STAGE}\ntest ! -L {STAGE}\necho FP_STAGE_ABSENT\n'
  need(call(command)=='FP_STAGE_ABSENT\n','owned cleanup receipt')
  record.update(phase='complete',cleanupRequired=False);save(record_path,record)
  result={'schema':'fp-wrapper-result-v1','accepted':True,'nativeAccepted':True,'nativeInvocations':1,'readAttempted':native['readAttempted'],'returnedBytes':native['returnedPrefixBytes'],'allocationBytes':4096,'retries':0,'driverWrites':0,'cleanup':'FP_STAGE_ABSENT','cleanupRequired':False,'receiptSha256':sha(receipt),'manifestSha256':sha(reviewed_manifest),'loadedModuleBytesAttested':False,'copyCompletionAttested':False,'completeLogProven':False,'externalRtpProducerProven':False,'producerAtomicityProven':False,'physicalPictureObserved':False,'timeoutOrRollbackGuaranteed':False}
  save(output/'result.json',result);return result
 except Exception as e:
  record.update(failure=str(e)[:1024],failurePhase=record['phase']);save(record_path,record)
  save(output/'result.json',{'schema':'fp-wrapper-result-v1','accepted':False,'nativeAccepted':record.get('nativeAccepted'),'nativeInvocations':record['nativeInvocations'],'nativeInvocationStatus':record['nativeInvocationStatus'],'readMayHaveOccurred':record['readMayHaveOccurred'],'retries':0,'cleanupRequired':record['cleanupRequired'],'failure':record['failure'],'failurePhase':record['failurePhase'],'copyCompletionAttested':False,'producerAtomicityProven':False,'physicalPictureObserved':False,'completeLogProven':False,'externalRtpProducerProven':False,'loadedModuleBytesAttested':False,'timeoutOrRollbackGuaranteed':False})
  raise

def main():
 cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--execute',action='store_true');cli.add_argument('--print-manifest',action='store_true');cli.add_argument('--manifest-sha256');cli.add_argument('--checkpoint-sha256');cli.add_argument('--output',type=Path);args=cli.parse_args()
 need(not(args.execute and args.print_manifest),'one mode')
 if not args.execute and not args.print_manifest:
  print(json.dumps({'schema':'fp-dry-v1','targetReads':0,'rootCalls':0,'nativeInvocations':0,'plannedReadCount':4096,'plannedNativeInvocations':1,'explicitExecuteRequired':True,'retries':0},sort_keys=True));return
 manifest,payload=build_manifest();raw=manifest_bytes(manifest)
 if args.print_manifest:print(raw.decode(),end='');return
 need(args.manifest_sha256==sha(raw)and args.checkpoint_sha256==CHECKPOINT_SHA,'exact reviewed manifest and FK checkpoint pins required');need(args.output is not None,'fresh output path required')
 parser=load_pinned(FK/'parse-receipt.py',PARSER_SHA,'fp_frozen_fk_parser')
 root=load_pinned(ROOT,ROOT_SHA,'fp_serial_root')
 need(root.REMOTE_TIMEOUT_SECONDS==45 and root.HOST_TIMEOUT_SECONDS==75 and root.MAX_COMMAND==MAX_COMMAND and root.MAX_RESPONSE==MAX_RESPONSE,'root transport limits')
 print(json.dumps(execute(args.output,raw,payload,root,parser),sort_keys=True))
if __name__=='__main__':main()
