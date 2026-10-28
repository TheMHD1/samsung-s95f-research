#!/usr/bin/env python3
"""Finite GE native-command/source equivalence; no live root imports."""
import ast,hashlib,json,types
from pathlib import Path
P=Path(__file__).resolve().parent;B=P.parent;checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def ck(v,s):
 global checks
 if not v:raise ValueError(s)
 checks+=1
def load(path):
 m=types.ModuleType(path.stem);m.__file__=str(path);exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m
def funcs(path):return {n.name:n for n in ast.parse(path.read_bytes()).body if isinstance(n,ast.FunctionDef)}
def dump(n):return ast.dump(n,include_attributes=False)
for row in json.loads((P/'input-pins.json').read_bytes())['files']:
 raw=(B/row['path']).read_bytes();ck(len(raw)==row['bytes']and sha(raw)==row['sha256'],'external input '+row['path'])
oldpath=B/'autonomous-fault-harness-20261028dh/run-deadline-mode2.py';old=funcs(oldpath);new=funcs(P/'helper.py')
for name in ['need','sha','load','contract','guard','parse_receipt','render_stage']:ck(dump(old[name])==dump(new[name]),'exact inherited function '+name)
def assigned(fn,target):
 return [n for n in fn.body if (isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id==target for t in n.targets))or(isinstance(n,ast.AugAssign)and isinstance(n.target,ast.Name)and n.target.id==target)]
for target in ['hashes','command','cleanup']:
 ck([dump(n)for n in assigned(old['execute'],target)]==[dump(n)for n in assigned(new['execute'],target)],'exact native invocation/cleanup expression '+target)
ck([dump(n)for n in old['execute'].body if isinstance(n,ast.For)]==[dump(n)for n in new['execute'].body if isinstance(n,ast.For)],'staging loop unchanged')
oldtext=oldpath.read_text().splitlines(True);delta=json.loads((P/'production-delta.json').read_bytes());out=[];at=0
for h in delta['hunks']:
 ck(type(h['oldStart'])is int and at<=h['oldStart']<=h['oldEnd']<=len(oldtext),'delta bounds')
 ck(''.join(oldtext[h['oldStart']:h['oldEnd']])==h['old'],'delta source bytes');out.extend(oldtext[at:h['oldStart']]);out.append(h['new']);at=h['oldEnd']
out.extend(oldtext[at:]);ck(''.join(out)==(P/'helper.py').read_text(),'complete helper delta')
w=load(P/'run-once.py');dh=load(oldpath);h=load(P/'helper.py');manifest,payload=w.build_manifest();ck(payload==dh.contract()==h.contract(),'all three exact unchanged native payloads')
ck(manifest['nativeDeadlineSeconds']==12 and manifest['rootTimeoutSeconds']==45 and manifest['hostTimeoutSeconds']==75 and manifest['rootCommandCap']==8192 and manifest['rootResponseCap']==65536,'fixed budgets/caps')
eb=funcs(B/'rtp-lane-gate-capture-20261028eb/run-once.py');rw=funcs(P/'run-once.py');src=(B/'rtp-lane-gate-capture-20261028eb/run-once.py').read_text()
expected=ast.get_source_segment(src,eb['load_readiness']).replace('eb-rtp-lane-gate-readiness-decision-v1','ge-live-saver-init-readiness-decision-v1');ck(dump(ast.parse(expected).body[0])==dump(rw['load_readiness']),'exact cached readiness contract except family')
policy=funcs(P/'policy.py');fu=funcs(B/'combined-live-trigger-adapter-20261028fu/wake-check.py')
ck(dump(policy['snapshot_command'])==dump(fu['snapshot_command']),'exact cached getter command')
for name in ['run-once.py','helper.py','policy.py','prepare-readiness.py','admit-fault.py']:
 text=(P/name).read_text();ck(not any(key in text for key in ['input_keyevent','one_key(','apps_gate(','--action','XF86Audio','prepare-live.py']),'no UI/navigation '+name)
ck(not any((P/name).exists()for name in ['Program.cs','DeadlineMode2.dll','parse-result.py']),'no native/parser copies or rebuild')
helper=(P/'helper.py').read_text();ck(helper.index('for command in render_stage')<helper.index('policy.identity_checkpoint')<helper.index('gates.public_gate')<helper.index('checkpoint = policy.snapshot')<helper.index('policy.dispatch')<helper.index('framed = adapter.root'),'explicit staged/preinvoke boundary')
ck(helper.index("policy.save(output / 'helper-terminal.json'")<helper.index("need(rc == 0")<helper.index('parsed = parse_receipt')<helper.index('adapter.root(cleanup'),'terminal retained before semantic/cleanup classification')
base=(B/'live-saver-onset-adapter-20261028ga/prepare-readiness.py').read_text().replace('GA','GE').replace('ga_','ge_').replace('ga-','ge-').replace("'ga'","'ge'").replace('live-saver-onset-adapter-20261028ga','live-saver-init-adapter-20261028ge').replace('ge-live-saver-event-readiness-decision-v1','ge-live-saver-init-readiness-decision-v1')
ck(base==(P/'prepare-readiness.py').read_text(),'exact readiness-builder family derivative')
print(json.dumps({'schema':'ge-source-validation-v1','checks':checks,'externalInputs':len(json.loads((P/'input-pins.json').read_bytes())['files']),'nativePayloadsUnchanged':True,'nativeCommandStagingCleanupUnchanged':True,'wrapperUiOperations':0,'targetOperations':0},sort_keys=True))
