# RTP alternate-threshold source-context provenance

Recorded 2026-10-27 UTC. This is a finite offline trace of the ordinary
image-1 context/configuration handoff that supplies CPU byte `0x20000bc7`.
It made no TV, root, USB, controller, network, UI, firmware, configuration,
threshold, protection, persistence, or storage operation. It does not enter
persistence, high-bank/POFLG, return-guard, or protection branches.

## Result

The byte that selects the alternate event-736 threshold has a positive
ordinary configuration provenance:

```text
selected AP_EXCO type-4 configuration
  first destination  0x2000ff14, length 0x033a
  second destination 0x2001024e, length 0x1200

image-1 startup resolves "AP_EXCO"
  -> maps first destination 0x2000ff14 to 0x4500ff14
  -> stores pointer 0x4500ff14 in slot 0x200002cc

getter 0x38e8 returns *(uint32 *)0x200002cc
callback 0x18c94 calls 0x3934
  -> reads byte [AP_EXCO pointer + 0x3d8] = [0x450102ec]
  -> writes that byte to fixed context 0x20000bc7
```

The selected packaged AP_EXCO payload supplies numeric byte **20** at its
object offset `+0x3d8`. This is a conditional initialization value: it reaches
the runtime object only if the selected type-4 configuration load succeeds,
and it reaches `0x20000bc7` only when the registered callback runs. It is not
a V6 event-time observation.

The only supported name is the section/object name `AP_EXCO`. Neither its
512-byte metadata record nor the exact field handoff provides a string,
schema member, API name, unit, or semantic label for offset `+0x3d8`.
Accordingly this report calls it the **unnamed AP_EXCO byte at `+0x3d8`**. It
does not relabel numeric 20 as a physical value or named product setting.

## Selected AP_EXCO configuration object

The selected 5 MiB package has SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
The established 21-row configuration mapping table begins at FILE
`0x3ccbc`; row 10 at FILE `0x3cdd4` is exactly:

| field | value |
| --- | ---: |
| name | `AP_EXCO` |
| name linked VA / stored FILE | `0x3dd8c` / `0x3df8c` |
| first destination / maximum | `0x2000ff14` / `0x033a` |
| second destination / maximum | `0x2001024e` / `0x1200` |
| first / second logical prefix | `0x1b0000` / `0x1b0400` |

The two physical destination ranges are contiguous:

```text
0x2000ff14 + 0x033a = 0x2001024e
```

The selected directory record at FILE `0x85e00` is type 4 and provides:

| metadata field | value |
| --- | ---: |
| name | `AP_EXCO` |
| logical base | `0x1b0000` |
| first present / source offset | `1` / `0x102200` |
| first destination offset / length | `0` / `0x033a` |
| second present / source offset | `1` / `0x102600` |
| second logical offset / length | `0x0400` / `0x1200` |

With selected configuration base FILE `0x80000`, the generic successful
type-4 copy path therefore binds:

```text
FILE 0x182200..0x182539 -> 0x2000ff14..0x2001024d
FILE 0x182600..0x1837ff -> 0x2001024e..0x2001144d
```

Object offset `+0x3d8` falls in the second region:

```text
0x3d8 - 0x33a = 0x9e
source FILE = 0x182600 + 0x9e = 0x18269e
destination = 0x2001024e + 0x9e = 0x200102ec
```

FILE byte `0x18269e` is `0x14`, decimal 20. Its neighboring payload is raw
binary numeric data; the metadata's only meaningful printable identifier is
the section name `AP_EXCO`. The generic copy code proves initialization
provenance, not successful execution on the current TV or later immutability.

## Startup lookup and pointer mapping

Image-1 application entry calls context initialization at VA `0x1ba12`:

```text
1ba12  bl 1bcc4
```

Within VA `0x1bcc4`, the material lookup is:

```text
1bcde  adr r1,1bd4c           ; "AP_EXCO"
1bce0  movs r0,#0
1bce2  bl 1bc24               ; table lookup, first-destination accessor
1bce6  ldr r1,=0x200002cc
1bce8  str r0,[r1]
```

The lookup at `0x1bc24` finds the named row and loads its word at `+4`, the
first destination `0x2000ff14`. It calls mapper VA `0x1bb74` with selector
zero. For inputs in the bounded `0x20000000` range, that mapper adds
`0x25000000`, giving:

```text
0x2000ff14 + 0x25000000 = 0x4500ff14
```

The getter is exact and has no fallback:

```text
38e8  ldr r0,=0x200002cc
38ea  ldr r0,[r0]
38ec  bx  lr
```

Thus, on successful selected configuration lookup, slot `0x200002cc`
contains mapped AP_EXCO pointer `0x4500ff14`. Reset decompression initializes
that slot to zero; application entry treats a failed context initialization
as fatal and does not continue normal startup.

This mapping is code-defined address translation. It should not be confused
with the still-conditional image-1 `0x2001...` versus image-0 `0x4701...`
RTP alias discussed elsewhere.

## Registration and runtime copy

Ordinary registration routine `0xaee4` calls VA `0x195f8` at `0xaef6`.
VA `0x195f8` stores Thumb callback pointer `0x00018c95` in the callback table
rooted at CPU `0x20000468`. The callback begins at even VA `0x18c94`, and its
first call is:

```text
18c96  bl 3934
```

The relevant beginning of VA `0x3934` is:

```text
3938  bl   38fc                    ; independent RTP root
393e  bl   38e8                    ; AP_EXCO pointer
3944  bl   38f4                    ; fixed base 0x20000500
394e  ldrb r0,[AP_EXCO,#0x3d8]
3952  strb r0,[0x20000500,#0x6c7]
```

Therefore the concrete runtime addresses are:

```text
source  0x4500ff14 + 0x3d8 = 0x450102ec
target  0x20000500 + 0x6c7 = 0x20000bc7
```

The exact `STRB ... #0x6c7` encoding occurs once in selected image 1. The only
direct `BL` to VA `0x3934` is callback site `0x18c96`. These bounded facts do
not exclude a computed writer or external agent, but they establish the
ordinary positive writer and registration chain.

The later ordinary function VA `0xc250` does not create this selector. It
reads byte `0x20000bc7`, mirrors its numeric value into halfword
`0x200004c2` when changed, and stores boolean nonzero state in
`0x200004c4`. It then reaches the RTP orchestrator. The event-736 predicate
still reads `0x20000bc7` directly.

## Exact effect on event-736 threshold selection

The copied AP_EXCO byte does not choose predicate mode. Mode remains selected
by `0x200004aa/0x200004ac`. Its only proved event-736 role is choosing the
threshold source for modes 1 and 6:

| predicate mode | AP_EXCO-derived byte zero | AP_EXCO-derived byte nonzero |
| ---: | ---: | ---: |
| 1 | `uint16[R+0x2430]` | `uint16[R+0x24c4]` |
| 6 | `uint16[R+0x24c0]` | `uint16[R+0x24c4]` |
| 2 | `uint16[R+0x2432]` regardless | same |
| 4 | `uint16[R+0x2440]` regardless | same |

If the selected AP_EXCO payload value 20 was loaded and the callback copied
it without a later change, its nonzero truth value would select `R+0x24c4`
for mode 1 or 6. That is a conditional static initialization inference, not
proof of the value at the V6 event. V6 did not sample `0x20000bc7` or the
AP_EXCO source byte.

## Boundary reached and deliberately not crossed

This trace closes the ordinary selected-package chain through the generic
successful configuration copy. Proving which configuration/high bank was
live, how a persisted selection chose it, or whether later code rewrote the
AP_EXCO payload would enter excluded bank/persistence work or require a new
live observation. The trace stops here.

No field-level symbol or API name was recovered for `AP_EXCO+0x3d8`. The
numeric default 20 and zero/nonzero branch are exact; an interpretation such
as temperature, panel mode, damage level, ONSEN setting, voltage, or timing
would be speculation. Nothing here supports modifying the payload, mirror
byte, or selected threshold.

## Reproduction

`rtp-alternate-source-context.py` pins the package and corrected coordinates,
configuration-table row and metadata, both payloads and byte arithmetic,
generic copy body, startup lookup/mapping, pointer slot/getter, callback
registration, exact source/target copy, and threshold consumers. It uses only
Python's standard library:

```sh
python3 rtp-alternate-source-context.py
python3 -O rtp-alternate-source-context.py
```

Both invocations are offline and emit one compact JSON result.
