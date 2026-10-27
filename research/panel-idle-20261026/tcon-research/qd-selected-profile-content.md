# Selected QD profile content: embedded firmware and calibration banks

Recorded 2026-10-27 UTC. This is a bounded offline examination of one already
retained regular file. It made no TV, root, network, controller, SSB, GPIO,
firmware-update, or display call and changed no prior evidence.

## Result

The selected 5 MiB asset is a **composite container**, not merely a calibration
table and not a raw copy of the controller's reported 2 MiB SPI flash.

* Its first `0x60000` bytes contain two high-confidence Cortex-M/Thumb firmware
  images. The first has a metadata header, vector table at file/linked address
  `0x200`, executable code, fault handlers, a December 2024 build banner, and
  QD display strings. A separately linked image begins at file offset
  `0x40000`, has its own vector table at `0x40200`, and contains extensive RTP
  scan/analysis code and strings.
* `0x60000..0x7ffff` is low-entropy support/configuration data, not proved
  executable. At `0x80000` begins a named parameter/LUT directory followed by
  dense table regions and later sparse repeated banks. Names include
  `FE_LUT`, `EXCO_*`, `AP_RTP`, `AP_SPC`, and other processing blocks.
* The first firmware image contains a concrete RT-protection path. A routine at
  `0x99e8` reads four bytes from an EEPROM-labelled path at address `0xe0`,
  compares signature/history/count state, and enters the common error path with
  selector **`0x10`** while carrying the exact messages `EEPROM Check RT
  Protection` and `EEPROM Check RT Protection Max count`. The common error path
  stores that selector in an internal error-mask field and has a dedicated
  `0x10` dispatch branch.

This is the first recovered byte-level producer-side explanation for an
internal RT-protection selector of `0x10`. It is an exact numeric and textual
match to the host-side `0x10`/`RT Protect` observation, but it is **not yet a
proved end-to-end producer binding**: the recovered bytes do not prove that
this packaged image was flashed or running, that the host `F3 80 ... 08` query
returns this particular internal mask, that the EEPROM branch ran, or what
electrical/physical condition caused the stored history/count. No byte is
identified here as a repair value or safe threshold.

## Input identity and selection provenance

The examined file is:

```text
overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin
size    5242880 (0x500000)
SHA256  bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0
```

Its copy manifest is 3,994 bytes, SHA256
`39ad1db84bfa64d2bad8928b80da5b9bb1b92b12398a0dc2c6ad756a3905a706`;
the retained copy audit is SHA256
`42b46c851fd266f4f3e673a910f840be60ab0bd5031f77036e539ddea8050d99`.
The manifest records an ordinary-filesystem source
`/factory_peq/tcon_data/QD/F_RSM1_BN9659934B_COMMON.bin`, no controller
operation, and equality of the source and reconstructed file hashes.

The selection is not based merely on the filename's `77` prefix. The exact
retained runtime tuple is:

```text
[QDF]FW[FA024C300/F:FA024C300]
MD[F77ABUAE20312300/F:F77ABUAE20312300]
```

Within the retained nine-file factory set, only this asset contains all three
matching fields: `FA024C300` at `0x4ffe00`, `F77ABUAE2` at `0x80100`, and
`12300` at `0x8000a`. The independent selection audit is
`qd-fault-next-discriminator-audit.md`, SHA256
`53a879cc890dc52f4ed181bc2d46523b02fef72417b85e2b30357fe571ba8989`.
That is a unique runtime-tuple-to-packaged-asset match within the retained
catalog; it is not a proof of a current flash-to-file byte match.

## Bounded method

The file was processed as bytes, with no loading or emulation:

1. Recompute full-file and selected-region SHA256/CRC32 values.
2. Enumerate printable strings with exact byte offsets.
3. Measure 64 KiB block entropy and nonzero-byte counts to distinguish dense
   images/tables from zero padding.
4. Scan every four-byte-aligned offset for a conservative Cortex-M vector
   signature: an 8-byte-aligned initial stack pointer in
   `0x20000000..0x20080000`, an odd in-range reset vector, and at least 12 of
   the next 15 entries either zero or odd/in-range. Exactly two offsets pass,
   and both have 15/15 plausible entries.
5. Decode only selected Thumb ranges with Capstone and verify literal targets,
   branch destinations, load/store widths, and immediate values against the
   original bytes. A separate every-halfword direct-`BL` census was used only
   to find syntactic callers; it is not represented as a recovered whole-file
   CFG.

Entropy, strings, or coincidental valid instructions alone are not treated as
executable proof. The executable classification below rests on the combination
of vector-table shape, odd Thumb handler addresses, coherent startup code,
fault-handler strings, linked-address consistency, and substantive decoded
functions.

## Container map

The following boundaries describe content, not a recovered vendor file-format
table:

| File interval | Bytes | SHA256 | Evidence-backed interpretation |
| --- | ---: | --- | --- |
| `0x000000..0x03ffff` | 262,144 | `e21cac7a33e92050be5b2231a7b17bfbda23f56f18ce0641eb80808dc6cbd7bb` | Header plus first linked Cortex-M image; meaningful code ends near `0x3ece0`, followed by padding |
| `0x040000..0x05ffff` | 131,072 | `c97865a60fcf0112b0547d41dca99bcad79d5411f90d26f4048cab926a9c4a5f` | Second linked Cortex-M image; meaningful bytes end near `0x5dce2` |
| `0x060000..0x07ffff` | 131,072 | `d5d4266a176859169b53f067674d57806dbec9a4a610a5b16d5554ef41b03ffe` | Low-entropy support/configuration bytes, then all-zero `0x70000..0x7ffff`; no executable claim |
| `0x080000..0x4fffff` | 4,718,592 | `ab1731396d13c8cc009445802bfe3101314ef87356f873642193b0fc0238c020` | Parameter/LUT directory, dense tables, sparse repeated banks, tail identity |

The first six 64 KiB blocks have Shannon entropy `6.198..6.887` bits/byte and
50,929..59,664 nonzero bytes. `0x60000..0x6ffff` drops to `1.327` with 8,092
nonzero bytes; `0x70000..0x7ffff` is all zero. Dense table blocks from
`0x90000..0x12ffff` have entropy `4.266..5.522`. Much of
`0x190000..0x4ffdff` is zero except for small repeated metadata/table banks.
Those measurements support the map but do not assign vendor semantics by
themselves.

The terminal word at `0x4ffffc` is `0x25925a07` little-endian. No verified
checksum relationship was recovered, so it is not labelled a checksum.

## Embedded image 0

The file begins with little-endian magic `0xa5a55a5a` and metadata:

| Offset | Exact ASCII |
| ---: | --- |
| `0x40` | `241230A` |
| `0x60` | `SDCAD\bonggyun.kang` |
| `0x80` | `12-30-2024 15:56:21` |
| `0xa0` | `4K_TV-VD` |
| `0xc0` | `ARMCC_5.06.0.45` |
| `0x140` | `mcu_ata` |

At `0x200`, the first words are initial SP `0x20020000`, reset vector
`0x00000345`, and exception vectors including `0x00017e7d`, `0x00012071`,
`0x00016d81`, `0x00003cf9`, and `0x0002b9a9`. The reset address's low bit
selects Thumb and decoding at `0x344` yields a coherent ARMCC startup sequence.
The 320-byte vector-and-pre-startup region `0x200..0x33f` has SHA256
`5ebb37e039d19b835f9cc23c7a467a43140d6b329c44882c9c150c77fea30e69`.

Near the end of the image are exact strings:

```text
0x39e78  _________________ S6TUT14FW_________________
0x39ea8  15:55:11
0x39eb4  Dec 30 2024
0x39ec4     Keil %d, Build(%s %s)
0x39ef5  QD-DISPLAY RUN
0x39f09  QD-DISPLAY STOP
```

This combination establishes an embedded controller-oriented executable, not
merely random parameter bytes. It does not establish that it is the complete
reported `F77ABU2D20` SPI-flash image: that exact string is absent, this region
is only 256 KiB, and a packaged updater may extract, relocate, combine, or
select content in ways not recovered here.

The exact version-like identities remain distinct. Image 0 says `241230A`,
`12-30-2024 15:56:21`, and `Dec 30 2024`; the package tail says
`FA024C300`, which is the exact retained QDF `FW[...]` value. The full-file
string census finds each once, but finds neither `F77ABU2D20` nor the combined
runtime `F77ABUAE20312300`. The shared date-looking characters do not prove an
encoding or transformation between `241230A` and `FA024C300`; this report
therefore records them as separate embedded-image and package/profile
identities rather than claiming they name the same firmware build.

## Embedded image 1

The second candidate begins at stored offset `0x40000`. Its vector table at
`0x40200` contains initial SP `0x20020000`, reset vector `0x00000369`, and 15/15
plausible handler entries. These vector values are linked relative to address
zero rather than file offset `0x40000`; decoding the reset handler at stored
offset `0x40368` produces coherent Thumb startup code. The corresponding
320-byte vector-and-pre-startup region has SHA256
`ee2935c2eea854eca5ba7d24cdd3c8192907d61b7873aed795a6aca28dce3aaf`.

It contains its own `HardFault_Handler`, `BusFault_Handler`, and
`UsageFault_Handler` strings, plus executable-adjacent RTP strings including:

```text
0x4b99b  [RTP]START
0x4b9d7  [RTP]END
0x4bb7b  [RTP]Frame end
0x4bb8f  [RTP]On scan end
0x4bbb7  [RTP]ONSEN Mode end
0x4bbd3  [RTP]IO Mode end
0x4bcfb  [RTP]On scan start
0x4bd13  [RTP]ONSEN Mode start
0x4bd2f  [RTP]IO Mode start
0x4c414  rtp_act_%d
0x4c4fb  [RTP]Emmc data empty!
0x4c783  [RTP]Fab scan start
0x4c7bb  [RTP]Fab scan end
0x4ca57  [RTP %3d]RGB:%d x:%4d y:%4d/c:%4d/diff:%d/m:%s
```

These bytes establish a second firmware component concerned with RTP scanning
and data. They do not prove what the acronym expands to, that this component
was selected at runtime, or that its scan result directly becomes the host
status bit.

## Exact RT-protection path in image 0

### Four-byte EEPROM-labelled read

Function `0x99e8..0x9a69` (130 bytes, SHA256
`2846fcc6978d6bbcb1184a54c3334ace79a387275d5ca30e1bde14c7234a9ddc`)
does the following:

1. Gets an object/base from `0xf194`.
2. Calls helper `0x9948` with address `0xe0`, length four, and a stack output
   buffer.
3. Requires helper return zero.
4. Requires returned bytes 0 and 1 to match the two bytes at literal RAM
   address `0x20000c50`.
5. Sets object halfword `+0x2466` to one.
6. Loads a byte at `+0x24aa` and an enable/gate halfword at `+0x2484`. If the
   gate is nonzero and the byte is less than two, it calls the common error
   entry with `r0=0x10` and the literal at `0x9a6f`, `EEPROM Check RT
   Protection`.
7. If returned bytes 2 and 3 are equal, stores byte 2 as a halfword at
   `+0x24ac`. If that byte is greater than or equal to the `+0x24aa` byte and
   the gate is nonzero, it calls the same common error entry with `r0=0x10`
   and `EEPROM Check RT Protection Max count` at `0x9a8c`.

The helper `0x9948..0x998b` (68 bytes, SHA256
`22f3b84e62aef70b87e5d942fde98acc416a90ffec73a8a1d590af2c1b8fb5ba`)
uses the low 16 address bits as a two-byte address, folds address bits 16..17
into device address `0xa0`, and passes both the caller's output pointer and
length to lower function `0x12df8`. The firmware's own adjacent literals call
this an EEPROM check. The exact external EEPROM device, physical storage
technology, and units of bytes 2/3 are not identified by these instructions.

### Error selector and internal mask

Common function `0xb860..0xb8f9` (154 bytes, SHA256
`40e434612828833aa7b433798a352a99c766cbb47351d2cb42ba364a868d2c6a`)
retains its first argument as an error-source selector, calls `0x14b10` and
`0x2b964` with that selector, and formats `Entry -> %s err_src[%s]`.

Function `0x2b964..0x2b979` (22 bytes, SHA256
`3d538c104bca6958c66173c7d56a095ded57e9453134e78933ee6d0e26fffb03`)
inserts the selector into the low 16 bits of an internal object field at
`+0x10`. Dispatch `0x14b10..0x14bbb` (172 bytes, SHA256
`5fcc7bea9301c9aa6b815a92fff05ac97769daf64e9eccbe1bac23f5667e3d18`)
has an explicit `selector == 0x10` branch; it clears one halfword, invokes
additional internal handlers, writes literal `0x10` to another state field,
then calls more RT-related functions.

A direct-`BL` encoding census over every halfword of the file found one
syntactic call to `0x99e8`: `BL 0x99e8` at `0x39d26`, embedded in a long,
coherently decoded initialization call sequence. The local block
`0x39cf2..0x39d3d` has SHA256
`4ed212a0286c80b4c67578224fed538bc106c77b32269fe38c4fa36e0ab4af5e`.
This is evidence that the check is wired into initialization, not just an
unreferenced string/function island. The census is not a whole-program proof:
indirect calls and alternate decoding paths were not recovered.

The numeric equality between this internal selector and the accepted host
status is significant but insufficient to merge their state. The missing
static edge is from the internal controller field/protocol response to the
host's QDF `F3 80 00 00 00 08` return word. Current-byte equality and actual
execution are also unproved.

### Related correction and temperature checks

Two small routines use the same object:

* `0x594c..0x5973` checks `+0x2436 == 1`, clears it, and logs `[RTP] Correct
  RTP ONSEN Mode!!!` (SHA256
  `080760214bff03bf4af2c2607ffb2e6bb7c5f7b5d30dac5c814748edd903de6a`).
* `0x59dc..0x5a03` checks `+0x2466 == 1`, sets `+0x2442 = 1`, and logs
  `[RTP] Correct RTP Fast Mode!! : RTP history + ONSEN Skip` (SHA256
  `49cc135c1a3cb278071705fce97e00115fc6261bcaf3175cc860ba10faf947c1`).

This connects the EEPROM signature flag to an RTP mode-correction path. It
does not define ONSEN, establish a safe mode transition, or prove the runtime
state of these fields.

Separately, function `0x39714..0x39767` (84 bytes, SHA256
`b750a92a57adab7f08a0cc1e76fe881f7be932b9215c69cfd372328183b7e73a`)
compares halfword `+0x24e` against lower/upper halfwords `+0x256/+0x258` and,
when enable `+0x28c == 1`, calls another handler and logs `[VEP] Temp Error`.
This proves explicit temperature-range checking exists. No recovered edge
equates these fields with RT protection, the EEPROM counters, a particular
sensor, physical temperature units, or host bit `0x10`.

## Calibration and parameter content

At `0x80000`, the directory metadata includes `2412300`, `Q100A_MCU`, and the
selected profile prefix `F77ABUAE2`. Named sections occur on `0x200`
boundaries:

```text
0x80600 Pre-PD           0x80800 LF(2.5.24)      0x80a00 IRC(0.3.5)
0x80c00 SPC(1.0.12)     0x80e00 SE(1.0.8)       0x81000 LP(0.0.4)
0x81600 ZA(3.3.4)       0x81800 ISC4.2_0        0x81a00 ISC4.2_1
0x81c00 DIA(0.2.1)      0x82400 RGC_ASIC        0x82a00 CSG_SYS
0x82c00 CSG_CK1         0x82e00 CSG_CK2         0x83000 CSG_GS
0x83200 CSG_OE          0x83400 CSG_GPO         0x83600 FE_LUT
0x83a00 EXCO_PAR1_S0    0x83c00 EXCO_PAR2_S0    0x83e00 EXCO_LUT1_S0
0x84000 EXCO_LUT2_S0    0x84200 EXCO_PAR1_S1    0x84400 EXCO_PAR2_S1
0x84600 EXCO_LUT1_S1    0x84800 EXCO_LUT2_S1    0x84a00 AP_GCM
0x84e00 NPC_AP          0x85400 AP_SBD           0x85800 AP_TED
0x85a00 AP_ISC4.1       0x85c00 AP_SA_ISC4.3    0x85e00 AP_EXCO
0x86000 AP_RTP          0x86200 AP_SPC           0x86600 AP_LOCAL_NPC
0x86800 AP_MULTI_LOGO   0x86a00 AP_HUT           0x86e00 AP_QFS
0x87000 AP_LCC          0x87200 AP_TDC
```

These names and dense following bytes are evidence for calibration,
parameters, and lookup tables within the same container. They do not by
themselves disclose entry lengths or threshold units. Later sparse banks at
`0x1d0000`, `0x2e0000`, and `0x3f0000` repeat `Q100A_MCU`, `Dalign`, and some
EXCO labels, each with only about `0x500e` meaningful bytes before long zero
runs. Their slot/mode selection logic was not recovered, so no active bank is
claimed.

## What is and is not closed

Closed by the actual bytes:

* The selected factory asset contains real embedded firmware as well as
  calibration/parameter data.
* There are exactly two conservative vector-table matches under the stated
  full-file scan, each followed by coherent Thumb code.
* An initialization-referenced EEPROM RT-protection check enters internal
  error handling with exact selector `0x10`; this is not merely an isolated
  printable string.
* The container contains explicit RT history/count comparisons, RTP mode
  correction state, a separate RTP scanning image, and a separate
  temperature-range checker.

Still open:

* Whether either embedded image exactly matches bytes currently executing on
  the controller, and how the images/tables are selected or installed.
* Whether internal error mask `0x10` is the exact source returned by the host
  status query. Numeric/text agreement is strong correlation, not a recovered
  transport edge.
* What EEPROM bytes 0..3 mean beyond the exact signature/equality/count
  operations, whether their values are current or latched, and what hardware
  event changes them.
* The expansion of RTP/ONSEN, the physical source of RT protection, threshold
  units, and whether a protection event caused the owner's black picture.
* The second image's installation/execution mode, the semantics of the sparse
  banks, and the meaning of the terminal word.

No absence claim follows from strings not found, no setting or patch is
recommended, and no recovered constant should be written to the controller or
EEPROM. The smallest remaining static edge is the controller protocol/status
serialization of the internal error mask; otherwise the next discriminator
would require contemporaneous, independently reviewed runtime evidence, not
reinterpretation of this packaged file.
