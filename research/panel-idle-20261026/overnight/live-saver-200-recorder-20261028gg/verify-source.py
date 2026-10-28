#!/usr/bin/env python3
"""GG exact source-delta audit; no target helper or real root import."""
import ast,hashlib,json,re,types
from pathlib import Path
P=Path(__file__).resolve().parent;B=P.parent;FN=B/'combined-event-successor-20261028fn';GA=B/'live-saver-onset-adapter-20261028ga';checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def ck(v,s):
 global checks
 if not v:raise ValueError(s)
 checks+=1
def load(path):
 m=types.ModuleType(path.stem);m.__file__=str(path);exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m
for row in json.loads((P/'input-pins.json').read_bytes())['files']:
 raw=(B/row['path']).read_bytes();ck(len(raw)==row['bytes']and sha(raw)==row['sha256'],'external source pin '+row['path'])
for name in ['NativeBinding.cs','OnsetKey.cs','NuGet.Config']:ck((P/name).read_bytes()==(FN/name).read_bytes(),'byte-identical '+name)
changes={'Protocol.cs':[('combined-event-checkpoints-fn-v1','live-saver-event200-gg-v1'),('Half(value,0xc4)!=40','Half(value,0xc4)!=200'),('Half(value, 0xc4) == 40','Half(value, 0xc4) == 200')], 'Engine.cs':[('known RT at40','known RT at200'),('combined-event-checkpoints-fn-v1','live-saver-event200-gg-v1'),('threshold=40,','threshold=200,')], 'ScoreCheckpoints.cs':[('fg-stockevent-checkpoints-v1','gg-stockevent200-checkpoints-v1')], 'ReceiptMain.cs':[('/tmp/researcher-fn-','/tmp/researcher-gg-'),('fn-dry-v1','gg-dry-v1'),('\\\"threshold\\\":40','\\\"threshold\\\":200'),('      if(args.Length==1&&args[0]=="--fixture")','      if(args.Length==1&&args[0]=="--branch-fixtures"){Console.WriteLine(BranchFixtures());return 0;}\n      if(args.Length==1&&args[0]=="--fixture")')]}
for name,items in changes.items():
 expected=(FN/name).read_text()
 for old,new in items:ck(old in expected,'explicit old production anchor');expected=expected.replace(old,new)
 ck(expected==(P/name).read_text(),'entire runtime production delta '+name)
ck((FN/'CombinedEventSuccessor.csproj').read_text().replace('CombinedEventSuccessor','CombinedEvent200')==(P/'CombinedEvent200.csproj').read_text(),'assembly-name-only csproj change')
parser=(FN/'parse-result.py').read_text()
for old,new in [('Strict FN receipt','Strict GG fixed200 receipt'),("half(b,0xc4)==40,'R fixed40'","half(b,0xc4)==200,'R fixed200'"),("'combined-event-checkpoints-fn-v1'and v['threshold']==40","'live-saver-event200-gg-v1'and v['threshold']==200"),("'fg-stockevent-checkpoints-v1'","'gg-stockevent200-checkpoints-v1'"),('half(b,2)==half(b,4)==40','half(b,2)==half(b,4)==200')]:ck(old in parser,'explicit parser anchor');parser=parser.replace(old,new)
ck(parser==(P/'parse-result.py').read_text(),'complete parser finite threshold/family delta')
ck((P/'cached-check.py').read_bytes()==(GA/'cached-check.py').read_bytes(),'entire GA cached helper unchanged')
expected=(GA/'run-once.py').read_text()
for old,new in [("FN = B / 'combined-event-successor-20261028fn'",'FN = HERE'),("cp['schema']=='fn-host-checkpoint-v1'","cp['schema']=='gg-host-checkpoint-v1'"),("ASSEMBLY = 'CombinedEventSuccessor'","ASSEMBLY = 'CombinedEvent200'"),('/tmp/researcher-fn-','/tmp/researcher-gg-'),('ga-live-saver-event-','gg-live-saver200-event-'),('ga-primary-native-outcome-v1','gg-primary-native-outcome-v1'),('ga_cached_live_saver','gg_cached_live_saver'),("'threshold':40","'threshold':200"),('GA cached Live+saver','GG fixed200 cached Live+saver'),('adapter around unchanged FN native/parser','adapter around FN-derived fixed200 native/parser'),("'production-delta.json']","'production-delta.json','test-key-exposure.py']")]:ck(old in expected,'specific GA wrapper anchor');expected=expected.replace(old,new)
local=(P/'run-once.py').read_text()
for name in ['PARSER_SHA','CHECKPOINT_SHA']:
 pattern=name+" = '[0-9a-f]{64}'";m=re.search(pattern,local);ck(m is not None,'sealed native/parser pin');expected=re.sub(pattern,m[0],expected)
ck(expected==local,'entire wrapper only explicit package/threshold/family changes')
prepare=(GA/'prepare-readiness.py').read_text().replace('GA','GG').replace('ga_','gg_').replace('ga-','gg-').replace("'ga'","'gg'").replace('live-saver-onset-adapter-20261028ga','live-saver-200-recorder-20261028gg').replace('gg-live-saver-event-readiness-decision-v1','gg-live-saver200-event-readiness-decision-v1')
ck(prepare==(P/'prepare-readiness.py').read_text(),'exact fixed readiness builder family derivative')
# Independently verify every published delta reconstruction, including host-only test additions.
for name,entry in json.loads((P/'production-delta.json').read_bytes())['files'].items():
 lines=(B/entry['base']).read_text().splitlines(True);out=[];at=0
 for h in entry['hunks']:
  ck(type(h['oldStart'])is int and at<=h['oldStart']<=h['oldEnd']<=len(lines),'bounded ordered hunk');ck(''.join(lines[h['oldStart']:h['oldEnd']])==h['old'],'exact old hunk');out.extend(lines[at:h['oldStart']]);out.append(h['new']);at=h['oldEnd']
 out.extend(lines[at:]);ck(''.join(out)==(P/name).read_text(),'complete source reconstruction '+name)
r=load(P/'run-once.py');m,payload=r.build_manifest();ck(m['threshold']==200 and m['wrapperUiOperations']==0 and m['loggerWritesMaximum']==2,'fixed200/logger-only wrapper contract')
ck([m[n]for n in ['wholeCooperativeBudgetUs','cleanupReserveUs','keyJoinReserveUs','rootTimeoutSeconds','hostTimeoutSeconds','rootCommandCap','rootResponseCap','structuredReceiptCap']]==[40000000,26000000,7000000,45,75,8192,65536,24576],'budgets/caps untouched')
ck('020100000624014702000000'in(P/'Protocol.cs').read_text()and 'LoggerOnPayload={1,0},LoggerOffPayload={0,0}'in(P/'Engine.cs').read_text(),'same fixed logger address/payload bytes')
ck('Half(r,0x30)==200&&Half(r,0xc0)==200'in(P/'Engine.cs').read_text(),'fallback200 fields unchanged')
ck(not any(word in (P/'run-once.py').read_text()for word in ['input_keyevent','--set-limit','--restore-limit']),'no wrapper UI or threshold writer')
print(json.dumps({'schema':'gg-source-validation-v1','checks':checks,'nativeBindingAndOnsetKeyByteIdentical':True,'engineRunAndContextUnchanged':True,'cachedWorkflowExactGA':True,'thresholdWrites':0,'wholeBudgetUs':40000000,'targetOperations':0,'externalInputs':len(json.loads((P/'input-pins.json').read_bytes())['files'])},sort_keys=True))
