#!/usr/bin/env python3
"""Run both fixed profiles against fake transport; never contact the TV."""
import base64
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('backup_wrapper',HERE/'run-bounded-backup.py')
wrapper=importlib.util.module_from_spec(spec)
spec.loader.exec_module(wrapper)

class FakeRoot:
    def __init__(self,mode,profile):
        self.mode=mode
        self.profile=profile
        self.commands=[]
        geometry=wrapper.PROFILES[profile]
        prefix=(HERE/'prefix-8192/returned-sector.bin').read_bytes()
        wrapper.need(len(prefix)==wrapper.CHUNK_BYTES and wrapper.sha(prefix)==wrapper.PREFIX_SHA,'fake known prefix')
        remainder=geometry['total']-len(prefix)
        data=prefix+(bytes(range(256))*(remainder//256))
        rows=[]
        for index in range(geometry['chunks']):
            start=index*2
            raw=data[index*wrapper.CHUNK_BYTES:(index+1)*wrapper.CHUNK_BYTES]
            rows.append(dict(Index=index,StartElapsedMs=start,EndElapsedMs=start+1,Value=wrapper.CHUNK_BYTES,
                             Errno=0,Stored=True,Sha256=wrapper.sha(raw)))
        if mode=='malformed':
            rows[-1]['Sha256']='0'*64
        accepted=mode!='partial'
        outcome=dict(Stage='complete',Steps=[
            dict(Phase='open',Value=9,Errno=0,Error=None),dict(Phase='claim',Value=0,Errno=0,Error=None),
            dict(Phase='out',Value=12,Errno=0,Error=None),dict(Phase='release',Value=0,Errno=0,Error=None),
            dict(Phase='close',Value=0,Errno=0,Error=None),dict(Phase='sink-close',Value=0,Errno=0,Error=None)],
            Chunks=rows,Opened=True,Claimed=True,Released=True,Closed=True,SinkClosed=True,Accepted=accepted,
            OutCount=12,InputTransfers=geometry['chunks'],CompletedChunks=geometry['chunks'],StoredBytes=len(data),
            ElapsedMs=geometry['chunks']*2,DataSha256=wrapper.sha(data),Error=None)
        result=json.dumps(outcome,separators=(',',':')).encode()
        self.outcome=outcome
        self.files={'fixeddata.bin':data,'result.json':result,'worker.pid':b'123\n',
                    'worker.start.stat':('123 (sh) S '+' '.join(['0']*18+['100']+['0']*12)+'\n').encode()}
        self.summary=dict(Accepted=accepted,Stage='complete',CompletedChunks=geometry['chunks'],
                          InputTransfers=geometry['chunks'],StoredBytes=len(data),ElapsedMs=geometry['chunks']*2,
                          DataSha256=wrapper.sha(data),resultBytes=len(result),dataFile='fixeddata.bin',resultFile='result.json')
    def save(self,path,record):
        path.write_text(json.dumps(record)+'\n')
    def root(self,command,record,path):
        self.commands.append(command)
        if 'ACTIVE_BACKUP_BEGIN' in command:
            if self.mode=='timeout':
                record['calls'].append(dict(command=command,host_timeout=True))
                self.save(path,record)
                raise TimeoutError('injected timeout after worker launch')
            returned=(wrapper.BOOT+'\n100 100\n'+
                      '[GC_INFO] GC_Start #1: Gen(2), Time(0 ms), Reason(0)\n'+
                      '[GC_INFO] GC_End #1: Gen(2), Time(1 ms)\n'+
                      '{"selfTestsPassed":45,"targetOperations":0}\nACTIVE_BACKUP_BEGIN\nWORKER_PID=123\n'+
                      json.dumps(self.summary,separators=(',',':'))+'\nHELPER_EXIT=0\nWORKER_WAIT_COMPLETED\n101 101\n')
        elif '# FETCH_METADATA' in command:
            match=re.search(r'sha256sum ([^\n ]+)\n$',command)
            wrapper.need(match is not None,'fake metadata command')
            raw_path=match.group(1)
            name=raw_path.rsplit('/',1)[1]
            raw=self.files[name]
            digest='0'*64 if self.mode=='hash' and name=='fixeddata.bin' else wrapper.sha(raw)
            returned=f'{len(raw)}\n{digest}  {raw_path}\n'
        elif 'dd if=' in command:
            match=re.search(r'dd if=([^ ]+) bs=(\d+) skip=(\d+) count=1',command)
            wrapper.need(match is not None,'fake retrieval command')
            name=match[1].rsplit('/',1)[1]
            size,index=int(match[2]),int(match[3])
            raw=self.files[name][size*index:size*(index+1)]
            if self.mode=='short' and name=='fixeddata.bin' and index==0:
                raw=raw[:-1]
            returned=base64.b64encode(raw).decode()+'\n'
        elif command.endswith('echo STAGE_ABSENT\n'):
            returned='STAGE_ABSENT\n'
        else:
            returned='FAKE_OK\n'
        if self.profile=='probe' and self.mode=='success':
            response=dict(model='QN77S95FAFXZC',authenticated=True,uid=0,euid=0,root_persistence='host-assisted',
                          global_system_files_unchanged_at_acquisition=True,
                          commands=[dict(command=command,exit_code=0,timed_out=False,stderr='',stdout=returned)])
            encoded=json.dumps(response,separators=(',',':')).encode()
            row=dict(command=command,command_bytes=len(command.encode()),host_timeout=False,transport_exit=0,
                     transport_stdout=dict(encoding='base64',data=base64.b64encode(encoded).decode()),
                     transport_stderr=dict(encoding='base64',data=''),response=response)
        else:
            row=dict(command=command)
        record['calls'].append(row)
        self.save(path,record)
        return returned

def run_case(profile,mode,output,probe_evidence=None):
    build=wrapper.PROFILES[profile]['build']
    digest=wrapper.sha((build/'build-manifest.json').read_bytes())
    fake=FakeRoot(mode,profile)
    argv=['run-bounded-backup.py','--profile',profile,'--execute','--manifest-sha256',digest,'--output',str(output)]
    if probe_evidence is not None:
        argv+=['--probe-evidence',str(probe_evidence)]
    fake_spec=SimpleNamespace(loader=SimpleNamespace(exec_module=lambda module:None))
    error=None
    with patch.object(wrapper.importlib.util,'spec_from_file_location',return_value=fake_spec),\
         patch.object(wrapper.importlib.util,'module_from_spec',return_value=fake),patch.object(sys,'argv',argv):
        try:
            wrapper.main()
        except (ValueError,TimeoutError) as caught:
            error=caught
    wrapper.need((error is None)==(mode=='success'),'expected outcome '+profile+' '+mode)
    wrapper.need(sum('ACTIVE_BACKUP_BEGIN' in command for command in fake.commands)==1,'one invocation')
    wrapper.need(all(0<len(command.encode())<=8192 for command in fake.commands),'root command bounds')
    cleanup=[command for command in fake.commands if command.endswith('echo STAGE_ABSENT\n')]
    wrapper.need(len(cleanup)==(1 if mode=='success' else 0),'cleanup policy')
    record=json.loads((output/'record.json').read_text())
    wrapper.need(record['profile']==profile and record['cleanup_deferred']==(mode!='success'),'retained/profile record')
    if mode=='success':
        wrapper.need((output/'fixeddata.bin').read_bytes()==fake.files['fixeddata.bin'],'retrieval bytes')
        wrapper.need('count=0\nfor item in ' in cleanup[0],'exact cleanup inventory')
    if mode=='timeout':
        wrapper.need(not any('dd if=' in command for command in fake.commands),'no fetch after unconfirmed process exit')
    wrapper.need(all(('dd if=' not in command and '# FETCH_METADATA' not in command) or
                     ('stat -c' in command and '0:0:700' in command and '0:0:600' in command)
                     for command in fake.commands),'fetch guards')

def main():
    modes=('success','short','hash','partial','timeout','malformed')
    with tempfile.TemporaryDirectory(prefix='tv-backup-host-test-') as temporary:
        base=Path(temporary)
        evidence=base/'probe-success'
        run_case('probe','success',evidence)
        for mode in modes[1:]:
            run_case('probe',mode,base/('probe-'+mode))
        for mode in modes:
            run_case('full',mode,base/('full-'+mode),evidence)
    print(json.dumps(dict(host_wrapper_cases_passed=len(modes)*2,profiles=['probe','full'],target_operations=0)))

if __name__=='__main__':
    main()
