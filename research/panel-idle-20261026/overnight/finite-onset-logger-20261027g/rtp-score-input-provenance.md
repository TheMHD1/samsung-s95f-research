# RTP score-input provenance: qualifying counts, not difference amplitude

Recorded 2026-10-27 UTC. This is a bounded offline analysis of the already
copied selected QD package and the retained accepted two-window read. It made
no TV, root, USB, controller, network, UI, reset, write, protection, storage,
return-guard, persistence, POFLG, or high-bank operation. It does not modify
any prior frozen evidence.

## Result

The six halfwords at CPU RAM `0x2000ba40 + 2*i` are per-category qualifying
sample **counts** for the current ordinary selector/unpacker invocation. They
are not packed pixel samples and are not sums of the printed `diff` values.

For category/mode `m` and `i=m-1`, the ordinary chain is:

```text
selector b7ec:
    s[0..5] = 0
    choose packed A and B sources

unpacker bd58:
    decode four 12-bit A/B lanes from each six-byte group
    helper bbbc computes diff = abs(A_lane - B_lane)
    qualifying helper paths call formatter c5d0 with category 1, 4, or 6

formatter c5d0, on an accepted path:
    if record_id[i] is within its bound:
        record_id[i] += 1               # u32 at 0x2000ba28 + 4*i
        publish low16(record_id[i])      # root +0x2490 or +0x2492
    # bound-exceeded path bypasses both preceding operations
    s[i] = uint16(s[i] + 1)             # exactly +1, never +diff

predicate 1e68:
    shift s[i] into a four-halfword history
    update q[i] from s[i] versus a root threshold
    on permitted q states, add a delayed history count to A[i]
    compare low16(A[i]) with fp
```

Thus the final event metric is a delayed, per-category aggregate of qualifying
lane-count values. It is more processed than “the current number of differing
samples,” and it is not a magnitude/amplitude integral. The actual unsigned
lane difference controls whether ordinary mode-1/mode-4 paths qualify and is
available to diagnostics, but no instruction in the accumulator body adds
that `diff` value to `A[i]`.

## Pinned image and corrected coordinates

The selected package is exactly 5 MiB with SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
For selected image 1, the corrected coordinate is:

```text
FILE = VA + 0x40200
```

The verifier pins these exact image-1 slices:

| Object | VA range | FILE range | SHA-256 |
| --- | --- | --- | --- |
| predicate/aggregate | `0x1e68..0x203f` | `0x42068..0x4223f` | `c3afd8863cf7f6d098fe7459ef91da9fd8827662041e77cd29497dccb2aae57a` |
| selector | `0xb7ec..0xb8a7` | `0x4b9ec..0x4baa7` | `78bbf2da87adaa7cc1c9c30cbed5381d079810c8d9e3809a1c0e6744cd6d8c07` |
| comparison helper | `0xbbbc..0xbd2d` | `0x4bdbc..0x4bf2d` | `9161e90f083f9e3f230c6e8d6f2b2f2503c7cbcd6c2ca1525e025f116a30dd71` |
| packed unpacker | `0xbd58..0xc02b` | `0x4bf58..0x4c22b` | `5d9924044096fbef1f5c14db5c289d60d465750ad5ea5be6ce479375542ffcb6` |
| formatter/count producer | `0xc5d0..0xc841` | `0x4c7d0..0x4ca41` | `51c6c80996f433f94b2774ae6b86ba61f1e95a306433b98aad6681256deb5827` |
| broad six-slot reset | `0xca84..0xcafb` | `0x4cc84..0x4ccfb` | `35f9ace204a351b9446e82f0fbab8cb6a6eb688f103a882ec2bf0d8f8e353795` |

RAM addresses receive no FILE bias.

## `s[]` reset and update are direct

At VA `0xb7f8..0xb80b`, before any of the three calls to unpacker `0xbd58`,
the selector executes this six-slot loop:

```text
b7f8  movs   r0,#0
b7fc  movs   r1,#0
b7fe  ldr    r2,[pc,#0x90]   ; literal b890 = 0x2000ba40
b800  strh.w r1,[r2,r0,lsl #1]
b804  adds   r0,#1
b806  uxtb   r0,r0
b808  cmp    r0,#6
b80a  blt    b7fc
```

The exact bytes are
`002005e00021244a22f81010411cc8b20628f7db`. Therefore each ordinary call
from the shared orchestrator at `0xb6fa` starts the six counts at zero before
packed data is analyzed.

The formatter update at VA `0xc708..0xc71b` is equally direct:

```text
c708  subs   r0,r4,#1             ; i = category - 1
c70a  ldr    r1,[pc,#0x180]       ; literal c88c = 0x2000ba40
c70c  ldrh.w r0,[r1,r0,lsl #1]    ; old s[i]
c710  adds   r0,#1
c712  uxth   r1,r0
c714  subs   r0,r4,#1
c716  ldr    r2,[pc,#0x174]       ; same literal
c718  strh.w r1,[r2,r0,lsl #1]    ; s[i] = old + 1
```

Its exact bytes are
`601e604931f81000401c81b2601e5d4a22f81010`. No `diff` register is read in
this update. The addition is one with 16-bit wrapping.

A broader initializer at VA `0xca84` also zeros six slots at each of these
bases:

```text
0x2000ba28  six u32 record IDs
0x2000ba40  six u16 s counts
0x2000d0e4  six u32 accumulators A
0x2000d0fc  six u16 q states
```

It then clears the associated history arrays. Its direct packaged callers are
`0xb964` and `0xcb50`. This wider reset is corroborative; the selector-local
reset already proves that `s[]` starts at zero immediately before ordinary
unpacking. The reset scopes differ: the selector resets only `s[]`, whereas
record IDs are cleared by the broader initializer and can span multiple
selector invocations in which `s[]` repeatedly restarts at zero.

## The apparent `0x2000ba40 + 8` pointer overlap is not real

An earlier retained report described the selector fallback as
`*(uint32_t *)0x2000ba40 + 8`, which would overlap `s[0]` and `s[1]`. The
selected bytes disprove that address resolution.

The adjacent selector literals are:

```text
b890  0x2000ba40   # s[] base, referenced by reset instruction b7fe
b894  0x20000494   # dynamic A pointer slot
b898  0x20000498   # dynamic B pointer slot
b8a0  0x20015000   # fixed A choice
b8a4  0x20015f10   # fixed A choice
```

The fallback at `0xb87a..0xb88d` is:

```text
b87e  ldr  r0,[pc,#0x18]       ; literal b898 -> 0x20000498
b880  ldr  r1,[r0]
b882  adds r1,#8               ; B = *(u32*)0x20000498 + 8
b884  ldr  r0,[pc,#0x0c]       ; literal b894 -> 0x20000494
b886  ldr  r0,[r0]
b888  adds r0,#8               ; A = *(u32*)0x20000494 + 8
b88a  bl   0xbd58
```

The exact local literal-reference census reinforces the correction: `b890` has only
the reset reference at `b7fe`; `b894` has references at `b812` and `b884`.
There is no pointer/count union at `0x2000ba40` in this path.
Across the whole selected image, raw word `0x20000494` also occurs at
`0x1c064`, while `0x20000498` occurs at `0xb7ac`, `0xb898`, `0xc5ac`, and
`0x1c1a4`. The verifier pins those full raw occurrence lists but interprets
only the selector-local loads resolved above. It does not claim that an
untraced indirect pointer could never reach the same RAM.

## From packed lane difference to a count

Unpacker `0xbd58` consumes six packed bytes at a time and reconstructs four
unsigned 12-bit lanes from each A and B source. It advances the logical lane
index by four and the packed byte offset by six at VA `0xbf98`:

```text
adds r4,#4
add.w r11,r11,#6
uxth.w r11,r0
```

For each lane, comparison helper `0xbbbc` computes unsigned absolute
difference. The two arithmetic arms are visible at `0xbc20..0xbc41`:

```text
if A < B: diff = uint16(B - A)
else:     diff = uint16(A - B)
```

Its four direct calls to formatter `0xc5d0` are at `0xbc74`, `0xbca8`,
`0xbcde`, and `0xbd1e`. They pass category values `4`, `6`, `1`, and `1`.
The ordinary routing is:

- flag halfword `0x200004aa == 1`: a direction-specific difference threshold
  is applied, and a qualifying lane is category 4;
- otherwise, flag `0x200004ac == 1`: the category-6 formatter path is used;
- otherwise, root state `+0x2410` and a direction-specific difference
  threshold select the category-1 paths.

This is the boundary between amplitude and count. `diff` participates in the
qualification and is passed to the detailed formatter, but the contribution
to `s[category-1]` is exactly one.

The 31 retained V6 lines are therefore not themselves the complete score
input. They are printed observations from qualifying formatter paths. Ring
capture limits and formatter gates can omit records, and categories have
separate counters.

## Three distinct quantities must not be conflated

| Quantity | Storage | Update | Role |
| --- | --- | --- | --- |
| lane `diff` | transient `uint16` | `abs(A_lane-B_lane)` | qualification and diagnostic value |
| record ID | six u32 at `0x2000ba28+4*i` | increment/publish only when its bound is not exceeded | printed sequence and root record-ID latch |
| `s[i]` | six u16 at `0x2000ba40+2*i` | increment by one on any path reaching `0xc708`, including the ID-bypass path | input count appended to predicate history |
| `A[i]` | six u32 at `0x2000d0e4+4*i` | add a delayed history count conditionally | final low-16 score compared with `fp` |

The printed first field comes from the record-ID table, not from `s[]`. The
formatter increments the u32 ID at VA `0xc6aa..0xc6b9`, then publishes its low
half as follows:

```text
category 1       -> R+0x2490
category 4 or 6  -> R+0x2492   # shared latch
```

Those stores are exact at `0xc6ca..0xc701`. They do not reveal which of modes
4 or 6 most recently wrote the shared `+0x2492` field.

Record IDs are not one-for-one proxies for `s[]`. VA `0xc604` branches on an
exceeded u32 record-ID bound to `0xc6de`, whose unconditional branch lands at
`0xc708`. That short path skips the ID increment and root-latch publication
but still increments `s[]`. Earlier rejected formatter paths can skip both.
Together with the different reset scopes, this explains why printed record
IDs and root ID latches cannot reconstruct the score input count exactly.

## How the count becomes the event score

Predicate `0x1e68` uses four separate state areas:

```text
0x2000d0fc  q[6]       uint16
0x2000d108  H[6][4]    four uint16 history entries per category
0x2000ba40  s[6]       current uint16 qualifying counts
0x2000d0e4  A[6]       uint32 aggregate/score
```

For the selected `i`, the exact ordinary transformation is:

```text
q[i] = (2*q[i]) & 0x1f

H[i].h0 = old H[i].h1
H[i].h1 = old H[i].h2
H[i].h2 = old H[i].h3
H[i].h3 = s[i]

if s[i] > uint16[R+0x24a0]:
    q[i] = uint16(q[i] + 1)
    uint16[R+0x24a2] = q[i]

if q[i] not in {8, 9, 10, 12, 24, 25}:
    A[i] = uint32(A[i] + H[i].h0)
    if A[i] >= T:
        A[i] = A[i] - T       # at most once in this invocation

r7 = low16(A[i])
```

Because history is shifted before the addition, `H[i].h0` is an older count,
not current `s[i]`. The q-state membership test may also suppress the
addition. Calling `r7` either “number of differing pixels” or “sum of
differences” would therefore be wrong. The narrow supported description is
“low 16 bits of a stateful, delayed aggregate of qualifying-lane counts.”

## Flags and the retained values

At the end of unpacker `0xbd58`, the direct predicate mode is selected by the
same two CPU halfword flags:

```text
0x200004aa == 1                 -> mode 4
else 0x200004ac == 1            -> mode 6
else                            -> mode 1
```

The accepted later two-window read returned these bus-window values:

```text
window +0x0f06  54   # static CPU interpretation: mode-6 r7 latch
window +0x0f08  44   # static CPU interpretation: non-mode-6 r7 latch
window +0x2490  41   # static CPU interpretation: mode-1 record-ID latch
window +0x2492  54   # static CPU interpretation: shared mode-4/mode-6 ID latch
fp candidates 200, 0, 0, 200, 40
```

The package mapper and prior same-boot observations support the CPU
`0x2001....` / bus `0x4701....` alias, but the read did not sample the core
tag. The raw facts remain window bytes; the `R+...` names below are the
conditional static interpretation, not a newly proved universal alias.

The value 41 at `+0x2490` is consistent with the retained maximum printed
NORMAL record ID 40 followed by an ID-updating formatter path. The read
occurred later, ID updates can be bypassed, and its reset scope differs from
`s[]`; numeric agreement is corroboration, not a reconstruction of the
score-input count or proof that no later mode-1 invocation occurred.

The two different fields that both contain 54 have no direct assignment
between them in this slice. `R+0x2492` is a record-ID latch shared by
categories 4 and 6; `R+0x0f06` is the low-half accumulator latch for mode 6.
Their equality does not prove event mode, common identity, or causation. The
V6 printed rows are labelled NORMAL/category 1, but the live flags were not
captured at the event tail, so the rows also do not prove which direct mode
call produced event 736.

Other changed fields reported at `+0x2494/+0x2496/+0x2498`, `+0x24c8/+0x24ca`,
and `+0x2442/+0x2464/+0x2466` have no direct store in this bounded ordinary
count-producer slice. This report does not assign meanings to them from
numeric coincidence or widen into their unrelated producers.

## No physical coordinate map is recovered

The software provenance recovers only representation coordinates:

- `x` is the logical 12-bit lane ordinal: four lanes per six packed bytes;
- `y` is an unchanged halfword loaded from CPU RAM `0x200004d0`;
- `RGB` is an unchanged halfword loaded from `0x200004d4`;
- A is selected from two fixed packed bases or a pointer at `0x20000494`;
- B comes from the pointer at `0x20000498`.

No instruction in the bounded selector/unpacker/helper/formatter chain maps
that ordinal and scalar to a physical panel column/row, applies a panel width,
crop, tile, orientation, or electrical-channel transform, or names the packed
sources physically. Consequently the captured labels `x=570..631` and
`y=2159` must remain firmware diagnostic values. Treating them as literal
screen coordinates would be an unsupported inference.

## Reproduction

`rtp-score-input-provenance.py` uses only Python's standard library. It pins
the selected package, corrected VA/FILE mapping, function slices, all four
literal occurrences for `0x2000ba40`, exact literal-reference sets, selector
reset, corrected dynamic pointers, comparison/helper calls, record-ID stores,
`s[]` increment, aggregate state, direct caller censuses, packed-loop stride,
and retained two-window values.

```sh
python3 rtp-score-input-provenance.py
python3 -O rtp-score-input-provenance.py
```

Both commands emit the same compact JSON conclusion and perform no external
operation.
