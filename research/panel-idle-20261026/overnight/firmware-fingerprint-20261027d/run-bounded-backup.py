#!/usr/bin/env python3
"""Deploy one fixed read-only backup; retain every envelope and retrieve hashes."""
import argparse
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shlex
import struct
import uuid

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
RUNNER=BASE/'managed-tcon-status-read/run-status-read.py'
RUNNER_SHA='7ca9bf01f3df4524f4f04e561dc4839d0805f4062f665b5c1b9a397adf788c8a'
BOOT='00000000-0000-4000-8000-000000000000'
DOTNET_SHA='e5840c05c567183295f0bb37e3b28613618cec5e0c8c08a44a400672a1c73310'
NAMES=['ManagedUsbEmmcBackupBounded.'+s for s in ('dll','deps.json','runtimeconfig.json')]
RETRIEVAL_CHUNK=24576
CHUNK_BYTES=8192
PROFILES={
    'probe':dict(build=BASE/'managed-usb-emmc-backup-probe-32768',total=32768,chunks=4,
                 manifest='494400b90a9e6771d19ff4a24706d7cca7be600922362b372c691cfa7f1fbb1b'),
    'full':dict(build=BASE/'managed-usb-emmc-backup-bounded',total=5242880,chunks=640,
                manifest='9f2ddf2dfc30f2174f2f064824347bb51174e5f25d510948a7df74657f8207a5'),
}
GC=re.compile(r'\[GC_INFO\] GC_(Start|End) #(\d+): Gen\((\d+)\), Time\((\d+) ms\)(?:, Reason\((\d+)\))?')
PREFIX_SHA='74d23e5947b7520dd4735422e206739f53bef92b7d26f9738a457ae1ae8b7061'

def need(ok,why):
    if not ok:
        raise ValueError(why)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def strict_json(raw):
    def bad(value):
        raise ValueError('non-JSON constant '+value)
    return json.loads(raw,parse_constant=bad)

def dir_guard(path):
    q=shlex.quote(path)
    return (f'test ! -L {q}\n'+f'test -d {q}\n'+
            f'test "$(stat -c "%u:%g:%a" {q})" = "0:0:700"\n')

def file_guard(path,size=None):
    q=shlex.quote(path)
    text=(f'test ! -L {q}\n'+f'test -f {q}\n'+
          f'test "$(stat -c "%u:%g:%a" {q})" = "0:0:600"\n')
    if size is not None:
        text+=f'test "$(wc -c < {q})" = {size}\n'
    return text

def exact_inventory(path,names):
    q=shlex.quote(path)
    cases='|'.join(shlex.quote(name) for name in sorted(names))
    return (f'count=0\nfor item in {q}/* {q}/.[!.]* {q}/..?*; do\n'+
            '  test -e "$item" || test -L "$item" || continue\n'+
            '  name=${item##*/}\n'+f'  case "$name" in {cases}) ;; *) exit 91 ;; esac\n'+
            '  count=$((count+1))\ndone\n'+f'test "$count" = {len(names)}\n')

def parse_helper_stdout(stdout):
    lines=stdout.splitlines()
    uptime=re.compile(r'[0-9]+(?:\.[0-9]+)? [0-9]+(?:\.[0-9]+)?')
    need(len(lines)>=8 and lines[0]==BOOT,'helper boot')
    need(uptime.fullmatch(lines[1]) is not None and uptime.fullmatch(lines[-1]) is not None,'helper uptime framing')
    need(lines.count('ACTIVE_BACKUP_BEGIN')==1 and lines.count('HELPER_EXIT=0')==1 and
         lines.count('WORKER_WAIT_COMPLETED')==1,'helper markers')
    phase='before'
    selftests=[]
    summaries=[]
    pids=[]
    gc=[]
    for line in lines[2:-1]:
        if line=='ACTIVE_BACKUP_BEGIN':
            need(phase=='before','active marker order')
            phase='active'
        elif line=='HELPER_EXIT=0':
            need(phase=='active','helper exit order')
            phase='exited'
        elif line=='WORKER_WAIT_COMPLETED':
            need(phase=='exited','worker wait order')
            phase='waited'
        elif re.fullmatch(r'WORKER_PID=[1-9][0-9]*',line):
            need(phase=='active','worker PID order')
            pids.append(int(line.split('=',1)[1]))
        elif line.startswith('{'):
            value=strict_json(line)
            need(isinstance(value,dict),'helper JSON object')
            need(phase in ('before','active'),'helper JSON order')
            (summaries if phase=='active' else selftests).append(value)
        elif GC.fullmatch(line) is not None:
            gc.append(line)
        else:
            raise ValueError('unclassified helper output: '+line)
    need(selftests==[{'selfTestsPassed':45,'targetOperations':0}],'self-test result')
    need(phase=='waited' and len(summaries)==1 and len(pids)==1,'helper summary/PID count')
    need(sum('GC_Start' in row for row in gc)==sum('GC_End' in row for row in gc),'GC pairs')
    return pids[0],summaries[0],len(gc)

def validate_outcome(outcome,data,result_size,summary,total,chunks):
    keys={'Stage','Steps','Chunks','Opened','Claimed','Released','Closed','SinkClosed','Accepted','OutCount',
          'InputTransfers','CompletedChunks','StoredBytes','ElapsedMs','DataSha256','Error'}
    need(isinstance(outcome,dict) and set(outcome)==keys,'outcome schema')
    need(outcome['Stage']=='complete' and outcome['Error'] is None,'outcome completion')
    need(all(outcome[name] is True for name in ('Opened','Claimed','Released','Closed','SinkClosed','Accepted')),'outcome lifecycle')
    need(all(type(outcome[name]) is int for name in ('OutCount','InputTransfers','CompletedChunks','StoredBytes','ElapsedMs')),'outcome integer fields')
    need(outcome['OutCount']==12 and outcome['InputTransfers']==outcome['CompletedChunks']==chunks,'outcome counts')
    need(len(data)==outcome['StoredBytes']==total and outcome['DataSha256']==sha(data),'outcome data')
    need(sha(data[:CHUNK_BYTES])==PREFIX_SHA,'known first-8192 fingerprint')
    steps=outcome['Steps']
    need(isinstance(steps,list) and len(steps)==6,'step count')
    expected=[('open',None),('claim',0),('out',12),('release',0),('close',0),('sink-close',0)]
    for index,(phase,value) in enumerate(expected):
        row=steps[index]
        need(isinstance(row,dict) and set(row)=={'Phase','Value','Errno','Error'},'step schema')
        need(row['Phase']==phase and type(row['Errno']) is int and row['Errno']==0 and row['Error'] is None,'step lifecycle')
        need(type(row['Value']) is int,'step integer value')
        need((type(row['Value']) is int and row['Value']>=0) if value is None else row['Value']==value,'step value')
    rows=outcome['Chunks']
    need(isinstance(rows,list) and len(rows)==chunks,'chunk count')
    previous_end=0
    for index,row in enumerate(rows):
        need(isinstance(row,dict) and set(row)=={'Index','StartElapsedMs','EndElapsedMs','Value','Errno','Stored','Sha256'},'chunk schema')
        start,end=row['StartElapsedMs'],row['EndElapsedMs']
        need(type(start) is int and type(end) is int and previous_end<=start<=end and start<15000,'chunk timing')
        need(type(row['Index']) is int and type(row['Value']) is int and type(row['Errno']) is int and
             row['Index']==index and row['Value']==CHUNK_BYTES and row['Errno']==0 and row['Stored'] is True,'chunk transport')
        need(row['Sha256']==sha(data[index*CHUNK_BYTES:(index+1)*CHUNK_BYTES]),'chunk hash')
        previous_end=end
    need(type(outcome['ElapsedMs']) is int and outcome['ElapsedMs']>=previous_end,'outcome elapsed')
    summary_keys={'Accepted','Stage','CompletedChunks','InputTransfers','StoredBytes','ElapsedMs','DataSha256','resultBytes','dataFile','resultFile'}
    need(isinstance(summary,dict) and set(summary)==summary_keys,'summary schema')
    for key in ('Accepted','Stage','CompletedChunks','InputTransfers','StoredBytes','ElapsedMs','DataSha256'):
        need(summary[key]==outcome[key],'summary '+key)
    need(summary['resultBytes']==result_size and summary['dataFile']=='fixeddata.bin' and summary['resultFile']=='result.json','summary files')

def validate_root_record(record):
    calls=record.get('calls')
    need(isinstance(calls,list) and calls,'probe raw call list')
    for call in calls:
        need(call.get('host_timeout') is False and call.get('transport_exit')==0,'probe transport completion')
        stderr=call.get('transport_stderr')
        stdout=call.get('transport_stdout')
        need(isinstance(stderr,dict) and stderr.get('encoding')=='base64' and
             base64.b64decode(stderr.get('data',''),validate=True)==b'','probe transport stderr')
        need(isinstance(stdout,dict) and stdout.get('encoding')=='base64','probe transport stdout')
        response=strict_json(base64.b64decode(stdout.get('data',''),validate=True))
        need(response==call.get('response'),'probe raw/parsed response identity')
        need(response.get('model')=='QN77S95FAFXZC' and response.get('authenticated') is True,'probe model/auth')
        need(response.get('uid')==response.get('euid')==0 and response.get('root_persistence')=='host-assisted','probe root identity')
        need(response.get('global_system_files_unchanged_at_acquisition') is True,'probe acquisition invariant')
        commands=response.get('commands')
        need(isinstance(commands,list) and len(commands)==1,'probe response command count')
        item=commands[0]
        need(item.get('command')==call.get('command') and item.get('exit_code')==0 and
             item.get('timed_out') is False and item.get('stderr')=='','probe command completion')

def write_probe_audit(directory,record_path):
    names=('record.json','stdout.txt','worker.pid','worker.start.stat','fixeddata.bin','result.json')
    rows={}
    for name in names:
        raw=(directory/name).read_bytes()
        rows[name]=dict(size=len(raw),sha256=sha(raw))
    audit=dict(schema='bounded-emmc-boundary-probe-evidence-v1',profile='probe',boot_id=BOOT,
               manifest_sha256=PROFILES['probe']['manifest'],wrapper_sha256=sha(Path(__file__).read_bytes()),
               prefix_8192_sha256=PREFIX_SHA,accepted=True,cleanup='STAGE_ABSENT',files=rows)
    path=directory/'backup-runtime-audit.json'
    with path.open('x') as output:
        json.dump(audit,output,indent=2,sort_keys=True)
        output.write('\n')
    return path,audit

def validate_probe_evidence(directory):
    need(directory.is_absolute() and directory.is_dir() and not directory.is_symlink(),'absolute probe evidence directory')
    expected={'record.json','stdout.txt','worker.pid','worker.start.stat','fixeddata.bin','result.json','backup-runtime-audit.json'}
    need({path.name for path in directory.iterdir()}==expected,'probe evidence inventory')
    audit=strict_json((directory/'backup-runtime-audit.json').read_bytes())
    audit_keys={'schema','profile','boot_id','manifest_sha256','wrapper_sha256','prefix_8192_sha256','accepted','cleanup','files'}
    need(isinstance(audit,dict) and set(audit)==audit_keys,'probe audit schema')
    need(audit['schema']=='bounded-emmc-boundary-probe-evidence-v1' and audit['profile']=='probe' and
         audit['boot_id']==BOOT and audit['manifest_sha256']==PROFILES['probe']['manifest'] and
         audit['wrapper_sha256']==sha(Path(__file__).read_bytes()) and audit['prefix_8192_sha256']==PREFIX_SHA and
         audit['accepted'] is True and audit['cleanup']=='STAGE_ABSENT','probe audit identity')
    files=expected-{'backup-runtime-audit.json'}
    need(isinstance(audit['files'],dict) and set(audit['files'])==files,'probe audit file inventory')
    for name in files:
        raw=(directory/name).read_bytes()
        need(audit['files'][name]=={'size':len(raw),'sha256':sha(raw)},'probe audit file '+name)
    record=strict_json((directory/'record.json').read_bytes())
    validate_root_record(record)
    need(record.get('profile')=='probe' and record.get('manifest_sha256')==PROFILES['probe']['manifest'] and
         record.get('deployment_script_sha256')==sha(Path(__file__).read_bytes()) and
         record.get('root_runner_sha256')==RUNNER_SHA,'probe record identity')
    need(record.get('request')=={'target':'0x203','address':'0x0','length':32768,'chunk_length':CHUNK_BYTES,'chunks':4},'probe request')
    need(record.get('worker_wait_completed') is True and record.get('helper_accepted') is True and
         record.get('cleanup_deferred') is False and record.get('cleanup_stdout')=='STAGE_ABSENT\n' and
         'host_error' not in record,'probe completion')
    stdout=(directory/'stdout.txt').read_text()
    worker_pid,summary,gc_rows=parse_helper_stdout(stdout)
    need(record.get('worker_pid')==worker_pid and record.get('helper_summary')==summary and
         record.get('helper_gc_rows')==gc_rows and record.get('helper_stdout_sha256')==sha(stdout.encode()),'probe stdout record')
    need((directory/'worker.pid').read_text().strip()==str(worker_pid),'probe PID file')
    data=(directory/'fixeddata.bin').read_bytes()
    result_raw=(directory/'result.json').read_bytes()
    validate_outcome(strict_json(result_raw),data,len(result_raw),summary,32768,4)
    return dict(directory=str(directory),record_sha256=sha((directory/'record.json').read_bytes()),
                audit_sha256=sha((directory/'backup-runtime-audit.json').read_bytes()),data_sha256=sha(data))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--profile',choices=sorted(PROFILES),default='probe')
    parser.add_argument('--manifest-sha256')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--probe-evidence',type=Path)
    args=parser.parse_args()
    profile=PROFILES[args.profile]
    build=profile['build']
    total=profile['total']
    chunks=profile['chunks']
    header=struct.pack('<III',0x203,0,total).hex()
    need(total==chunks*CHUNK_BYTES,'internal profile geometry')
    if not args.execute:
        print(json.dumps(dict(target_operations=0,profile=args.profile,header_hex=header,total_bytes=total,
                              usb_in_length=CHUNK_BYTES,usb_in_count=chunks)))
        return
    need(args.output is not None and args.output.is_absolute() and args.manifest_sha256 is not None,'absolute new output and reviewed manifest required')
    if args.profile=='full':
        need(args.probe_evidence is not None,'full profile requires retained probe evidence')
        probe_evidence=validate_probe_evidence(args.probe_evidence)
    else:
        need(args.probe_evidence is None,'probe profile does not consume probe evidence')
        probe_evidence=None
    raw=(build/'build-manifest.json').read_bytes()
    need(args.manifest_sha256==profile['manifest'] and sha(raw)==profile['manifest'],'reviewed manifest')
    manifest=strict_json(raw)
    need(manifest['schema']=='usb-fixed-emmc-backup-bounded-build-v1','schema')
    for key,value in dict(fixed_target='0x203',fixed_address='0x0',fixed_total_length=total,
                          fixed_chunk_length=CHUNK_BYTES,fixed_chunk_count=chunks,deadline_ms=15000,
                          per_bulk_timeout_ms=2000,header_hex=header).items():
        need(manifest[key]==value,'fixed scope '+key)
    expected={'Program.cs','ManagedUsbEmmcBackupBounded.csproj',*('bin/Release/net6.0/'+n for n in NAMES)}
    need(set(manifest['files'])==expected,'manifest inventory')
    for name,row in manifest['files'].items():
        data=(build/name).read_bytes()
        need(len(data)==row['size'] and sha(data)==row['sha256'],'build '+name)
    need(sha(RUNNER.read_bytes())==RUNNER_SHA,'root runner identity')
    spec=importlib.util.spec_from_file_location('pinned_runner',RUNNER)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    args.output.mkdir(parents=True,exist_ok=False)
    record_path=args.output/'record.json'
    remote='/tmp/researcher-usb-emmcbackup-'+uuid.uuid4().hex
    record=dict(profile=args.profile,manifest_sha256=sha(raw),deployment_script_sha256=sha(Path(__file__).read_bytes()),root_runner_sha256=RUNNER_SHA,
                remote_stage=remote,request=dict(target='0x203',address='0x0',length=total,chunk_length=CHUNK_BYTES,chunks=chunks),
                calls=[],retrieved_files={},cleanup_deferred=True,probe_evidence=probe_evidence,
                failure_policy='A partial/timeout may leave the controller transaction in flight: do not retry, send a new header or reset USB until guarded reset/requalification.')
    module.save(record_path,record)
    def call(command):
        return module.root(command,record,record_path)
    try:
        call('set -eu\numask 077\n'+f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n'+
             f'test "$(sha256sum /usr/bin/dotnet | cut -d " " -f1)" = {DOTNET_SHA}\n'+
             'test "$(df -Pk /tmp | awk \'NR==2 {print $4}\')" -ge 16384\n'+
             f'test ! -e {shlex.quote(remote)}\ntest ! -L {shlex.quote(remote)}\n'+
             f'mkdir -m 700 {shlex.quote(remote)}\n'+dir_guard(remote)+'echo STAGE_CREATED\n')
        for name in NAMES:
            data=(build/'bin/Release/net6.0'/name).read_bytes()
            encoded=base64.b64encode(data).decode('ascii')
            target=remote+'/'+name
            temp=target+'.b64'
            for start in range(0,len(encoded),5000):
                chunk=encoded[start:start+5000]
                initialize=(f'test ! -e {shlex.quote(temp)}\ntest ! -L {shlex.quote(temp)}\n'+
                            f': > {shlex.quote(temp)}\nchmod 600 {shlex.quote(temp)}\n') if start==0 else ''
                call('set -eu\numask 077\n'+dir_guard(remote)+initialize+file_guard(temp,start)+
                     f'printf %s {shlex.quote(chunk)} >> {shlex.quote(temp)}\n'+
                     file_guard(temp,start+len(chunk))+'echo STAGE_CHUNK_COMPLETE\n')
            call('set -eu\numask 077\n'+dir_guard(remote)+file_guard(temp,len(encoded))+
                 f'test ! -e {shlex.quote(target)}\ntest ! -L {shlex.quote(target)}\n'+
                 f'base64 -d {shlex.quote(temp)} > {shlex.quote(target)}\nchmod 600 {shlex.quote(target)}\n'+
                 file_guard(target,len(data))+
                 f'test "$(sha256sum {shlex.quote(target)} | cut -d " " -f1)" = {sha(data)}\n'+
                 f'rm {shlex.quote(temp)}\ntest ! -e {shlex.quote(temp)}\necho FILE_VERIFIED\n')
        dll=shlex.quote(remote+'/'+NAMES[0])
        # sh records its own PID and start ticks before exec preserves that PID.
        # wait must return before files can be fetched or the stage removed.
        child=('set -eu\numask 077\n'+dir_guard(remote)+
               ''.join(f'test ! -e {shlex.quote(remote+"/"+n)}\ntest ! -L {shlex.quote(remote+"/"+n)}\n'
                       for n in ('worker.pid','worker.start.stat','fixeddata.bin','result.json'))+
               'printf "%s\\n" "$$" > '+shlex.quote(remote+'/worker.pid')+'\nchmod 600 '+shlex.quote(remote+'/worker.pid')+'\n'+
               'cat /proc/$$/stat > '+shlex.quote(remote+'/worker.start.stat')+'\nchmod 600 '+shlex.quote(remote+'/worker.start.stat')+'\n'+
               file_guard(remote+'/worker.pid')+file_guard(remote+'/worker.start.stat')+
               'exec /usr/bin/dotnet '+dll+' --execute\n')
        integrity=dir_guard(remote)+exact_inventory(remote,NAMES)
        for name in NAMES:
            staged=remote+'/'+name
            raw_build=(build/'bin/Release/net6.0'/name).read_bytes()
            integrity+=file_guard(staged,len(raw_build))+f'test "$(sha256sum {shlex.quote(staged)} | cut -d " " -f1)" = {sha(raw_build)}\n'
        command=('set -eu\numask 077\n'+f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n'+integrity+
                 'cat /proc/sys/kernel/random/boot_id\ncat /proc/uptime\n'+
                 f'/usr/bin/dotnet {dll} --self-test\n'+'echo ACTIVE_BACKUP_BEGIN\n'+
                 'sh -c '+shlex.quote(child)+' &\nworker=$!\necho WORKER_PID=$worker\nrc=0\nwait "$worker" || rc=$?\n'+
                 'echo HELPER_EXIT=$rc\necho WORKER_WAIT_COMPLETED\ncat /proc/uptime\n')
        stdout=call(command)
        (args.output/'stdout.txt').write_text(stdout)
        record['helper_stdout_sha256']=sha(stdout.encode())
        worker_pid,helper_summary,gc_rows=parse_helper_stdout(stdout)
        record['worker_pid']=worker_pid
        record['helper_summary']=helper_summary
        record['helper_gc_rows']=gc_rows
        record['worker_wait_completed']=True
        module.save(record_path,record)
        # Fetch ordinary tmpfs files after the USB worker ended. Never repeat it.
        limits={'worker.pid':(2,32),'worker.start.stat':(1,4096),'fixeddata.bin':(total,total),'result.json':(1,524288)}
        for name,(minimum,maximum) in limits.items():
            raw_path=remote+'/'+name
            path=shlex.quote(raw_path)
            metadata=call('set -eu\numask 077\n'+dir_guard(remote)+file_guard(raw_path)+
                          f'# FETCH_METADATA\nwc -c < {path}\nsha256sum {path}\n')
            lines=metadata.splitlines()
            need(len(lines)==2 and re.fullmatch('[0-9]+',lines[0].strip()) is not None,'file metadata')
            size=int(lines[0].strip())
            need(minimum<=size<=maximum,'bounded file')
            match=re.fullmatch(r'([0-9a-f]{64})  '+re.escape(raw_path),lines[1])
            need(match is not None,'exact metadata hash/path')
            digest=match.group(1)
            partial=args.output/(name+'.partial')
            with partial.open('xb') as output:
                for index,start in enumerate(range(0,size,RETRIEVAL_CHUNK)):
                    encoded=call('set -eu\numask 077\n'+dir_guard(remote)+file_guard(raw_path,size)+
                                 f'dd if={path} bs={RETRIEVAL_CHUNK} skip={index} count=1 2>/dev/null | base64 | tr -d \'\\n\'\necho\n')
                    need(encoded.endswith('\n') and encoded.count('\n')==1,'retrieval framing')
                    need(len(encoded)<=((RETRIEVAL_CHUNK+2)//3)*4+1,'retrieval encoded bound')
                    chunk=base64.b64decode(encoded[:-1],validate=True)
                    need(len(chunk)==min(RETRIEVAL_CHUNK,size-start),'retrieval exact length')
                    output.write(chunk)
            data=partial.read_bytes()
            need(len(data)==size and sha(data)==digest,'retrieved file hash')
            final=args.output/name
            need(not final.exists(),'new retained file')
            partial.rename(final)
            record['retrieved_files'][name]=dict(size=size,sha256=digest)
            module.save(record_path,record)
        need((args.output/'worker.pid').read_text().strip()==str(record['worker_pid']),'child PID agrees')
        stat=(args.output/'worker.start.stat').read_text()
        need(stat.split(' ',1)[0]==str(record['worker_pid']) and ') ' in stat,'recorded proc identity')
        tail=stat.rsplit(') ',1)[1].split()
        need(len(tail)>=20 and tail[19].isdigit(),'start ticks')
        record['worker_start_ticks']=int(tail[19])
        result_raw=(args.output/'result.json').read_bytes()
        outcome=strict_json(result_raw)
        data=(args.output/'fixeddata.bin').read_bytes()
        validate_outcome(outcome,data,len(result_raw),helper_summary,total,chunks)
        record['helper_accepted']=True
        # Retain failed/partial cases on target for follow-up; never drain/reset.
        output_names=list(limits)
        names=NAMES+output_names
        files=[remote+'/'+name for name in names]
        cleanup='set -eu\numask 077\n'+dir_guard(remote)+exact_inventory(remote,names)
        for name in NAMES:
            raw_build=(build/'bin/Release/net6.0'/name).read_bytes()
            cleanup+=file_guard(remote+'/'+name,len(raw_build))+f'test "$(sha256sum {shlex.quote(remote+"/"+name)} | cut -d " " -f1)" = {sha(raw_build)}\n'
        for name in output_names:
            info=record['retrieved_files'][name]
            cleanup+=file_guard(remote+'/'+name,info['size'])+f'test "$(sha256sum {shlex.quote(remote+"/"+name)} | cut -d " " -f1)" = {info["sha256"]}\n'
        cleanup+='rm -f '+' '.join(map(shlex.quote,files))+'\n'+f'rmdir {shlex.quote(remote)}\ntest ! -e {shlex.quote(remote)}\necho STAGE_ABSENT\n'
        record['cleanup_stdout']=call(cleanup)
        need(record['cleanup_stdout']=='STAGE_ABSENT\n','cleanup confirmation')
        record['cleanup_deferred']=False
        module.save(record_path,record)
        audit_path=None
        if args.profile=='probe':
            audit_path,_=write_probe_audit(args.output,record_path)
        print(json.dumps(dict(record=str(record_path),profile=args.profile,accepted=True,data_bytes=len(data),
                              data_sha256=sha(data),cleanup='STAGE_ABSENT',
                              probe_audit=None if audit_path is None else str(audit_path))))
    except Exception as error:
        record['host_error']=type(error).__name__+': '+str(error)
        module.save(record_path,record)
        raise

if __name__=='__main__':
    main()
