#!/usr/bin/env python3
from pathlib import Path
import subprocess,json,hashlib,re,datetime
p=Path(__file__).resolve().parent
dot='${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet'
checks=[]
def run(name,args,expected=0):
 r=subprocess.run(args,cwd=p,capture_output=True,text=True,timeout=45);(p/(name+'.log')).write_text(r.stdout+r.stderr)
 checks.append({'name':name,'exit':r.returncode,'expected':expected});assert r.returncode==expected,(name,r.returncode,r.stdout,r.stderr)
run('build',[dot,'build','-c','Release','--nologo'])
run('native-host-build',['cc','-std=c11','-Wall','-Wextra','-Werror','-Wpedantic','-fPIC','-shared','-Wl,-soname,host_vconf_mock.so','-Wl,--version-script=host_vconf_mock.map','host_vconf_mock.c','-o','bin/Release/net6.0/host_vconf_mock.so'])
run('host-test',[dot,'bin/Release/net6.0/VconfLoaderDiagnostic.dll','--self-test'])
run('host-default-refusal',[dot,'bin/Release/net6.0/VconfLoaderDiagnostic.dll'],64)
text='\n'.join(f.read_text() for f in p.glob('*.cs'))
assert not any(s in text for s in ['Marshal.GetDelegateForFunctionPointer','UnmanagedFunctionPointer','TEEC_','libteec','Process.Start','vconf_get_int'])
assert text.count('vconf_get_bool')==1
imports=re.findall(r'\[DllImport\("([^"]+)"',text)
assert set(imports)=={'libc.so.6','libdl.so.2'}
by=p.parent/'swu-metadata-adapter-20261027by'
manifest={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'artifact_kind':'portable net6.0 IL; not native ARM cross-build','checks':checks,'target_operations_by_agent':0,'host_only':True,'target_vconf_loaded_on_host':False,'resolved_pointer_invoked':False,'delegate_created':False,'imports':sorted(set(imports)),'inherited_guard_source':str(by/'Native.cs'),'inherited_guard_sha256':hashlib.sha256((by/'Native.cs').read_bytes()).hexdigest(),'assembly_sha256':hashlib.sha256((p/'bin/Release/net6.0/VconfLoaderDiagnostic.dll').read_bytes()).hexdigest(),'files':[]}
for f in sorted(p.rglob('*')):
 if f.is_file() and 'obj' not in f.relative_to(p).parts and f.name not in ['build-manifest.json','source-audit.md']:
  b=f.read_bytes();manifest['files'].append({'path':str(f.relative_to(p)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
(p/'build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({k:v for k,v in manifest.items() if k!='files'},indent=2))
