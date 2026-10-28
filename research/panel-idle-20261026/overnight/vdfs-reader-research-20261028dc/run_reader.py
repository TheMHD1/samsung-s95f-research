#!/usr/bin/env python3
"""Offline pinned VDFS userspace reader in a minimal read-only-root sandbox."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import signal
import stat
import subprocess
import time

HERE = Path(__file__).resolve().parent
TOOL = HERE / 'private/vdfs-unpack-patched/target/release/vdfs-unpack'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()


def limits():
    resource.setrlimit(resource.RLIMIT_AS, (6*1024**3, 6*1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (600, 600))
    resource.setrlimit(resource.RLIMIT_FSIZE, (512*1024**2, 512*1024**2))
    resource.setrlimit(resource.RLIMIT_NOFILE, (256, 256))


def command(image, tree, catalog):
    # No home, credentials, network, writable host root, or OEM executable is
    # exposed. Only this fresh output tree is a writable persistent bind.
    argv = ['/usr/bin/bwrap', '--unshare-all', '--die-with-parent', '--new-session',
            '--clearenv', '--setenv', 'PATH', '/usr/bin:/bin',
            '--ro-bind', '/usr', '/usr', '--ro-bind', '/lib', '/lib',
            '--ro-bind', '/lib64', '/lib64', '--proc', '/proc', '--dev', '/dev',
            '--dir', '/tmp', '--dir', '/input', '--ro-bind', str(image), '/input/image.img',
            '--ro-bind', str(TOOL), '/reader', '--dir', '/work', '--bind', str(tree), '/work',
            '--chdir', '/work', '--remount-ro', '/', '--', '/reader', '/input/image.img', '-o', '/work']
    if catalog: argv.append('--catalog-only')
    return argv


def run(image:Path, expected:str, output:Path, catalog:bool):
    if not re.fullmatch('[0-9a-f]{64}', expected): raise ValueError('input SHA256 required')
    if image.is_symlink(): raise ValueError('input symlink')
    image = image.resolve(strict=True)
    before = image.stat()
    if not stat.S_ISREG(before.st_mode): raise ValueError('input regular file required')
    if sha(image) != expected: raise ValueError('input hash mismatch')
    pin = json.loads((HERE/'reader-pin.json').read_text())
    if sha(TOOL) != pin['patched_tool_sha256']: raise ValueError('reader hash mismatch')
    os.umask(0o077)
    output.mkdir(mode=0o700)  # exclusive, never reuse prior partial output
    tree = output/'tree'; tree.mkdir(mode=0o700)
    start = time.monotonic(); code = None; timed_out = False
    with (output/'stdout.txt').open('xb') as out, (output/'stderr.txt').open('xb') as err:
        p = subprocess.Popen(command(image, tree, catalog), stdout=out, stderr=err,
                             stdin=subprocess.DEVNULL, start_new_session=True, preexec_fn=limits)
        try: code = p.wait(timeout=900)
        except subprocess.TimeoutExpired:
            timed_out=True; os.killpg(p.pid,signal.SIGKILL)
            code=p.wait(timeout=5)
    after = image.stat()
    unchanged = (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(
        after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns) and sha(image)==expected
    text = (output/'stdout.txt').read_text(errors='strict')
    rows = re.findall(r'^VDFS_RESULT (.+)$',text,re.M)
    fields = dict(x.split('=',1) for x in rows[0].split()) if len(rows)==1 else {}
    accepted = (code==0 and not timed_out and unchanged and len(rows)==1 and
                fields.get('errors')=='0' and fields.get('catalog_only')==str(int(catalog)) and
                fields.get('file_authentication_validated')=='0' and
                (output/'stderr.txt').stat().st_size==0)
    result = dict(schema='vdfs-contained-reader-v1', input_sha256=expected,input_bytes=before.st_size,
                  reader_sha256=pin['patched_tool_sha256'], catalog_only=catalog,
                  completed_without_reported_errors=accepted, exit_code=code,timed_out=timed_out,
                  source_unchanged=unchanged,elapsed_seconds=round(time.monotonic()-start,3),
                  counters=fields, file_authentication_validated=False,
                  full_filesystem_schema_validated=False, oem_code_executed=False,
                  target_operations=0, filesystem_images_mounted=0,
                  sandbox_private_bind_mounts=True)
    (output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',required=True,type=Path)
    p.add_argument('--sha256',required=True)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--catalog-only',action='store_true')
    a=p.parse_args(); result=run(a.input,a.sha256,a.output,a.catalog_only)
    print(json.dumps(result)); return 0 if result['completed_without_reported_errors'] else 1


if __name__=='__main__': raise SystemExit(main())
