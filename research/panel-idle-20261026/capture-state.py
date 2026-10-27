#!/usr/bin/env python3
"""Record the stock compositor and display diagnostics; no display policy writes."""
from pathlib import Path
import argparse
import base64
import hashlib
import json
import re
import subprocess

BASE = Path(__file__).resolve().parent
ACCESS = BASE.parent/'root-access/s95f-access.py'
parser = argparse.ArgumentParser()
parser.add_argument('label')
parser.add_argument('--fetch-only', action='store_true')
args = parser.parse_args()
if not re.fullmatch(r'[a-z][a-z0-9-]{0,45}', args.label):
    parser.error('use a unique lowercase label')
out = BASE/'paired-capture'
out.mkdir(exist_ok=True)
destination = out/(args.label+'.json')
if destination.exists() and not args.fetch_only:
    raise SystemExit('Existing capture; use another label')
tvdir = '/tmp/researcher-panel-trace-20261026'
shot = tvdir+'/'+args.label+'.png'
command = f'''date -u
cat /proc/sys/kernel/random/boot_id
cat /proc/uptime
mkdir -p {tvdir}
test ! -e {shot} || exit 80
enlightenment_info -dump_screen -p {tvdir}/ -n {args.label}.png
enlightenment_info -topvwins
enlightenment_info -hwc_wins
enlightenment_info -screen_info
enlightenment_info -scrsaver info
enlightenment_info -compobjs simple
cat /sys/kernel/debug/dri/0/framebuffer
dbus-send --system --print-reply --reply-timeout=1000 --dest=org.tizen.tv.avoc /org/tizen/tv/avoc org.tizen.tv.avoc.AvOutputControl.GetPanelMute
dbus-send --system --print-reply --reply-timeout=1000 --dest=org.tizen.system.deviced /Org/Tizen/System/DeviceD/Display org.tizen.system.deviced.display.GetScreenState
dbus-send --system --print-reply --reply-timeout=1000 --dest=org.tizen.system.deviced /Org/Tizen/System/DeviceD/Display org.tizen.system.deviced.display.BurnInProtectionInProgress
dmesg
vlogutil -v kerneltime -t 20 2>&1 | grep -Ei 'FSAVMute|SetNewHome|newhome|newHome|DEVICED.*(power|sensing|dpms|state)|SCRSAVER|SCREENSAVER|tcon-monitor|AVEMonDIM.*(ScreenSaver|PowerConsumption|reboot|recover)' | tail -n 180
cat /proc/uptime
ls -l {shot}
'''

def root(cmd):
    p = subprocess.run(['python3',str(ACCESS),'root','--timeout','25','--command',cmd],
                       capture_output=True,text=True,timeout=50)
    if p.returncode:
        raise RuntimeError(p.stderr[:300] or p.stdout[:300])
    result = json.loads(p.stdout)
    c = result['commands'][0]
    if c['exit_code'] or c['timed_out']:
        raise RuntimeError('capture command failed')
    return p.stdout, c['stdout']

if args.fetch_only:
    raw = destination.read_text()
    text = json.loads(raw)['commands'][0]['stdout']
else:
    raw, text = root(command)
    destination.write_text(raw)
_, metadata = root('wc -c '+shot+'\nsha256sum '+shot)
fields = metadata.split()
length, digest = int(fields[0]), fields[2]
if not 0 < length < 32 * 1024 * 1024:
    raise RuntimeError('unexpected screenshot length')
blocks = []
for index in range((length+131071)//131072):
    _, encoded = root(f'dd if={shot} bs=131072 skip={index} count=1 2>/dev/null | base64')
    blocks.append(base64.b64decode(encoded,validate=False))
pixels = b''.join(blocks)
if len(pixels) != length or hashlib.sha256(pixels).hexdigest() != digest:
    raise RuntimeError('screenshot transfer length/hash mismatch')
png = out/(args.label+'.png')
png.write_bytes(pixels)
summary = {'label':args.label,'sha256':hashlib.sha256(pixels).hexdigest(),
           'physical_state':'pending explicit owner label','bytes':len(pixels),
           'time_header':text.splitlines()[:3]}
try:
    from PIL import Image
    with Image.open(png) as im:
        rgb = im.convert('RGB')
        summary['size'] = list(rgb.size)
        summary['nonblack_pixels'] = sum(1 for px in rgb.getdata() if any(px))
except ImportError:
    pass
(out/(args.label+'-summary.json')).write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
