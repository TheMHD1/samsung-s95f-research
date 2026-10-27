# `F3:0x128` controller boundary — static profile result

## Scope and corrected address map

This is an offline examination of the selected QD profile, not a device
experiment. Input: `overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin`,
5,242,880 bytes, SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.

Image-0 addresses below are linked addresses, with `file = linked + 0x200`.
Image 1 has a distinct `file = linked + 0x40200` map. This corrects prior
raw-file labels and does not identify the two images as one address space.

The bounded source slices used here are pinned independently of the whole
file: dispatcher file `0x21824..0x21876` (82 bytes,
`5f9a3da21a8aff22610a23c58b4e79bc20836d4111a456ccb393044616abacbe`),
selector-handler prologue `0x2194c..0x21992` (70 bytes,
`47585f141e91dbc5fdd5a7bc4cb56e7cbbd4c836be72ab86f296e6e125bb8943`),
the selected leaf `0x21e30..0x21e3a` (10 bytes,
`37a7239da81cda82bcd8dd1575a598c015bc4b4fa5848a79e1a53618007a9f9f`),
and the `r4` getter `0xf19c..0xf1a4` (8 bytes,
`84f93c6639be7fc7a21229eead9d80b31746059a46741f4973167e2b14ff0b47`).

The host-side [qd-content-duty-policy.md](qd-content-duty-policy.md) records
construction of `0xf30000000128`; that motivated this inspection. It does
not prove controller packet framing, delivery, acceptance, or a physical
brightness effect.

## Exact image-0 `F300` selector route

Linked `0x21624` (file `0x21824`) compares its first argument with `0xf300`.
On equality it calls `0x2174c` with its selector argument, then calls
`0x5924` with `(0xf300, selector, returned-value)`:

```text
2162c  cmp.w r4, #0xf300
21632  mov   r0, r5
21634  bl    2174c
21638  mov   r6, r0
2163a  mov   r2, r6
2163c  mov   r1, r5
2163e  mov   r0, r4
21640  bl    5924
```

`0x5924` sums the four bytes of each of those three words and stores one
checksum byte through a literal-backed global. It does not write the selector
or returned value into an RT object.

`0x2174c` receives only `r0` (selector). For `0x128`, its table index is
`(0x128 >> 2) - 9 = 0x41`. At `0x217a6..0x217ac`, the computed table entry is
linked `0x218b4 = 0x00000480`; added to Thumb PC `0x217b0`, this reaches
linked `0x21c30`:

```text
21c30  ldrh.w r0, [r4, #0xa6]
21c34  ubfx   r0, r0, #0, #0xa
21c38  b      2178e
```

The handler assigned `r4` from `BL 0xef9c` at `0x21758`. The getter's literal
is `0x2000d71c`, so this case returns the low ten bits of the halfword at
`0x2000d7c2`. The selected leaf has no store.

## Scalar and RT boundary

The reported `F3 00 00 00 01 28` prefix plus four-byte scalar cannot be
equated with this two-argument controller reader from the retained code.
There is no scalar argument at this call boundary: selector `0x128` returns a
ten-bit RAM field. A transport/framing route that could consume a scalar
elsewhere remains unresolved.

The exact recovered slice also has no direct branch or memory reference to:

| Separate location | Evidence | Relation to `F300:0x128` |
| --- | --- | --- |
| image-0 RT bit | known effective address `0x47010000 + 0x240a = 0x4701240a` | the selected leaf reads `0x2000d7c2` instead. |
| image-0 common-error routine | linked `0xb660` (file `0xb860`) | no call from `0x21624 → 0x2174c → 0x21c30`. |
| image-1 event object | separate analysis has a runtime pointer from `0x200004e0`, with one observed target `0x20010000` | no image-1 transition, call, or handoff in this slice. |

The wider `0x2174c` prologue also calls getter `0xef94`, whose literal is
`0x47010000`, but saves it in `r8`; the `0x128` leaf uses `r4` from the
different `0xef9c` getter. That is not an RT connection. The separate
[qd-secondary-core-window-loader.md](qd-secondary-core-window-loader.md)
likewise found no positive alias/loader proof between `0x4701240a` and
image-1's analogous `0x2001240a` offset.

The independently queued configuration-table analysis may establish how
profile data targets `0x47012400`; it is deliberately outside this selector
trace and does not change the no-direct-edge result above.

## Conclusion and limits

In this exact profile, the recoverable image-0 `F300:0x128` route is a
read/response-style ten-bit RAM-field lookup, not a recovered drive-level
write, RT-protection setter, controller reset, or image-1 event handoff.
That does not rule out a different scalar-consuming transport route.

Therefore the differing HDMI value sequences are observational records only;
they do not establish that a particular `0x128` scalar caused a blackout or
recovery. No threshold, drive-level, RT bit, or recovery policy is derived.
No TV, root, network, controller, or firmware action was performed.
