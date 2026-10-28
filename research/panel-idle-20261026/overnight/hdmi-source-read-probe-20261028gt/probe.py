#!/usr/bin/env python3
"""Fixed S95F cached current-source read; dry by default, no source selection."""
import argparse,hashlib,importlib.util,json,os,re,time
from decimal import Decimal
from pathlib import Path
P=Path(__file__).resolve().parent
B=P.parent
ROOT=B/'managed-ui-tab-launch/root-with-margin.py'
ROOT_SHA='bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a'
MODEL='QN77S95FAFXZC';BUILD='BUILD_ID=T-RSMFAKUC-0090-REL-202607141953'
KEYS=('memory/system/source_type','memory/eden/source/current_source')
MAX_COMMAND=8192;MAX_ROOT=65536;MAX_TEXT=12288;MAX_KEY_BYTES=4096
UUID=re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')
TARGET_FILES=(
('/usr/bin/vconftool','e4d04ac482f6a25133d7cd3be8f03fd6cf0b2106b0397aa13b094127a9ed6864'),
('/usr/bin/buxton2ctl','e3d05a7b592492fa8815c025328da4e9bc980269035dd778f4fcec5803fbd0d5'),
('/usr/lib/libbuxton2.so.1.1','e34a07cabf2748c3d180e131b068e8382b31e0f12dabe4d884471a7a738e55d4'),
('/bin/bash','5cf101248e6418ee72ab1144aed551beea0ae7aeda1dad78c7808f901b286bfe'),
('/lib/ld-2.30.so','c3d873492560ead2db138c3b4859210ce3b5fb2fef128decd84c9e6a587a966a'),
('/lib/libc-2.30.so','588d0362d99db1507cd66162570596c9dab5c43cdbe4faca009f9b514bf0c17b'))
# These are the source-query components, interpreter, loader and libc, not a
# full transitive runtime or already-loaded-code attestation.

def need(ok,message):
 if not ok:raise ValueError(message)
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(v):return (json.dumps(v,indent=2,sort_keys=True,ensure_ascii=True)+'\n').encode()
def save(path,value):
 with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as f:f.write(dump(value));f.flush();os.fsync(f.fileno())
def strict_json(text):
 def pairs(xs):
  d={}
  for k,v in xs:
   need(k not in d,'duplicate JSON key');d[k]=v
  return d
 def bad(v):raise ValueError('nonfinite JSON')
 return json.loads(text,object_pairs_hook=pairs,parse_constant=bad)
def check_boot(boot):need(type(boot)is str and UUID.fullmatch(boot)is not None,'canonical expected boot')

def command(boot):
 check_boot(boot)
 lines=['set -eu','set -o pipefail','PATH=/usr/bin:/bin; export PATH','LC_ALL=C; export LC_ALL','unset LD_PRELOAD LD_LIBRARY_PATH ENV BASH_ENV',
 'printf "GT_SOURCE_READ_BEGIN\\n"',f'test "$(cat /proc/sys/kernel/random/boot_id)" = {boot}',
 'cat /proc/sys/kernel/random/boot_id','cat /proc/uptime',
 'test "$(id -u)" = 0','test "$(id -ru)" = 0','printf "UID=0 EUID=0\\n"',
 'printf "SMACK_BEGIN\\n"','cat /proc/self/attr/current','printf "\\nSMACK_END\\n"',
 f'grep -Fx {BUILD} /etc/tizen-release','uname -r',
 'test "$(readlink -f /bin/sh)" = /bin/bash',
 'test "$(readlink -f /lib/ld-linux.so.3)" = /lib/ld-2.30.so',
 'test "$(readlink -f /lib/libc.so.6)" = /lib/libc-2.30.so',
 'test "$(readlink -f /usr/lib/libbuxton2.so.1)" = /usr/lib/libbuxton2.so.1.1',
 'sha256sum -c <<\'GT_SOURCE_FILE_PINS\'']
 lines += [digest+'  '+path for path,digest in TARGET_FILES]
 lines += ['GT_SOURCE_FILE_PINS','printf "GT_FILES_VERIFIED\\n"']
 for i,key in enumerate(KEYS,1):
  # pipefail preserves failure/SIGPIPE; bounded stdout retains incomplete data
  # for diagnosis. No target temporary files, retries or user-supplied keys.
  lines += [f'printf "GT_KEY_{i}_BEGIN\\n"',f'/usr/bin/vconftool get {key} | head -c {MAX_KEY_BYTES+1}',f'printf "\\nGT_KEY_{i}_END\\n"']
 lines += ['cat /proc/sys/kernel/random/boot_id','cat /proc/uptime','printf "GT_SOURCE_READ_END\\n"']
 c='\n'.join(lines)+'\n';need(len(c.encode())<=MAX_COMMAND,'fixed command bound');return c

def parse(text,boot):
 check_boot(boot)
 need(type(text)is str and 0<len(text.encode())<=MAX_TEXT and text.endswith('\n'),'bounded complete source response')
 need('\r' not in text and '\x00' not in text,'source response controls')
 rows=text.splitlines();i=0
 def take():
  nonlocal i
  need(i<len(rows),'source response truncated');v=rows[i];i+=1;return v
 def exact(v):need(take()==v,'expected source frame '+v)
 def uptime(v):
  need(re.fullmatch(r'[0-9]+\.[0-9]+ [0-9]+\.[0-9]+',v)is not None,'uptime shape');return Decimal(v.split()[0])
 exact('GT_SOURCE_READ_BEGIN');exact(boot);before=take();start=uptime(before);exact('UID=0 EUID=0');exact('SMACK_BEGIN');label=take()
 need(1<=len(label.encode())<=255 and re.fullmatch(r'[A-Za-z0-9_:.@/+-]+',label)is not None,'bounded observed SMACK label')
 # proc attribute implementations may include a newline; command adds one.
 if i<len(rows) and rows[i]=='':i+=1
 exact('SMACK_END');exact(BUILD);exact('5.4.261')
 for path,_ in TARGET_FILES:exact(path+': OK')
 exact('GT_FILES_VERIFIED');values=[]
 for n,key in enumerate(KEYS,1):
  exact(f'GT_KEY_{n}_BEGIN');row=take();need(0<len(row.encode())<=MAX_KEY_BYTES,'vconf row cap')
  # CLI emits a newline; fixed framing adds a second newline.
  exact('');exact(f'GT_KEY_{n}_END')
  prefix=key+', value = ';need(row.startswith(prefix),'exact vconf key order');values.append(row[len(prefix):])
 exact(boot);after=take();end=uptime(after);exact('GT_SOURCE_READ_END');need(i==len(rows),'source trailing data')
 need(0<=end-start<=10,'source observation uptime window')
 m=re.fullmatch(r'(0|[1-9][0-9]{0,4}) \(Int32\)',values[0]);need(m is not None,'source type exact Int32 row')
 source_type=int(m.group(1));need(source_type<=65535,'finite source type storage bound')
 suffix=' (String)';need(values[1].endswith(suffix),'current-source String row')
 encoded=values[1][:-len(suffix)];need(0<len(encoded.encode())<=MAX_KEY_BYTES,'nonempty current-source JSON')
 obj=strict_json(encoded);need(type(obj)is dict and 2<=len(obj)<=16,'bounded current-source object')
 for k,v in obj.items():
  need(type(k)is str and 1<=len(k)<=128 and type(v)is str and len(v.encode())<=2048,'flat bounded current-source strings')
  need(all(ord(c)>=32 and ord(c)!=127 for c in k+v),'source JSON controls')
 need(type(obj.get('source_type'))is str and 1<=len(obj['source_type'])<=128 and type(obj.get('uuid'))is str,'source_type/uuid fields')
 return {'schema':'gt-source-observation-v1','acceptedRead':True,'expectedModel':MODEL,'freshModelGetterPerformed':False,'boot':boot,'uptimeBefore':before,'uptimeAfter':after,'observedRootSmackLabel':label,'onDiskQueryComponentPinsVerified':True,'transitiveRuntimeAttested':False,'loadedBytesAttested':False,'cachedSourceType':source_type,'cachedPortCandidate':{13:'HDMI1',14:'HDMI2',15:'HDMI3',16:'HDMI4'}.get(source_type),'cachedCurrentSource':obj,'currentSourceKeysAtomic':False,'sourceListQueried':False,'primaryUgoosIdentified':False,'sourceSelectionPerformed':False,'physicalPictureObserved':False}

def manifest(boot):
 c=command(boot)
 return {'schema':'gt-fixed-source-read-manifest-v1','model':MODEL,'expectedBoot':boot,'build':BUILD,'probeSha256':sha(Path(__file__).read_bytes()),'rootAdapterSha256':ROOT_SHA,'inputPinsSha256':sha((P/'input-pins.json').read_bytes()),'commandSha256':sha(c.encode()),'commandBytes':len(c.encode()),'keys':list(KEYS),'rootCalls':1,'retries':0,'remoteTimeoutSeconds':45,'hostTimeoutSeconds':75,'commandCap':MAX_COMMAND,'rootEnvelopeCap':MAX_ROOT,'sourceTextCap':MAX_TEXT,'vconfRowCap':MAX_KEY_BYTES,'targetStagedFiles':0,'sourceSelectionCalls':0,'targetWrites':0,'transitiveRuntimeAttested':False,'loadedBytesAttested':False}

def check_inputs():
 d=json.loads((P/'input-pins.json').read_text())
 for f in d['files']:
  x=Path(f['path']);need(x.is_file() and x.stat().st_size==f['bytes'] and sha(x.read_bytes())==f['sha256'],'frozen input '+x.name)
 need(sha(ROOT.read_bytes())==ROOT_SHA,'root adapter pin')
def validate_root_record(record,c,text):
 need(type(record)is dict and type(record.get('calls'))is list and len(record['calls'])==1,'one retained actual root call')
 item=record['calls'][0];need(type(item)is dict and item.get('command')==c and type(item.get('transport_exit'))is int and item['transport_exit']==0 and item.get('host_timeout')is False,'actual root transport completion')
 need(item.get('remote_timeout_seconds')==45 and item.get('host_timeout_limit_seconds')==75,'actual root timing contract')
 response=item.get('response');need(type(response)is dict and response.get('model')==MODEL and response.get('authenticated')is True,'root-client model/authentication envelope')
 need(type(response.get('uid'))is int and type(response.get('euid'))is int and response['uid']==response['euid']==0,'root envelope UIDs')
 need(response.get('root_persistence')=='host-assisted' and response.get('global_system_files_unchanged_at_acquisition')is True,'root envelope contract')
 xs=response.get('commands');need(type(xs)is list and len(xs)==1 and type(xs[0])is dict,'root envelope one command')
 x=xs[0];need(x.get('command')==c and type(x.get('exit_code'))is int and x['exit_code']==0 and x.get('timed_out')is False and x.get('stderr')=='' and x.get('stdout')==text,'root envelope exact completed result')
 return {'rootEnvelopeModel':response['model'],'modelBinding':'validated root-client envelope; no fresh model getter'}

def run(output,boot,call):
 check_boot(boot);need(output.is_absolute() and not output.exists() and not output.is_symlink(),'new absolute private output')
 for parent in output.parents:need(not parent.is_symlink(),'output ancestor symlink')
 old=os.umask(0o077)
 try:output.mkdir(mode=0o700)
 finally:os.umask(old)
 c=command(boot);save(output/'manifest.json',manifest(boot));(output/'command.txt').write_bytes(c.encode());(output/'command.txt').chmod(0o600)
 start=time.monotonic_ns();save(output/'intent.json',{'schema':'gt-read-intent-v1','submitted':True,'rootCallsMaximum':1,'noRetries':True,'startedMonotonicNs':start})
 record={'schema':'gt-root-read-record-v1','calls':[]}
 try:
  text=call(c,record,output/'root.json');returned=time.monotonic_ns()
  if (output/'root.json').is_file():(output/'root.json').chmod(0o600)
  need(type(text)is str,'root returned text')
  # Retain returned data before semantic parser decisions, including refusal.
  with os.fdopen(os.open(output/'response.txt',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb')as f:f.write(text.encode());f.flush();os.fsync(f.fileno())
  need(0<=returned-start<=75000000000,'host observation clock/budget')
  binding=validate_root_record(record,c,text)
  result=parse(text,boot);result.update(**binding);result.update(commandSha256=sha(c.encode()),responseSha256=sha(text.encode()),startedMonotonicNs=start,returnedMonotonicNs=returned)
  save(output/'result.json',result);return result
 except Exception as exc:
  if (output/'root.json').is_file():(output/'root.json').chmod(0o600)
  save(output/'refusal.json',{'schema':'gt-read-refusal-v1','acceptedRead':False,'errorType':type(exc).__name__,'reason':str(exc)[:1024],'rootCallsRecorded':len(record.get('calls',[])),'noAutomaticRetry':True,'sourceSelectionPerformed':False});raise

def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--expected-boot',required=True);a.add_argument('--execute',action='store_true');a.add_argument('--manifest-sha256');a.add_argument('--output',type=Path);args=a.parse_args()
 check_inputs();m=manifest(args.expected_boot);digest=sha(dump(m))
 if not args.execute:
  print(dump({'manifest':m,'manifestSha256':digest,'fixedCommand':command(args.expected_boot),'execute':False}).decode(),end='');return
 need(args.manifest_sha256==digest,'explicit exact manifest digest');need(args.output is not None,'private output required')
 spec=importlib.util.spec_from_file_location('gt_pinned_root',ROOT);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 need((mod.MAX_COMMAND,mod.MAX_RESPONSE,mod.REMOTE_TIMEOUT_SECONDS,mod.HOST_TIMEOUT_SECONDS)==(8192,65536,45,75),'root adapter bounds')
 print(dump(run(args.output,args.expected_boot,mod.root)).decode(),end='')
if __name__=='__main__':main()
