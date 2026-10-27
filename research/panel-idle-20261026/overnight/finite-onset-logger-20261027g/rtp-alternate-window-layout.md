# RTP alternate-selector local 16-byte layout

Recorded 2026-10-27 UTC. This is a narrow offline layout of image-1 fixed
context CPU `0x20000bc0..0x20000bcf` (`context+0x6c0..+0x6cf`) and the
candidate bus window `0x47000bc0`, length 16. It made no TV, root, USB,
controller, network, UI, reader-build, firmware, threshold, protection,
configuration, persistence, or storage operation. It does not enter
high-bank/POFLG, return-guard, persistence, or protection paths.

## Result

The 16-byte range is a heterogeneous local context header, not one AP_EXCO
field. Its directly qualified layout is:

| context offset | CPU address | width | positive ordinary writer/use |
| ---: | ---: | ---: | --- |
| `+0x6c0` | `0x20000bc0` | u16 | startup VA `0x17984` stores `0x0870` |
| `+0x6c2` | `0x20000bc2` | u16 | startup VA `0x1797c` stores `0x0780` |
| `+0x6c4` | `0x20000bc4` | u16 | startup VA `0x1798c` stores `0x0b40` |
| `+0x6c6` | `0x20000bc6` | byte | no direct immediate-offset store recovered; read at `0x1bd90` |
| `+0x6c7` | `0x20000bc7` | byte | callback VA `0x3952` copies unnamed `AP_EXCO+0x3d8` |
| `+0x6c8` | `0x20000bc8` | byte | same callback VA `0x3958` copies `AP_EXCO+0` |
| `+0x6c9` | `0x20000bc9` | byte | volatile flag, cleared at `0x17156` |
| `+0x6ca` | `0x20000bca` | byte | volatile flag, cleared at `0x1717a` |
| `+0x6cb` | `0x20000bcb` | byte | volatile flag, cleared at `0x185a2` |
| `+0x6cc` | `0x20000bcc` | byte | volatile flag, cleared at `0x17ac6` |
| `+0x6cd` | `0x20000bcd` | byte | cleared at `0x17af4`; set to 1 or 2 at `0x19a92` |
| `+0x6ce` | `0x20000bce` | byte | set to 1 at `0x17b7a`/`0x197fe`; cleared at `0x19954` |
| `+0x6cf` | `0x20000bcf` | byte | no direct immediate-offset store recovered in the bounded census |

The numeric halfwords `0x0870`, `0x0780`, and `0x0b40` are exact. This report
does not call them dimensions, timing, pixels, voltage, or any physical unit.
The names “flag” and “header” describe software layout/behavior only.

## Reset, startup, and callback fingerprints

Image-1 scatter zero-fills
`0x200004f8..0x2000e19b`, so the reset fingerprint of all 16 bytes is:

```text
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
```

Application entry has one direct call to VA `0x17970`, at VA `0x1ba9e`.
That function gets fixed context base `0x20000500` and performs:

```text
17978  r0 = 0x0780
1797c  strh r0,[context,#0x6c2]
17980  r0 = 0x0870
17984  strh r0,[context,#0x6c0]
17988  r0 = 0x0b40
1798c  strh r0,[context,#0x6c4]
```

Immediately after those startup stores, before runtime flag changes, the
known fingerprint is:

```text
70 08 80 07 40 0b 00 00 00 00 00 00 00 00 00 00
```

The ordinary registered callback then refreshes two neighboring bytes in the
same VA `0x3934` invocation:

```text
394e  ldrb r0,[AP_EXCO,#0x3d8]
3952  strb r0,[context,#0x6c7]
3956  ldrb r0,[AP_EXCO,#0]
3958  strb r0,[context,#0x6c8]
```

For the selected packaged AP_EXCO payload, the two source bytes are:

```text
AP_EXCO+0x3d8 = FILE 0x18269e = 0x14 (20)
AP_EXCO+0     = FILE 0x182200 = 0x00
```

If that selected configuration was loaded, the AP_EXCO object was not later
changed, and the callback ran, the corresponding conditional fingerprint is:

```text
70 08 80 07 40 0b 00 14 00 ?? ?? ?? ?? ?? ?? ??
```

Question marks are intentional. Bytes `+0x6c9..+0x6ce` are ordinary runtime
flags with positive setters/clearers, and `+0x6cf` lacks a direct writer in
this bounded census. Even the non-question-mark bytes are packaged/control-
flow expectations rather than a live anchor.

## Exact direct stores in the local slice

Every listed direct writer obtains its base from fixed-context getter VA
`0x38f4`, either in the function itself or its containing ordinary main-loop
body. The exact immediate-offset stores are:

| site | operation |
| ---: | --- |
| `0x1797c` | `STRH 0x0780 -> +0x6c2` |
| `0x17984` | `STRH 0x0870 -> +0x6c0` |
| `0x1798c` | `STRH 0x0b40 -> +0x6c4` |
| `0x3952` | `STRB AP_EXCO[0x3d8] -> +0x6c7` |
| `0x3958` | `STRB AP_EXCO[0] -> +0x6c8` |
| `0x17156` | `STRB 0 -> +0x6c9` |
| `0x1717a` | `STRB 0 -> +0x6ca` |
| `0x185a2` | `STRB 0 -> +0x6cb` |
| `0x17ac6` | `STRB 0 -> +0x6cc` |
| `0x17af4` | `STRB 0 -> +0x6cd` |
| `0x19a92` | `STRB 1 or 2 -> +0x6cd` |
| `0x17b7a` | `STRB 1 -> +0x6ce` |
| `0x197fe` | `STRB 1 -> +0x6ce` |
| `0x19954` | `STRB 0 -> +0x6ce` |

This is an exact direct-immediate-offset store census, not a whole-firmware
absence proof. Other bodies form `base+0x6c0` as an array pointer or accept a
base as an argument; their recovered instances either read the region or
operate on another supplied buffer. A computed writer, interrupt, later-loaded
code, corruption, or external agent is not excluded.

The callback writes only `+0x6c7/+0x6c8`; it does not populate the whole
16-byte slice from AP_EXCO. Therefore a future match at byte `+7` alone cannot
be described as an AP_EXCO-block copy or an alias proof.

## Older mirror evidence already contradicts a live-default assumption

The frozen D5 64-byte read at bus `0x470004c0` has SHA-256
`2543a59edfbd16832cfddd460c3dae28017309669d35eabc6eedcdfd95b7675d`.
It returned:

```text
window +0x04c2 = 0
window +0x04c4 = 0
window +0x04e0 = 0x20010000
```

In the packaged ordinary path, VA `0xc250` compares context `+0x6c7` with
CPU mirror halfword `0x200004c2`; when changed, it copies the byte to that
halfword and writes boolean nonzero state at `0x200004c4`. The older zeros do
not prove that context `+0x6c7` was zero—address aliasing and exact timing
remain conditional—but they do prove that selected packaged default 20 must
not be assumed live merely because it exists in the payload.

## How to interpret candidate bus `0x47000bc0`, length 16

The recovered conditional mapper arithmetic turns CPU `0x20000bc0` into
candidate bus address `0x47000bc0`. A raw read there would return bus bytes;
it would not, by itself, prove they are the image-1 CPU context.

A useful comparison should preserve the complete 16 bytes and classify them:

- matching only byte `+7 == 0x14` is weak and can be coincidental;
- matching the three little-endian startup constants at `+0..+5` is stronger
  layout evidence, but still not a time or alias proof;
- matching `+7/+8` to the selected AP_EXCO pair `14 00` additionally supports
  the ordinary callback/configuration hypothesis, subject to runtime changes;
- bytes `+9..+14` are volatile and must be reported rather than forced to a
  packaged expectation;
- disagreement with `14 00` does not identify a single cause: a different or
  inactive configuration, callback not run, later AP_EXCO change, later local
  write, non-aliasing candidate window, or different runtime image remain
  possible.

Correlation with a separately sampled `0x470004c0` mirror block can add
evidence, especially `+0x04c2/+0x04c4`, but two sequential raw reads are not
atomic. No one byte or one pair should be promoted into a live CPU alias
claim.

## Boundary

This report stops at the ordinary local layout, selected packaged AP_EXCO
bytes, and already retained mirror read. Establishing an active configuration
bank, persisted selection, or a protection consequence would cross the
excluded boundary. No reader or target operation is implemented here.

## Reproduction

`rtp-alternate-window-layout.py` pins the selected package, reset extent,
startup/callback bytes, every direct store instruction above, AP_EXCO payload
fingerprint, mapper arithmetic, and frozen D5 mirror block. It uses only
Python's standard library:

```sh
python3 rtp-alternate-window-layout.py
python3 -O rtp-alternate-window-layout.py
```
