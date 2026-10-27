#!/usr/bin/env python3
"""One stock unmute request; no trace, remote files, retries, or power operation.

Owner reported a powered-on black panel and no optimization cycle in chat.
Physical outcome must be obtained from the owner; public success is insufficient.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
CLIENT = Path('${S95F_EVIDENCE_ROOT}/root-access/s95f-access.py')
CLIENT_SHA = '3a92e02003ce51d2faeace231191f6f0c73731f2bfca9caa196e05b195b439a5'
DEST = HERE / 'stock-unmute-once-20261026'
COMMAND = '''set -eu
identity() {
 boot=$(cat /proc/sys/kernel/random/boot_id); echo "$boot"
 test "$boot" = 00000000-0000-4000-8000-000000000000
 grep -qx 'BUILD_ID=T-RSMFAKUC-0090-REL-202607141953' /etc/tizen-release
 test "$(pidof avocd)" = 706
 test "$(readlink -f /proc/706/exe)" = /usr/bin/avocd
 row=$(cat /proc/706/stat); rest=${row##*) }; set -- $rest
 test "$#" -ge 20; test "${20}" = 603; echo 'AVOC 706 603'
 ah=$(sha256sum /usr/bin/avocd); echo "$ah"
 vh=$(sha256sum /prd/usr/lib/libave.so.0.1); echo "$vh"
 test "${ah%% *}" = ab450eaf99c793f3c7a9360629b1a1677e9d86dcd74a1f93796b56ba07401de9
 test "${vh%% *}" = a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777
 test "$(cat /sys/kernel/debug/tracing/tracing_on)" = 0
 test "$(cat /sys/kernel/debug/tracing/current_tracer)" = nop
}
stamp() { date -u +%s; cat /proc/uptime; }
getter() {
 dbus-send --system --print-reply --reply-timeout=1500 --dest=org.tizen.tv.avoc /org/tizen/tv/avoc "org.tizen.tv.avoc.AvOutputControl.$1"
}
baseline() {
 reply=$(getter "$1") || return 1
 echo "$reply"
 printf '%s\n' "$reply" | awk '$1=="int32"{n++;if($2!=0)bad=1} END{exit(n==2 && !bad?0:1)}'
}
echo '@@ ID_START'; identity
echo '@@ BEFORE_BASELINE'; stamp
echo '@@ BASELINE_MUTE'; baseline GetPanelMute
echo '@@ BASELINE_CASE'; baseline GetPanelMuteCaseStatus
echo '@@ BEFORE_SINGLE_UNMUTE_ZERO'; stamp
status=0
dbus-send --system --print-reply --reply-timeout=1500 --dest=org.tizen.tv.avoc /org/tizen/tv/avoc org.tizen.tv.avoc.AvOutputControl.SetPanelMute int32:0 || status=$?
echo "SETTER_DBUS_EXIT=$status"
echo '@@ AFTER_SINGLE_UNMUTE_ZERO'; stamp
echo '@@ POST_MUTE'; post=0; getter GetPanelMute || post=$?; echo "POST_MUTE_EXIT=$post"
echo '@@ POST_CASE'; post=0; getter GetPanelMuteCaseStatus || post=$?; echo "POST_CASE_EXIT=$post"
echo '@@ ID_END'; identity
echo '@@ COMPLETE'; echo SINGLE_REQUEST_NO_RETRY
'''

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run', action='store_true')
    args = ap.parse_args()
    if hashlib.sha256(CLIENT.read_bytes()).hexdigest() != CLIENT_SHA:
        raise ValueError('reviewed root client changed')
    if len(COMMAND.encode()) > 8192 or COMMAND.count('SetPanelMute int32:0') != 1:
        raise ValueError('command bound or setter count')
    argv = ['python3', str(CLIENT), 'root', '--persistent-only', '--timeout', '25', '--command', COMMAND]
    intent = dict(command=COMMAND, command_sha256=hashlib.sha256(COMMAND.encode()).hexdigest(),
                  client_sha256=CLIENT_SHA, argv=argv, retry=False,
                  physical_state_source='owner chat report; not directly observed by operator',
                  owner_report=dict(panel='black while powered on', optimization_cycle='not running'),
                  wire_capture=False, persistent_config_write=False)
    if not args.run:
        print(json.dumps(intent, indent=2)); return
    DEST.mkdir(mode=0o700, exist_ok=False)
    intent['started_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
    (DEST/'intent.json').write_text(json.dumps(intent, indent=2)+'\n')
    with (DEST/'client-stdout.json').open('xb') as out, (DEST/'client-stderr.txt').open('xb') as err:
        try:
            r = subprocess.run(argv, stdout=out, stderr=err, timeout=45, check=False)
            result = dict(returncode=r.returncode, host_timeout=False)
        except subprocess.TimeoutExpired:
            result = dict(returncode=None, host_timeout=True)
    result['finished_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
    (DEST/'client-result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))

if __name__ == '__main__':
    main()
