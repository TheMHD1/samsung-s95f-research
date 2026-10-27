# Image-0 `0x2dbd0` numeric transform

## Scope and evidence boundary

This is an offline, byte-pinned analysis of the selected package's image 0.
It makes no TV, USB, network, MMIO, or write operation.  It does not identify
a physical unit, propose a firmware change, or enter any protection, return-
guard, high-bank, storage, or bootloader path.

The source is
`selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin`, a
`0x500000`-byte package with SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
Image 0 is package file range `[0x200,0x40200)`, so image-0 virtual address
`VA` is package file offset `VA+0x200`.  The prior bounded caller report
`npc-ap-writer-math-20261027am/writer-math.md` is pinned at SHA-256
`6fde3f57183820a60646b48ce59da70c1e3ef7f73dc371f4f5d5231a082d5baa`.

## Result

The operation at image-0 VA `0x2dbd0` is positively identifiable by its
instructions and data tables as a **single-precision binary power transform,
`x^y`**.  This conclusion does not come from the caller's exponent alone:

- the entry classifies the IEEE-754 bit fields of both arguments and splits
  the base into exponent and mantissa;
- the main path reduces the mantissa into one of 16 intervals and reads 16
  high/low pairs whose sums are `16*log2(1+i/16)`;
- VA `0x2dd70` executes `VMUL.F32 s0,s17,s18` in the split-log/split-exponent
  product, followed by correction terms involving the low parts;
- the result is reduced into an integer power-of-two component and a
  four-bit table index;
- three 16-entry tables contain split and exact binary32 values of
  `2^(i/16)`, followed by a polynomial residual and exponent reconstruction;
- separate paths classify negative bases, integer versus non-integer
  exponents, zero, subnormal, infinity, and NaN.

That establishes the mathematical operation class.  It does **not** identify
the vendor/source-library function name, a particular libm revision, all
floating-point exception side effects, or a bit-for-bit/ULP conformance
contract for every input.  Those remain beyond the static evidence.

The complete bounded primary body, including its interleaved literal pools,
is `[0x2dbd0,0x2e228)`, 1,624 bytes, SHA-256
`70d0dd8ce4728859af7c86a1d71fb2d5191e45c9d78b10f5c984c04d215a6937`.
The next bytes at `0x2e228` begin another code body.  The external special-case
leaf helpers used by this body are separately pinned by the verifier; they are
not silently counted as part of those 1,624 bytes.

## Ordinary fixed call

The ordinary caller body `[0x1ae9c,0x1af52)` has SHA-256
`8761bfa3a6e42095a66d789dfa95d0541708ae85203136409b96d65f6f0223b4`.
Its direct calls at `0x1aeb8`, `0x1aecc`, and `0x1aee0` all target `0x2dbd0`
and pass the same second argument loaded from VA `0x1af54`:

- bits: `0x3ee8ba2e`
- exact decoded binary32 value: `0.45454543828964233`
- Python hexadecimal spelling: `0x1.d1745c0000000p-2`
- classification: positive, normal, nonzero, and non-integer

It is close to `5/11`, but its stored binary32 value is not equal to the host
double-precision value of `5/11`; this report does not replace the literal
with that rational.

The nominal image-0 direct-BL census finds 11 call sites to `0x2dbd0`:
`0x33ae`, `0xd488`, `0xdac6`, `0x17a98`, `0x197d2`, `0x19ea0`, `0x1aeb8`,
`0x1aecc`, `0x1aee0`, `0x22fe4`, and `0x23292`.  That is a bounded direct-BL
census, not a claim that indirect calls do not exist.

For this ordinary caller, the real-number target on finite positive
`x in [0,1]` is therefore:

```text
G(x) = x ** 0.45454543828964233
```

The mathematical endpoints are `G(0)=0` and `G(1)=1`; for `0<x<1`, the real
target lies strictly between `x` and `1`.  The body has explicit branches
returning the corresponding binary32 endpoints.  This mathematical statement
does not prove strict monotonicity or correctly rounded output of every finite
machine evaluation.

## Pinned stages and tables

| Region | VA range | Bytes | SHA-256 |
|---|---:|---:|---|
| entry/classification | `[0x2dbd0,0x2dc20)` | 80 | `aac0ce1c3dbacddbefd4ea1f827e089fe5550cafdb8833bd87ec7ff3070a035b` |
| log2 reduction | `[0x2dc20,0x2dd54)` | 308 | `02d7d12129e9be98302f2ad8dd779cc0dab35fd62cd176d3a5ba1c530da509a9` |
| log-times-y/reduction | `[0x2dd54,0x2ddce)` | 122 | `63a4f12252e4848aec220693e4a815e755537cb9c6f3df6002240bcfd92cee21` |
| exp2 reconstruction | `[0x2ddce,0x2df4a)` | 380 | `8ec1092f776370a73f5f66330934d893ca14dd42c975f7683fa873ec771fced5` |
| negative-base/integer-y path | `[0x2df4c,0x2dfd0)` | 132 | `069386061879775eed2a58600d70a7a5fbe630df2ac90e0cd92610fc1cc7ee10` |
| main literals | `[0x2dfd0,0x2e030)` | 96 | `762dfdd9f6e3111949a4ec9960387c77a19f47949126aaf30f9beb0165fac164` |
| special cases/small-log path | `[0x2e030,0x2e206)` | 470 | `755765c8649d45ab606d5add9bce24741608365a012b660f265fd726aab50922` |
| trailing literals | `[0x2e206,0x2e228)` | 34 | `4ba26efc42d09215c013ed1fb1205bda7e34ff82d4a7b3df9d56c178bf7ece2e` |

Four PC-relative constructions resolve to these tables:

| Purpose | VA range | Structure | SHA-256 |
|---|---:|---|---|
| log2 split | `[0x3db78,0x3dbf8)` | 16 `(high,low)` pairs | `f09c6d6c83a6f1d2bb607527e42b69bd7e3bb94416e979ad7856e3ddbae966cb` |
| exp2 high | `[0x3dbf8,0x3dc38)` | 16 floats | `0b9acac1c771ff6b79f9a659dffee2771ff6431dda6ef2022280248eb65c9813` |
| exp2 low | `[0x3dc38,0x3dc78)` | 16 floats | `d40eeb9d3e47ac1b5907842859de142687de58d0a3d0e2a54c4da62f7b05c099` |
| exp2 exact | `[0x3dc78,0x3dcb8)` | 16 floats | `897133476516e88d5d9dc2d47dc5e236b66cab035bbabbf8212cdeff4c54e620` |

For every index `i=0..15`, the exact table bit-equals nearest-binary32
`2^(i/16)`, and binary32 rounding of `exp2_high[i]+exp2_low[i]` bit-equals
that exact-table entry.  Each log pair's real sum differs from the host
reference `16*log2(1+i/16)` by less than `6e-11`.  These numerical identities,
together with the direct table loads and multiply/reduction instructions, are
the positive structural basis for identifying power rather than guessing a
function name.

## Branch-domain facts for the fixed exponent

Only behavior supported by the pinned instructions is claimed:

- `+0` returns `+0`; `1` returns `1`; `+infinity` returns `+infinity` for this
  positive, nonzero exponent.
- A positive subnormal base is multiplied by the literal `2^27`, with the
  corresponding exponent adjustment, before entering the main log path.
- A finite strictly negative, nonzero base fails the integer-exponent test for
  this fixed `y`.  The path calls VA `0xdb4` with argument 1 and then branches
  to VA `0x2e328`, whose leaf loads zero and performs `0/0` in binary32.  The
  resulting NaN payload and floating-point status side effects are not fixed
  here because they depend on the target VFP environment and the separately
  uncharacterized diagnostic helper.
- A NaN operand can route to VA `0x2e320`, which performs binary32 addition of
  the operands before returning.  Static bytes establish that propagation
  operation, not a universal payload rule.

No exceptional-input fact above is used to infer a physical failure, panel
state, or repair action.

## Reproduction

Run both modes; they must print byte-identical one-line JSON:

```sh
python3 verify-transform-math.py
python3 -O verify-transform-math.py
```

The verifier uses only Python's standard library.  It pins the package and
prior-report hashes, complete body and subregions, caller and exponent,
direct-BL census, table-address constructions, table hashes and mathematical
relations, key special helpers, and three fail-closed byte-mutation fixtures.
Its output explicitly reports `target_operations: 0`.
