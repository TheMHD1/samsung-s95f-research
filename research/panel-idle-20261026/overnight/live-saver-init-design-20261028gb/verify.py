#!/usr/bin/env python3
"""Read-only source and retained EB qualification for GB design; no executor import."""
import hashlib,json,struct,types
from pathlib import Path
D=Path(__file__).resolve().parent;B=D.parent;checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def ck(v,s):
 global checks
 if not v:raise ValueError(s)
 checks+=1
pins=json.loads((D/'input-pins.json').read_bytes())['files']
for r in pins:
 raw=(B/r['path']).read_bytes();ck(len(raw)==r['bytes']and sha(raw)==r['sha256'],'pinned '+r['path'])
ei=(B/'refresh-checkpoint-trial-20261028ei/recover-eb-fault.py').read_text();bv=(B/'recovery-quickpath-20261027bv/recover.py').read_text();dh=(B/'autonomous-fault-harness-20261028dh/run-deadline-mode2.py').read_text();cs=(B/'autonomous-fault-harness-20261028dh/deadline-mode2/Program.cs').read_text()
ck('apps_gate'in ei and "nav.one_key('right'"in ei and 'helper.execute('in ei,'higher level UI admission')
ck('current_tab'not in dh and 'input_keyevent'not in cs and 'current_tab'not in cs and 'enlightenment_info'not in cs,'no intrinsic cachedtab/nativekey dependency found in inspected helper')
for needle in ['private const uint Request = 0xc010749f','private const uint Operation = 41','private const uint Mode = 2','alarm(12)','FileMode.CreateNew','receipt.Flush(true)','RuntimeInformation.ProcessArchitecture != Architecture.Arm','getuid()','geteuid()'] :ck(needle in cs,'native fixed anchor '+needle)
ck(cs.count('ioctlReturn = ioctl(fd, Request, ref value);')==1 and 'closeReturn = close(fd);'in cs,'fixed oneioctl/finallyclose')
for needle in ['working_status','GetPowerState','GetScreenState','BurnInProtectionInProgress',"int_values == ['1', '0']"]:ck(needle in bv,'public reject gate '+needle)
ck(dh.index('for command in render_stage(remote, payloads):')<dh.index('framed = adapter.root(command, record, root_path)'),'poststage insertion boundary')
helper=Path('autonomous-fault-harness-20261028dh');manifest=json.loads((B/helper/'deadline-mode2/build-manifest.json').read_bytes());ck(manifest['operation']==41 and manifest['mode']==2 and manifest['deadline_seconds']==12,'native deadline manifest')
for path,pin in manifest['files'].items():ck(sha((B/helper/'deadline-mode2'/path).read_bytes())==pin,'helper manifest dependency '+path)
file=B/'rtp-lane-gate-capture-20261028eb/parse-result.py';p=types.ModuleType('pure_eb');p.__file__=str(file);exec(compile(file.read_bytes(),str(file),'exec'),p.__dict__)
f=B/'combined-live-trigger-trial-20261028fw';v=f/'validation-capture';n,raws,q=p.parse_native((v/'native.receipt.json').read_text());r=json.loads((v/'result.json').read_bytes());ck(n['accepted']and n['device']==66 and n['headersSent']==16 and n['bulkTransfers']==32 and r['accepted']and r['cleanup']=='STAGE_ABSENT','latest accepted EB66')
for name,data,h in raws:ck((v/name).read_bytes()==data and sha(data)==h,'strict retained EB raw '+name)
ck(r['manifestSha256']=='e7df47861e25aca4df6fc18e82b646a53eada192451b9b16383c5b31a9f44a11'and r['rawFiles']==[{'name':name,'bytes':len(data),'sha256':h}for name,data,h in raws],'fixed EB result manifest/raw inventory')
r0=(v/'start-R.bin').read_bytes();r1=(v/'end-R.bin').read_bytes();ck(r0==r1 and [struct.unpack_from('<H',r0,i)[0]for i in [0,10,14,0xc4]]==[0,0,1,40]and struct.unpack_from('<H',r0,6)[0]==0,'latest full R clean40/logger0')
ck((v/'start-N.bin').read_bytes()==(v/'end-N.bin').read_bytes()==bytes(36),'latest N0')
identity=json.loads((f/'after-recovery-identity/identity.json').read_bytes());lifecycle=json.loads((f/'recovery-lifecycle-proof.json').read_bytes());ck(identity['devnum']=='66'and lifecycle['accepted']and lifecycle['oldDevice']==65 and lifecycle['newDevice']==66 and lifecycle['sameBoot']and lifecycle['sameDescriptors']and lifecycle['positiveDisconnectThenEnumeration'],'retained recovery identity premise')
ui=json.loads((f/'final-ui/before-summary.json').read_bytes());ck(ui['cached_current_tab']=='d/apps.tab'and ui['screensaver_windows_present']and ui['csfs_window_present'],'latest cached Apps+saver not Live candidate')
text=(D/'README.md').read_text()
for phrase in ['No intrinsic Apps/current-tab requirement was identified','not a relaxation of the frozen Apps','after staging, immediately before','No ScreenSaver launcher','no repair, wake']:
 ck(phrase in text,'claim/design boundary '+phrase)
m=(v/'M.bin').read_bytes();c=(v/'C.bin').read_bytes()
summary={'schema':'gb-live-saver-design-checkpoint-v1','checks':checks,'inputPins':len(pins),'implementationCreated':False,'intrinsicAppsDependencyFoundInInspectedHelper':False,'empiricalAppsPolicyPreservedAsHistory':True,'latestRetainedEb':{'device':66,'accepted':True,'headers':16,'bulks':32,'fullRStableClean40Logger0':True,'nZero':True,'aa':struct.unpack_from('<H',m,10)[0],'ac':struct.unpack_from('<H',m,12)[0],'scan':m[56],'c7':c[7],'c8':c[8]},'latestCachedUiIsAppsSaver':True,'liveSaverCandidateCurrentlyAdmitted':False,'liveSaverMode2ExperimentExecuted':False,'targetOperations':0,'rootCalls':0,'networkOperations':0}
print(json.dumps(summary,sort_keys=True,indent=2))
