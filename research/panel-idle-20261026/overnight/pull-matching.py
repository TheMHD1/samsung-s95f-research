#!/usr/bin/env python3
"""Copy explicitly allowlisted matching driver binaries via bounded read-only reads."""
from pathlib import Path
import base64,hashlib,json,subprocess,shlex
BASE=Path(__file__).resolve().parent
ACCESS=BASE.parents[1]/'root-access/s95f-access.py'
FILES={
'sdp_drm.ko':'/lib/modules/5.4.261/kernel/soc/sdp_drm.ko',
'sdp_frc.ko':'/lib/modules/5.4.261/kernel/soc/sdp_frc.ko',
'sdp_pqe_dp.ko':'/lib/modules/5.4.261/kernel/soc/sdp_pqe_dp.ko',
'rosem_frc.ko':'/lib/modules/5.4.261/kernel/rosem_frc.ko',
'tztv_frc_tcon_api.ko':'/lib/modules/5.4.261/kernel/tztv_frc_tcon_api.ko',
}
def root(cmd):
 r=subprocess.run(['python3',str(ACCESS),'root','--timeout','25','--command',cmd],capture_output=True,text=True,timeout=50,check=True)
 c=json.loads(r.stdout)['commands'][0]
 if c['exit_code'] or c['timed_out']:raise RuntimeError(c['stderr'])
 return c['stdout']
manifest={}
for name,remote in FILES.items():
 destination=BASE.parent/'binaries'/name
 fields=root('wc -c '+shlex.quote(remote)+'\nsha256sum '+shlex.quote(remote)).split()
 size,digest=int(fields[0]),fields[2]
 if size>16*1024*1024:raise RuntimeError('Unexpected binary size')
 if destination.exists():
  if hashlib.sha256(destination.read_bytes()).hexdigest()!=digest:raise RuntimeError('Existing different binary')
 else:
  chunks=[]
  for i in range((size+131071)//131072):
   chunks.append(base64.b64decode(root(f'dd if={shlex.quote(remote)} bs=131072 skip={i} count=1 2>/dev/null | base64')))
  data=b''.join(chunks)
  if len(data)!=size or hashlib.sha256(data).hexdigest()!=digest:raise RuntimeError('Transfer verification failed')
  destination.write_bytes(data)
 manifest[name]={'remote':remote,'size':size,'sha256':digest}
 (BASE/'matching-driver-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(name,size,digest,flush=True)
