# NPC_AP divisor writer math

Recorded 2026-10-27 UTC. This is a bounded offline analysis of selected
image-0 ordinary numeric code. It made no TV, root-agent, network, USB,
device-node, debugger, UI, playback, or configuration call. It implements no
collector, probe, writer, patch, reset, bypass, or firmware change. Protection,
return-guard, persistence, storage, high-bank, and bootloader paths are outside
scope.

## Result

The retained AK eight-byte sample contains:

```text
NPC_AP+0x14 = 100
NPC_AP+0x16 = 118
NPC_AP+0x18 = 118
NPC_AP+0x1a = 118
```

This trace explains the complete ordinary selected-image calculation that can
write the last three values, but it does **not** identify which branch produced
the retained values. The decisive new fact is that the path is stateful as well
as nonlinear: dispatcher VA `0x180e4` reads reference floats from fixed RAM,
passes them through VA `0x1a530`, and writes the pre-factor results back to the
same RAM before applying two more runtime factors and VA `0x1ae9c`.

For a finite writer input `y` in `[0,1]`, the already-reviewed AF conversion
model reduces each final store to:

```text
out = trunc_u32(float32(y * 1024.0)) & 0xffff
```

Multiplication by `1024` is an exact binary exponent shift in this bounded
range. Therefore output `118` corresponds exactly to:

```text
0.115234375 <= y < 0.1162109375
```

This interval is the strongest inverse statement supported by the retained
number alone. It does not recover the pre-transform inputs or identify a
physical unit. Values outside the finite nonnegative in-range model, NaNs,
infinities, unsigned-conversion exceptions, and live VFP exception state are
not assigned host semantics here.

## Dispatcher pipeline

The complete dispatcher body VA `0x180e4..0x18407` has SHA-256
`9f31abe91ea5bb0d0c3da95817152ccc15cf1364b7d9fd8616feb3afd235db14`.
Let:

- `x[j]`, for `j=0..2`, be incoming `s0..s2` already traced by AI;
- `f` be incoming `s3`, the AI-traced return from VA `0xd254`;
- `g` be the float returned by VA `0x38c8c`, which is exactly the float stored
  at CPU address `0x20000714`;
- `H(a,b)` be VA `0x1a530`, defined below;
- `G(v)` be the return of VA `0x2dbd0(v, 0.45454543828964233)`, as invoked by
  VA `0x1ae9c`. The second argument has exact bits `0x3ee8ba2e`. This report
  does not infer that `0x2dbd0` implements any named mathematical function.

The top-level branches are:

```text
if u16[NPC_AP+0x02] != 1:
    use unity triples
else if u16[NPC_AP+0xbe] == 1:
    build rows and call array writer 0x1a748
else:
    build one triple and call direct writer 0x1aa20
```

The getter for `g` is called before this branch, although the unity paths do
not use its result.

### Stateful array path

This path uses the float table rooted at fixed CPU address `0x20007c8c`.
Define:

```text
n = min(u16[NPC_AP+0x8e], 12)
c = u16[NPC_AP+0xc0]
d[i] = u16(c + n - 1 - i)
q[i,j] = float32(float32(x[j] * float32(c)) / float32(d[i]))
r[i,j] = H(table[i,j], q[i,j])
table[i,j] = r[i,j]
z[i,j] = float32(r[i,j] * float32(f * g))
row[i,j] = G(z[i,j])
```

The loop executes for `i=0..n-1`, then passes all rows and `n` to VA
`0x1a748`. The table write occurs before multiplication by `f*g`; it makes a
later invocation depend on retained results from an earlier invocation.

For the final row `i=n-1`, `d[i]=u16(c)`. With `c!=0`, the *real-number*
factors cancel, but the implemented expression has one binary32 multiply and
one binary32 divide. It is not guaranteed to reproduce the input bit for bit.
The verifier pins a concrete counterexample using `c=2250`, where input bits
`0x3d6a936e` become `0x3d6a936d`.

`c` still changes every earlier row. `n` chooses the final row and hence which
retained table row is supplied to `H`. Addition is truncated to 16 bits before
`d[i]` is converted to float, so high `c` values can wrap an earlier
denominator to zero. There is no zero-denominator guard in this body.

The `n=0` case is not a valid empty result: the loop is skipped, but VA
`0x1a748` later addresses `rows[n-1]`, twelve bytes before the row array. This
report therefore gives the final-row formula only for `1<=n<=12`.

### Stateful direct path

This path uses the adjacent three-float state rooted at fixed CPU address
`0x20007c80`:

```text
r[j] = H(table[j], x[j])
table[j] = r[j]
z[j] = float32(r[j] * float32(f * g))
y[j] = G(z[j])
```

It calls VA `0x1aa20` with `y[0..2]`. That writer additionally calls VA
`0x2178`: a nonzero return forces all three divisor outputs to zero; otherwise
it performs the `1024`, unsigned conversion, and low-16 store shown above.
The helper return is another required producing-pass input; it cannot be
reconstructed from retained `118`.

### Unity paths

When `NPC_AP+0x02 != 1`, the array path fills each constructed row with three
`1.0` values, while the direct path supplies three `1.0` values. Under the
finite well-formed model and a positive array count, the array path writes
`1024/1024/1024`. The direct path writes either `1024/1024/1024` or, when VA
`0x2178` is nonzero, `0/0/0`. Thus those ordinary unity outcomes do not yield
`118/118/118`. This is a conditional arithmetic exclusion, not proof that the
runtime `+0x02` branch was one rather than zero: count-zero, exceptional VFP,
memory corruption, and untraced writers remain outside that model.

## Interpolator VA `0x1a530`

The complete body VA `0x1a530..0x1a6c5` has SHA-256
`67ef1d4a4418980222e40645147c4ed7eb732eb29365b011333d771d32242eca`.
It receives `a` in `s0` and `b` in `s1`.

If `NPC_AP+0x24 != 1`, the preliminary result is `b`.

If `NPC_AP+0x24 == 1` and `NPC_AP+0x4de == 0`, the finite ordered formulas
are:

```text
if a > b:
    t = min(float32(u16[NPC_AP+0x28]) / 1023.0, 1.0)
    result = a - (a-b)*t
else:
    t = min(float32(u16[NPC_AP+0x26]) / 1023.0, 1.0)
    result = a + (b-a)*t
```

If `NPC_AP+0x4de == 1`, helper VA `0x27b78` returns an integer `k`. With
`epsilon=1/32768`, the finite ordered formulas are:

```text
a > b and b+epsilon > a  -> result = b
a > b otherwise          -> result = a - (a-b)*k/1023
a < b and a+epsilon > b  -> result = b
a < b otherwise          -> result = a + (b-a)*k/1023
a == b                    -> result = a
```

The strict snap test means a difference exactly equal to epsilon continues
through the interpolation expression. If `NPC_AP+0x4de` is neither zero nor
one, the body reaches the common path without defining the result from `a`
and `b`; absent the final override below, it exposes the incoming callee-saved
`s18` content. That branch is not modeled as a numeric transform.

VA `0x27b78` computes a lookup coordinate as follows:

```text
d = low16(trunc_u32(float32(abs(a-b) * 1024.0)))
if d > 1024: d = 0
selector = u16[NPC_AP+0x51e]
if selector > 3: selector = 0
k = low16(lookup_0x19830(d, selected tables, count=5))
```

It stores `d` and `k` at `NPC_AP+0x4f4/+0x4f6`. A bit in the separate object
returned by VA `0xf4f0`, and a conditional group rooted at
`NPC_AP+0x1a8/+0x1ac/+0x1d2/+0x1d4`, can each force `k=1023`. The trace does
not prove a general `0..1023` bound for the unforced `0x19830` return; only its
low 16 bits survive. Because masking precedes the `d>1024` comparison, a large
converted difference can in principle wrap back into the accepted range.

Finally, a separate object from getter VA `0xe670` can override every result:

```text
if u16[object+0x3e] == 1:
    NPC_AP+0x7e == 1 -> result = b
    NPC_AP+0x7e == 2 -> result = u16[NPC_AP+0x7c] / 65535.0
```

Other `+0x7e` values retain the preliminary result. All comparisons here are
the selected ARM `VCMPE` plus condition-code branches, not a generic `minNum`
operation. The formulas above are deliberately restricted to finite ordered
inputs; unordered/NaN branch and arithmetic behavior is not normalized by a
host approximation.

## Fixed-second-argument transform VA `0x1ae9c`

The complete body VA `0x1ae9c..0x1af51` has SHA-256
`8761bfa3a6e42095a66d789dfa95d0541708ae85203136409b96d65f6f0223b4`.
It calls VA `0x2dbd0` once for each component with the exact second argument
`0.45454543828964233`, then returns the three calls' results unchanged.

If the caller's row index equals `min(u16[NPC_AP+0x214],11)`, it also converts
each returned value after multiplication by `65535.0` and caches the low
halfwords at `NPC_AP+0x70/+0x72/+0x74`. Those cache stores do not feed the
returned triple in this body. Inputs are not domain-checked here; negative,
NaN, infinity, and exceptional behavior belongs to `0x2dbd0` and the target
VFP environment and is unresolved.

## What determines retained `118`

Within the finite, nonnegative, positive-count path, each lane must reach the
writer interval `[118/1024,119/1024)`. The producing-pass state needed to
compute that value includes:

| State | Exact role |
|---|---|
| `NPC_AP+0x02` | processed versus unity path |
| `NPC_AP+0xbe` | array versus direct writer |
| `NPC_AP+0x8e`, `+0xc0` | row count and 16-bit denominator sequence |
| RAM `0x20007c8c` or `0x20007c80` | retained reference floats, rewritten on the pass |
| incoming `s0..s2` | three AI-traced numeric inputs |
| incoming `s3` and float at `0x20000714` | common multiplier |
| `NPC_AP+0x24/+0x26/+0x28/+0x4de/+0x51e` | interpolation mode, rates, and lookup selection |
| getter-`0xe670` object `+0x3e`, `NPC_AP+0x7c/+0x7e` | final interpolator override |
| helper/table state used by `0x27b78` | lookup result `k` and force-to-1023 conditions |
| fixed VA `0x2dbd0` behavior | final nonlinear transform |
| VA `0x2178` return on the direct path | three-value zero override |

The selected stored initializer has `+0x02=1`, `+0xbe=1`, `+0x8e=1`,
`+0xc0=2250`, `+0x24=1`, `+0x4de=1`, and `+0x51e=0`, among other pinned
values. These are package defaults only. They do not prove loading, the live
branch, retained table contents, helper returns, or the controls on the pass
that produced `118`. AK captured only `NPC_AP+0x14..+0x1b`; W and its later
ordinary repeat captured different objects at different times. No existing
capture is atomic with this writer invocation.

Accordingly, equal retained divisors do not prove equal upstream inputs. The
three lanes merely landed in the same quantization bin. The exact producing
branch and current control tuple remain unresolved.

## Evidence and limits

Input package
`selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin` has
SHA-256 `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`;
image-0 linked VA is FILE minus `0x200`. This is static package evidence, not
proof that a particular body executed on the producing pass.

`verify-writer-math.py` pins the package, corrected AF and AI reports, AK raw
tuple, six complete function bodies, eight subpaths, direct-call sites, both
state-table roots, the common-factor getter, all numeric literals used above,
control loads, masks, conversion/store sequences, package-only initializer
values, the exact `118` interval, a binary32 cancellation counterexample, and
a 16-bit zero-denominator wrap fixture. It uses explicit `need()` checks, so
optimized Python does not remove validation.

The trace covers direct selected-image ordinary code and fixed literals. It
does not establish current RAM state, indirect writers, interrupt/DMA
ordering, another image, actual VFP exception state, event-time causality,
field units, content class, brightness, panel power, or a physical fault
mechanism.
