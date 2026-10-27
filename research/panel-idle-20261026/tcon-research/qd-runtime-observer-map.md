# Read-only runtime observer map: QD AutoDim object

## Scope

This is an offline address derivation for a later root-operated, **read-only**
`/proc/<avocd-pid>/maps` and `/proc/<avocd-pid>/mem` observation. It does not
attach, trace, inject, alter memory, issue D-Bus, or contact the TV. It applies
only to copied `libave.so.0.1` SHA-256:

```
a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777
```

All VMAs are 32-bit little-endian addresses in that image.

## Exact root chain selected by `ave_dimming::SetAutoDim`

`ave_dimming::SetAutoDim(int)` is Thumb code at `0x150f78` (symbol value
`0x150f79`, size 320). Its actual PIC/GOT chain is:

```
0x150f86  ldr r6, [pc, #0x104]       ; literal 0x15108c = 0x00453070
0x150f8c  add r6, pc                 ; Thumb PC 0x150f90 -> GOT base 0x005a4000
0x150fa4  ldr r3, [pc, #0xe8]        ; literal 0x151090 = 0x000029ec
0x150fa8  ldr r3, [r6, r3]           ; GOT slot 0x005a69ec
0x150faa  ldr r0, [r3]               ; active dimming-panel pointer
0x150fac  ldr r3, [r0]
0x150fae  ldr.w r3, [r3, #0x124]
0x150fb2  blx r3
```

`.rel.dyn` resolves GOT `0x005a69ec` as `R_ARM_GLOB_DAT` for
`ave_dimming::m_pDimmingPanel`, static storage `0x005be2a4`. Therefore:

```
load bias L
slot     = L + 0x005a69ec
global   = *(uint32_t *)slot              # expected: L + 0x005be2a4
panel    = *(uint32_t *)global             # active virtual dimming object
vptr     = *(uint32_t *)panel
inner    = *(uint32_t *)(panel + 0x4)
autodim  = *(int32_t  *)(inner + 0x2a8)
```

This function uses **`m_pDimmingPanel`**, not the nearby
`DimmingInstanceList::m_pDimmingObject`. The latter has separate GOT
`0x005a6a2c` and storage `0x005be504`; do not substitute it into this chain.

## Type and fields

Accept `panel` only when its vptr equals an allowed runtime address point:

| Class | Vtable symbol VMA / size | Allowed vptr |
| --- | --- | --- |
| `QDDimming` | `0x0059f2e0` / 552 | `L + 0x0059f2e8` |
| `QDDimmingMNT` | `0x005a0944` / 568 | `L + 0x005a094c` |

The `+8` is the Itanium C++ vtable address point after offset-to-top and RTTI.
Both vtables have `SetAutoDim(int)` at address point `+0x124`, resolving to
`QDDimming::SetAutoDim(int)` at `0x00172a34`.

The setter establishes these fields only:

| Relative address | Width | Observed use |
| --- | --- | --- |
| `panel+0x0` | pointer | vptr allowlist above |
| `panel+0x4` | pointer | inner object |
| `panel+0x18` | byte | tested before the setter writes |
| `inner+0x2a8` | signed 32-bit | raw AutoDim argument; no Boolean normalization |

`m_AutoPowerOff()` reads the same `inner+0x2a8` field and has a branch for
value `1`. No full allocation size is established; require only that each
four-byte read lies in a readable mapping. Do not assign meanings to other
values.

## Maps/load-bias rule and historical example

For every capture, derive `L` from the mapping of the exact library pathname
with file offset zero: `L = map_start - PT_LOAD.p_vaddr`. This library's first
PT_LOAD VMA is zero, so `L` is that map start. Never use its writable mapping
start as the bias.

The historical snapshot `overnight/runtime-dimming-map-20261026T112047Z.json`
had `L=0xf6b77000`, yielding:

```
slot f711d9ec; global-storage f71352a4;
QDDimming vptr f71162e8; QDDimmingMNT vptr f711794c.
```

The named writable library mapping ended at `f7125000`; BSS storage extends
beyond it. The later full-map capture confirms anonymous readable/writable BSS
`f7125000-f7139000`, so `f71352a4` is mapped in that historical run. A root
read-only, four-byte `dd` sequence then observed this one-time chain:

```
*(uint32_t *)f711d9ec = f71352a4       # GOT -> relocated global storage
*(uint32_t *)f71352a4 = f7203698       # global -> panel
*(uint32_t *)f7203698 = f71162e8       # QDDimming vptr allowlist member
*(uint32_t *)(f7203698+4) = f63895d8   # inner
```

Those values are retained in `overnight/runtime-dimming-dd-word-20261026T112605Z.json`,
`runtime-dimming-global-word-20261026T112635Z.json`, and
`runtime-dimming-object-header-20261026T112706Z.json`. They were not
double-read for stability and are historical observations, not current state.
The earlier `od` failure was its procfs seek semantics, not evidence of a null
pointer, denied access, or panel state.

## Race-safe read-only contract

1. Retain complete maps, derive `L`, and check every target range is readable.
2. Read twice, with no writes: `slot`, `global`, `panel`, `vptr`, `inner`,
   `panel+0x18`, and `inner+0x2a8`.
3. Accept only identical snapshots where `global==L+0x005be2a4`, panel/inner
   are nonzero and aligned, and vptr is in the two-value allowlist.
4. Otherwise report only `unstable`, `unmapped`, or `unexpected type`; do not
   follow guessed alternatives or make a physical-panel causal claim.

An accepted process-memory snapshot still cannot prove TCON health, panel
voltage, physical light output, or blackout causation.
