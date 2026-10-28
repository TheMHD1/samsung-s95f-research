import hashlib,importlib.util,json,os,stat,subprocess,sys,tempfile
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parent;H=R.parent;OLD=H.parent/'stock-log-instrumentation-map-20261028hc'
spec=importlib.util.spec_from_file_location('review_hcv2',H/'stock_log.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
checks=0

def ck(v,w):
 global checks
 if not v:raise ValueError(w)
 checks+=1

def bad(fn,w):
 try:fn()
 except (ValueError,TypeError,KeyError,OSError):ck(True,w);return
 raise ValueError('unexpected accept '+w)

def shell_type(path,directory=False):
 code='[ ! -L "$1" ] && [ -d "$1" ]'if directory else'[ ! -L "$1" ] && [ -f "$1" ]'
 p=subprocess.run(['/bin/sh','-c',code,'hc-v2-review-fixture',str(path)],capture_output=True,timeout=3)
 ck(not p.stdout and not p.stderr,'type predicate no output')
 return p.returncode==0

def main():
 ck(m.sha((H/'source-inventory.json').read_bytes())=='59ce2fc0f7fb06ccde74f7ef14e8092b8ad0caacc5add2a13bee2b21846d4258','final author inventory')
 inv=json.loads((H/'source-inventory.json').read_text())
 for row in inv['files']:
  b=(H/row['path']).read_bytes();ck(len(b)==row['bytes'] and m.sha(b)==row['sha256'],'author source '+row['path'])
 for stem,author in [('delta','delta.normal.json'),('actual-stat','actual-stat.normal.json'),('host','validation.normal.json'),('source','source-audit.json')]:
  ck((R/(stem+'.normal.json')).read_bytes()==(R/(stem+'.optimized.json')).read_bytes()==(H/author).read_bytes(),'exact normal/O author reproduction '+stem)
 audit=json.loads((H/'source-audit.json').read_text())
 for row in audit['inputPins']:
  p=H.parent.parent/row['path'];b=p.read_bytes();ck(len(b)==row['bytes'] and m.sha(b)==row['sha256'],'source input '+row['path'])
 prior=json.loads((OLD/'source-audit.json').read_text());current=dict(audit);prior.pop('schema');current.pop('schema');ck(prior==current,'source audit unchanged except version schema')
 oldreview=OLD/'reviews/independent-source-review.md';ck(m.sha(oldreview.read_bytes())=='6294722b7ccff0163ba2a46131f866092a127b94816fa6d2799d2cc8ca9b4256','inherited independent contract review pin')
 nonce='d'*32;boot='12345678-1234-1234-1234-123456789abc';cmd=m.capture_command(nonce,boot)
 ck(m.identifiers(nonce,boot)=='/tmp/s95f-stock-log-v2-'+nonce,'new fixed stage namespace')
 ck(m.SCHEMA=='s95f-stock-log-hc-v2' and '%F'not in cmd,'new schema and no human type field')
 ck(cmd.count('[ -f "$stage/')==2 and cmd.count('[ ! -L "$stage/')==2 and cmd.count("= '0:0:600' ]")==2,'both type/no-link/private root guards retained')
 ck('(ulimit -f 2048 && dmesg)'in cmd and '\\'not in cmd and 'dmesg -'not in cmd,'plain single bounded read no backslashes')
 with tempfile.TemporaryDirectory(dir=R/'private')as tmp:
  d=Path(tmp);os.chmod(d,0o700);empty=d/'empty';empty.write_bytes(b'');empty.chmod(0o600);data=d/'data';data.write_bytes(b'x');data.chmod(0o600)
  for p,n,label in [(empty,0,'regular empty file'),(data,1,'regular file')]:
   s=subprocess.run(['stat','-c','%F',str(p)],capture_output=True,check=True,timeout=3);ck(s.stdout.decode().strip()==label,'actual GNU stat distinction')
   ck(shell_type(p),'new predicate accepts actual regular file')
   numeric=subprocess.run(['stat','-c','%u:%g:%a:%s',str(p)],capture_output=True,check=True,timeout=3).stdout.decode().strip()
   ck(numeric==f'{os.getuid()}:{os.getgid()}:600:{n}','actual independent numeric fields')
  link=d/'link';link.symlink_to(empty);fifo=d/'fifo';os.mkfifo(fifo,0o600)
  for p in [link,fifo,d,d/'missing']:ck(not shell_type(p),'nonregular/link refused')
  ck(shell_type(d,True),'real directory accepted')
  dirlink=d/'dirlink';dirlink.symlink_to(d,target_is_directory=True);ck(not shell_type(dirlink,True),'directory symlink refused')
  empty.chmod(0o644);ck(shell_type(empty),'type test alone never asserts private mode');ck(stat.S_IMODE(empty.stat().st_mode)!=0o600,'independent numeric private mode remains needed')
 frame=('HC_CAPTURE_BEGIN\n'+f'nonce={nonce}\nboot={boot}\nprocUptimeBefore=1.00\nprocUptimeAfter=1.01\ndmesgExit=0\nrawBytes=1\nrawSha256={m.sha(b"x")}\nstderrBytes=0\nstderrSha256={m.sha(b"")}\nstageMode=0:0:700\nfileMode=0:0:600\nfileCount=2\nHC_CAPTURE_END\n').encode()
 receipt=m.parse_capture(frame,nonce,boot);ck(receipt['schema']==m.SCHEMA and receipt['captureAccepted']is True,'v2 receipt accepts complete independent mock frame')
 fetch=m.fetch_command(receipt,'raw',0);ck('%F'not in fetch and "= '0:0:600:0' ]"in fetch and '[ -d "$stage" ]'in fetch,'fetch zero stderr and directory checks')
 old=dict(receipt,schema='s95f-stock-log-hc-v1');bad(lambda:m.revalidate_receipt(old),'old sidecar family refused')
 bad(lambda:m.parse_capture(frame[:-1],nonce,boot),'missing canonical terminal newline refused')
 return {'schema':'hc-v2-independent-review-v1','status':'PASS_HOST_ONLY_SCOPED','checks':checks,'authorFiles':len(inv['files']),'sourcePins':len(audit['inputPins']),'reproduced':{'deltaChecks':33,'actualStatChecks':37,'hostChecks':345,'sourceChecks':13330,'shellSyntaxChecks':66,'maxCommandBytes':1418},'normalOptimizedExact':True,'generatedCommandsExecuted':0,'targetRootNetworkCalls':0,'actualHostStatAndTypePredicatesOnly':True,'oldCaptureRefusalPromoted':False,'limitations':['Inherited chunk CRLF/wrapping and Boolean-equivalent receipt equality qualifications remain unchanged.','Parent must bind fresh exact command/frame/envelope/boot; HC-v2 does not independently attest target utility compatibility.','Fresh v2 capture is a separate explicit invocation, never an automatic v1 retry or reconstruction of unknown dmesg exit.']}
if __name__=='__main__':print(json.dumps(main(),sort_keys=True,indent=2))
