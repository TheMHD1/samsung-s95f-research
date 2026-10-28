#!/usr/bin/env python3
"""Independent HC host review: no target/root transport or generated shell execution."""
import base64, copy, hashlib, importlib.util, json, os, stat, sys, tempfile
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parent;H=R.parent
spec=importlib.util.spec_from_file_location('hc_review_stock_log',H/'stock_log.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
checks=0
N='b'*32;B='12345678-1234-1234-1234-123456789abc'
def ck(v,msg):
 global checks
 if not v:raise ValueError(msg)
 checks+=1
def bad(fn,msg):
 try:fn()
 except (ValueError,KeyError,TypeError,OSError,UnicodeError):ck(True,msg);return
 raise ValueError('admitted malformed input: '+msg)
def capture(raw,err=b'',rc=0):
 return ('HC_CAPTURE_BEGIN\n'+f'nonce={N}\nboot={B}\nprocUptimeBefore=100.00\nprocUptimeAfter=100.01\ndmesgExit={rc}\nrawBytes={len(raw)}\nrawSha256={m.sha(raw)}\nstderrBytes={len(err)}\nstderrSha256={m.sha(err)}\nstageMode=0:0:700\nfileMode=0:0:600\nfileCount=2\nHC_CAPTURE_END\n').encode()
def chunk(raw,kind='raw',index=0):
 piece=raw[index*m.CHUNK:(index+1)*m.CHUNK];encoded=base64.b64encode(piece).decode();wrapped='\n'.join(encoded[i:i+76]for i in range(0,len(encoded),76))
 return (f'HC_CHUNK_BEGIN\nnonce={N}\nkind={kind}\nindex={index}\noffset={index*m.CHUNK}\nbytes={len(piece)}\n'+wrapped+'\nHC_CHUNK_END\n').encode()
def main():
 inventory=json.loads((H/'source-inventory.json').read_text())
 ck(m.sha((H/'source-inventory.json').read_bytes())=='26c311d11a845dad76a02370259bb4ed997312406269da1df669c7f91d718621','final author seal')
 for p in inventory['files']:
  raw=(H/p['path']).read_bytes();ck(len(raw)==p['bytes'] and m.sha(raw)==p['sha256'],'author file '+p['path'])
 audit=json.loads((H/'source-audit.json').read_text())
 for p in audit['inputPins']:
  raw=(H.parent.parent/p['path']).read_bytes();ck(len(raw)==p['bytes'] and m.sha(raw)==p['sha256'],'source input '+p['path'])
 for stem,author in [('host','validation.normal.json'),('source','source-audit.json')]:
  ck((R/(stem+'.normal.json')).read_bytes()==(R/(stem+'.optimized.json')).read_bytes()==(H/author).read_bytes(),'independent normal/O exact '+stem)
 cmd=m.capture_command(N,B)
 ck(cmd.count('dmesg')==2 and '(ulimit -f 2048 && dmesg)'in cmd,'one executable dmesg plus metadata name')
 ck(all(x not in cmd for x in ['dmesg -','rm ','rmdir','chmod','tracing_on','ioctl','input_keyevent','\\']),'fixed nonclearing no-action command')
 ck('set -eu'in cmd and '[ "$(id -u)" = 0 ]'in cmd and cmd.count('/proc/sys/kernel/random/boot_id')==2,'shell UID and boot guards')
 ck(cmd.index('[ ! -e "$stage" ]')<cmd.index('mkdir -m 700 "$stage"')<cmd.index('dmesg)'),'exclusive stage before one read')
 raw=bytes(range(256))*66+b'\x00\xff\xfe[1.100] QDF Reset(2)\r\n';receipt=m.parse_capture(capture(raw),N,B)
 ck(receipt['captureAccepted']is True,'binary raw accepted by metadata')
 for index in range(2):
  f=chunk(raw,index=index);expected=raw[index*m.CHUNK:(index+1)*m.CHUNK]
  ck(m.parse_chunk(f,receipt,'raw',index)==expected,'actual base64 76-column wrapping')
  ck(len(f)<m.CHUNK_FRAME_CAP,'full wrapped frame cap')
 good=chunk(raw)
 for mutated in [good.replace(b'kind=raw',b'kind=stderr'),good.replace(b'index=0',b'index=1'),good.replace(b'offset=0',b'offset=16384'),good.replace(N.encode(),b'c'*32),good+b'HC_CHUNK_END\n',b'x\n'+good,good.replace(b'HC_CHUNK_END',b'HC_CHUNK_OTHER'),good[:100],bytes(m.CHUNK_FRAME_CAP+1)]:bad(lambda:m.parse_chunk(mutated,receipt,'raw',0),'chunk binding/frame mutation')
 for mutated in [capture(raw).replace(b'fileMode=0:0:600',b'fileMode=0:0:666'),capture(raw).replace(b'dmesgExit=0',b'dmesgExit=256'),capture(raw).replace(b'rawBytes=',b'rawBytes=0'),capture(raw).replace(b'procUptimeAfter=100.01',b'procUptimeAfter=NaN'),capture(raw).replace(b'HC_CAPTURE_END',b'HC_CAPTURE_END\nx=1')]:bad(lambda:m.parse_capture(mutated,N,B),'capture scalar/frame mutation')
 for value in [True,-1,2]:bad(lambda:m.fetch_command(receipt,'raw',value),'index extent/type')
 zero=m.parse_capture(capture(b''),N,B);ck(zero['captureAccepted']is True,'zero-byte snapshot explicitly allowed, not completeness')
 for kind in ['raw','stderr']:bad(lambda:m.fetch_command(zero,kind,0),'zero-size has no fetch')
 with tempfile.TemporaryDirectory(dir=R/'private')as temp:
  root=Path(temp);os.chmod(root,0o700);chunks=root/'chunks';chunks.mkdir(mode=0o700)
  for i in range(2):p=chunks/f'raw-{i:02d}.txt';p.write_bytes(chunk(raw,index=i));p.chmod(0o600)
  original=m.classify;fsync=m.os.fsync;events=[]
  def sync(fd):events.append(('fsync',stat.S_ISDIR(os.fstat(fd).st_mode)));return fsync(fd)
  def classify(blob):
   ck(blob==raw and (root/'archive/kernel.raw').read_bytes()==raw,'classification sees preserved original bytes')
   ck(events[:3]==[('fsync',False),('fsync',False),('fsync',True)],'both raw files and directory fsynced before classifier')
   return original(blob)
  m.os.fsync=sync;m.classify=classify
  try:out=m.archive(receipt,chunks,root/'archive')
  finally:m.os.fsync=fsync;m.classify=original
  ck(out['captureAccepted']is True and out['classification']['physicalRecoveryProven']is False,'archive acceptance and physical limitation')
  ck(all(stat.S_IMODE(p.stat().st_mode)==0o600 for p in (root/'archive').iterdir()),'all archive artifacts mode0600')
  def fail(blob):raise ValueError('independent classifier failure')
  m.classify=fail
  try:bad(lambda:m.archive(receipt,chunks,root/'classifier-failure'),'classifier failure retained')
  finally:m.classify=original
  ck((root/'classifier-failure/kernel.raw').read_bytes()==raw and (root/'classifier-failure/stderr.raw').read_bytes()==b'','raw retained despite classifier failure')
  ck(not(root/'classifier-failure/analysis.json').exists(),'failure not promoted into analysis')
  bad(lambda:m.archive(receipt,chunks,root/'classifier-failure'),'partial archive never overwritten')
  refused=m.parse_capture(capture(raw,b'warning\n',0),N,B)
  p=chunks/'stderr-00.txt';p.write_bytes(chunk(b'warning\n','stderr'));p.chmod(0o600)
  out=m.archive(refused,chunks,root/'refused')
  ck(out['archiveVerified']is True and out['captureAccepted']is False and out['captureReceipt']['refusalReasons']==['dmesg stderr is nonempty'],'successful forensic archival preserves original refusal')
 # Frame line endings/wrapping may be normalized by splitlines; payload canonicality/hash is still exact.
 ck(m.parse_chunk(good.replace(b'\n',b'\r\n'),receipt,'raw',0)==raw[:m.CHUNK],'CRLF chunk framing accepted with exact payload; not a canonical-frame claim')
 # Revalidate equality permits Boolean-equivalent JSON numbers, without changing acceptance truth value.
 numeric=copy.deepcopy(receipt);numeric['captureAccepted']=1;m.revalidate_receipt(numeric)
 ck(numeric['captureAccepted']==receipt['captureAccepted'],'receipt Boolean-equivalent scalar observation only')
 return {'schema':'hc-independent-review-v1','status':'PASS_HOST_ONLY_SCOPED','checks':checks,'authorFiles':len(inventory['files']),'inputPins':len(audit['inputPins']),'authorHostChecks':345,'authorSourceChecks':13330,'sourceAndHostNormalOptimizedExact':True,'targetOperations':0,'networkOperations':0,'generatedCommandsExecuted':0,'nonBlockingParserObservations':['Chunk framing accepts CRLF/variable base64 wrapping while canonical decoded payload/whole hash remain exact.','Receipt revalidation uses Python equality and admits Boolean-equivalent numeric flags; acceptance truth cannot be flipped by this equivalence. Coordinator should consume generated private receipt bound to actual root frame.'],'limitations':['Plan/archive CLI has no authenticated live transport; parent must bind exact request/envelope/remote exit/deadlines and freshness.','Shell syntax qualification is not live utility/path compatibility attestation.','Existing messages are source-associated observations, not per-invocation success or physical recovery.']}
if __name__=='__main__':print(json.dumps(main(),sort_keys=True,indent=2))
