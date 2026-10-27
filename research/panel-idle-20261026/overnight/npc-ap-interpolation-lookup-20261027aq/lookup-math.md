# NPC_AP interpolation lookup math

Recorded 2026-10-27 UTC. This is a bounded offline analysis of selected
image-0 ordinary integer lookup code and stored `NPC_AP` table bytes. It made
no TV, root-agent, network, USB, device-node, debugger, UI, playback, or
configuration call. It contains no instrumentation, collector, probe, writer,
patch, reset, bypass, or continuation of the rejected recorder. Protection,
return-guard, persistence, storage, high-bank, and bootloader paths are outside
scope.

## Result

VA `0x19830` is a five-point, endpoint-clamped, piecewise-linear **integer**
lookup. It is called twice in VA `0x27b78`, once for selector zero and once for
selectors one through three. Both call sites pass the immediate count five.

The selected package's stored `NPC_AP` tables are:

```text
shared X at NPC_AP+0x4e0: [1024, 256, 128, 64, 32]
selector 0 Y at +0x4ea:  [1023,1023,512,256,64]
selector 1 Y at +0x520:  [32,32,32,32,32]
selector 2 Y at +0x52a:  [16,16,16,16,16]
selector 3 Y at +0x534:  [64,64,64,64,64]
```

The X table is strictly descending and has no duplicate coordinate. Selector
zero's Y table is nonincreasing and duplicates `1023` in its first two rows.
Selectors one through three are constant. Across the upstream input domain
`d=0..1024`, these stored tables give:

| Selector | Stored unforced output range | Unique outputs |
|---|---:|---:|
| 0 | 64..1023 | 225 |
| 1 | 32 | 1 |
| 2 | 16 | 1 |
| 3 | 64 | 1 |

Thus an unforced `k` bound of `16..1023` is proved **only if these stored table
values are the values used on the relevant runtime call**. The package bytes
do not prove loading or current RAM contents. The general AM conclusion is
unchanged: absent a live table identity, arbitrary u16 Y entries can produce
an unforced low-16 `k` above `1023`.

After this lookup, VA `0x27b78` can still force `k=1023` through either of the
two conditions already pinned by AM. Nothing here changes that override.

## Exact VA `0x19830` algorithm

The complete body VA `0x19830..0x19897` is 104 bytes, SHA-256
`2b9338f990c409e8848d43d1fd64c05b5eb9640ed12d762764c8f82c821572e3`.
It receives:

```text
r0 = x       (the caller's u16 lookup coordinate)
r1 = X       (u16 coordinate table)
r2 = Y       (u16 value table)
r3 = count   (five at both selected call sites)
```

Its exact control order is:

```text
if X[0] <= x:
    return Y[0]

if X[count-1] >= x:
    return Y[count-1]

for i = 1 .. count-1:
    if X[i] >= x:
        continue

    numerator32 = low32((x-X[i]) * (Y[i-1]-Y[i]))
    quotient = signed_divide_toward_zero(
                   signed32(numerator32),
                   X[i-1]-X[i])
    return low32(Y[i] + quotient)
```

The caller then applies `UXTH`, so `k` is the low 16 bits of the returned
word. This is integer truncation toward zero, not nearest rounding and not a
floating-point blend.

### Endpoint and tie order

- `x==X[0]` takes the first endpoint immediately and returns `Y[0]`.
- `x==X[count-1]` takes the last endpoint and returns `Y[count-1]`, unless the
  first-endpoint condition already won because the endpoint coordinates are
  equal.
- An interior `x==X[i]` does not stop at row `i`: the `X[i]>=x` branch skips
  it. The next strictly smaller coordinate forms the crossing pair and, in
  the no-overflow domain, yields `Y[i]` exactly.
- For a run of duplicate interior coordinates equal to `x`, all equal rows
  are skipped. The next lower crossing therefore selects the **last**
  duplicate's Y as its upper endpoint. The verifier pins a four-row duplicate
  fixture that returns the last duplicate's value.

### Zero-width handling

There is no explicit `denominator==0` test. Nevertheless, for any positive
count the division site itself cannot select a zero-width pair:

```text
all previously skipped rows satisfy X[i-1] >= x
the selected row satisfies                X[i]   < x
therefore                                 X[i-1] > X[i]
```

So `X[i-1]-X[i]` is positive at every reachable interior division, even if
the table contains duplicates or is globally unsorted. Duplicate coordinates
are resolved by the search order rather than divided across.

The function has no count-zero guard. It still reads `X[0]`; if that first
endpoint test does not return, its `count-1` endpoint access underflows the
index before the loop. That is not relevant to the two selected call sites,
which each execute `MOVS r3,#5`, but count zero is not modeled as a safe empty
table. Count one returns its sole Y for every x.

### Unsorted tables

The routine does not validate global ordering. For an unsorted table, its two
endpoint tests can return before inspecting an interior crossing. If neither
endpoint returns, it chooses the first row whose X is strictly less than x;
only that locally crossing pair is used. Consequently, ordinary monotonic
table interpolation requires an external ordering premise. The selected
stored X table satisfies the stronger strictly-descending premise.

## Arithmetic and non-overshoot boundary

For a selected crossing pair, define:

```text
alpha = (x-X[i]) / (X[i-1]-X[i])
```

The search proves `0 < alpha <= 1`. If the signed 32-bit multiplication does
not overflow, the integer expression is `Y[i]` plus the signed endpoint
difference scaled by alpha and truncated toward zero. It therefore stays
between `Y[i-1]` and `Y[i]`; this proves local non-overshoot. With strictly
descending coordinates, all endpoint clamps and all local segments together
give global non-overshoot within the table's Y range.

For the selected stored tables and every caller-reachable `d=0..1024`, the
largest absolute mathematical product is only `65,408`, far below signed
32-bit overflow. Therefore the stored selector-zero result is globally within
`64..1023`; the other selectors are their constant values. This is a positive
restricted proof, not a semantic or runtime-table claim.

For arbitrary u16 tables, the product can approach `2^32` and the ARM `MUL`
keeps only its low 32 bits before signed `SDIV`. The straightforward convex
expression then no longer describes the returned 32-bit word. The caller's
subsequent low-16 mask further changes the numeric interpretation. The
verifier includes an overflow fixture whose mathematical product is
`4,294,770,690`, whose signed wrapped product is `-196,606`, and whose raw
returned word is `0xfffffffd`. No broad convex/non-overshoot claim is made for
that overflow domain.

## Stored selector-zero mapping

For the selected stored selector-zero table, the exact unforced low-16 result
over `d=0..1024` is:

```text
d <= 32:
    k = 64

32 <= d <= 64:
    k = 64 + 6*(d-32)

64 <= d <= 128:
    k = 256 + 4*(d-64)

128 <= d <= 256:
    k = 512 + trunc((d-128)*511/128)

d >= 256:
    k = 1023
```

The overlapping endpoints agree. Representative pinned values are:

```text
d:  0  32  33  64  65  128 129 256 257 1024
k: 64  64  70 256 260  512 515 1023 1023 1023
```

The packed 1025-halfword selector-zero map has SHA-256
`4cdf124c57ff845ea7fdc807246ee7c2cd337a38f50171761d2bf3b4e08ed485`.
Selectors one, two, and three are respectively constant `32`, `16`, and `64`
for the complete domain.

## Relation to AM's upstream masking

AM established that VA `0x27b78` constructs the coordinate before this
lookup as:

```text
d = low16(trunc_u32(float32(abs(a-b) * 1024.0)))
if d > 1024:
    d = 0
```

The low-16 reduction occurs **before** the `d>1024` comparison. A large
converted difference can therefore wrap into `0..1024` and reach this lookup;
this report does not replace that input rule with an unmasked magnitude. Once
inside VA `0x19830`, the selected stored tables cover every possible post-cap
coordinate.

## Evidence and limits

Input package
`selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin` has
SHA-256 `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`;
image-0 linked VA is FILE minus `0x200`. The stored NPC_AP payload at FILE
`0x172600..0x172b3d` is 0x53e bytes, SHA-256
`3e9f4747fa26eeca6818944a6dae2fbba54f6ccc79d1ed6a4dc05434b5ad21b7`.
The last selector table ends exactly at that declared payload extent.

`verify-lookup-math.py` pins the package, corrected AF and reviewed AM inputs,
the complete lookup body and its three control slices, both direct call sites,
the count-five/table-pointer setup, the stored payload and all five table
slices, every `d=0..1024` stored-table output map, endpoint/tie/duplicate
fixtures, the positive-width invariant, selected-product bound, a signed
overflow boundary, count-zero refusal, and deliberate byte mutations. It uses
explicit `need()` checks, so optimized Python does not remove validation.

This proves selected-package integer arithmetic only. It does not establish
that the stored tables were loaded or remained unchanged at runtime, which
selector was active when retained `118` was written, current table contents,
units, ticks, cadence, timing, event causality, content class, brightness,
panel power, or a physical fault mechanism.
