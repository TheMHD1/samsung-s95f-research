#!/usr/bin/env python3
"""Independent EH frozen-artifact and full-width source-byte tests; host mocks only."""
from pathlib import Path
import base64,copy,hashlib,importlib.util,json,struct,subprocess,sys
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent.parent;P=D.parent/'rtp-score-checkpoints-20261028dp';checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(x,s):
 global checks
 checks+=1
 if not x:raise ValueError(s)
def load(path,name,pin):
 raw=path.read_bytes();need(sha(raw)==pin,'module '+name);spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def reject(fn):
 try:fn()
 except (ValueError,KeyError,TypeError):need(True,'malformed refused');return
 raise ValueError('malformed accepted')
need(sha((D/'source-inventory.json').read_bytes())=='38ae37ba3e64c516d0e9aa5d2e811d7c6d85e0164f6a155e3bb93ff0990991fd','frozen37file inventory')
inv=json.loads((D/'source-inventory.json').read_text());need(len(inv['files'])==37,'37 files')
for f in inv['files']:
 b=(D/f['path']).read_bytes();need(len(b)==f['bytes']and sha(b)==f['sha256'],'all inventory '+f['path'])
need(sha((D/'deployment-manifest.json').read_bytes())=='d0059b32e4e3d99a398a3763934e8927cd2967126c6d1ad9e76d8bf069f3059e','manifest pin')
need(sha((D/'bin/Release/net6.0/RefreshCheckpoints.dll').read_bytes())=='7ea168e30685a75e474774b0893f631d30fd28fea944f7360f62de25a461af19','DLL pin')
for name in ('NativeBinding.cs','OnsetKey.cs'):need((D/name).read_bytes()==(P/name).read_bytes(),'unchanged '+name)
old=(P/'Program.cs').read_text();expected=old.replace('20_000_000','15_000_000').replace('MaxCycles = 80','MaxCycles = 60').replace('managed-usb-rt-synchronized-key-dp-v1','managed-usb-rt-synchronized-key-eh-v1').replace('durationMs = 20000, maxCycles = 80','durationMs = 15000, maxCycles = 60');need((D/'Program.cs').read_text()==expected,'entire Program exact schema/budget delta including Run/ReadPair/ReadSet')
r=load(D/'run-once.py','eh_review_wrapper','4870a6a0c089a739e6bc8af4f3b9076dc73bc5cf21123a2a0b8305ef206dfc15');p=load(D/'parse-result.py','eh_review_parser','1de2a8f769f4a801b85f2dff74bb840221e0394db8ec7acb9cffdd7a763d5229')
manifest,payload=r.build_manifest();need(r.manifest_bytes(manifest)==(D/'deployment-manifest.json').read_bytes(),'regenerated exact manifest');need(len(payload)==3,'three payloads')
need(manifest['nativeDurationUs']==15000000 and manifest['nativeMaxCycles']==60 and manifest['checkpointRecordBytes']==54 and manifest['nominalPeriodUs']==250000,'native config budgets')
need(manifest['structuredReceiptCap']==24576 and manifest['rootResponseCap']==65536 and manifest['rootTimeoutSeconds']==45 and manifest['hostTimeoutSeconds']==75,'inherited caps/deadlines')
# Host fixture path is pure FakeOps; never --execute.
cmd=['${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet',str(D/'bin/Release/net6.0/RefreshCheckpoints.dll'),'--checkpoint-fixture-full'];out=subprocess.run(cmd,check=True,capture_output=True);need(out.stderr==b'','fixture stderr');native=json.loads(out.stdout);_,_,_,_,q=p.parse_native(out.stdout.decode());need(q['trialQualified'],'full fixture qualified')
raw=base64.b64decode(native['scoreCheckpoints']['rawBase64']);need(len(raw)==60*54,'54x60bytes')
# Only native retained source bytes justify equality; allow all u16/u32 values without invented pointer/gate semantics.
complete=[c for c in native['retained']if len(c['windows'])==8 and len(c['transfers'])==16];baseline=next(c for c in complete if c['cycleIndex']==1);need(len(complete)==3,'three distinct full retained cycles')
fields=[(34,1,2,2,'mCpu4a2U16'),(36,1,4,2,'mCpu4a4U16'),(38,1,34,2,'mCpu4c2U16'),(40,1,36,2,'mCpu4c4U16'),(42,7,0x60,2,'endRRoot2460U16'),(44,7,0x6e,2,'endRRoot246eU16'),(46,3,4,4,'capturedDynamicAPointerU32'),(50,3,8,4,'capturedDynamicBPointerU32')]
def repack(n,b):n['scoreCheckpoints'].update(rawBase64=base64.b64encode(b).decode(),sha256=sha(b))
for dest,wi,src,length,key in fields:
 n=copy.deepcopy(native);cp=bytearray(raw);cap=next(c for c in n['retained']if c['cycleIndex']==1);w=cap['windows'][wi];b=bytearray(base64.b64decode(w['rawBase64']));b[src:src+length]=bytes([255])*length;w.update(rawBase64=base64.b64encode(b).decode(),sha256=sha(b));cp[dest:dest+length]=bytes([255])*length;repack(n,cp)
 _,_,_,_,qq=p.parse_native(json.dumps(n));need(qq['scoreCheckpoints']['rows'][0][key]==(1<<(8*length))-1,'full-width exact raw-source acceptance '+key)
 cp[dest]^=1;repack(n,cp);reject(lambda:p.parse_native(json.dumps(n)))
 # Matching compact data must never be recomputed from start R for the end-R fields.
 if wi==7:
  n=copy.deepcopy(native);cap=next(c for c in n['retained']if c['cycleIndex']==1);w=cap['windows'][0];b=bytearray(base64.b64decode(w['rawBase64']));b[src:src+length]=bytes([255])*length;w.update(rawBase64=base64.b64encode(b).decode(),sha256=sha(b));_,_,_,_,qq=p.parse_native(json.dumps(n));need(qq['scoreCheckpoints']['rows'][0][key]!=(1<<(8*length))-1,'endR field ignores different startR '+key)
# A discarded intermediate cycle has compact raw-source values without retained raw recomputation, and no alias/epoch guarantee.
n=copy.deepcopy(native);cp=bytearray(raw);cp[54+34:54+54]=bytes([255])*20;repack(n,cp);_,_,_,_,qq=p.parse_native(json.dumps(n));need(qq['scoreCheckpoints']['rows'][1]['capturedDynamicBPointerU32']==0xffffffff,'unretained pointer word remains a word, not address-qualified')
for prefix in ('[GC_INFO]\n','garbage\n'):reject(lambda:p.parse_native(prefix+out.stdout.decode()))
for key,value in [('count',61),('recordBytes',34)]:
 n=copy.deepcopy(native);n['scoreCheckpoints'][key]=value;reject(lambda:p.parse_native(json.dumps(n)))
for k,v in [('cyclesStarted',80),('deadlineUs',native['startUs']+20000000),('headersSent',488),('bulkTransfers',976)]:
 n=copy.deepcopy(native);n[k]=v;reject(lambda:p.parse_native(json.dumps(n)))
# All timing and clock-failure transport rules are inherited source-identically; explicit budget check above prevents80-cycle projection.
need('15s cooperative observation'in q['scoreCheckpoints']['limitations'][0]and not q['scoreCheckpoints']['everyComparatorCallObserved'],'scope15s samplednotcallback')
print(json.dumps({'accepted':True,'checks':checks,'inventoryFiles':37,'payloadBytes':sum(len(x)for x in payload.values()),'targetOperations':0,'networkOperations':0,'fullWidthSourceWordTests':8,'originalPrefixBytes':34,'recordBytes':54,'maximumCheckpoints':60}))
