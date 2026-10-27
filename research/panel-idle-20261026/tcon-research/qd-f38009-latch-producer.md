# Selector `09` latch producer and object-provenance boundary

Recorded 2026-10-27 UTC. This is an offline analysis of the already copied
selected QD profile. It made no TV, root, network, controller, I2C, EEPROM,
USB, UART, process-memory, or firmware call and changed no retained input.

## Result

The selector-`09` bit-`0x20` halfword has positive object and reset provenance,
but this bounded pass did **not** recover its nonzero producer.

* Image-0 linked VA `0xf4f0` (stored file `0xf6f0`) is a constant-return
  accessor for object base `0x2000f7c2`. The selector getter reads and clears
  object offset `+0x46`, exactly RAM `0x2000f808`.
* Image-0 reset's final scatter record zero-fills
  `0x20000f4c..0x20017383`, which includes `0x2000f808`. The packaged reset
  value of the latch is therefore zero.
* Forty direct Thumb `BL` sites target this accessor. A bounded review of
  those direct consumers and of every decoded fixed-offset `STRH ...,+0x46`
  in image 0 found no nonzero store to this object field. The only proved
  exact-field runtime store is selector `09`'s destructive clear.
* Image 1 contains no direct word literal for `0x2000f7c2` or `0x2000f808`.
  It supplies no positive alias or writer for this image-0 field.

This narrows the missing edge: a nonzero value must arise after reset through
an unrecovered computed/indirect store, a bulk copy, DMA/peripheral action,
another core or address-window alias, or a later external loader. The bytes do
not support naming it an RT latch, a fault subtype, a counter, or a particular
physical condition. Stock `sp-kpi` polling can consume it, but that fact does
not identify its producer.

## Inputs and address convention

The selected package is:

```text
overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin
size    5242880 (0x500000)
SHA256  bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0
```

Image 0's vector table is at stored file `0x200`; therefore image-0 linked VA
equals stored file offset minus `0x200`. Absolute RAM addresses are not
shifted. Image 1's vector table is at file `0x40200`; its linked VA equals
file offset minus `0x40200`.

The immediate predecessor is `qd-f38009-stock-telemetry.md`, SHA-256
`cec443ad8e0becd7f6fd4b33eea1360ca6f79e4d4f26e85b2d897e735d3a177c`.
That report establishes the stock polling and selector response semantics.
This report addresses only the field's local object, reset initialization,
and bounded writer/alias census.

## Exact object path

Stored file `0xf6f0..0xf6f7` is the accessor (linked VA `0xf4f0`):

```text
VA f4f0  ldr r0,[pc,#0]
VA f4f2  bx  lr
VA f4f4  .word 0x2000f7c2
```

The established selector-`09` getter at linked VA `0xfe6c` calls that
accessor at `0xfe7c`, saves it in `r8`, and performs:

```text
VA ff66  ldrh.w r0,[r8,#0x46]   ; 0x2000f7c2 + 0x46 = 0x2000f808
VA ff6a  cbz    r0,ff76
VA ff6c  orr    r4,r4,#0x20
VA ff70  movs   r0,#0
VA ff72  strh.w r0,[r8,#0x46]
```

Thus the field is a 16-bit member of the object returned by the accessor,
not a guessed address obtained solely from a raw-word search. The getter
provides the only proved exact-field runtime write, and it writes zero.

## Reset-time writer

The canonical image-0 scatter table is stored at file
`0x3e340..0x3e3ff`. Its last 16-byte record is:

```text
source/unused  0x0003e764
destination    0x20000f4c
length         0x00016438
handler VA     0x000001d8
```

Handler `0x1d8` zeroes registers `r3..r6`, repeatedly stores them to the
destination, handles the remaining words, and returns at `0x1f2`; it is the
reset zero-fill handler. The exclusive end is
`0x20017384`; therefore:

```text
0x20000f4c <= 0x2000f808 < 0x20017384
```

This is a concrete packaged reset initializer for the latch, not an
assumption based on the absence of a writer. It does not prove the current
controller is running these packaged bytes or that the field remained zero
after startup.

## Bounded writer and alias census

The executable image-0 range was decoded as Thumb at each halfword for a
conservative direct-reference census.

1. Exactly 40 decoded immediate `BL` instructions target accessor VA
   `0xf4f0`. Their direct consumer bodies use many other members of the same
   object, but none supplies a nonzero store at `+0x46`, nor a fixed word store
   at `+0x44` that is proved to use this accessor result and overlap the
   halfword.
2. There are ten decoded fixed-displacement `STRH` instructions with
   displacement `0x46` in image 0. Base provenance separates them:

   | stores | proved base/range | relation to latch |
   | --- | --- | --- |
   | VA `0x93ae`, `0x944e` | accessor `0xe670` = `0x2000f0e0` | distinct object |
   | VA `0xf568` | accessor `0xf1ec` = `0x2000fc6c` | distinct object |
   | VA `0xff72` | accessor `0xf4f0` = `0x2000f7c2` | exact latch; zero clear |
   | VA `0x1cd5e`, `0x1ce32` | indexed `0x2021f800/0x2021f400` regions | distinct RAM |
   | VA `0x1dae8`, `0x22246` | indexed `0x2021f000` region | distinct RAM |
   | VA `0x24b5a` | accessor `0xf500` = `0x2000d340` | distinct object |
   | VA `0x2b8e4` | accessor `0xf508` = `0x20014440` | distinct object |

3. Raw aligned/unaligned word census finds `0x2000f7c2` twice. File
   `0xf6f4` is the real accessor literal; file `0x3cd4c` is instruction bytes
   `c2 f7 00 20`, not a data pointer. The sole raw occurrence of
   `0x2000f808`, file `0x1dec0`, is instruction bytes `08 f8 00 20`, also not
   a literal. Neither value occurs in stored image 1 (`0x40000..0x5ffff`).

This is not a whole-program proof that no producer exists. In particular,
direct-call and fixed-offset scans cannot exclude a pointer passed through an
indirect call, register-derived address arithmetic, a bulk copy whose range
includes the member, DMA, an interrupt/peripheral engine, another processor,
or a physical alias not represented by the same numeric address.

## Consequence for retained observations

The stock approximately-60-second selector-`09` poll clears this halfword
after reporting returned bit `0x20`. A later zero cannot recover whether the
latch had previously been nonzero. Conversely, a future observed `0x20`
would prove only that this field was nonzero at that read. With the nonzero
writer still unresolved, it would not prove RT protection, explain status
`0x10`, or identify a blackout cause.

No additional stock read is proposed here. The smallest remaining source gap
is the nonzero writer or a proved inter-core/window alias for `0x2000f808`,
not another interpretation of selector `09` itself.

## Reproducible anchors

`qd-f38009-latch-producer-reproduce.py` checks the full input hash, vector/load
mapping, accessor literal, exact read-to-clear bytes, zero-fill record and
range, raw-word coincidences, image-1 negative, all 40 direct accessor calls,
and these bounded slice hashes:

| stored file interval | bytes | SHA-256 |
| --- | ---: | --- |
| image 0 `0x200..0x3ffff` | 261,632 | `57ef8b1abd39e8d14dc5c9c299ef4b80631262638a065368027680a233a32b5e` |
| accessor `0xf6f0..0xf6f7` | 8 | `fc60655e318a4b18ca66752d54d97fce55021d10ca6c5ccfcacebd3641a42bda` |
| selector getter `0x1006c..0x101a7` | 316 | `24f30bf63c8dbfd8fbeb0a8410d07057215b126b5125b91bf0c375615e971b0c` |
| scatter table `0x3e340..0x3e3ff` | 192 | `3f09781583f48d9b429fe8438b06bbd26196b3f673c79e6a2cf7adde356b612d` |
| zero-fill handler `0x3d8..0x3f3` | 28 | `35c9c9990fd6fca376959800dc4a120df626f42d01eb18e8fdfebc5487f091ec` |

The checker uses no external packages and supports normal and `python -O`
execution because its guards do not depend on `assert`.
