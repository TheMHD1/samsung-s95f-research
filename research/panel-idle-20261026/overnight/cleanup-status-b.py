import json,subprocess,hashlib
from pathlib import Path
B=Path(__file__).resolve().parent;D=B/'managed-tcon-status-read/failure-b-cleanup-corrected';D.mkdir();a=B.parent.parent/'root-access/s95f-access.py'
if hashlib.sha256(a.read_bytes()).hexdigest()!='3a92e02003ce51d2faeace231191f6f0c73731f2bfca9caa196e05b195b439a5':raise ValueError('client')
c=r'''set -eu
test "$(cat /proc/sys/kernel/random/boot_id)" = 00000000-0000-4000-8000-000000000000
p=/tmp/researcher-tcon-ff8723b1725944ce872489d3d4350ce5
if test -r /proc/896/stat; then
x=$(cat /proc/896/stat); x=${x##*) }; set -- $x
test "${20}" != 18751314 || test "$1" = Z
fi
echo ORIGINAL_CHILD_NOT_LIVE
for f in /proc/[0-9]*/cmdline; do
if tr '\000' ' ' < "$f" 2>/dev/null | grep -q -F "$p/TconStatusRead.dll"; then echo UNEXPECTED_MATCH; exit 81; fi
done
test ! -L "$p"; test "$(stat -c '%u:%g:%a' "$p")" = 0:0:700
for f in "$p"/* "$p"/.[!.]* "$p"/..?*; do
test -e "$f" || test -L "$f" || continue
test ! -L "$f"; test -f "$f"; test "$(stat -c '%u:%g:%a' "$f")" = 0:0:600
case "${f##*/}" in TconStatusRead.dll|TconStatusRead.deps.json|TconStatusRead.runtimeconfig.json|helper.ready|helper.go|managed.stdout|managed.stderr) ;; *) exit 82;; esac
done
test "$(sha256sum "$p/TconStatusRead.dll"|cut -d' ' -f1)" = b218d8f4a76ed22f081d9e26a8047af1fdffbfe3faa9ebc42898fdbb560f6eab
test "$(wc -c < "$p/managed.stdout")" = 0
test "$(wc -c < "$p/managed.stderr")" = 0
rm "$p/TconStatusRead.dll" "$p/TconStatusRead.deps.json" "$p/TconStatusRead.runtimeconfig.json" "$p/helper.ready" "$p/helper.go" "$p/managed.stdout" "$p/managed.stderr"
rmdir "$p"
test ! -e "$p"; test ! -L "$p"
echo PRIVATE_REMOVED
'''
(D/'intent.json').write_text(json.dumps({'command':c},indent=2));p=subprocess.run(['python3',str(a),'root','--persistent-only','--timeout','25','--command',c],capture_output=True,timeout=40);(D/'client.stdout').write_bytes(p.stdout);(D/'client.stderr').write_bytes(p.stderr);print('exit',p.returncode);v=json.loads(p.stdout);print(v['commands'][0]['stdout']);print(v['commands'][0]['stderr'])
