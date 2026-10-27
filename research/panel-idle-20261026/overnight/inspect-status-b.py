import json,subprocess,hashlib
from pathlib import Path
B=Path(__file__).resolve().parent;P=B/'managed-tcon-status-read';r=json.loads((P/'result-20261026b.json').read_bytes());private=r['private_directory']
if private!='/tmp/researcher-tcon-ff8723b1725944ce872489d3d4350ce5':raise ValueError('path')
a=B.parent.parent/'root-access/s95f-access.py'
if hashlib.sha256(a.read_bytes()).hexdigest()!='3a92e02003ce51d2faeace231191f6f0c73731f2bfca9caa196e05b195b439a5':raise ValueError('client')
c=f'''set -eu
test "$(cat /proc/sys/kernel/random/boot_id)" = 00000000-0000-4000-8000-000000000000
echo BOOT; cat /proc/sys/kernel/random/boot_id; cat /proc/uptime
echo DIRECTORY
stat -c '%u:%g:%a:%F' {private}
for n in TconStatusRead.dll TconStatusRead.deps.json TconStatusRead.runtimeconfig.json managed.stdout managed.stderr helper.ready helper.go; do
f={private}/$n
echo "$n"
if test -e "$f"; then stat -c '%u:%g:%a:%F:%s' "$f"; sha256sum "$f"; case "$n" in helper.ready|managed.stdout|managed.stderr) head -c 4096 "$f"; echo;; esac; else echo ABSENT; fi
done
echo DONE
'''
d=P/'failure-b-inspection';d.mkdir();(d/'intent.json').write_text(json.dumps({'command':c},indent=2));p=subprocess.run(['python3',str(a),'root','--persistent-only','--timeout','25','--command',c],capture_output=True,timeout=40);(d/'client.stdout').write_bytes(p.stdout);(d/'client.stderr').write_bytes(p.stderr);print('exit',p.returncode);v=json.loads(p.stdout);print(v['commands'][0]['stdout']);print(v['commands'][0]['stderr'])
