#!/usr/bin/env python3
"""Reconcile completed fixed CX02, without another decryption invocation."""
import hashlib,importlib.util,json,os,re,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE));import extraction
OUT=Path('/home/researcher/.local/state/s95f-live-trials/swu-cx-02')
def need(ok,why):
 if not ok:raise ValueError(why)
def save(p,o):p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');p.chmod(0o600)
s=importlib.util.spec_from_file_location('fixed_da',HERE/'run-cx.py');runner=importlib.util.module_from_spec(s);s.loader.exec_module(runner)
need(json.loads((OUT/'deployment.json').read_text())==runner.manifest(),'execution source/payload drift')
terminal=json.loads((OUT/'job/terminal.json').read_text());need(terminal['transport_completed'] is True and terminal['exit_code']==0 and not terminal['deadline'] and terminal['termination_confirmed'] and terminal['launch_attempts']==1,'native terminal')
server=json.loads((OUT/'transport-result.json').read_text());need(server['status']=='raw_complete' and server['error_code']==0 and server['raw_complete'] and server['connections_accepted']==1 and server['cipher_bytes']==server['raw_bytes']==1455423504,'bulk transport')
raw=(OUT/'reconciliation/native.stdout.bin').read_bytes();need(len(raw)==345471 and hashlib.sha256(raw).hexdigest()=='fbdd095b5231a6e003a74d8c600dad066bf1a7b0c0eb7b2168f7557c8c6bbebf','immutable raw native receipt')
needle=b'SWU_STREAM_RAW ';need(raw.count(needle)==1,'unique native status');start=raw.index(needle);end=raw.index(b'\n',start)+1;status=raw[start:end]
framed='RUN_EXIT=0\nSTDOUT_BEGIN\n'+status.decode('ascii')+'STDOUT_END\nSTDERR_BEGIN\nSTDERR_END\n';fields=runner.parse_native(framed)
# Removing this one complete status row (including its newline) restores the
# runtime line around it: '[GC_INFO] GC_' + 'Start #3012...'. Nothing else is
# discarded or repaired. Validate the whole remaining stream, not just a tail.
residual=raw[:start]+raw[end:];lines=residual.splitlines();need(len(lines)%2==0,'GC line parity');events=0;last_time=-1
for at in range(0,len(lines),2):
 a=re.fullmatch(rb'\[GC_INFO\] GC_Start #([0-9]+): Gen\(([0-9]+)\), Time\(([0-9]+) ms\), Reason\(([0-9]+)\)',lines[at]);z=re.fullmatch(rb'\[GC_INFO\] GC_End #([0-9]+): Gen\(([0-9]+)\), Time\(([0-9]+) ms\)',lines[at+1]);need(a is not None and z is not None,'entire GC grammar');events+=1
 need(int(a[1])==int(z[1])==events and a[2]==z[2] and last_time<=int(a[3])<=int(z[3]),'GC sequence/pair/time');last_time=int(z[3])
need(events==3020,'complete GC event count')
proof={'schema':'s95f-native-receipt-interleaving-reconciliation-v1','unique_status_rows':1,'native_status_byte_span':[start,end],'all_other_bytes_validated_as_gc':True,'gc_start_end_pairs':events,'original_driver_accepted':False,'original_driver_rejection':'Runtime GC prefix interleaved around native status; exact-prefix line filter hid the otherwise complete native receipt','offline_reconciliation_accepted':True,'native_reinvoked':False,'root_or_firmware_modified_for_reconciliation':False}
save(OUT/'reconciliation/receipt-proof.json',proof);(OUT/'reconciliation/normalized-native.txt').write_text(framed)
r=extraction.section(1001);result=extraction.validate_and_copy(OUT/'transport/raw-complete.bin',OUT/'platform.img',r)
result.update(accepted=True,native=fields,source_trial=OUT.name,firmware_written=False,retries=0,original_driver_accepted=False,reconciled_native_receipt=True,native_reinvoked=False);save(OUT/'result.json',result)
job=runner.load(runner.B/'swu-prepared-inline-job-20261028cw/job.py','reconcile_cw');spec=job.JobSpec(stage=runner.STAGE,dll='SwuStreamTarget.dll',boot=runner.BOOT,dotnet_sha256=runner.DOTNET_SHA,payloads=tuple(job.Payload(n,p.stat().st_size,runner.sha(p.read_bytes())) for n,p in sorted(runner.PAYLOAD.items())),native_seconds=1700,supervisor_seconds=1750,host_seconds=1800,io_seconds=10)
with job.guarded_access(Path('${S95F_EVIDENCE_ROOT}/root-access/s95f-access.py')) as access:
 calls=[]
 def call(command,label):
  item={'command':command,'response_unknown':True};calls.append(item);save(OUT/'reconciliation/cleanup-calls.json',calls)
  try:text=access.exec(command)
  except BaseException as e:item.update(error_type=type(e).__name__,last_response=access.last_response);save(OUT/'reconciliation/cleanup-calls.json',calls);raise
  item.update(response_unknown=False,stdout=text);save(OUT/'reconciliation/cleanup-calls.json',calls);return text
 need(call(job.cleanup_command(spec),'job')=='JOB_REMOVED\n','job cleanup')
 command=runner.guard()+runner.exact(runner.PAYLOAD)+'rm -- '+' '.join(runner.shlex.quote(runner.STAGE+'/'+n) for n in sorted(runner.PAYLOAD))+f'\nrmdir -- {runner.STAGE}\ntest ! -e {runner.STAGE}\ntest ! -L {runner.STAGE}\nprintf "STAGE_REMOVED\\n"\n';need(call(command,'stage')=='STAGE_REMOVED\n','stage cleanup')
 save(OUT/'cleanup.json',{'stage_removed':True,'job_removed':True,'reconciliation_cleanup_calls':len(calls),'native_reinvoked':False})
print(json.dumps({'accepted':True,'section':1001,'original_bytes':result['bytes'],'strict_padding_validated':True,'original_crc_validated':True,'native_elapsed_ms':int(fields['elapsed_ms']),'native_reinvoked':False,'gc_pairs_validated':events,'original_driver_accepted':False,'reconciled_native_receipt':True,'stage_removed':True}))
