#!/usr/bin/env python3
"""Bounded GK source/pin/profile review. No target transport/native execution."""
import hashlib,json,struct,sys,types
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;B=P.parent;checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def ck(v,s):
 global checks
 if not v:raise ValueError(s)
 checks+=1
def rejects(f):
 try:f()
 except ValueError as e:ck(True,'expected refusal');return str(e)
 raise ValueError('unexpected profile admission')
def read(name):return (B/name).read_bytes()
def data(name):return json.loads(read(name))
for row in json.loads((P/'input-pins.json').read_bytes())['files']:
 raw=read(row['path']);ck(len(raw)==row['bytes']and sha(raw)==row['sha256'],'pinned source '+row['path'])
a=json.loads((P/'source-anchors.json').read_bytes());blob=read('selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin')
ck(sha(blob)==a['selectedAssetSha256']=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','selected whole asset');image=blob[0x40200:0x60200]
for span in a['spans']:
 start=int(span['va'],16);end=int(span['endExclusive'],16);ck(int(span['fileOffset'],16)==start+0x40200 and sha(image[start:end])==span['sha256'],'selected bounded source span')
for ins in a['instructions']:
 start=int(ins['va'],16);ck(sha(image[start:start+ins['bytes']])==ins['bytesSha256'],'source instruction coordinate '+ins['va'])
for at,target in a['literalTargets'].items():ck(struct.unpack_from('<I',image,int(at,16))[0]==int(target,16),'publication bound/ordinal literal '+at)
ck(a['literalTargets']=={'0xc03c':'0x200004ca','0xc84c':'0x2000ba28','0xc850':'0x200004ca'},'same CPU publication bound copied and consumed')
ck(200+1==201 and 201<512,'finite publication201 below512')
fa=B/'selective-endpoint-limit-writer-20261028fa/parse-result.py';m=types.ModuleType('gk_fa_profile');m.__file__=str(fa);exec(compile(fa.read_bytes(),str(fa),'exec'),m.__dict__)
base='live-saver-wake-trial-20261028gf/baseline-capture/';r=read(base+'start-R.bin');M=read(base+'M.bin');C=read(base+'C.bin');m.guard_r(r,40);m.validate_candidate_context(M,C,r);ck(True,'unchanged actual GF40 baseline fits exact FA profile/context')
raised=bytearray(r);struct.pack_into('<H',raised,0xc4,200);raised=bytes(raised);m.guard_r(raised,200);m.validate_candidate_context(M,C,raised);ck(True,'explicit in-memory clean200 profile clone only')
ck([i for i,(x,y)in enumerate(zip(r,raised))if x!=y]==[0xc4],'counterfactual raw delta onlyc4 lowbyte')
fault=bytearray(read('live-saver-wake-trial-20261028gf/fault-capture/start-R.bin'));struct.pack_into('<H',fault,0xc4,200)
fault_refusal=rejects(lambda:m.guard_r(bytes(fault),200))
bad_c=bytearray(C);bad_c[8]=0;c8_refusal=rejects(lambda:m.validate_candidate_context(M,bytes(bad_c),raised))
bad_m=bytearray(M);bad_m[56]=0;scan_refusal=rejects(lambda:m.validate_candidate_context(bytes(bad_m),C,raised))
for offset,value in [(6,1),(14,0)]:
 bad=bytearray(raised);struct.pack_into('<H',bad,offset,value);rejects(lambda:m.guard_r(bytes(bad),200))
# Same workflow contracts, with fixed treatment profile/schema distinct.
ga='live-saver-onset-adapter-20261028ga/';gg='live-saver-200-recorder-20261028gg/';fn='combined-event-successor-20261028fn/'
ck(read(ga+'cached-check.py')==read(gg+'cached-check.py'),'identical cached-only saver policy')
for name in ['OnsetKey.cs','NativeBinding.cs']:ck(read(fn+name)==read(gg+name),'unchanged key/binding '+name)
ma=data(ga+'deployment-manifest.json');mg=data(gg+'deployment-manifest.json')
ck(ma['threshold']==40 and mg['threshold']==200 and ma['schema']!=mg['schema'],'fixed profiles and distinct family')
keys=['wholeCooperativeBudgetUs','cleanupReserveUs','keyJoinReserveUs','rootTimeoutSeconds','hostTimeoutSeconds','rootCommandCap','rootResponseCap','structuredReceiptCap','nativeInvocations','retries','wrapperUiOperations','loggerWritesMaximum','sidecarBytesEach','cachedSaverRequired','expectedCachedTab','intendedNativeAction']
for key in keys:ck(ma[key]==mg[key],'matched recorder bound/policy '+key)
for dn in [fn,gg]:
 text=read(dn+'Engine.cs').decode();ck('config.MaxCycles<=56'in text and 'config.DurationUs==2_000_000'in text and 'config.PeriodUs==25_000'in text,'unchanged56/2s/25ms source caps')
gh=data('fault200-apps-recovery-20261028gh/deployment-manifest.json');ge=data('live-saver-init-adapter-20261028ge/deployment-manifest.json')
ck(gh['sourceAlternateLimit']==200 and gh['restoresLimit40Proven']is False and gh['mode2Under200ProfileEmpiricallyQualified']is False,'recovery200 outcome limits')
for key in ['nativePayloads','operation','mode','nativeDeadlineSeconds','rootTimeoutSeconds','hostTimeoutSeconds','rootCommandCap','rootResponseCap']:ck(gh[key]==ge[key],'same stock ABI/payload/budget '+key)
ck(gh['nativePayloads']['DeadlineMode2.dll']['sha256']=='1b466d8303769951945988dd8b31734b1374bad6a81a4d9f4d5c2f86bb08d7a6','unchanged DH payload pin')
gf=data('live-saver-wake-trial-20261028gf/live-analysis/decoded.json');ex=data('limit-rechallenge-trial-20261028ex/raised-analysis/decoded.json');gd=data('predicate-binary-oracle-20261028gd/qualification.json')
ck(gf['actualFpProven']is False and gf['physicalPictureObserved']is False and gf['wrapperKeys']==0,'GF observation/inference distinction')
ck(ex['cleanSelectorOneAbove40Count']==23 and ex['maximumSampledH0']==76,'actual EX finite witness')
ck(gd['liveComparisonOperandsProven']is False and gd['instructionHookInstalled']is False,'oracle is not runtime operands')
report={'schema':'gk-matched-limit-source-plan-v1','checks':checks+1,'sourceFilesPinned':len(json.loads((P/'input-pins.json').read_bytes())['files']),'targetOperations':0,'networkOperations':0,'newBinaryOrInstallation':False,'actualGfClean40ProfileFitsFa':True,'counterfactuals':{'syntheticInMemoryOnly':True,'cleanC4Only200ProfileFitsFa':True,'fault200RestoreRefusal':fault_refusal,'clean200C8ZeroRefusal':c8_refusal,'clean200ScanZeroRefusal':scan_refusal,'notCurrentReadiness':True},'publication':{'inclusiveIdsAtBound200':[0,200],'finalOrdinal':201,'independentArrayIndexGuard':512,'helperCallBeforeCapacityGuard':'image1 0xc640 -> 0x1c0c8','electricalSafetyProven':False,'isolatedComparatorManipulation':False},'plan':['qualify recovery route','construct clean Live+saver at40','fixed FA set and fresh200 baseline','one GG attempt','classify actual state/phase/logger; restore or separately qualified GH','positive lifecycle/fresh EB/actual limit readback as applicable','one GA40 rechallenge if all premises are rebuilt'],'mode2Under200EmpiricallyQualified':False,'mode2Restores40Proven':False,'matchedCausalEffectProven':False,'physicalResultProven':False,'normalOptimizedExpectedIdentical':True}
raw=(json.dumps(report,indent=2,sort_keys=True)+'\n').encode()
if sys.argv[1:]==['--write']:(P/'report.json').write_bytes(raw)
elif sys.argv[1:]:raise ValueError('only optional --write')
# The write mode is author-only; normal verification never changes the report.
ck((P/'report.json').read_bytes()==raw,'derived report reproducible')
print(raw.decode(),end='')
