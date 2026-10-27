#!/usr/bin/env python3
"""One fixed read-only residue check for the completed quiescence smoke."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
DEST = HERE/'quiescent-smoke-residue-20261026'
CLIENT = Path('${S95F_EVIDENCE_ROOT}/root-access/s95f-access.py')
COMMAND = '''set -eu
echo BOOT_START
boot=$(cat /proc/sys/kernel/random/boot_id)
echo "$boot"
test "$boot" = 00000000-0000-4000-8000-000000000000 || exit 61
echo TIME_START
date -u +%s
cat /proc/uptime
echo GLOBAL_START
cat /sys/kernel/debug/tracing/tracing_on
cat /sys/kernel/debug/tracing/current_tracer
status=0
for p in /sys/kernel/debug/tracing/instances/researcher-quiescent-pm-onset-qpm-smoke-20261026t204819 /sys/kernel/debug/tracing/instances/researcher-pm-onset-qpm-smoke-20261026t204819 /tmp/researcher-observed-quiescent-pm-onset-20261026/qpm-smoke-20261026t204819 /tmp/researcher-observed-quiescent-pm-onset-stage-20261026/qpm-smoke-20261026t204819 /tmp/researcher-observed-pm-onset-20261026/qpm-smoke-20261026t204819 /tmp/researcher-observed-pm-onset-stage-20261026/qpm-smoke-20261026t204819; do
 if test -e "$p" || test -L "$p"; then printf 'PRESENT %s\n' "$p"; status=1; else printf 'ABSENT %s\n' "$p"; fi
done
echo GLOBAL_END
cat /sys/kernel/debug/tracing/tracing_on
cat /sys/kernel/debug/tracing/current_tracer
echo BOOT_END
cat /proc/sys/kernel/random/boot_id
echo TIME_END
date -u +%s
cat /proc/uptime
exit "$status"
'''


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run', action='store_true')
    args = ap.parse_args()
    argv = ['python3', str(CLIENT), 'root', '--persistent-only', '--timeout', '25',
            '--command', COMMAND]
    intent = dict(command=COMMAND, command_sha256=hashlib.sha256(COMMAND.encode()).hexdigest(),
                  client_sha256=hashlib.sha256(CLIENT.read_bytes()).hexdigest(), argv=argv,
                  purpose=__doc__, retry=False, physical_state='unobserved')
    if not args.run:
        print(json.dumps(intent, indent=2))
        return
    DEST.mkdir(exist_ok=False)
    intent['started_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (DEST/'intent.json').write_text(json.dumps(intent, indent=2)+'\n')
    with (DEST/'client-stdout.json').open('xb') as out, (DEST/'client-stderr.txt').open('xb') as err:
        try:
            result = subprocess.run(argv, stdout=out, stderr=err, timeout=45, check=False)
            status = dict(returncode=result.returncode, host_timeout=False)
        except subprocess.TimeoutExpired:
            status = dict(returncode=None, host_timeout=True)
    status['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (DEST/'client-result.json').write_text(json.dumps(status, indent=2)+'\n')
    print(json.dumps(status))


if __name__ == '__main__':
    main()
