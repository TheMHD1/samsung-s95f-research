#!/usr/bin/env python3
"""Offline exact replay of the existing one-shot status getter and log read."""
from pathlib import Path
import base64,hashlib,importlib.util,json,re,tempfile,shlex
from types import SimpleNamespace
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
BASE=HERE.parent

def sha(b):return hashlib.sha256(b).hexdigest()
def need(v,why):
 if not v:raise ValueError(why)
def module(name,path,pin):
 need(sha(path.read_bytes())==pin,'module identity '+name)
 spec=importlib.util.spec_from_file_location(name,path)
 obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj
prior=module('prior',BASE/'rt-onset-memory-20261027c/audit-runtime.py','ef6819eae26c9b4e0210edf8ebf0470993a2030b9b6a1489c0877bd282724704')
runner=module('runner',BASE/'managed-tcon-status-read/run-status-read.py','7ca9bf01f3df4524f4f04e561dc4839d0805f4062f665b5c1b9a397adf788c8a')
raw=(HERE/'host-tcon-status-read-once').read_bytes();r=json.loads(raw)
def validate_calls(record):
 uploads={}
 for row in record['calls']:
  need(not row['host_timeout'] and row['transport_exit']==0,'completed root transport')
  need(base64.b64decode(row['transport_stderr']['data'],validate=True)==b'','transport stderr')
  decoded=prior.strict_json(base64.b64decode(row['transport_stdout']['data'],validate=True))
  need(decoded==row['response'],'raw response identity')
  runner.validate_response(decoded,row['command'])
  need(row['command_bytes']==len(row['command'].encode()),'command extent')
  for line in row['command'].splitlines():
   if line.startswith('printf %s '):
    words=shlex.split(line)
    need(len(words)==8 and words[:2]==['printf','%s'] and words[3:7]==['|','base64','-d','>>'],'chunk decode framing')
    path=Path(words[7]);need(str(path.parent)==record['private_directory'],'private upload')
    uploads.setdefault(path.name,bytearray()).extend(base64.b64decode(words[2],validate=True))
 return uploads
uploads=validate_calls(r)
manifest,files=runner.contract()
need(manifest==r['build'] and sha(runner.MANIFEST.read_bytes())==r['build_manifest_sha256'],'manifest')
need(set(uploads)==set(files),'staged inventory')
for name,data in files.items():need(bytes(uploads[name])==data,'exact staged '+name)
class Replay:
 index=0
 def root(self,command,value,path):
  need(self.index<len(r['calls']),'no extra call')
  row=r['calls'][self.index];need(command==row['command'],'exact command '+str(self.index));self.index+=1
  value['calls'].append(row);runner.save(path,value);return row['response']['commands'][0]['stdout']
replay=Replay();times=iter([r['created_utc'],r['finished_utc']])
with tempfile.TemporaryDirectory(prefix='status-audit-') as tmp:
 with patch.object(runner,'root',replay.root),patch.object(runner,'now',side_effect=lambda:next(times)),patch.object(runner.uuid,'uuid4',return_value=SimpleNamespace(hex=r['private_directory'].rsplit('-',1)[1])):
  again=runner.run_once(Path(tmp)/'replay.json',manifest,files)
 need(again==r and replay.index==len(r['calls']),'exact full record replay')
need(r['accepted'] and r['cleanup_confirmed'] and r['one_shot'] and not r['retry_permitted'],'accepted one-shot and cleanup')
log_raw=(HERE/'host-status-log-corroboration.json').read_bytes();log=json.loads(log_raw)
validate_calls(log);need(len(log['calls'])==1 and log['capture_complete'],'one nonclearing log read')
row=log['calls'][0];need('dmesg | grep QDFTcon_GetErrDetStatus | tail -n 15' in row['command'] and 'dmesg -' not in row['command'],'nonclearing bounded filter')
text=row['response']['commands'][0]['stdout'];lines=text.splitlines()
need(lines[0]=='0' and lines[1]==r['preflight']['boot_id'],'UID/boot corroboration')
pid=r['execution']['helper_pid'];status=int(r['execution']['result']['status_hex'],16)
pattern=re.compile(r'\[([0-9.]+)\].*QDFTcon_GetErrDetStatus\['+str(pid)+r':TconStatusRead\.\]: ERR DET Status:0x([0-9a-fA-F]+)$')
hits=[pattern.search(line) for line in lines];hits=[h for h in hits if h]
need(len(hits)==1 and int(hits[0].group(2),16)==status,'same PID/value raw QDF row')
report={'schema':'one-shot-host-status-replay-audit-v1','record_sha256':sha(raw),'corroboration_record_sha256':sha(log_raw),'root_calls':len(r['calls']),'exact_commands_and_record_replayed':True,'status_hex':r['execution']['result']['status_hex'],'helper_pid':pid,'execute_uptime_anchor':r['execution']['execute_uptime'],'qdf_log_time':float(hits[0].group(1)),'raw_qdf_line_matches_pid_and_value':True,'cleanup_confirmed':True,'controller_transaction_proved':False,'read_to_clear_excluded':False,'debug_override_excluded':False,'physical_state_observed':False,'repair_established':False}
(HERE/'host-status-runtime-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
