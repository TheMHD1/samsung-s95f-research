#!/usr/bin/env python3
"""Finite GA source equivalence; no target helpers or root adapter imported."""
import ast,hashlib,json,types
from pathlib import Path
P=Path(__file__).resolve().parent;B=P.parent;FN=B/'combined-event-successor-20261028fn';checks=0
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def check(ok,label):
 global checks
 if not ok:raise ValueError(label)
 checks+=1
def load(path):
 module=types.ModuleType(path.stem);module.__file__=str(path);exec(compile(path.read_bytes(),str(path),'exec'),module.__dict__);return module
pins=json.loads((P/'input-pins.json').read_bytes())['files']
for row in pins:
 raw=(B/row['path']).read_bytes();check(len(raw)==row['bytes']and sha(raw)==row['sha256'],'external pin '+row['path'])
delta=json.loads((P/'production-delta.json').read_bytes())
for name,entry in delta['files'].items():
 lines=(FN/entry['base']).read_text().splitlines(True);out=[];at=0
 for hunk in entry['hunks']:
  check(type(hunk['oldStart'])is int and at<=hunk['oldStart']<=hunk['oldEnd']<=len(lines),'bounded ordered delta')
  check(''.join(lines[hunk['oldStart']:hunk['oldEnd']])==hunk['old'],'exact old delta')
  out.extend(lines[at:hunk['oldStart']]);out.append(hunk['new']);at=hunk['oldEnd']
 out.extend(lines[at:]);check(''.join(out)==(P/name).read_text(),'entire derivative source reconstructed '+name)
def funcs(path):return {node.name:node for node in ast.parse(path.read_bytes()).body if isinstance(node,ast.FunctionDef)}
def dump(node):return ast.dump(node,include_attributes=False)
old=funcs(FN/'run-once.py');new=funcs(P/'run-once.py')
for name in old.keys()-{'build_manifest','execute','main'}:
 text=ast.unparse(old[name]).replace('fn-combined-event-','ga-live-saver-event-')
 check(dump(ast.parse(text).body[0])==dump(new[name]),'inherited function unchanged '+name)
source=(FN/'run-once.py').read_text();expected=ast.get_source_segment(source,old['execute'])
for before,after in [
 ("wake=load_pinned(HERE/'wake-check.py',WAKE_SHA,'fn_frozen_fc_wake')","cached=load_pinned(HERE/'cached-check.py',CACHED_SHA,'ga_cached_live_saver')"),
 ('wake.','cached.'),('wakeCheckpoint','cachedCheckpoint'),('wake-checkpoint.json','cached-checkpoint.json'),
 ('fn-combined-event-','ga-live-saver-event-'),('fn-primary-native-outcome-v1','ga-primary-native-outcome-v1'),
 ('def call(command, native_submission=False, ui_wake_submission=False):','def call(command, native_submission=False):'),
 ("        if ui_wake_submission:record['wrapperUiOperations']=1\n",''),
 ("'visible_wake_checkpoint'","'cached_live_saver_checkpoint'"),('firstUiCallIndex','firstCachedCallIndex'),('lastUiCallIndex','lastCachedCallIndex'),
 ("'wrapperUiOperations':1","'expectedCachedTab':'Live','cachedSaverRequired':True,'intendedNativeAction':'saver-wake-from-cached-Live','wrapperUiOperations':0"),
 ("primary={'schema':'ga-primary-native-outcome-v1',","primary={'schema':'ga-primary-native-outcome-v1','wrapperUiOperations':0,'expectedCachedTab':'Live','cachedSaverRequired':True,'intendedNativeAction':'saver-wake-from-cached-Live',")]:
 check(before in expected,'specific execute substitution exists');expected=expected.replace(before,after)
check(dump(ast.parse(expected).body[0])==dump(new['execute']),'complete execute AST differs only explicit wrapper changes')
for name in ['run','payload_guard']:
 a=next(node for node in ast.walk(old['execute'])if isinstance(node,ast.FunctionDef)and node.name==name)
 b=next(node for node in ast.walk(new['execute'])if isinstance(node,ast.FunctionDef)and node.name==name)
 check(dump(a)==dump(b),'native command/payload guard byte-equivalent AST '+name)
old_cached=funcs(FN/'wake-check.py');cached=funcs(P/'cached-check.py')
check(dump(cached['snapshot_command'])==dump(old_cached['snapshot_command']),'exact existing cached getter command')
expected=ast.get_source_segment((FN/'wake-check.py').read_text(),old_cached['parse_snapshot']).replace('Apps','Live').replace('d/apps.tab','d/ug.tab@Live')
check(dump(ast.parse(expected).body[0])==dump(cached['parse_snapshot']),'cached decoder only exact Live substitution')
for name in ['wake_command','key_status']:check(name not in cached,'no wrapper key function '+name)
for name in ['cached-check.py','prepare-readiness.py','run-once.py']:
 text=(P/name).read_text();check(not any(key in text for key in ['input_keyevent','XF86AudioRaiseVolume','prepare-live.py','--preparation']),'no wake/preparation/key implementation '+name)
r=load(P/'run-once.py');fn=load(FN/'run-once.py');manifest,payload=r.build_manifest();check(payload==fn.build_manifest()[1],'all three native payload bytes identical')
check(r.PARSER_SHA==fn.PARSER_SHA and r.CHECKPOINT_SHA==fn.CHECKPOINT_SHA and r.ROOT_SHA==fn.ROOT_SHA,'exact native parser/checkpoint/root pins')
check([manifest[name]for name in ['rootTimeoutSeconds','hostTimeoutSeconds','rootCommandCap','rootResponseCap','structuredReceiptCap','wholeCooperativeBudgetUs','cleanupReserveUs','keyJoinReserveUs']]==[45,75,8192,65536,24576,40000000,26000000,7000000],'unchanged caps/budgets')
check(manifest['wrapperUiOperations']==0 and manifest['expectedCachedTab']=='Live'and manifest['cachedSaverRequired']is True,'truthful GA premise/zero wrapper UI')
check('/tmp/researcher-fn-'in(P/'run-once.py').read_text(),'native stage family unchanged')
check(not any((P/name).exists()for name in ['Engine.cs','Protocol.cs','OnsetKey.cs','parse-result.py','prepare-live.py','CombinedEventSuccessor.dll']),'no native/parser/preparation copies')
engine=(FN/'Engine.cs').read_text();check(engine.index('LoggerR(pre,0);Need(ClassifyRt(pre)==RtState.Clean')<engine.index('WriteLogger(ops,clock,x,fd,ref phase,true)')<engine.index('key?.Start(clock)'),'unchanged native clean-before-arm-before-key gate')
print(json.dumps({'schema':'ga-source-validation-v1','checks':checks,'externalInputs':len(pins),'nativeAndParserUnchanged':True,'nativeCommandAndPayloadGuardUnchanged':True,'executeFiniteDeltaOnly':True,'cachedGetterCommandUnchanged':True,'wrapperKeys':0,'liveSaverMode2Implemented':False,'targetOperations':0},sort_keys=True))
