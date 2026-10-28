#!/usr/bin/env python3
"""Run one explicit parent CLI step, retaining intent and completion. No retries."""
import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
os.umask(0o077)
if len(sys.argv) < 4 or not re.fullmatch(r'[a-z][a-z0-9-]{0,63}', sys.argv[1]) or sys.argv[2] != '--':
    raise ValueError('one step label, separator and explicit argv required')
label = sys.argv[1]
argv = sys.argv[3:]
folder = HERE/(label+'-logs')
folder.mkdir(mode=0o700, exist_ok=False)
intent = {'schema':'fo-parent-explicit-step-v1','argv':argv,'automaticRetry':False,
          'startedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'startedHostMonotonicNs':time.monotonic_ns()}
(folder/'intent.json').write_text(json.dumps(intent, indent=2)+'\n')
with (folder/'stdout.txt').open('xb') as stdout, (folder/'stderr.txt').open('xb') as stderr:
    # The individual reviewed CLI owns its root-call deadlines. Do not add a
    # parent kill that could interrupt an accepted controller transaction.
    done = subprocess.run(argv, stdout=stdout, stderr=stderr, check=False)
completion = {'exitCode':done.returncode,'endedHostMonotonicNs':time.monotonic_ns(),
              'endedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(folder/'completion.json').write_text(json.dumps(completion, indent=2)+'\n')
print(json.dumps({'step':label,'exitCode':done.returncode,'logs':str(folder)},sort_keys=True))
raise SystemExit(done.returncode)
