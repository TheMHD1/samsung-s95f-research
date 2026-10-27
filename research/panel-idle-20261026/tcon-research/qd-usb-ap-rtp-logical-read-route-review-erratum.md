# Erratum: AP_RTP generic-reader unsigned branch

Recorded 2026-10-27 UTC. This is an offline correction to the independent
review of `qd-usb-ap-rtp-logical-read-route.md`. It made no TV, root, network,
USB, UART, controller, I2C, process, EEPROM, updater, or firmware call. It
does not provide command bytes or authorize an invocation.

## Result

The independent review's proposed correction is itself incorrect. The
original route report's address result survives exact instruction review:

```text
logical 0x0021000a, count one word
  -> unsigned first_length 0x100 > low 0x000a
  -> BHI at linked VA 0x63c4 IS TAKEN
  -> first destination 0x47012400 + 0x000a
  -> source 0x4701240a, length two bytes
```

The review read `cmp r0,r7; bhi` backwards. After `cmp 0x100,0x000a`, ARM's
unsigned `HI` condition is true (`C=1`, `Z=0`), so execution branches to
linked VA `0x63e4`. That path loads table row `+0x04`, the first destination.
It does not fall through to the row-`+0x0c` path.

No target command was sent from either interpretation. The separate missing
transport/binding limits in the original report remain unchanged.

## Exact branch proof

The retained selected profile is 5,242,880 bytes with SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
Image-0 linked VA equals stored file offset minus `0x200`.

At stored file `0x65c0` / linked VA `0x63c0`, the relevant bytes are:

```text
8068       ldr  r0,[row,#8]       ; first_length = 0x100
b842       cmp  r0,r7             ; unsigned first_length - low
0ed8       bhi  0x63e4            ; taken iff first_length > low
```

The conditional halfword is `0xd80e`: condition code `8` is `HI`, and its
displacement resolves to linked VA `0x63e4`. The path beginning there loads
row `+0x04`, adds `low`, and copies `count << 1` bytes. The fall-through path
at linked VA `0x63c6` instead loads row `+0x0c`, adds `low`, and subtracts
`row[6]-row[5]`.

For AP_RTP row 14 at stored file `0x3ce44`:

| row field | value |
| --- | ---: |
| first destination | `0x47012400` |
| first length | `0x00000100` |
| second destination | `0x47010000` |
| second length | `0x00002400` |
| first logical base | `0x00210000` |
| second logical base | `0x00210400` |

The table loop has 21 rows, and row 14 is the unique row whose first logical
base has high halfword `0x0021`, matching the comparison actually performed.
For low `0x000a`, `0x100 > 0x000a`, so the first path produces
`0x4701240a`. The selected caller loads count one, the reader converts that
to two bytes, and `0x000a + 2 <= 0x0100`; this exact read does not cross the
first-region length.

The branch boundary further disproves the reversed interpretation:

| logical input | exact condition/path | computed source |
| --- | --- | ---: |
| `0x2100ff` | `0x100 > 0xff`, first | `0x470124ff` |
| `0x210100` | equality, not `HI`, second | `0x4700fd00` |
| `0x210400` | `0x100 > 0x400` false, second | `0x47010000` |

These are static reader calculations, not proposed command values. The
unusual equality/gap behavior is reported exactly and is not repaired or
reinterpreted.

## What is corrected, and what is not

Historical artifacts remain unchanged:

| artifact | SHA-256 |
| --- | --- |
| original route report | `a28594a181c6bd5fd37bc4000b62ff16769872d74a51d56c6c05ad90290a7f75` |
| original route reproducer | `e174f6344cdedfe96159381d9778a275917dbdd5ddf595ae8b0a7626dc31284c` |
| superseded independent review | `91079e99f4eee17a653c73423eb1152d6290d26a26ed40087f75053e6a846139` |
| exact reader stored `0x657c..0x660f` | `7ebc90f811630e1be84808d2dbac850e4c067c0643066714ef5a75b2b0f11b16` |

The original checker reached the correct `0x4701240a` result, but its Python
arithmetic did not independently model the actual `CMP/BHI` split. The new
`qd-usb-ap-rtp-logical-read-route-branch-check.py` closes that checker gap by
pinning the instruction bytes, decoding the `BHI` target, requiring the
unique 21-row prefix match, modeling both branches, and testing the boundary.

The following original limitations remain in force:

* current controller flash equality with the packaged image is unproved;
* no CDC-to-local-UART command-parser bridge is proved;
* controller-local UART wiring and host accessibility are unproved;
* the generic reader has incomplete second-region/gap bounds outside this
  exact modeled input;
* no USB, UART, controller, I2C, or other command is supplied or justified;
* a returned halfword would not by itself prove an image-1 producer,
  physical RT cause, panel state, or repair.

## Offline reproduction

Run locally only:

```sh
python3 tcon-research/qd-usb-ap-rtp-logical-read-route-branch-check.py
python3 -O tcon-research/qd-usb-ap-rtp-logical-read-route-branch-check.py
```

Expected result: `PASS`, `branch=first`, `source=0x4701240a`, and an explicit
statement that no command was generated and no target was accessed.
