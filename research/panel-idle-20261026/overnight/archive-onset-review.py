#!/usr/bin/env python3
"""Archive an exact observer revision for review, without contacting the TV."""
from pathlib import Path
import argparse
import ast
import ctypes
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile

BASE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def ensure(condition, message):
    if not condition:
        raise ValueError(message)


def pure_generator(data, filename):
    """Extract two constrained functions and literal constants, not module code."""
    tree = ast.parse(data, filename=filename)
    constants = {}
    functions = {}
    required = {'AVE_PATH', 'AVE_SHA', 'AVOC_PATH', 'AVOC_SHA', 'BUILD',
                'DEV_PATH', 'DEV_SHA', 'REMOTE_ROOT', 'SUFFIX',
                'TRACE_DRAIN_SECONDS', 'TRACE_DRAIN_MIN_SECONDS', 'TRACE_DRAIN_MAX_SECONDS'}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in required:
                constants[target.id] = ast.literal_eval(node.value)
        if isinstance(node, ast.FunctionDef) and node.name in {'require', 'build_remote_script'}:
            ensure(not node.decorator_list, 'Generator decorators are not permitted')
            functions[node.name] = node
    ensure(set(constants) == required and set(functions) == {'require', 'build_remote_script'},
           'Missing constrained generator definitions')
    for name, node in functions.items():
        allowed_calls = {'ValueError'} if name == 'require' else {'require', 're.fullmatch'}
        for part in ast.walk(node):
            if isinstance(part, ast.Call):
                ensure(ast.unparse(part.func) in allowed_calls, 'Unexpected generator call')
            ensure(not isinstance(part, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal,
                                         ast.With, ast.AsyncWith, ast.ClassDef)), 'Impure generator node')
            if isinstance(part, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = part.targets if isinstance(part, ast.Assign) else [part.target]
                ensure(all(isinstance(target, ast.Name) and target.id in {
                    'out', 'tr', 'stage', 'expiry_log', 'script'} for target in targets), 'Unexpected generator assignment')
    module = ast.Module(body=[functions['require'], functions['build_remote_script']], type_ignores=[])
    namespace = {'__builtins__': {'str': str, 'int': int, 'bool': bool, 'ValueError': ValueError},
                 're': re, **constants}
    exec(compile(module, filename, 'exec'), namespace)
    return namespace['build_remote_script']


def sync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def publish_directory(temporary, destination):
    """Linux renameat2 with RENAME_NOREPLACE: atomic and exclusive."""
    libc = ctypes.CDLL(None, use_errno=True)
    rename = libc.renameat2
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    rename.restype = ctypes.c_int
    if rename(-100, os.fsencode(temporary), -100, os.fsencode(destination), 1) != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(destination))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source_sha256')
    parser.add_argument('tests_sha256')
    args = parser.parse_args()
    for value in (args.source_sha256, args.tests_sha256):
        if re.fullmatch(r'[0-9a-f]{64}', value) is None:
            parser.error('Expected full lowercase SHA-256 values')
    source = BASE / 'observed-onset-capture.py'
    tests = BASE / 'observed-onset-capture-tests.py'
    source_data, tests_data = source.read_bytes(), tests.read_bytes()
    ensure(sha(source_data) == args.source_sha256, 'Source changed before archive')
    ensure(sha(tests_data) == args.tests_sha256, 'Tests changed before archive')
    generator = pure_generator(source_data, str(source))
    generated = {}
    for seconds in (5, 10, 85, 90):
        label = f'review-{args.source_sha256[:12]}-s{seconds}'
        shell = generator(label, seconds, allow_short=seconds < 85).encode()
        check = subprocess.run(['/bin/sh', '-n'], input=shell, capture_output=True)
        ensure(check.returncode == 0, check.stderr.decode(errors='replace'))
        generated[f'remote-{seconds}.sh'] = shell
    ensure(source.read_bytes() == source_data, 'Source changed while preparing archive')
    ensure(tests.read_bytes() == tests_data, 'Tests changed while preparing archive')
    parent = BASE / 'onset-review-archives'
    parent.mkdir(mode=0o700, exist_ok=True)
    destination = parent / f'{args.source_sha256[:16]}-{args.tests_sha256[:12]}'
    files = {'observed-onset-capture.py': source_data,
             'observed-onset-capture-tests.py': tests_data, **generated}
    metadata = {
        'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'status': 'Archived for independent review; not cleared for live execution',
        'source_original_path': str(source), 'tests_original_path': str(tests),
        'archive_tool_tv_calls': 0,
        'checks': ['Exact expected source/test hashes', 'Four generated shells pass sh -n'],
        'unit_tests_run_by_archive_tool': False,
        'qualification': 'Archived Python retains original relative-path assumptions. Review bytes directly; run tests at original paths only after verifying exact hashes.',
        'files': {name: {'bytes': len(data), 'sha256': sha(data)}
                  for name, data in files.items()},
    }
    temporary = Path(tempfile.mkdtemp(prefix='.onset-review-', dir=parent))
    try:
        for name, data in files.items():
            with (temporary / name).open('xb') as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        with (temporary / 'manifest.json').open('x') as stream:
            json.dump(metadata, stream, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        sync_directory(temporary)
        publish_directory(temporary, destination)
        sync_directory(parent)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    print(json.dumps({'archive': str(destination), 'files': len(files),
                      'source_sha256': args.source_sha256, 'tests_sha256': args.tests_sha256,
                      'live_cleared': False}))


if __name__ == '__main__':
    main()
