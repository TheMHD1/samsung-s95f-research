# RTP ordinary scan-input origin

Recorded 2026-10-27 UTC. This is a finite offline trace of the selected
image-1 package and already-retained V6 artifacts. It covers only the
ordinary `x`, `y`, `RGB`, packed-source, and loop-bound handoff. It made no
TV, root, USB, controller, network, UI, firmware, reader, threshold,
protection, return-guard, high-bank, persistence, or storage operation. All
75 frozen D7 files remain unchanged.

## Result

The three diagnostic fields do not have the same origin:

- `x` is the ordinary software loop index of an unpacked 12-bit lane. It is
  reset to zero in each unpacker invocation and advances through four lane
  ordinals while the packed byte offset advances by six.
- `y` is an unsigned halfword copied into CPU RAM `0x200004d0` before the
  scan and passed unchanged through selector, unpacker, comparison helper,
  and formatter. The ordinary packed loop does not increment or reset it.
- `RGB` is a byte/halfword scalar copied into CPU RAM `0x200004d4` and likewise
  held constant through one packed scan. The package format names it `RGB`,
  but no physical color/electrical meaning is assigned here.

The recovered positive producer chain reaches an ordinary input-header
handoff from an `EXCO_PAR2_S0`-associated address block. Its individual
fields and physical producer remain unresolved. It does **not** prove that
`y` is a physical panel row:

```text
EXCO_PAR2_S0-associated address block / source header
        |
        +-- low16[0x58601414] -> 0x200004b4 -> 0x200004d0 -> y
        +-- low8 [0x5860140c] -> 0x200004b0 -> 0x200004d4 -> RGB

dynamic packed-B header can also seed:
        uint16[B+6] -> 0x200004d0
        uint8 [B+2] -> 0x200004d4

packed B payload begins at B+8
```

The selected package record at FILE `0x83c00` is named `EXCO_PAR2_S0` and
contains address word `0x58601400`; the refresh root `0x58601408` is exactly
that word plus eight. This establishes association with that named parameter
block. It does not name the individual `+0x0c/+0x10/+0x14` fields, prove the
record was loaded for the observed boot, or establish the physical producer,
units, or panel-coordinate transform. That unresolved physical edge remains
the finite stopping point.

## Exact `y` and `RGB` RAM writers

The aligned literal census for these two CPU addresses is finite:

```text
0x200004d0 literal b7b0: refs b692, b6f6, b736
0x200004d4 literal b7b4: refs b69c, b6c2, b6f2, b71e, b746
```

Within ordinary orchestrator VA `0xb644`, the direct writers are copies, not
arithmetic updates.

The refresh path reads a dynamic packed-B header:

```text
b68c  B = *(uint32 *)0x20000498
b690  y = uint16[B+6]
b692  uint16[0x200004d0] = y
b696  B = *(uint32 *)0x20000498
b69a  RGB = uint8[B+2]
b69c  uint16[0x200004d4] = RGB
```

That route does not run the packed selector in the same invocation. The
ordinary postlude refreshes the next scan scalars from callback-latched input
fields:

```text
b732..b738  uint16[0x200004d0] = uint16[0x200004b4]
b73a..b740  uint16[0x200004d2] = uint16[0x200004b2]
b742..b748  uint16[0x200004d4] = uint16[0x200004b0]
```

Immediately before the only direct selector call, the orchestrator merely
loads those values:

```text
b6f2  r1 = uint16[0x200004d4]   ; RGB
b6f6  r0 = uint16[0x200004d0]   ; y
b6fa  call b7ec
```

The selector preserves them and passes `r2=y, r3=RGB` to unpacker `0xbd58`.
The unpacker and formatter retain those scalar arguments unchanged. There is
no direct add/subtract, loop update, or reset of `0x200004d0/4d4` in this
ordinary chain.

## Input-header handoff into `0x200004b0/b2/b4`

Registered callback VA `0x18c94` calls ordinary refresh VA `0x3934`. That
body reads the memory-mapped input block rooted at `0x58601408` and constructs
a small stack header:

```text
low8 [0x5860140c] -> stack halfword 0
low16[0x58601410] -> stack halfword 1
low16[0x58601414] -> stack halfword 2
```

VA `0x3a0e` then calls the only direct instance of handoff helper `0xbb58`.
Its first three stores are:

```text
stack halfword 0 -> uint16[0x200004b0]
stack halfword 1 -> uint16[0x200004b2]
stack halfword 2 -> uint16[0x200004b4]
```

Accordingly, the `y` scalar used by a later ordinary packed scan descends
from the third input-header field, while `RGB` descends from the first. The
neighboring `0x200004b2/d2` field is separate. Exact callback scheduling can
make these values one handoff behind the active producer; the retained text
does not provide an instruction timeline.

This chain positively identifies data movement and associates its address
block with `EXCO_PAR2_S0`, but deliberately leaves the individual fields and
physical source unnamed. A term such as row counter, scanline, timing phase,
tile index, or electrical channel would require evidence beyond this body.

## `x` is the software lane index

Unpacker VA `0xbd58` resets the logical lane index in `r4` to zero at
`0xbd72` and the packed byte offset in `r11` to zero at `0xbe34`. For each
six-byte group it decodes four unsigned 12-bit lanes. The four helper calls
use indices `r4`, `r4+1`, `r4+2`, and `r4+3`. At VA `0xbf98` the loop does:

```text
r4  += 4       ; next logical lane ordinal
r11 += 6       ; next packed group
```

Root halfword `R+0x2402` is copied to CPU halfword `0x200004a6` by VA
`0xcb36..0xcb3e`. The packed loop compares its six-byte offset `r11` with
that value at VA `0xbfa2..0xbfa8`. The selected AP_RTP default and retained
late value are both 2880, so the configured ordinary extent is:

```text
2880 packed bytes / 6 bytes per group = 480 groups
480 groups * 4 unsigned 12-bit lanes  = 1920 x ordinals
nominal software x range              = 0..1919
```

This is a representation count, not a physical width. The V6 printed values
`x=570..631` are qualifying logged lanes within that software range; they do
not locate a panel defect without an additional transform.

## What the 2160 and 2157..2160 fields actually gate

The selected AP_RTP defaults, also preserved in the retained late root
window, are:

```text
R+0x2402 = 2880
R+0x2404 = 2160
R+0x2452 = 2157
R+0x2454 = 2160
```

The 2160 field at `R+0x2404` is used in VA `0xb6fe..0xb71c` as `2160-1`.
Crucially, it is compared with `0x200004d2` and callback field
`0x200004b2`, not with `y` at `0x200004d0`. A later conjunction also checks
the current/next `RGB` fields for value two before calling `0xb8a8`.
Therefore this code supports a last-index check on the **neighboring header
field**, but does not prove that the printed `y` scalar itself is an ordinary
counter spanning `0..2159`.

The fields `R+0x2452/2454` do directly bound the formatter's `y` argument for
a later gated action. Formatter prologue VA `0xc5d8` saves incoming `r2` as
`r8`; VA `0xc7f2..0xc804` requires:

```text
uint16[R+0x2452] <= y <= uint16[R+0x2454]
```

for that later path. Defaults 2157 and 2160 make `y=2159` eligible. The detail
row formatter call at VA `0xc638` occurs earlier; this later range check does
not itself explain or filter those already-emitted rows. Every one of the 31
retained V6 detail rows nevertheless has `y=2159` and `RGB=0`, but that text
does not prove that all scan inputs had those values or that 2159 denotes the
physical bottom row.

The narrow conclusion is:

- `x` is conclusively the inner software lane index;
- `y` is conclusively a per-scan input/header scalar, not incremented by that
  inner loop;
- `y` participates in a later ordered 2157..2160 firmware gate and
  numerically equals `R+0x2404-1` in V6;
- the code compares `R+0x2404-1` to a different neighboring field, so it does
  not close the claim that `y` is the ordinary last-row index;
- neither the owner's bottom-edge spot nor vertical dark band supplies the
  missing software-to-physical coordinate transform.

## Reproduction

`rtp-scan-input-origin.py` pins the package, AP_RTP payload and retained root
window, the exact `EXCO_PAR2_S0` metadata record and `+8` address relation,
all direct `0x200004d0/4d4` literal references, exact writer/load slices,
callback/header handoff, source pointers, 12-bit unpacker and stride,
`R+0x2402/2404/2452/2454` consumers, and all 31 V6 `y/RGB` rows. It includes
positive fixtures for the input-header stores and lane/byte advances and uses
only Python's standard library:

```sh
python3 rtp-scan-input-origin.py
python3 -O rtp-scan-input-origin.py
```
