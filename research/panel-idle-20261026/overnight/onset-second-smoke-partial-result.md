# Command-string smoke: real data acquired, qualification failed

The second separate five-second unobserved smoke used frozen observer
`ed257ee5f53fbddb65e755766f31fe0650a237093e7285b2613315ca305f45d4`
and tests
`0ad774ba45ca142d93ed2c76be75bd90a11e80c115e84e49aa0b77ba32dd3535`.
Its exact source/tests/four shell variants are archived in
`onset-review-archives/ed257ee5f53fbddb-0ad774ba45ca/`.
Independent review cleared this revision for one bounded smoke after 28
offline fixtures passed. No automatic retry occurred.

**Result: incomplete and unclassified. It is not a physical blackout capture,
recovery or prevention test.** The command-string launch works on the actual
TV without changing execution policy. It produced seven sidecars, preserved
as `partial-*` in [smoke-20261026t1625b.onset](smoke-20261026t1625b.onset/).
All seven retained lengths and SHA-256 values match the collector manifest.

## Actual interval and integrity

Host start/finish: 16:22:32.009–16:23:16.472 UTC. This includes staging,
scheduled lead, capture, transfer and cleanup; it is not a 44-second physical
test. TV trace markers delimit uptime 53375.33–53380.44, about 5.11 seconds.
Fork/other trace records begin earlier in setup, so the retained ring spans
about 12.686 seconds in total.

The saved metadata validates source/script hashes, AVOC PID706/start603,
Deviced PID675/start560, boot, before/end maps, pointer chains, FD/TID checks
and private trace settings. The boot remains
`00000000-0000-4000-8000-000000000000`. These are non-atomic process/source
checks and do not measure OLED emission or live kernel instruction bytes.

| Retained artifact | Bytes | Bounded finding |
| --- | ---: | --- |
| Trace | 6,696,262 | 66,185 retained/written rows; no ring loss in this short run |
| Metadata | 480,681 | Identity, source, map, pointer and configuration checks pass offline |
| Samples | 599 | Only two monitor rows and one QD/Deviced row; insufficient |
| Sample stderr | 3,599 | All 47 dd operations report full successful reads, 524 bytes total |
| Vlog | 4,693,966 | 31,011 timestamped records; endpoint/order/gap check passes |
| Artifacts | 4,433 | Diagnostic output retained; not emitted-light proof |
| FD/TID inventory | 2,170 | Selected process descriptors/lifecycle checked |

Vlog timestamps span 53373.001–53382.997, maximum observed inter-record gap
0.010 seconds, natural exit0 and no forced termination. This is a coverage
check; it does not prove generic log-message absence or lossless internals.

## Concrete defects exposed by the TV run

1. **Sampler performance:** monitor samples occur at 53375.34 and 53379.56,
   a 4.22-second gap; only one QD/Deviced row exists. Repeated Bash scans of
   approximately 1,300 map entries per memory read consume the window. The
   same shell generates 17,648 in-window broad syscall rows. Replace those
   scans with an exact prevalidated `(PID,address,word-count)` allowlist while
   retaining source, pointer, lifecycle, decoded-length and dd checks.
2. **Actual marker grammar:** the two exact marker rows use event token
   `0xffffffc01017095c`, not `tracing_mark_write`. Only an exact marker body,
   consistent token, recorded collector PID/TGID, order and matching clock
   anchors may qualify; arbitrary marker-like payloads must not qualify.
3. **Idempotent cleanup:** normal completion removes the private instance,
   then the EXIT trap writes to its now-missing tracing_on/events paths.
   Redirection order leaks two errors totaling243 bytes. The strict transport
   guard correctly rejects them. Guard instance existence and place stderr
   redirection before potentially failing output redirection.
4. **Long-window capacity:** 66,185 rows fit in this short run; that does not
   prove an 85–90-second ring will fit. Most load is unrelated/self-generated
   syscall54 activity. A scoped AVOC filter is valid only with the reviewed
   PRE/START/ARM/END equality, filter readback and whole-armed-interval
   fork/exit rejection. Any unresolved lifecycle or overflow stays incomplete.

The reviewer normalized only the two marker tokens in memory as a diagnostic
check; the raw file remains unchanged. The remainder then passes trace syntax/
accounting checks, including 36,632 in-window rows and 2,163 AVOC ioctl pairs.
This diagnostic normalization does not turn the failed run into an accepted
capture or fix the insufficient sample coverage.

## What the partial data says about the TV

Both 152-byte monitor samples have error counters0/0/0, retry history2/0/0,
history latch `qd_tcon_off=1`, `si_ok_count=4`, `ip_status_count=7` and
`fault_occurred=0`. They are two snapshots separated by4.22 seconds: they do
not exclude an intervening transition or establish present electrical health.

The existing offline I2C decoder reports 12 structurally complete transfers,
no orphan results, and n=ret=2 throughout. Its `semantic_capture_complete`
field applies to its I2C decoding only, not the whole observer or physical
state. Two stock AVEMonDIM power-query sequences return raw1; a stock sp-kpi
thread issues four other reads whose payload meanings are not assigned here.
The decoder has no observed mute/frame-mode/maintenance/dimming focus entries
in this finite retained interval. That is not a global command-absence claim
and the physical picture was unobserved.

Derived output: `smoke-20261026t1625b.onset/offline-partial-qd.json`, generated
from the untouched trace with `decode-qd-trace.py`. It never sends TV traffic
and cannot prove MCU acceptance or emitted light.

## Cleanup, status and next action

Authenticated quiesce and cleanup both exit0 without stderr. Cleanup's exact
output is `0\nCLEAN\n`, with explicit private instance/directory/expiry-log
absence checks. The collector remains `accepted=false`,
`technical_capture_complete=false`, `diagnostic_eligible=false`, physical
state unobserved, and `absence_claim_supported=false`.

No display/factory/sensing/power setting, firmware or execution-policy change
ran. The next candidate must fix these measured defects, receive its own
archive/review, and pass a new bounded smoke before a full owner-observed
transition is attempted. The underlying blackout fault remains unidentified.
