# `Pre-PD` companion consumers

Recorded 2026-10-27 UTC. This is a bounded offline trace of two complete
selected-image functions. It made no TV, network, root, USB, device-node,
firmware, UI, setting, protection, or storage operation. Image-0 coordinates
use `FILE = VA + 0x200`.

## Result

The 16 words rooted at fixed address `0x58410178` are used as an ordered
numeric boundary table by two ordinary calculations. The selected package's
stored sequence is:

```text
L[0..15] =
960, 768, 640, 512, 448, 384, 320, 256,
192, 160, 128, 96, 64, 36, 1, 0
```

This is a code-role statement: both consumers index these words while
reducing the adjacent `Pre-PD`-associated four-by-sixteen source. It does not
identify the boundaries as pixel, luma, RGB, voltage, brightness, or any
other physical unit.

The two functions use the companion differently:

- VA `0x10334` computes per-lane 32-bit prefix sums and maps the **first
  threshold crossing** to a descending capped output in `AP_SPC`.
- VA `0x19064` filters three source lanes, finds each lane's first maximum
  bin, and uses consecutive companion boundaries to choose either an
  external cap or the preceding boundary minus one before applying a common
  floating scale. It writes per-lane and final values in `NPC_AP`. The fourth
  source lane is copied to an unnamed context but does not enter this
  function's three-lane selection math.

The package's stored four-lane source is all zero, while its companion holds
the constants above. These are stored initializer bytes, not a live sample.
Neither current source nor current companion values were captured at the
same invocation, so the formulas do not by themselves reproduce W or V6.

## Shared inputs and exact fixed helpers

Define the live fixed-source words as `S[k][i]`, for lane `k=0..3` and word
`i=0..15`. Define the companion words as `L[i]`. Both complete consumers
load `S` from `0x584109a4` and `L` from `0x58410178`.

Both functions call byte-identical helpers at VAs `0x23510` and `0x19338`.
Each returns, for lane `k`:

```text
C[k] = max_u32(u32[0x584301f0 + 4*k],
               u32[0x584311f0 + 4*k])
```

The complete 44-byte helper, including both literals, has SHA-256
`1c1ef2774d5f516ebade2b709a8e341545a49b87306f9b3afbd92b2dabe1abd1`.
The two fixed arrays have no positive individual name or live capture in
this scope. `C[k]` is therefore an exact arithmetic input, not a claimed
physical limit.

## Consumer `0x10334`: first prefix crossing

The complete body `0x10334..0x10423` has SHA-256
`12d4d300b3402aab6bb23d31744b4bc9a1babb12698075c45fdd399c872c0dc2`.
It calls the selected getter for named RAM record `AP_SPC`, whose base is
`0x2000f7c2` and extent is `0x124`.

The routine assembles one unsigned 32-bit threshold:

```text
T = u16[AP_SPC+0x56] | (u16[AP_SPC+0x58] << 16)
```

For each source lane `k=0..2`, it calls the fixed helper above for `C[k]`,
then computes prefix sums using ordinary 32-bit wrapping additions:

```text
P[k,0] = S[k,0]
P[k,i] = (P[k,i-1] + S[k,i]) mod 2^32
```

Let `j` be the first index in `0..15` for which `P[k,j] >= T`. The exact
output is:

```text
if no such j:  O[k] = low16(L[15])
if j == 0:     O[k] = low16(min(C[k], 1023))
if j > 0:      O[k] = low16(min_u32(C[k], u32(L[j-1] - 1)))
```

It writes `O[0..2]` to `AP_SPC+0x5a`, `+0x5c`, and `+0x5e`.

Using the stored companion, the uncapped output ceiling for crossings
`j=0..15` is:

```text
1023, 959, 767, 639, 511, 447, 383, 319,
255, 191, 159, 127, 95, 63, 35, 0
```

Thus this consumer is precisely a first-prefix-crossing mapper. A later
crossing selects a lower numeric ceiling. That is useful behavioral
structure, but it supplies no physical meaning for either the source words
or the resulting halfwords.

Boundary details matter:

- `T=0` crosses at index zero even when every source word is zero.
- If positive `T` is never reached, stored `L[15]=0` makes the output zero.
- Prefix addition has no overflow check; a wrap can prevent a crossing that
  unbounded arithmetic would have reported.
- `C[k]` can lower every listed ceiling.
- Subtraction wraps modulo 2^32 and comparisons are unsigned. A live earlier
  boundary of zero would yield `0xffffffff` before the minimum, not negative
  one. The stored sequence avoids that underflow for the used preceding words.

## Consumer `0x19064`: filtered peak-bin mapper

The complete body `0x19064..0x1932f` has SHA-256
`d6e9d5f5d129583ba1b248b790c947558e6759bd49371ec3ebe7f9832bff842a`.
Its positive named RAM-record context is `NPC_AP`, base `0x2000d71c`, extent
`0x540`. Its separate getter returning `0x47010000` remains an unnamed
context root. The fourth-lane destinations
`0x47013adc..0x47013b18` are not relabelled as `AP_RTP` fields.

### Filtering and boundary construction

The function reads:

```text
N = min(u16[NPC_AP+0x45e], 16)
U = u32[NPC_AP+0x460]
```

For lanes `k=0..2`, it forms:

```text
V[k,i] = S[k,i]  if i <= N and S[k,i] <= U
         0        otherwise
```

It also constructs a 17-word boundary row for every lane:

```text
B[0] = 1024
B[i+1] = L[i], i=0..15
```

Independently, all 16 words of source lane 3 are copied to the unnamed
context range above. Lane 3 does not enter `V`, the peak search, or the final
lane choice in this body.

### Per-lane peak and mapping

For each lane, the function scans `V[k,0..15]` for its maximum. Within one
lane the comparison is strict, so the first equal maximum retains the bin
index. There is one terminal rule: at bin 15, a zero `B[16]` stops before
processing that bin. With stored `L[15]=0`, bin 15 is therefore excluded.

Let `M[k]` be the retained maximum and `j[k]` its bin. If `M[k]=0`, the
per-lane output `Q[k]` is zero. Otherwise the function selects:

```text
X[k] = C[k]          if B[j+1] <=u C[k] <u B[j]
       u32(B[j]-1)  otherwise
```

It calls VA `0x1ae9c` with three floating inputs and selector zero. That
helper returns three floating values, but `0x19064` copies only its first
return value into all three lane-factor slots. Call this common single-
precision value `F`. The stored halfword is the low 16 bits of:

```text
Q[k] = VCVT_U32_F32( f32(0.5 + f32(f32(X[k]) * F)) )
```

This notation intentionally preserves the selected floating conversion
rather than replacing it with a generic host-language `round`. The function
writes `Q[0..2]` to `NPC_AP+0x56`, `+0x58`, and `+0x5a`.
Here `<=u`/`<u` denote unsigned comparisons; fallback subtraction wraps before
the unsigned-to-float conversion. A zero live upper boundary can therefore
produce `0xffffffff`, even though the stored sequence avoids that case for
processed bins. The checker models finite, nonnegative, in-range conversion
fixtures using its host binary32 rounding. It rejects out-of-domain results;
it is not a complete ARM floating-point emulator. Live floating-point control
state, exceptional conversions and actual factor `F` have not been captured.

### Final conditional output

The source-peak lane selection uses `>=` across lanes, so a tie selects the
**last** equal lane. Let `p` be that lane. The final write to
`NPC_AP+0x150` is:

```text
if u16[NPC_AP+0x194] == 1:  final = Q[p]
otherwise:                  final = max(Q[0], Q[1], Q[2])
```

This distinction is material. With flag one, the lane having the largest
filtered source word wins even if another lane has a larger mapped output.
With every other flag value, the largest mapped output wins directly.

## What this sharpens—and what it does not

The companion is no longer merely a nearby descending constant list. Its
code role is exact:

- in `0x10334`, `L[j-1]-1` supplies a descending crossing ceiling;
- in `0x19064`, `[1024] + L` supplies adjacent peak-bin boundaries;
- stored terminal zero has concrete control-flow impact in both consumers.

A future synchronized observation could reproduce both functions from a
finite set of numeric inputs:

- live `S[0..3][0..15]` and live `L[0..15]`;
- `AP_SPC` threshold `T` and external caps `C[0..2]` for `0x10334`;
- `NPC_AP` index/value filters `N/U`, external caps `C[0..2]`, common factor
  `F`, and final-selection flag for `0x19064`.

The first unresolved edge remains the live producer and units of the
`Pre-PD`-associated source/companion and the two cap arrays. The stored source
is zero, W's mirrored sums are nonzero, and no same-invocation live source
capture exists. The formulas also do not prove that either output caused a
physical blackout. Content dependence remains testable, but terms such as
histogram, RGB, pixel, luma, luminance, or panel coordinate are not promoted
from numerical shape alone.

## Reproduction

`verify-companion-consumers.py` uses only Python's standard library. It pins
the selected package, accepted Y/AB inputs, complete `Pre-PD` metadata,
stored companion bytes, both complete consumer bodies, the byte-identical
cap helpers and fixed arrays, the three-float transform, named getters and
registry rows, and the unnamed `0x47010000` root. Its semantic fixtures cover
first/last/no crossing, cap clamping, 32-bit prefix wrap, in-boundary versus
fallback mapping, bin-15 exclusion, source filters, equal-bin and equal-lane
ties, unsigned subtraction underflow, fractional factors, host binary32
rounding and both final-output branches. Normal and optimized runs must emit
byte-identical JSON with `target_operations:0`.
