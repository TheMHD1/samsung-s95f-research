#!/usr/bin/env python3
"""Read one stock event format and global baseline; no trace enable or control."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
DEST = HERE/'pm-idle-tracepoint-format-20261026'
CLIENT = Path('${S95F_EVIDENCE_ROOT}/root-access/s95f-access.py')
COMMAND = '''set -euo pipefail
echo '@@ BOOT_START'
cat /proc/sys/kernel/random/boot_id
echo '@@ TIME_START'
date -u +%s
cat /proc/uptime
echo '@@ GLOBAL_START'
cat /sys/kernel/debug/tracing/tracing_on
cat /sys/kernel/debug/tracing/current_tracer
echo '@@ FORMAT rpm/rpm_idle'
cat /sys/kernel/debug/tracing/events/rpm/rpm_idle/format
echo '@@ END_FORMAT'
echo '@@ GLOBAL_END'
cat /sys/kernel/debug/tracing/tracing_on
cat /sys/kernel/debug/tracing/current_tracer
echo '@@ BOOT_END'
cat /proc/sys/kernel/random/boot_id
echo '@@ TIME_END'
date -u +%s
cat /proc/uptime
'''


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run', action='store_true')
    args = ap.parse_args()
    argv = ['python3', str(CLIENT), 'root', '--persistent-only', '--timeout', '25', '--command', COMMAND]
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
