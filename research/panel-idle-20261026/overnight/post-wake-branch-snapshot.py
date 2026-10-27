#!/usr/bin/env python3
"""One finite passive proc-memory snapshot; compressed maps only, no TV controls."""
import base64, copy, datetime, gzip, hashlib, importlib.util, json, subprocess
from pathlib import Path
def require(ok):
 if not ok: raise ValueError('local contract mismatch')
B=Path(__file__).resolve().parent
S=B/'pqe-branch-baseline.py'
A=B.parent.parent/'root-access/s95f-access.py'
require(hashlib.sha256(S.read_bytes()).hexdigest()=='84ff5138a7c4551b932b10360eb6b98d806dc2ef385497b4ec2f7123d6c27acb')
require(hashlib.sha256(A.read_bytes()).hexdigest()=='3a92e02003ce51d2faeace231191f6f0c73731f2bfca9caa196e05b195b439a5')
spec=importlib.util.spec_from_file_location('baseline',S); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
c=m.build_command()
guard='''test "$(cat /proc/sys/kernel/random/boot_id)" = 00000000-0000-4000-8000-000000000000
test "$(pidof avocd)" = 706
s=$(cat /proc/706/stat); s=${s##*) }; set -- $s; test "${20}" = 603
'''
c=c.replace('set -euo pipefail\n','set -euo pipefail\n'+guard,1)
for side in ('START','END'):
 old=f"echo '@@ MAPS_{side}'; cat /proc/$P/maps"
 new=f"echo '@@ MAPS_{side}'; gzip -c /proc/$P/maps|base64; echo"
 require(c.count(old)==1)
 c=c.replace(old,new)
require(len(c.encode())<=8192)
import sys
if '--run' not in sys.argv:
 print(json.dumps({'dry_run':True,'command_bytes':len(c.encode()),'command_sha256':hashlib.sha256(c.encode()).hexdigest(),'command':c})); raise SystemExit
D=B/'post-wake-branch-20261026b'; D.mkdir(mode=0o700)
r={'schema':'post-wake-compressed-baseline-v1','accepted':False,'physical_state':'owner-last-reported-black; not time-calibrated','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':c,'command_sha256':hashlib.sha256(c.encode()).hexdigest(),'base_source_sha256':hashlib.sha256(S.read_bytes()).hexdigest()}
(D/'intent.json').write_text(json.dumps(r,indent=2))
try:
 p=subprocess.run(['python3',str(A),'root','--persistent-only','--timeout','25','--command',c],capture_output=True,timeout=40)
 (D/'client.stdout').write_bytes(p.stdout);(D/'client.stderr').write_bytes(p.stderr)
 if p.returncode!=0 or p.stderr: raise ValueError('root transport failure')
 if len(p.stdout)>65536: raise ValueError('framed response over64KiB')
 raw=json.loads(p.stdout); v=copy.deepcopy(raw)
 if len(v.get('commands',[]))!=1: raise ValueError('command count')
 item=v['commands'][0]
 if item.get('command')!=c: raise ValueError('command binding')
 text=item['stdout']; sections=m.blocks(text)
 map_sizes={}
 for side in ('START','END'):
  key='MAPS_'+side
  packed=sections[key]
  maps=gzip.decompress(base64.b64decode(''.join(packed.splitlines()),validate=True))
  map_sizes[side]=len(maps)
  if len(maps)>1024*1024: raise ValueError('map expansion limit')
  text=text.replace('@@ '+key+'\n'+packed,'@@ '+key+'\n'+maps.decode().rstrip('\n'),1)
 item['stdout']=text
 r['summary']=m.validate_response(v,m.static_contract()); r['accepted']=True
 r['expanded_maps_bytes']=map_sizes
except BaseException as e:
 r['error']=type(e).__name__+': '+str(e)
 raise
finally:
 r['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();(D/'result.json').write_text(json.dumps(r,indent=2))
print(json.dumps({'accepted':r['accepted'],'path':str(D),'summary':r['summary']},indent=2))
