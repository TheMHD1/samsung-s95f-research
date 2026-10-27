#!/usr/bin/env python3
"""Explicit rollback entry point. No mutation occurs merely by importing this file."""
import json
import pathlib
import subprocess

BASE = pathlib.Path(__file__).resolve().parent

def main():
    output = BASE / 'restore-native-home.json'
    if output.exists():
        raise SystemExit('A rollback result already exists; inspect it before retrying.')
    script = (BASE / 'restore-native-home.sh').read_text()
    result = subprocess.run([
        'python3', '${S95F_EVIDENCE_ROOT}/root-access/s95f-access.py',
        'root', '--timeout', '25', '--command', script,
    ], capture_output=True, text=True, check=True)
    output.write_text(result.stdout)
    (BASE / 'restore-native-home.stderr').write_text(result.stderr)
    evidence = json.loads(result.stdout)
    command = evidence['commands'][0]
    print(command['stdout'])
    if command.get('stderr'):
        print(command['stderr'])
    raise SystemExit(command['exit_code'])

if __name__ == '__main__':
    main()
