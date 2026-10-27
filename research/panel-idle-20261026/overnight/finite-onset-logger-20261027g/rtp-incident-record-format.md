# RTP incident record format and packed-input provenance

Recorded 2026-10-27 UTC. This is an offline trace of the accepted onset-v6
volatile logger outcome and the selected packaged image. No TV, controller,
USB, root, or network operation was performed. The scope is the ordinary RTP
scan/log producer and its record arguments; it excludes persistence,
high-bank/POFLG analysis, protection-threshold changes, and repair proposals.

## Incident capture

`onset-v6/native-outcome.json`, SHA-256
`1dad737eac2e3f9d9ca08b13e6e57484f84e3af9aafa81c856f9a39b1d6752d9`,
records an accepted finite run with all 16 transfers complete, final protocol
phase `ReadyForHeader`, and verified gate transition `0 -> 1 -> 0`. The
pre-arm fault halfword at RT offset `+0x0a` was zero. The restored RT read,
SHA-256 `2175e6ce7455123b8071e9edb3b3ada855107d182650c47a307f31bdd39a6ab8`,
has `0x1001` at that offset.

The secondary ring moved from `(write 143, read 143, flag 0)` to
`(write 1899, read 1899, flag 0)`. The non-wrapping 1,756-byte span has
SHA-256 `deccf31188b565c7c4c9aadcb838e042c55f81f94ffae7c88093902dc21678ba`.
It contains, in order:

- `[RTP]END`;
- `[RTP:NORMAL][395]`;
- 31 detailed RTP rows;
- two adjacent `rtp_act_736` records.

The detailed rows use this exact retained text format (the `diff` conversion is
`%d`, not `%4d`):

```text
[RTP %3d]RGB:%d x:%4d y:%4d/c:%4d/diff:%d/m:%s
```

Their record IDs are
`0..15,18..21,24..27,32..35,38..40`; every row has `RGB:0`, `y:2159`,
and `m:NORMAL`. Observed `(x,c,diff)` combinations are:

| x | c | diff | count |
| ---: | ---: | ---: | ---: |
| 620 | 0 | 1252 | 8 |
| 621 | 0 | 1252 | 7 |
| 630 | 4095 | 1065 | 3 |
| 631 | 4095 | 1065 | 3 |
| 570 / 571 | 492 | 1836 | 2 each |
| 570 / 571 | 464 | 1864 | 1 each |
| 570 / 571 | 482 | 1846 | 1 each |
| 570 / 571 | 470 | 1858 | 1 each |

These are exact captured integers and labels. They are not, by themselves,
physical pixel coordinates, voltages, luminance values, temperatures, or
engineering units.

## Corrected package map and producer bodies

The selected package is
`selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin`, 5 MiB,
SHA-256 `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
For selected image 1, corrected coordinates use:

```text
stored FILE offset = linked VA + 0x40200
```

RAM addresses receive no FILE bias.

| Packaged object | linked VA | stored FILE | slice SHA-256 |
| --- | ---: | ---: | --- |
| shared RTP orchestrator | `0xb644..0xb797` | `0x4b844..0x4b997` | `77eaad94857db91496e71c80e7dd23f9509519fa5b0da7b2eac7a0119fba4ffa` |
| packed-source selector | `0xb7ec..0xb8a7` | `0x4b9ec..0x4baa7` | `78bbf2da87adaa7cc1c9c30cbed5381d079810c8d9e3809a1c0e6744cd6d8c07` |
| comparison helper | `0xbbbc..0xbd2d` | `0x4bdbc..0x4bf2d` | `9161e90f083f9e3f230c6e8d6f2b2f2503c7cbcd6c2ca1525e025f116a30dd71` |
| packed unpacker | `0xbd58..0xc02b` | `0x4bf58..0x4c22b` | `5d9924044096fbef1f5c14db5c289d60d465750ad5ea5be6ce479375542ffcb6` |
| detailed-record formatter | `0xc5d0..0xc841` | `0x4c7d0..0x4ca41` | `51c6c80996f433f94b2774ae6b86ba61f1e95a306433b98aad6681256deb5827` |
| detailed format string | `0xc858` | `0x4ca58` | exact 48-byte C string |
| common event setter | `0xc1e0..0xc211` | `0x4c3e0..0x4c411` | `f8a6285dd94b3338eff37ded006a2ebff6ecfe7409bef9044f34fd25cdb27102` |
| `rtp_act_%d\n` | `0xc214` | `0x4c414` | exact 12-byte C string |

These are even Thumb code addresses and linked data addresses. They are not
container offsets mislabeled as code VAs.

## Packed source selection

The shared orchestrator loads two scalar arguments immediately before its only
direct call to the packed-source selector:

```text
b6f2  ldr   r0,[pc,#0xc0]  ; literal b7b4 -> RAM 200004d4
b6f4  ldrh  r1,[r0]        ; caller scalar printed as RGB
b6f6  ldr   r0,[pc,#0xb8]  ; literal b7b0 -> RAM 200004d0
b6f8  ldrh  r0,[r0]        ; caller scalar printed as y
b6fa  bl    b7ec
```

Thus `RGB:0` is the unsigned halfword observed from `0x200004d4`, and
`y:2159` is the unsigned halfword observed from `0x200004d0`. The literal
format names those arguments `RGB` and `y`, but this code does not convert them
to a physical color measurement or panel row. They are ordinary caller
scalars.

The selector passes two packed buffers to VA `0xbd58`. Packed source B is
always:

```text
B = *(uint32_t *)0x20000498 + 8
```

Depending on ordinary state tests in the selector, packed source A is one of:

```text
A = 0x20015000
A = 0x20015f10
A = *(uint32_t *)0x2000ba40 + 8
```

There are exactly three halfword-aligned direct call encodings to the unpacker,
at VAs `0xb84c`, `0xb874`, and `0xb88a`, corresponding to those selection
paths. The capture does not include the selector RAM needed to choose which A
base was active, so this report does not pretend to select one after the fact.

## Six bytes become four unsigned 12-bit lanes

At VA `0xbd58`, each loop iteration consumes six bytes from A and six bytes
from B. The B group is decoded into four unsigned 12-bit integers:

```text
B0 = word[11:0]
B1 = word[23:12]
B2 = word[31:24] | ((halfword_at_+4 & 0x000f) << 8)
B3 = halfword_at_+4 >> 4
```

The corresponding A lane is extracted with the same four layouts immediately
before one of four direct calls to comparison helper VA `0xbbbc`. The loop's
packed byte offset advances by six and its logical element index advances by
four. Therefore the printed `x` value is the logical element index of the
selected 12-bit lane. It is not derived from a panel geometry calculation in
this path and is not proven to be a physical horizontal pixel coordinate.

The helper receives `(A_lane, B_lane, element_index, y, RGB)`. It computes:

```text
diff = abs(A_lane - B_lane)
```

For the captured `NORMAL` calls that reach the detailed formatter, it passes:

```text
c     = B_lane
x     = element_index
y     = uint16 at RAM 0x200004d0
RGB   = uint16 at RAM 0x200004d4
diff  = abs(A_lane - B_lane)
mode  = code 1 -> "NORMAL"
```

The captured arithmetic independently agrees with those unsigned 12-bit
sources:

| c (B) | diff | only in-range A candidate |
| ---: | ---: | ---: |
| 0 | 1252 | 1252 |
| 4095 | 1065 | 3030 |
| 492 | 1836 | 2328 |
| 464 | 1864 | 2328 |
| 482 | 1846 | 2328 |
| 470 | 1858 | 2328 |

This establishes representation and arithmetic, not the analogue or physical
meaning of either packed source.

## Final formatter argument order

The detailed formatter at VA `0xc5d0` receives six machine arguments. It saves
the first four from `r0..r3` and loads arguments five and six from the caller
stack. Immediately before the formatter/ring sink call at `0xc638`, it lays out
the eight C-format fields as follows:

| Text field | Machine provenance |
| --- | --- |
| first `%3d` | 32-bit mode-specific record counter at `0x2000ba28 + 4*(mode-1)` |
| `RGB` | incoming argument 4, the `0x200004d4` scalar |
| `x` | incoming argument 2, logical 12-bit element index |
| `y` | incoming argument 3, the `0x200004d0` scalar |
| `c` | incoming argument 1, B's unsigned 12-bit lane |
| `diff` | incoming argument 5, unsigned absolute A/B difference |
| `m` | mode mapper result; code 1 is `NORMAL` |

The record ID is not `x`: it comes from a separate per-mode 32-bit counter.
The function increments that counter after the optional log block. Its logging
gate can suppress some formatted records while the counter continues, so gaps
in observed IDs do not imply missing ring bytes or skipped `x` values by
themselves.

## `[RTP]END`, status 395, and duplicated event 736

The shared RTP orchestrator contains the exact `[RTP]END\n` literal at linked
VA `0xb7d8` / FILE `0x4b9d8`. When its internal END byte is nonzero on the
relevant path, it emits that literal and clears the byte. The following
`[RTP:NORMAL][395]` has the status-counter provenance already traced for v3:
`395` is the pre-increment unsigned halfword at RAM `0x200004a0`, not a fault
code or physical unit.

The last two records have a separate exact producer. At VA `0x2036`, packaged
code loads event `0x2e0` (decimal 736) and calls common setter `0xc1e0`. That
setter writes, relative to its secondary root:

```text
root + 0x2400 = 1
root + 0x240e = 0
root + 0x240a = 0x1001
```

It then calls the gated formatter twice with the same `rtp_act_%d\n` literal
and the same event argument. One packaged invocation therefore naturally
produces two adjacent `rtp_act_736` records. The native restored RT read's
`0x1001` at bus window offset `+0x0a` is consistent with that common-setter
field write during the observation interval.

This is a strong internal event correlation, but it does not assign the event
to a physical blackout: no physical picture observation was recorded for v6,
and the requested For You UI state was not confirmed. The ring order proves
that the two event strings followed the detailed rows in the retained stream;
it does not supply a PC trace, exact instruction timestamps, or emitted-light
state.

## Evidence boundary

The selected package exactly supplies the strings, packed decoders, arithmetic,
argument order, direct callers, and `0x1001` event-field writer matching this
capture. Existing callback evidence ties live state to this packaged pointer
generation, but no immutable hash of the complete executing controller image
exists. The package bodies are therefore precise candidates, not a proved
full match to every executed instruction.

The bounded conclusions are:

1. `x` is a logical packed-array element index; `y` and `RGB` are separate RAM
   halfword scalars. None is proven to be a physical pixel coordinate or unit.
2. `c` is packed source B's unsigned 12-bit lane, and `diff` is the unsigned
   absolute difference between corresponding A and B lanes.
3. The paired event strings and restored `0x1001` field match the packaged
   common event setter, but do not by themselves prove blackout causation.

Run the offline verifier with:

```sh
PYTHONPATH=/tmp/tcon-capstone python3 rtp-incident-record-format.py
```

It pins the native outcome, RT/ring snapshots, exact 1,756-byte delta, all 31
records, package/slice identities, corrected FILE/VA mappings, Thumb argument
movement, packed source choices, four-lane decode, A/B arithmetic, formatter
order, and duplicated event setter. It performs no target operation.
