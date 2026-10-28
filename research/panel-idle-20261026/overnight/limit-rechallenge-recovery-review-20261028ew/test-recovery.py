#!/usr/bin/env python3
"""Offline synthetic200 adaptation of retained EB bytes; no adapter invocation."""
import base64,copy,hashlib,importlib.util,json,shutil,struct,tempfile,types
from pathlib import Path
HERE=Path(__file__).resolve().parent;B=HERE.parent
spec=importlib.util.spec_from_file_location('ew_guard',HERE/'recover-eb200-fault.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
ORIGINAL=B/'quiescent-onset-trial-20261028es/trial-01/recovery-validation'
checks=0;negative=0

def need(ok,why):
 global checks
 checks+=1
 if not ok:raise ValueError(why)

def readj(p):return json.loads(p.read_text())
def writej(p,j):p.write_text(json.dumps(j,separators=(',',':'))+'\n')
def pins(p):return(m.sha((p/'result.json').read_bytes()),m.sha((p/'record.json').read_bytes()))
def validate(p):return m.validate_capture(p,*pins(p))
def reject(fn,contains=None):
 global negative
 try:fn()
 except(ValueError,KeyError,TypeError,UnicodeError)as e:
  need(contains is None or contains in str(e),'expected refusal reason');negative+=1;return
 raise ValueError('malformed input accepted')
def envelope(terminal,receipt,stdout,stderr,prefix=''):
 blobs=[receipt,stdout,stderr]
 text=prefix+'EBMETA_BEGIN\n'+terminal['boot']+'\n'+terminal['uptime']+'\n'+str(terminal['exit_code'])+'\n'
 for b in blobs:text+=str(len(b))+'\n'+m.sha(b)+'\n'
 text+='EBMETA_END\n'
 for name,b in zip(['RECEIPT','STDOUT','STDERR'],blobs):text+=name+'_B64_BEGIN\n'+base64.encodebytes(b).decode()+name+'_B64_END\n'
 return text+'EBRUN_COMPLETE\n'
def fixture(path,limit=200,end_changed=False,native_mutator=None):
 shutil.copytree(ORIGINAL,path)
 n=readj(path/'native.receipt.json');result=readj(path/'result.json');rec=readj(path/'record.json')
 old_receipt=(path/'native.receipt.json').read_bytes();old_envelope=(path/'native-envelope.txt').read_text()
 for row in n['windows']:
  if row['name']in('start-R','end-R'):
   raw=bytearray(base64.b64decode(row['base64']))
   for at,value in[(0,1),(10,0x1001),(14,0),(0xc4,limit)]:struct.pack_into('<H',raw,at,value)
   if end_changed and row['name']=='end-R':raw[20]^=1
   row['base64']=base64.b64encode(raw).decode();row['sha256']=m.sha(raw);(path/(row['name']+'.bin')).write_bytes(raw)
 if native_mutator:native_mutator(n)
 new_receipt=(json.dumps(n,separators=(',',':'))+'\n').encode();(path/'native.receipt.json').write_bytes(new_receipt)
 expected=[{'name':r['name']+'.bin','bytes':r['bytes'],'sha256':r['sha256']}for r in n['windows']]
 result['rawFiles']=expected;rec['retained_raw_files']=expected
 new_env=envelope(rec['nativeTerminal'],new_receipt,(path/'native.stdout').read_bytes(),b'','IMMEDIATE_READY\n')
 (path/'native-envelope.txt').write_text(new_env)
 for call in rec['calls']:
  oldcommand=call['command'];newcommand=oldcommand.replace(m.sha(old_receipt),m.sha(new_receipt))
  call['command']=newcommand;call['command_bytes']=len(newcommand.encode())
  response=call['response'];command=response['commands'][0];command['command']=newcommand
  if command['stdout']==old_envelope:command['stdout']=new_env
  call['transport_stdout']={'encoding':'base64','data':base64.b64encode(json.dumps(response,separators=(',',':')).encode()).decode()}
 writej(path/'result.json',result);writej(path/'record.json',rec)
 return path

(HERE/'private').mkdir(mode=0o700,exist_ok=True)
with tempfile.TemporaryDirectory(prefix='host-',dir=HERE/'private')as td:
 t=Path(td);good=fixture(t/'synthetic200');admission=validate(good)
 need(admission['faultTuple']==[1,4097,0,200]and admission['samePhase']=='ReadyForHeader','fixed200 admission')
 wrong=fixture(t/'synthetic40',40);reject(lambda:validate(wrong),'fixed200 fault')
 p=fixture(t/'unstable-R',end_changed=True);reject(lambda:validate(p),'stable captured')
 for field,value in [('protocolPhase','Unknown'),('released',False),('closed',False),('headersSent',17)]:
  p=fixture(t/('native-'+field),native_mutator=lambda n,k=field,v=value:n.update({k:v}));reject(lambda:validate(p))
 for suffix in (',\"accepted\":true}',',\"bad\":NaN}'):
  p=t/('json-'+str(len(suffix)));shutil.copytree(good,p);q=p/'result.json';q.write_text(q.read_text().rstrip()[:-1]+suffix);reject(lambda:validate(p))
 for name,mut in [
 ('resultaccepted',lambda j:j.update(accepted=False)),('boolcount',lambda j:j.update(nativeInvocations=True)),
 ('count',lambda j:j.update(headersSent=17)),('cleanup',lambda j:j.update(cleanup='retained')),
 ('manifest',lambda j:j.update(manifestSha256='0'*64)),('retries',lambda j:j.update(retries=1)),
 ('physical',lambda j:j.update(physicalPictureObserved=True))]:
  p=t/name;shutil.copytree(good,p);j=readj(p/'result.json');mut(j);writej(p/'result.json',j);reject(lambda:validate(p))
 p=t/'rawtamper';shutil.copytree(good,p);raw=bytearray((p/'end-R.bin').read_bytes());raw[20]^=1;(p/'end-R.bin').write_bytes(raw);reject(lambda:validate(p),'raw binding')
 p=t/'envelopetamper';shutil.copytree(good,p);q=p/'native-envelope.txt';q.write_text(q.read_text().replace('EBRUN_COMPLETE','EBRUN_INCOMPLETE'));reject(lambda:validate(p),'framing')
 for name,mut in [('recordcount',lambda j:j.update(native_invocations=True)),('recordcleanup',lambda j:j.update(cleanup_required=True)),('transport',lambda j:j['calls'][0].update(transport_exit=1)),('response',lambda j:j['calls'][0]['response'].update(authenticated=False))]:
  p=t/name;shutil.copytree(good,p);j=readj(p/'record.json');mut(j);writej(p/'record.json',j);reject(lambda:validate(p))
 p=t/'seal';shutil.copytree(good,p);before=pins(p);q=p/'result.json';q.write_text(q.read_text()+' ');reject(lambda:m.validate_capture(p,*before),'sealed actual')
 p=t/'symlink';shutil.copytree(good,p);(p/'start-R.bin').unlink();(p/'start-R.bin').symlink_to(good/'start-R.bin');reject(lambda:validate(p),'regular local')
 # Identical EI operation sequence, but injected modules have no target binding.
 def modules(fail=None):
  events=[]
  def mark(name,value=None):
   events.append(name)
   if name==fail:raise ValueError('injected '+name)
   return value
  nav=types.SimpleNamespace(command_snapshot=lambda root,out,label:mark('snapshot-'+label,{'cached_current_tab':'d/apps.tab'}),one_key=lambda *args:mark('key'))
  gates=types.SimpleNamespace(load_adapter=lambda:mark('adapter',object()),apps_gate=lambda out:mark('apps',{'accepted':True}),public_gate=lambda out:mark('public'))
  helper=types.SimpleNamespace(contract=lambda:mark('contract',{}),execute=lambda *args:mark('mode2',{'accepted':True,'request_count':1,'cleanup_confirmed':True}))
  return (gates,nav,helper),events
 mods,events=modules();r=m.perform_recovery(t/'recovery-ok',admission,mods)
 need(r['accepted']and r['mode2_invocations']==1 and r['threshold_writes']==0 and not r['automatic_dv_restore'],'one successful request/no restore')
 need(events==['adapter','snapshot-before','apps','public','contract','mode2','snapshot-final'],'unchanged Apps/public/MODE2 sequence')
 for stage in('adapter','apps','public','contract'):
  mods,events=modules(stage);p=t/('failure-'+stage);reject(lambda:m.perform_recovery(p,admission,mods));r=readj(p/'result.json')
  need('mode2'not in events and r['mode2_attempts']==0 and r['mode2_invocations']==0,'earlier failure zero MODE2')
 mods,events=modules('mode2');p=t/'mode2-failure';reject(lambda:m.perform_recovery(p,admission,mods));r=readj(p/'result.json')
 need(events.count('mode2')==1 and r['mode2_attempts']==1 and r['mode2_invocations']is None,'ambiguous request attempt never retried or inferred zero')
 need(r['threshold_writes']==0 and not r['automatic_dv_restore'],'failure never threshold write')
print(json.dumps({'schema':'ew-host-recovery-validation-v1','checksPassed':checks,'malformedRefusals':negative,'fixture':'synthetic200-from-retained-EB-not-an-actual200-capture','targetOperations':0,'rootCalls':0,'networkOperations':0},sort_keys=True))
