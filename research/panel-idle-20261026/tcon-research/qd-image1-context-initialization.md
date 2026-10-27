# QD image-1 context initialization and corrected load mapping

Recorded 2026-10-27 UTC. This is bounded offline analysis of the already
copied selected QD profile. It made no TV, root, network, controller, flash,
EEPROM, USB, UART, emulation, or process call. It does not propose a value to
change.

## Result

The image-1 context slot has a positive packaged-startup provenance. The
reset-time scatter loader decompresses a data block to RAM
`0x20000000..0x200004f7`; bytes at destination offset `0x4e0` are exactly
`00 00 01 20`, little-endian pointer **`0x20010000`**. Thus the getter loads:

```text
*(uint32_t *)0x200004e0 == 0x20010000
```

on the recovered reset/scatter path. The later RTP event store therefore uses
image-1 address **`0x2001240a`**, while image 0 uses `0x4701240a`. Those are
numerically distinct addresses in independently linked image address spaces;
no alias between them is established. Numeric inequality is not proof that
they reach physically distinct storage: an interconnect/window mapping could
in principle expose one resource at different addresses to separate MCUs.

This also corrects the packaged images' file-to-linked-address convention.
Each component has a `0x200`-byte container prefix before the vector table:

| component | component start | vector / linked VA 0 | canonical mapping |
| --- | ---: | ---: | --- |
| image 0 | file `0x00000` | file `0x00200` | linked VA = file offset - `0x200` |
| image 1 | file `0x40000` | file `0x40200` | linked VA = file offset - `0x40200` |

Earlier reports treated the component starts as linked VA zero. Their
relative branch/control-flow walks and RAM/MMIO literals generally survive a
constant `-0x200` relabel, but their linked code addresses are high by
`0x200`. An absolute Thumb code pointer must be translated to stored bytes by
adding the component's `0x200` prefix. This matters materially for previously
decoded absolute USB callback pointers; it is not merely cosmetic.

These are packaged-byte conclusions. They do not prove which image is
installed or executing on the TV, nor that live RAM still contains its reset
value.

## Pinned input and prior boundary

| item | SHA-256 |
| --- | --- |
| `overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin` (5,242,880 bytes) | `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0` |
| prior handoff report `qd-rtp-image-handoff.md` | `a8ee5d8571a8ee782dca561cb1bf01fb99c377b6a4495b98bc8da53061a9246f` |
| prior image-1 RTP report `qd-profile-rtp-image1.md` | `90230a772b149d3f56c5beecf9ebfd3546a5e488d684d6ebcd3fa97e2b502c87` |
| prior container report `qd-selected-profile-content.md` | `e2dcdd78576032d2a250d388cbc55f40950f961238ce426bd5c9b961a4a40beb` |

The prior handoff report correctly refused to equate the two roots, but left
the writer of `0x200004e0` unresolved and used stored component offsets as
linked addresses. This report closes the reset-time writer and supersedes
that address convention without editing the frozen prior files.

## The vector tables prove the `0x200` load displacement

Image 1's vector begins at file `0x40200`, with initial SP `0x20020000` and
reset Thumb pointer `0x00000369`. Clearing the Thumb bit gives linked reset VA
`0x368`. The coherent reset body is at file:

```text
0x40200 + 0x368 = 0x40568
```

and is:

```text
VA 00368  ldr r0,[pc,#0x18]   ; literal 0x0000dc01
VA 0036a  blx r0              ; call VA 0x0000dc00
VA 0036c  ldr r0,[pc,#0x18]   ; literal 0x00000141
VA 0036e  bx r0               ; enter scatter loader VA 0x00000140
```

The 36 stored bytes at file `0x40568..0x4058b` have SHA-256
`77428a5791705e4b966092c95715a84b617dfd7f414902ff35ae2089d92c93d6`.
By contrast, decoding file `0x40368`—the old convention—lands in the middle
of the scatter dispatcher (`tst r3,#1`), not at a callable reset entry.

Image 0 independently has the same layout. Its vector is at file `0x200`, its
reset pointer is `0x345`, and linked VA `0x344` is coherent at file `0x544`.
File `0x344` instead lands inside its scatter code. This independent second
component rules out treating the image-1 displacement as a coincidental
instruction alignment.

The first image-1 reset call at VA `0xdc00` updates the Cortex-M CPACR through
literal `0xe000ed88`; it does not touch `0x200004e0`. Reset then branches to
VA `0x140`, so scatter initialization precedes the C/runtime application
entry.

## Exact scatter table and order

The scatter dispatcher at linked VA `0x140..0x1f2` is stored at file
`0x40340..0x403f3` (180 bytes, SHA-256
`cf4020e3cdb1b314345608c30d00c1efa1e0ad4cf87bf8e54aa92f568fcb6330`).
At VA `0x148` it forms a table base and end from two PC-relative words:

```text
table start = 0x174 + 0x1d530 = 0x1d6a4
table end   = 0x174 + 0x1d5c0 = 0x1d734
```

The resulting nine 16-byte records are stored at file
`0x5d8a4..0x5d933` and have SHA-256
`73eaacb3784da627c734f46dceeca569c403209c3e3e969d813f2bf13d09caef`.
Each record is `(source linked VA, destination RAM, output size, handler VA)`:

| source VA | destination | output bytes | handler |
| ---: | ---: | ---: | ---: |
| `0x1d860` | `0x20000000` | `0x4f8` | decompressor `0x17c` |
| `0x1d95c` | `0x20015000` | `0xb50` | decompressor `0x17c` |
| `0x1d974` | `0x20015f10` | `0xb50` | decompressor `0x17c` |
| `0x1d98c` | `0x2020a000` | `0x2d30` | decompressor `0x17c` |
| `0x1d9e8` | `0x20253000` | `0x223c` | decompressor `0x17c` |
| `0x1da30` | `0x20209000` | `0x6c0` | decompressor `0x17c` |
| `0x1da40` | `0x20209800` | `0x6c0` | decompressor `0x17c` |
| `0x1da50` | `0x20269000` | `0x4890` | decompressor `0x17c` |
| `0x1d95c` | `0x200004f8` | `0xdca4` | zero-fill `0x1d8` |

The last record begins zero-fill at `0x200004f8`, 24 bytes after the pointer
slot. It therefore does not erase `0x200004e0`.

After the table loop, startup VA `0x2ac` sets the stack, calls runtime init at
VA `0x284`, then calls the application entry at VA `0x1ba0c`. The application
entry immediately calls the context getter at VA `0x38fc`. Consequently this
is not a constructor that receives the base from an application argument:
the base slot is populated by scatter before ordinary application code uses
it.

## Reproduced decompression and pointer value

The first stream begins at linked VA `0x1d860`, hence file
`0x40200 + 0x1d860 = 0x5da60`. Its first 251 bytes through file `0x5db5a`
have SHA-256
`0e31a52894540406c6c1fd1d07cc1694d245ee57aecb596ff435561a648e06d1`.

I reproduced the exact byte-oriented algorithm at linked VA `0x17c`:

* low tag bits select a literal count, with an extended byte when zero;
* high tag bits select a zero/back-reference run, also with an extended byte
  when zero;
* tag bit 3 selects a one-byte-distance back-reference, otherwise the run is
  zero-filled; and
* output stops at the table's exact destination end.

For the first record it consumes exactly `0xfb` source bytes, ending at linked
VA `0x1d95b`; the next table stream starts at `0x1d95c`. It produces exactly
`0x4f8` bytes with SHA-256
`76bebfc83f8e286d8ae152749a1aa376d0bc8d3f415f2433d9ca6944506e7ef8`.
That exact boundary agreement is a stronger check than finding a coincident
four-byte constant.

The relevant tail of the decompressed destination is:

```text
RAM 0x200004cc  01 00 01 00
RAM 0x200004d0  00 00 00 00
RAM 0x200004d4  00 00 00 01
RAM 0x200004d8  00 01 00 00
RAM 0x200004dc  00 00 00 00
RAM 0x200004e0  00 00 01 20  ; uint32 little-endian 0x20010000
RAM 0x200004e4  00 00 00 00
...
RAM 0x200004f4  00 00 00 00
```

This is a positive dataflow from packaged compressed bytes, through the reset
scatter table and exact decompressor, to the getter's RAM slot.

## Corrected getter, consumer, and effective field

The bytes previously labelled image-1 getter `0x3afc` are at absolute file
`0x43afc`; with the corrected mapping their linked VA is **`0x38fc`**:

```text
VA 038fc  ldr r0,[pc,#4]
VA 038fe  ldr r0,[r0]
VA 03900  bx  lr
VA 03904  .word 0x200004e0
```

The 12 stored bytes at file `0x43afc..0x43b07` have SHA-256
`d495280b4557a25b3c9154ca8d64678afb7b949c089d353ef884a74e68790268`.

Likewise, the prior event setter labelled `0xc3e0` is stored at file
`0x4c3e0` and has canonical linked VA **`0xc1e0`**. It calls VA `0x38fc`,
then stores `0x1001` as a halfword at returned base `+0x240a`. On the reset
value above, its concrete target is:

```text
0x20010000 + 0x240a = 0x2001240a
```

The setter's 50 stored bytes have SHA-256
`f8a6285dd94b3338eff37ded006a2ebff6ecfe7409bef9044f34fd25cdb27102`.
The same correction applies to its local event codes and callers: the prior
relative control-flow structure remains meaningful, while each old code label
must be reduced by `0x200`.

The getter's literal is the only aligned `0x200004e0` word in the executable
image-1 component. No second direct slot writer or adjacent `movw`/`movt`
construction of that full address was recovered. This bounded negative does
not exclude a computed writer, DMA, debugger, boot ROM, or later external
loader. It does establish reset scatter as a concrete writer and
`0x20010000` as the value before the recovered application entry.

## Image-0 comparison

Image 0 has the same `0x200` mapping correction. Its old file-coordinate
getter `0xf194` is canonical linked VA **`0xef94`**; its stored literal remains
the fixed value `0x47010000`. Its old file-coordinate RT check `0x216d4` is
canonical VA `0x214d4`, so the checked byte remains fixed address
`0x4701240a`.

The mapping correction changes code labels, not those RAM constants. The two
effective addresses are therefore numerically distinct on the packaged reset
path:

| path | effective address |
| --- | ---: |
| image-1 RTP setter | `0x2001240a` |
| image-0 RT check | `0x4701240a` |

They are not the same numeric address, and equal displacement `+0x240a` does
not by itself create a handoff. This does **not** prove physically distinct
SRAM across separate MCU address spaces. A hardware/interconnect window could
map image-0 `0x47010000` onto storage that image 1 sees at `0x20010000`; a
secondary-image loader could also copy or expose the state. Such a window,
later copy, mailbox, or loader bridge would need separate boot/interconnect
evidence, and none is recovered here.

## Impact on earlier USB/code-pointer claims

The constant displacement leaves relative `BL`, table-branch, and
PC-relative dataflow internally coherent when old labels are understood as
stored file offsets. It does **not** permit an absolute Thumb pointer to be
used directly as a file offset.

One material example is already concrete. The image-0 USBSerial constructor
at stored file `0x22358` (canonical VA `0x22158`) loads literal Thumb pointer
`0x0002b071` into state `+0x5c`. The pointed-to body is linked VA `0x2b070`,
stored at file:

```text
0x200 + 0x2b070 = 0x2b270
```

The prior USB report instead decoded file `0x2b070`, which is canonical VA
`0x2ae70`, and attributed that different body's register-bit rewrite to the
callback. That callback semantic claim is superseded and requires a corrected
trace of file `0x2b270`. Relative endpoint/ring routes that followed encoded
branches to their stored target bytes are not invalidated wholesale, but all
their published code labels should be read as file coordinates until
corrected. Stored-byte hashes still identify the bytes they actually audited.

The same rule applies to any vtable or callback entry in either component:
the pointer is a linked VA; locating its code in the container requires the
component payload base (`0x200` or `0x40200`). RAM/MMIO constants such as
`0x200004e0`, `0x20010000`, and `0x47010000` are not shifted.

## Limits

This report proves a packaged reset-time initialization, not current live
state. It does not establish that image 1 is installed, selected, executing,
or concurrent with image 0; that live RAM still equals its reset value;
whether image-0 `0x47010000` is an interconnect window onto image-1
`0x20010000`; how a secondary image is loaded or booted; that the RTP event
path ran during the fault; or that either image produced the host-observed
status `0x10`.

It also does not repair every historical address label. The correction is
mechanical for code labels but semantic claims involving absolute function
pointers need a fresh target-body audit. No controller instruction, readback,
write, patch, reset, or recovery action follows from this result.
