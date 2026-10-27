#!/usr/bin/env python3
"""Read fixed backend paths including the control implementation already in AVOC maps."""
from pathlib import Path
import hashlib
import importlib.util

HERE = Path(__file__).resolve().parent
SOURCE = HERE/'read-pm-idle-format.py'
if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != '47262917994451714b3dbfb8f53d761c61232587f2e83b3303cd5ce94a1b28e9':
    raise ValueError('frozen acquisition helper changed')
spec = importlib.util.spec_from_file_location('fixed_hdmi_backend_versioned_metadata', SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.__doc__ = __doc__
module.DEST = HERE/'hdmi-backend-versioned-metadata-20261026'
module.COMMAND = '''set -eu
echo BOOT_START
boot=$(cat /proc/sys/kernel/random/boot_id)
echo "$boot"
test "$boot" = 00000000-0000-4000-8000-000000000000 || exit 61
echo TIME_START
date -u +%s
cat /proc/uptime
echo AVOC_IDENTITY
readlink -f /proc/706/exe
cat /proc/706/stat
echo AVOC_BACKEND_MAPS
awk '$NF ~ /libhdmi.*control-impl-sec[.]so/ { print }' /proc/706/maps
for p in /prd/usr/lib/libhdmi-input-control-impl-sec.so /prd/usr/lib/libhdmi-input-control-impl-sec.so.0.1 /prd/usr/lib/libhdmi-control-impl-sec.so /prd/usr/lib/libhdmi-control-impl-sec.so.0.1; do
  echo PATH_IDENTITY
  echo "$p"
  if test -L "$p"; then
    echo SYMLINK
    readlink "$p"
  elif test -f "$p"; then
    stat -c '%s %F %a %u' "$p"
    sha256sum "$p"
  elif test -e "$p"; then
    echo OTHER_TYPE
    stat -c '%F' "$p"
  else
    echo ABSENT
  fi
done
echo BOOT_END
cat /proc/sys/kernel/random/boot_id
echo TIME_END
date -u +%s
cat /proc/uptime
'''

if __name__ == '__main__':
    module.main()
