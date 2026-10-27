#!/usr/bin/env python3
"""Authenticate raw records and reconstruct fixed CPU/alias reads offline."""
import base64
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import struct
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
PRIOR=BASE/'rt-onset-memory-20261027c/audit-runtime.py'

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

if sha(PRIOR.read_bytes())!='ef6819eae26c9b4e0210edf8ebf0470993a2030b9b6a1489c0877bd282724704':
    raise ValueError('pinned raw auditor')
spec=importlib.util.spec_from_file_location('prior',PRIOR)
prior=importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
need=prior.need

RUNS=[('callback-read-once','managed-usb-current-callbacks-read-once',0x20000580,
       '6e7bcb04e390452929f54f3bba9ca72c6894a7496b57f4167d68ff2322261f0e','430871ea0cabfc46c42dcb8bc5a8651679019591b5aa67b916e3a58b2e7329db'),
      ('callback-alias-read-once','managed-usb-current-callbacks-alias-read-once',0x45000580,
       'b38d123e2c7339f31b82d8d88daf51a28007b3da820a1862ed4227701cf1f71c','b80c5a4553e351b23a842a96c5dc6bdf5275e811543cf19be8f0c53ca6ca43e8')]
CURRENT=(0x291c1,0x29135,0x2925f,0,0,0x288e9,0x28a55,0x29259)
PACKAGED=(0x2945d,0x293d1,0x294fb,0,0,0x28b85,0x28cf1,0x294f5)

def audit(item):
    name,helper,address,manifest_pin,wrapper_pin=item
    directory=HERE/name
    build=BASE/helper
    record_raw=(directory/'record.json').read_bytes()
    record=prior.strict_json(record_raw)
    uploads=prior.root_calls(record)
    raw=(build/'build-manifest.json').read_bytes()
    need(sha(raw)==manifest_pin==record['manifest_sha256'],'manifest pin')
    manifest=json.loads(raw)
    need(manifest['fixed_target']=='0x101' and manifest['fixed_address']==hex(address) and manifest['fixed_length']==64 and manifest['header_hex']==struct.pack('<III',0x101,address,64).hex(),'fixed header and extent')
    names={'ManagedUsbRtBlockReadOnce.'+suffix for suffix in ('dll','deps.json','runtimeconfig.json')}
    need(set(uploads)==names,'upload inventory')
    need(set(manifest['files'])=={'Program.cs','ManagedUsbRtBlockReadOnce.csproj',*('bin/Release/net6.0/'+n for n in names)},'build inventory')
    for filename,entry in manifest['files'].items():
        payload=(build/filename).read_bytes()
        need(sha(payload)==entry['sha256'] and len(payload)==entry['size'],'build identity '+filename)
        if filename.startswith('bin/'):
            need(base64.b64decode(uploads[Path(filename).name],validate=True)==payload,'exact staged bytes')
    source=build/'run-once.py'
    need(sha(source.read_bytes())==wrapper_pin==record['deployment_script_sha256'],'wrapper identity')
    need(record['root_runner_sha256']=='7ca9bf01f3df4524f4f04e561dc4839d0805f4062f665b5c1b9a397adf788c8a','root runner')
    need(record['request']==dict(target='0x101',address=hex(address),length=64),'fixed request')
    spec=importlib.util.spec_from_file_location('fixed_wrapper',source)
    wrapper=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wrapper)
    class Replay:
        index=0
        final=None
        def save(self,path,value):
            self.final=value
            path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
        def root(self,command,value,path):
            need(self.index<len(record['calls']),'no extra replay call')
            call=record['calls'][self.index]
            need(command==call['command'],'exact replay command '+str(self.index))
            self.index+=1
            value['calls'].append(call)
            return call['response']['commands'][0]['stdout']
    replay=Replay()
    fake_spec=SimpleNamespace(loader=SimpleNamespace(exec_module=lambda module:None))
    with tempfile.TemporaryDirectory(prefix='callback-audit-') as temporary:
        output=Path(temporary)/'replayed'
        argv=['run-once.py','--execute','--manifest-sha256',manifest_pin,'--output',str(output)]
        with patch.object(wrapper.importlib.util,'spec_from_file_location',return_value=fake_spec),patch.object(wrapper.importlib.util,'module_from_spec',return_value=replay),patch.object(wrapper.uuid,'uuid4',return_value=SimpleNamespace(hex=record['remote_stage'].rsplit('-',1)[1])),patch.object(sys,'argv',argv),contextlib.redirect_stdout(io.StringIO()):
            wrapper.main()
        need(replay.index==len(record['calls']) and replay.final==record,'complete command and record replay')
        need((output/'stdout.txt').read_bytes()==(directory/'stdout.txt').read_bytes(),'reconstructed stdout')
    stdout=(directory/'stdout.txt').read_text()
    before,after,outcomes,gc=prior.parse_stdout(stdout,26)
    need(len(outcomes)==1,'one native outcome')
    payload=prior.transport(outcomes[0],64)
    active=[call for call in record['calls'] if 'ACTIVE_READ_BEGIN' in call['command']]
    need(len(active)==1 and active[0]['command'].count(' --execute')==1,'one native invocation')
    need(stdout==active[0]['response']['commands'][0]['stdout'] and sha(stdout.encode())==record['helper_stdout_sha256'],'actual helper stdout')
    need(record['cleanup_stdout']=='STAGE_ABSENT\n'==record['calls'][-1]['response']['commands'][0]['stdout'],'cleanup')
    extracted=directory/'returned-block.bin'
    if extracted.exists():
        need(extracted.read_bytes()==payload,'extracted bytes')
    else:
        extracted.write_bytes(payload)
    words=struct.unpack_from('<8I',payload,12)
    physical=address==0x45000580
    classification='inconclusive_raw_cpu_address' if not physical else ('matches_current_stored_callbacks' if words==CURRENT else 'matches_packaged_callbacks' if words==PACKAGED else 'neither_prediction')
    return dict(run=name,address=hex(address),record_sha256=sha(record_raw),manifest_sha256=manifest_pin,wrapper_sha256=wrapper_pin,
                root_calls=len(record['calls']),uptime_before=before,uptime_after=after,payload_sha256=sha(payload),all_bytes_zero=not any(payload),
                callback_words=[hex(word) for word in words],classification=classification,
                callback_words_match_current_prediction=words==CURRENT,
                callback_words_match_packaged_prediction=words==PACKAGED,
                raw_bytes_match_current_prediction=payload==(HERE/'expected-current-callbacks.bin').read_bytes(),
                raw_bytes_match_packaged_prediction=payload==(HERE/'expected-packaged-callbacks.bin').read_bytes(),
                exact_record_and_command_replay=True,cleanup='STAGE_ABSENT',
                whole_image_identity_proved=False,physical_picture_observed=False,repair_established=False)

def main():
    runs=[audit(item) for item in RUNS if (HERE/item[0]/'stdout.txt').exists()]
    need(runs,'no retained read')
    report=dict(schema='callback-cpu-dma-runtime-audit-v1',runs=runs)
    (HERE/'callback-runtime-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    main()
