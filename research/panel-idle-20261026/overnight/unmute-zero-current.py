#!/usr/bin/env python3
"""Default-dry preparation for exactly one public SetPanelMute(int32:0)."""
from pathlib import Path
import argparse, hashlib, json, re

HERE=Path(__file__).resolve().parent
ACCESS=Path('${S95F_EVIDENCE_ROOT}/root-access/s95f-access.py')
BOOT='00000000-0000-4000-8000-000000000000'; PID=706; START=603; SECONDS=12
MAIN='067ddb8f639f8e91d02524f0820fb3a56e2d9f174d0f3f75a5dec963f7339410'
def require(ok,msg):
    if not ok: raise ValueError(msg)
def build(label):
    t='/sys/kernel/debug/tracing/instances/researcher-'+label; r='/tmp/researcher-unmute-zero-'+label
    d='dbus-send --system --print-reply --reply-timeout=1500 --dest=org.tizen.tv.avoc /org/tizen/tv/avoc org.tizen.tv.avoc.AvOutputControl.'
    lines=['set -euo pipefail',f'P={PID}; T={t}; R={r}',"trap 'echo 0 > \"$T/tracing_on\" 2>/dev/null || true; echo 0 > \"$T/events/enable\" 2>/dev/null || true; rmdir \"$T\" 2>/dev/null || true' EXIT",f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}',"x=$(cat /proc/$P/stat); x=${x##*) }; set -- $x; test \"${20}\" = "+str(START),'test "$(readlink -f /proc/$P/exe)" = /usr/bin/avocd',f'test "$(sha256sum /usr/lib/libhdmi-control.so.0.1|cut -d\' \"\' -f1)" = {MAIN}','mkdir "$T"',f'{d}GetPanelMute > "$R.before"',f'{d}GetPanelMuteCaseStatus > "$R.case"',"awk '$1==\"int32\"{n++;if($2!=0)b=1}END{exit(n!=2||b)}' \"$R.before\"","awk '$1==\"int32\"{n++;if($2!=0)b=1}END{exit(n!=2||b)}' \"$R.case\"",'echo nop > "$T/current_tracer"','echo 1 > "$T/events/enable"','echo 1 > "$T/tracing_on"','echo BEFORE_SINGLE_UNMUTE_ZERO > "$T/trace_marker"','echo UNMUTE_REPLY_BEGIN >> "$R"','rc=0',f'{d}SetPanelMute int32:0 >> "$R" 2>&1 || rc=$?','echo "PROBE_DBUS_EXIT=$rc" >> "$R"','echo UNMUTE_REPLY_END >> "$R"','echo AFTER_SINGLE_UNMUTE_ZERO > "$T/trace_marker"',f'sleep {SECONDS}','echo 0 > "$T/tracing_on"','cat "$T/trace"','sha256sum "$R"','wc -c "$R"']
    s='\n'.join(lines)+'\n'; require(s.count('SetPanelMute int32:0')==1 and 'int32:1' not in s,'single zero only'); require(len(s.encode())<=8192,'command size'); return s
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('label');p.add_argument('--run',action='store_true');p.add_argument('--physical-black-now',action='store_true');p.add_argument('--screen-optimization-inactive-now',action='store_true');a=p.parse_args()
    require(re.fullmatch(r'[a-z][a-z0-9-]{0,30}',a.label) is not None,'label'); body=build(a.label); intent={'command':body,'command_sha256':hashlib.sha256(body.encode()).hexdigest(),'seconds':SECONDS,'retry':False,'physical_state':'unobserved','run_ready':False,'argv':['python3',str(ACCESS),'root','--persistent-only','--timeout','25','--command',body]}
    if not a.run: print(json.dumps(intent,indent=2)); return
    require(a.physical_black_now and a.screen_optimization_inactive_now,'current operator assertions'); raise RuntimeError('held for independent review; no command submitted')
if __name__=='__main__': main()
