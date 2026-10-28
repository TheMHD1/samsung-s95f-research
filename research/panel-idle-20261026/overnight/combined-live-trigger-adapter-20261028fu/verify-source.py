#!/usr/bin/env python3
"""Explicit finite source equivalence and external native identity checks; zero I/O."""
import ast,hashlib,json,difflib,types
from pathlib import Path
P=Path(__file__).resolve().parent;B=P.parent;FN=B/'combined-event-successor-20261028fn';checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def check(v,s):
 global checks
 if not v:raise ValueError(s)
 checks+=1
def load(path):
 m=types.ModuleType(path.stem);m.__file__=str(path);exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m
pins=json.loads((P/'input-pins.json').read_bytes())
for row in pins['files']:
 raw=(B/row['path']).read_bytes();check(len(raw)==row['bytes']and sha(raw)==row['sha256'],'external input pin '+row['path'])
delta=json.loads((P/'production-delta.json').read_bytes())
for name,hunks in delta['files'].items():
 old=(FN/name).read_text();lines=old.splitlines(True);out=[];at=0
 for h in hunks:
  check(type(h['oldStart'])is int and at<=h['oldStart']<=h['oldEnd']<=len(lines),'ordered exact delta')
  check(''.join(lines[h['oldStart']:h['oldEnd']])==h['old'],'exact old delta')
  out.extend(lines[at:h['oldStart']]);out.append(h['new']);at=h['oldEnd']
 out.extend(lines[at:]);check(''.join(out)==(P/name).read_text(),'entire derivative source reconstructed '+name)
expected=(FN/'wake-check.py').read_text().replace('Apps','Live').replace('d/apps.tab','d/ug.tab@Live').replace('fc-ordinary-wake-checkpoint-v1','fu-live-wake-checkpoint-v1')
check(expected==(P/'wake-check.py').read_text(),'only exact Live wake predicate/schema substitutions')
def functions(path):return {f.name:f for f in ast.parse(path.read_bytes()).body if isinstance(f,(ast.FunctionDef,ast.AsyncFunctionDef))}
old=functions(FN/'run-once.py');new=functions(P/'run-once.py')
class Normalize(ast.NodeTransformer):
 def visit_Constant(self,node):
  if type(node.value)is str:
   v=node.value.replace('fu-combined-live-event-','fn-combined-event-').replace('fu-primary-native-outcome-v1','fn-primary-native-outcome-v1').replace('fu_frozen_live_wake','fn_frozen_fc_wake');return ast.copy_location(ast.Constant(v),node)
  return node
 def visit_Dict(self,node):
  node=self.generic_visit(node);pairs=[(k,v)for k,v in zip(node.keys,node.values)if not(isinstance(k,ast.Constant)and k.value in ['expectedCachedTab','intendedNavigation'])];node.keys=[k for k,v in pairs];node.values=[v for k,v in pairs];return node
for name in old.keys()-{'build_manifest','main'}:
 check(ast.dump(old[name],include_attributes=False)==ast.dump(Normalize().visit(new[name]),include_attributes=False),'function AST unchanged '+name)
# Every native source, parser, key worker and payload is external and read in place.
r=load(P/'run-once.py');manifest,payload=r.build_manifest();fn=load(FN/'run-once.py');check(payload==fn.build_manifest()[1],'native three payloads identical')
check(r.PARSER_SHA==fn.PARSER_SHA and r.CHECKPOINT_SHA==fn.CHECKPOINT_SHA and r.FN==FN,'exact native/parser source base')
check(r.ROOT_SHA==fn.ROOT_SHA and [manifest[k]for k in ['rootTimeoutSeconds','hostTimeoutSeconds','rootCommandCap','rootResponseCap','structuredReceiptCap','wholeCooperativeBudgetUs','cleanupReserveUs','keyJoinReserveUs']]==[45,75,8192,65536,24576,40000000,26000000,7000000],'all fixed transport/budget caps')
check(manifest['expectedCachedTab']=='Live'and manifest['intendedNavigation']=='Live-header-to-ForYou','honest derivative premise')
prep=(P/'prepare-live.py').read_text();check("replace('XF86AudioRaiseVolume','Up')"in prep and "for n in [1,2]"in prep,'fixed two Up pairs')
main=new['main'];source=ast.unparse(main);check(source.index('preparation.load_certificate')<source.index('root = load_pinned')and source.index("readiness['evidence']")<source.index('root = load_pinned'),'certificate bound before root import')
check('--execute --device 'in (P/'run-once.py').read_text()and '/tmp/researcher-fn-'in (P/'run-once.py').read_text(),'native family stage preserved')
nav=load(B/'ui-navigation-20261027br/navigate.py');preparation=load(P/'prepare-live.py');captured=[]
class Captured(Exception):pass
class MockNav:
 def root(self,command,record,path):captured.append(command);raise Captured()
try:nav.local_key_action('up',P,MockNav(),'source-only-capture')
except Captured:pass
check(captured==[preparation.up_command()],'fixed Up bytes equal calibrated NAV command')
plans=[n for n in ast.walk(ast.parse((B/'ui-navigation-20261027br/navigate.py').read_bytes()))if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='plans'for t in n.targets)]
check(len(plans)==1 and ast.literal_eval(plans[0].value)['for-you']['d/ug.tab@Live']==[('up','d/ug.tab@Live'),('up','d/ug.tab@Live'),('left','d/ug.tab@ForYou')],'exact calibrated Live header trajectory')
check(not any((P/n).exists()for n in ['Engine.cs','Protocol.cs','OnsetKey.cs','parse-result.py','CombinedEventSuccessor.dll']),'no local native/parser copies')
print(json.dumps({'schema':'fu-source-validation-v1','checks':checks,'nativeAndParserUnchanged':True,'allInheritedFunctionsIncludingExecuteAstEqual':True,'wakePredicateFiniteSubstitution':True,'externalInputs':len(pins['files']),'targetOperations':0},sort_keys=True))
