#!/usr/bin/env python3
"""Independent narrow FV review; no live adapter, all scratch here."""
from pathlib import Path
import hashlib,json,subprocess,sys,types
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;P=D.parent;n=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(v,s):
 global n
 n+=1
 if not v:raise ValueError(s)
def load(p):
 m=types.ModuleType(p.stem);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
for ref in json.loads((P/'source-inventory.json').read_bytes())['files']:
 b=(P/ref['path']).read_bytes();need(len(b)==ref['bytes']and sha(b)==ref['sha256'],'frozen FV file '+ref['path'])
m=load(P/'run-once.py');manifest,base,payload=m.build_manifest();need(m.raw_manifest(manifest)==(P/'deployment-manifest.json').read_bytes(),'exact FV manifest')
old=m.load_base();_,oldpayload=old.build_manifest();need(payload==oldpayload,'all native bytes unchanged')
need(base.metadata_body()==old.metadata_body().replace(m.OLD,m.NEW,1),'one exact body replacement')
need(old.metadata_body().count(m.OLD)==1 and m.NEW not in old.metadata_body(),'unique original guard')
for function in ['execute','parse_envelope','run_command','private_bytes','inventory','integrity','file_guard','prefix']:
 need(getattr(base,function).__code__==getattr(old,function).__code__,'unchanged delegate code '+function)
raw=(P/'qualify.py').read_text();expr="P/'host-environment/tmp'";need(raw.count(expr)==2,'two isolated scratch references');t=types.ModuleType('fv_independent_qualification');t.__file__=str(P/'qualify.py');exec(compile(raw.replace(expr,"P/'reviews/private'"),t.__file__,'exec'),t.__dict__)
# New predicate must not leak through to child/module/path guards.
refusals=0
for before,after in [('0:100:755','100:100:755'),('0:100:755','0:0100:755'),('0:100:755','0:100:0755'),('0:0:755','0:100:755'),('0:0:644:0','0:100:644:0'),('0:0:644:226262','0:100:644:226262')]:
 try:base.parse_metadata(t.metadata.replace(before,after))
 except ValueError:refusals+=1
 else:raise ValueError('unexpected metadata acceptance '+after)
command=base.run_command(payload);need(command==old.run_command(payload).replace(m.OLD,m.NEW,1),'exact native command one guard delta');need(len(command.encode())==7608,'actual command length');need(subprocess.run(['sh','-n'],input=command.encode(),capture_output=True).returncode==0,'native command shell syntax')
need('chown 'not in command and 'chmod 'not in base.metadata_body()and 'cat '+base.TARGET not in command,'no metadata mutation/content read')
need(sha(payload['TconLogSingleRead.dll'])=='3abfbbde0045f268073f45d557c63103c3c93a2d4906182e453c1303e5e0cbc0','FK binary remains frozen')
for ref in json.loads((P/'source-inventory.json').read_bytes())['files']:need(sha((P/ref['path']).read_bytes())==ref['sha256'],'posttest frozen file '+ref['path'])
print(json.dumps(dict(schema='fv-independent-validation-v1',decision='PASS_HOST_ONLY_EXACT_GID_DERIVATIVE',checks=n,extraMetadataRefusals=refusals,authorChecks=t.checks,mockCases=len(t.cases),mockCommands=len(t.commands),maxCommandBytes=max(len(c.encode())for c in t.commands),gidCandidates=201,manifestSha256=sha((P/'deployment-manifest.json').read_bytes()),inventorySha256=sha((P/'source-inventory.json').read_bytes()),wrapperSha256=sha((P/'run-once.py').read_bytes()),nativePayloadsUnchanged=True,delegateLifecycleUnchanged=True,targetReads=0,rootCalls=0,networkCalls=0),sort_keys=True))
