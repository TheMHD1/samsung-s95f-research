# RTP ordinary predicate: observable, latched, and missing event-time state

Recorded 2026-10-27 UTC. This is an offline interpretation and logging-design
note based on the frozen V6 capture, `rtp-incident-record-format.md`,
`rtp-736-predicate.md`, and the later accepted two-window read. It made no TV,
root, network, USB, controller, UI, firmware, threshold, protection, storage,
or persistence operation. It proposes no firmware patch or bypass. The scope
is only numeric provenance and what a future ordinary volatile diagnostic
would have to observe.

## Bottom line

The selected packaged ordinary path has one exact final predicate:

```text
m    = selected mode
i    = m - 1
A32  = uint32[0x2000d0e4 + 4*i]
r7   = low16(A32)
fp   = selected uint16 threshold

event argument 0x2e0 is issued iff r7 > fp
```

V6 observed two `rtp_act_736` lines and the matching `0x1001` fault-field
transition during one finite logger interval. That is strong evidence that
the numeric event tail ran. V6 did **not** retain `m`, the selected threshold
source, `fp`, `A32`, or `r7` at that instant. The 31 detailed rows before the
event cannot reconstruct those missing values.

The minimum self-identifying event-time record is:

```text
mode, selected_fp_offset, selected_fp_value, full_A32, low16_A32
```

`low16_A32` is arithmetically redundant but is a useful direct check against
the actual compare operand. The record belongs on the taken edge after VA
`0x202c` and before either call at `0x2032`/`0x203a`. It must precede the two
`rtp_act_736` strings in the same volatile ring. This is a design boundary,
not an implemented modification.

## What the ordinary numeric predicate proves

The selected package proves the following local dataflow.

1. VA `0x1e68` selects `fp` from one of five root-relative halfwords.
2. After a mode-indexed state/history update, VA `0x2012` loads the low
   halfword of `A32` from `0x2000d0e4 + 4*(m-1)` into `r7`.
3. VA `0x2020` stores `r7` at `R+0x0f06` for mode 6; VA `0x2028` stores it at
   `R+0x0f08` for every other mode.
4. VA `0x202a` compares the zero-extended halfwords `r7` and `fp`; VA
   `0x202c` exits on `r7 <= fp`.
5. On the taken edge, VA `0x2032` calls helper `0x1c0c8(mode,4)`, then VA
   `0x2036` loads literal `0x2e0` and VA `0x203a` calls the common setter.
6. That setter writes `0x1001` and formats the decimal argument twice as
   `rtp_act_736`.

Because both compare operands are in `0..65535`, the encoded signed `ble` and
an unsigned halfword `<=` give the same result on this path. This proves the
ordinary **numeric** condition. It does not give 736 an enum meaning, assign
electrical or physical units to `A32/fp`, prove which panel condition produced
the values, or prove that the event caused the physical picture to disappear.
No physical picture state was recorded for V6, and complete identity of every
executing controller byte remains unproved.

## Why the captured row `diff` values cannot recover `r7`

The detailed rows and the final predicate operate on different values.

| item | exact provenance | role |
| --- | --- | --- |
| row `x` | logical index of one unpacked 12-bit lane | formatter only; not passed to VA `0x1e68` |
| row `c` | unsigned 12-bit lane from packed source B | formatter/comparison helper; not passed to VA `0x1e68` |
| row `diff` | `abs(A_lane-B_lane)` for that one lane | formatter/comparison helper; not passed to VA `0x1e68` |
| row first `%3d` | `uint32[0x2000ba28+4*(mode-1)]` | separate record counter |
| status 395 | pre-increment `uint16[0x200004a0]` | separate scan/status counter |
| predicate `r7` | `low16(uint32[0x2000d0e4+4*(mode-1)])` | final operand compared to `fp` |

The unpacker tail passes only the common `y` and `RGB` scalars to VA
`0x1e68`; it does not pass the last row's `x`, `c`, `diff`, or record number.
Inside the predicate routine, even `y` and `RGB` are used only by the optional
`BPFLG` text. They do not enter the accumulator arithmetic.

The accumulator also has hidden history. Before the compare, the routine:

```text
q[i] = (2*q[i]) & 0x1f
shift H[i], inserting s[i]
optionally increment q[i]
conditionally add H[i].h0 to A[i]
obtain T from c8a0/ca10
conditionally subtract T once
```

Neither the initial `A[i]`, `q[i]`, four-halfword history `H[i]`, source
`s[i]`, selected `T`, nor the update/subtraction decisions are in the V6 row
text. Detailed logging can also be gated while row counters continue. Thus
the same 31 emitted rows are compatible with multiple accumulator states and
different `r7` results. Conversely, a large row `diff` is not the value
compared at VA `0x202a`. Selecting the largest captured `diff`, averaging the
rows, or comparing a row directly with a candidate `fp` has no support in the
recovered dataflow.

## What is latched, and why a late read is not event-time evidence

The later accepted read in `fault-context-after-v6` returned these separate
bus windows at target `0x101`:

```text
uptime                         117834.25
0x47010f04                     0
0x47010f06                     54
0x47010f08                     44

0x4701240a                     0x1001
0x47012430 / +2432 / +2440     200 / 0 / 0
0x470124c0 / +24c4             200 / 40
0x4701249e / +24a0 / +24a2     1 / 160 / 0
0x470124d2 / +24d6             1 / 10
```

The retained `context.bin` is 64 bytes with SHA-256
`0683bb72c1bb998774ba4747987ec82ac938ce892ede62d877b9a1da641f2439`;
the 256-byte `rt.bin` has SHA-256
`91055b0ce0f0b798a78313bd90520506f63261fa1c35d78a0de85b2d332379f9`.
The accepted result explicitly reports no bus-content alteration and no
physical-picture observation.

This was about 1,926.8 seconds after V6 ended at uptime `115907.45`. The
context and RT reads were sequential, not atomic. More importantly, on an
invocation that reaches the calculator, its ordinary caller writes
`+0x0f06` or `+0x0f08` before it tests the predicate. Those are last-seen
per-mode-class values, not event-exclusive latches. `+0x0f04` is similarly
the latest `T` stored by the calculator. This does **not** prove that these
fields keep updating after the fault. In the direct ordinary call chain
`0x4446 -> 0xc250 -> 0xb644 -> 0xb7ec -> 0xbd58 -> 0x1e68`, VA
`0xc25e..0xc27a` makes `d8=0` when `R+0x2400 != 0` or `R+0x240e != 1`, VA
`0xc2e0..0xc2e6` passes that value, and VA `0xb6a6/0xb6a8` skips the
status/unpacker/frame branch when the saved value is zero. Alternate-selector
and mirror refreshes occur separately before that gate if `0xc250` itself is
invoked. Thus a late `+0x0f04/+0x0f06/+0x0f08` sample may be stale from the
last qualifying scan, may reflect a later qualifying invocation, or may have
another unexcluded writer; it is not a continuously refreshed post-fault
measurement.

The late values therefore preserve all of these live possibilities rather
than selecting a convenient one:

- `54` is the later window value at the mode-6 latch offset; `44` is the
  later value at the shared non-mode-6 latch offset.
- Candidate later window thresholds include `0`, `40`, and `200`, selected by
  mode and, for modes 1/6, the event-time context byte.
- Some cross-combinations satisfy `r7>fp` and others do not. That is exactly
  why mixing a convenient zero/40 threshold with one later latch does not
  recover the V6 comparison.
- The mode-selection CPU fields `0x200004aa/0x200004ac` and context selector
  byte `0x20000bc7` were not in either read.

Finally, image-1 CPU addresses `0x20010f..`/`0x200124..` and the sampled
`0x47010f..`/`0x470124..` bus windows remain separate address-space facts.
The recovered mapper and runtime correlations support the alias hypothesis,
but the late bus bytes must not be relabelled as certain CPU values at the V6
event instant.

## Minimum event-time record

### Required semantic fields

One record emitted only on the taken `r7>fp` edge should contain:

| field | width | exact source | why required |
| --- | ---: | --- | --- |
| `mode` | 1 byte | live `r4` at VA `0x202a` | selects accumulator slot and latch class |
| `fp_offset` | 2 bytes | source ID carried from the actual threshold-load branch | distinguishes `2430/2432/2440/24c0/24c4`, even when values are equal |
| `fp_value` | 2 bytes | live zero-extended `fp` register | exact right operand at VA `0x202a` |
| `A32` | 4 bytes | `uint32[0x2000d0e4+4*(mode-1)]` immediately after its update | preserves the full aggregate, not only its low half |
| `r7` | 2 bytes | live zero-extended `r7` register | exact left operand; must equal `low16(A32)` |

`r7` can be derived from `A32`, so the irreducible semantic tuple is
`(mode, fp_offset, fp_value, A32)`. Retaining `r7` costs one halfword and
detects a bad slot selection, race, or formatter argument error. A ring
sequence number is useful for transport diagnostics but is not required to
evaluate the predicate when the record immediately precedes the paired event
strings.

The source offset must be captured from the branch that actually loaded
`fp`; rereading `0x20000bc7` at the tail is weaker because that byte could
change after selection. The qualified load sites are:

| branch | threshold load / transfer site | `fp_offset` |
| --- | ---: | ---: |
| mode 1, selector nonzero | `0x1ea2`, moved to `fp` at `0x1eac` | `0x24c4` |
| mode 1, selector zero | `0x1eaa`, moved at `0x1eac` | `0x2430` |
| mode 2 | direct `fp` load at `0x1eb4` | `0x2432` |
| mode 4 | direct `fp` load at `0x1ebe` | `0x2440` |
| mode 6, selector nonzero | `0x1ece`, moved at `0x1ed8` | `0x24c4` |
| mode 6, selector zero | `0x1ed6`, moved at `0x1ed8` | `0x24c0` |
| fallback, selector nonzero | `0x1ee6`, moved at `0x1ef0` | `0x24c4` |
| fallback, selector zero | `0x1eee`, moved at `0x1ef0` | `0x2430` |

This table describes what a future observation must preserve. It does not
authorize modifying those instructions.

### Exact emission boundary

The strongest ordering point is the taken edge of VA `0x202c`, before VA
`0x202e` prepares arguments for helper `0x1c0c8` and before VA `0x203a`
enters the common event setter. At that point:

- `r4`, `r7`, and `fp` are the exact compare inputs;
- the selected `A32` has already been updated and, if applicable, reduced;
- the `R+0x0f06/0x0f08` store has already occurred; and
- no event-736 setter call has yet occurred.

A valid volatile trace would consequently order one predicate record directly
before the two existing `rtp_act_736` records. Any future implementation would
have to preserve all live registers and existing control flow, remain behind
the existing finite logger gate, and be independently reviewed. This report
does not implement it.

## Optional causal extension, not part of the minimum

If the goal changes from identifying the comparison to explaining how `A32`
was updated, append the following ordinary fields in a second-tier record:

| field | qualified source/site | diagnostic value |
| --- | --- | --- |
| final `q[i]` | `0x2000d0fc+2*i`; stores at `0x1f2c` and optionally `0x1f92` | shows membership-gate input |
| inserted `s[i]` | `0x2000ba40+2*i`; history store at `0x1f6e` | current source halfword |
| addend `H[i].h0` | `0x2000d108+8*i`; loaded at `0x1fca` | value added when update is allowed |
| `T` | return of `c8a0/ca10`; latches at `R+0x0f04` via stores `0xc9fe`/`0xca70` | conditional subtraction value |
| final `A32` | stores at `0x1fd4` and, after subtraction, `0x200a` | full post-update aggregate |
| BP threshold | `uint16[R+0x24a0]` | explains the optional q increment decision with `s[i]` |

The existing `BPFLG :q (y / rgb)` line is insufficient because it is emitted
only when `s[i] > R+0x24a0`; it carries neither mode, selected `fp`, nor
`A32/r7`. V6 contains no `BPFLG` line in its retained interval. The causal
extension should not be confused with the minimal event proof and does not
justify changing any of these values.

## Decision boundary

The late two-window read is useful current state, especially because it
preserves both `r7` latch offsets and every candidate window threshold. It
cannot retroactively select the V6 mode or comparison. Per-row `diff` is also
not a substitute for the aggregate. Only an event-time record containing the
actual mode, threshold source/value, and accumulator/compare operand would
close that provenance gap.

Such a record would still be a software observation. It would not establish
physical blackout timing, panel current, a safe threshold, or permission to
disable protection. This plan deliberately stops at the ordinary numeric
predicate and volatile diagnostic boundary.
