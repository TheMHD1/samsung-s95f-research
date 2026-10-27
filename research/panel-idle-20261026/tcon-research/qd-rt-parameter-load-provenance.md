# QD image-0 RT-field parameter/load provenance

Recorded 2026-10-27 UTC. This is a bounded, offline inspection of the retained selected QD profile; it made no TV, root, network, controller, firmware, or file-source call and changes no prior evidence.

## Result

No recovered image-0 loader, block copy, decoder, or DMA setup binds the container directory member named `AP_RTP` to the fixed image-0 RT field window at base `0x47010000`. The recovered image-0 code accesses that window directly through a fixed-base accessor, and its concrete RT-related writes are runtime EEPROM/check bookkeeping—not a parameter-table load:

| field address | image-0 access recovered | source/result provenance actually proved |
| --- | --- | --- |
| `0x4701240a` (`+0x240a`) | byte read, low bit tests selector-`0x10` condition at `0x216dc..0x216f2` | no writer recovered in the bounded direct-immediate census |
| `0x47012466` (`+0x2466`) | `strh 1` at `0x9a18..0x9a1c` after a successful four-byte EEPROM-labelled check | runtime check result; not a package copy |
| `0x47012484` (`+0x2484`) | halfword read/gate at `0x9a24..0x9a2a`, later read again at `0x9a56..0x9a5c` | reader only recovered; units/initializer unknown |
| `0x470124aa` (`+0x24aa`) | byte read at `0x9a1e..0x9a22` | reader only recovered; threshold meaning/initializer unknown |
| `0x470124ac` (`+0x24ac`) | byte-derived value stored as halfword at `0x9a48..0x9a4c`; low byte later incremented at `0x9b78..0x9b80` | runtime EEPROM response / counter path, not a package-table binding |

`AP_RTP` is certainly a named 512-byte directory record at file offset `0x86000`, but that name and record location do not by themselves prove that its payload initializes any of these fields. No threshold tuning, recovery action, or parameter-write conclusion follows.

## Pinned input and scope

```text
file    overnight/selected-qd-profile-copy-20261027b/
        F_RSM1_BN9659934B_COMMON.bin
SHA256  bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0
```

Image 0 occupies stored/linked range `0x00000..0x3ffff`. Its accessor at `0xf194` is:

```text
0f194  ldr r0,[pc,#0]
0f196  bx  lr
0f198  .word 0x47010000
```

Therefore the five relevant object offsets resolve arithmetically to the addresses in the result table. This does not establish what the `0x470...` region is, whether it is persistent, or whether the selected profile is running.

## `AP_RTP` record evidence and boundary

The container's named-directory region starts at `0x80000`; its entries are spaced by `0x200`. The exact `AP_RTP` record begins at `0x86000`:

```text
00086000  41 50 5f 52 54 50 00 00 ...   ASCII "AP_RTP"
00086020  00 04 00 00 00 00 00 21 00 01 00 00 38 00 00 10 ...
```

This proves a named record and raw bytes, but no record-field schema or unit. In particular, it does not identify the words at `0x86020` as a threshold, length, address, or command.

A raw-word search of the executable image-0 range found no direct literal `0x00086000` and no direct literals for the five final fixed field addresses. That supports the narrower statement that this image contains no simple literal-addressed `AP_RTP` copy route. It is not a proof against an external container loader or a computed/scatter-load/DMA path.

## Concrete local field dataflow

The image-0 routine `0x99e8..0x9a69` calls its local lower helper with EEPROM address `0xe0`, length four, and stack output. Subject to the two initial-byte comparisons succeeding, it executes:

```text
09a16  movs r1,#1
09a18  movw r0,#0x2466
09a1c  strh r1,[r4,r0]
09a1e  movw r0,#0x24aa
09a22  ldrb r5,[r4,r0]
09a24  movw r0,#0x2484
09a28  ldrh r0,[r4,r0]
...
09a44  ldrb r1,[sp,#2]
09a48  movw r0,#0x24ac
09a4c  strh r1,[r4,r0]
```

`r4` comes from `0xf194`, hence these are the fixed addresses above. The routine invokes the known image-0 error entry with selector `0x10` only when the respective existing gate/check comparisons pass. It does not read file offset `0x86000`, construct that offset, or call a recovered directory parser in its complete bounded body.

Routine `0x9b68..` separately derives an unsigned byte from the low byte at `+0x24ac`, increments it with a wrap guard, and uses the same EEPROM helper in its surrounding flow. That is evidence of a runtime counter path, not the initial provenance of `+0x2484` or `+0x24aa`.

## Bounded direct-immediate audit

I decoded every halfword-aligned candidate in the meaningful image-0 range and collected instructions whose operands contain one of `0x240a`, `0x2466`, `0x2484`, `0x24aa`, or `0x24ac`. Apart from branch targets that merely happen to share those numeric values, the coherent field references are:

* `0x59ea`: reads `+0x2466` and conditionally writes a different field `+0x2442`.
* `0x9a18`, `0x9a1e`, `0x9a24`, `0x9a48`, `0x9a56`: the EEPROM/check body above.
* `0x9b78`: reads/increments the low byte of `+0x24ac`.
* `0x216dc`: reads low bit of `+0x240a`.

This is useful coverage of direct immediate construction, not a whole-image writer proof. A producer could use a different base plus a smaller offset, register-derived offset, scatter-load/copy loop, boot argument, opaque call, or external loader/DMA. The image-1 RAM-pointer question is deliberately out of scope and remains unresolved separately in `qd-rtp-image-handoff.md`.

## Consequence and valid next discriminator

The retained bytes establish a local EEPROM/check-driven use of these fields, but do not establish their boot-time initialization or bind `AP_RTP` to them. A valid future discriminator would be a recovered profile-directory loader with a source/destination range that includes these addresses, or read-only runtime/loader evidence of the memory mapping and initializer. It would still need to show actual selected/running identity before it could inform the current panel fault. Neither this report nor the package name supplies a safe parameter change or a recovery procedure.
