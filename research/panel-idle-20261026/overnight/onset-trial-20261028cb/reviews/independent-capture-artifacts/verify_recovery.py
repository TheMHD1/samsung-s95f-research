#!/usr/bin/env python3
"""Offline classification of the later, separate CB recovery record."""
from pathlib import Path
import hashlib,json,re
B=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
checks=0
def need(v,why):
 global checks
 if not v:raise ValueError(why)
 checks+=1
r=json.loads((B/'recovery/mode2.json').read_text());need(r['accepted'] is False and r['cleanup_confirmed'] is True,'rejected harness with cleanup')
need(r['error']=='ContractError: Remote command stderr','error classification')
matching=[]
for call in r['calls']:
 for item in call.get('response',{}).get('commands',[]):
  if 'HELPER_EXIT=' in item.get('stdout',''):matching.append(item)
need(len(matching)==1,'one returned native execution')
item=matching[0];need(item['exit_code']==0 and re.fullmatch(r'cat: /proc/[0-9]+/stat: No such file or directory\n',item['stderr']) is not None,'proc-exit race stderr')
for line in ['HELPER_EXIT=0','OPERATION_DECIMAL=41','MODE_DECIMAL=2','IOCTL_RETURN=0','CLOSE_RETURN=0','CLASSIFICATION=kernel_return_zero_only','RECOVERY_INFERRED=0','PHYSICAL_STATE_INFERRED=0']:
 need(line in item['stdout'].splitlines(),'retained native claim '+line)
need(not (B/'recovery/result.json').exists(),'no completed quickpath result')
need(json.loads((B/'recovery/mode2.result.json').read_text())['exit_code']==1,'quickpath child failure')
owner=json.loads((B/'owner-recovery-observation.json').read_text());need(owner['physicalAppsVisible'] and owner['physicalReturnExactTimeUs'] is None,'owner physical report scoped')
c=json.loads((B/'recovery-classification.json').read_text());need(c['mode2OverallAccepted'] is False and c['cleanupConfirmed'] is True and c['physicalRecoveryOwnerConfirmed'] is True and c['retries']==0 and c['postMode2Keys']==0,'parent classification preserves separation')
files=['recovery/mode2.json','recovery/mode2.result.json','recovery-classification.json','owner-recovery-observation.json']
v={'schema':'cb-independent-later-recovery-verification-v1','pass':True,'checks':checks,'target_operations_by_reviewer':0,'overall_mode2_harness_accepted':False,'cleanup_confirmed':True,'native_helper_exit_ioctl_close_reported_zero':True,'failure':'Remote stderr from exited helper /proc/PID/stat read','owner_physical_apps_return_reported':True,'exact_physical_return_time_known':False,'retrospective_change_to_onset_acceptance':False,'input_hashes':{f:hashlib.sha256((B/f).read_bytes()).hexdigest() for f in files}}
(O/'recovery-verification.json').write_text(json.dumps(v,indent=2,sort_keys=True)+'\n');print(json.dumps({'pass':True,'checks':checks,'overall_mode2_harness_accepted':False,'owner_apps_return_reported':True,'target_operations_by_reviewer':0}))
