#!/usr/bin/env python3
"""Build four fixed read-only sector derivatives without editing frozen evidence."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import argparse

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
SOURCE = BASE / 'managed-usb-emmc-sector-read-once'
DOTNET = BASE.parents[1] / 'live-cast/sdk/runtime/dotnet'

def need(ok, why):
    if not ok:
        raise ValueError(why)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--protocol-followup', action='store_true')
    args = parser.parse_args()
    need(sha((SOURCE / 'Program.cs').read_bytes()) == 'b4e400c973fc5c6c7737a0c6e21fe291c9320d57403e86968d0c6c5180293e49', 'source pin')
    need(sha((SOURCE / 'run-once.py').read_bytes()) == '1a6c5870cc4eb33493d6bfe3b79eca03ab108741ae251a02014fe1ea85f1ffc5', 'wrapper pin')
    rows = json.loads((HERE/'builds.json').read_text()) if args.protocol_followup else []
    for address in ((0x28e00, 0x28a00) if args.protocol_followup else (0x200, 0x29000, 0x40200, 0x80000)):
        build = BASE / ('managed-usb-emmc-sector-' + format(address, '06x'))
        build.mkdir(exist_ok=False)
        header = struct.pack('<III', 0x203, address, 512).hex()
        text = (SOURCE / 'Program.cs').read_text()
        need(text.count('030200000000000000020000') == 2, 'header occurrence count')
        text = text.replace('030200000000000000020000', header.upper())
        need(text.count('address = "0x0"') == 1, 'address occurrence count')
        text = text.replace('address = "0x0"', f'address = "{address:#x}"')
        (build / 'Program.cs').write_text(text)
        project = 'ManagedUsbEmmcSectorReadOnce.csproj'
        (build / project).write_bytes((SOURCE / project).read_bytes())
        wrapper = (SOURCE / 'run-once.py').read_text()
        wrapper = wrapper.replace('030200000000000000020000', header)
        wrapper = wrapper.replace('"address": "0x0"', f'"address": "{address:#x}"')
        (build / 'run-once.py').write_text(wrapper)
        built = subprocess.run([str(DOTNET), 'build', '-c', 'Release', '--nologo', str(build / project)], capture_output=True, text=True)
        (build / 'build.log').write_text(built.stdout + built.stderr)
        need(built.returncode == 0, 'build failed')
        checks = []
        for args, expected in (([], 0), (['--self-test'], 0), (['--execute'], 64), (['--unknown'], 63)):
            done = subprocess.run([str(DOTNET), str(build / 'bin/Release/net6.0/ManagedUsbEmmcSectorReadOnce.dll'), *args], capture_output=True, text=True)
            need(done.returncode == expected, 'host check ' + str(args))
            checks.append(dict(args=args, exit_code=done.returncode, stdout=done.stdout, stderr=done.stderr))
        names = ['Program.cs', project] + ['bin/Release/net6.0/ManagedUsbEmmcSectorReadOnce.' + s for s in ('dll', 'deps.json', 'runtimeconfig.json')]
        manifest = dict(schema='usb-fixed-emmc-sector-read-build-v1', fixed_target='0x203', fixed_address=hex(address), fixed_length=512, header_hex=header,
                        files={n:dict(size=len((build/n).read_bytes()), sha256=sha((build/n).read_bytes())) for n in names}, checks=checks,
                        acceptance_scope='Exact counts and cleanup only; ignored storage-leaf result means freshness and running-image identity remain unproved.')
        raw = (json.dumps(manifest, indent=2) + '\n').encode()
        (build / 'build-manifest.json').write_bytes(raw)
        rows.append(dict(address=hex(address), header_hex=header, build=str(build), manifest_sha256=sha(raw), wrapper_sha256=sha((build/'run-once.py').read_bytes())))
    (HERE / 'builds.json').write_text(json.dumps(rows, indent=2) + '\n')
    print(json.dumps(rows, indent=2))

if __name__ == '__main__':
    main()
