# Host selector-8 status-field lifetime

Recorded 2026-10-27 UTC. This is a bounded offline census of the selected
image-0 bytes. It made no TV, root-agent, network, USB, device-node, firmware,
configuration, storage, UI, or instrumentation request. It does not follow
the common handler's excluded persistent-service or return-guard branches.

## Result

The common status halfword at CPU `0x2000f0f0` (`AP` object
`0x2000f0e0 + 0x10`) has three positively established ways to acquire a
value in the selected package:

1. reset scatter zero-fills it;
2. a successful startup type-4 `AP` configuration load copies a packaged
   zero over it; and
3. common selector setter VA `0x2b764` overwrites all 16 bits with the
   selector supplied to common error entry VA `0xb660`.

The third route is not restricted to nonzero errors. Four direct ordinary
call sites pass selector zero. Therefore a selector-8 reply of zero is not,
by itself, proof that no common error ran. It is only a value observed at a
time boundary.

A genuinely successful raw selector-8 reply of zero after startup would
nevertheless rule out a still-retained selector-`0x10` from before that
sample. If a later raw reply from the same controller instance is `0x10`,
then some write or copy after the zero sample is required. Under the narrower
model in which only the coherent setter writes this field, that later write
must be a post-zero `b660(0x10)` entry. It still does not distinguish the two
startup/history sites from the recurring RT poll without timing evidence.

The earlier stock selector-8 “zero” mentioned in prior reports did not include
a raw selector-8 controller transaction proving the underlying transfer
succeeded. It does not satisfy this premise. A separately retained direct-RAM
zero candidate is under its own address/transport audit and is not interpreted
or promoted here.

## Source and address convention

The source is
`overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin`,
5,242,880 bytes, SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
For image 0, `FILE = VA + 0x200`; absolute RAM addresses are not shifted.
These are packaged-code facts, not a whole-image live-PC proof.

## Fixed object and reset initialization

Accessor VA `0xe670` / FILE `0xe870` is exactly:

```text
e670  ldr r0, [pc, #0]
e672  bx  lr
e674  .word 0x2000f0e0
```

It returns a fixed `AP` object; there is no allocator or nullable pointer in
this accessor.

Image-0 scatter row 11 is exactly:

```text
source/unused  0x0003e764
destination    0x20000f4c
length         0x00016438
handler        0x000001d8
```

Handler VA `0x1d8` is the reviewed zero-fill loop. Its destination extent is
`0x20000f4c..0x20017383`, so it contains the entire status halfword
`0x2000f0f0..0x2000f0f1`. The field is zero after this reset operation.
This says nothing about subsequent writes or survival across a later reset.

## Positive startup configuration overwrite

The ordinary 21-row table's `AP` row is FILE `0x3ccd8`:

```text
name VA             0x0003de88 -> "AP"
first destination   0x2000f0e0
table maximum       0x0000040c
second destination  0
logical prefix      0x00130000
```

Directory record 37 at FILE `0x84c00` is type 4 and supplies one present
segment:

```text
source relative to configuration base  0x000f2000
destination offset                      0
requested length                        0x0000040a
```

With configuration base FILE `0x80000`, the packaged source is FILE
`0x172000..0x172409`. The loader copies
`min(table 0x40c, metadata 0x40a) = 0x40a` bytes to `0x2000f0e0` after a
successful lower read. This is pinned in the verifier by the type-4 compare
and branch, the startup-wrapper-to-enumerator call, loader call, first-length
minimum selection, zero-result gate on the lower read, destination
construction, and copy call. Source halfword
`+0x10` is exactly zero. Thus the successful startup load positively
overwrites the status with zero; this is not inferred merely from the reset
image.

The payload's SHA-256 is
`936bf564162421ffca508509e7aba21e360f4556d9eaafc16230676aa53ca858`.
The two allocation bytes beyond the copied `0x40a` are irrelevant to `+0x10`.
Runtime load success and later modification remain unproved. A loader failure
can itself enter common error handling with selector `0x400`; the packaged
zero is consequently not an unconditional post-startup runtime value.

## Exact overwrite setter

Setter VA `0x2b764..0x2b779` / FILE `0x2b964..0x2b979` is:

```text
2b764  push {r4,r5,r6,lr}
2b766  mov  r4,r0
2b768  bl   e670
2b76c  add  r5,r0,#0x10
2b770  ldrh r0,[r0,#0x10]
2b772  bfi  r0,r4,#0,#16
2b776  strh r0,[r5]
2b778  pop  {r4,r5,r6,pc}
```

The `BFI` replaces the complete low 16 bits, so this is an overwrite rather
than an OR. A zero selector produces halfword zero. A bounded direct-BL census
finds exactly one direct caller, VA `0xb6a6`, inside common error entry
`0xb660`; the entry retains the original selector and supplies it to the
setter. This does not prove there is no computed call to either routine.

## Direct common-entry callers and zero writers

The halfword-aligned direct-BL census finds 35 calls to `b660`. Every one has
an immediate selector assignment to `r0` directly before the call:

| selector | direct-call count |
| ---: | ---: |
| `0` | 4 |
| `1` | 1 |
| `2` | 2 |
| `4` | 1 |
| `8` | 4 |
| `0x10` | 3 |
| `0x20`, `0x40` | 1 each |
| `0x80` | 2 |
| `0x400` | 7 |
| `0x800`, `0x900` | 1 each |
| `0xa00` | 3 |
| `0xb00` | 2 |
| `0xc00`, `0x2000` | 1 each |

The four selector-zero sites and their exact message arguments are:

| call VA | exact message string | bounded context |
| ---: | --- | --- |
| `0x12fbc` | `INA226_GetCurReg` | lower transaction failure branch |
| `0x130ea` | `INA238_GetReg` | lower transaction failure branch |
| `0x13226` | `INA238_SetReg` | lower transaction failure branch |
| `0x1c970` | `PMIC_Init` | conditional failure after two init results |

These labels are firmware strings passed to `b660`; they do not prove the
physical identity of a sensor, regulator, or rail.

The last zero site has a positive static startup order. Main startup calls the
type-4 configuration wrapper at VA `0x39a5e`, calls the EEPROM/history check
at `0x39b26`, then calls the sole direct caller of the PMIC helper at
`0x39b4a`. The helper's conditional error branch at `0x1c970` passes selector
zero. If that zero site executes while the field retains `0x10`, reaching the
setter overwrites it with zero. Static ordering does **not** prove that a
pre-loop selector-`0x10` entry returns and the later PMIC branch is then
reachable in the same startup. This report neither follows nor assumes a
return from the common handler.

The three direct selector-`0x10` sites remain exactly:

```text
0x9834  first EEPROM/history condition
0x9862  second EEPROM/history condition
0x214f2 recurring RT flag bit-0 poll
```

Any of them writes the same final halfword if it reaches the common setter.

## Bounded direct-access census and its limit

A linear register-use heuristic starts at 223 accessor calls recognized by
the decoder, follows simple register moves and constant adds/subtracts in file
order until a return (maximum 250 decoded instructions), and records apparent
effective offset `+0x10`. It is not control-flow-graph analysis: it ignores
branch edges and can both miss feasible paths and overapproximate infeasible
instruction sequences. Its ten generated candidates are:

```text
reads:  1eca2, 1f324, 1f33a, 1f34a, 1f35a, 1f36a,
        1fbfc, 21e6a, 2b770
write:  2b776
```

The bytes and local dataflow at these candidates were then checked directly;
the one write is the selector setter above. Getter VA `0x21e66` is the
established non-clearing host selector-8 case. The heuristic also records 62
apparent sites where the base or a subpointer reaches a call argument. Their
canonical digest is
`3c742bd201ed4aa9120acebc9f6397282278875af14415b21f51b53deecde8e8`.

Those apparent escapes are an explicit boundary, not an exhaustive escape
list: this is not a whole-program direct-call, alias, DMA, computed-address,
indirect-call, or bulk-copy proof. The separate positive type-4 loader already
demonstrates why a direct accessor/store pattern alone cannot enumerate every
writer. Raw `0x2000f0e0` words occur at image offsets `0x70f0`, `0xe674`, and
`0x3cadc`; they comprise another code literal, the accessor literal, and the
configuration-table destination. Computed construction, paths missed by the
linear heuristic, and external agents remain possible.

It is therefore accurate to say “the setter is the only direct accessor-
derived explicit store recovered by this bounded scan,” not “the setter is
the sole writer in the firmware.”

## Interpretation of a post-startup raw zero

Conditional on all of the following:

- the reply is an authenticated successful controller transaction, not a
  wrapper default or failed-read placeholder;
- selector 8 still executes the reviewed non-clearing `LDRH` path;
- the zero and later `0x10` come from the same controller instance without an
  intervening restart or image replacement; and
- writes are coherent at the halfword and no unmodelled writer fabricates
  the later value;

a raw zero after startup is a valid lower temporal bound. An `0x10` observed
later cannot be the unchanged stale contents from before that zero. Something
must have written or copied `0x10` afterward.

That conclusion is narrower than origin attribution. Selector zero is itself
a possible common error value, other selectors overwrite the same field, the
three selector-`0x10` call sites converge, and pointer/copy escapes prevent a
global sole-writer proof. A zero reply cannot prove that the EEPROM/history
path never ran, and a later `0x10` cannot prove the recurring poll ran.

## Reproduction

`verify-status-lifetime.py` pins the whole package, accessor, scatter record
and zero loop, AP table/metadata/payload, the type-4 gate and successful
bounded first-copy instruction slices, the direct startup-wrapper-enumerator-
loader chain, startup call order, exact setter, all
35 direct common-entry callers and their immediate selectors, four zero
labels, and the bounded linear-use output and limitations. It contains ten
explicit mutation-rejection tests, including the wrapper-to-enumerator call,
type gate, minimum branch, success gate, and copy call. Normal and optimized Python output are
byte-identical. The verifier performs zero target operations.

```sh
PYTHONPATH=/tmp/tcon-re-capstone \
  python3 overnight/host-status-lifetime-20261027as/verify-status-lifetime.py
PYTHONPATH=/tmp/tcon-re-capstone \
  python3 -O overnight/host-status-lifetime-20261027as/verify-status-lifetime.py
```
