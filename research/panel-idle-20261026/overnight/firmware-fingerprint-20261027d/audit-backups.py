#!/usr/bin/env python3
"""Offline raw-envelope reconciliation and exact host-runner replay; no TV I/O."""
import base64
import contextlib
from datetime import datetime
import importlib.util
import io
import json
import hashlib
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
prior_path=BASE/'rt-onset-memory-20261027c/audit-runtime.py'
if hashlib.sha256(prior_path.read_bytes()).hexdigest()!='ef6819eae26c9b4e0210edf8ebf0470993a2030b9b6a1489c0877bd282724704':
    raise ValueError('prior audit identity')
spec=importlib.util.spec_from_file_location('prior_audit',prior_path)
prior=importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
need,sha=prior.need,prior.sha

PINS={
    'probe':('boundary-probe-recovered-v2','managed-usb-emmc-backup-probe-32768',32768,4,'494400b90a9e6771d19ff4a24706d7cca7be600922362b372c691cfa7f1fbb1b'),
    'full':('full-backup-recovered','managed-usb-emmc-backup-bounded',5242880,640,'9f2ddf2dfc30f2174f2f064824347bb51174e5f25d510948a7df74657f8207a5')}

def audit(profile):
    name,buildname,length,chunks,digest=PINS[profile]
    directory=HERE/name
    record_raw=(directory/'record.json').read_bytes()
    record=prior.strict_json(record_raw)
    uploaded=prior.root_calls(record)
    previous=None
    for call in record['calls']:
        start,end=(datetime.fromisoformat(call[key]) for key in ('started_utc','finished_utc'))
        need(start<=end and (previous is None or previous<=start),'ordered root calls')
        need(call['command_bytes']==len(call['command'].encode()),'command bytes')
        previous=end
    build=BASE/buildname
    manifest_raw=(build/'build-manifest.json').read_bytes()
    need(sha(manifest_raw)==record['manifest_sha256']==digest,'reviewed immutable build')
    manifest=json.loads(manifest_raw)
    need(manifest['fixed_total_length']==length and manifest['fixed_chunk_length']==8192 and manifest['fixed_chunk_count']==chunks,'fixed geometry')
    names={'ManagedUsbEmmcBackupBounded.'+suffix for suffix in ('dll','deps.json','runtimeconfig.json')}
    need(set(uploaded)==names,'exact upload inventory')
    for filename,entry in manifest['files'].items():
        data=(build/filename).read_bytes()
        need(len(data)==entry['size'] and sha(data)==entry['sha256'],'build file hash')
        if filename.startswith('bin/'):
            need(base64.b64decode(uploaded[Path(filename).name],validate=True)==data,'exact uploaded bytes')
    wrapperpath=HERE/'run-bounded-backup.py'
    need(sha(wrapperpath.read_bytes())==record['deployment_script_sha256'],'same reviewed wrapper')
    need(record['root_runner_sha256']=='7ca9bf01f3df4524f4f04e561dc4839d0805f4062f665b5c1b9a397adf788c8a','root runner')
    spec=importlib.util.spec_from_file_location('retained_wrapper',wrapperpath)
    wrapper=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wrapper)
    adapter_meta=json.loads(json.dumps(record['transport_adapter']))
    candidates=[HERE/name for name in ('run-backup-with-normalizer.py','run-backup-with-normalizer-v2.py','run-backup-with-normalizer-v1.py')]
    matches=[path for path in candidates if path.exists() and sha(path.read_bytes())==adapter_meta['adapter_sha256']]
    need(len(matches)==1,'unique preserved adapter source')
    adapter_path=matches[0]
    need(adapter_meta['adapter_sha256']==sha(adapter_path.read_bytes()) and adapter_meta['wrapper_sha256']==record['deployment_script_sha256'],'adapter identity')
    spec=importlib.util.spec_from_file_location('normalizing_adapter',adapter_path)
    adapter=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    replay_prefix_count=adapter_meta['replayed_prefix_calls']
    if replay_prefix_count:
        original_name='boundary-probe' if profile=='probe' else 'full-backup'
        original_raw=(HERE/original_name/'record.json').read_bytes()
        original=json.loads(original_raw)
        need(sha(original_raw)==adapter_meta['initial_failed_record_sha256'] and replay_prefix_count==len(original['calls']),'original failed record provenance')
        expected_original='e4fe50646255d43f5287d4ee4a1eddf8a95dd5c984511520522af6c2f5dad65a' if profile=='probe' else 'a5a97c1a69e0c4fc3dbb5c6ce39bbc2c99b1ac43acd2e2881a94f0f912e759dd'
        need(sha(original_raw)==expected_original,'pinned failed acquisition')
        need(record['calls'][:replay_prefix_count]==original['calls'],'unmodified replayed raw history')
    else:
        need(replay_prefix_count==0 and adapter_meta['initial_failed_record_sha256'] is None,'live acquisition provenance')
    adapter_meta['replayed_prefix_calls']=0
    adapter_meta['normalized_call_indices']=[]
    adapter_meta['wire_rewrite_indices']=[]
    if 'helper_stdout_normalized_indices' in adapter_meta:
        adapter_meta['helper_stdout_normalized_indices']=[]
    class Replay:
        index=0
        final=None
        def save(self,path,value):
            value['transport_adapter']=adapter_meta
            self.final=value
            path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
        def root(self,command,value,path):
            need(self.index<len(record['calls']),'no extra call during replay')
            raw=record['calls'][self.index]
            forwarded=command if self.index<replay_prefix_count else adapter.wire_command(command)
            need(forwarded==raw['command'],f'exact replay wire command {self.index}')
            if forwarded!=command:
                adapter_meta['wire_rewrite_indices'].append(self.index)
            self.index+=1
            value['calls'].append(raw)
            if self.index<=replay_prefix_count:
                adapter_meta['replayed_prefix_calls']=self.index
            self.final=value
            stdout=raw['response']['commands'][0]['stdout']
            if 'ACTIVE_BACKUP_BEGIN' in command and profile=='full' and hasattr(adapter,'normalize_helper_stdout'):
                corrected=adapter.normalize_helper_stdout(stdout)
                if corrected!=stdout:
                    adapter_meta['helper_stdout_normalized_indices'].append(self.index-1)
                stdout=corrected
            if adapter.is_fetch(command):
                adapter_meta['normalized_call_indices'].append(self.index-1)
                stdout=adapter.canonicalize(stdout)
            return stdout
    replay=Replay()
    fake_spec=SimpleNamespace(loader=SimpleNamespace(exec_module=lambda module:None))
    suffix=record['remote_stage'].removeprefix('/tmp/researcher-usb-emmcbackup-')
    need(len(suffix)==32 and all(c in '0123456789abcdef' for c in suffix),'private UUID')
    with tempfile.TemporaryDirectory(prefix='tv-backup-audit-replay-') as temporary:
        output=Path(temporary)/'reconstructed'
        argv=['run-bounded-backup.py','--profile',profile,'--execute','--manifest-sha256',digest,'--output',str(output)]
        if profile=='full':
            argv+=['--probe-evidence',str(HERE/'boundary-probe-recovered-v2')]
        with patch.object(wrapper.importlib.util,'spec_from_file_location',return_value=fake_spec),patch.object(wrapper.importlib.util,'module_from_spec',return_value=replay),patch.object(wrapper.uuid,'uuid4',return_value=SimpleNamespace(hex=suffix)),patch.object(sys,'argv',argv),contextlib.redirect_stdout(io.StringIO()):
            wrapper.main()
        need(replay.index==len(record['calls']),'all original calls consumed')
        need(replay.final==record,'complete reconstructed record evolution')
        for filename in ('worker.pid','worker.start.stat','fixeddata.bin','result.json','stdout.txt'):
            need((output/filename).read_bytes()==(directory/filename).read_bytes(),'reconstructed retained file '+filename)
    need(record['cleanup_deferred'] is False and record['cleanup_stdout']=='STAGE_ABSENT\n' and record['worker_wait_completed'] is True,'finished cleanup')
    data=(directory/'fixeddata.bin').read_bytes()
    prefix=(HERE/'prefix-8192/returned-sector.bin').read_bytes()
    need(len(prefix)==8192 and sha(prefix)=='74d23e5947b7520dd4735422e206739f53bef92b7d26f9738a457ae1ae8b7061','prefix identity')
    need(len(data)==length and data[:8192]==prefix,'prefix repeat')
    sector_pins={0x200:'9b67558a2dd74c56273962ceee694e3cc4dc11f3b900a1f904dd2317803ffaec',0x29000:'8cd7aa864b8f0caa156df3d2498f6fa2b3a7f88d00136872d0501e04cfbac50d',
                 0x40200:'c435e2646632d52fd1780abed4f80c17d3ca504072a088e477e5b673ba900235',0x80000:'a83bfbe0a5a370f4d07512562e992d54040b58dc8baa52f45dc9a99bc0f6f53d',
                 0x28e00:'28e1db6bad575359da47c6c553a4cca7d2923aabfd804bfcea8abd76f5bdca98',0x28a00:'115e870ba1431deaab2a3920ef022a5ce35672d38fbb6cbd84716f475c2e34d5'}
    for address,sector_digest in sector_pins.items():
        sector=(HERE/f'sector-{address:06x}/returned-sector.bin').read_bytes()
        need(len(sector)==512 and sha(sector)==sector_digest,'sector pin')
        if address+512<=length:
            need(data[address:address+512]==sector,'independent sector repeat')
    if profile=='full':
        need(data[:32768]==(HERE/'boundary-probe-recovered-v2/fixeddata.bin').read_bytes(),'boundary probe repeat')
    outcome=json.loads((directory/'result.json').read_text())
    profiledata=(BASE/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes()
    need(len(profiledata)==5242880 and sha(profiledata)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','selected profile identity')
    regions={}
    if profile=='full':
        for label,begin,end in (('first_header',0,0x200),('first_slot_after_header',0x200,0x40000),('second_slot',0x40000,0x80000),('configuration_tail',0x80000,length)):
            regions[label]=dict(start=hex(begin),end_exclusive=hex(end),returned_sha256=sha(data[begin:end]),packaged_sha256=sha(profiledata[begin:end]),
                                equal=data[begin:end]==profiledata[begin:end],different_bytes=sum(a!=b for a,b in zip(data[begin:end],profiledata[begin:end])))
    return dict(profile=profile,length=length,usb_in_count=chunks,record_sha256=sha(record_raw),manifest_sha256=digest,payload_sha256=sha(data),
                root_calls=len(record['calls']),exact_command_replay=True,complete_record_reconstructed=True,all_retrieved_bytes_reconstructed=True,
                stdout_sha256=sha((directory/'stdout.txt').read_bytes()),result_sha256=sha((directory/'result.json').read_bytes()),elapsed_ms=outcome['ElapsedMs'],
                maximum_chunk_ms=max(c['EndElapsedMs']-c['StartElapsedMs'] for c in outcome['Chunks']),regions=regions,
                storage_read_result_observed=False,current_executing_image_identity_proved=False,physical_picture_observed=False,repair_established=False)

def main():
    runs=[audit(profile) for profile in PINS if (HERE/PINS[profile][0]/'stdout.txt').exists()]
    need(runs,'no completed acquisition')
    report=dict(schema='fixed-emmc-backup-raw-replay-v1',runs=runs)
    (HERE/'backup-runtime-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    main()
