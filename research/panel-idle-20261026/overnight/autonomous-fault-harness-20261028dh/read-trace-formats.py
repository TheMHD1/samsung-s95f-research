#!/usr/bin/env python3
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('passive', HERE / 'capture-passive.py')
# Import the adapter directly; don't re-execute the discovery entrypoint.
source = (HERE / 'capture-passive.py').read_text().split('command =', 1)[0]
namespace = {'__file__': str(HERE / 'capture-passive.py')}
exec(compile(source, str(HERE / 'capture-passive.py'), 'exec'), namespace)
command = '''set -eu
echo BOOT
cat /proc/sys/kernel/random/boot_id
for name in gpio/gpio_value gpio/gpio_direction irq/irq_handler_entry irq/irq_handler_exit raw_syscalls/sys_enter raw_syscalls/sys_exit power/suspend_resume; do echo FORMAT "$name"; cat /sys/kernel/debug/tracing/events/$name/format; done
echo CURRENT_GLOBAL
cat /sys/kernel/debug/tracing/tracing_on
cat /sys/kernel/debug/tracing/current_tracer
cat /sys/kernel/debug/tracing/events/enable
'''
text = namespace['module'].root(command, {'schema': 'trace-format-read-v1', 'calls': []}, HERE / 'trace-formats.json')
(HERE / 'trace-formats.txt').write_text(text)
print(text)
