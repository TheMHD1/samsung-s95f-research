# RTP ordinary mode-selector provenance

Recorded 2026-10-27 UTC. This is an offline trace of the selected image-1
package, reset scatter output, and retained V6 artifacts. It made no TV,
root, USB, controller, network, UI, threshold, protection, persistence, or
storage operation. The scope is the ordinary orchestrator, packed-input scan,
and their initialization paths; it excludes persistence, high-bank/POFLG,
return-guard, and protection branches.

## Result

Three values that previously looked like one “mode” are distinct:

1. CPU halfwords `0x200004aa` and `0x200004ac` select the mode code used by
   the status text, detailed-row wrapper, and final event-736 predicate.
2. CPU byte `0x20000bc7` does **not** select that mode. For predicate modes 1
   and 6, it selects which root-relative threshold supplies `fp`.
3. Root halfword `R+0x2410`, even when numerically equal to 4, is not the
   final predicate's mode-4 selector. It gates the scan and selects ordinary
   per-row mode-1 comparison routes.

Consequently, `R+0x2410=4` can coexist naturally with rows printed as
`m:NORMAL`. A final predicate mode 4 instead requires
`uint16[0x200004aa] == 1` at the unpacker tail.

Within the selected unpacker body VA `0xbd58..0xc040`, there is no direct
store to `0x200004aa`, `0x200004ac`, or context byte `+0x6c7`. The flags are
reread by each comparison helper and again at the final predicate tail; they
are not snapshotted once. Thus ordinary unpacker code cannot itself change a
NORMAL row into a different final predicate mode. An interrupt, external
writer, or other asynchronous execution could still change a reread value
between the last row and the tail. The retained log has no PC trace or
event-time selector snapshot to exclude that possibility.

## Reset and ordinary initialization

The selected package is 5 MiB, SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
For image 1, stored FILE offset equals linked VA plus `0x40200`.

Replaying the exact image-1 scatter stream produces the established
`0x4f8`-byte RAM prefix with SHA-256
`76bebfc83f8e286d8ae152749a1aa376d0bc8d3f415f2433d9ca6944506e7ef8`.
It gives both selector halfwords an initial value of zero:

```text
uint16[0x200004aa] = 0
uint16[0x200004ac] = 0
```

Normal application entry independently calls VA `0xc220` from VA `0x1ba7e`.
The exact stores are:

```text
c234  movs  r0,#0
c236  ldr   r1,=0x200004a2
c238  strh  r0,[r1]
c23a  ldr   r1,=0x200004aa
c23c  strh  r0,[r1]
c23e  ldr   r1,=0x200004ac
c240  strh  r0,[r1]
```

Thus both mode-selector halfwords are reset-derived zero and explicitly
zeroed again by the ordinary startup call. Runtime code must change them for
mode 4 or 6 to be selected.

The final scatter record zero-fills
`0x200004f8..0x2000e19b`. Fixed context byte `0x20000bc7` is inside that
range, so its reset value is also zero. This is a stronger default provenance
than merely observing a zero in a packaged configuration table.

Image-1 root `R=0x20010000` is pointed to by reset slot `0x200004e0`, but the
image-1 scatter table does not initialize that root allocation. Therefore no
image-1 reset value for `R+0x2410` is established here. The separate image-0
AP_RTP payload and later `0x47012400` bus reads contain value 4 at window
offset `+0x2410`; treating that as image-1 `R+0x2410` remains conditional on
the cross-address-space relation.

## Direct ordinary state machine for `0x200004aa/ac`

The complete aligned literal census in selected image 1 is finite:

```text
0x200004aa literals: b7cc b9b0 bb10 bd50 c030 c248
0x200004ac literals: b7d0 b9d0 bb2c bd54 c040 c24c
```

Within the ordinary bodies in scope, these literals resolve the following
direct stores.

| function/site | condition | direct store |
| --- | --- | --- |
| startup `0xc23c` / `0xc240` | application initialization | `aa=0`, `ac=0` |
| orchestrator `0xb784` | caller `r4==0` and `aa==1` after the scan | `aa=3` |
| orchestrator `0xb792` | caller `r4==0` and `ac==1` after the scan | `ac=3` |
| status `0xba7a` | `aa==3` before mode text selection | `aa=1` |
| status `0xba88` | `ac==3` before mode text selection | `ac=1` |
| frame function `0xb940` | `aa==1` and `uint16[0x200004a0]==1` | `aa=2` |
| frame function `0xb95c` | `ac==1` and `uint16[0x200004a0]==1` | `ac=2` |

This yields explicit ordinary transitions `1→3`, `3→1`, and `1→2`, plus
startup `→0`. It does not establish a closed global state machine: a computed
writer, interrupt source outside the bounded bodies, boot ROM, corruption, or
external agent is not excluded. Within the aligned literal-reference set,
however, there is no other direct store and no unconditional ordinary
`0→1` transition.

The relevant ordering within one uninterrupted orchestrator invocation is:

```text
b6ce  optional status function b9f4
      (converts any direct state 3 to 1, then prints mode)
b6de..b6f0  test scan request / aa / ac
b6fa  call dispatcher and packed unpacker
b72e  optional frame function (later than the scan)
b74a..b794  post-scan state transitions, including 1 -> 3
```

There is no `aa/ac` store between the status call and the scan call in this
ordinary linear path. The frame and post-scan transitions occur only after
the packed scan and its final event predicate have returned.

## Mode selection at the three consumers

### Status line

VA `0xb9f4` performs any `3→1` transition first, then selects the printed
status mode at `0xba8c..0xbaa4`:

```text
if ac == 1: code 6 -> "IO"
else if aa == 1: code 4 -> "ONSEN"
else: code 1 -> "NORMAL"
```

The status priority is therefore `ac`, then `aa`. If both equal one, it prints
IO/code 6.

### Detailed rows

The comparison helper VA `0xbbbc` computes one lane's unsigned absolute
difference and rereads the same selector halfwords:

```text
bc4a: if aa == 1, the qualifying formatter call uses mode 4
bc80: else if ac == 1, the formatter call uses mode 6
bcb2..bd1e: otherwise R+0x2410 and difference gates may call mode 1
```

For the last branch, `R+0x2410==4` is one positive route to a mode-1
formatter call when the difference exceeds its selected comparison value.
Values 1 or 3 provide another mode-1 route. This is why the numeric root field
4 is compatible with a row literally printed `m:NORMAL`: the formatter gets
code 1, not the root field value.

### Final event-736 predicate

The unpacker tail independently rereads the flags:

```text
bfae: if aa == 1, call predicate 1e68 with mode 4
bfc2: else if ac == 1, call it with mode 6
bfd6: otherwise call it with mode 1
```

Its priority is `aa`, then `ac`, unlike the status function. If both equal
one, status would print IO/code 6 while the final predicate would receive
mode 4. No retained evidence shows both were one during V6; the difference is
reported because a printed status label alone is not a universal selector
snapshot.

## Provenance of alternate-threshold byte `0x20000bc7`

VA `0x38f4` returns fixed context base `0x20000500`, so byte `+0x6c7` is CPU
address `0x20000bc7`. The only exact `STRB ... #0x6c7` encoding in selected
image 1 is in function VA `0x3934`:

```text
393e  call 38e8                    ; source-context pointer
3944  call 38f4                    ; fixed 0x20000500 context
394e  ldrb r0,[source_context,#0x3d8]
3952  strb r0,[fixed_context,#0x6c7]
```

The only direct `BL` to `0x3934` is VA `0x18c96`, the start of the ordinary
registered callback at `0x18c94`. Thus this byte is a runtime mirror of
`source_context+0x3d8`, refreshed when that callback runs; it is not derived
from `aa`, `ac`, or `R+0x2410`.

The dispatcher reads it at `0xb83a/0xb862`; the packed scan reads it while
choosing setup thresholds at `0xbdc2/0xbdf4`; and the event-736 predicate
reads it at `0x1e98/0x1ec4/0x1edc`. The predicate uses it only to select:

```text
mode 1: R+0x24c4 when nonzero, otherwise R+0x2430
mode 6: R+0x24c4 when nonzero, otherwise R+0x24c0
```

Mode 2 and mode 4 threshold sources do not depend on this byte. There is no
direct `+0x6c7` store in VA `0xbd58..0xc040` or `0x1e68..0x2040`. As with
`aa/ac`, an asynchronous callback could change it between separate reads,
but the unpacker/predicate body does not change it internally.

## Can NORMAL rows and a different predicate mode coexist?

There are three answers at different evidence strengths.

1. **`R+0x2410=4` plus NORMAL rows: yes, directly.** The difference wrapper
   explicitly maps that root condition to formatter mode 1 when `aa/ac` are
   not one and the difference gate passes. The root value 4 is not a mode-4
   code at the final predicate.
2. **One uninterrupted unpacker with no asynchronous writer: no internal
   transition.** The comparison helper and final tail reread `aa/ac`, but no
   direct store to either exists anywhere in the unpacker/callee bodies in
   scope. NORMAL detailed rows therefore remain consistent with predicate
   mode 1 under this execution model.
3. **Retained text alone: a different tail mode is not impossible.** Because
   the flags are reread rather than snapshotted, an interrupt or unbounded
   writer could change a flag after the last emitted NORMAL row and before
   `0xbfae`. Detailed logging can also be gated, so absence of a differently
   labelled later row is not a selector snapshot. V6 did not log the flags at
   the tail.

The V6 sequence `[RTP:NORMAL][395]`, 31 NORMAL detailed rows, and paired
`rtp_act_736` is strongly consistent with one ordinary mode-1 scan. It is not
an instruction trace proving that no interrupt occurred. The event-time
record proposed in `rtp-observable-vs-latched-plan.md` remains the smallest
way to close that gap.

## Bounded conclusion

The numeric value 4 at `+0x2410` should no longer be described as proof of
predicate mode 4. Predicate mode 4 is selected by `0x200004aa==1`; predicate
mode 6 by `aa!=1 && 0x200004ac==1`; otherwise it is mode 1. The alternate-fp
byte `0x20000bc7` is an independently refreshed context mirror and affects
threshold source, not mode.

Reset and startup establish zero defaults for all three CPU selectors. The
ordinary package contains finite state transitions for `aa/ac`, but none
inside the packed unpacker itself. These facts narrow mode provenance without
changing a threshold, selector, root field, or protection behavior.

## Reproduction

`rtp-mode-selection-provenance.py` pins the selected package and corrected
image mapping, replays reset decompression, checks zero defaults, exact direct
literal occurrences, writer slices, direct-call census, selector-copy store,
unpacker/tail bodies, V6 NORMAL/event sequence, and the late window-side
`+0x2410=4`. It uses only Python's standard library and performs no external
operation:

```sh
python3 rtp-mode-selection-provenance.py
python3 -O rtp-mode-selection-provenance.py
```
