#!/usr/bin/env python3
"""Read a filtered snapshot of retained kernel messages; never clear the ring.

Only positive retained text is evidence. Omitted/overwritten records, truncation,
and logging gates prevent any absence or physical inference.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
DEST = HERE/'private-rpm-log-baseline-20261026'
CLIENT = Path('${S95F_EVIDENCE_ROOT}/root-access/s95f-access.py')
COMMAND = '''set -euo pipefail
echo '@@ BOOT_START'
cat /proc/sys/kernel/random/boot_id
echo '@@ TIME_START'
date -u +%s
cat /proc/uptime
echo '@@ RETAINED_PRIVATE_HDMI_MESSAGES'
dmesg | awk 'index($0,"[sdp_runtime_pm]") && index($0,"sdp-hdmi") {n++; if(length($0)>512){bad=1;next} a[n%64]=$0} END {print "MATCHED_ROWS " n+0; if(bad){print "OVERSIZE_ROW";exit 66} first=n>64?n-63:1; for(i=first;i<=n;i++)print a[i%64]; print "END_ROWS"}'
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
                  purpose=__doc__, retry=False, physical_state='unobserved', absence_claim_supported=False)
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
