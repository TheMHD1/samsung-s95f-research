# NPC_AP floating-input provenance

Recorded 2026-10-27 UTC. This is a bounded, offline trace of the ordinary
inputs passed at selected image-0 VA `0x136d0` to dispatcher VA `0x180e4`.
It made no TV, network, root-agent, USB, device-node, controller, UI, or
configuration call. It does not inspect VA `0x2f5a8` and does not enter a
protection, return-guard, high-bank, storage, bootloader, persistence, or
bypass path.

## Result

There is a positive but conditional arithmetic path from the received
`F3:0x128` low-ten-bit field `NPC_AP+0xa6` into the floating inputs of the
two ordinary routines that can write `NPC_AP+0x16/+0x18/+0x1a`.

The path is:

```text
received F3:0x128 low ten bits -> NPC_AP+0xa6
  -> 0x188d8 duty multiplication
  -> 0x18410 three-way min
  -> 0x184c8 three-way scaling/conditional comparison
  -> saved s0/s1/s2 at outer 0x13628..0x13630
  -> dispatcher 0x180e4
  -> conditional call to 0x1a748 or 0x1aa20
  -> NPC_AP+0x16/+0x18/+0x1a
```

This is a real direct data-flow join, not merely a shared object or nearby
field. It is not an unconditional value relation: minima, scale factors,
dispatcher controls, and writer-local decisions can mask, replace, or zero
the duty-dependent input. It also does not establish a physical unit, a
current runtime value, a hardware-output action, or a cause of the panel
fault.

The source edge is independently byte-pinned here rather than inherited
only from prose. The selector-`0x128` entry/table slice VA
`0x2c71c..0x2c7b1` selects displacement `0x4e2`, resolving to leaf VA
`0x2cc96`. That leaf masks the received scalar in `r4` to ten bits and stores
the halfword through the `NPC_AP` base in `r5` at offset `+0xa6`. Its entry
gates remain real: a received transport request does not prove this leaf ran.

The earlier four-lane source/companion outputs at
`NPC_AP+0x56/+0x58/+0x5a` do **not** directly feed the saved triple used by
this same invocation. The outer routine computes and stores the triple
first, calls VA `0x18b20` (which calls source consumer VA `0x19064`) second,
and later reloads the original three stack values at `0x136c4..0x136cc`.
The nominal-image direct-call census finds VA `0x18b44` as the sole direct
caller of `0x19064`. Dispatcher `0x180e4` does not directly read
`+0x56/+0x58/+0x5a`. This is a bounded direct-flow result, not a
whole-firmware independence claim: computed calls and the intervening call's
changes to other shared state remain outside that negative statement.

## Exact `0x136d0` call interface

Immediately before the sole direct call to VA `0x180e4`, the enclosing body
sets:

```text
r0 = r5 = u32[0x20000e38]
r1 = r6 = u32[0x20000e3c]
s0,s1,s2 = the three values returned by VA 0x18984 and retained at sp+8/+c/+10
s3 = the value returned by VA 0xd254
```

### `r5/r6`: one pre-increment 64-bit numeric pair

VA `0x38b14` loads the adjacent words at CPU addresses `0x20000e38` and
`0x20000e3c` with one `ldm`, returning them in `r0/r1`. The enclosing body
calls that getter at `0x134a4`, retains the pair in `r5/r6`, and passes the
same pair at `0x136d0`.

After the dispatcher and later ordinary calls, VA `0x1373c` calls the sole
direct increment routine VA `0x390a4`. That routine loads the same two words,
adds one with carry, and stores the pair back. The image's exact byte census
finds the `0x20000e38` literal only at getter literal VA `0x38b1c` and
increment literal VA `0x390b8`.

Consequently the dispatcher sees the retained pair from before this
enclosing pass's increment. The proved updater advances the 64-bit numeric
pair by one; this bounded trace does not exclude a reset or another writer
elsewhere, so it does not claim global monotonicity. No seconds, frames,
scans, ticks, or other unit is recovered. Other passed/computed aliases are
outside the exact-word census.

## `s0..s2`: exact duty-dependent chain

At the call to VA `0x18984`, `r0` is the halfword at the caller's `sp+0x24`.
VA `0x243ac` received that address at `0x1360a` and writes the halfword at
its VA `0x24776`. `r1` is the word at caller `sp+0x20`: the earlier sole call
to VA `0x24838` passed `sp+0x20` as its first output address, and
`0x248e8..0x248ec` copies `u32[0x200006c4]` there. The float input is the
return retained from the earlier VA `0x188a4` call. These are numeric source
edges only; this report does not assign units to either integer. The
following calculations then occur inside the pinned direct chain.

First, VA `0x18984` applies `minNum` to its initial float and the return of VA
`0x21124`. VA `0x1895c` then multiplies by a selector-derived unsigned value
divided by literal `1024.0`. VA `0x18834` further multiplies by:

```text
u16[NPC_AP+0x2c] / 1023.0
u16[NPC_AP+0x10a] / 65535.0
```

For the next stage, define only numeric quantities:

```text
D = low10(u16[NPC_AP+0xa6])       # 0..1023
G = u16[NPC_AP+0x2e]              # 0..65535
x = float input to VA 0x188d8
```

The recovered VA `0x188d8` arithmetic is:

```text
d = float32(D) / 1023.0
g = float32(G) / 65535.0
y = minNum(g, x) * d
NPC_AP+0x68 = low16(unsigned_float_convert(y * 65535.0))
return y
```

This directly proves the `NPC_AP+0xa6` value is an arithmetic factor in the
returned float. The cache scale is the `65535.0` literal at VA `0x18958`,
loaded by VA `0x18934`; the separate `1024.0` literal at VA `0x18980` belongs
to VA `0x1895c` and is not this cache scale. Calling any ratio percent, duty,
brightness, amplitude, or another physical unit would go beyond the evidence.

VA `0x18410` receives `y`. It multiplies it by
`u16[NPC_AP+0xa8]/1023.0`, gets a three-float reference from VA `0x193e0`,
and returns the component-wise `minNum` with that scaled value. Thus every
returned component has a duty-dependent candidate, while the minima can
mask that dependence.

VA `0x184c8` receives those three components. Its exact numeric fields are:

```text
component factors: NPC_AP+0x50/+0x52/+0x54, each divided by 65535.0
optional numerator: NPC_AP+0xbc divided by 1023.0
optional divisor:   NPC_AP+0xac divided by 1024.0
optional gate:      NPC_AP+0xba == 1
common multiplier: return from VA 0x1582c over the three inputs
```

When the optional gate is one, the routine scales each input by the
`(+0xbc)/1023` to `(+0xac)/1024` ratio and compares it with another triple
from VA `0x193e0`. There is no zero guard for `NPC_AP+0xac`. For finite,
ordered operands the `VCMPE` followed by `BHS` retains the smaller value. It
is not a general `minNum`: if the scaled candidate is NaN, the comparison is
unordered and the branch retains that candidate. This report therefore makes
no claim about division-by-zero results, exceptional inputs, live FPSCR
state, or subsequent conversion behavior. When the optional gate is zero,
the input triple is retained directly. The routine then multiplies each
component by its `+0x50/+0x52/+0x54` factor and the common multiplier,
returns the results, and VA `0x18984` returns those same retained stack
values. For finite in-range values, zero factors, the first `minNum`, and the
later ordered comparisons can erase numeric sensitivity to `D`; the static
path proves possible contribution, not its magnitude on a particular pass.

The already-documented earlier VA `0x188a4 -> 0x1a1f8` calculation also
reads `NPC_AP+0xa6/+0xa8` before VA `0x18984`. The direct VA `0x188d8` path
above is sufficient to prove the new writer-input join without depending on
that second relationship.

## `s3`: feedback-derived scalar

The fourth floating input is distinct from the triple. Before VA `0x18674`,
the outer body loads a float from fixed CPU address `0x20000890` into `s3`.
VA `0x18674` combines it with `u16[NPC_AP+0x5c]/1024.0`, then invokes the
ordinary helper sequence `0x19fd8 -> 0x18f7c -> 0x19a40 -> 0x1a1de` and
writes the resulting halfword to the caller's `sp+0x18`.

VA `0xd254` receives that halfword. Its complete pinned body selects and can
rescale a local unsigned halfword through multiple ordinary gates. The
bounded coherent accesses through its `NPC_AP` base are `+0x196/+0x19a/+0x19c`,
not `+0xa6`. At its final conversion it computes:

```text
s3_return = float32(final_u16) / 1024.0
```

The outer body stores that return back to `0x20000890` and passes it as `s3`
to VA `0x180e4`. This proves a numeric feedback relation, but neither the
helper-chain value nor `final_u16` has a recovered physical unit. It also
does not prove independence from all indirect/shared state.

## How the path reaches the divisor writers

Dispatcher VA `0x180e4` saves incoming `s3`, and its incoming `s0..s2` are
the caller-stack values at its offsets `+0xc8/+0xcc/+0xd0`. When
`NPC_AP+0x02 == 1`, it processes the three inputs through VA `0x1a530`,
multiplies them by the saved `s3` and a float from VA `0x38c8c`, then passes
the result through VA `0x1ae9c`:

- `NPC_AP+0xbe == 1` selects the row-building path and call to VA `0x1a748`.
- otherwise it selects the three-argument path and call to VA `0x1aa20`.

When `NPC_AP+0x02 != 1`, the corresponding branches use unity values instead,
so the duty-derived triple is not what reaches the writer call. Writer-local
conversion, count, zeroing, and outward-copy details are deliberately left
to the corrected divisor-provenance audit; this report establishes only the
upstream call-input join and does not restate the older writer summary.

Thus the former AF boundary is narrowed: the ordinary writer inputs are
prepared from a selected-package chain that includes the received
`F3:0x128` low-ten-bit field. The first unresolved causal boundary is no
longer whether the two paths meet; it is the runtime choice of clamps,
factors, dispatcher controls, helper returns, and writer-local gates on the
specific pass of interest.

## Evidence and limits

Input is the selected 5 MiB profile copy
`F_RSM1_BN9659934B_COMMON.bin`, SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
Image-0 linked VA is FILE minus `0x200`. This package is static evidence; it
does not by itself prove which code body executed during the captured fault.

`trace-floating-inputs.py` pins 17 complete function bodies, all direct call
sites on the bounded path, the selector-`0x128` entry/table/leaf, the counter
getter/update bytes and literal census, caller save/reload order, the duty
arithmetic and exact `65535.0` cache scale, the three `VCMPE/BHS` sequences,
feedback load/derive/save order, and the final `u16/1024` conversion. It also
performs four deliberate byte-mutation failure tests. It uses explicit
`need()` checks, so optimized Python does not remove validation.

The negative boundary remains narrow: direct Thumb `BL` calls and exact
bytes are covered; computed callbacks, interrupts, DMA, passed aliases,
other images, and runtime branch outcomes are not. No live value, event-time
ordering, brightness, panel power, fault, protection, or physical display
meaning is inferred.
