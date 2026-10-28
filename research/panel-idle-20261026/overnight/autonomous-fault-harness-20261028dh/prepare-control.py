#!/usr/bin/env python3
"""Fresh cached USB identity and FD census; no vendor transfers or UI keys."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shlex

HERE = Path(__file__).resolve().parent
BASE = HERE.parent

def load(path, pin, name):
    if hashlib.sha256(path.read_bytes()).hexdigest() != pin:
        raise ValueError(name + ' identity')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    out = HERE / 'control-readiness-01'
    out.mkdir(mode=0o700)
    wrapper = load(BASE / 'firmware-rtp-producer-20261028df/capture/run-once.py',
                   '946c0b8f66156b70d69bbf0acb121a165d7db26fac09811b247c8cdc8b008ff9', 'df_wrapper')
    root = load(BASE / 'managed-ui-tab-launch/root-with-margin.py',
                'bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a', 'readiness_root')
    usb = '/sys/bus/usb/devices/7-1'
    intf = usb + ':1.2'
    commands = {'boot': 'cat /proc/sys/kernel/random/boot_id',
                'sysfsRealpath': f'readlink -f {usb}',
                'sysfsStat': f'stat -L -c "%d:%i" {usb}',
                'busnum': f'cat {usb}/busnum', 'devnum': f'cat {usb}/devnum',
                'deviceNode': 'echo "$tvnode"',
                'nodeStat': 'stat -L -c "%t:%T:%i" "$tvnode"',
                'descriptorsSha256': f'sha256sum {usb}/descriptors | cut -d " " -f1'}
    for key, suffix in [('configuration', 'bConfigurationValue'), ('authorized', 'authorized'), ('runtimeStatus', 'power/runtime_status')]:
        commands[key] = f'cat {usb}/{suffix}'
    for key, suffix in [('interfaceNumber', 'bInterfaceNumber'), ('alternate', 'bAlternateSetting'),
                        ('interfaceClass', 'bInterfaceClass'), ('interfaceSubClass', 'bInterfaceSubClass'), ('interfaceProtocol', 'bInterfaceProtocol')]:
        commands[key] = f"awk '{{print $1}}' {intf}/{suffix}"
    command = 'set -eu\n' + f'tvnum=$(cat {usb}/devnum)\n' + "tvnode=$(printf '/dev/bus/usb/007/%03d' \"$tvnum\")\n"
    for key in wrapper.META_KEYS:
        command += 'echo ' + shlex.quote('@@ ' + key) + '\n' + commands[key] + '\n'
    command += f'test ! -e {intf}/driver\ntest ! -L {intf}/driver\necho "@@ USB_LIFECYCLE"\ndmesg | sed -n "/usb 7-1/p" | tail -12\necho "@@ UPTIME"\ncat /proc/uptime\n'
    record = {'schema': 'autonomous-onset-readiness-raw-v1', 'calls': []}
    text = root.root(command, record, out / 'metadata.json')
    (out / 'metadata.txt').write_text(text)
    sections = {}
    current = None
    for line in text.splitlines():
        if line.startswith('@@ '):
            current = line[3:]
            if current in sections: raise ValueError('duplicate section')
            sections[current] = []
        else:
            if current is None: raise ValueError('unframed')
            sections[current].append(line)
    identity = {key: '\n'.join(sections[key]).strip() for key in wrapper.META_KEYS}
    (out / 'identity.json').write_text(json.dumps(identity, indent=2) + '\n')
    census = root.root('set -eu\n' + wrapper.metadata_body(identity, 'DH_READY'), record, out / 'census.json')
    parsed = wrapper.parse_metadata(census, 'DH_READY')
    (out / 'census.txt').write_text(census)
    (out / 'census-summary.json').write_text(json.dumps(parsed, indent=2) + '\n')
    print(json.dumps({'identity': identity, 'census': parsed,
                      'usb_lifecycle': sections['USB_LIFECYCLE'],
                      'physical_state': 'unobserved', 'vendor_transfers': 0}))

if __name__ == '__main__':
    main()
