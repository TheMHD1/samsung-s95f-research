# QD secondary-component / `0x4701` window: bounded loader audit

Recorded 2026-10-27 UTC. This is an offline analysis of already copied package
and module bytes. It made no TV, root, network, controller, USB, SSB, flash,
or process call. In particular, it does **not** select, start, validate, or
modify either embedded component.

## Result

The retained evidence establishes two embedded Cortex-M components and a
host-side whole-file transport, but does **not** establish the missing bridge
between them:

* Component 0 has a `0x200`-byte container prefix, a vector table at file
  `0x200`, and an image-0 accessor returning the fixed address `0x47010000`.
  Its recovered RT consumer consequently reads `0x4701240a`.
* Component 1 starts at file `0x40000`, has its own `0x200`-byte prefix and
  vector table at file `0x40200`. Its reset scatter sequence puts
  `0x20010000` in RAM slot `0x200004e0`; the recovered RTP setter therefore
  targets `0x2001240a` on that reset path.
* The host CAD provider can read and stream the **entire** 5 MiB file in an
  update-capable SSB path. Its bounded body does not inspect either component
  prefix, parse `0xa5a55a5a`, or identify an image-1 load/start command.

Thus the numerically different addresses, `0x4701240a` and `0x2001240a`, are
not a proven shared-state handoff and are not a proven separation either. A
processor-local alias/window, boot ROM action, later loader, DMA, or mailbox
would require positive mapping/activation evidence. None was recovered in the
bounded sources below.

## Pinned inputs and coordinate convention

| item | SHA-256 |
| --- | --- |
| selected 5 MiB package `overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin` | `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0` |
| image-1 scatter analysis | `e885c17d2d1092fd82d761ed4c7b1cd1627bcfa921bfba8027b515918da39c66` |
| selected-package content map | `e2dcdd78576032d2a250d388cbc55f40950f961238ce426bd5c9b961a4a40beb` |
| CAD provider analysis | `d7ab562a52f2a33d5c5446a2ceffccc5afe486f4bd7d53fc828060e580e2a575` |

The canonical mappings are important here. Both component prefixes are data,
not linked address zero:

```text
image 0 linked VA = stored file offset - 0x00200
image 1 linked VA = stored file offset - 0x40200
```

The image-0 reset vector `0x345` maps to stored code `0x544`; image-1 reset
vector `0x369` maps to stored code `0x40568`. Relative branch walks wholly
inside either component remain valid when described in stored coordinates.
An absolute function pointer or a literal must use the mapping above.

## Component prefixes: a role question, not a validity conclusion

The first 0x200 bytes of component 0 begin with little-endian
`0xa5a55a5a` (stored bytes `5a 5a a5 a5`) and carry text such as `241230A`,
`SDCAD`, and `mcu_ata`. Component 1's first word at stored `0x40000` is
`0xffffffff`; its following pre-vector metadata area through `0x401df` is
zero in this selected file, while its vector at `0x40200` and coherent reset
startup are present.

That contrast is useful evidence that the two prefixes do not have identical
contents. It does **not** show that component 1 is invalid, inactive, a backup,
or a secondary core. The retained host consumer supplies no recovered schema
for either prefix, no header length, no footer interpretation, and no validator
that compares either magic value. In particular, the provider's selected
bounded CFG contains neither byte order of the component-0 magic as a literal;
that is a bounded code fact, not proof that no other loader validates it.

## Exact image-local state roots

### Image 0: fixed `0x4701` root

The coherent stored image-0 accessor is at `0xf194..0xf19b` (linked
`0xef94..0xef9b`):

```text
linked 0xef94  ldr r0, [pc, #0]
linked 0xef96  bx  lr
stored 0xf198  .word 0x47010000
```

The recovered RT check at stored `0x216d4` (linked `0x214d4`) calls this
accessor, adds `0x240a`, loads the byte, and tests bit 0. Its effective
address is therefore `0x4701240a`. This access establishes a fixed literal
in packaged image-0 code; it does not name the underlying bus, RAM, register
bank, interconnect mapping, or another processor's view.

There are two other aligned raw `0x47010000` words in the image-0 stored range
(`0x3ce50` and `0x3e3d4`). The latter has one syntactic Thumb literal load at
stored `0x3e322`, but no containing entry/function or cross-component call was
recovered from that data-heavy tail. They must not be upgraded from raw words
to an activation or alias mechanism.

### Image 1: reset-populated RAM root

The separately documented image-1 scatter loader decompresses a record to
`0x20000000..0x200004f7`. Its output at `0x200004e0` is little-endian
`0x20010000`; the following zero-fill begins at `0x200004f8`, so it does not
erase that word. The image-1 getter at linked `0x38fc` loads that slot, and the
RTP setter uses its result plus `0x240a`, giving `0x2001240a` for the recovered
reset path.

This proves image-1's own startup dataflow. It does not say whether a physical
window maps that address to image-0's `0x47010000`, or whether either image is
currently executing on the TV.

## Bounded search for an activation or alias edge

I checked the positive mechanisms that the retained inputs can actually
support:

1. **Image-0 direct fixed-base access.** The only recovered coherent
   `0x47010000` accessor is the one above. It performs no image-1 range test,
   image-1-vector write, remap register write, or branch to image-1 linked
   code in its complete short body.
2. **Component-boundary literals.** The selected package contains component 1
   at stored `0x40000..0x5ffff`, but a raw occurrence of `0x40000` or
   `0x60000` is not treated as code evidence: those values occur frequently in
   tables and data. The bounded instruction/literal examination recovered no
   coherent image-0 function that consumes the `0x40000` component header and
   then programs a secondary-core entry, VTOR, reset, or mapping register.
3. **Configuration-copy text.** Image 0 contains strings `Config_CopyData_To_MCU_v5`,
   `Config_CopyData_To_MCU`, `Config_CopyData_To_IP_v5`,
   `Config_CopyData_To_IP_LUT`, `Config_CopyData_DDR_To_RTL`, and
   `Config_CopyData_DDR_To_MCU` at stored `0x3cf3b..0x3cfba`. Several are
   referenced from image-local code (for example, the `To_IP_v5` string is a
   literal at stored `0x62f0` used by code at `0x6098`, `0x62cc`). These names
   support the existence of copy-related diagnostics, but their selected
   callers do not prove a copy from file `0x40000`, a destination `0x470...`,
   image-1 execution, or a shared window. Names alone are deliberately not
   used as a bridge.
4. **Host package transport.** The pinned `sdp_pqe_frc.ko` provider has an
   update path that whole-file reads a 5 MiB CAD asset and, for commands
   `0x30..0x33`, sends data via SSB in chunks with a 12-byte target/address/
   size envelope. Its recovered body neither parses this package's component
   boundaries nor decides which embedded image should run. It is write-capable
   and not a diagnostic interface.

This is a finite search of these direct, source-supported possibilities. It is
not a claim that no bridge exists anywhere: computed addresses, indirect calls,
boot-ROM behaviour, peripheral/SoC mapping, DMA, an unretained loader, or a
later controller action remain outside it.

## What would actually close the question

Useful evidence would need to demonstrate at least one concrete relation, such
as a loader source range including stored `0x40000..0x5ffff` and a destination
or entrypoint; a processor remap/window register setting tying `0x47010000` to
the image-1 RAM region; or a mailbox/DMA operation whose source and destination
ranges include both roots. A second raw matching offset, an RTP string, or a
component header difference would not suffice.

No conclusion here identifies a safe setting, a fault cause, or a recovery
action. It also does not alter the key constraint from the Apps-visible control:
the historical monitor latch was already set while the picture was visible, so
the static latch alone cannot be assigned as a later blackout cause.
