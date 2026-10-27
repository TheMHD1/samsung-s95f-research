# Selected-profile read-only selectors for RT state

Recorded 2026-10-27 UTC. This is a bounded offline analysis of the already
retained selected QD profile. It made no TV, root, network, controller, I2C,
EEPROM, MMIO, getter, or display call and changed no earlier evidence.

## Result

The exact packaged image has **35 valid entries** in its `F3:80` getter table
(selectors `0x00..0x22`). None of those entries reads the RT EEPROM state at
the image-0 object offsets `+0x2466`, `+0x2484`, `+0x24aa`, or `+0x24ac`.
There is therefore no source-backed selector in this table that returns the
saved RT signature flag, enable/gate, threshold byte, or saved count.

Selector `0x08` remains the sole recovered RT-specific result: it returns the
current common error-selector halfword at `common_object+0x10`. That is the
field the packaged RT path writes with `0x0010`; it is not the four-field
EEPROM history record.

One other table entry is demonstrably stateful. Selector `0x09` builds a
generic seven-bit status word and, when one of its input halfwords is nonzero,
sets result bit `0x20` and **clears that input halfword**. It is not a
read-only diagnostic. No recovered instruction connects that consumed flag
to the RT EEPROM fields.

The table also exposes generic temperatures/measurements, RAM words, and
three MMIO-derived values. Those may be useful for other questions, but the
code does not map them to saved RT history. The MMIO reads cannot be called
side-effect-free without peripheral documentation. Consequently this report
does not propose another controller query: the table contains no finite,
source-backed extra read that distinguishes saved RT history from the
already observed current selector `0x10`.

This is a negative result over one exact table and its selector-specific
callees, not a proof that no diagnostic exists anywhere in controller
firmware.

## Inputs and identity

| Input | Size | SHA-256 |
| --- | ---: | --- |
| `overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin` | 5,242,880 | `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0` |
| `qd-selected-profile-content.md` | 17,350 | `e2dcdd78576032d2a250d388cbc55f40950f961238ce426bd5c9b961a4a40beb` |
| `qd-profile-rt-status-wire.md` | 11,365 | `6c532e2ad8a48041cf83ebddfa42af1282019d14169902b47e621f6a1c237f6e` |
| `qd-protection-additional-telemetry.md` | 13,543 | `ba005d7e5b6508d1ed68983e1a49100f7e7dc161452a51b0f7e7344962d4e6a2` |

The selected asset's first embedded Thumb image is linked at zero, so the
image-0 addresses below are also file offsets. This report does not establish
that these packaged bytes equal the firmware currently installed in the
controller.

The preceding wire report already proves the exact packet parser, the
`F3:80` open-register dispatch, four-byte big-endian response serialization,
and selector `0x08`'s non-clearing read of `common_object+0x10`. They are not
re-derived here.

## Exact table bounds

The selector function is `0x21ff8..0x220e9`, 242 bytes, SHA-256
`7b7038d870a46b9f897a44d3368618a13a61025ed86a9c5c61b6dccddba23aa0`.
At `0x2200a` it compares the selector with `0x23`; `BHS 0x220e6` returns zero
for every selector at or above that bound. Valid values enter a 35-byte Thumb
`TBB` table at `0x22012`. Its exact bytes are:

```text
1216191c6a2124272a2e31343945486a4a4b4c4d4e546a576a6a5a6a6a6a6a6a606366
```

There is no caller-supplied address or length in this getter. Each valid case
returns one 32-bit word; the already-proved transmit path emits exactly four
bytes, most-significant byte first. Eleven selectors return literal zero;
the remaining 24 cases are enumerated below. This accounts for all 35 valid
table entries.

## Complete selector inventory

| Selector(s) | Exact case behavior | Four-byte result / state effect |
| --- | --- | --- |
| `00`, `01`, `05` | literal `0xabababab` | `ab ab ab ab`; no state access |
| `02` | `0x10dd0` reads the float at `0x20000d3c`, converts and tags it | computed 32-bit measurement; no store in the recovered body |
| `03` | loads `common_object+0x158` | four bytes from that RAM word; no store |
| `04`, `0e`, `0f`, `16`, `18`, `19`, `1b..1f` | literal/default zero | `00 00 00 00`; no state access |
| `06` | literal `0xffffffff` | `ff ff ff ff`; no state access |
| `07` | `0x220f0` packs six ASCII digit nibbles from the pointer returned at `0x6610` | computed four-byte value; no store |
| `08` | loads `common_object+0x10` with `LDRH` | `00 00 HH LL`; non-clearing current error selector |
| `09` | calls `0x1006c` and builds bits `0x01..0x40` from several inputs | `00 00 00 xx`; **clears one nonzero input halfword at accessor-`0xf6f0` object `+0x46`** |
| `0a` | `0x24ff0 -> 0x2801c` loads two words beginning at `0x20000480`; the first is returned | four bytes from the first RAM word; no store |
| `0b` | loads byte `0x20000cb0`, XORs it with one | zero-extended/XOR result; no store |
| `0c` | calls `0x27870` twice and packs portions of the returned halfword | computed four-byte value from `0x20000c1e`; no store |
| `0d` | `0x10e40` computes and clamps a ratio to at most 100 | `00 00 00 xx`; no store in the recovered body |
| `10..14` | `0x10c04(selector-0x10)` reads one of five words at `0x2000b44c` | four bytes from the selected RAM word; no store |
| `15` | `0x31f8c` tests accessor-`0xe878` object halfword `+0x264` | `00 00 00 00` or `00 00 00 01`; no store |
| `17` | `0x38e7c` reads accessor-`0xe988` object halfword `+0xe8` | zero-extended halfword; no store |
| `1a` | reads accessor-`0xf194` object halfword `+0x389a` | zero-extended halfword; no store |
| `20` | `0xfed4` reads `0x58300254`, extracts bits `8..12` | zero-extended five-bit value; no store in the getter |
| `21` | reads 32-bit MMIO `0x58300258` | raw four-byte register value; no store in the getter |
| `22` | reads 32-bit MMIO `0x5830025c` | raw four-byte register value; no store in the getter |

The table-level case labels are functional descriptions of exact
instructions, not recovered vendor names. In particular, a RAM or MMIO value
is not labelled as an RT counter merely because it is returned by this table.

### Selector `0x09` is read-to-clear

The selector-`0x09` body `0x1006c..0x101a7` is 316 bytes, SHA-256
`24f30bf63c8dbfd8fbeb0a8410d07057215b126b5125b91bf0c375615e971b0c`.
It reads several thresholds and status fields and accumulates result bits in
`r4`. The relevant sequence is exact:

```text
0x10166  LDRH  r0,[r8,#0x46]
0x1016a  CBZ   r0,0x10176
0x1016c  ORR   r4,r4,#0x20
0x10170  MOVS  r0,#0
0x10172  STRH  r0,[r8,#0x46]
```

`r8` came from accessor `0xf6f0`. Stack stores earlier in the function are
temporary; `0x10172` is a persistent object write. Thus the entry consumes a
latched input as part of reading it. The source field is not any of the four
RT EEPROM offsets and its semantic name was not recovered. It cannot be used
as a non-destructive RT-history discriminator.

### Direct MMIO getters are not declared harmless

Selectors `0x20..0x22` contain only loads and arithmetic in their local
bodies. That proves there is no explicit write in those getter instructions;
it does not prove that reads from `0x58300254..0x5830025c` lack
read-to-clear/acknowledge behavior. No matching peripheral specification was
recovered. They remain unknown-effect MMIO reads and are not proposed as
diagnostics.

## RT-field exclusion

The four saved-RT fields are source-bound by the earlier content report:

| Object offset | Proven use in the packaged image |
| --- | --- |
| `+0x2466` | signature/check-complete flag set by the EEPROM check; later tested by the RTP fast-mode correction path |
| `+0x2484` | gate tested before the two RT-protection entries |
| `+0x24aa` | threshold/history byte compared with the EEPROM bytes |
| `+0x24ac` | saved EEPROM count/value written by the check and incremented by the RT action |

Every one of the 35 table entries was resolved to its target, and every
selector-specific call target used to produce the returned word was decoded
through its direct value source. None uses offsets `0x2466`, `0x2484`,
`0x24aa`, or `0x24ac`. The computed cases use the value sources listed in the
inventory; none calls the EEPROM helper `0x9948`, the RT check `0x99e8`, the
RT action `0x9b68`, or the common error entry `0xb860`.

This is strong enough to exclude a direct getter-table route to those four
fields in this exact packaged image. It does not exclude an indirect
correlation between unrelated measurements and an RT event, nor does it
assign undocumented meaning to generic RAM/MMIO values.

## Diagnostic consequence and limits

There is no justified additional controller selector to sample for saved RT
history. The existing selector `0x08` answers a narrower question: the
current common error-selector word. The EEPROM signature/gate/threshold/count
remain internal to the packaged firmware in the recovered paths.

Host-side counters and cached status described in
`qd-protection-additional-telemetry.md` can provide separately timed policy
context, but they do not expose these controller fields. A direct controller
memory read, arbitrary open-register experiment, EEPROM transaction, or
controller write would cross the bounded interface established here and is
not synthesized or recommended.

Nothing in this report proves current-flash identity, electrical fault cause,
physical panel state, RT threshold units, persistence across reset, or a safe
recovery action. It also does not turn the absence of a table entry into
evidence that saved RT history was absent during the owner's incident.
