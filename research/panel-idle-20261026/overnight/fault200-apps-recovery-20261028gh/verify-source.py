#!/usr/bin/env python3
"""Finite GH source/profile/native-command checks. Never loads root transport."""
import ast,hashlib,json,types
from pathlib import Path
P=Path(__file__).resolve().parent;B=P.parent;GE=B/'live-saver-init-adapter-20261028ge';checks=0
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
# Explicit complete finite source derivative, including all family/name substitutions.
def expected(name):
 s=(GE/name).read_text().replace('GE','GH').replace('ge_','gh_').replace('ge-','gh-').replace("'ge'","'gh'").replace('live-saver-init-adapter-20261028ge','fault200-apps-recovery-20261028gh').replace('gh-live-saver-init','gh-fault200-apps-recovery').replace('gh-live-saver','gh-fault200-apps')
 s=s.replace('STAGH','STAGE').replace('AGH_NS','AGE_NS').replace('stagh','stage')
 if name=='policy.py':s=s.replace('d/ug.tab@Live','d/apps.tab').replace('canonical Live','canonical Apps').replace("need(saver and csfs,'cached Live+saver+CSFS required')","need(not saver and csfs,'cached Apps+noSaver+CSFS required')").replace('cached-live-saver','cached-apps').replace('GH fixed cached','GH fixed Fault200 Apps cached')
 if name=='admit-fault.py':s=s.replace('[1,0,0x1001,0,40]','[1,0,0x1001,0,200]').replace('fault40','fault200').replace('Fault40','Fault200')
 if name=='run-once.py':
  s=s.replace('Live+saver','Fault200 Apps').replace("'cachedContext':'Fault200 Apps+CSFS'","'cachedContext':'Apps+noSaver+CSFS','sourceAlternateLimit':200,'mode2Under200ProfileEmpiricallyQualified':False,'restoresLimit40Proven':False").replace("'liveSaverPremiseNotEstablished':True","'fault200AppsPremiseNotEstablished':True").replace("'rootCauseFixEstablished':False,","'rootCauseFixEstablished':False,'mode2Under200ProfileEmpiricallyQualified':False,'restoresLimit40Proven':False,").replace("'production-delta.json']","'production-delta.json','test-fixture.py','fixture-provenance.json']")
 if name=='helper.py':s=s.replace("POLICY_SHA = 'a8930454d12991eb4c8896ded2ffb2dccf28ab6d9681342482ccda2854383948'","POLICY_SHA = '"+sha((P/'policy.py').read_bytes())+"'")
 return s
production=['run-once.py','helper.py','policy.py','admit-fault.py','prepare-readiness.py']
for name in production:ck((P/name).read_text()==expected(name),'complete finite GE derivative '+name)
# Independently reconstruct every delta, pinned against GE bytes.
delta=json.loads((P/'production-delta.json').read_bytes());ck([x['output']for x in delta['files']]==production,'complete production delta set')
for file in delta['files']:
 lines=(B/file['base']).read_text().splitlines(True);out=[];at=0
 for h in file['hunks']:
  ck(type(h['oldStart'])is int and at<=h['oldStart']<=h['oldEnd']<=len(lines),'delta bounds')
  ck(''.join(lines[h['oldStart']:h['oldEnd']])==h['old'],'delta frozen source bytes');out.extend(lines[at:h['oldStart']]);out.append(h['new']);at=h['oldEnd']
 out.extend(lines[at:]);ck(''.join(out)==(P/file['output']).read_text(),'complete production reconstruction')
oldpath=B/'autonomous-fault-harness-20261028dh/run-deadline-mode2.py';old=funcs(oldpath);new=funcs(P/'helper.py')
for name in ['need','sha','load','contract','guard','parse_receipt','render_stage']:ck(dump(old[name])==dump(new[name]),'exact inherited DH function '+name)
def assigned(fn,target):return [n for n in fn.body if (isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id==target for t in n.targets))or(isinstance(n,ast.AugAssign)and isinstance(n.target,ast.Name)and n.target.id==target)]
for target in ['hashes','command','cleanup']:ck([dump(n)for n in assigned(old['execute'],target)]==[dump(n)for n in assigned(new['execute'],target)],'exact DH command expression '+target)
ck([dump(n)for n in old['execute'].body if isinstance(n,ast.For)]==[dump(n)for n in new['execute'].body if isinstance(n,ast.For)],'unchanged staging loop')
w=load(P/'run-once.py');dh=load(oldpath);h=load(P/'helper.py');manifest,payload=w.build_manifest();ck(payload==dh.contract()==h.contract(),'three exact DH payloads')
for key,value in [('operation',41),('mode',2),('nativeDeadlineSeconds',12),('nativeInvocationsMaximum',1),('rootTimeoutSeconds',45),('hostTimeoutSeconds',75),('rootCommandCap',8192),('rootResponseCap',65536),('nativeReceiptCap',8192),('nativeStderrCap',4096),('sourceAlternateLimit',200),('finalQueryToSubmitMaxNs',1000000000),('cachedContext','Apps+noSaver+CSFS'),('mode2Under200ProfileEmpiricallyQualified',False),('restoresLimit40Proven',False)]:ck(manifest[key]==value,'fixed profile/bound '+key)
ck(w.manifest_bytes(manifest)==(P/'deployment-manifest.json').read_bytes(),'exact sealed manifest')
eb=funcs(B/'rtp-lane-gate-capture-20261028eb/run-once.py');rw=funcs(P/'run-once.py');src=(B/'rtp-lane-gate-capture-20261028eb/run-once.py').read_text()
ready=ast.get_source_segment(src,eb['load_readiness']).replace('eb-rtp-lane-gate-readiness-decision-v1','gh-fault200-apps-recovery-readiness-decision-v1');ck(dump(ast.parse(ready).body[0])==dump(rw['load_readiness']),'unchanged16-field readiness except family')
policy=funcs(P/'policy.py');gepolicy=funcs(GE/'policy.py')
for name in ['snapshot_command','stamp','dispatch','identity_checkpoint','validate_framed','call_stdout']:ck(dump(policy[name])==dump(gepolicy[name]),'unchanged GE guard/getter '+name)
for name in production:
 text=(P/name).read_text();ck(not any(token in text for token in ['input_keyevent','one_key(','apps_gate(','--action','XF86','prepare-live.py','test-fixture.py\'','from test_fixture'] if not(name=='run-once.py'and token=="test-fixture.py'")),'no key/navigation/test-fixture import '+name)
ck(not any((P/name).exists()for name in ['Program.cs','DeadlineMode2.dll','parse-result.py']),'no native/parser duplication')
helper=(P/'helper.py').read_text();ck(helper.index('for command in render_stage')<helper.index('policy.identity_checkpoint')<helper.index('gates.public_gate')<helper.index('checkpoint = policy.snapshot')<helper.index('policy.dispatch')<helper.index('framed = adapter.root'),'poststage identity/public/Apps/freshness order')
ck(helper.index("policy.save(output / 'helper-terminal.json'")<helper.index('need(rc == 0')<helper.index('parsed = parse_receipt')<helper.index('adapter.root(cleanup'),'terminal receipt precedes classification/cleanup')
main=(P/'run-once.py').read_text();ck(main.index('admission=admit.admit')<main.index('adapter=load(ROOT'),'complete source admission precedes real transport import')
ck('limit=200'in(P/'test-fixture.py').read_text()and 'SYNTHETIC HOST FIXTURE ONLY'in(P/'test-fixture.py').read_text(),'explicit reconstructed positive profile')
print(json.dumps({'schema':'gh-source-validation-v1','checks':checks,'externalInputs':len(json.loads((P/'input-pins.json').read_bytes())['files']),'sourceAlternateLimit':200,'nativePayloadsUnchanged':True,'nativeCommandStagingCleanupUnchanged':True,'wrapperUiOperations':0,'targetOperations':0,'actualFault200Observed':False},sort_keys=True))
