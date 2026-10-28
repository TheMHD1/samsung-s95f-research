#!/usr/bin/env python3
"""Host-only exact DP delta proof. No root transport imports or target access."""
from pathlib import Path
import hashlib,json,re
D=Path(__file__).resolve().parent;P=D.parent/'rtp-score-checkpoints-20261028dp';E=D.parent/'reference-refresh-control-20261028eg'
sha=lambda b:hashlib.sha256(b).hexdigest();checks=0
def need(ok,s):
 global checks
 if not ok:raise ValueError(s)
 checks+=1
def part(s,a,b):return s[s.index(a):s.index(b,s.index(a))]
def file(name):return (D/name).read_text()
need(sha((P/'deployment-manifest.json').read_bytes())=='ba02517d7f8bb5cae6aa4257c426b7cc50780bfdfd5e0a73a7838e2386dff9ee','frozen DP manifest')
inv=json.loads((P/'source-inventory.json').read_text());pins={}
for row in inv['files']:
 n=row['path']
 if n in ('Program.cs','NativeBinding.cs','OnsetKey.cs','ReceiptMain.cs','ScoreCheckpoints.cs','transport-parser.py','parent-synchronized-parser.py','run-once.py','SynchronizedOnset.csproj'):
  b=(P/n).read_bytes();need(len(b)==row['bytes']and sha(b)==row['sha256'],'frozen DP '+n);pins[n]=row['sha256']
need(len(pins)==9,'complete parent scope')
for n in ('NativeBinding.cs','OnsetKey.cs'):need((D/n).read_bytes()==(P/n).read_bytes(),'byte-identical '+n)
old=(P/'Program.cs').read_text();new=file('Program.cs')
expected=old.replace('20_000_000','15_000_000').replace('MaxCycles = 80','MaxCycles = 60').replace('managed-usb-rt-synchronized-key-dp-v1','managed-usb-rt-synchronized-key-eh-v1').replace('durationMs = 20000, maxCycles = 80','durationMs = 15000, maxCycles = 60')
need(new==expected,'Program exact schema/default-budget-only delta')
for a,b in [('    static readonly WindowSpec R','    readonly record struct Identity'),('    static PairResult ReadPair','    static PairResult ReadSet'),('    static PairResult ReadSet','    static CaptureDto ToDto'),('    static Outcome Run','    // sysfs binary attributes')]:need(part(new,a,b)==part(old,a,b),'unchanged controller section '+a.strip())
need('alarm'not in new+file('NativeBinding.cs')+file('ReceiptMain.cs')+file('OnsetKey.cs'),'no invented native40s alarm; exact inherited cooperative deadline')
s=file('ScoreCheckpoints.cs');oldscore=(P/'ScoreCheckpoints.cs').read_text()
need(part(s,'   Need(Count<Capacity','   // Appended source bytes only:')==part(oldscore,'   Need(Count<Capacity','   Count++;'),'original34-byte builder prefix unchanged')
need('Size=54, Capacity=60'in s and 'readonly byte[] raw=new byte[Size*Capacity]'in s,'rigid54/60 storage')
for source,offset,dest,length in [('m','2',34,2),('m','4',36,2),('m','0x22',38,2),('m','0x24',40,2),('e','0x60',42,2),('e','0x6e',44,2),('p','4',46,4),('p','8',50,4)]:need(f'Array.Copy({source},{offset},raw,at+{dest},{length})'in s,'exact appended source '+str(dest))
need('e=c.Windows[7].Buffer'in s and 'm=c.Windows[1].Buffer,p=c.Windows[3].Buffer'in s,'endR and earlier M/P indices')
receipt=(P/'ReceiptMain.cs').read_text().replace('/tmp/researcher-dp-','/tmp/researcher-eh-').replace('==44','==46').replace('checkpointTestsPassed=44','checkpointTestsPassed=46')
need(receipt==file('ReceiptMain.cs'),'same exclusive receipt helpers/entrypoint and no added transport call')
t=(P/'transport-parser.py').read_text()
for a,b in [('1, 80)','1, 60)'),('20_000_000','15_000_000'),('0, 80)','0, 60)'),('0, 79)','0, 59)'),('80-cycle','60-cycle'),('cycle 80','cycle 60'),('post-fault five-read','post-fault seven-read'),('0, 647)','0, 487)'),('0, 1294)','0, 974)'),('clean == 80','clean == 60')]:t=t.replace(a,b)
need(t==file('transport-parser.py'),'transport decoder exact budget-only narrowing')
f=(P/'parent-synchronized-parser.py').read_text();f=re.sub(r'PARENT_SHA = "[^"]+"', 'PARENT_SHA = "'+sha(t.encode())+'"',f)
# Parent uses a single-quoted pin in some retained variants.
f=re.sub(r"PARENT_SHA = '[^']+'", "PARENT_SHA = '"+sha(t.encode())+"'",f)
need(f==file('parent-synchronized-parser.py'),'key parser unchanged except derived transport pin')
w=(P/'run-once.py').read_text().replace("ASSEMBLY = 'ScoreCheckpoints'","ASSEMBLY = 'RefreshCheckpoints'").replace('dp-score-checkpoint','eh-refresh-checkpoint').replace('/tmp/researcher-dp-','/tmp/researcher-eh-').replace("'checkpointTestsPassed':44","'checkpointTestsPassed':46").replace("'nativeDurationUs': 20000000, 'writes': 0","'nativeDurationUs': 15000000, 'nativeMaxCycles': 60, 'checkpointRecordBytes': 54, 'nominalPeriodUs': 250000, 'writes': 0")
def unpin(s):return re.sub(r"(CHECKPOINT_SHA|PARSER_SHA) = '[^']+'",r"\1 = '<PIN>'",s)
need(unpin(w)==unpin(file('run-once.py')),'wrapper command/cleanup/ambiguity guards unchanged, schemas and budgets only')
need(file('SynchronizedOnset.csproj')==(P/'SynchronizedOnset.csproj').read_text().replace('<AssemblyName>ScoreCheckpoints</AssemblyName>','<AssemblyName>RefreshCheckpoints</AssemblyName>'),'assembly-only build setting change')
e=(E/'source-audit.json').read_bytes();need(sha(e)=='be0481dcd3f122122132c8b64e33d32c961a433f800fb5d1df71e7ee6cc74ce3','EG source proof pin');eg=json.loads(e)
for addr,value in [('0x38f8','0x20000500'),('0xb894','0x20000494'),('0xb898','0x20000498'),('0xc2f0','0x200004c2'),('0xc2f4','0x200004c4'),('0x1c1a4','0x20000498')]:need(eg['literals'][addr]==value,'EG literal '+addr)
need(0x20000500+0x6c7==0x20000bc7 and 0x200004a0+2==0x200004a2 and 0x20000490+4==0x20000494 and 0x20000490+8==0x20000498,'CPU source offsets')
lineage={'schema':'eh-source-lineage-v1','targetOperations':0,'networkOperations':0,'parentDpFiles':pins,'parentDpManifestSha256':'ba02517d7f8bb5cae6aa4257c426b7cc50780bfdfd5e0a73a7838e2386dff9ee','egSourceAuditSha256':sha(e),'nativeBindingControllerReadPairReadSetRunOneLeftUnchanged':True,'originalCompactPrefixBytes':34,'compactRecordBytes':54,'maximumCheckpoints':60,'cooperativeObservationUs':15000000,'nominalPeriodUs':250000,'perBulkTimeoutMs':2000,'rootTimeoutSeconds':45,'hostTimeoutSeconds':75,'nativeProcessAlarmImplemented':False,'newTargetReads':0,'newWrites':0,'newKeyCalls':0,'pointerAliasHeaderEpochOrActiveBranchProven':False,'refreshSequenceFullyObserved':False,'independentReviewPending':True,'buildRoute':'retained .NET6.0.428 SDK, no network; managed DLL host-built; native ARM32 execution unobserved'}
print(json.dumps({'schema':'eh-source-verification-v1','checksPassed':checks,'targetOperations':0,'lineage':lineage},indent=2))
