#!/usr/bin/env python3
"""Hash-pinned root transport with fixed foreground firmware-stream timing margin."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
RUNNER = BASE / 'managed-tcon-status-read/run-status-read.py'
RUNNER_SHA256 = '7ca9bf01f3df4524f4f04e561dc4839d0805f4062f665b5c1b9a397adf788c8a'
ACCESS = BASE.parents[1] / 'root-access/s95f-access.py'
ACCESS_SHA256 = '3a92e02003ce51d2faeace231191f6f0c73731f2bfca9caa196e05b195b439a5'
REMOTE_TIMEOUT_SECONDS = 120
HOST_TIMEOUT_SECONDS = 150
MAX_COMMAND = 8192
MAX_RESPONSE = 65536


def digest(data):
    return hashlib.sha256(data).hexdigest()


if digest(RUNNER.read_bytes()) != RUNNER_SHA256:
    raise ValueError('Root runner identity mismatch')
if digest(ACCESS.read_bytes()) != ACCESS_SHA256:
    raise ValueError('Root access client identity mismatch')

spec = importlib.util.spec_from_file_location('pinned_margin_base_runner', RUNNER)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
base.require(base.ACCESS.resolve() == ACCESS.resolve(), 'Root access path mismatch')
base.require(base.ACCESS_SHA256 == ACCESS_SHA256, 'Root access pin mismatch')
base.require(base.MAX_COMMAND == MAX_COMMAND and base.MAX_RESPONSE == MAX_RESPONSE,
             'Root transport bounds mismatch')
save = base.save
validate_response = base.validate_response
retained = base.retained


def root(command, record, output):
    size = len(command.encode())
    base.require(0 < size <= MAX_COMMAND, 'Root command size')
    argv = ['python3', str(ACCESS), 'root', '--persistent-only', '--timeout',
            str(REMOTE_TIMEOUT_SECONDS), '--command', command]
    item = {'command': command, 'command_bytes': size,
            'remote_timeout_seconds': REMOTE_TIMEOUT_SECONDS,
            'host_timeout_limit_seconds': HOST_TIMEOUT_SECONDS,
            'started_utc': base.now()}
    calls = record.setdefault('calls', [])
    base.require(isinstance(calls, list), 'Internal call record')
    calls.append(item)
    base.save(output, record)
    try:
        process = subprocess.run(argv, capture_output=True,
                                 timeout=HOST_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as exc:
        item.update(host_timeout=True, timeout_seconds=exc.timeout,
                    partial_stdout=base.retained(exc.stdout),
                    partial_stderr=base.retained(exc.stderr),
                    finished_utc=base.now())
        base.save(output, record)
        raise
    item.update(host_timeout=False, transport_exit=process.returncode,
                transport_stdout=base.retained(process.stdout),
                transport_stderr=base.retained(process.stderr),
                finished_utc=base.now())
    base.save(output, record)
    base.require(len(process.stdout) + len(process.stderr) <= MAX_RESPONSE,
                 'Response over 64 KiB')
    base.require(process.returncode == 0 and process.stderr == b'',
                 'Root client failed')
    try:
        response = json.loads(process.stdout.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise base.ContractError('Root response is not strict UTF-8 JSON') from exc
    item['response'] = response
    base.save(output, record)
    return base.validate_response(response, command)
