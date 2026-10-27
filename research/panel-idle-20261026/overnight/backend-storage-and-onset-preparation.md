# Live backend, corrected storage route, and onset-capture preparation

This phase makes diagnostic progress; it deploys no repair. The latest owner
size correction is **no larger than a thumb**. Both closeups were reopened:
the irregular lower-edge patch and upward narrow dark line are visible, but
there is no calibrated scale or independent one-pixel-width measurement.
The uploads do not establish present physical emission or observer availability.

## Resolved live diagnosis backend

The [reviewed 44-byte capture](factory-backend-runtime.md) at 14:58:02–14:58:03 UTC
binds the running TIFS diagnosis import, wrapper table, implementation callback,
singleton and method GOT. PID 1085/start 1203, boot, executable/library source
hashes and maps match throughout. This closes the previous live-provider
pairing gap. The capture calls no factory function and cannot exclude
concurrent daemon activity. It does not execute or validate a factory write.
Seven host-only fixtures pass, including short-read retention and lifecycle,
hash, map and range rejection. Independent review decoded the saved raw bytes.

## Storage and disable-scope corrections

The [corrected getter/storage audit](../tcon-research/factory-off-sensing-storage-readback.md)
uses the actual 32-byte FactoryIndexFile tuple, not the separate 0x164-byte UI
record. UID 0x506e has type 2, length 1 and base offset 0x1860, selecting
PrdNvramMap::ReadFactoryArea. The corresponding PRD setter takes its NVRAM
write arm and computes a possibly-zero storage-index adjustment. The prior type 1
volatile-vconf interpretation was rejected before any live getter/setter or
setting change in this phase. The separate FC and PRD classes are not equated:
newly acquired, hash-checked NVRAM/EEPROM libraries show their static routes
converging on the same named `/dev/eeprom` interface. Both use read request
`0x80044906` and write request `0x40044905`. The getter's logical offset is
translated by `+0x3e00` to driver-request offset `0x5660`; this is not a proven
physical-media address. The live factory backend-table selection, driver
persistence/notification behavior and exact rollback remain unresolved.
Absence of the named definition key does not establish absence of the actual
storage record. No setting was changed.

The [disable-route audit](../tcon-research/off-sensing-disable-route-coverage.md)
proves a narrower value 6 effect: the eligible ordinary classifier skips its
new off-sensing warning state. Existing countdowns, reinforcement, manual,
standby and EL routes are not thereby globally disabled. This is not yet a
usable permanent-maintenance-disable procedure or a sparse-menu repair.

## Real logging and resource contracts

Installed vlog help and a real unfiltered 2-second dump establish the timestamp
grammar and observed 6,327-record/936,079-stdout-byte load. See the
[format/coverage contract](vlog-capture-contract.md). Footer timestamps are
not producer-event timestamps; retained first/last records and interior loss
matter. The query itself took about 2.84 seconds to finish.

The environment capture records installed bash/gzip and point-in-time /tmp,
memory and CPU headroom. A child-only ulimit probe then measured 1,024 bytes per
file-limit unit through /proc/self/limits. No file was written by that probe,
and no parent shell limit or TV setting changed. Thus 131,072 units means 128 MiB
on this TV, rather than 64 MiB. Trace buffers also need per-CPU total accounting.

## Observer is not deployed

The first combined-observer draft passed 15 offline tests but failed semantic
review: it could overstate physical eligibility and coverage, had incomplete
process cleanup, and miscounted resources. These failures and required fixes
are retained in [onset-capture-review.md](onset-capture-review.md). Passing
fixture tests did not clear it for a live run. The implementer is correcting
the new tool while a separate reviewer checks its contracts. A second draft's
21 passing tests also missed the actual controller timeout and serial-gate
cancellation contract. These were caught before execution; its blocking
acquisition architecture is being replaced with an owned detached collector
and bounded control/status requests.

No observer smoke or physical-trigger test has run in this phase. No remote
key, factory write, notification deletion, active QD getter, display/power
control, service restart, kernel/firmware patch or execution-policy change ran.
Physical recovery, prevention, permanent root and the permanent blackout fix
remain unverified. The existing OS boot and software activity are not proof
that the OLED is currently emitting light.

The [phase manifest](backend-storage-onset-evidence-manifest.json) freezes the
reviewed backend/storage evidence, raw observations and documentation. It
explicitly excludes the observer source/tests while they are being rewritten;
it does not certify those drafts. The preceding48-file snapshot remains
unchanged, with subsequent documentation/acquisition drift listed explicitly.
