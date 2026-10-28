"""Host-only signed-fixture and fake-root tests. No root adapter is loaded."""
from pathlib import Path
import base64,contextlib,hashlib,importlib.util,io,json,subprocess,tempfile
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('ce_runner_test',HERE/'run-once.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
F=HERE.parent/'swu-header-authentication-20261028cc/fixtures';fixtures=json.loads((F/'manifest.json').read_text());checks=0

def need(ok,why):
 global checks
 if not ok:raise RuntimeError(why)
 checks+=1

# Independently verify every signed fixture, including signed malformed framing.
original=m.verify_host_authentication
for row in fixtures['fixtures']:
 pin=fixtures[row['anchor']];pem=(F/('synthetic-public.pem' if row['anchor']=='primary' else 'synthetic-wrong-public.pem')).read_bytes();raw=(F/row['path']).read_bytes()
 selected=row.get('selectedBytes',4032);pad=row.get('paddingBytes',0);form=row.get('representation','Raw4032');roots=int.from_bytes(raw[313:317],'little')
 accepted=True
 try:original(raw,pem,form,selected,pad,roots,public_sha=pin['pemSha256'],public_crc=int(pin['pemCrc32'],16),plaintext_crc=int(row['plaintextCrc32'],16))
 except Exception:accepted=False
 need(accepted==row['accepted'],'independent signed fixture '+row['name'])

case=next(x for x in fixtures['fixtures'] if x['name']=='known-leaf-18');raw=(F/case['path']).read_bytes();public=(F/'synthetic-public.pem').read_bytes();pin=fixtures['primary'];roots=int.from_bytes(raw[313:317],'little')
def synthetic_verify(r,p,form,selected,pad,count):
 return original(r,p,form,selected,pad,count,public_sha=pin['pemSha256'],public_crc=int(pin['pemCrc32'],16),plaintext_crc=int(case['plaintextCrc32'],16))
details=synthetic_verify(raw,public,case['representation'],case['selectedBytes'],case['paddingBytes'],roots)
present=sum(bool(x['present']) for x in details['records']);leaves=sum(bool(x.get('leaf_layout_checked',False)) for x in details['records'])
need(roots>4032//5,'fixture catches absent-root bound regression')
manifest=HERE/'deployment-manifest.json';m.save(manifest,m.manifest());digest=m.sha(manifest.read_bytes())
max_command=0
class FakeRoot:
 def __init__(self,failure):self.failure=failure;self.invocations=0;self.fetches=0;self.cleanups=0;self.calls=0
 def root(self,command,record,output):
  global max_command
  self.calls+=1;max_command=max(max_command,len(command.encode()));need(len(command.encode())<=8192,'command cap')
  check=subprocess.run(['sh','-n'],input=command.encode(),capture_output=True);need(check.returncode==0,'shell syntax')
  if 'base64 -d >>' in command and self.failure=='upload':raise ValueError('synthetic upload')
  if '\nrun_exit=$?' in command:
   self.invocations+=1
   if self.failure=='framing':return 'damaged\n'
   native=('SWU_METADATA_DIAGNOSTIC stage=quarantined result=0x00000000 origin=0x00000004 local=0 calls=1,1,1 counts=4032,0 observed=4032,0 closed=1 released=3 finalized=1 metadata_published=0\n')
   if self.failure=='short_count':native=native.replace('counts=4032,0 observed=4032,0','counts=4031,0 observed=4031,0')
   if self.failure=='observed_mismatch':native=native.replace('observed=4032,0','observed=4031,0')
   auth=(f'SWU_HEADER_AUTH accepted=1 reason=None representation={case["representation"]} raw_bytes=4032 selected_bytes={case["selectedBytes"]} padding_bytes={case["paddingBytes"]} root_count={roots} present_roots={present} checked_leaves={leaves} signature_authenticity_validated=1 framing_subset_checked=1 full_schema_validated=0 metadata_published=0 private_raw_saved=1\n')
   if self.failure=='auth':auth=auth.replace('accepted=1','accepted=0')
   if self.failure=='schema_overclaim':auth=auth.replace('full_schema_validated=0','full_schema_validated=1')
   if self.failure=='count_representation':auth=auth.replace(f'selected_bytes={case["selectedBytes"]}','selected_bytes=4030')
   code=70 if self.failure=='native' else 0
   return f'RUN_EXIT={code}\nSTDOUT_BEGIN\n'+'SELECTOR result=0 value=0\n'*5+native+auth+'STDOUT_END\nSTDERR_BEGIN\nSTDERR_END\n'
  if 'PRIVATE_RAW_BASE64_BEGIN' in command:
   self.fetches+=1;need('authenticated-header-raw.bin) count=' not in command,'not a single-file inventory')
   need('test "$count" = 7' in command,'all seven post-run files in fetch inventory')
   hash_value='0'*64 if self.failure=='fetch_hash' else hashlib.sha256(raw).hexdigest()
   return 'PRIVATE_RAW_SHA256='+hash_value+'\nPRIVATE_RAW_BASE64_BEGIN\n'+base64.encodebytes(raw).decode()+'PRIVATE_RAW_BASE64_END\n'
  if '\nrmdir ' in command:
   self.cleanups+=1
   if self.failure=='cleanup':raise ValueError('synthetic cleanup failure')
   need('test "$count" = 7' in command,'exact cleanup inventory')
   return 'STAGE_REMOVED\n'
  return ''

for failure in ('none','upload','native','framing','auth','schema_overclaim','count_representation','short_count','observed_mismatch','fetch_hash','host_auth','cleanup'):
 fake=FakeRoot(failure);m.load_root=lambda:fake
 with tempfile.TemporaryDirectory() as temp:
  base=Path(temp);m.BASE=base;keydir=base/'swu-public-key-20261028cc';keydir.mkdir();(keydir/'itemsPublicRSAKey.txt').write_bytes(public)
  m.verify_host_authentication=synthetic_verify
  if failure=='host_auth':
   def reject(*args,**kwargs):raise ValueError('synthetic host signature refusal')
   m.verify_host_authentication=reject
  out=base/'run';failed=False
  try:
   with contextlib.redirect_stdout(io.StringIO()):m.execute(out,digest)
  except Exception:failed=True
  need(failed==(failure!='none'),'trial outcome '+failure)
  need(fake.invocations==(0 if failure=='upload' else 1),'one native dispatch '+failure)
  need(fake.cleanups==(1 if failure in ('none','cleanup') else 0),'cleanup gated '+failure)
  need((out/'result.json').exists()==(failure=='none'),'no false success '+failure)
  if failure=='none':
   need((out/'authenticated-header-raw.bin').read_bytes()==raw,'exact private raw copy')
   need((out/'authenticated-header-raw.bin').stat().st_mode&0o777==0o600,'private raw permissions')
   result=json.loads((out/'result.json').read_text());need(result['signature_authenticity_validated'] and not result['full_schema_validated'],'narrow accepted claim')
  if failure in ('fetch_hash','host_auth'):need(not (out/'authenticated-header-raw.bin').exists(),'no private promotion on failed verification')
# Bad manifest must stop before loading transport.
fake=FakeRoot('none');m.load_root=lambda:fake
with tempfile.TemporaryDirectory() as temp:
 try:m.execute(Path(temp)/'bad','0'*64)
 except ValueError:pass
 else:raise RuntimeError('bad digest accepted')
 need(fake.calls==0,'bad manifest no target')
print(json.dumps({'checks':checks,'signedFixtures':len(fixtures['fixtures']),'orchestrationCases':12,'maximumCommandBytes':max_command,'targetOperations':0,'rootAdapterImported':False}))
