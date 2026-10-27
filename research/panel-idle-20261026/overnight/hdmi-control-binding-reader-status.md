# HDMI control backend binding reader: prepared, not run

This proposed finite read-only `/proc/706/mem` observation has never run on
the TV. Execution is held pending complete offline failure-case and
raw-result validation. No display action or persistent instrumentation is
running from this candidate.

## Purpose and exact static derivation

A live pointer sample could distinguish the statically constructed control
backend table from the table actually installed in AVOC. It would not identify
physical picture state, a blackout trigger, or successful panel operation.

The copied main ELF's Thumb getter loads literal `0x2214a` at VA
`0x47e613ac`, adds Thumb PC `0x47e613aa`, then adds eight. The returned
storage VA is `0x47e834fc`; its `+4` field is the table pointer. The first
word is an initialization flag, not a pointer to follow. Independent review
checked this arithmetic. The copied implementation's DPMS callback Thumb
symbol is `0x8575`; a fresh offset-zero executable mapping supplies its bias.
The historical map `0xf503c000` would imply callback `0xf5044575`, but the
candidate derives the mapping anew.

## Implemented candidate guards

The [default-dry reader](read-hdmi-control-binding.py) pins the two local ELF
hashes and the fixed acquisition helper. Its command is below 8192 bytes.
It uses no callback, getter, setter, ioctl, process stop/attach, injection,
key, or display action.

The working source checks boot, AVOC PID/start tick/executable, remote file
hashes, unique offset-zero executable maps, map device/inode against `stat`,
and source-specific storage/getter/callback ranges. Each word read requires
exactly four octets. It includes matching main-getter and callback entry
words. Two sequential snapshots compare the flag, table pointer, exact odd
callback pointer and two instruction words. Selected maps, bases and source
identities are checked again. Concurrent changes away and back remain
possible; this is not atomic or a whole-live-code hash.

## Corrected offline contract; independent clearance still required

Initial independent review held the reader because storage was only
generically readable, mapped-file identity was insufficiently bound to the
copied file, full-command failure fixtures were absent, and remote `dd`
stderr accounting lacked a result-validator contract. A second review found
that an early parser also looked for remote `dd` diagnostics in the host
stderr sidecar, rejected the helper's real result schema, trusted an intent's
self-hash instead of the reviewed command, and accepted non-finite uptime.

The corrected offline contract now pins reader SHA-256
`84d60b3d066dd03fb4911e1a233014c70f553ac17dba427883ef8e2d235fa889`,
command SHA-256
`f840067004cb1080f63fa9fbd1a2eb192ce2a739e587f35ceadecaad819a765a`,
and root-client SHA-256
`3a92e02003ce51d2faeace231191f6f0c73731f2bfca9caa196e05b195b439a5`.
It requires the exact persistent-only argv, no retry, unobserved state,
authenticated root framing, unchanged-system-files assertion, exact intent
and result fields, valid ordered UTC timestamps, finite monotonic uptime and
wall-clock spans no greater than 26 seconds, and the installed stock `dd`
four-byte summary grammar in the embedded remote stderr. The host stderr
sidecar must be empty.

The response validator independently reconstructs source device encoding,
requires every retained source mapping to match device/inode, binds each bias
to one offset-zero executable source mapping, checks readable 32-bit map
ranges and source-specific storage/getter/callback coverage, requires the
implementation's exact `0x100` publication flag, and accounts for exactly ten
four-byte reads. Full-command fixtures now cover source-path and readability
failures, callback execution/range failures, table boundary/readability,
malformed and duplicate maps, endpoint change, PID/start/executable/hash/
device identity, and read failures. The fixture refuses unknown `/proc`
fallbacks. Response fixtures independently mutate transport authority,
identity, source mappings, ranges, values, time bounds and `dd` accounting.

These corrections remain **offline and not self-clearing**. An independent
review of the final exact bytes is still required before one finite target
sample. No automatic retry, physical-state inference, callback invocation, or
panel conclusion is authorized.

[Eight local helper shell tests](read-hdmi-control-binding-tests.py) pass.
They cover little-endian words including UINT32_MAX, truncated/excess reads,
pipeline failure despite four output bytes, malformed/unreadable maps,
map-end boundaries, invalid/unaligned ranges, and conditional contexts that
suppress shell `errexit`. These do not constitute full-command/result-parser
validation. Default-dry generation and shell syntax checks also pass.
