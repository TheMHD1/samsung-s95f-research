"""Host-only independent FC boundary checks; all temporary writes remain in reviews."""
from pathlib import Path
import contextlib,copy,hashlib,io,json,runpy,subprocess,sys,tempfile
P=Path(__file__).resolve().parents[1];R=P/'reviews';PRIVATE=R/'private';TMP=PRIVATE/'tmp'
sys.dont_write_bytecode=True
checks=0
def need(ok,s):
 global checks
 checks+=1
 if not ok:raise ValueError(s)
def sha(b):return hashlib.sha256(b).hexdigest()
def inventory():
 raw=(P/'source-inventory.json').read_bytes()
 need(sha(raw)=='225011942323f7be66baf69212415c699c9e3aa4f9b103c02a540385d48913f9','corrected author inventory freeze')
 rows=json.loads(raw)['files'];need(len(rows)==13,'13 source entries')
 for row in rows:
  path=P/row['path'];need(Path(row['path']).name==row['path']and not path.is_symlink()and path.is_file(),'ordinary frozen source')
  data=path.read_bytes();need(len(data)==row['bytes']and sha(data)==row['sha256'],'exact author source bytes')
 return sha(raw)
original_temp=tempfile.TemporaryDirectory
def temp(*args,**kwargs):
 kwargs['dir']=TMP
 return original_temp(*args,**kwargs)
original_run=subprocess.run
def safe_run(args,*rest,**kwargs):
 need(isinstance(args,list)and((args==['sh','-n'])or(args==[sys.executable,'-B',str(P/'run-once.py')])),'only local syntax checking or dry FC subprocess')
 return original_run(args,*rest,**kwargs)
def main():
 inventory();results={};namespaces={};tempfile.TemporaryDirectory=temp;subprocess.run=safe_run
 try:
  for name in ['verify-source.py','test-readiness.py','test-runner.py']:
   stdout=io.StringIO();argv=sys.argv[:]
   try:
    with contextlib.redirect_stdout(stdout):ns=runpy.run_path(str(P/name),run_name='__main__')
   finally:sys.argv=argv
   text=stdout.getvalue();(R/(name+'.log')).write_text(text);results[name]=json.loads(text.splitlines()[-1]);namespaces[name]=ns
  ns=namespaces['test-runner.py'];r=ns['r'];parser=ns['parser'];admission=ns['admission']
  with original_temp(prefix='extra-',dir=TMP)as tmp:
   b=Path(tmp);e=b/'evidence.txt';e.write_text('SYNTHETIC independent host fixture only; no device readiness asserted.')
   ready=ns['ready']();ready['evidence']=[{'path':str(e),'sha256':sha(e.read_bytes())}];rb=json.dumps(ready).encode()
   fake=ns['FakeRoot']();clock=ns['Clock']();out=b/'capture'
   with contextlib.redirect_stdout(io.StringIO()):r.execute(out,ready,rb,ns['rawmanifest'],ns['payload'],fake,parser,clock,clock.sleep)
   need(admission.verify(out,sha(ns['rawmanifest']))['accepted']is True,'independent positive control')
   original=json.loads((out/'record.json').read_text())
   tampered=copy.deepcopy(original);tampered['calls']=tampered['calls'][:-1]
   r.save(out/'record.json',tampered)
   try:admission.verify(out,sha(ns['rawmanifest']))
   except(ValueError,KeyError,TypeError):missing_cleanup_rejected=True
   else:missing_cleanup_rejected=False
   r.save(out/'record.json',original)
   tampered=copy.deepcopy(original);tampered['calls'][-1]['response']['commands'][0]['stdout']='NOT_REMOVED\n'
   r.save(out/'record.json',tampered)
   try:admission.verify(out,sha(ns['rawmanifest']))
   except(ValueError,KeyError,TypeError):wrong_cleanup_rejected=True
   else:wrong_cleanup_rejected=False
   r.save(out/'record.json',original)
   need(missing_cleanup_rejected and wrong_cleanup_rejected,'both initial cleanup blockers now reject')
   findings={'missingCleanupRootCallRejected':missing_cleanup_rejected,'wrongCleanupStdoutRejected':wrong_cleanup_rejected}
   mutations=[]
   def reject_record(name,mutate):
    value=copy.deepcopy(original);mutate(value);r.save(out/'record.json',value)
    try:admission.verify(out,sha(ns['rawmanifest']))
    except(ValueError,KeyError,TypeError,IndexError):pass
    else:raise ValueError('accepted tampered ledger: '+name)
    need(True,'independent ledger mutation rejected: '+name);mutations.append(name);r.save(out/'record.json',original)
   reject_record('remove-post-census',lambda x:x['calls'].pop(-3))
   reject_record('remove-integrity',lambda x:x['calls'].pop(-2))
   reject_record('reorder-integrity-cleanup',lambda x:x['calls'].__setitem__(slice(-2,None),list(reversed(x['calls'][-2:]))))
   reject_record('extra-post-native-call',lambda x:x['calls'].append(copy.deepcopy(x['calls'][-1])))
   reject_record('integrity-stdout',lambda x:x['calls'][-2]['response']['commands'][0].__setitem__('stdout','NOT_VERIFIED\n'))
   reject_record('post-census-stdout',lambda x:x['calls'][-3]['response']['commands'][0].__setitem__('stdout','POST_READY\n'))
   reject_record('cleanup-command-and-echo',lambda x:(x['calls'][-1].__setitem__('command','echo STAGE_ABSENT\n'),x['calls'][-1]['response']['commands'][0].__setitem__('command','echo STAGE_ABSENT\n')))
   reject_record('integrity-command-only',lambda x:(x['calls'][-2].__setitem__('command','echo FINAL_INTEGRITY_OK\n'),x['calls'][-2]['response']['commands'][0].__setitem__('command','echo FINAL_INTEGRITY_OK\n')))
   reject_record('boolean-post-census',lambda x:x['postCensus'].__setitem__('observedHolders',False))
   reject_record('wrong-owned-stage',lambda x:x.__setitem__('remote_stage','/tmp/researcher-er-'+'b'*32))
   reject_record('boolean-native-invocations',lambda x:x.__setitem__('native_invocations',True))
   # Runtime entry clocks: exact equality is permitted, one ns late or backwards refuses.
   cp=copy.deepcopy(original['wakeCheckpoint']);wake=ns['wake'];at=cp['acceptedQueryReturnedHostMonotonicNs']
   need(wake.dispatch(copy.deepcopy(cp),lambda:at+1_000_000_000)==at+1_000_000_000,'age inclusive boundary')
   for now in (at-1,at+1_000_000_001):
    try:wake.dispatch(copy.deepcopy(cp),lambda:now)
    except ValueError:need(True,'age outside exact bound refused')
    else:raise ValueError('accepted invalid age')
   # Explicitly qualify parser grammar limits without claiming a full top-window parser.
   s=ns['snapshot']();need(wake.qualified(wake.parse_snapshot(s)),'narrow cached predicate')
   need(wake.qualified(wake.parse_snapshot(s.replace('volume-app ordinary OSD','arbitrary unparsed window-list text'))),'window-list text is not parsed as a full grammar')
   for text in (s+s,s.replace('1.01 2.00\n',''),s.replace('memory/eden/current_tab, value = d/apps.tab (String)\n','memory/eden/current_tab, value = d/apps.tab (String)\n'*2)):
    try:wake.parse_snapshot(text)
    except ValueError:need(True,'duplicate or incomplete primary snapshot refused')
    else:raise ValueError('accepted malformed primary snapshot')
   # Use the actual retained current identity to size generated commands, never to contact it.
   identity_path=P.parent/'limit-rechallenge-trial-20261028ex/after-recovery-identity/identity.json'
   identity_raw=identity_path.read_bytes();actual=json.loads(identity_raw)
   real_ready=copy.deepcopy(ready);real_ready['identity']=actual;real_rb=json.dumps(real_ready).encode()
   real_rpath=b/'real-ready.json';real_rpath.write_bytes(real_rb)
   need(r.load_readiness(real_rpath,sha(real_rb))[0]==real_ready,'saved real identity satisfies fixed FC readiness shape')
   class RealIdentityRoot(ns['FakeRoot']):
    def response(self,command):
     if' --execute --device 'in command:
      self.native+=1;value=json.loads(ns['fixture40']());value['device']=int(actual['devnum'])
      return'IMMEDIATE_READY\n'+ns['envelope'](json.dumps(value).encode())
     return super().response(command)
   real_fake=RealIdentityRoot();real_clock=ns['Clock']();real_out=b/'real-identity-capture'
   r.execute(real_out,real_ready,real_rb,ns['rawmanifest'],ns['payload'],real_fake,parser,real_clock,real_clock.sleep)
   need(admission.verify(real_out,sha(ns['rawmanifest']))['accepted']is True,'real identity synthetic response positive admission')
   real_max=max(len(c.encode())for c in real_fake.commands);need(real_max<=8192,'actual identity plus exact-length stage root command cap')
   need(sum(' --execute --device 'in c for c in real_fake.commands)==1,'one fixed native request with actual identity')
   real_proof={'identityInputSha256':sha(identity_raw),'commandCount':len(real_fake.commands),'maximumCommandBytes':real_max,'remainingRootCommandBytes':8192-real_max,'rootCommandCap':8192,'actualTargetOperations':0}
  inventory()
 finally:tempfile.TemporaryDirectory=original_temp;subprocess.run=original_run
 result={'schema':'fc-independent-corrected-review-v1','authorSuites':results,'independentChecks':checks,'cleanupTamperChecks':findings,'additionalLedgerMutationsRejected':mutations,'savedRealIdentityCommandProof':real_proof,'targetOperations':0,'rootCalls':0,'networkOperations':0}
 (R/('independent-optimized.json'if sys.flags.optimize else'independent-normal.json')).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(json.dumps(result))
if __name__=='__main__':main()
