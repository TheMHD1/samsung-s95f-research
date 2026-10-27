# NPC_AP divisor provenance

Recorded 2026-10-27 UTC. This is a bounded, offline trace of the three
`NPC_AP` halfwords consumed by selected image-0 VA `0x2f5d8`. It made no TV,
network, root-agent, USB, device-node, controller, UI, playback, or
configuration call. It changes no parameter and does not enter protection,
return-guard, storage, high-bank, bootloader, persistence, or bypass paths.

## Result

The three inputs are `NPC_AP+0x16`, `+0x18`, and `+0x1a`. They are not the
same fields as the `NPC_AP+0x56/+0x58/+0x5a` outputs written by the earlier
four-lane source/companion consumer.

The selected and recovered-backup stored initializer gives:

```text
NPC_AP+0x16 = 1024
NPC_AP+0x18 = 1024
NPC_AP+0x1a = 1024
```

Two ordinary selected-image routines directly overwrite all three fields:

- VA `0x1a748` takes an array of three-component floating-point rows. It
  caps each component above at `1.0`, derives per-row values, and sets the
  three low fields from `rows[count-1]` (the final row only if count > 0) after multiplication by `1024.0` and
  unsigned floating-to-integer conversion.
- VA `0x1aa20` takes three floating-point arguments, applies the same upper
  cap and `1024.0` conversion, and stores them directly. If helper VA
  `0x2178` returns nonzero, it instead stores three zeros.

Both writers obtain the object through getter VA `0xef9c`. Their only direct
callers are four sites inside dispatcher VA `0x180e4`; that dispatcher has
one direct caller, VA `0x136d0`. This direct layer does not read
`NPC_AP+0x56/+0x58/+0x5a`, does not contain the fixed source word
`0x584109a4`, and does not call source/companion consumer VA `0x19064`.
Thus there is no direct edge in this recovered layer from the source-bin math
or its three `+0x56/+0x58/+0x5a` results into the low fields. The low fields
instead arrive through a distinct floating-input path.

That is not a whole-firmware independence proof. The first unresolved
producer boundary is the input preparation immediately above dispatcher
`0x180e4`: its sole caller VA `0x136d0` supplies `r5/r6`, floating results
ultimately returned through VA `0x18984`, and a fourth floating result from
VA `0xd254`. Indirect sharing upstream, a passed alias, DMA, or another writer
outside the exact getter-rooted layer is not excluded. No field unit or
physical meaning is assigned.

## Positive object and stored provenance

The selected image's ordinary 21-row registry at FILE
`0x3ccbc..0x3cf07` has SHA-256
`669adda911a2e5bf5b053ab486f11c2611e115b284eeaec79c58e5876fbad287`.
Row 2 is:

```text
name VA 0x3de84 -> "NPC_AP"
CPU base 0x2000d71c
extent   0x540
```

Getter VA `0xef9c` is the eight bytes
`004870471cd70020`, SHA-256
`84f93c6639be7fc7a21229eead9d80b31746059a46741f4973167e2b14ff0b47`.
Across the image's byte-granular exact-word census, `0x2000d71c` occurs only
at getter literal VA `0xefa0` and registry VA `0x3caf8`. This constrains the
direct census; it does not rule out callers passing or computing aliases.

The named `NPC_AP` directory block at FILE `0x84e00..0x84fff` is identical
in the selected image and recovered backup, SHA-256
`04a151171ff9a3774578ff4ad328f2a0016f2ab4c60c9afa7dd30501c307b414`.
Its first-payload relative coordinate at `+0x2c` is `0x0f2600`; under the
retained parameter-region coordinate this selects FILE `0x172600`. The
metadata declares type 4, logical base `0x140000`, destination offset 0 and
copy length `0x53e`, distinct from the registry allocation extent `0x540`.
The declared `0x53e`-byte stored payload is identical in both artifacts, SHA-256
`3e9f4747fa26eeca6818944a6dae2fbba54f6ccc79d1ed6a4dc05434b5ad21b7`.
For comparison, the allocation-sized `0x540`-byte stored slice has SHA-256
`37bb4edfb3d24fc8fe0887f59815cbfb10e3ecf87bfbdf40e481b0852de56518`;
its last two bytes are outside the declared copy. This report pins metadata
association, not execution of a type-4 loader or live object initialization.
The three stored halfwords at offsets `+0x16/+0x18/+0x1a` are each 1024.
This is stored-initializer evidence, not proof of the values at W, V6, boot,
or any other runtime instant.

## Exact `0x2f5d8` calculation

The complete function VA `0x2f5d8..0x2f96f` has SHA-256
`428c93783eeb93bec0a363d29043bca4c8aecdbf5e7339542ccd5c70ba537b45`.
Its prolog calls `0xef9c`, saves the returned pointer, and loads the three
halfwords into `s19`, `s20`, and `s21` at VAs
`0x2f5fa..0x2f60e`.

Let `O` be the separate `AP_EXCO` object. The initial source-table sums use
three different lower-bound fields:

```text
lane 0 lower bound = 15 - u16[O+0xea]
lane 1 lower bound = 15 - u16[O+0xec]
lane 2 lower bound = 15 - u16[O+0xee]
```

The common upper bound is 15 when `O+0xe8` is nonzero, otherwise 14. This is
the initial-tail path only.

When `O+0x116` is nonzero, VAs `0x2f6ba..0x2f716` recompute three candidate
indexes. Importantly, all three use the **same** numerator:

```text
N = float32(u16[O+0xea]) * float32(u16[O+0xf0])
C0 = unsigned_convert(float32(N / u16[NPC_AP+0x16]) + 0.5)
C1 = unsigned_convert(float32(N / u16[NPC_AP+0x18]) + 0.5)
C2 = unsigned_convert(float32(N / u16[NPC_AP+0x1a]) + 0.5)
```

`O+0xec` and `O+0xee` do not replace `O+0xea` in the second and third
numerators. W happened to contain 3 in all three initial-tail fields, which
would conceal this distinction in a value-only reconstruction.

The u32 conversions are first truncated to their low 16 bits by STRH
at `O+0x104/+0x106/+0x108`, reloaded with LDRH, then independently
clamped down to `O+0xf2/+0xf4/+0xf6`. Thus each final value is
`min(converted & 0xffff, cap)`, not `min(converted, cap)`. For example,
65535*65535/divisor1 converts to `0xfffe0000` in the modeled binary32 domain,
then the halfword store yields zero even with cap6. The host model covers
finite nonnegative in-range unsigned conversion and does not model live
floating-point control or exceptional ARM VFP conversion. No zero-divisor guard occurs between
the low-field loads and the three VFP divisions; this report does not infer
the architecture-specific exceptional conversion result for a zero value.

## Direct writers and copies

### Array writer VA `0x1a748`

The complete body VA `0x1a748..0x1aa03` has SHA-256
`c6389c2f4d136215608d5242b09a17b4a8b75214f25e82eb5fc087d1862261b6`.
It receives `r0 = rows` and `r1 = count`, with each row containing three
single-precision components. Every component above 1.0 is replaced by 1.0.
For `rows[count-1]`, VAs `0x1a890..0x1a8e4` multiply each component
by the literal `1024.0` at VA `0x1aa0c`, convert it to unsigned integer, and
store the low halfword into `NPC_AP+0x16/+0x18/+0x1a`. The dispatcher
sets count to `min(u16[NPC_AP+0x8e],12)` without a positive lower bound.
The final-row description requires count > 0; count zero instead forms an
address twelve bytes before the array (`rows[-1]`). No live zero count is
claimed.

The same body reads those fields back at VAs `0x1a966`, `0x1a978`, and
`0x1a98a`, on its copy branch mirrors them to offsets `+0x44/+0x48/+0x4c` beneath both
fixed roots `0x58431000` and `0x58430000`. These are positive copy edges;
they do not name the three fields or prove the current contents or physical
role of either destination. When `NPC_AP+0x19a == 1 && +0x19c == 0`, the
other branch writes zeros to those destinations instead of mirroring the
three low fields; it does not clear the low fields themselves.

### Direct writer VA `0x1aa20`

The complete body VA `0x1aa20..0x1ab7b` has SHA-256
`9d34ab9fb84cf51a05f6bbd9a34396f716ab43d213c706d7f3f22d1cd94cdfe6`.
It receives the three components directly in VFP argument registers, caps
them above at 1.0, and calls VA `0x2178`. A nonzero return selects three
zeros; otherwise the body applies literal `1024.0` at VA `0x1ab7c`, converts
the three results, and writes the low halfwords at VAs
`0x1aae8/0x1aaee/0x1aaf4`. Its later branch mirrors the chosen values to the
same two fixed roots unless `NPC_AP+0x19a == 1 && +0x19c == 0`, which
selects zero writes to those roots instead.

### One caller layer

The writer direct-call census is exact for selected nominal image 0:

```text
VA 0x1a748 callers: 0x1829e, 0x183ca
VA 0x1aa20 callers: 0x1836a, 0x183f8
```

All four calls are inside complete dispatcher body VA
`0x180e4..0x18407`, SHA-256
`9f31abe91ea5bb0d0c3da95817152ccc15cf1364b7d9fd8616feb3afd235db14`.
That body gets `NPC_AP` and reads only controls `+0x02`, `+0xbe`, `+0xc0`,
and `+0x8e` directly through its retained base. Depending on those controls,
it either builds an array of floating triples and calls `0x1a748`, or supplies
three floating values to `0x1aa20`, with unity fallbacks in two branches.

Dispatcher VA `0x180e4` has one direct caller at VA `0x136d0`, inside pinned
body VA `0x13464..0x1377f`, SHA-256
`b3b7d880f11c68c6eddb95628baaf9e2b19864747dceff366c9d835199df327a`.
Immediately before the call it places `r5/r6` in `r0/r1`, the retained three
floating results in `s0..s2`, and another floating result in `s3`. Following
those producer routines further would exceed the requested one-layer trace;
this is the exact unresolved input boundary.

No exact `0x584109a4` source word occurs in the dispatcher or either writer.
This proves separation only for the recovered direct layer. A computed or
passed pointer and indirect common ancestor remain outside the negative
census.

## What the W snapshot does and does not determine

W's retained ordinary AP_EXCO prefix has SHA-256
`0f7884892da5714a9adcb97cdc033c4d5b24201b1ac570dabcc6771c01a7e271`.
Its relevant fields are:

```text
O+e8=0
O+ea/ec/ee = 3/3/3
O+f0 = 900
O+f2/f4/f6 = 6/6/6
O+104/106/108 = 6/6/6
O+116 = 1
```

If the three stored defaults 1024 were substituted into the recovered
formula with these captured O values, the unclamped rounded candidates would
be `3/3/3`, so the outputs would remain `3/3/3`, not W's retained `6/6/6`.
For a positive integer divisor and the captured numerator 2700, the cap-six
boundary is exact: divisor 490 yields 6 after rounding/clamping, while 491
yields 5.

That arithmetic does not prove the runtime divisors differed from their
initializer. W did not capture `NPC_AP`, and its USB read is sequential rather
than an atomic cross-object observation. Earlier invocations with different
inputs can also leave retained candidate fields.

The logical minimum additional measurement relevant to this ambiguity is
therefore exactly six bytes: the three current halfwords
`NPC_AP+0x16..+0x1b`, captured alongside the already-known O inputs if
time-correlation matters. A transport implementation may choose a larger
fixed aligned envelope, but no other `NPC_AP` field is required to evaluate
these three quotient terms. Such a measurement would distinguish current
divisors from the stored `1024/1024/1024`; it would not identify their units,
physical producer, or establish event-time causality.

## Evidence and limits

`verify-divisor-provenance.py` pins the selected package, recovered backup,
W prefix, registry, getter, directory and payload, all five complete bodies,
exact call sites, divisor loads, shared-numerator operations, halfword-before-cap semantics, cap clamps,
direct writer stores, fixed copy roots, and W boundary arithmetic. It also
checks that normal and optimized Python execution can use explicit `need()`
failures rather than removable assertions.

The negative boundary is deliberately narrow:

- the two proved direct writers are complete, and their direct call sites are
  completely enumerated in nominal image 0;
- the image's only exact `0x2000d71c` words are its getter and registry row;
- passed/computed aliases, indirect calls, DMA, other images, and upstream
  shared producers are not excluded;
- stored defaults are not runtime observations; and
- no offset name, unit, calibration meaning, physical-input identity, or
  repair implication is inferred.

Reproduce offline:

```sh
python3 overnight/npc-ap-divisor-provenance-20261027af/verify-divisor-provenance.py
python3 -O overnight/npc-ap-divisor-provenance-20261027af/verify-divisor-provenance.py
```

Both executions must emit byte-identical compact JSON with
`target_operations:0`.
