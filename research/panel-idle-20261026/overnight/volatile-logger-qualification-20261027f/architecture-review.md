# Offline architecture review: finite secondary logger qualification

Recorded 2026-10-27 UTC. This report describes the offline build-review
phase only. No TV, USB node, controller, network endpoint, RAM location,
flash, EEPROM, firmware, threshold, protection setting, ring cursor or
availability flag was accessed or changed as part of that offline phase.
The subsequent accepted live qualification is documented separately in
[progress.md](progress.md) and [independent-runtime-review.md](independent-runtime-review.md).

## Result

The fixed helper is at `../managed-usb-secondary-logger-smoke`. It implements
the preferred arm-verified variant as one claimed-interface session and one
native invocation. It has no caller-selected target, address, length, payload,
hold duration, deadline, retry, reset, or follow-up action.

The build manifest SHA-256 is
`150189300d1fb78507e8dcad330cc1ca2ebbef05617d5741506a062986445b8b`.
The native source SHA-256 is
`abbfd7bbfafe11c4204934187600983379db1a93de9fde4fe9ac1fe3736a6991`,
the wrapper SHA-256 is
`eeb852c8e1b9a0d2611abc17e853ad2ee834f4e42712b2810bf8309eda5e59ca`,
and the release DLL SHA-256 is
`03296496c42c01453d05a02678ef7a79d121e5822ff17097f7f6ae8b34eea3b5`.
The local margin adapter SHA-256 is
`bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a`.

At this offline build-review phase the build had **not** been independently
approved or executed on the TV. The later independent clearance and actual
invocation are retained separately; this report is not the runtime result.

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
transport exception, clock exception while a payload/IN is pending, or
malformed result after a transaction starts enters `Unknown`.
Release and close are local cleanup and never repair protocol phase.

A managed allocation failure in the narrow interval after an exact header but
before creation/cloning of its data buffer is a separate safe-stop case. It can
retain `ExpectingReadIn` or `ExpectingWritePayload`, rather than relabeling the
state `Unknown`, but it is still non-Ready and therefore permits no later USB
request. The helper does not claim hard out-of-memory guarantees.

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

The ordinary native-operation monotonic deadline is 20 seconds. Before arm,
at least 18 seconds must remain. Each two-transfer transaction reserves both two-second
timeouts before its header. After an exact write header, the mandatory payload
is never skipped by a new deadline check. At a known ready boundary, the fixed
restore overrides an expired logical deadline and records a rejected
`DeadlineViolation`; it never overrides `Unknown`. Post-restore reads stop if
the ordinary native-operation budget is exhausted.

The wrapper uses a helper-local, hash-pinned transport adapter that imports the
unchanged reviewed root runner and reuses its response validation and record
format. It independently pins the root access client, preserves authenticated
`--persistent-only` access, allows 45 seconds remotely and 75 seconds on the
host, and retains the reviewed 8,192-byte command and 65,536-byte response
limits. It contains no retry or fallback. The target self-test must finish in
one root call before the wrapper issues a separate call containing exactly one
native `--execute`. Thus the 20-second ordinary window plus a worst-case
four-second urgent restore has explicit space inside the 45-second remote
envelope without sharing it with target self-tests; the remaining margin also
covers execute-process CLR startup, serialization, shell framing, and transport.
These are finite transport limits and operational margin, not a hard real-time
execution guarantee.

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
outcome. The zero-I/O target self-test runs in its own completed root call.
The execute call removes the private target stage only after its synchronous worker
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
