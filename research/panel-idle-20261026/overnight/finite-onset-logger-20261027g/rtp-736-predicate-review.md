# Independent review: RTP event 736 predicate and prospective context windows

Date: 2026-10-27 UTC  
Scope: offline review only; no TV, root, USB, network, UI, reset, or storage action

## Findings

### P1 — The predicate and field locations are supported by the selected bytes

No defect was found in the ordinary predicate trace pinned by
`rtp-736-predicate.md` SHA-256
`2ea99e5cf5e77ec25e0a82b685b090c9e66487dada4eccc0b0c749564af88348`
and `rtp-736-predicate.py` SHA-256
`a644c9ecbd2682840b4252d03fe8acc51bdf4a1278853a87b13cb81484acee78`.
Normal and optimized verifier runs produced identical accepted JSON.

Independent Thumb decoding confirms:

- the three direct encoded callers pass modes 4, 6, and 1 at VAs `0xbfbc`,
  `0xbfd0`, and `0xbfdc` respectively;
- `fp` is selected from exactly `R+0x2430`, `R+0x2432`, `R+0x2440`,
  `R+0x24c0`, or `R+0x24c4`, with the documented mode and context-byte
  branches;
- the gate is `uint16[R+0x249e] == 1`, followed by the documented wait;
- the tail loads the halfword at
  `0x2000d0e4 + 4*(mode-1)`, thereby taking the low 16 bits of the selected
  32-bit accumulator;
- mode 6 stores that value to `R+0x0f06`; every other mode stores it to
  `R+0x0f08`; and
- the calls using `(uint8(mode),4)` and event argument `0x2e0` occur only
  after `cmp r7,fp; ble`. Both registers contain zero-extended halfwords, so
  signed `ble` has the same ordering as a 16-bit unsigned comparison here.

This establishes the software predicate `r7 > fp`. It does not establish a
physical unit or the live mode during V6. The whole-image/body execution and
indirect-caller limitations in the source report remain necessary.

### P1 — The two bus ranges are bounded, but their CPU-RAM meaning remains conditional

The packaged AP_RTP table and loader independently reproduce these exact,
contiguous destination extents:

```text
0x47010000 + 0x2400 = 0x47010000..0x470123ff
0x47012400 + 0x0100 = 0x47012400..0x470124ff
```

Consequently, target-`0x101` reads at `0x47010f00` for 64 bytes and
`0x47012400` for 256 bytes remain wholly within those statically configured
windows. Their exact little-endian headers are:

```text
01010000000f014740000000
010100000024014700010000
```

The recovered mapper does map CPU `[0x20000000,0x20200000)` through
`+0x27000000` on its non-A branch, which arithmetically maps
`0x20010f00`/`0x20012400` to the proposed bus addresses. The live core-tag
register was not sampled. Therefore returned bytes must remain described as
window-side observations. A match with the predicted image-1 fields would
support, but not independently prove, the live alias or immutable executing
body.

### P1 — The older read plan is stale and should not be the execution authority

`fault-context-read-plan.md` SHA-256
`a2a1d644bfa379a399f4a2a750337a15f32fe20eafa326de19b9e13dd13aa02a`
still says that the predicate is pending, recommends one 64-byte read, and
ends with “no helper should be built” until that gate is resolved. The final
predicate instead justifies the separate 64-byte latch window plus the full
256-byte threshold/control window. The plan must be marked superseded or
updated before it is cited as live-execution authorization; otherwise the
record contains conflicting geometry and readiness requirements.

### P2 — A two-read result is not an atomic reconstruction of V6

The proposed reads are sequential. The firmware can update the latches and
root fields between them, and scans after V6 may already have replaced the
values that caused the retained event. The result can establish two bounded
samples and correlation with a still-latched fault; it cannot identify one
atomic mode/r7/fp tuple or prove UI/physical causality. The final helper must
stop after any short/error/unknown phase, send no retry or later header from
an unknown boundary, and retain the ordering/timestamps needed to expose
this limitation.

## Decision

The predicate/address derivation and proposed fixed geometry are clear for a
final source/build review. This review does not clear an unfinished helper or
a target execution. Clearance still requires immutable source/wrapper/build
pins, zero-I/O state-machine evidence, and resolution of the stale-plan
conflict above.
