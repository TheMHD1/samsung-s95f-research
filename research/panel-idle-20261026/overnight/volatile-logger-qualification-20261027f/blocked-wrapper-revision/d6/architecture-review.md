# Offline architecture review: finite secondary logger qualification

Recorded 2026-10-27 UTC. This directory contains offline build review only.
No TV, USB node, controller, network endpoint, RAM location, flash, EEPROM,
firmware, threshold, protection setting, ring cursor, or availability flag was
accessed or changed.

## Result

The fixed helper is at `../managed-usb-secondary-logger-smoke`. It implements
the preferred arm-verified variant as one claimed-interface session and one
native invocation. It has no caller-selected target, address, length, payload,
hold duration, deadline, retry, reset, or follow-up action.

The build manifest SHA-256 is
`6293e99052cac89be90b7d90a5654673106bcf5f16a853d0fd6ee3d02ba6f21b`.
The native source SHA-256 is
`abbfd7bbfafe11c4204934187600983379db1a93de9fde4fe9ac1fe3736a6991`,
the wrapper SHA-256 is
`d488ac74d5999f1633fd64600dab3b39bed1164d3ba2da2f158127a1a1f48e4a`,
and the release DLL SHA-256 is
`03296496c42c01453d05a02678ef7a79d121e5822ff17097f7f6ae8b34eea3b5`.

This build has **not** been approved for or executed on the TV. It must receive
independent review before any live invocation.

## Architecture difference from the fixed readers

The low-level boundary remains the reviewed ARM32 usbfs engine: boot and USB
identity preflight, cached descriptor pin, unbound vendor interface 2, FD
character-device identity validation, one claim, two-second bulk timeouts,
one release, and one close. The new code changes the orchestration from a
single fixed read to a finite transaction controller with four explicit
protocol phases:

| phase | permitted next action |
| --- | --- |
| `ReadyForHeader` | one fixed read or write header |
| `ExpectingWritePayload` | only the exact two-byte payload already selected |
| `ExpectingReadIn` | only the exact fixed-length IN already selected |
| `Unknown` | no further controller USB traffic |

Every exact write payload and exact read IN returns to `ReadyForHeader`.
Every short count, overcount, ioctl error, timeout, disconnect-shaped
exception, or malformed result after a transaction starts enters `Unknown`.
Release and close are local cleanup and never repair protocol phase.

Restoration is not sent from `finally`. It is attempted only when mutation may
have begun and the state machine positively records `ReadyForHeader`. This
preserves two distinct requirements: mandatory restoration after logic or
hold failure at a known boundary, and prohibition of a blind header after an
ambiguous transfer.

## Fixed sequence and interlocks

1. Read `0x45000580/64` and require the eight packaged callback words at
   offset `+0x0c`.
2. Read `0x20200000/0x3c0c`; preserve all bytes and require both cursors in
   `0..0x3c00` inclusive and the flag in `{0,1}`.
3. As the last controller read before arm, read `0x47012400/64` and require
   the complete halfword at `+6` to equal `0x0000`.
4. Send target `0x102` header `020100000624014702000000`, then payload
   `0100`, each once with exact counts.
5. Immediately read `0x47012400/64` and require the halfword to equal
   `0x0001`.
6. Hold exactly three seconds with no USB transaction. The arm deadline is ten
   seconds; the hold starts only with a full worst-case restore reserve.
7. At the known header-ready boundary send the same fixed write header and
   payload `0000`, then require a fixed readback of `0x0000`.
8. Only after verified restoration, read and preserve the full ring again.

The ordinary whole-operation monotonic deadline is 20 seconds, leaving four
seconds for an urgent fixed restore plus shell/cleanup margin. Before arm, at least 18
seconds must remain. Each two-transfer transaction reserves both two-second
timeouts before its header. After an exact write header, the mandatory payload
is never skipped by a new deadline check. At a known ready boundary, the fixed
restore overrides an expired logical deadline and records a rejected
`DeadlineViolation`; it never overrides `Unknown`. Post-restore reads stop if
the ordinary whole-operation budget is exhausted.

## Offline verification

The release build completed with zero warnings and zero errors. Seventy-four
zero-I/O tests passed: the retained 26 engine tests and 48 state-machine tests.
The latter include success `0 -> 1 -> 0`, callback/cursor/gate precondition
rejections, short counts and exceptions at all 16 possible bulk transfers,
known-boundary arm-read and hold failures that restore, ambiguous restore
failure that forbids verification, post-restore read failure, cleanup failure
variants, pre-arm budget exhaustion, time advancing between hold samples,
hold oversleep, a post-arm clock exception, and output-size enforcement.

The maximum success-shaped native JSON in the fake test is 45,119 bytes,
including both 15,372-byte ring snapshots. The wrapper accepts at most 55,000
bytes, extracts retained binary artifacts host-side, invokes the native helper
only once, and does not issue a second native call after a rejected or partial
outcome. It removes the private target stage only after the synchronous worker
completion marker is returned; an ambiguous transport leaves cleanup deferred.

## Limitations

The build does not prove target-`0x102` writeability, two-byte DMA atomicity,
absence of concurrent firmware togglers, stable full-ring data, or that an
exact USB OUT changed memory. Those are why readback is mandatory. If an
armed read becomes ambiguous, the protocol phase is unknown and restoration
is forbidden even though the volatile gate may remain changed.

An accepted run would qualify a finite logger transition and preserve ring
evidence. It would not establish a physical picture observation, panel fault
causality, a repair, or any safe persisted modification. Persisted-storage,
high-bank, and POFLG work is deliberately outside this helper.
