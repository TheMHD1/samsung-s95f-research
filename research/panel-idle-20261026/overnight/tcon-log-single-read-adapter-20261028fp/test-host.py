#!/usr/bin/env python3
"""FP host-only tests. Root responses are synthetic; sh -n parses without execution."""
from pathlib import Path
import base64,copy,json,os,shlex,subprocess,sys,tempfile,types
P=Path(__file__).resolve().parent;checks=0;commands=[]
def load(p):
 m=types.ModuleType(p.stem);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
r=load(P/'run-once.py');parser=load(r.FK/'parse-receipt.py')
def check(ok,s):
 global checks
 if not ok:raise ValueError(s)
 checks+=1
def rejects(f,fragment=None):
 try:f()
 except(ValueError,KeyError,TypeError,OSError,UnicodeError)as e:
  check(fragment is None or fragment in str(e),'expected refusal '+str(fragment));return
 raise ValueError('unexpected acceptance')
# Derive mocked runtime values from retained FJ, never the live TV. UID/GID here are synthetic.
fj=(r.B/'tcon-log-runtime-metadata-20261028fj/metadata.txt').read_text();lines=fj.splitlines()
boot=lines[lines.index('BOOT')+1];kernel=lines[lines.index('KERNEL')+1]
modules=lines[lines.index('MODULES')+1:lines.index('DEBUGFS_METADATA')];module=next(s for s in modules if s.startswith('sdp_tcon '))
mount=next(s for s in lines if s.startswith('debugfs /sys/kernel/debug debugfs '));modulehash=lines[-1].split()[0]
check(boot==r.BOOT and kernel==r.KERNEL and modulehash==r.MODULE_SHA,'cached FJ boot/kernel/module hash')
check('regular empty file 644 0 '+r.TARGET in lines,'cached FJ target stat, no contents read')
check('regular file 644 226262 '+r.MODULE in lines,'cached FJ module stat')
metadata='\n'.join(['FP_METADATA_BEGIN',boot,kernel,' '.join(mount.split()[:3]),module,'0:0:755','0:0:755','0:0:644:0','0:0:644:226262',modulehash,'FP_METADATA_END'])+'\n'
check(r.parse_metadata(metadata)['loadedModuleBytesAttested']is False,'metadata is not loaded byte attestation')
for old,new in [(r.BOOT,'0'*36),(r.KERNEL,'5.4.262'),('debugfs /sys/kernel/debug debugfs','none /sys/kernel/debug tmpfs'),(' Live ',' Loading '),('0:0:644:0','0:0:644:1'),('0:0:755','0:0:777'),('0:0:644:226262','0:0:644:226261'),(r.MODULE_SHA,'a'*64),('sdp_tcon ','sdp_other '),('FP_METADATA_END','FP_METADATA_END\nextra')]:rejects(lambda old=old,new=new:r.parse_metadata(metadata.replace(old,new)))
rejects(lambda:r.parse_metadata(metadata.replace(module,module+'\n'+module)))
fixture=(r.FK/'fixture.json').read_bytes();parser.parse(fixture)
def envelope(receipt=fixture,stdout=b'[GC_INFO]\nopaque runtime diagnostics\n',stderr=b'',rc=0,present=True):
 vals=[receipt,stdout,stderr];out='FP_RUN_BEGIN\n'+r.BOOT+'\n1.0 2.0\n'+str(rc)+'\n'+str(int(present))+'\n'
 for b in vals:out+=str(len(b))+'\n'+r.sha(b)+'\n'
 out+='FP_RUN_META_END\n'
 for label,b in zip(['RECEIPT','STDOUT','STDERR'],vals):out+=label+'_B64_BEGIN\n'+base64.b64encode(b).decode()+'\n'+label+'_B64_END\n'
 return out+'FP_RUN_COMPLETE\n'
check(r.parse_envelope(envelope())[1]==fixture,'receipt separated from diagnostics')
for bad in [envelope()+'x',envelope()[:-2],envelope().replace(r.sha(fixture),'a'*64),envelope().replace(str(len(fixture))+'\n',str(len(fixture)+1)+'\n',1),envelope().replace('FP_RUN_BEGIN','MALFORMED'),envelope(present=False)]:rejects(lambda bad=bad:r.parse_envelope(bad))
for cap,pos in [(r.RECEIPT_CAP,0),(r.STDOUT_CAP,1),(r.STDERR_CAP,2)]:
 vals=[fixture,b'',b''];vals[pos]=b'x'*(cap+1);rejects(lambda vals=vals:r.parse_envelope(envelope(*vals)))
worst=envelope(b'x'*r.RECEIPT_CAP,b'x'*r.STDOUT_CAP,b'x'*r.STDERR_CAP);check(len(r.parse_envelope(worst)[1])==r.RECEIPT_CAP,'inclusive envelope cap')
for name in ['CHECKPOINT_SHA','FK_INVENTORY_SHA','PARSER_SHA','ROOT_SHA']:
 original=getattr(r,name);setattr(r,name,'0'*64)
 try:rejects(r.build_manifest)
 finally:setattr(r,name,original)
manifest,payload=r.build_manifest();reviewed=r.manifest_bytes(manifest);check(reviewed==(P/'deployment-manifest.json').read_bytes(),'exact manifest reconstruction')
class FakeRoot:
 def __init__(self,kind):self.kind=kind;self.calls=0;self.native=0;self.cleanup=0;self.after_native=0;self.did_native=False;self.commands=[]
 def root(self,c,record,path):
  commands.append(c);self.commands.append(c);self.calls+=1
  check(len(c.encode())<=r.MAX_COMMAND,'command cap');check(subprocess.run(['sh','-n'],input=c.encode(),capture_output=True).returncode==0,'shell syntax')
  if self.did_native:self.after_native+=1
  record['calls'].append({'command':c,'mockOnly':True});r.save(path,record)
  if self.kind=='response-cap':return 'x'*(r.MAX_RESPONSE+1)
  if c==r.prefix()+r.metadata_body():
   if self.kind=='metadata-ambiguous':raise OSError('mock metadata transport ambiguity')
   if self.kind=='bad-metadata':return metadata.replace(r.MODULE_SHA,'f'*64)
   return metadata
  if c.endswith('echo FP_STAGE_CREATED\n'):
   check('test ! -e '+r.STAGE in c and 'test ! -L '+r.STAGE in c,'refuse existing stage/symlink before creation')
   if self.kind in ['stage-exists','stage-symlink']:raise OSError('mock stage collision refused')
   return 'FP_STAGE_CREATED\n'
  if c.endswith('echo FP_STAGED_CHUNK\n'):
   if self.kind=='chunk-ambiguous':raise OSError('mock staged chunk ambiguity')
   return 'FP_STAGED_CHUNK\n'
  if c.endswith('echo FP_STAGED_FILE\n'):return 'FP_STAGED_FILE\n'
  if ' --execute > 'in c:
   self.native+=1;self.did_native=True
   check(c.count(' --execute > ')==1 and c.count(r.TARGET)==4,'one fixed invocation; target only path metadata tests/stat')
   check(r.metadata_body()in c and c.index(r.metadata_body())<c.index(' --execute > '),'fresh guarded runtime metadata before invocation')
   if self.kind=='native-ambiguous':raise OSError('mock native response ambiguity; no rollback claim')
   if self.kind=='immediate-changed':raise OSError('mock immediate metadata guard failed before possible invocation')
   v=json.loads(fixture);rc=0;stderr=b'';present=True;receipt=fixture
   if self.kind=='native-refused':v.update(accepted=False,readResult=-1,readErrno=5,returnedPrefixBytes=0,returnedPrefixSha256=None);receipt=(json.dumps(v)+'\n').encode();rc=1
   if self.kind=='close-refused':v.update(accepted=False,closeResult=-1,closeErrno=4);receipt=(json.dumps(v)+'\n').encode();rc=1
   if self.kind=='missing-receipt':present=False;receipt=b'';rc=64;stderr=b'FK refused: IOException\n'
   if self.kind=='empty-receipt':receipt=b'';rc=64
   if self.kind=='partial-receipt':receipt=fixture[:33];rc=64
   if self.kind=='bad-receipt-hash':v['rawAllocationSha256']='0'*64;receipt=(json.dumps(v)+'\n').encode()
   if self.kind=='duplicate-receipt':receipt=fixture.replace(b'{',b'{"accepted":true,',1)
   if self.kind=='nonzero-exit':rc=1
   if self.kind=='diagnostic-error':stderr=b'FK refused: IOException\n'
   out=envelope(receipt,stderr=stderr,rc=rc,present=present)
   if self.kind=='bad-envelope':out=out[:-3]
   if self.kind=='zero-result':
    v.update(readResult=0,returnedPrefixBytes=0,returnedPrefixSha256=r.sha(b''));out=envelope((json.dumps(v)+'\n').encode())
   if self.kind=='short-result':
    v.update(readResult=1,returnedPrefixBytes=1,returnedPrefixSha256=r.sha(base64.b64decode(v['rawAllocationBase64'])[:1]));out=envelope((json.dumps(v)+'\n').encode())
   return metadata+out
  if c.endswith('echo FP_FINAL_INTEGRITY_OK\n'):
   if self.kind=='integrity-failure':raise OSError('mock final integrity drift')
   return 'FP_FINAL_INTEGRITY_OK\n'
  if c.endswith('echo FP_STAGE_ABSENT\n'):
   self.cleanup+=1
   if self.kind=='cleanup-ambiguous':raise OSError('mock cleanup ambiguous')
   return 'FP_STAGE_ABSENT\n'
  raise ValueError('unexpected mock command')
(P/'host-environment/tmp').mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix='fp-mock-',dir=P/'host-environment/tmp')as d:
 base=Path(d)
 accepted=['success','zero-result','short-result'];kinds=accepted+['metadata-ambiguous','bad-metadata','response-cap','stage-exists','stage-symlink','chunk-ambiguous','native-ambiguous','immediate-changed','native-refused','close-refused','missing-receipt','empty-receipt','partial-receipt','bad-receipt-hash','duplicate-receipt','bad-envelope','nonzero-exit','diagnostic-error','integrity-failure','cleanup-ambiguous']
 for kind in kinds:
  f=FakeRoot(kind);out=base/kind
  if kind in accepted:
   result=r.execute(out,reviewed,payload,f,parser);check(result['accepted']and f.native==f.cleanup==1 and f.after_native==2,'one native and exact accepted cleanup')
   for k in ['loadedModuleBytesAttested','copyCompletionAttested','completeLogProven','externalRtpProducerProven','producerAtomicityProven','physicalPictureObserved','timeoutOrRollbackGuaranteed']:check(result[k]is False,'limitations retained '+k)
   check((out/'allocation.bin').stat().st_size==4096,'entire allocation private')
   check((out/'returned-prefix.bin').stat().st_size==result['returnedBytes'],'returned prefix exact')
   check((out/'native.stdout').read_bytes().startswith(b'[GC_INFO]'),'GC diagnostic kept separately')
   line=next(x for x in f.commands[-1].splitlines()if x.startswith('rm -- '));names=shlex.split(line)[2:]
   check(names==[r.STAGE+'/'+n for n in r.NAMES+r.OUTPUTS]and len(names)==6,'exact six owned ordinary files only')
   check('rm -r'not in f.commands[-1]and r.integrity(dict(payload,**{'read.receipt.json':(out/'read.receipt.json').read_bytes(),'native.stdout':(out/'native.stdout').read_bytes(),'native.stderr':b''}))in f.commands[-1],'final cleanup repeats full integrity')
  else:
   rejects(lambda:r.execute(out,reviewed,payload,f,parser));rec=json.loads((out/'record.json').read_bytes());res=json.loads((out/'result.json').read_bytes());check(not res['accepted']and rec['cleanupRequired'],'refusal retains stage obligation')
   check(f.native<=1 and f.cleanup==(1 if kind=='cleanup-ambiguous'else 0),'no retry/no refusal cleanup')
   if kind not in ['integrity-failure','cleanup-ambiguous']:check(f.after_native==0,'no further root call after refused/ambiguous native')
   if kind in ['missing-receipt','empty-receipt','partial-receipt','native-refused','close-refused','bad-receipt-hash','duplicate-receipt','nonzero-exit','diagnostic-error']:
    check((out/'read.receipt.json').exists()and (out/'native.stdout').exists()and (out/'native.stderr').exists(),'all framed raw artifacts retained before refusal')
   if kind in ['native-refused','close-refused']:check(rec['nativeInvocationStatus']=='one_completed'and rec['nativeAccepted']is False,'known refused lifecycle remains refused')
   if kind in ['native-ambiguous','immediate-changed','bad-envelope']:check(rec['nativeInvocationStatus']=='inflight_or_unknown'and rec['readMayHaveOccurred'],'ambiguity does not assert rollback/read absence')
   if kind in ['metadata-ambiguous','bad-metadata','response-cap','stage-exists','stage-symlink','chunk-ambiguous']:check(f.native==0 and rec['nativeInvocations']==0,'preflight/staging failure no native')
  check(out.stat().st_mode&0o777==0o700,'private local directory')
  for p in out.iterdir():check(p.stat().st_mode&0o777==0o600,'private local artifact '+p.name)
 # CLI refusal/default paths must not import the real root adapter or invoke a subprocess transport.
 for args,ok in [([],True),(['--execute'],False),(['--execute','--manifest-sha256','0'*64,'--checkpoint-sha256',r.CHECKPOINT_SHA,'--output',str(base/'bad-pin')],False),(['--execute','--manifest-sha256',r.sha(reviewed),'--checkpoint-sha256','0'*64,'--output',str(base/'bad-checkpoint')],False),(['--target','/dev/anything'],False)]:
  p=subprocess.run([sys.executable,'-B',str(P/'run-once.py')]+args,capture_output=True);check((p.returncode==0)==ok,'CLI dry/explicit pins/fixed arguments')
  if ok:check(json.loads(p.stdout)['rootCalls']==0,'dry zero root calls')
# Bound a representative serialized authenticated root response with all raw channels at caps.
run=r.run_command(payload);max_response=json.dumps({'model':'QN77S95FAFXZC','authenticated':True,'uid':0,'euid':0,'root_persistence':'host-assisted','global_system_files_unchanged_at_acquisition':True,'commands':[{'command':run,'stdout':metadata+worst,'stderr':'','exit_code':0,'timed_out':False}]},ensure_ascii=True).encode()
check(len(max_response)<r.MAX_RESPONSE,'worst serialized root response below cap')
check(len(run.encode())<=r.MAX_COMMAND,'native command below cap')
summary={'schema':'fp-host-tests-v1','checks':checks,'cases':len(kinds),'mockRootCommands':len(commands),'maxCommandBytes':max(len(x.encode())for x in commands),'serializedRootResponseBound':len(max_response),'rawTerminalEnvelopeAtCapsBytes':len((metadata+worst).encode()),'targetReads':0,'targetRootCalls':0,'nativeInvocationsOnTarget':0,'cachedFjMetadataSha256':r.sha(fj.encode()),'allScratchUnderFp':True}
print(json.dumps(summary,sort_keys=True))
