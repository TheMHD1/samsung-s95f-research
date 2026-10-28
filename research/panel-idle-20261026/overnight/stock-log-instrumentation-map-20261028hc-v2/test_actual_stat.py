#!/usr/bin/env python3
"""Real host GNU stat/type predicates; never executes any capture command."""
import hashlib,json,os,stat,subprocess,sys,tempfile
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
from stock_log import capture_command,fetch_command,parse_capture,sha
checks=0

def need(v,why):
 global checks
 if not v:raise ValueError(why)
 checks+=1

def hoststat(path,fmt):
 p=subprocess.run(['stat','-c',fmt,str(path)],capture_output=True,timeout=5)
 need(p.returncode==0 and not p.stderr,'actual stat succeeded')
 return p.stdout.decode().strip()

def typecheck(path):
 # This executes only the two file-type predicates used in the generated guard,
 # against private host fixtures. It never runs dmesg, a root agent or the capture.
 p=subprocess.run(['/bin/sh','-c','[ ! -L "$1" ] && [ -f "$1" ]','hc-v2-type-fixture',str(path)],capture_output=True,timeout=5)
 need(not p.stdout and not p.stderr,'predicate has no output')
 return p.returncode==0

def main():
 with tempfile.TemporaryDirectory(dir=Path(os.environ.get('HC_TEST_TMPDIR',str(HERE/'private-tmp')))) as tmp:
  d=Path(tmp);os.chmod(d,0o700)
  empty=d/'stderr.raw';empty.write_bytes(b'');os.chmod(empty,0o600)
  data=d/'kernel.raw';data.write_bytes(b'actual bytes\n');os.chmod(data,0o600)
  need(hoststat(empty,'%F')=='regular empty file','real GNU empty file classification')
  need(hoststat(data,'%F')=='regular file','real GNU nonempty file classification')
  for p,n in [(empty,0),(data,13)]:
   need(typecheck(p),'explicit regular/nonlink type proof includes empty')
   expected=f'{os.getuid()}:{os.getgid()}:600:{n}'
   need(hoststat(p,'%u:%g:%a:%s')==expected,'actual numeric owner/mode/size independently checked')
   need((p.stat().st_mode&stat.S_IFMT(p.stat().st_mode))==stat.S_IFREG,'native stat confirms regular')
   if os.getuid()!=0 or os.getgid()!=0:
    need(hoststat(p,'%u:%g:%a:%s')!=f'0:0:600:{n}','production root owner guard would refuse nonroot host fixture')
  link=d/'link';link.symlink_to(empty);need(not typecheck(link),'symlink to regular rejected')
  need(not typecheck(d),'directory rejected as file')
  fifo=d/'fifo';os.mkfifo(fifo,0o600);need(not typecheck(fifo),'FIFO rejected without opening')
  need(not typecheck(d/'absent'),'absent file rejected')
  need(not typecheck('/dev/null'),'character device rejected without reading')
  os.chmod(empty,0o644);need(hoststat(empty,'%u:%g:%a')!=f'{os.getuid()}:{os.getgid()}:600','mode drift refused independently of type')
  need(typecheck(empty),'type check alone does not falsely imply private mode')
  os.chmod(empty,0o600)
  nonce='a'*32;boot='00000000-0000-0000-0000-000000000001'
  cap=capture_command(nonce,boot)
  need('%F'not in cap and '[ -f "$stage/kernel.raw" ]'in cap and '[ -f "$stage/stderr.raw" ]'in cap,'capture generated explicit type checks')
  need(cap.count("= '0:0:600' ]")==2,'capture retains exact root private mode')
  frame=('HC_CAPTURE_BEGIN\n'+f'nonce={nonce}\nboot={boot}\nprocUptimeBefore=1.00\nprocUptimeAfter=1.01\ndmesgExit=0\nrawBytes=13\nrawSha256={sha(data.read_bytes())}\nstderrBytes=0\nstderrSha256={sha(b"")}\nstageMode=0:0:700\nfileMode=0:0:600\nfileCount=2\nHC_CAPTURE_END\n').encode()
  receipt=parse_capture(frame,nonce,boot);fetch=fetch_command(receipt,'raw',0)
  need('%F'not in fetch and '[ -f "$stage/kernel.raw" ]'in fetch and '[ -f "$stage/stderr.raw" ]'in fetch,'fetch generated explicit type checks')
  need("= '0:0:600:0' ]"in fetch,'zero stderr size retained exactly')
  need('[ -d "$stage" ]'in fetch and "= '0:0:700' ]"in fetch,'directory type and private root mode retained')
 return dict(schema='hc-v2-actual-stat-host-v1',checks=checks,
  actualEmptyFileType='regular empty file',actualNonemptyFileType='regular file',
  executedOnlyHostFixtureStatAndTypePredicates=True,fullGeneratedCommandsExecuted=False,
  rootCaptureCalls=0,networkCalls=0,hostOwnerNotRewritten=True,
  ownerTestScope='numeric metadata equals actual host uid/gid; exact production root guard is separately retained and rejects nonroot fixtures')
if __name__=='__main__':print(json.dumps(main(),indent=2,sort_keys=True))
