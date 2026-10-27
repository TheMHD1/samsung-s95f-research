"""One read-only kernel log retrieval after a completed GPIO helper result."""
import json,subprocess,hashlib
from pathlib import Path
B=Path(__file__).resolve().parent;P=B/'managed-tcon-gpio-read';v=json.loads((P/'result-20261026a.json').read_bytes());pid=v['execution']['helper_pid']
if not isinstance(pid,int) or pid<=1:raise ValueError('pid')
D=P/'filtered-dmesg-a';D.mkdir();a=B.parent.parent/'root-access/s95f-access.py'
if hashlib.sha256(a.read_bytes()).hexdigest()!='3a92e02003ce51d2faeace231191f6f0c73731f2bfca9caa196e05b195b439a5':raise ValueError('client')
c='''set -euo pipefail
test "$(cat /proc/sys/kernel/random/boot_id)" = 00000000-0000-4000-8000-000000000000
echo LOG_READ_START; cat /proc/uptime
echo FILTERED_DMESG_LAST_32_GPIO_GETTER_ROWS
dmesg | awk '/QDFTcon_GetErrDetFault|read_err_det_status/ {a[n%32]=$0;n++} END {start=n>32?n-32:0;for(i=start;i<n;i++) print a[i%32];print "MATCH_COUNT",n+0}'
echo LOG_READ_END; cat /proc/uptime
echo COMPLETE
'''
(D/'intent.json').write_text(json.dumps({'command':c,'helper_pid':pid},indent=2));p=subprocess.run(['python3',str(a),'root','--persistent-only','--timeout','25','--command',c],capture_output=True,timeout=40);(D/'client.stdout').write_bytes(p.stdout);(D/'client.stderr').write_bytes(p.stderr);print('exit',p.returncode);v=json.loads(p.stdout);print(v['commands'][0]['stdout']);print(v['commands'][0]['stderr'])
