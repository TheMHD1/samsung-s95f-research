import json,subprocess,hashlib
from pathlib import Path
B=Path(__file__).resolve().parent;D=B/'managed-tcon-status-read/status-c-filtered-dmesg';D.mkdir();a=B.parent.parent/'root-access/s95f-access.py'
if hashlib.sha256(a.read_bytes()).hexdigest()!='3a92e02003ce51d2faeace231191f6f0c73731f2bfca9caa196e05b195b439a5':raise ValueError('client')
c='''set -euo pipefail
test "$(cat /proc/sys/kernel/random/boot_id)" = 00000000-0000-4000-8000-000000000000
echo LOG_READ_START; cat /proc/uptime
echo FILTERED_DMESG_ALL_RETAINED
dmesg | awk '/ERR DET Status|GetErrDetStatus|ERR DET Status Debug|RT Protect/ {n++; if(n<=32) print} END {print "FILTER_MATCH_COUNT",n+0}'
echo LOG_READ_END; cat /proc/uptime
echo COMPLETE
'''
(D/'intent.json').write_text(json.dumps({'command':c},indent=2));p=subprocess.run(['python3',str(a),'root','--persistent-only','--timeout','25','--command',c],capture_output=True,timeout=40);(D/'client.stdout').write_bytes(p.stdout);(D/'client.stderr').write_bytes(p.stderr);print('exit',p.returncode);v=json.loads(p.stdout);print(v['commands'][0]['stdout']);print(v['commands'][0]['stderr'])
