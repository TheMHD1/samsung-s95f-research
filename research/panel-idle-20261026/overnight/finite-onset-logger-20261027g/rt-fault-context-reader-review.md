# Independent review: fixed RT fault-context reader

Date: 2026-10-27 UTC  
Scope: offline source, build, wrapper, manifest, and test review only; no TV,
root, USB, network, UI, reset, or storage action

## Findings

### No open P0/P1 blocker in the final pinned candidate

The reviewed build is manifest SHA-256
`c64d77d8356fde3867490155095e1ef240151634f1c72a529a43970055f5aa7e`.
Its important pins are:

| artifact | SHA-256 |
| --- | --- |
| `Program.cs` | `f7418df841af9b616c198958b5b725dd7fc2434c92f5b360b65989c9da66b6a0` |
| managed DLL | `cd80eafa03fdcf9f3cc514434aef78ccd25228bb3b5cbe058d93dcb788e32127` |
| `run-once.py` | `93af800b0e4103a03d268680cb13b6ea6ed3c2d4ceeead79625f75b10b584c1a` |
| `test-wrapper.py` | `d3967809f381de17d79439071ab8dbb1f26b570df8cf6f5b9d4675faf9d66f8b` |

All 11 manifest rows independently match current file sizes and hashes. A
direct wrapper contract load accepts this exact manifest and returns only the
three pinned managed runtime artifacts for staging.

The native state machine sends only these fixed requests, in this order:

```text
target 0x101, address 0x47010f00, length 64
header 01010000000f014740000000

target 0x101, address 0x47012400, length 256
header 010100000024014700010000
```

Each is one exact 12-byte OUT request header followed by one exact IN. A
header call is entered only from `ReadyForHeader`; the phase becomes unknown
before the transfer; only an exact header advances to its expected IN; only
an exact IN returns to `ReadyForHeader`. Therefore no second header is sent
after a short, over-count, exception, or otherwise incomplete first request.
The catch path sends no vendor packet. Release and close are the only cleanup
attempts after failure. There is no retry, reset, memory-write operation,
caller-selected geometry, gate change, or firmware action.

The earlier one-window plan is explicitly superseded by
`fault-context-two-window-plan.md`. The two exact ranges are wholly contained
in the independently reproduced AP_RTP destinations
`0x47010000..0x470123ff` and `0x47012400..0x470124ff`.

### P2 — Failure accounting is conservative, and must remain so in audit

Before the active invocation, the final wrapper records one native invocation
and changes `target_operations` to null with status
`inflight_or_unknown`. It records exact two/status `accepted_exact` only
after exit zero, empty stderr, exact artifact hashes, all eight native steps,
final `ReadyForHeader`, release, and close validate. Thus an ambiguous or
rejected active call is no longer falsely reported as zero target activity.
It leaves the private stage and raw authenticated evidence intact; there is
no automatic retry or cleanup. That null/unknown state must not later be
normalized to zero without inspecting the retained native bytes.

The final envelope parser requires the metadata block at line zero, exactly
eight metadata lines, contiguous stdout/stderr blocks, and the completion
marker as the last line. Leading, interstitial, and trailing noise cases are
covered by explicit rejection tests.

### P2 — The samples remain sequential and alias-conditional

Successful execution would return two bounded bus-window samples, not one
atomic event-time snapshot. Firmware may update a latch between the reads or
after V6. The recovered non-A mapper gives the expected CPU-`0x2001...` to
bus-`0x4701...` arithmetic, but the live core tag was not sampled. Results
must first be reported as window bytes; interpreting `+0x0f06/+0x0f08` as
the image-1 `r7` latches, or the five second-window fields as the live `fp`
candidates, remains conditional. Neither a match nor a mismatch alone proves
physical-panel causality or a repair.

## Test evidence

Independent read-only reruns passed:

- native fake-operation suite: 34 tests, zero target operations;
- wrapper suite: 30 tests normally and the same 30 under `python3 -O`;
- direct manifest contract load: 11 valid rows, exactly three stage files;
- local default invocation: dry fixed geometry;
- local active invocation: refused before I/O on the non-ARM32 host.

The native tests cover every transfer's negative, zero, short, over-count,
and exception results and forbid later traffic. The wrapper tests use explicit
checks that remain active under `-O`, validate all native steps and hashes,
retain framed failure output, reject malformed envelopes, and pin the dry
geometry and adapter.

## Decision

This exact final build is clear for one bounded, read-only two-request
capture, provided the pinned boot/device preflight still passes and the root
caller supplies the reviewed manifest SHA. Any other hash, boot, geometry,
short transfer, unknown phase, rejected native outcome, or ambiguous host
transport is a stop condition with no new controller request and no retry.
