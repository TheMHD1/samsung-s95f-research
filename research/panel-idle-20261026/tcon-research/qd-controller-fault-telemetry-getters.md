# F3:80 controller fault-telemetry getter audit

Recorded 2026-10-27 UTC. This is a bounded, offline re-audit of the selected
5 MiB profile only. It made no TV, root, controller, I2C, MMIO, or target
command call.

## Result

No new positive F3:80 route exports RT history, subtype, index, threshold, or
saved count beyond selector `0x08`. The finite selector table already excludes
the recovered RT EEPROM fields. Two concrete, non-RT getter paths are retained
to make the negative boundary falsifiable rather than to propose a query:

| selector | corrected linked VA / file offset | direct result source | fault-telemetry conclusion |
| --- | --- | --- | --- |
| `0x08` | table VA `0x21ff8..0x220e9` / FILE `0x221f8..0x222e9`; case loads common object `+0x10` | 16-bit current common-error selector | existing positive route only; it yields current `0x0010`, not subtype/history/threshold |
| `0x03` | same table, its direct case | common object `+0x158` 32-bit RAM word | source gives no RT/history label or connection to the RT EEPROM fields; not a new fault-telemetry export |
| `0x10..0x14` | same table → VA `0x10c04` / FILE `0x10e04` | one of five words at RAM `0x2000b44c` | bounded RAM reads, but no decoded edge to RT action/check/history; not classified as subtype/index/threshold |

The image-0 mapping is `FILE = VA + 0x200`. The profile's full SHA-256 is
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
The table bytes at corrected FILE `0x221f8..0x222e9` have SHA-256
`7b7038d870a46b9f897a44d3368618a13a61025ed86a9c5c61b6dccddba23aa0`
when expressed in the prior report's linked interval; the address correction
does not change those bytes.

The table's selector bound is `0x23`; only `0x00..0x22` are valid. It has 35
entries. The already-resolved selector `0x09` is explicitly read-to-clear and
therefore is not a neutral fallback. Selectors `0x20..0x22` directly read
undocumented MMIO and are also not promoted as harmless diagnostics.

## RT exclusion

The recovered RT fields are image-0 object offsets `+0x2466`, `+0x2484`,
`+0x24aa`, and `+0x24ac`. The finite table and its direct selector callees do
not access any of them, do not call the EEPROM helper `VA 0x9948`, RT check
`VA 0x99e8`, RT action `VA 0x9b68`, or common-error entry `VA 0xb860`.
Thus no numeric selector is proposed. This does not prove the fields are
absent in the running controller or that another firmware interface cannot
exist; it only closes this bounded F3:80 getter-table route.

Accepted duty `207` and accepted status `0x10` with raw-kernel corroboration
remain observations from other work. They do not identify the RT subcause,
threshold, subtype, or history value.

## Provenance

This audit relies on the existing exact-table resolution in
`qd-profile-readonly-rt-state-selectors.md` and the load-address correction in
`qd-firmware-load-address-erratum.md`. It adds no getter implementation,
arbitrary selector, or execution recommendation.
