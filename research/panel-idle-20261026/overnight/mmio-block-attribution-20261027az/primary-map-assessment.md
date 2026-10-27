# Primary-source assessment of the `0x4013....` output boundary

Recorded 2026-10-27 UTC. This is a bounded offline and public-document
assessment. It made no TV, USB, root, controller, network-device, firmware,
MMIO, reset, storage, UI, or physical-board operation. It did not design a
patch, bypass, register write, or probe.

## Result

No official primary hardware document found in this finite search satisfies
both requirements needed to name the live registers:

1. a register layout matching more than one of the relevant addresses; and
2. positive silicon identity tying that layout to the controller represented
   by the selected `RSM1` package and the photographed TV.

The four locations therefore remain **unnamed controller MMIO**:

| Address | Selected-image write established by the prior code trace | Hardware attribution after this search |
| --- | ---: | --- |
| `0x40130010` | `0x00000008` | unknown |
| `0x40131010` | `0x00000004` | unknown |
| `0x40132010` | `0x00000080`, and conditionally `0x00000200` on an earlier path | unknown |
| `0x4013400c` | `0x00000010` | unknown |

It is not source-safe to relabel these as GPIO, panel enable, a panel rail,
reset, scan control, timing, PWM, OTP, fault-data, or FlexSPI registers. The
power-of-two values and the repeated `0x1000` spacing of three addresses are
patterns, not peripheral identification.

## Local evidence boundary

The starting point is
`../rtp-action-causality-20261027t/rtp-action-causality.md`, SHA-256
`4465ca1a50b9c4a851cf0233a4172e930987b1b1dec7f1b7d3972e264755dbb5`.
Its corrected image-0 trace proves literal stores to the addresses above in
the selector-`0x10` emergency path. It explicitly stops short of assigning a
physical effect.

The selected package is
`../selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin`, size
`0x500000`, SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
Its image-0 banner contains the part-like string `S6TUT14FW`. That is a
firmware-package fact, not a readable chip marking, manufacturer datasheet,
or proof of which public memory map the fitted silicon implements.

The owner-photo assessment at
`../../tcon-research/owner-photo-board-map.md`, SHA-256
`93ede258bbb6f5b163466205c0ed828cf0b912ec0a1dacdc9ec7371d07f0f0a3`,
identifies the board/ribbon topology but not the controller silicon. The
relevant T-con area is shielded and no usable MCU marking is visible. The
`RSM1` profile token, board labels, and panel/cable part numbers cannot fill
that identity gap.

## Candidate map 1: Infineon PSoC HVMS — exact one-address collision only

Infineon's official *PSoC 4 HVMS-64K registers reference manual*, document
002-34137 Rev. B, lists a FAULT block at `0x40130000` and names
`FAULT_STRUCT0_DATA0` at exactly `0x40130010`. However, the same register
table places structure 1 at `0x40130100` and its `DATA0` at `0x40130110`, not
at the target's `0x40131010`. The official table does not provide the target
sequence at `0x40131010`, `0x40132010`, and `0x4013400c`.

Primary source:
[Infineon PSoC 4 HVMS-64K registers reference manual, FAULT register table](https://www.infineon.com/assets/row/public/documents/10/57/infineon-psoc-4-high-voltagehvmixed-signalmsmcu-psoc4hvms-64k-registers-reference-manual-additionaltechnicalinformation-en.pdf).

Classification: **rejected as an attribution; retained only as a documented
address collision**. It matches one address but not the multi-address layout,
and there is no positive evidence that the Samsung T-con controller is this
Infineon device. Consequently `0x40130010` must not be called
`FAULT_STRUCT0_DATA0` in this investigation.

## Candidate map 2: NXP RT600 — two block-base coincidences, no multi-address match

NXP's official RT600 product data sheet maps:

* `0x40130000` to the OTP controller; and
* `0x40134000` to FlexSPI and OTFAD registers.

In that same contiguous AHB table, `0x40131000` and `0x40132000` are not
listed peripheral bases. The next named base after `0x40130000` is
`0x40134000`. The table alone does not prove whether the two intervening
target addresses are reserved or internal offsets of the OTP allocation, but
it does not positively reproduce or name the target's four-address layout.

Primary source:
[NXP RT600 product data sheet, AHB peripheral memory map, Table 14](https://www.nxp.com/docs/en/data-sheet/RT600.pdf).

The official product data sheet does not name the exact `0x4013400c` offset,
the other target offsets, or any four-address relationship among them. No
evidence identifies the Samsung controller as an RT600. Classification:
**rejected as an attribution; at most a partial block-base coincidence**.

## Samsung identity search

Samsung Semiconductor's current official display-IC material establishes
only that its panel-DDI/TCON product category exists and includes TV timing
controllers. It does not publish an `S6TUT14` register map or connect the
four addresses above to a current part page. The official current catalog and
an example current TCON product brief are:

* [Samsung Semiconductor Panel DDI / TCON catalog](https://semiconductor.samsung.com/display-ic/panel-ddi/)
* [Samsung S6TST21 TCON product brief](https://download.semiconductor.samsung.com/resources/brochure/S6TST21%20TCON.pdf)

The current catalog is useful only for product-category context. The
S6TST21 brief concerns a different named part and contains no register map;
it cannot be transferred to `S6TUT14FW`. An earlier local search had found a
formerly indexed Samsung `S6TUT14` product URL, but the English path returned
404 and the Japanese path redirected to the general site. A former product
listing without a datasheet or register map is not positive silicon identity.

## Finite search method and stopping point

The search used exact-address queries for each location, pairwise and
four-address combinations, block-base combinations
`0x40130000/0x40131000/0x40132000/0x40134000`, and official-domain searches
for `S6TUT14`, `RSM1`, Cortex-M, and the returned candidate families. Search
results not hosted or authored by the silicon vendor were excluded from the
evidence set. Generic Cortex-M memory-map material was also insufficient:
the processor architecture can place vendor peripherals in this region but
does not assign vendor-specific registers.

The bounded search stops here because the two official exact-address leads
produce incompatible layouts and neither has a chip-identity edge to the TV.
Continuing to search by visual address similarity would increase false-match
risk without closing either required proof gate.

## What this changes, and what would close the gap

The prior software conclusion remains intact: the emergency path issues real
MMIO stores. This assessment prevents a stronger but unsupported physical
claim. In particular, it does not show that selector `0x10` directly turns
the panel off, nor that changing any written value would be safe.

A hardware name becomes defensible only after obtaining both:

1. a positive fitted-silicon identity, such as a legible controller marking,
   authoritative board BOM/schematic, or Samsung document that binds this
   `RSM1` package generation to a specific controller; and
2. that exact device's primary register documentation matching multiple
   target addresses and their offsets/layout.

To bridge further to physical light output, the schematic or other primary
board documentation would additionally need to map the identified output
pin/block to a panel-enable, rail, reset, timing, PWM, or other named signal.
Until then, the smallest honest label for all four locations is **unnamed
MMIO in the selected controller image's emergency path**.
