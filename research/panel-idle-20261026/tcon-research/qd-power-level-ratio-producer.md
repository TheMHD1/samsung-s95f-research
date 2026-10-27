# Packaged QD selector `0x0d` ratio producer

Recorded 2026-10-27 UTC. This is a bounded offline analysis of the already
retained selected QD profile. It made no TV, root, network, controller, I2C,
EEPROM, MMIO, getter, or display call and changed no earlier evidence.

## Result

The controller-side value exposed through `F3:80` selector `0x0d` is a
rounded, clamped ratio. It is not a panel-power Boolean and it has no local
fault-return branch. In source-shaped notation, exact function at container
file `F:0x10e40..F:0x10ed1` (linked image address
`L:0x10c40..L:0x10cd1`) computes:

```text
denominator = uint16(*(object_2000f0e0 + 0x1a8))
effective_denominator = denominator != 0 ? denominator : 20000
numerator = uint16(*(0x200008d0))
result = uint32_trunc(float(numerator) * 100.0 /
                      float(effective_denominator) + 0.5)
return min(result, 100)
```

The zero-denominator case is explicitly supported by substituting `20000`;
it is not an error exit. A returned zero is therefore an ordinary arithmetic
result: the rounded ratio was below `0.5`, for example because the cached
numerator was zero or small. No instruction in this function tests RT
Protect, ERR_DET, controller error state, or panel power.

The exact producer of the numerator is a smoothed/calibrated cache pipeline.
It normally can produce zero, and it updates only on an internal invocation
cadence. This makes the captured change from `1` to `0` useful evidence that
this derived controller ratio changed, but not evidence by itself that a
fault branch ran or that the panel was switched off.

## Inputs and identity

| Input | Size | SHA-256 |
| --- | ---: | --- |
| `overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin` | 5,242,880 | `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0` |
| `qd-profile-readonly-rt-state-selectors.md` | 9,595 | `cde271e73dc03bafb950862df9ec3fe1a0323463c770b236cb5aa087bf5a4de8` |
| `qd-profile-rt-status-wire.md` | 11,365 | `6c532e2ad8a48041cf83ebddfa42af1282019d14169902b47e621f6a1c237f6e` |
| `overnight/apps-foryou-transition-analysis-20261027.md` | 21,618 | `c28aa6e0d14156a3a7ef8d56670162475c401c8c989fef1cb8e2dc6155bdf9c1` |

The selected asset has a `0x200`-byte container prefix before image 0. Its
vector table begins at file `0x200`: the initial SP is `0x20020000`, the
reset vector is linked Thumb address `0x345`, and the coherent reset
trampoline is at file `0x544` (linked `0x344`). Therefore, for this image,
`linked_address = container_file_offset - 0x200`. All otherwise-unqualified
code addresses below are explicitly **container file offsets**, prefixed
`F:` where ambiguity would matter. Relative branches and table walks retain
the same deltas under this constant shift; RAM/MMIO literal addresses remain
absolute and are not shifted. Absolute flash/code pointers require the
translation and were not used to establish the ratio formula.

These packaged bytes are not proved identical to the currently installed
controller firmware. The prior wire report establishes the `F3:80` selector
route and four-byte response, but its earlier linked-at-zero convention needs
the same `-0x200` code-address correction. This report only resolves selector
`0x0d`'s packaged computation.

The exact reviewed slices are:

| Image-0 range | Bytes | SHA-256 | Role |
| --- | ---: | --- | --- |
| `F:0x10e40..0x10ed1` (`L:0x10c40..0x10cd1`) | 146 | `683357695bc49cec924dc1efebf648c1633d93382751f4690a7bf2d3246ae83f` | selector `0x0d` ratio |
| `F:0x12480..0x124f7` (`L:0x12280..0x122f7`) | 120 | `355edb1f00ebc3cb6b7b9a0240e69fc041511c47382bd8bf209b07a494b48627` | numerator-cache update |
| `F:0x13234..0x1329d` (`L:0x13034..0x1309d`) | 106 | `9dcd0da2a6b4cd156e88ac5ef08c68c50a155849bf070ed20d6d8ea639eff865` | scale producer |
| `F:0x13194..0x131e3` (`L:0x12f94..0x12fe3`) | 80 | `b92b5410d88699996873c77929f1a6f7ed2051822f3b67a453e1a02b6ee920a4` | input acquisition wrapper |
| `F:0x1e54c..0x1e5a3` (`L:0x1e34c..0x1e3a3`) | 88 | `8aa38d7e0e89f185d6a4ab14ca9068d1e6987abaef48c743d1f4afe7d88d1beb` | cadence-state initialization |
| `F:0x7f5c..0x7f67` (`L:0x7d5c..0x7d67`) | 12 | `4c6a3bca9dc3d91934ca34b5750a1fc332de34dde488ef30be5e8ab8b2fefb52` | cached-input getter |
| `F:0x7f38..0x7f4f` (`L:0x7d38..0x7d4f`) | 24 | `8a242c8128bb88f9f1df40cb1a618de2e2ef148e203d32b93e55d2423f427c6d` | scale application |

## Exact ratio body

Accessor at `F:0xe870` returns constant object base `0x2000f0e0`.
`F:0x10e56` and `F:0x10e8e` load the unsigned halfword at object offset
`+0x1a8` (`0x2000f288`). Both arithmetic branches load the unsigned
halfword at `0x200008d0`. The literal pool supplies float `20000.0` at
`F:0x10ed4` and float `100.0` at `F:0x10edc`; `0.5` is encoded directly in VFP
instructions. Both branches convert their input halfwords to unsigned float,
add `0.5`, and convert to unsigned integer. `F:0x10ec2..F:0x10ece` clamps every
result above 100 to 100.

The body contains no store. A direct-instruction census of the first image
did not recover a direct `STRH` to accessor `F:0xe870` plus `0x1a8`; bulk
profile copies, indexed/aliased stores, DMA, and other indirect producers are
not excluded. The explicit denominator-zero branch proves only that zero is
a supported state and selects `20000`, not what product setting owns it.

The sole direct `BL` caller recovered for `F:0x10e40` in image 0 is selector
case `0x0d` at `F:0x2209c`. Indirect calls are not excluded.

## Numerator cache and cadence

`F:0x12480..F:0x124f7` maintains four RAM fields:

| Address | Recovered code role |
| --- | --- |
| `0x200008d0` | unsigned halfword result cache read by selector `0x0d` |
| `0x200008d4` | 32-bit update period/divisor |
| `0x200008d8` | 32-bit accumulator |
| `0x200008e0` | 64-bit invocation counter |

Each call increments the 64-bit counter, calls `F:0x7f5c`, sign-extends the
returned halfword, and adds it to the accumulator only when that signed value
is greater than zero. The call at `F:0x124b4` has the ARM EABI-shaped 64-bit
unsigned divide/mod argument and result layout; the following instructions
test its 64-bit remainder. The cache update runs only when the counter is
exactly divisible by `0x200008d4`.

On an update, the body divides the accumulator by the period, truncates that
average to a signed halfword, applies the `0x7f38` scale, converts the signed
scaled result to float, divides by `32768.0`, converts to unsigned integer,
and stores the low halfword at `0x200008d0`. It then clears the accumulator.
The invocation counter is not cleared by this update.

Initialization `F:0x1e54c..F:0x1e5a3` sets the period to 120 and clears the
accumulator and 64-bit counter. A separate switch body at
`F:0x2d12a..F:0x2d148` selects period 120 for an even input or 12 for an odd
input, then clears accumulator and counter. The meaning of that switch input
was not recovered. These are invocation counts, not seconds; host sample
spacing cannot be converted into a controller update interval.

No RT/status predicate is present in the cache update. Zero is a normal
possible cache value when no positive sample has accumulated, the integer
average is zero, the scale/truncation produces zero, or the cache has not yet
reached its next update. The exact initialization bodies do not explicitly
store `0x200008d0`, so this report does not claim when its initial value first
becomes valid. The sole direct `BL` caller found for `F:0x12480` is in the
main processing body at `F:0x13904`; indirect calls are not excluded.

## Input and scale provenance

The input getter at `F:0x7f5c` returns the halfword at `0x20000c3e`.
`F:0x13194..F:0x131e3` is the recovered direct writer: its caller at `F:0xd314`
passes operation ID `0x8a`; on lower-call success, the wrapper combines two
bytes in big-endian order, writes the caller's output, and mirrors that
halfword to `0x20000c3e`. On lower-call failure it invokes the common error
path with selector zero and does not write the numerator result cache.
The caller later maps values at or above `0x8000` to zero in a separate
field, after the mirror was written. A direct literal/xref census recovered
no other direct writer to `0x20000c3e`; aliased, indirect, or DMA writers are
not excluded. The physical units of operation `0x8a` were not recovered.

Scale helper at `F:0x7f38` multiplies its input by the unsigned halfword at
accessor-`F:0xe980` object offset `+0xe` (`0x2000d448`). Its setup body
`F:0x13234..F:0x1329d` reads object halfword `+0xc`; when bit 4 of object byte
`+0x150` is set, it stores the conversion-helper result of
`4096000.0 / field_c` into `+0xe`, otherwise it uses
`16384000.0 / field_c`. There is no zero guard for `field_c` in this local
body, so behavior for an invalid zero configuration is not inferred. The
conversion helper at `F:0x224cc` was not independently named, and this report
does not assign units to either field.

## Captured transition and limits

The retained transition trace contains selector-`0x0d` results of `1` near
target uptimes `84419.767` and `84429.794`, followed by `0` near
`84439.838`. Product logs around the same capture label the corresponding
value `ANA`; they report `ANA:1` before the For You UI activity and `ANA:0`
after it. The owner's physical report has no calibrated target clock or
reaction timestamp, so this does not establish an exact onset time.

The source supports a narrower conclusion: the cached derived ratio fell
from a rounded value of one to zero. Zero is compatible with an ordinary
low/zero input, a scale/truncation result, or cache cadence. It does not by
itself identify content load, a halted producer, panel power, RT Protect,
ERR_DET, or a hardware fault. Conversely, this report does not prove that a
fault could not indirectly change the ratio's upstream inputs.

Nothing here proves live-controller identity, physical units, a safe setter,
or a recovery action. No write, replay, control, or additional controller
query is proposed.
