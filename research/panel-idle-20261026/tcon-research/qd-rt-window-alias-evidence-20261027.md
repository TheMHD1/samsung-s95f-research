# QD RT-window alias / cross-image bridge audit

Recorded 2026-10-27 UTC. This is a bounded offline analysis of the pinned
selected 5 MiB package. No TV, root transport, network, firmware update,
controller command, memory read, emulation, or process action was performed.

## Result

No executable cross-image bridge was recovered. In particular, this audit does
not treat the shared `+0x240a` displacement as an alias.

It does add one concrete boot-time fact: **image 0 itself** has a reset scatter
record which decompresses directly to the fixed `0x47010000` window. Image 1
has a separate reset scatter table which initializes only `0x200...` and
`0x202...` destinations, including the context slot that leads to
`0x20010000`. The established AP_RTP configuration loader is a second,
separate image-0 route into `0x47010000`; its packaged sources are in the
configuration bank, not in image 1.

Those are positive provenance facts for each root, not a copy, mailbox,
mapping-register, boot-selection, or shared-window relation between them.

| Path | Verified packaged destination | How established | Does it bridge images? |
| --- | ---: | --- | --- |
| Image-0 reset scatter record 9 | `0x47010000`, `0x47bc` bytes | table row at file `0x3e3d0` | No; source is image-0 linked VA `0x3ea34` (stored file `0x3ec34`). |
| Image-0 AP_RTP type-4 loader | `0x47012400` / `0x47010000` | established configuration table + successful-path copy body | No; raw package sources are files `0x183800` / `0x183a00`. |
| Image-1 reset scatter record 0 | `0x20000000`, `0x4f8` bytes | table at file `0x5d8a4` | No; its decompressed pointer slot is `0x200004e0 = 0x20010000`. |
| Image-1 RTP event setter | `0x2001240a` on reset-established root | getter + setter dataflow | No image-0 write/copy or mapping edge recovered. |

Therefore the live-image-0 read of `0x4701240a` and the image-1 event write
to `0x2001240a` remain different packaged operations. This audit neither
proves a physical separation nor rules out an external/retained-unavailable
interconnect alias.

## Exact boot records and corrected coordinates

The selected file uses 512-byte prefixes before both vector tables:

```text
image 0 linked VA = file offset - 0x200
image 1 linked VA = file offset - 0x40200
```

Absolute RAM/window values do not receive that bias. The image-0 scatter table
is at stored file `0x3e340..0x3e3ff`; its relevant row is index 9 at
`0x3e3d0`:

```text
source linked VA  0x0003ea34
destination       0x47010000
output size       0x000047bc
handler linked VA 0x0000017c  (the established decompressor)
```

For image 0, a linked source VA maps to stored file by adding `0x200`, so that
record's compressed source begins at **file `0x3ec34`**, within image 0's
stored `0x00000..0x3ffff` interval. This is a concrete source/destination
pair for the fixed window. It is not a claim about what resource the window
represents or about a current controller boot.

Image 1's nine reset scatter destinations are, verbatim:

```text
0x20000000  0x20015000  0x20015f10  0x2020a000  0x20253000
0x20209000  0x20209800  0x20269000  0x200004f8 (zero fill)
```

None is `0x47010000`. Its first record decompresses `0x4f8` bytes to
`0x20000000`; retained decompression evidence establishes the pointer at
`0x200004e0` as `0x20010000`. Its final zero fill starts at `0x200004f8`, so
it does not overwrite that pointer. These facts establish image-1 local root
provenance, not a translation to image 0's address space.

## Checked candidate bridge mechanisms

The audit intentionally checked only concrete, executable/metadata mechanisms
available in the retained file rather than repeating a broad literal search.

1. **Reset / scatter copy.** Each image has its own reset prefix and scatter
   table. Image 0's relevant destination is `0x47010000`; image 1's table has
   no destination in the `0x4701....` range. There is no table record with an
   image-1 stored source and the image-0 window destination.
2. **Packaged configuration copy.** The already recovered AP_RTP entry has
   fixed destinations `0x47012400` (`0x100` bytes) and `0x47010000`
   (`0x2400` bytes). Its payloads begin at files `0x183800` and `0x183a00`,
   outside image 1's stored `0x40000..0x5ffff` interval. This strengthens the
   conclusion that it is an independent configuration route, not an image-1
   installation/copy.
3. **Component prefixes / vector setup.** Image 0 has its nonempty package
   metadata prefix before vector file `0x200`; image 1's prefix through
   `0x401df` is retained as empty/`0xff`/zero metadata before vector file
   `0x40200`. No decoded header schema, secondary-core entry field, mailbox
   descriptor, reset-release register, or remap/window-register write was
   recovered from those prefixes. Prefix shape alone is not a boot mapping.
4. **Direct local event and reader bodies.** The image-1 event setter reaches
   its `0x20010000` root through the scatter-populated `0x200004e0` slot.
   The image-0 reader has a fixed `0x47010000` accessor. Neither complete
   bounded body establishes a call, a copy, or a register transaction to the
   other root.

This does not claim such an edge cannot exist. It could be a hardware
interconnect window, boot ROM behavior, unretained loader, peripheral/DMA
operation, mailbox protocol, or live configuration. It says the selected
executable startup/configuration paths checked here do not provide it.

## Reproducible checker

`qd-rt-window-alias-evidence-20261027.py` pins the whole selected file hash,
both reset/table slice hashes, the exact image-0 fixed-window row, all
image-1 reset destinations, image-0 source coordinate, and AP_RTP source
ranges. It intentionally does not emulate decompression or assert alias
semantics.

```sh
python3 tcon-research/qd-rt-window-alias-evidence-20261027.py
python3 -O tcon-research/qd-rt-window-alias-evidence-20261027.py
```

Both runs pass on the retained file. The checker is bounded: it is evidence
for these explicit table/source facts, not a whole-firmware absence proof.

## Next valid discriminator

A positive bridge needs an artifact which relates **both** address spaces, not
another matching structure offset. The smallest useful examples are:

* a decoded boot/interconnect register write that maps `0x47010000` to an
  image-1-visible resource or releases image 1 with such a mapping;
* a loader/DMA/mailbox descriptor whose source/destination ranges explicitly
  include one `0x2001....` and one `0x4701....` range; or
* a safe, independently reviewed live read-only memory/window observation
  bound to the selected running image and boot.

Until one exists, the image-1 RTP event is not a proved writer of image-0's
RT selector bit and is not a basis for changing a threshold or controller
state.

## Provenance

| Artifact | SHA-256 |
| --- | --- |
| selected 5 MiB package | `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0` |
| image-0 reset prefix, file `0x544..0x56c` | `ab26f68c73c5451c7a615f64d0e2a4241000bba3c50e6f1f21eabaacebec8162` |
| image-0 scatter table, file `0x3e340..0x3e400` | `3f09781583f48d9b429fe8438b06bbd26196b3f673c79e6a2cf7adde356b612d` |
| image-1 reset prefix, file `0x40568..0x4058c` | `77428a5791705e4b966092c95715a84b617dfd7f414902ff35ae2089d92c93d6` |
| image-1 scatter table, file `0x5d8a4..0x5d934` | `73eaacb3784da627c734f46dceeca569c403209c3e3e969d813f2bf13d09caef` |
| image-0 fixed-window source prefix, file `0x3ec34..0x3ec74` | `aefd6168b636ab121e9fdd8e449d248ccbc36a7f2d75d4bcc8a42ca74a8d4ca7` |

Prior context deliberately retained rather than overwritten:
`qd-rtp-image-handoff.md`, `qd-image1-context-initialization.md`,
`qd-secondary-core-window-loader.md`, and `qd-config-rtp-table-load.md`.
