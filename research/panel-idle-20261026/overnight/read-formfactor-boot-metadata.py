#!/usr/bin/env python3
"""One bounded read of boot metadata. Default prints intent; --run is explicit.

No hardware getter or device control. A saved namespace is never reused.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
DEST = HERE / 'formfactor-boot-metadata-20261026'
CLIENT = Path('${S95F_EVIDENCE_ROOT}/root-access/s95f-access.py')
COMMAND = '''set -euo pipefail
echo '@@ BOOT_START'
cat /proc/sys/kernel/random/boot_id
echo '@@ TIME_START'
date -u +%s
cat /proc/uptime
echo '@@ KERNEL_RELEASE'
uname -r
echo '@@ SYSTEM_MODULE_HASH'
sha256sum /lib/modules/5.4.261/kernel/system_drv.ko
echo '@@ CMDLINE_BASE64'
head -c 8193 /proc/cmdline | base64
echo '@@ BOOT_END'
cat /proc/sys/kernel/random/boot_id
echo '@@ TIME_END'
date -u +%s
cat /proc/uptime
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    intent = {
        'purpose': 'Bounded /proc/cmdline metadata for ffinfo boot-parameter provenance; no live cached field, hardware getter, control, or physical result.',
        'command': COMMAND,
        'command_sha256': hashlib.sha256(COMMAND.encode()).hexdigest(),
        'client_sha256': hashlib.sha256(CLIENT.read_bytes()).hexdigest(),
        'argv': ['python3', str(CLIENT), 'root', '--persistent-only', '--timeout', '25', '--command', COMMAND],
        'physical_state': 'unobserved',
        'retry': False,
    }
    if not args.run:
        print(json.dumps(intent, indent=2))
        return
    DEST.mkdir(exist_ok=False)
    intent['started_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (DEST/'intent.json').write_text(json.dumps(intent, indent=2)+'\n')
    with (DEST/'client-stdout.json').open('xb') as out, (DEST/'client-stderr.txt').open('xb') as err:
        try:
            result = subprocess.run(intent['argv'], stdout=out, stderr=err, timeout=45, check=False)
            status = {'returncode': result.returncode, 'host_timeout': False}
        except subprocess.TimeoutExpired:
            status = {'returncode': None, 'host_timeout': True}
    status['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (DEST/'client-result.json').write_text(json.dumps(status, indent=2)+'\n')
    print(json.dumps(status))


if __name__ == '__main__':
    main()
