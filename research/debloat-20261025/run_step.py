#!/usr/bin/env python3
"""Run a reviewed local shell payload through the existing S95F guard."""
import json
import os
from pathlib import Path
import subprocess
import sys

os.umask(0o077)
base = Path(__file__).resolve().parent
if len(sys.argv) != 2 or not sys.argv[1].replace('-', '').isalnum():
    raise SystemExit('usage: run_step.py STEP (reads STEP.sh)')
step = sys.argv[1]
payload = base / (step + '.sh')
output = base / (step + '.json')
if output.exists():
    raise SystemExit('Evidence already exists; choose a new step name.')
command = payload.read_text()
if len(command.encode()) > 8192:
    raise SystemExit('Payload exceeds guarded command limit.')
result = subprocess.run([
    str(base.parent / 'root-access/s95f-access.py'), 'root',
    '--timeout', '90', '--command', command,
], capture_output=True, text=True, timeout=240)
output.write_text(result.stdout)
(base / (step + '.stderr')).write_text(result.stderr)
print('Guard exit:', result.returncode)
if result.returncode == 0:
    evidence = json.loads(result.stdout)
    print(json.dumps({key: evidence.get(key) for key in (
        'uid', 'euid', 'smack', 'system_files_unchanged', 'staging_cleaned'
    )}))
    for item in evidence['commands']:
        print(item['stdout'])
        print(item['stderr'], file=sys.stderr)
else:
    print(result.stderr, file=sys.stderr)
raise SystemExit(result.returncode)
