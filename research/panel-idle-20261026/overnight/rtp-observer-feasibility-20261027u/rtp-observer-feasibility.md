# Passive RTP event observer: feasibility and minimum finite design

Recorded 2026-10-27 UTC. This is an offline engineering assessment of the
retained V6 capture, ordinary scan-gating trace, selector and fault-context
reads, and mapped-view evidence. It performed no TV, network, USB, controller,
UI, reset, memory, threshold, protection, code, or storage operation. It does
not implement a target helper or protocol writer.

## Decision

A fixed, read-only USB recorder is practical and would materially improve the
next fault capture. It can bracket the persistent RT transition and retain the
last clean and first faulted samples of every qualified candidate field. It
**cannot guarantee the exact event-time compare tuple**. Live mode, selected
threshold source, threshold value, final `A32`, and live `r7` are not atomically
latched together.

The recommended next instrument is a **passive bounded snapshot recorder**,
not another armed ring-logger run. It makes no memory write. This matters:
while the existing ring helper is armed, a short or ambiguous USB read leaves
protocol phase unknown. The reviewed contract then forbids a new header,
including a logger-gate restore, so polling while armed could strand the
diagnostic gate at one. V6 avoided this by issuing no USB traffic during its
20-second hold.

The passive recorder gives a strong last-pre/first-post candidate tuple and a
host-monotonic onset interval. Its result remains a bounded sequential sample,
not the CPU registers at VA `0x202a`.

## Clean-start precondition

The first RT sample must be clean:

```text
R+0x2400 == 0
R+0x240a == 0
R+0x240e == 1
```

If it already contains the V6 stopped/faulted tuple `1 / 0x1001 / 0`, onset
was missed. Save the baseline and exit. Do not clear, reset, or change a
protection field. The currently preserved V6 state is therefore unsuitable
for a new onset run unless the controller returns naturally to a separately
qualified clean state.

## Fixed read windows

One native process should keep the validated USB FD/interface claim and use
only these hard-coded target-`0x101` reads:

| ID | bus address / bytes | exact header | retained fields |
| --- | --- | --- | --- |
| `M` | `0x470004a0 / 0x44` | `01010000a004004744000000` | `aa` at `+0x0a`, `ac` at `+0x0c`, alternate mirror at `+0x22`, companion at `+0x24`, scan byte at `+0x38`, root anchor at `+0x40` |
| `C` | `0x47000bc0 / 0x10` | `01010000c00b004710000000` | raw alternate-context candidate, including `bc7` at response `+7` |
| `H` | `0x4700d0e0 / 0x60` | `01010000e0d0004760000000` | six `A32` slots at `+4..+0x1b`, six `q` halfwords at `+0x1c..+0x27`, six four-halfword histories at `+0x28..+0x57` |
| `L` | `0x47010f00 / 0x40` | `01010000000f014740000000` | last `T` at response `+4`, mode-6 `r7` latch at `+6`, shared other-mode latch at `+8` |
| `R` | `0x47012400 / 0x100` | `010100000024014700010000` | stop at `+0`, logger gate at `+6`, fault at `+0x0a`, ordinary gate at `+0x0e`, five threshold candidates at `+0x30/+0x32/+0x40/+0xc0/+0xc4` |

Each header is `struct.pack('<III', 0x101, address, length)`. One read is one
exact 12-byte OUT followed by one exact-length IN. No retry, reset, write,
fallback geometry, or fresh header after uncertain phase is allowed.

### Qualification strength

- `M` is inside the decompressed image-1 allocation
  `0x20000000..0x200004f7`. Its accepted live response contained root pointer
  `0x20010000` at the same-response offset `+0x40`.
- `C` is inside the zero-filled allocation
  `0x200004f8..0x2000e19b`. A prior response matched three startup constants
  and the alternate mirror, but remains raw candidate bus evidence.
- `H` is also inside that allocation. The non-A mapper yields bus
  `0x4700d0e0`, and N captured the selected mapper code bytes exactly. No live
  core tag or same-response anchor exists in `H`, so its transport bytes are
  positive while CPU-field interpretation remains conditional.
- `L` and `R` are inside reproduced AP_RTP bus destinations
  `0x47010000..0x470123ff` and `0x47012400..0x470124ff`; both exact ranges have
  already been read live. Their CPU-root interpretation is still conditional
  on the non-A mapping.

Cross-window agreement may strengthen a candidate. It must not silently
promote `C` or `H` into a universal CPU alias.

## Smallest finite recording sequence

The minimum useful cycle reads `R` twice and every other window once:

```text
R-start -> M -> C -> H -> L -> R-end
```

The duplicate `R` is necessary. Without it, the event can occur at an unknown
point relative to the other reads. Timestamp immediately before and after
every bulk call with the native monotonic clock; one post-transfer `AtMs` is
not enough for a formal interval.

Use fixed limits:

```text
maximum observation       20 seconds
nominal cycle period       250 ms
maximum cycles             80
terminal post-fault cycles 1
automatic retries          0
memory writes              0
```

Stop on the first time/cycle limit, exact fault transition, transport/count or
identity error, or unexpected RT state.

1. Clean `R-start` and faulted `R-end` means the event occurred within that
   cycle's measured interval.
2. A preceding clean `R-end` followed by a faulted next `R-start` brackets the
   event between cycles.
3. After either case, complete exactly one fixed post-fault set `M,C,H,L,R`
   only while phase remains known-ready, then stop.
4. An initially faulted `R-start` is “onset missed”; it is not a pre-fault
   tuple.

Retain the preceding fully clean cycle and every raw completed response. One
six-read cycle is 756 response bytes; 80 cycles are 60,480 raw bytes before
timestamps. A fixed binary artifact below 96 KiB is sufficient and should be
fetched in bounded chunks after completion, rather than placed as base64 in a
64 KiB root response. Stdout should contain only a summary plus artifact
size/hash.

V6 shows a 250-ms nominal cadence is plausible, not guaranteed: its callback
header/IN timestamps were 59/63 ms and later small reads usually completed in
the same or adjacent millisecond. Each bulk call still has a 2-second timeout.
Actual before/after timestamps define the real cadence. A short/error/timeout
makes phase unknown and ends all vendor traffic. Because this design never
arms a gate, it has nothing to restore.

## What a transition capture can establish

It positively establishes the raw RT transition and monotonic bracket; the
last clean and first faulted five-window values; whether an `r7` latch changed;
all six `A32/q/history` candidates; and whether `aa/ac`, `bc7`, and threshold
fields appeared stable.

A strong, still-qualified candidate requires all of:

1. exactly one `r7` latch changes at the fault transition;
2. it equals the low half of exactly one post-update `A32` slot;
3. last-clean and first-fault `aa/ac` select that mode class;
4. `bc7` and the selected threshold are stable across the bracket;
5. the sampled values satisfy `r7 > fp`; and
6. the RT tuple changes to `1 / 0x1001 / 0`.

This can reject competing explanations. It remains sequential corroboration,
not an exact register trace.

## Exact versus approximate fields

The ordinary path stores an `r7` latch immediately before compare, then the
taken setter changes stop/fault fields. Since the stop gate suppresses later
ordinary scans, the first post-fault latch is a good event-left-operand
candidate. It is not event-exclusive: nonfault comparisons write it too,
equal consecutive values hide a write, and another writer is not globally
excluded.

- `aa/ac` may undergo frame/post-scan transitions after the predicate returns.
- `bc7` is callback-refreshed and its mirror update precedes the stop gate.
- `A32/q/history` can race the DMA read and have no event tag.
- thresholds are sampled configuration values; stability does not prove which
  branch loaded `fp`.
- USB never captures live `r4`, `fp`, or `r7`, and RAM does not retain the
  selected `fp` source ID.
- process monotonic time is not a controller-PC or physical-panel timestamp.

Thus snapshots cannot satisfy the stronger exact record
`(mode, fp_offset, fp_value, A32, r7)` by themselves.

## Effect of the new long-term stable V context

The new accepted `rt-context-once` read at uptime `124639.19` returns all 320
bytes byte-identical to the read at `117834.25`: fault `0x1001`, last `T=0`,
mode-6 latch `54`, other-mode latch `44`, and logger gate zero. The state is
therefore demonstrably stable across 6,804.94 seconds on the same boot.

This materially supports calling `0/54/44` retained state. It does not bridge
the approximately 1,927-second gap between V6 and the first 320-byte read, and
it does not select which latch belonged to the fault. Threshold bytes being
stable across the two late reads likewise does not prove their event-time
source branch.

### Could helper `0x1c0c8(mode,4)` recover the tuple now?

Potentially it can recover **mode**, but only after its pending ordinary trace
proves all of the following:

1. argument one selects a specific per-mode RAM slot;
2. argument two writes a retained code `4` to that slot;
3. that code is unique to the taken event path rather than ordinary frame or
   housekeeping calls;
4. no later call overwrites/clears the slot while the RT stop state remains;
5. the slot's allocated bus window is positively qualified; and
6. exactly one slot carries the retained event mark.

The immediate `4` must not be confused with predicate **mode 4**: it is the
helper's second argument, while mode is the first argument. Until destination
and lifecycle are proved, it is not a mode latch.

Even a proven retained mode does not always reconstruct the full tuple. For
mode 1 or 6, event-time `bc7` still selects between threshold sources, and the
late callback-refreshed byte is not a latch. For mode 4, `bc7` is irrelevant
and a unique helper mark plus a uniquely matching frozen `A32` slot and stable
`R+0x2440` would make the numeric reconstruction much stronger. It would
still need proof that neither the accumulator slot nor threshold changed in
the V6-to-first-read gap. The new 6,804.94-second equality proves later
retention, not that missing earlier interval.

Accordingly, helper-state and a future `H` read may narrow or sometimes
identify the mode without a code patch. They cannot yet be called a complete
event-time tuple. Incorporate the helper window only after its independent
trace supplies exact address, extent, stores, clears, and writer lifecycle;
do not guess a sixth read from the call arguments.

## Implementation boundary

An eventual helper may reuse the reviewed ARM32 usbfs preflight,
descriptor/FD checks, one-claim known-phase read engine, raw failure retention,
and fixed-file retrieval. It needs independent review for the polling machine
and new `H` range. Required properties are:

- zero-I/O default and hard-coded geometry;
- allocate all response/file buffers before USB open;
- no logger-gate, threshold, protection, code, firmware, or other write;
- unknown-before-call and ready-only-after-exact-count phase handling;
- no packet after ambiguity and no retry/reset;
- finite time/cycle/file bounds checked before every cycle; and
- preserve raw prior windows even if a later read fails.

This report does not authorize or provide a runnable implementation and does
not enter storage, bootloader, high-bank, POFLG, protection, or return-guard
branches.
