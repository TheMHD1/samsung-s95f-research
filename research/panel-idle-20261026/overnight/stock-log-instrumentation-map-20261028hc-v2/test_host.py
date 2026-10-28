#!/usr/bin/env python3
"""Finite host-only protocol, malformed frames, source-filter and private archive tests."""
import ast, base64, copy, hashlib, json, os, stat, subprocess, sys, tempfile
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
from stock_log import *
checks=0; cases=[]; shells=0; longest=0
NONCE='0123456789abcdef'*2;BOOT='00000000-0000-0000-0000-000000000001'
def test(v,why):
 global checks
 if not v:raise ValueError(why)
 checks+=1
def refuse(fn,why):
 try:fn()
 except (ValueError,KeyError,UnicodeError,TypeError,OSError):test(True,why);return
 raise ValueError('unexpected acceptance: '+why)
def frame(raw=b'kernel line\n',err=b'',rc=0):
 return ('HC_CAPTURE_BEGIN\n'+f'nonce={NONCE}\nboot={BOOT}\nprocUptimeBefore=123.01\nprocUptimeAfter=123.03\ndmesgExit={rc}\nrawBytes={len(raw)}\nrawSha256={sha(raw)}\nstderrBytes={len(err)}\nstderrSha256={sha(err)}\nstageMode=0:0:700\nfileMode=0:0:600\nfileCount=2\nHC_CAPTURE_END\n').encode()
def chunk(blob,kind,index):
 part=blob[index*CHUNK:(index+1)*CHUNK]
 return (f'HC_CHUNK_BEGIN\nnonce={NONCE}\nkind={kind}\nindex={index}\noffset={index*CHUNK}\nbytes={len(part)}\n'+base64.b64encode(part).decode()+'\nHC_CHUNK_END\n').encode()
def syntax(command):
 global shells,longest
 test(len(command.encode())<=COMMAND_CAP,'command byte bound')
 test('\\'not in command,'quote protocol avoids backslashes')
 cp=subprocess.run(['/bin/sh','-n'],input=command.encode(),capture_output=True,timeout=5)
 test(cp.returncode==0 and not cp.stdout and not cp.stderr,'shell syntax only, no execution')
 shells+=1;longest=max(longest,len(command.encode()))
def run():
 syntax(capture_command(NONCE,BOOT))
 test('dmesg)'in capture_command(NONCE,BOOT),'only plain dmesg')
 for forbidden in ['dmesg -c','dmesg -C','tracing_on','kprobe','gpio_value','ioctl','wget','curl','input_keyevent']:
  test(forbidden not in capture_command(NONCE,BOOT),'no added controller/debug action '+forbidden)
 for n in ['',NONCE+'x','../x','a'*31,'A'*32,'a'*31+"'"]:
  refuse(lambda:capture_command(n,BOOT),'nonce injection')
 for b in ['',BOOT+'x',BOOT.upper().replace('00000000','AAAAAAAA',1),"';id",'0'*36]:
  refuse(lambda:capture_command(NONCE,b),'boot injection/syntax')
 raw=bytes(range(256))*4096;receipt=parse_capture(frame(raw),NONCE,BOOT)
 test(receipt['captureAccepted']and receipt['archiveEligible'],'max fixed raw accepted')
 test(not receipt['completeKernelRingProven'],'accepted does not imply complete ring')
 for i in range(64):
  syntax(fetch_command(receipt,'raw',i));test(parse_chunk(chunk(raw,'raw',i),receipt,'raw',i)==raw[i*CHUNK:(i+1)*CHUNK],'all64 exact chunks')
 refuse(lambda:fetch_command(receipt,'raw',64),'chunk extent')
 refuse(lambda:fetch_command(receipt,'../../x',0),'no arbitrary path')
 refuse(lambda:fetch_command(receipt,'raw',True),'boolean index not int')
 test(len(base64.b64encode(bytes(CHUNK)))+2048<RESPONSE_CAP,'worst fetch response accounting')
 err_receipt=parse_capture(frame(bytes(RAW_CAP),bytes(ERR_CAP),1),NONCE,BOOT)
 syntax(fetch_command(err_receipt,'stderr',0))
 test(parse_chunk(chunk(bytes(ERR_CAP),'stderr',0),err_receipt,'stderr',0)==bytes(ERR_CAP),'exact capped stderr chunk')
 test(64+1==LIMITS['maximumFetchCalls'],'full cap64 raw plus one stderr')
 for changed,label in [(frame()+b'x','trailing junk'),(frame()[:-1],'noncanonical missing newline'),(frame().replace(b'HC_CAPTURE_END',b''),'missing terminal'),(frame().replace(b'fileCount=2',b'fileCount=3'),'extra file'),(frame().replace(b'0:0:600',b'0:0:644'),'public mode'),(frame().replace(b'rawBytes=12',b'rawBytes=-1'),'negative size'),(frame().replace(b'123.03',b'122.00'),'clock reversal'),(frame().replace(b'nonce='+NONCE.encode(),b'nonce='+b'f'*32),'other instance'),(frame().replace(b'\n',b'\r\n'),'noncanonical CRLF')]:
  refuse(lambda:parse_capture(changed,NONCE,BOOT),label)
 for rc,err in [(1,b''),(127,b'not found\n'),(153,b'file size limit\n')]:
  r=parse_capture(frame(b'partial',err,rc),NONCE,BOOT)
  test(not r['captureAccepted']and r['archiveEligible'],'refusal retained, bounded forensic archival allowed')
  test(bool(r['refusalReasons']),'original refusal reason retained')
 for rawsize,errsize in [(RAW_CAP+1,0),(0,ERR_CAP+1)]:
  f=frame().replace(b'rawBytes=12',('rawBytes='+str(rawsize)).encode()).replace(b'stderrBytes=0',('stderrBytes='+str(errsize)).encode())
  r=parse_capture(f,NONCE,BOOT);test(not r['archiveEligible']and not r['captureAccepted'],'oversize refused')
  refuse(lambda:fetch_command(r,'raw',0),'no oversize fetch')
 r=parse_capture(frame(b'abc'),NONCE,BOOT); good=chunk(b'abc','raw',0)
 for bad in [good[:-15],good+b'extra',good.replace(b'bytes=3',b'bytes=4'),good.replace(b'YWJj',b'YQ=='),good.replace(b'YWJj',b'YWJ?'),good.replace(b'offset=0',b'offset=1'),good.replace(NONCE.encode(),b'f'*32)]:
  refuse(lambda:parse_chunk(bad,r,'raw',0),'malformed chunk')
 changed=copy.deepcopy(r);changed['captureAccepted']=False
 refuse(lambda:fetch_command(changed,'raw',0),'receipt flags cannot be changed')
 # Subprocess execution above is only /bin/sh -n syntax validation. No generated command runs.
 with tempfile.TemporaryDirectory(dir=Path(os.environ.get('HC_TEST_TMPDIR',str(HERE/'private-tmp'))))as temp:
  root=Path(temp);os.chmod(root,0o700)
  chunks=root/'chunks';chunks.mkdir(mode=0o700)
  (chunks/'raw-00.txt').write_bytes(good);os.chmod(chunks/'raw-00.txt',0o600)
  outcome=archive(r,chunks,root/'archive')
  test(outcome['rawSavedBeforeFiltering']and outcome['archiveVerified'],'raw archived before filtering')
  test((root/'archive/kernel.raw').read_bytes()==b'abc','exact original bytes')
  for p in (root/'archive').iterdir():test(stat.S_IMODE(p.stat().st_mode)==0o600,'all outputs private')
  test(stat.S_IMODE((root/'archive').stat().st_mode)==0o700,'output directory private')
  refuse(lambda:archive(r,chunks,root/'archive'),'no overwrite archive')
  (chunks/'extra').write_bytes(b'');refuse(lambda:archive(r,chunks,root/'other'),'extra chunk file');(chunks/'extra').unlink()
  (chunks/'raw-00.txt').write_bytes(good.replace(b'YWJj',b'eHl6'));refuse(lambda:archive(r,chunks,root/'hashbad'),'whole hash binding')
  (chunks/'raw-00.txt').unlink();(chunks/'raw-00.txt').symlink_to(root/'archive/kernel.raw');refuse(lambda:archive(r,chunks,root/'linkbad'),'symlink input')
  (chunks/'raw-00.txt').unlink()
  refused=parse_capture(frame(b'',b'failed\n',1),NONCE,BOOT)
  (chunks/'stderr-00.txt').write_bytes(chunk(b'failed\n','stderr',0));os.chmod(chunks/'stderr-00.txt',0o600)
  outcome=archive(refused,chunks,root/'refused')
  test(outcome['archiveVerified']and not outcome['captureAccepted'],'archive does not promote refused capture')
  test((root/'refused/stderr.raw').read_bytes()==b'failed\n','exact refused stderr preserved')
 sample=(b'[10.000100] [TCON:QDF] QDFTcon_SetQdTconPowerControl[123:example]: Reset(2)\n'
 b'[10.000200] [TCON:QDF] f[123:example]: err_det is fault. skip the tcon recovery. err_det_status[1]\n'
 b'[10.000300] [TCON:QDF] f[124:other]: Check Tcon and register recovery\n'
 b'[10.000400] [TCON:QDF] f[124:other]: resume npc_lut data done[226 reg ->89 count]\n')
 result=classify(sample)
 test(result['markerCounts']['qdf-mode2-request']==1,'mode2 source formatter')
 test(result['markerCounts']['qdf-err-skipped-recovery']==1,'positive printed ERR-skip')
 test(result['markerCounts']['qdf-normal-tail-entered']==1,'positive printed normal tail separately')
 test('qdf-register-replay-start'not in result['markerCounts'],'end does not fabricate start')
 test(result['observations'][1]['printedPid']==123,'printed PID decoded without cross-call inference')
 test(result['observations'][2]['printedPid']==124,'interleaved PID kept separate')
 test(result['observations'][0]['printkTimestamp']=='10.000100','exact textual timestamp, no native mapping')
 for f in ['absentMessageProvesAbsentExecution','controllerInstructionReloadProven','sharedFaultFlagsClearedProven','physicalRecoveryProven','nativeClockMappingProven']:
  test(result[f]is False,'scientific boundary '+f)
 test(classify(b'no relevant messages\n')['markerCounts']=={},'no marker is no evidence of absent execution')
 refuse(lambda:classify(bytes(RAW_CAP+1)),'filter cap')
 # CLI module has no transport library, dynamic target import, or command executor.
 tree=ast.parse((HERE/'stock_log.py').read_text())
 imports=[n.names[0].name for n in ast.walk(tree)if isinstance(n,ast.Import)]
 test(not any(n in imports for n in ['subprocess','socket','requests','urllib']),'CLI has no execution/network import')
 return dict(schema='s95f-stock-log-hc-host-validation-v2',checks=checks,shellSyntaxChecks=shells,
   longestCommandBytes=longest,maximumFetchResponseBytesUpperBound=CHUNK_FRAME_CAP,
   maximumRawBytes=RAW_CAP,maximumErrorBytes=ERR_CAP,maximumFetchCalls=65,
   generatedCommandsExecuted=0,targetOperations=0,networkOperations=0,
   cases=['strict capture/receipt and instance binding','all64 max-size chunks','refusal-preserving forensic archive',
    'whole-file hash/private-mode/exclusive archive','finite malformed frames','source-marker/PID/time separation','missing messages never exclusion proof'])
if __name__=='__main__':print(json.dumps(run(),indent=2,sort_keys=True))
