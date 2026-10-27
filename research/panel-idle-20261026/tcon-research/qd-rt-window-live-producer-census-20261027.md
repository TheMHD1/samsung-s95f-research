# Image-0 fixed RT-window live-producer census

## Result

For the selected retained profile, the proven writers covering image-0
`0x4701240a` are the already established reset scatter (zeroes the window) and
AP_RTP configuration copy (loads the `0x47012400..0x470124ff` subrange).  This
new bounded census found **no direct accessor-caller construction of `+0x240a`
that stores or copies to the field** outside those two block producers.  It
does not prove a global absence of a computed-address, DMA, boot, or external
writer.

The live reader remains a separate operation: canonical linked VA `0x214d4`
(stored file `0x216d4`) calls the fixed-root accessor at VA `0xef94` (stored
`0xf194`), forms `+0x240a`, loads a byte, and tests bit zero before the
selector-`0x10` path.  This is a reader/gate, not a recovered producer.

## Exact bounded evidence

The selected package SHA-256 is
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
This report uses the corrected coordinate convention `FILE = VA + 0x200` for
image 0.

The fixed root word `0x47010000` occurs only at stored offsets `0xf198`,
`0x3ce50`, and `0x3e3d4` in image 0.  Their bounded roles are:

| Stored location | Role | Relation to `0x4701240a` |
| ---: | --- | --- |
| `0xf198` | literal returned by accessor at VA `0xef94` | reader base |
| `0x3ce50` | AP_RTP table second destination | known block-copy base, length `0x2400` |
| `0x3e3d4` | reset scatter destination | known all-zero reset block, length `0x47bc` |

The known F300 selector-`0x128` write path is excluded as a producer: it
stages the scalar at its separately recovered RAM location and has no
recovered store/copy into this fixed window.  Likewise, the image-1
`0x2001240a` store is a different addressed operation and is not used as
evidence of an image-0 writer here.

## Accessor caller census

I decoded every halfword-aligned Thumb-2 direct `BL` encoding in the image-0
file interval and reconstructed its signed immediate target.  Exactly **91**
direct calls resolve to the fixed-root accessor at canonical VA `0xef94`.
This is a finite direct-call census, not a claim about indirect calls.

Among those 91 call sites, only the live-loop caller at VA `0x214d6` directly
constructs the exact `+0x240a` immediate.  Its canonical bytes are:

```text
214d6  bl    0xef94        ; returns 0x47010000
214dc  movw  r0,#0x240a
214e0  ldrb  r0,[r0,r4]    ; r4 is returned base
```

The complete image-0 direct-immediate pattern for that construction is unique
at stored file `0x216dc`; its next memory operation is `ldrb`, not `strb`,
`strh`, `str`, or a block-copy call.  Thus the accessor-caller census adds a
concrete dataflow result: the exact live producer candidate is only a reader.
The other 90 accessor callers may read or write other fields of the returned
object, but none directly constructs this exact displacement.

## Coverage and next edge

This is deliberately narrower than a whole-program writer proof.  It covers
all 91 decoded direct accessor calls plus the exact `+0x240a` direct-immediate
use, and distinguishes both known block producers.  It does not cover an
offset synthesized without that immediate, indirect copy/DMA descriptors, or
code outside image 0.  A meaningful next missing edge is a concrete
runtime/boot/DMA mapping or copy descriptor whose destination range includes
`0x4701240a`; another bare `+0x240a` match is not enough.

Run `PYTHONPATH=/tmp/tcon-capstone python3
tcon-research/qd-rt-window-live-producer-census-20261027.py` to verify the
hash-pinned landmarks.  No TV, root, network, controller, or firmware action
was performed.
