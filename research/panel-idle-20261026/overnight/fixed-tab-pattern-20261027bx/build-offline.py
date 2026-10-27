#!/usr/bin/env python3
"""Build/check/package BX locally. No network, root transport or TV operation."""
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[2]
DOTNET=BASE/'live-cast/sdk/runtime/dotnet'
DOTNET_SHA='6206ebc1d4b6fb5d73311bc7571c654451550e446daf39fe7cfd3cd84bd6da36'
PROJECT='ManagedEflContentOnce.csproj'
NAMES=['ManagedEflContentOnce'+x for x in ('.dll','.deps.json','.runtimeconfig.json')]
UPSTREAM=BASE/'research-20261027-external/sources/root-sources/chris-ritsen--samsung-tv-root/samsung-tv-root-3b97edf3762db7670585d73e29623dc56195bf98'
UPSTREAM_PINS={
 'payloads/qn90f/Qn90fEflTextOverlayProbe.cs':'0e72141c18df8f995dc1a5bb36718aaaad9fda473b524caf439f2f3b5953de3f',
 'payloads/qn90f/Qn90fEflTextOverlayProbe.csproj':'713f8c087a8e0597f6cecd26a50e977c6084104872d29e597eedf605aea6c1e2',
 'src/samsung_tv_root/overlay.py':'ba0db48b90ee0fc078ba8d5a63736e0b3e02b58954f5467902970a832f38680f',
}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def need(ok,message):
 if not ok:raise ValueError(message)
def run(argv,expected=0,cwd=HERE,timeout=30):
 env=dict(os.environ,DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1',DOTNET_NOLOGO='1')
 p=subprocess.run([str(x) for x in argv],cwd=cwd,env=env,capture_output=True,text=True,timeout=timeout)
 need(p.returncode==expected,repr(argv)+'\n'+p.stdout+p.stderr)
 return {'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
def build(root):
 a=run([DOTNET,'restore','--configfile',root/'NuGet.Config',root/PROJECT],cwd=root)
 b=run([DOTNET,'build','-c','Release','--no-restore','--nologo',root/PROJECT],cwd=root)
 need('0 Warning(s)' in b['stdout'] and '0 Error(s)' in b['stdout'],'clean build')
 return a,b

def main():
 need(sha(DOTNET.read_bytes())==DOTNET_SHA,'offline SDK pin')
 for name,pin in UPSTREAM_PINS.items():need(sha((UPSTREAM/name).read_bytes())==pin,'upstream pin '+name)
 src=(HERE/'Program.cs').read_text()
 # Source surface checks complement behavior fixtures; these are not target ABI proof.
 modules=set(re.findall(r'\[DllImport\("([^"]+)"',src))
 need(modules=={'libc.so.6','librt.so.1','libelementary.so.1','libcapi-ui-efl-util.so.0','libevas.so.1','libecore.so.1'},'native surface allowlist')
 for banned in ['Process.Start','/usr/bin/dotnet','/run/user/5001','wayland-0','libavoc','libave','input_keyevent','timer_delete','elm_shutdown','evas_object_del']:
  need(banned not in src,'forbidden or inherited hardcoded behavior '+banned)
 need(src.index('Native.ArmKernelDeadline(HardSeconds)')<src.index('session = Session.Discover()')<src.index('ui.Create()'),'deadline before session/native UI')
 need('if(n>limit)throw' in src and 'count>32' in src and 'stream.Length+line.Length>32768' in src,'input/log bounds')
 first,second=build(HERE)
 output=HERE/'bin/Release/net6.0'
 dll=output/NAMES[0]
 checks={}
 checks['dry']=run([DOTNET,dll]);dry=json.loads(checks['dry']['stdout']);need(dry['target_operations']==0 and dry['dry_run'] is True,'dry contract')
 checks['self_test']=run([DOTNET,dll,'--self-test']);st=json.loads(checks['self_test']['stdout']);need(st['checks']==316 and st['native_calls']==0,'self test')
 for mode in ['--check-native','--execute-sham','--execute-change']:
  got=run([DOTNET,dll,mode],64);need(json.loads(got['stdout'])['native_calls']==0,'host ABI guard');checks[mode]=got
 for args in [['--invalid'],['--execute-sham','extra'],['--seconds','0']]:
  got=run([DOTNET,dll,*args],63);need(got['stdout']==got['stderr']=='','unknown arguments silent reject')
 checks['invalid_cli_cases']=3
 run(['gcc','-std=c11','-Wall','-Wextra','-Werror','host-deadline-test.c','-lrt','-o','host-deadline-test'])
 checks['host_kernel_deadline']=run([HERE/'host-deadline-test'],timeout=5)
 need(json.loads(checks['host_kernel_deadline']['stdout'])['host_posix_timer_sigkill'] is True,'host deadline semantics')
 with tempfile.TemporaryDirectory(prefix='.repro-',dir=HERE) as tmp:
  root=Path(tmp)
  for name in ['Program.cs',PROJECT,'NuGet.Config']:shutil.copy2(HERE/name,root/name)
  build(root)
  for name in NAMES:need((output/name).read_bytes()==(root/'bin/Release/net6.0'/name).read_bytes(),'reproducibility '+name)
 payload=io.BytesIO()
 with tarfile.open(fileobj=payload,mode='w',format=tarfile.USTAR_FORMAT) as tf:
  for name in NAMES:
   raw=(output/name).read_bytes();info=tarfile.TarInfo(name);info.size=len(raw);info.mode=0o600;info.mtime=0;info.uid=0;info.gid=0
   tf.addfile(info,io.BytesIO(raw))
 with (HERE/'target-package.tar.gz').open('wb') as f:
  with gzip.GzipFile(filename='',mode='wb',fileobj=f,mtime=0) as z:z.write(payload.getvalue())
 binding={
  'schema':'fixed-tab-pattern-bindings-v1','architecture':'ARM32 little endian','pointer_bytes':4,
  'target_validated':False,'runtime_target_pin_from_existing_helpers':'e5840c05c567183295f0bb37e3b28613618cec5e0c8c08a44a400672a1c73310',
  'native_modules':sorted(modules),'efl_exports':re.findall(r'\[DllImport\("(?:libelementary.so.1|libcapi-ui-efl-util.so.0|libevas.so.1|libecore.so.1)"[^\n]*extern [^\n]*? (\w+)\(',src),
  'support_exports':['clock_gettime','geteuid','statx','timer_create','timer_settime'],
  'arm32_layouts':{'timespec_bytes':8,'itimerspec_bytes':16,'sigevent_bytes':64,'sigev_signo_offset':4,'sigev_notify_offset':8,'timer_t_bytes':4,'statx_bytes':256,'statx_uid_offset':20,'statx_mode_offset':28},
  'kernel_deadline':{'clock':'CLOCK_MONOTONIC=1','notification':'SIGEV_SIGNAL=0','signal':'SIGKILL=9','seconds':30,'cancelled_before_exit':False,'startup_covered':False},
  'missing_target_qualification':['relevant installed-library hashes and exports','ARM32 libc/librt timing/sigevent/statx call ABI','unique CSFS cmdline/session environment and socket mode/ownership','notification focus/plane/geometry and alpha behavior','observed normal and forced process-death Wayland cleanup','physical visible/clean ForYou under baseline gray','accepted paired RT/onset recorder coverage']}
 (HERE/'native-binding-requirements.json').write_text(json.dumps(binding,indent=2)+'\n')
 provenance={'schema':'fixed-tab-pattern-provenance-v1','upstream_commit':'3b97edf3762db7670585d73e29623dc56195bf98','upstream':[{ 'path':str(UPSTREAM/name),'sha256':pin,'sourceURL':'https://github.com/chris-ritsen/samsung-tv-root/blob/3b97edf3762db7670585d73e29623dc56195bf98/'+name} for name,pin in UPSTREAM_PINS.items()], 'local_inputs':[]}
 for rel in ['research-20261027-external/reports/content-control-experiment.md','panel-idle-20261026/overnight/managed-plugin-inventory.json','panel-idle-20261026/overnight/managed-ui-tab-launch/build.py','live-cast/sdk/verified-source.json','panel-idle-20261026/overnight/supporting-files-20261027bx/csfs-session-filtered.json']:
  p=BASE/rel;provenance['local_inputs'].append({'path':str(p),'sha256':sha(p.read_bytes())})
 (HERE/'source-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
 (HERE/'build.log').write_text(first['stdout']+first['stderr']+second['stdout']+second['stderr'])
 paths=['Program.cs',PROJECT,'NuGet.Config','build-offline.py','host-deadline-test.c','README.md','native-binding-requirements.json','source-provenance.json','target-package.tar.gz']+['bin/Release/net6.0/'+n for n in NAMES]
 manifest={'schema':'fixed-tab-pattern-build-v1','status':'offline-built-not-target-qualified','host_dotnet_sha256':DOTNET_SHA,'target_operations':0,'network_dependencies':0,'reproducible_managed_outputs':True,'checks':checks,'files':{name:{'bytes':(HERE/name).stat().st_size,'sha256':sha((HERE/name).read_bytes())} for name in paths},'claims':{'target_execution':False,'physical_picture_observed':False,'presentation_observed':False}}
 (HERE/'build-manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'manifest_sha256':sha((HERE/'build-manifest.json').read_bytes()),'program_sha256':sha((HERE/'Program.cs').read_bytes()),'dll_sha256':sha(dll.read_bytes()),'target_package_sha256':sha((HERE/'target-package.tar.gz').read_bytes()),'checks':st['checks'],'target_operations':0,'target_qualified':False},indent=2))
if __name__=='__main__':main()
