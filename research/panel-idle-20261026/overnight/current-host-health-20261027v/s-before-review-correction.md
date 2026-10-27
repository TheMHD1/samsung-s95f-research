# AP_EXCO helper-input provenance

Recorded 2026-10-27 UTC. This is a finite offline trace over three selected
image-0 helper bodies left unresolved by P/Q. It made no TV, network, USB,
controller, root, device-node, write, reset, UI, or configuration request. It
does not inspect protection or return/bypass paths, bootloader, persistent
storage, high-bank state, POFLG, or guards.

## Result

The helpers implement three separate, stateful diagnostics:

1. `0x2f5d8` computes two debounced booleans and overwrites ordinary AP_EXCO
   halfword `+0xe6` as `F0 | (F1 << 1)` when gate `+0xca` is nonzero; it writes
   zero when `+0xca` is zero. It does not write `+0xca` or `+0x2fc`.
2. `0x2f9ba` evaluates a two-alternative condition and debounces bit 0 of
   AP_EXCO `+0x2fc` using counter `+0x300`.
3. `0x2fa38` samples three fixed 32-bit source words, applies six strict
   comparisons, and debounces bit 1 of `+0x2fc` using counter `+0x302`.

The positive object-level labels are `AP_EXCO`, `AP`, `AP_AG`, `NPC_AP`, and
the distinct derived `MULTI/AP_EXCO`. No helper contains a direct printable
field/control name, and no field unit or physical signal name is inferred.

The retained captures do **not** discriminate the V6 fault. They never sampled
ordinary AP_EXCO `+0xca`, `+0xe6`, `+0x2fc`, their counters, or the helper
comparison inputs. The late derived value `+0x3d8 = 1` is compatible with
either `+0xe6 bit 0` or any nonzero `+0x2fc`; it cannot select which diagnostic
was active, and it was not captured at the fault instant.

The selected and recovered-backup initializer payloads do add one useful
negative result: both store ordinary `+0xe6 = 0` and `+0x2fc = 0`, so their
final predicate is zero. Their gates/counters also prevent either helper from
maturing a positive result on its first invocation after that initializer.
Consequently the late derived `+0x3d8 = 1` is not the stored/reset default. It
requires runtime state evolution, another writer, or a different live source;
this offline comparison does not choose among those possibilities or prove
which initializer was active at V6.

## Positive object bindings

The selected package is 5 MiB with SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
Its complete ordinary 21-row registry table at FILE
`0x3ccbc..0x3cf07` has SHA-256
`669adda911a2e5bf5b053ab486f11c2611e115b284eeaec79c58e5876fbad287`.
The relevant first-object rows and exact getter bindings are:

| getter | positive row name | CPU base | extent |
| ---: | --- | ---: | ---: |
| `0xe660` | `AP_AG` | `0x2000dc5c` | `0x282` |
| `0xe670` | `AP` | `0x2000f0e0` | `0x40c` |
| `0xe678` | `AP_EXCO` | `0x2000ff14` | `0x33a` |
| `0xef9c` | `NPC_AP` | `0x2000d71c` | `0x540` |

Getter `0xe76c` returns the separately qualified derived object at
`0x200158a8`, whose object-level record names are `MULTI/AP_EXCO`. These names
qualify object provenance only; they do not name the offsets below.

## `0x2f5d8`: ordinary `+0xe6`

The complete body VA `0x2f5d8..0x2f96f` is 920 bytes with SHA-256
`428c93783eeb93bec0a363d29043bca4c8aecdbf5e7339542ccd5c70ba537b45`.
Its 16-byte literal pool at `0x2f970..0x2f97f` has SHA-256
`9a9c9a4bfefe85282065081ad355f3168e7551664dea99ad0eaf769039ea31c3`.
The decision/output region `0x2f804..0x2f963` has SHA-256
`1edc35ef9c97b5836cbf6be9c671d948f247b31375c70d1fe9cff1f57941566a`.

The helper gets, in order, derived `MULTI/AP_EXCO`, ordinary `AP_EXCO`,
`NPC_AP`, and `AP`. Define the values present at its final decision stage:

```text
P0 = u32(O+0xd0, low; O+0xd2, high)
P1 = u32(O+0xd4, low; O+0xd6, high)
P2 = u32(O+0xd8, low; O+0xda, high)
P3 = u32(O+0xdc, low; O+0xde, high)
X0, X1, X2 = three earlier table/ratio aggregates computed by this body
T  = O.u16[+0xe0]
```

`X0..X2` are positively body-local computed values, but their physical
meaning and units are not named. With `A = (P0 < X0) OR (P1 < X1) OR
(P2 < X2)`, the first candidate is:

```text
if O.u16[+0xcc] == 0:
    C0 is not evaluated and F0 = 0
elif O.u16[+0xce] != 0:
    C0 = A AND ((P3 >= X0) OR (P3 >= X1) OR (P3 >= X2))
else:
    C0 = A
```

When evaluated, false `C0` clears counter `O+0xe2`; true `C0` sets `F0=1`
once `O.u16[+0xe2] >= T`, otherwise it increments that counter and leaves
`F0=0` for this invocation. If `+0xcc` is zero, the counter is bypassed and
retained while `F0` remains zero.

The second candidate exists only when `O.u16[+0xce] != 0`:

```text
C1 = (P3 <= X0) OR (P3 <= X1) OR (P3 <= X2)
```

False `C1` clears counter `O+0xe4`; true `C1` sets `F1=1` once
`O.u16[+0xe4] >= T`, otherwise it increments that counter and leaves `F1=0`
for this invocation. If `+0xce` is zero, that counter is bypassed and retained
while `F1` remains zero.

Finally:

```text
if O.u16[+0xca] == 0: O.u16[+0xe6] = 0
else:                  O.u16[+0xe6] = F0 | (F1 << 1)
```

Only bit 0 is consumed by P's final derived expression. The function also
updates other counters, derived byte `+0x43`, AP offsets `+0x206/+0x208`, and
fixed unnamed literals/MMIO locations. Those side effects do not provide a
field name or physical meaning for `F0/F1`, so this trace does not name them.

## `0x2f9ba`: AP_EXCO `+0x2fc` bit 0

The complete 126-byte body VA `0x2f9ba..0x2fa37` has SHA-256
`e0b885549f1a95d40867a7289c6b7d05eba931523a9a10ae7a7c7ed4fa35bae5`.
It gets `AP`, `AP_AG`, and ordinary `AP_EXCO`. Define:

```text
g = AP_AG.u16[+0x92]
a = AP.u16[+0x37a]
Q0 = (g <= O.u16[+0x2d0]) AND (O.u16[+0x2d2] == a)
Q1 = (g <= O.u16[+0x2d4]) AND (O.u16[+0x2d6] == a)
Q  = Q0 OR Q1
```

Its state transition is:

```text
if not Q:
    O.u16[+0x300] = 0
    O.u16[+0x2fc] &= ~1
elif O.u16[+0x300] >= O.u16[+0xe0]:
    O.u16[+0x2fc] |= 1
else:
    O.u16[+0x300] += 1
    bit 0 is left unchanged
```

Thus bit 0 is stateful: a qualifying but not-yet-mature invocation increments
the counter without forcibly clearing a previously set bit.

## `0x2fa38`: AP_EXCO `+0x2fc` bit 1

The complete body VA `0x2fa38..0x2fb3f` is 264 bytes with SHA-256
`0275a3f5b85be051f4b4a48a2759b9cf8005ffdc96e6b7f26e1c5735274cfb56`.
Its following literal word is exactly `0x584109a4`. The helper reads three
32-bit values at offsets `+0x3c`, `+0x7c`, and `+0xbc` from that fixed but
unnamed source. Call them `S0`, `S1`, and `S2`. It copies their high/low
halves into AP_EXCO `+0x2d8..+0x2e2` before evaluating:

```text
R0 = (O.u16[+0x2e8] << 16) | O.u16[+0x2ea]
R1 = (O.u16[+0x2ec] << 16) | O.u16[+0x2ee]
X  = (O.u16[+0x10c] << 16) | O.u16[+0x10a]
R2 = (O.u16[+0x2f8] << 16) | O.u16[+0x2fa]
R3 = (O.u16[+0x2e4] << 16) | O.u16[+0x2e6]
R4 = (O.u16[+0x2f0] << 16) | O.u16[+0x2f2]
R5 = (O.u16[+0x2f4] << 16) | O.u16[+0x2f6]

Q = (S1 > R0) AND (S2 > R1) AND (X > R5) AND
    (R2 > X) AND (S0 > R3) AND (S0 < R4)
```

Its transition mirrors bit 0:

```text
if not Q:
    O.u16[+0x302] = 0
    O.u16[+0x2fc] &= ~2
elif O.u16[+0x302] >= O.u16[+0xe0]:
    O.u16[+0x2fc] |= 2
    O.u16[+0x304] = O.u16[+0x10c]
    O.u16[+0x306] = O.u16[+0x10a]
else:
    O.u16[+0x302] += 1
    bit 1 is left unchanged
```

The fixed source address and threshold fields have no direct string or named
register evidence in these bodies. They remain raw sources and comparisons,
not a claimed display-pixel, sensor, rail, temperature, or current diagnostic.

## Why the retained captures do not select a cause

### Stored selected/backup initializer

The selected package and recovered backup have byte-identical AP_EXCO
directory metadata and first payload. The directory at FILE
`0x85e00..0x85fff` has SHA-256
`dad4caf149769f0b363a11231267d73752802a3bd7484bd720562bbaa7be1cd8`.
The first payload at FILE `0x182200`, length `0x33a`, has SHA-256
`c50e438b4882c04e62542fa718cda662b56c3ea0930e20d54944a949e2e3afbf`
in both artifacts. Its relevant stored halfwords are:

```text
+ca=1  +cc=1  +ce=0  +e0=30  +e2=0  +e4=0  +e6=0
+2cc=1 +2ce=2 +2fc=0 +300=0 +302=0
+10a=0 +10c=0
+2e4=0x0032 +2e6=0xa000
+2f4=0x0032 +2f6=0xa000
```

This establishes four bounded consequences:

- The copied final expression is zero: `(+e6 & 1) OR +2fc = 0`.
- `+ca=1/+cc=1/+ce=0` selects the first candidate form but bypasses `F1`.
  With counter `+e2=0` below threshold `+e0=30`, `F0` cannot mature on the
  first invocation, regardless of the unnamed aggregate comparison.
- `+2cc=1/+2ce=2` selects the bit-1 helper and skips the bit-0 helper.
- In that bit-1 helper, `X=0` while `R5=0x0032a000`; the mandatory strict
  condition `X > R5` is false regardless of the three fixed-source samples.
  The helper therefore keeps/returns bit 1 clear from this initial state.

The distinct derived object is reset-zeroed by the independently pinned
scatter row. Thus neither reset state nor these selected/backup initializer
values make derived `+0x3d8=1` an intentional copied baseline. The later one
is evidence of state differing from those two stored/reset baselines, but not
by itself evidence that a particular helper ran, which physical input was
involved, the fault instant, the active bank, or causality.

### Captured live windows

The accepted ordinary AP_EXCO reads sampled only:

```text
+0x000..+0x00f
+0x3cc..+0x3eb
```

Their SHA-256 values are
`374708fff7719dd5979ec875d56cd2286f6d3cf7ec317a3b25632aab28ec37bb`
and
`f4eec86c76db591f12c003fc318c76418e9455c10f10ad2c40acf0b21010814b`.
Neither range covers any gate, candidate input, debounce counter, or output
described above.

The later corrected read sampled `+0..+0xf` and `+0x3c8..+0x3e7` in the
distinct derived object, not ordinary AP_EXCO. Its tail contains derived
`+0x3d8 = 1` at returned offset `0x10`.
That is only the late composite:

```text
(ordinary +0xe6 bit 0) OR (ordinary +0x2fc != 0)
```

It cannot distinguish the first-helper `F0`, bit-0 helper, bit-1 helper, any
other nonzero bit in `+0x2fc`, or a retained state. The RT fault capture is a
different controller block and supplies no same-invocation binding to these
ordinary fields.

## Boundary

This pass ends at the named object getters and the fixed raw source
`0x584109a4`. It does not recursively trace the aggregate-table producer,
MMIO producer, all writers of the threshold fields, or all writers of
`+0x2fc`; it makes no whole-firmware completeness, event-time, executing-bank,
physical-cause, or safe-write claim. The crucial remaining gap is a bounded,
same-incident observation of the ordinary gates, counters, inputs, and outputs
listed here—not another inference from derived `+0x3d8` alone.

`verify-helper-inputs.py` pins the package, object rows/getters, complete
helper bodies, decisive branches and set/clear encodings, direct caller sets,
literal pools, retained capture hashes/ranges, and the explicit negative
claims using only Python's standard library. Normal and optimized runs must
emit byte-identical JSON with `target_operations:0`.
