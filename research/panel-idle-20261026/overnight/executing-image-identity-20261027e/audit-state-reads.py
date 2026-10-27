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

RUNS=[('common-error-guard-read-once','managed-usb-common-error-guard-read-once',0x4500f0c0,
       'db25f3b8dccd5d95705a097a987784a7fc902d7d18a78a348794de91a0840aa4','f5e1b1789f73e49babd0d571d9ba5e02b204c3ecdb5201445cd38582c9e256f8'),
      ('secondary-root-read-once','managed-usb-secondary-root-read-once',0x470004c0,
       '180acb56334ac1af0e4ccf3838e02bbefc7b7a91c2c9735848a2fba947ab2319','8023844c0219918544214f0a2ebaf8a6d8937ade14ea65c2b6b86027d674db9a')]

RUNS.extend([
 ('secondary-event-log-baseline-read-once','managed-usb-secondary-event-log-read-once',0x20200000,
  'fca9538254a4b4e442e3ff20249624af96d52be650a9d25e6ade3545327a76cd','b13ea5bbb8c7d2499a75a77ce7d47cd702a24f43f9f124a390ab9c3f4eb2f8aa',15372),
 ('secondary-log-header-read-once','managed-usb-secondary-log-header-read-once',0x20200000,
  'f7e84f9381ce9a443eef53ce787a340c874b0d279162ac974d9477abd4124da2','dce9119f8657e8b5b32a6b566d2006b940677ec3b2ecb55b51d39aa0f24e5e81'),
 ('main-event-log-read-once','managed-usb-main-event-log-read-once',0x20205000,
  'ac4133ccb6e2b12576006a981f1d585ad0fe1384a2a6d1a5096f3a81bced5371','245323c709dc098d343a1ee470c505ba909249126d4fe5645b12b20709ff7031',3072),
 ('main-log-index-read-once','managed-usb-main-log-index-read-once',0x45000e20,
  'b48fc00f8d14d3f4f611f7a1c4957a8cf86225b4ae75620ee3116d2aea18d075','6c087933cb23b3d4edffc443fa1ac3b05227af984c6a6f10b9b53527069cca7f')])

def audit(item):
    name,helper,address,manifest_pin,wrapper_pin,*optional_length=item
    length=optional_length[0] if optional_length else 64
    directory=HERE/name
    build=BASE/helper
    record_raw=(directory/'record.json').read_bytes()
    record=prior.strict_json(record_raw)
    uploads=prior.root_calls(record)
    raw=(build/'build-manifest.json').read_bytes()
    need(sha(raw)==manifest_pin==record['manifest_sha256'],'manifest pin')
    manifest=json.loads(raw)
    need(manifest['fixed_target']=='0x101' and manifest['fixed_address']==hex(address) and manifest['fixed_length']==length and manifest['header_hex']==struct.pack('<III',0x101,address,length).hex(),'fixed header and extent')
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
    need(record['request']==dict(target='0x101',address=hex(address),length=length),'fixed request')
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
    payload=prior.transport(outcomes[0],length)
    active=[call for call in record['calls'] if 'ACTIVE_READ_BEGIN' in call['command']]
    need(len(active)==1 and active[0]['command'].count(' --execute')==1,'one native invocation')
    need(stdout==active[0]['response']['commands'][0]['stdout'] and sha(stdout.encode())==record['helper_stdout_sha256'],'actual helper stdout')
    need(record['cleanup_stdout']=='STAGE_ABSENT\n'==record['calls'][-1]['response']['commands'][0]['stdout'],'cleanup')
    extracted=directory/'returned-block.bin'
    if extracted.exists():
        need(extracted.read_bytes()==payload,'extracted bytes')
    else:
        extracted.write_bytes(payload)
    observed={}
    if name=='common-error-guard-read-once':
        observed={'halfword_at_plus_0x20':struct.unpack_from('<H',payload,0x20)[0],
                  'halfword_at_plus_0x30':struct.unpack_from('<H',payload,0x30)[0],
                  'conditional_packaged_meaning':'first return guard and common selector; immutable accessor identity unproved',
                  'emergency_loop_execution_proved':False}
    elif name=='secondary-root-read-once':
        observed={'word_at_plus_0x20':hex(struct.unpack_from('<I',payload,0x20)[0]),
                  'halfwords_at_plus_6_8_10':list(struct.unpack_from('<3H',payload,6)),
                  'live_core_tag_proved':False}
    elif name in ('secondary-log-header-read-once','secondary-event-log-baseline-read-once'):
        observed={'write_index_candidate':struct.unpack_from('<I',payload,0)[0],
                  'word_at_plus_4':struct.unpack_from('<I',payload,4)[0],
                  'valid_flag_candidate':struct.unpack_from('<I',payload,8)[0],
                  'index_and_flag_within_static_range':struct.unpack_from('<I',payload,0)[0]<=0x3c00 and struct.unpack_from('<I',payload,8)[0] in (0,1),
                  'log_data_prefix_hex':payload[12:64].hex(),
                  'logger_activity_proved_by_header_alone':False}
    elif name=='main-log-index-read-once':
        observed={'packaged_index_candidate':struct.unpack_from('<I',payload,0x3c)[0],
                  'current_stored_index_candidate':struct.unpack_from('<I',payload,0x2c)[0],
                  'packaged_byte_flag_candidate':payload[0x10],
                  'atomic_with_log_read':False}
    return dict(run=name,address=hex(address),length=length,record_sha256=sha(record_raw),manifest_sha256=manifest_pin,wrapper_sha256=wrapper_pin,
                root_calls=len(record['calls']),uptime_before=before,uptime_after=after,payload_sha256=sha(payload),all_bytes_zero=not any(payload),
                payload_hex=payload.hex() if length<=64 else None,observed=observed,exact_record_and_command_replay=True,cleanup='STAGE_ABSENT',
                whole_image_identity_proved=False,physical_picture_observed=False,repair_established=False)

def main():
    runs=[audit(item) for item in RUNS if (HERE/item[0]/'stdout.txt').exists()]
    need(runs,'no retained read')
    report=dict(schema='controller-ram-state-runtime-audit-v1',runs=runs)
    (HERE/'state-runtime-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    main()
