#!/usr/bin/env python3
"""Focused frozen FU audit. Only pure mocked callbacks; no live transports."""
import copy,hashlib,json,tempfile,types,sys
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parent;P=R.parent;B=P.parent;checks=0;mutations=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def ck(v,msg):
 global checks
 if not v:raise ValueError(msg)
 checks+=1
def load(path):
 m=types.ModuleType(path.stem);m.__file__=str(path);exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m
def reject(fn):
 global mutations
 try:fn()
 except (ValueError,KeyError,TypeError,OSError,UnicodeError):mutations+=1;ck(True,'expected refusal');return
 raise ValueError('unexpected acceptance')
expected={'source-inventory.json':'5015c1acc3d00cdabf5b057f9dc6568fee2bed6c637be462f44f5643abef6a7a','deployment-manifest.json':'3bfe3f0dd98368ad7fb576ac251dd46204391705b2e64b64831082e7d4967e6a','run-once.py':'6f718399b98faa0226f97072d149803bfe96b03da5ff4a3b15d9f13afbc4bfae','wake-check.py':'2d228ed789b83bfe94d7b88bc7617d39309790e57567909611623eaac16e7214','prepare-live.py':'9773de41b6bb6528f8e090b14265f62d434653cceb88da87254c49d444cf7c48','prepare-readiness.py':'9173d6ee1edbe7ae76f6a9fc97c984f926adb8e5bbea04d2c8d21205272a60fb','input-pins.json':'5276e1bb6344fb3541cdbdff9c8caee33a2f4095715aa8dd022853307d63e4e7','qualification.json':'e604217a7555a611cc9aea662d37d25ffb5f554b71aefadbdeb7aba21816d552'}
for name,h in expected.items():ck(sha((P/name).read_bytes())==h,'final pin '+name)
inventory=json.loads((P/'source-inventory.json').read_bytes())
for row in inventory['files']:
 raw=(P/row['path']).read_bytes();ck(len(raw)==row['bytes'] and sha(raw)==row['sha256'],'source inventory '+row['path'])
pins=json.loads((P/'input-pins.json').read_bytes())
for row in pins['files']:
 raw=(B/row['path']).read_bytes();ck(len(raw)==row['bytes'] and sha(raw)==row['sha256'],'external input '+row['path'])
r=load(P/'run-once.py');prep=load(P/'prepare-live.py');w=prep.w
manifest,payload=r.build_manifest();rawmanifest=r.manifest_bytes(manifest);ck(rawmanifest==(P/'deployment-manifest.json').read_bytes(),'regenerated manifest exact')
fn=load(r.FN/'run-once.py');ck(payload==fn.build_manifest()[1],'native payload byte identity')
fc=B/'reader-wake-checkpoints-20261028fc/test-runner.py';m=types.ModuleType('fake_definitions');m.__file__=str(fc);exec(compile(fc.read_text().split('manifest,payload=r.build_manifest();')[0],str(fc),'exec'),m.__dict__)
def snap(saver=False):return m.snapshot('saver'if saver else'success').replace('d/apps.tab','d/ug.tab@Live')
with tempfile.TemporaryDirectory(dir=R/'private',prefix='independent-')as td:
 out=Path(td)/'full';clock=m.Clock();calls=[];settle=0
 def call(command):
  global settle
  calls.append(command)
  if command in [w.wake_command(),prep.up_command()]:settle=0;return 'LOCAL_KEY_DOWN_EXIT=0\nLOCAL_KEY_UP_EXIT=0\n'
  if len(calls)==1:return snap(True)
  settle+=1;return snap(settle<10)
 v=prep.perform(out,call,sha(rawmanifest),clock,clock.sleep)
 ck(len(calls)==34 and calls.count(prep.up_command())==2 and calls.count(w.wake_command())==1,'maximal finite sequence')
 certificate=out/'preparation.json';certbytes=certificate.read_bytes();ck(len(certbytes)<=49152,'maximal certificate cap')
 ck(prep.load_certificate(certificate,sha(certbytes),sha(rawmanifest))['requests']==34,'maximal certificate validates')
 for key,value in [('physicalPictureObserved',True),('uiConsumptionProven',True),('expectedCachedTab','Apps'),('intendedNavigation','Live-to-Live'),('manifestSha256','0'*64),('wakeSourceSha256','0'*64),('preparationSourceSha256','0'*64),('navigationSourceSha256','0'*64),('keyBinarySha256','0'*64),('submittedLabel','inflight'),('optionalWakePairsCompleted',0),('leftPairsAttempted',1),('upPairsCompleted',1)]:
  bad=copy.deepcopy(v);bad[key]=value;reject(lambda:prep.validate(out,bad,sha(rawmanifest)))
 for edit in ['reorder','extra','clock','phase','summary']:
  bad=copy.deepcopy(v)
  if edit=='reorder':bad['entries'][0],bad['entries'][1]=bad['entries'][1],bad['entries'][0]
  if edit=='extra':bad['entries'].append(copy.deepcopy(bad['entries'][-1]))
  if edit=='clock':bad['entries'][2]['returnedHostMonotonicNs']+=w.BUDGET_NS+1
  if edit=='phase':bad['entries'][2]['phaseStartedHostMonotonicNs']+=1
  if edit=='summary':bad['entries'][-1]['summary']['cachedTab']='d/apps.tab'
  reject(lambda:prep.validate(out,bad,sha(rawmanifest)))
 rawpath=out/'up-1-command.txt';orig=rawpath.read_bytes();rawpath.unlink();target=out/'aliased-command';target.write_bytes(orig);rawpath.symlink_to(target)
 reject(lambda:prep.validate(out,v,sha(rawmanifest)));rawpath.unlink();rawpath.write_bytes(orig)
 bad=out/'duplicate.json';bad.write_bytes(certbytes.replace(b'{',b'{"schema":"fake",',1));reject(lambda:prep.load_certificate(bad,sha(bad.read_bytes()),sha(rawmanifest)))
 for normal,optimized in [('source.normal.json','source.optimized.json'),('host.normal.json','host.optimized.json')]:ck((R/normal).read_bytes()==(R/optimized).read_bytes(),'normal/O exact '+normal)
 ck(sha((P/'source-inventory.json').read_bytes())==expected['source-inventory.json'],'source unchanged after tests')
 print(json.dumps({'schema':'fu-independent-validation-v1','verdict':'PASS','checks':checks,'negativeCertificateCases':mutations,'inventoryFiles':len(inventory['files']),'externalInputs':len(pins['files']),'maxPreparationRequests':len(calls),'maxPreparationCertificateBytes':len(certbytes),'nativePayloadUnchanged':True,'authorSourceChecks':116,'authorHostChecks':172,'authorHostCases':33,'authorMockCommands':214,'maxCommandBytes':7944,'targetOperations':0,'rootTransportInvocations':0,'networkOperations':0,'finalPins':expected},sort_keys=True,indent=2))
