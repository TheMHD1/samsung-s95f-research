#!/usr/bin/env python3
"""Canonicalize file-transfer base64; optionally resume a completed probe's fetch."""
import argparse
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
from types import SimpleNamespace
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
WRAPPER=HERE/'run-bounded-backup.py'
WRAPPER_SHA='92d6aa58c71737188a652355b7f8da6c0116a58fd68b51afb29ecd1eaca05a1b'
RUNNER=HERE.parent/'managed-tcon-status-read/run-status-read.py'
RUNNER_SHA='7ca9bf01f3df4524f4f04e561dc4839d0805f4062f665b5c1b9a397adf788c8a'
PRIOR=HERE.parent/'rt-onset-memory-20261027c/audit-runtime.py'
PRIOR_SHA='ef6819eae26c9b4e0210edf8ebf0470993a2030b9b6a1489c0877bd282724704'
FAILED_PROBE_SHA='e4fe50646255d43f5287d4ee4a1eddf8a95dd5c984511520522af6c2f5dad65a'
FAILED_FULL_SHA='a5a97c1a69e0c4fc3dbb5c6ce39bbc2c99b1ac43acd2e2881a94f0f912e759dd'

def need(ok,why):
    if not ok:
        raise ValueError(why)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def load(name,path,digest):
    need(sha(path.read_bytes())==digest,'pinned module '+name)
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def is_fetch(command):
    lines=[line for line in command.splitlines() if line.startswith('dd if=')]
    return len(lines)==1 and re.fullmatch(r"dd if=/tmp/researcher-usb-emmcbackup-[0-9a-f]{32}/(worker\.pid|worker\.start\.stat|fixeddata\.bin|result\.json) bs=24576 skip=[0-9]+ count=1 2>/dev/null \| base64 \| tr -d '\\n'",lines[0]) is not None

def canonicalize(stdout):
    need(isinstance(stdout,str) and len(stdout)<=34000 and re.fullmatch('[A-Za-z0-9+/=\n]+',stdout) is not None,'bounded base64/LF output')
    compact=stdout.replace('\n','')
    raw=base64.b64decode(compact,validate=True)
    need(base64.b64encode(raw).decode('ascii')==compact,'canonical base64')
    return compact+'\n'

def wire_command(command):
    if not is_fetch(command):
        return command
    fragment=" | tr -d '\\n'"
    need(command.count(fragment)==1,'one legacy tr removal')
    return command.replace(fragment,'')

def normalize_helper_stdout(stdout):
    lines=stdout.splitlines(keepends=True)
    changes=0
    for index,line in enumerate(lines[:-1]):
        if line=='[GC_INFO] {"selfTestsPassed":45,"targetOperations":0}\n':
            need(re.fullmatch(r'GC_End #256: Gen\(0\), Time\(104723170 ms\)\n',lines[index+1]) is not None,'specific interleaved GC tail')
            lines[index]=line.removeprefix('[GC_INFO] ')
            lines[index+1]='[GC_INFO] '+lines[index+1]
            changes+=1
    need(changes in (0,1),'one exact interleaving correction')
    return ''.join(lines)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--profile',choices=('probe','full'),default='probe')
    parser.add_argument('--manifest-sha256')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--probe-evidence',type=Path)
    parser.add_argument('--replay-prefix',type=Path)
    args=parser.parse_args()
    if not args.execute:
        print(json.dumps(dict(target_operations=0,purpose='base64 newline normalization and optional completed-probe retrieval recovery')))
        return
    need(args.output is not None and args.output.is_absolute() and not args.output.exists(),'new absolute retained output')
    wrapper=load('pinned_wrapper',WRAPPER,WRAPPER_SHA)
    native=load('pinned_root',RUNNER,RUNNER_SHA)
    original=None
    original_raw=None
    if args.replay_prefix:
        original_raw=args.replay_prefix.read_bytes()
        expected_failed=FAILED_PROBE_SHA if args.profile=='probe' else FAILED_FULL_SHA
        need(sha(original_raw)==expected_failed,'specific preserved failed acquisition')
        original=json.loads(original_raw)
        audit=load('pinned_prior_audit',PRIOR,PRIOR_SHA)
        audit.root_calls(original)
        need(original['profile']==args.profile and original['manifest_sha256']==wrapper.PROFILES[args.profile]['manifest'],'original profile identity')
        need(original['deployment_script_sha256']==WRAPPER_SHA and original['root_runner_sha256']==RUNNER_SHA,'original source identity')
        need(original['cleanup_deferred'] is True and original['retrieved_files']=={},'retained original stage before file retrieval')
        active=[c for c in original['calls'] if 'ACTIVE_BACKUP_BEGIN' in c['command']]
        need(len(active)==1 and active[0]['command'].count(' --execute')==1,'one original native execution')
        helper_stdout=active[0]['response']['commands'][0]['stdout']
        parsed_stdout=normalize_helper_stdout(helper_stdout) if args.profile=='full' else helper_stdout
        pid,summary,gc_rows=wrapper.parse_helper_stdout(parsed_stdout)
        need(summary['Accepted'] is True and summary['CompletedChunks']==summary['InputTransfers']==wrapper.PROFILES[args.profile]['chunks'] and summary['StoredBytes']==wrapper.PROFILES[args.profile]['total'],'completed native transfer')
        if args.profile=='probe':
            need(original['worker_wait_completed'] is True,'original probe wait complete')
            need(original.get('host_error')=='ValueError: retrieval framing','specific probe framing failure')
            need(is_fetch(original['calls'][-1]['command']) and '/worker.pid bs=' in original['calls'][-1]['command'],'failed first PID-file retrieval')
            need((pid,summary,gc_rows)==(original['worker_pid'],original['helper_summary'],original['helper_gc_rows']),'parsed original helper identity')
        else:
            need(original.get('host_error')=='ValueError: unclassified helper output: [GC_INFO] {"selfTestsPassed":45,"targetOperations":0}','specific full GC parse failure')
            need(original['calls'][-1]==active[0] and len(original['calls'])==19,'full stopped immediately after completed helper')
            need(summary['DataSha256']=='f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562','specific completed full data')
            need(pid==18979 and summary['ElapsedMs']==281 and summary['resultBytes']==149638,'specific completed full worker')
            need(parsed_stdout!=helper_stdout and len(parsed_stdout)==len(helper_stdout),'one byte-preserving GC prefix correction')
        need(sha(helper_stdout.encode())==original['helper_stdout_sha256'],'original helper stdout hash')
        need(re.fullmatch('/tmp/researcher-usb-emmcbackup-[0-9a-f]{32}',original['remote_stage']) is not None,'original private UUID')
    metadata=dict(schema='base64-lf-normalizing-root-adapter-v1',adapter_sha256=sha(Path(__file__).read_bytes()),wrapper_sha256=WRAPPER_SHA,
                  mode='completed-'+args.profile+'-retrieval-recovery' if original else 'live-fixed-acquisition',
                  initial_failed_record_sha256=sha(original_raw) if original_raw is not None else None,
                  replayed_prefix_calls=0,normalized_call_indices=[],wire_rewrite_indices=[],helper_stdout_normalized_indices=[])
    class Adapter:
        prefix_index=0
        forward_count=0
        def save(self,path,record):
            record['transport_adapter']=metadata
            native.save(path,record)
        def root(self,command,record,path):
            if original is not None and self.prefix_index<len(original['calls']):
                call=json.loads(json.dumps(original['calls'][self.prefix_index]))
                need(call['command']==command,'exact replay prefix command')
                self.prefix_index+=1
                metadata['replayed_prefix_calls']=self.prefix_index
                record['calls'].append(call)
                stdout=call['response']['commands'][0]['stdout']
            else:
                if original is not None:
                    need('ACTIVE_BACKUP_BEGIN' not in command and ' --execute' not in command and 'printf %s ' not in command and 'base64 -d ' not in command and 'mkdir ' not in command,'no repeated device or deployment operation')
                    need(is_fetch(command) or '# FETCH_METADATA\n' in command or command.endswith('echo STAGE_ABSENT\n'),'recovery file retrieval/cleanup only')
                self.forward_count+=1
                forwarded=wire_command(command)
                if forwarded!=command:
                    metadata['wire_rewrite_indices'].append(len(record['calls']))
                stdout=native.root(forwarded,record,path)
            if 'ACTIVE_BACKUP_BEGIN' in command and args.profile=='full':
                corrected=normalize_helper_stdout(stdout)
                if corrected!=stdout:
                    metadata['helper_stdout_normalized_indices'].append(len(record['calls'])-1)
                stdout=corrected
            if is_fetch(command):
                metadata['normalized_call_indices'].append(len(record['calls'])-1)
                stdout=canonicalize(stdout)
            self.save(path,record)
            return stdout
    adapter=Adapter()
    argv=['run-bounded-backup.py','--execute','--profile',args.profile,'--manifest-sha256',args.manifest_sha256 or '', '--output',str(args.output)]
    if args.probe_evidence:
        argv+=['--probe-evidence',str(args.probe_evidence)]
    fake_spec=SimpleNamespace(loader=SimpleNamespace(exec_module=lambda module:None))
    context=[]
    from contextlib import ExitStack
    with ExitStack() as stack:
        stack.enter_context(patch.object(wrapper.importlib.util,'spec_from_file_location',return_value=fake_spec))
        stack.enter_context(patch.object(wrapper.importlib.util,'module_from_spec',return_value=adapter))
        stack.enter_context(patch.object(sys,'argv',argv))
        if original:
            stack.enter_context(patch.object(wrapper.uuid,'uuid4',return_value=SimpleNamespace(hex=original['remote_stage'].rsplit('-',1)[1])))
        wrapper.main()
    need(original is None or adapter.prefix_index==len(original['calls']),'all recovery prefix consumed')
    print(json.dumps(dict(adapter_sha256=metadata['adapter_sha256'],replayed_prefix_calls=adapter.prefix_index,new_root_calls=adapter.forward_count,
                          normalized_file_fetches=len(metadata['normalized_call_indices']),device_request_repeated=False if original else None)))

if __name__=='__main__':
    main()
