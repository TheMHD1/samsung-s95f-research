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
 need(sha(raw)=='6729ebc867af37e91e1e09841710306e13ec0f8f773ed0720b17b01928cdf3ad','author inventory freeze')
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
   findings={'missingCleanupRootCallRejected':missing_cleanup_rejected,'wrongCleanupStdoutRejected':wrong_cleanup_rejected}
  inventory()
 finally:tempfile.TemporaryDirectory=original_temp;subprocess.run=original_run
 result={'schema':'fc-independent-review-preliminary-v1','authorSuites':results,'independentChecks':checks,'cleanupTamperChecks':findings,'targetOperations':0,'rootCalls':0,'networkOperations':0}
 (R/('independent-optimized.json'if sys.flags.optimize else'independent-normal.json')).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(json.dumps(result))
if __name__=='__main__':main()
