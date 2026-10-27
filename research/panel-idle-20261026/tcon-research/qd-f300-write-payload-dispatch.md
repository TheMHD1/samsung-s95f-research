# Image-0 `F3 00 ... 0x128` payload path

## Scope

This is an offline trace in the selected 5 MiB QD profile only.  It resolves
the distinction left open by the adjacent selector-reader report: an observed
two-message I2C transaction has a six-byte header followed by a four-byte
write payload, whereas the earlier `F300` open-register routine is a reader.

Input is `overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin`,
SHA-256 `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
Image-0 linked addresses use `file = linked + 0x200`.  No TV, root, network,
I2C, firmware, or controller call occurred.

## Receive framing and payload assembly

The image-0 bus-event state machine is linked `0x128c4..0x12bbe` (file
`0x12ac4..0x12dbe`; 762-byte slice hash
`5b2cbcbac9d03ba3a1dd175568a5cbc8cb7e74a75264a17fd354833d1f4e9c85`).
It reads the current bus byte from its object at `+0x28`.

The reviewed payload-assembly slice, linked `0x12966..0x12a0a` (file
`0x12b66..0x12c0a`), has SHA-256
`4457659f3fa29d596ab49fa4dc789bd841cb519401c2dd3db82f98b2b4123611`.

Its receive branch uses the command-byte count at RAM `0x200008fc` and the
mode byte at `0x20000910`:

| received byte positions | code | RAM result |
| --- | --- | --- |
| 0–1 | `0x12966..0x12988`, while count `< 2` | shift/OR into halfword `0x200008c8`; `f3 00` becomes `0xf300`. At count zero it also clears `0x200008cc` and classifies the leading byte. |
| 2–5 | `0x129a4..0x129c6`, while count `< 6` and mode is zero | shift/OR into word `0x200008cc`; `00 00 01 28` becomes `0x00000128`. |
| 6–9 | `0x129cc..0x12a04`, once count is at least six | shift/OR each byte into word `0x20000904`; a local modulo-four counter at `0x20000908` calls the write dispatcher after the fourth byte. |

At the completed fourth payload byte, registers are explicitly loaded as:

```text
129f8  ldr r0, [literal -> 0x20000904] ; r2 = BE-assembled payload
129fa  ldr r2, [r0]
129fc  ldr r0, [literal -> 0x200008cc] ; r1 = selector
129fe  ldr r1, [r0]
12a00  ldr r0, [literal -> 0x200008c8] ; r0 = command halfword
12a02  ldrh r0, [r0]
12a04  bl  2c5f4
```

Therefore the retained state machine itself maps the complete observed shape
`f3 00 00 00 01 28` followed by BE32 scalar to
`write_dispatch(0xf300, 0x128, scalar)`.  This does not rely on a host-side
name for selector `0x128`.

## `F300` write dispatch and selector `0x128`

`0x2c5f4` preserves its three incoming words.  For command `0xf300`, it
passes selector in `r0` and scalar in `r1` to `0x2c71c`:

```text
2c5fc  cmp.w r4, #0xf300
2c602  mov   r1, r6
2c604  mov   r0, r5
2c606  bl    2c71c
```

Write ingress linked `0x2c5f4..0x2c642` (file `0x2c7f4..0x2c842`) hashes to
`d16e6fc80b238ce85265229a7d328548e0ef614a9544e233f6973ee4272a4b49`.

`0x2c71c` has entry gates before its selector table:

* a literal-backed byte at `0x200008e8` equal to `1` immediately returns;
* value `2` enters the `0x2c762..0x2c778` special gate, where nonzero
  halfword `[getter(0xe678)+6]` permits only selector `0x180`;
* otherwise it dispatches aligned selectors below `0x31c` through its table.

Those values have not been semantically named here.  They are real static
conditions, so successful Linux transfer must not be equated with reaching
the selected store.

For `0x128`, table index `(0x128 >> 2)-9 = 0x41` selects table word at linked
`0x2c8b8 = 0x4e2`; added to the final Thumb PC `0x2c7b4`, it targets
`0x2cc96`:

```text
2cc96  ubfx     r0, r4, #0, #0xa
2cc9a  strh.w   r0, [r5, #0xa6]
2cc9e  b        2cf4e
2cf52  b        2c75e                   ; function return
```

Here `r4` is the scalar and `r5` is from `BL 0xef9c`; that getter's literal
is `0x2000d71c`.  Thus, after the gates, the scalar's low ten bits are stored
as a halfword at `0x2000d7c2`, and this selected path returns.  The separately
recovered `F300` read leaf for selector `0x128` reads the same halfword and
extracts the same low ten bits.  The field is consequently a controller RAM
request/state field in this packaged image; its downstream hardware consumer
is not recovered by this trace.

The selector-entry slice linked `0x2c71c..0x2c7b2` (file
`0x2c91c..0x2c9b2`) hashes to
`150862c6cbfb1e403bccf967f6ab8267356552e9ecd47e46eb30ce60386aca3c`; the
`0x128` leaf linked `0x2cc96..0x2cca0` (file `0x2ce96..0x2cea0`) hashes to
`288b05c9e05c206ce67df2860890dfde42fab4049e07d7e8b4c121b3d3c12bf7`.

## RT, image-1, and hardware limits

The complete receive/write slice above has no recovered direct branch or
memory reference to image-0 RT address `0x4701240a`, the common-error entry
linked `0xb660`, or image-1's separately inferred `0x20010000 + 0x240a`
object.  The write dispatcher does acquire the `0x47010000` root in its
prologue, but selector `0x128` uses the other root (`0x2000d71c`) and its leaf
only performs the `+0xa6` halfword store.

This proves a static controller-RAM write path for the exact wire framing. It
does **not** prove that the selected profile was executing, that an observed
transaction passed all gates, that a later consumer drove hardware, or that a
particular scalar changes brightness, triggers RT protection, or repairs a
black panel. The separate profile configuration-table work may establish
other initialization relations, but is not used as an inferred edge here.
