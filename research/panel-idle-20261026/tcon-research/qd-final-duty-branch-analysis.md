# Base QDDimming final-duty branch and immediate RoseMQD backend

## Scope and evidence

This is a bounded offline analysis of the base (non-MNT) path in
`binaries/libave.so.0.1`, SHA-256
`a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777`.
The ELF is ARM32.  All addresses below are ELF virtual addresses; Thumb function
symbols have bit zero set while the displayed instruction starts are even.

The companion `qd-final-duty-reproduce.py` hash-gates that ELF and the accepted
passive baseline, checks symbol sizes, instruction operands, PC-relative static
objects, PLT identities, and the concrete backend vtable relocation, and models
the instruction-level integer arithmetic.  CFG recovery and field typing are
still manual.  No TV, network, root, process-memory, device, getter, setter, or
IOCTL operation was performed for this analysis.

Principal functions:

| Function | Thumb symbol | Code range |
|---|---:|---:|
| `QDDimming::m_AutoPowerOff()` | `0x1740f1` | `0x1740f0..0x17425f` |
| `QDDimming::m_SetFinalDuty2D()` | `0x174261` | `0x174260..0x1745cb` |
| `DimmingBackendRoseMQD::t_Set2DFinalDuty(...)` | `0x1c6275` | `0x1c6274..0x1c636f` |

The names “duty,” “gain,” and “AutoPowerOff” below are binary symbol/field-role
labels.  The binary proves integer dataflow, but not a calibrated PWM, voltage,
luminance, percentage, physical-light, mute, or power-state unit.

## `m_SetFinalDuty2D`: ordered calculation gates

At `0x174272`, `inner = *(this+4)`.  The routine selects exactly one initial
calculation path in this order:

1. `*(uint8_t *)(inner+0x38) != 0` (`0x17427c..0x174282`): use the word at
   `inner+0x88` as the weight.
2. Otherwise, `*(int32_t *)(inner+0x450) == 1`
   (`0x1743d2..0x1743d8`): use `inner+0x98` as the weight.
3. Otherwise, `*(int32_t *)(inner+0x188) == 1`
   (`0x1743dc..0x1743e2`): replace the existing `inner+0xac` with signed
   division by four, rounded toward zero (`0x174510..0x174520`).  This branch
   consumes a prior cached value; it does not freshly read `+0xf8`, `+0xfc`, or
   the Weber inputs.
4. Otherwise take the ordinary Weber calculation (`0x1743e6..0x174438`).

Thus `+0x38` wins over both later gates, and `+0x450 == 1` wins over
`+0x188 == 1`.  `+0x188` still affects the later lower bounds even when one of
the first two calculation paths won.

### Exact integer expressions

All `mul` operations below retain the low 32 bits.  Signed comparisons and the
`/100`, `/300`, and `/4` descriptions use signed 32-bit values after that
wrapping.  `T100(x)` denotes signed division of wrapped `x` by 100, toward zero;
the instructions implement it with `0x51eb851f`, `smull`, arithmetic shift 5,
and sign correction.

Both weighted paths calculate:

```text
base = T100(1023 * inner[+0xfc])
delta = int32(inner[+0xf8] - inner[+0xfc])
inner[+0xac] = int32(base + T100(weight * delta))
```

The `+0x38` path takes `weight = inner[+0x88]`; the `+0x450` path takes
`weight = inner[+0x98]`.  This is a dimensionless integer expression as far as
the available binary proves; “percent,” nits, or electrical duty would be an
unsupported unit assignment.

The ordinary Weber path performs this exact unsigned/mixed fixed-point
sequence, again with each 32-bit `mul` wrapping:

```text
u = uint32(inner[+0x458] * inner[+0x2a4]) >> 10
v = uint32(inner[+0x98] * u) >> 10
w = uint32(int32(inner[+0xf8] - inner[+0xfc]) * v)
x = uint32(w * 1023) >> 2
term = high32(uint64(x) * 0x52000521) >> 13
inner[+0xac] = int32(T100(1023 * inner[+0xfc]) + term)
```

The reciprocal constant is numerically associated with the preceding scaling,
but the report retains the exact operations rather than inventing a physical
unit or replacing the expression with an unproved source-level decimal formula.

## Post-calculation mutation, AutoPowerOff, and clamps

After the selected calculation:

- If `inner+0x188 != 1`, `inner+0xac` is raised to at least signed
  `inner+0xa4` (`0x1742be..0x1742d6`).  Exact value 1 skips this floor.
- The interface at `this+8`, virtual slot `+0x54`, is then called with a pointer
  to `inner+0xac` (`0x1742e6..0x1742f0`).  Its return value is ignored, but it
  can mutate the word.  This analysis does not bind that dynamic target, so the
  arithmetic above is not by itself the final request.
- The possibly mutated `+0xac` is copied to `+0xa8`, then
  `m_AutoPowerOff()` runs (`0x1742f2..0x1742fe`).
- If `inner+0x188 != 1`, the resulting signed `+0xa8` is clamped to
  `[51,1023]`.  If it equals 1, it is clamped to `[12,1023]`
  (`0x174302..0x17432c`, alternate minimum at `0x17443e`).

The word at `inner+0x138` has two debug-log tests: original bit 15 around
`0x1742dc` and original bit 25 around `0x174330`.  Those detours conditionally
format logs and rejoin, respectively, the `this+8/+0x54` call and the backend
call.  They do **not** bypass those calls.  They are not output-policy gates.
`m_AutoPowerOff` similarly tests original `inner+0x138` bit 18 only for a log
detour, and the RoseMQD backend tests bit 0 of its own inner debug word only for
logging after its send/cache decision.

The final signed clamps are important: on the routine's normal sequential
control flow, the immediate backend candidate cannot be zero.  It is at least
51 normally or 12 for exact `inner+0x188 == 1`.  This statement concerns the
integer passed by this routine, not physical light and not successful hardware
application.

## What `m_AutoPowerOff` actually does

`m_AutoPowerOff` reads:

- source word `inner+0xfc`;
- current working word `inner+0xa8`;
- raw gate `inner+0x2a8`; and
- its function-local static `siAutoDimCount` at ELF `0x5be420`.

It first computes, with 32-bit wrapping before the signed division:

```text
floor = trunc_toward_zero(int32(uint32(inner[+0xfc] << 10)) / 100)
```

If `inner+0x2a8 == 1`, and both `count < 300` and current `+0xa8 > floor`, it
increments the count (with a zero floor).  Otherwise that exact-1 branch sets
the count to 300 and the working word directly to `floor`.  For every other
`+0x2a8` value, it decrements the count, clamps it to `[0,300]`, and continues.
The continuing path calculates:

```text
remain = 300 - count
inner[+0xa8] = floor
                 + trunc_toward_zero(
                       int32(uint32((old_a8 - floor) * remain)) / 300)
```

Division by 300 is the `0x1b4e81b5` signed reciprocal sequence.  The count is
an invocation count, not seconds.  It is function-static rather than stored in
the individual QD object.  The routine returns zero; its caller here ignores
that result.

The arithmetic alone **can** produce zero: for example a zero `floor` and a
zero working word, or saturation to a zero `floor`, yields zero.  But the
subsequent `m_SetFinalDuty2D` clamp changes that zero to 51 or 12 before the
immediate backend request.  `m_AutoPowerOff` contains no direct power-service,
mute, or device operation despite its name.

## Immediate typed backend, cache, and transport calls

`m_SetFinalDuty2D` builds a request record and places the clamped `inner+0xa8`
at record offset `+8`.  If `this+0x10` is non-null, it calls virtual slot
`+0xd8`.  The accepted baseline typed that object as `DimmingBackendRoseMQD`;
its captured vptr was AVE bias `+0x5a152c`, and ELF relocation `0x5a1604`
(`+0xd8`) names the base `DimmingBackendRoseMQD::t_Set2DFinalDuty`, Thumb target
`0x1c6275`.

That backend performs:

1. Read the requested scalar from record `+8` (`0x1c6288`).
2. Compare it with function-local static `siDimLvl` at ELF `0x5ab958`.
   Its ELF initializer is `0xffffffff`.
3. On equality, skip both transport calls and return zero.
4. On mismatch, write the **requested** scalar to `siDimLvl` before either
   call (`0x1c62ac`), and copy it to a stack-local word.
5. Call `ave_tcon_api_send_onecommand(0x0000f30000000128, &local)` through PLT
   `0x8db9c`.
6. Reload the local word after that call and pass it to
   `ave_frc_write_i2c(0x00042b48, local_after)` through PLT `0x9023c`.
7. Return the bitwise OR of both call results.

Because the first call receives a pointer, static analysis does not prove that
the second call's value still equals the requested scalar.  The cache does
remain the original requested value.  There is no rollback on either error, so
a failed mismatching attempt can suppress an identical later request until the
cache or requested value changes.  Cache equality therefore means only
software request equality, not successful transport or applied panel state.

Back in `m_SetFinalDuty2D`, a null backend contributes zero.  Independently, if
`inner+0 == 1`, the vendor object at `this+0xc`, virtual slot `+0x48`, is called
and its result is ORed with the backend result.  The routine returns that
aggregate.  The established vsync caller at `0x17b564..0x17b56a` calls
`m_SetFinalDuty2D` and immediately branches without inspecting `r0`; other
possible callers were not exhaustively classified.

The two numeric transport calls are the nearest concrete software outputs
recovered here.  Their presence does not establish wire bytes, device
acceptance, panel application, or physical luminance.

## Concrete writers of the principal gates

A bounded review of direct, immediate-offset stores in exported base
`QDDimming` methods found:

- `inner+0x38` is initialized to zero in the constructor at `0x17aac0`.
  `QDDimming::SetCondition(int,int)` selector 1 dispatches to `0x17033e` and
  stores `value != 0` as a byte at `0x170346`.
- `inner+0x450` is written in the constructor at `0x17afd2` from
  `get_product_type(1)`.
- `inner+0x188` is written in the constructor.  The constructor first calls
  `ave_get_oled_model_type(&local)` unconditionally at `0x17afc4..0x17afc6`,
  then calls `get_product_type(1)`, stores that result at `+0x450`, and tests
  it.  When `+0x450 != 1`, the already-returned OLED model enum makes `+0x188`
  equal 1 exactly when it is 2 (`0x17afec`).  When `+0x450 == 1`, `+0x188` is
  forced to zero (`0x17b080`).
- `inner+0x2a8` is initialized to zero.  `QDDimming::SetAutoDim(int)` stores its
  raw integer at `0x172a4e`; the final-duty routine tests exact value 1.
  `SetInstantOn` also clears this word on its qualifying enum paths.
- `inner+0x138` is initialized to zero and is modified as a bitmask by
  `SetDebugPrintFlag` category 1 (`0x170e88`/`0x170f00`); as noted above, its
  relevant bits only route logging in this function.

This is a finite direct-store inventory, not proof that no indirect writer
exists.  Bulk copies, stores through calculated pointers, debug parsers, or
writers in other DSOs were not exhaustively decompiled.  The data-producing
path behind the Weber virtual getter is intentionally outside this report's
scope.

## Relation to the accepted passive baseline

The only dynamic evidence used here is
`overnight/pqe-policy-baseline-20261026T174544Z.json`, SHA-256
`5c36124d0d510fff8ac5ff282cfc43c1a70854d065b76da68ad760ceb56482a4`.
It is an accepted, sequential, non-atomic, **physical-unobserved** read over TV
uptime `58355.79..58356.56`.

It established a base `QDDimming` object and typed base
`DimmingBackendRoseMQD` chain.  It sampled:

- `inner+0xa8 = 236` and `inner+0xac = 236`;
- `inner+0x458 = 1023`; and
- backend `siDimLvl = 236`.

It did **not** sample the decisive `+0x38`, `+0x450`, `+0x188`, `+0x2a8`,
`+0x2a4`, `+0x88`, `+0x98`, `+0xa4`, `+0xf8`, `+0xfc`, the AutoPowerOff
counter, or the mutating `this+8/+0x54` call.  Therefore it cannot identify
which formula branch was active or replay the calculation.  Equality of the
two working words and backend cache at one non-atomic instant does not show
that this callback ran then, that a send occurred, or that the panel applied
236.  No physical state, onset, fault, repair, causal policy, mute, or power
conclusion follows.

## Reproduction and limits

Run locally:

```sh
PYTHONPATH=/tmp/tcon-capstone python3 tcon-research/qd-final-duty-reproduce.py
```

The checker deliberately stops at pinned instruction/relocation landmarks and
an explicit arithmetic model.  Unrecovered edges are the concrete `this+8`
slot target and mutation, indirect gate writers, transport implementation/wire
format, driver acceptance, and physical effect.  Concurrency and arithmetic
inputs outside the intended runtime domain are not reconstructed from the
single passive sample.
