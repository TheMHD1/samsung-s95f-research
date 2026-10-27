# AP_EXCO alternate-pair runtime-writer provenance

Recorded 2026-10-27 UTC. This is a finite offline source trace over already
copied firmware and already captured bytes. It made no TV, network, USB,
UART, I2C, root, controller, device-node, getter, setter, reset, or UI call.
It did not inspect active-bank selection, persistence, protection, return
guards, high-bank state, or POFLG.

## Result

The selected controller image contains one positive ordinary RAM-update route
that can address both AP_EXCO fields later copied by the image-1 callback:
the controller-local manufacturing-console handlers labelled `param` and
`bin` call generic configuration writer VA `0x733c`.

That writer maps AP_EXCO logical address `0x1b0000` to object offset `+0` and
logical address `0x1b049e` to object offset `+0x3d8`. A one-halfword write at
the first address takes a dedicated AP_EXCO selector-zero hook at VA `0xc4bc`;
the second address follows the generic second-region copy arithmetic.

This is a concrete update path, but it does **not** identify a named field or
prove that the path ran before the V6 capture. No source-backed Linux/QDF/I2C
API binding to this generic writer was recovered. The proven ingress for the
two handlers remains the controller-local UART parser, not USB CDC or the
ordinary host `F300` scalar API. Therefore the observed pair `1,3` cannot be
attributed to a Samsung setting, host call, or particular runtime event from
the retained evidence.

## Inputs and coordinates

The selected 5 MiB package is
`selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin`, SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
For image 0, `FILE = VA + 0x200`; absolute RAM addresses are unchanged.

The already recovered 5 MiB backup has SHA-256
`f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562`.
The saved 16-byte candidate window has SHA-256
`2efca8a0f734277a3df0351751a2ec11d33d20423983381f5068299289fc308a`.
The script independently verifies the AP_EXCO record and both payloads are
byte-identical between the selected package and recovered backup.

| source | AP_EXCO offset | retained baseline byte | saved callback-mirror byte |
| --- | ---: | ---: | ---: |
| FILE `0x18269e` | `+0x3d8` | 20 | 1 |
| FILE `0x182200` | `+0` | 0 | 3 |

The saved mirror is not a live read of the AP_EXCO object. The separately
frozen callback trace is what relates those mirror byte positions to AP_EXCO;
this report does not strengthen the conditional bus/CPU-alias claim.

## Exact generic-writer route

The 28-byte controller command table contains these exact rows:

| FILE row | label | Thumb handler pointer | linked handler |
| ---: | --- | ---: | ---: |
| `0x3d36c` | `bin` | `0x00011719` | `0x11718` |
| `0x3d3a4` | `param` | `0x00011a75` | `0x11a74` |

Adjacent retained strings are `HandlerSetBin` and `HandlerSetParam`. Those
names identify the generic manufacturing-console handlers, not either target
field's meaning.

The complete halfword-aligned direct-call census for generic writer `0x733c`
is exactly:

```text
VA 0x11906  bin set handler
VA 0x11d52  param set handler
```

The `param` branch passes one halfword. The `bin` branch passes its parsed
byte count divided by two. No third direct caller exists in image 0.

Writer `0x733c` walks the same 21-row table used by the configuration loader.
The AP_EXCO row is:

| row member | value |
| --- | ---: |
| first physical destination / length | `0x2000ff14` / `0x33a` |
| second physical destination / length | `0x2001024e` / `0x1200` |
| first / second logical prefix | `0x1b0000` / `0x1b0400` |

It separates a logical address into its high-16-bit row prefix and low-16-bit
offset. For an offset below `0x33a`, it uses first destination plus low offset.
For an offset at or above `0x33a`, it uses:

```text
second_destination + low - (second_logical - first_logical)
```

Thus the two relevant calculations are:

```text
logical 0x1b0000
  -> 0x2000ff14 + 0
  -> AP_EXCO + 0

logical 0x1b049e
  -> 0x2001024e + 0x49e - 0x400
  -> 0x200102ec
  -> AP_EXCO + 0x3d8
```

The `0x400` logical gap is essential. Treating object offset `0x3d8` as
logical low offset `0x3d8` would resolve to the wrong destination.

## The AP_EXCO `+0` special case

When the requested count is one halfword and the selected row name is
`AP_EXCO`, writer `0x733c` calls hook `0x73ec`, which passes the low logical
offset and input halfword to VA `0xc4bc`. That hook obtains AP_EXCO root
`0x2000ff14` through getter `0xe678`.

For selector zero, the exact relevant instructions are:

```text
c4e8  cmp   r4,#1
c4ea  bne   c4f0
c4ec  bl    37390       ; additional initialization only for input 1
c4f0  strh  r4,[r8]     ; r8 = AP_EXCO root
```

Therefore an ordinary one-halfword configuration write at logical
`0x1b0000` can place a low byte of 3 at AP_EXCO `+0`, matching the numeric
byte later seen in the mirror. This proves capability and address flow only;
there is no retained invocation record. The halfword store also writes
AP_EXCO `+1`, so it must not be described as an isolated byte setter.

The input-one helper initializes a different bounded AP_EXCO subrange. Its
presence does not name selector zero and is not evidence that input one or
that helper ran in the captured incident.

## The AP_EXCO `+0x3d8` generic case

Logical `0x1b049e` is in the writer's second-region branch. That branch does
not take the one-halfword AP_EXCO special hook; it computes destination
`0x200102ec` and calls the local copy primitive with `count * 2` bytes.
Consequently the `param` path could place the low byte of a supplied
halfword at AP_EXCO `+0x3d8`, and the `bin` path can update a caller-supplied
bounded span covering it.

Again, this does not prove an invocation or field semantics. A one-halfword
write affects both `+0x3d8` and `+0x3d9`; the retained mirror only sampled the
first byte.

## Why this is not yet a named Samsung or host setting

The normal I2C `F300` receive path is a different finite scalar dispatcher.
The pinned setter body VA `0x2c71c..0x2cf53` contains no direct call to
generic writer `0x733c` or AP_EXCO special hook `0xc4bc`. It acquires the
AP_EXCO root once, but its directly addressed AP_EXCO store in that body is a
separate halfword field at `+6`, not either target here. This report does not
follow that unrelated field or its downstream behavior.

The complete direct-caller census also leaves `0x733c` reachable only from
the two local command handlers above. Prior source work binds their line
parser to controller-local UART MMIO and found no positive USB-CDC bridge.
Conversely, the ordinary Linux/QDF host calls use the finite `F300` command
protocol. No retained host module symbol, I2C selector, public setting name,
or fixed API call is tied to logical `0x1b0000` or `0x1b049e`.

So the strongest supported conclusion is:

- a real ordinary controller-local update mechanism can produce the two
  changed RAM values;
- its generic handler names are known;
- the target fields themselves remain unnamed;
- no evidence shows that mechanism ran, or that a routine Samsung host API
  selected either address; and
- computed/indirect writers outside the pinned paths remain possible.

Numeric equality alone—`1` at `+0x3d8` and `3` at `+0`—does not identify a
mode, threshold, temperature, row, panel state, or physical cause.

## Reproduction and pinned slices

Run locally only:

```sh
python3 trace-runtime-origin.py
python3 -O trace-runtime-origin.py
```

Both runs emit the same compact JSON and `target_operations:0`.

| linked image-0 slice | bytes | SHA-256 |
| --- | ---: | --- |
| generic writer `0x733c..0x73e5` | 170 | `8f8d3ab719d3869d997d6712da77d2a79895b1057d60fa08770831853d4fe9c5` |
| one-word row hook `0x73ec..0x7427` | 60 | `b5c77a049af33775dcb207e056527f72fd12fb977af21cb9ce6b42276f5afd12` |
| AP_EXCO selector-zero prefix `0xc4bc..0xc4f5` | 58 | `322df5e83f263d7afc631f9b8d8efa5d8d6a25fabf7a80ed2e4b2a79dfd569d8` |
| `bin` set handler `0x11718..0x1197d` | 614 | `8daeb8b04c6bce8fa2e0890412d28698b35b43b729f31520d3755b304365cf5c` |
| `param` set handler `0x11a74..0x11dad` | 826 | `c9108478bf841a5ef0d01fd695fa1bf2c11668c10cc56d8fa2c8754fff1ec568` |
| ordinary `F300` setter `0x2c71c..0x2cf53` | 2,104 | `9c84175a8a05a888f1b820b155b0cc52e1aaf2cecbc8f2fcd2831b982d9b548d` |

Relevant prior offline reports, used only for their established boundaries,
are `qd-usb-ap-rtp-logical-read-route.md` SHA-256
`a28594a181c6bd5fd37bc4000b62ff16769872d74a51d56c6c05ad90290a7f75`
and `qd-f300-write-payload-dispatch.md` SHA-256
`2fd6029d587022c839a2655108c977ed0108e2835a7069d590b2ac7ac4da7664`.
The companion verifier pins the exact firmware, backup, observed bytes,
mapping row, command rows, call census, branch bytes, and address arithmetic.

