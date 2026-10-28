#!/usr/bin/env python3
"""Read-only EM frozen source/host test review; output confined to reviews."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
H=Path(__file__).resolve().parent;D=H.parent;B=D.parent;EH=B/'rtp-refresh-checkpoints-20261028eh';DOTNET=Path('${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet')
sha=lambda b:hashlib.sha256(b).hexdigest();checks=0

def need(ok,label):
 global checks
 checks+=1
 if not ok:raise ValueError(label)
pins={'source-inventory.json':'57f39a8f4041944d4cb2515b03c25fabedcc6b5de37206d65bbeb23306ee8be2','deployment-manifest.json':'83382d9a55271194480cb17d777a0d45737128f3dd849228b9517c3d2284c522','run-once.py':'01b5937f625e45516d435e6093cef47aebde9cbf1380e997173f238eab9e9308','parse-result.py':'cfa98869b725ce86d9bab876e7a59c554f690b75f77e17e22de035b214cdc49c','bin/Release/net6.0/DenseRefreshCheckpoints.dll':'ce1918d9aae89d5a0529482c529bac1a99381c6ebe32f2305b4a345499bafc2a','host-build-checkpoint.json':'f57c882db57db0207bb2ee2899cb36d26e5d9ba0ec08c67fe5568fb17d6c6d4c'}
for name,pin in pins.items():need(sha((D/name).read_bytes())==pin,'final frozen pin '+name)
rows=json.loads((D/'source-inventory.json').read_text())['files'];need(len(rows)==44,'44 frozen files')
for row in rows:
 b=(D/row['path']).read_bytes();need(len(b)==row['bytes']and sha(b)==row['sha256'],'frozen inventory '+row['path'])
for n in ['NativeBinding.cs','OnsetKey.cs','NuGet.Config']:need((D/n).read_bytes()==(EH/n).read_bytes(),'unchanged '+n)
s=(EH/'Program.cs').read_text().replace('DurationUs = 15_000_000','DurationUs = 2_000_000').replace('public long PeriodUs = 250_000','public long PeriodUs = 25_000').replace('key-eh-v1','key-em-v1').replace('durationMs = 15000','durationMs = 2000').replace('nominalPeriodMs = 250','nominalPeriodMs = 25')
need(s==(D/'Program.cs').read_text(),'whole Program delta exactly permitted defaults/schema/dry metadata')
need((EH/'ScoreCheckpoints.cs').read_text().replace('eh-refresh-checkpoints-v1','em-dense-refresh-checkpoints-v1')==(D/'ScoreCheckpoints.cs').read_text(),'checkpoint schema-only54B delta')
need((EH/'ReceiptMain.cs').read_text().replace('researcher-eh-','researcher-em-')==(D/'ReceiptMain.cs').read_text(),'receipt prefix-only delta')
need((EH/'transport-parser.py').read_text().replace('15_000_000','2_000_000')==(D/'transport-parser.py').read_text(),'transport deadline-only delta')
bootstrap='''import pathlib,runpy,sys,tempfile
orig=tempfile.TemporaryDirectory
class OwnedTemp(orig):
 def __init__(self,*a,**kw):
  if kw.get('dir') is not None:kw['dir']=sys.argv[2]
  super().__init__(*a,**kw)
tempfile.TemporaryDirectory=OwnedTemp
runpy.run_path(sys.argv[1],run_name='__main__')
'''
env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(H/'tmp'),DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1')
results=[]
for optimized in (False,True):
 for test in ['verify_source.py','test-parse-result.py','test-runner.py','test-timing.py','test-readiness.py']:
  argv=[sys.executable]+(['-O']if optimized else[])+['-B','-c',bootstrap,str(D/test),str(H/'tmp')]
  r=subprocess.run(argv,cwd=H,env=env,capture_output=True,timeout=60);need(r.returncode==0 and not r.stderr,'host test '+test)
  text=r.stdout.decode();suffix='optimized'if optimized else'normal';(H/(test+'.'+suffix+'.stdout')).write_text(text)
  if test in ('verify_source.py',):value=json.loads(text)
  else:value=json.loads(text.splitlines()[-1])
  results.append({'test':test,'optimized':optimized,'returncode':r.returncode,'stdoutSha256':sha(r.stdout),'summary':value})
# Native fixture-only checks: each switch is a retained FakeOps/host mode, never --execute.
native=[]
for switch in ['--self-test','--key-self-test','--checkpoint-self-test','--checkpoint-fixture-clean']:
 r=subprocess.run([str(DOTNET),str(D/'bin/Release/net6.0/DenseRefreshCheckpoints.dll'),switch],cwd=H,env=env,capture_output=True,timeout=20)
 need(r.returncode==0 and not r.stderr,'managed host-only '+switch);v=json.loads(r.stdout)
 if switch=='--checkpoint-fixture-clean':
  need(v['terminalReason']=='CycleLimit'and v['cyclesStarted']==60 and v['deadlineUs']-v['startUs']==2_000_000 and v['headersSent']==480 and v['bulkTransfers']==960,'60 cycle actual fake2s ceiling')
  native.append({'switch':switch,'bytes':len(r.stdout),'sha256':sha(r.stdout),'cycleCap':60,'headers':480,'bulks':960,'fakeSpanUs':v['endUs']-v['startUs']})
 else:
  if switch=='--checkpoint-self-test':need(v['maxTestOutputBytes']+1==24256 and 24576-(v['maxTestOutputBytes']+1)==320,'native maximum serialized receipt plusnewline cap')
  native.append({'switch':switch,'summary':v,'stdoutSha256':sha(r.stdout)})
for row in rows:need(sha((D/row['path']).read_bytes())==row['sha256'],'all functional bytes unchanged after host checks')
value={'schema':'em-independent-host-review-v1','accepted':True,'checks':checks,'frozenPins':pins,'frozenFilesVerified':len(rows),'sourceDeltaScope':'exactEHdefaults/schema/prefix/pins;allnativebinding/readpair/run/keyunchanged','tests':results,'nativeHostOnly':native,'targetCalls':0,'networkCalls':0,'realRootAdapterImported':False,'outputOnlyReviews':True,'temporaryDirectoryOverride':'testreadiness hardcoded scratch redirected into owned reviews/tmp;testlogic unchanged'}
(H/'independent-validation.json').write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
print(json.dumps({'accepted':True,'checks':checks,'tests':len(results),'validationSha256':sha((H/'independent-validation.json').read_bytes()),'targetCalls':0,'networkCalls':0}))
