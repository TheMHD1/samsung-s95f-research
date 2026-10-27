# Current two-window retained-statistic read plan

This supersedes the initial one-window planning note. The native predicate trace and independent Thumb review now identify the retained latch offsets and all candidate root-relative thresholds. The owner authorizes unattended diagnostic commands. No physical observation or firmware modification is part of this read.

## Geometry frozen before execution

Exactly two vendor memory reads, in order:

| Target | Bus window | Bytes | Fixed header |
| --- | --- | ---: | --- |
|0x101|0x47010f00|64|01010000000f014740000000|
|0x101|0x47012400|256|010100000024014700010000|

The first includes offsets+4/+6/+8 corresponding to root-relative latest subtractor and mode-dependent accumulator latches. The second includes all five potential fp fields at relative+2430,+2432,+2440,+24c0,+24c4 and gates+249e,+24a0,+24a2,+24d2,+24d6. Existing V6 prefix already held200 at window-relative+2430. The package mapper has the non-A arithmetic CPU2001→bus4701, but the live core tag and whole-object alias are not sampled. Values must be reported first as bus-window contents; interpretation as exact image-1 fields is conditional. These reads cannot reconstruct the event-time CPU global mode/alternate-selector/accumulator histories.

The independent AP_RTP loader reproduction establishes full contiguous destination extents47010000+2400 and47012400+100. Both read ranges are inside those allocated/configured windows. No unqualified CPU-global, peripheral, high-bank or storage range is included.

## State and action boundary

The last controller USB run V6 ended with16exact transfers, restored loggergate0 and ReadyForHeader, verified release/close and private-stage removal. Since then only one ordinary stock I2C status query, one GPIO input request, cached Linux reads and six-file UI-stage cleanup occurred; no further vendor request or reset was sent. The same boot and active cached device identity must pass the new helper's preflight. Current hoststatus0x10/pin1 is preserved; the read does not clear or reset it.

Build and review `../managed-usb-rt-fault-context-read` offline first, pinned to the exact fixed geometry, known native engine and current root adapter. Target execution is synchronous with bounded I/O, exactly one OUT/IN pair per read, no retry or compensating command. An incomplete first transaction forbids the second. Phase-unknown execution stops with no new vendor header or cleanup. Interface/FD cleanup is attempted by the known engine. Exact private-stage cleanup is permitted only after a parsed, validated complete known terminal result and saved raw output. The helper contains no gate/settings/threshold/protection/firmware write, reset, signal or UI action.

The windows are sequential, not atomic. The controller may have updated statistics since V6. A matching high latch is corroboration of the late state, not proof of which fp/mode was selected at the event instant. Preserve all raw values even when zero, unexpected or incompatible; never silently select a threshold to force the hypothesis.
