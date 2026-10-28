#!/usr/bin/env python3
"""Finite FZ81 delta and fixed production semantics checker; no target access."""
import ast,hashlib,json,types
from pathlib import Path
P=Path(__file__).resolve().parent;B=P.parent;FN=B/'combined-event-successor-20261028fn';checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(v,s):
 global checks
 if not v:raise ValueError(s)
 checks+=1
def normalize(s):return s.replace('combined-event-checkpoints-fz-v1','combined-event-checkpoints-fn-v1').replace('fz-combined-event-81','fn-combined-event').replace('fz-primary-native','fn-primary-native').replace('fz-dry-v1','fn-dry-v1').replace('/tmp/researcher-fz-','/tmp/researcher-fn-').replace('CombinedEvent81Successor','CombinedEventSuccessor').replace('fz-host-checkpoint-v1','fn-host-checkpoint-v1').replace('fz-stockevent-81-checkpoints-v1','fg-stockevent-checkpoints-v1').replace('fz-fresh-cached-readiness-v1','fn-fresh-cached-readiness-v1')
need(sha((FN/'deployment-manifest.json').read_bytes())=='44ddd0699a59329ced1290a0570e791672004b4aa7875e4d203ad0621bc0f7ce','frozen FN manifest cutoff')
need(sha((FN/'source-inventory.json').read_bytes())=='cda3b1936cab9127ab221e08c588c9e11ecb3628938b0dfd8da84daeec39afc3','frozen FN inventory cutoff')
for row in json.loads((P/'input-pins.json').read_bytes())['files']:
 raw=(B/row['path']).read_bytes();need(sha(raw)==row['sha256']and len(raw)==row['bytes'],'frozen input')
for name in ['NativeBinding.cs','OnsetKey.cs','wake-check.py','NuGet.Config']:
 need((P/name).read_bytes()==(FN/name).read_bytes(),'byte-identical '+name)
for name,old,new in [('Protocol.cs','MaxCycles = 56','MaxCycles = 81'),('Engine.cs','config.MaxCycles<=56','config.MaxCycles<=81'),('ScoreCheckpoints.cs','Capacity=56','Capacity=81')]:
 need(normalize((P/name).read_text()).replace(new,old)==(FN/name).read_text(),'only finite cap/schema delta '+name)
need(normalize((P/'CombinedEvent81Successor.csproj').read_text())==(FN/'CombinedEventSuccessor.csproj').read_text(),'assembly rename only')
class Normalize(ast.NodeTransformer):
 def visit_Constant(self,n):
  if type(n.value)is str:return ast.copy_location(ast.Constant(normalize(n.value)),n)
  return n
for name in ['run-once.py']:
 a={f.name:f for f in ast.parse((FN/name).read_bytes()).body if isinstance(f,ast.FunctionDef)};b={f.name:f for f in ast.parse((P/name).read_bytes()).body if isinstance(f,ast.FunctionDef)}
 for function in a.keys()-{'build_manifest','main'}:need(ast.dump(a[function],include_attributes=False)==ast.dump(Normalize().visit(b[function]),include_attributes=False),'unchanged inherited wrapper function '+function)
a=ast.parse((FN/'prepare-readiness.py').read_bytes());b=ast.parse((P/'prepare-readiness.py').read_bytes())
for function in ['sha','load','main']:
 left=next(f for f in a.body if isinstance(f,ast.FunctionDef)and f.name==function);right=next(f for f in b.body if isinstance(f,ast.FunctionDef)and f.name==function);need(ast.dump(left,include_attributes=False)==ast.dump(Normalize().visit(right),include_attributes=False),'unchanged readiness function '+function)
parser=(P/'parse-result.py').read_text();need("'headers':660,'bulks':1320,'inputs':658,'writes':2"in parser and "'cyclesStarted':81,'cleanCycles':81,'quiescentCycles':81"in parser,'precise counter maxima')
need('0,1000'not in parser and ',0,56)'not in parser and '<=56'not in parser,'no legacy parser cap')
need('TimeLimitedPartial'in(P/'Engine.cs').read_text()and 'x.ObservationComplete=true'not in(P/'Engine.cs').read_text().split('o.TerminalReason="TimeLimitedPartial"')[1].split('break;')[0],'partial is never promoted')
need('class FastClock:IClock'in(P/'HostTests.cs').read_text()and 'FastClock'not in(P/'Engine.cs').read_text()and 'FastClock'not in(P/'Protocol.cs').read_text(),'no-wait mock clock is host-test-only')
print(json.dumps({'schema':'fz-source-checks-v1','checks':checks,'nativeBindingKeyWakePacketsBudgetsUnchanged':True,'wholeBudgetUs':40000000,'durationUs':2000000,'periodUs':25000,'maxCycles':81,'maxHeaders':660,'maxInputs':658,'maxBulks':1320,'maxWrites':2,'targetOperations':0},sort_keys=True))
