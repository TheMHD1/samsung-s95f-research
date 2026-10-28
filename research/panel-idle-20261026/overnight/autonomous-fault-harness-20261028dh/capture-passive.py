#!/usr/bin/env python3
"""Fixed read-only instrumentation discovery; no trace/event setting writes."""
import hashlib
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
ADAPTER = HERE.parent / 'swu-stream-root-20261028cp/root-with-margin.py'
if hashlib.sha256(ADAPTER.read_bytes()).hexdigest() != 'be9c5362fa40b52be2b824e6cc3e11013bdaafd44b1710f010bbccebac2bdc55':
    raise ValueError('adapter identity')
spec = importlib.util.spec_from_file_location('passive_root', ADAPTER)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
command = '''set -eu
echo BOOT
cat /proc/sys/kernel/random/boot_id
echo UPTIME
cat /proc/uptime
echo TRACE_RELEVANT
awk '/gpio:|irq:|raw_syscalls:|power:|drm:|tcon|pqe|frc|v4l2|video|display/ {print}' /sys/kernel/debug/tracing/available_events
echo TRACE_INSTANCES
if test -d /sys/kernel/debug/tracing/instances; then ls -ld /sys/kernel/debug/tracing/instances; else echo ABSENT; fi
echo READERS
for name in dlogutil vlogutil journalctl; do if command -v "$name"; then :; else echo ABSENT; fi; done
echo AVOC_PID
pidof avocd
echo IRQ_COUNTS
cat /proc/interrupts
echo UPTIME_END
cat /proc/uptime
'''
out = HERE / 'passive-capability-04.json'
if out.exists():
    raise ValueError('fresh output required')
text = module.root(command, {'schema': 'passive-capability-v1', 'calls': []}, out)
(HERE / 'passive-capability-04.txt').write_text(text)
print(text)
