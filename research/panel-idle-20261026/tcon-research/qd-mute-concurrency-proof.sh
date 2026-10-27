#!/usr/bin/env bash
# Offline, stdout-only proof extractor for qd-mute-concurrency.md.
set -euo pipefail

base=${1:-${S95F_EVIDENCE_ROOT}/panel-idle-20261026}
module="$base/binaries/qdf_tcon.ko"
expected=97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63

actual=$(sha256sum "$module" | awk '{print $1}')
test "$actual" = "$expected"
printf 'module SHA-256: %s\n' "$actual"
readelf -sW "$module" | rg 'm_mute_state|frc_comm_mutex|tcon_comm_mutex|frc_tcon_mutex'
for span in 0xbbd0:0xbfb0 0x9bc8:0x9ca8 0x104f0:0x10788 0xcdf0:0xd070 0x16480:0x16540; do
  start=${span%:*}
  stop=${span#*:}
  aarch64-linux-gnu-objdump -dr --start-address="$start" --stop-address="$stop" "$module"
done
