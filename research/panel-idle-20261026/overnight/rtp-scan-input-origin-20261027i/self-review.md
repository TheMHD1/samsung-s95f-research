# Self-review of RTP scan-input origin trace

Recorded 2026-10-27 UTC. This is an author self-review, not an independent
review. It rechecks `rtp-scan-input-origin.md` and its verifier against the
selected package and retained evidence. It made no TV, network, root, USB,
controller, UI, firmware, reader, protection, persistence, high-bank, POFLG,
return-guard, or storage operation. It did not edit either reviewed artifact
or any frozen D7 file.

Reviewed pins:

```text
rtp-scan-input-origin.md
  84ead8cd06b5b0136c7ee05b651094fb43c7387b7f26262f1fd25a4ab74499f2
rtp-scan-input-origin.py
  09ea55f6096de5aa1332f571137471053d3ca043e1de58e3342af9d165d7824b
selected package
  bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0
```

## Decision

No correctness blocker was found in the bounded claims. The main negative
claim is correctly narrow: packaged ordinary code does not increment `y` in
the packed lane loop, and `R+0x2404-1` is compared with neighboring
`d2/b2`, not with `y` at `d0`. The report does not promote `y=2159` into a
physical row or use the owner's damage photos as a coordinate transform.

One qualification is worth keeping visible: the `R+0x2452/2454` comparisons
are only part of a later action's gate. VA `0xc7e8..0xc7f0` first requires
`R+0x244e==1`, and other conditions follow. The report calls the range a
required later gate rather than a sufficient trigger, which is accurate.

## `d0` versus neighboring `d2`

Literal resolution in orchestrator VA `0xb644` is unambiguous:

| instruction | resolved object | width/effect |
| ---: | --- | --- |
| `0xb6f2` | `0x200004d4` | `LDRH`, passed as `RGB` |
| `0xb6f6` | `0x200004d0` | `LDRH`, passed as `y` |
| `0xb706` | `0x200004d2` | `LDRH`, compared with `R+0x2404-1` |
| `0xb716` | `0x200004b2` | `LDRH`, compared with `R+0x2404-1` |
| `0xb732..0xb738` | `b4 -> d0` | halfword copy for later `y` |
| `0xb73a..0xb740` | `b2 -> d2` | separate halfword copy |
| `0xb742..0xb748` | `b0 -> d4` | halfword copy for later `RGB` |

Capstone independently decodes both root-limit sequences as:

```text
movw r0,#0x2404
ldrh r0,[r0,r6]
subs r0,#1
ldrh r1,[d2 or b2]
cmp  r0,r1
bne  b732
```

The following conjunction tests `d4==2` and `b0==2`, then may call `0xb8a8`.
Neither `0x200004d0` nor `0x200004b4` participates in that last-index
comparison. `root_2404_directly_compares_y=false` is therefore a positive
instruction-level conclusion, not an inference from naming.

## Widths and input-header handoff

The two direct `d0/d4` writer groups use these exact widths:

```text
b690  LDRH [B+6] -> b694 STRH d0
b69a  LDRB [B+2] -> b69e STRH d4

b734  LDRH b4 -> b738 STRH d0
b73c  LDRH b2 -> b740 STRH d2
b744  LDRH b0 -> b748 STRH d4
```

The memory-mapped input handoff at VA `0x398a` also preserves the report's
claimed widths:

```text
low8 [0x5860140c]  -> UXTB -> stack halfword 0
low16[0x58601410]  -> UXTH -> stack halfword 1
low16[0x58601414]  -> SXTH then UXTH -> stack halfword 2
```

The `SXTH`/`UXTH` pair on the third word preserves its low-16 bit pattern; it
does not turn the later `LDRH` into a signed `y`. Helper VA `0xbb58` copies
those three stack halfwords to `b0/b2/b4`. The producer or ownership of
memory-mapped block `0x58601408` is not established, so stopping there is
appropriate.

The aligned literals for `d0` and `d4` each occur once, and all decoded
references are in the orchestrator. This supports the direct ordinary
writer census. It remains deliberately short of excluding computed-address,
interrupt, later-loaded, or external writers.

## 2,880-byte and 1,920-lane arithmetic

VA `0xcb36..0xcb3e` loads `R+0x2402` as an unsigned halfword and stores it in
CPU `0x200004a6`. The selected AP_RTP payload and retained late root window
both contain 2880.

The packed loop has independently decoded positive fixtures:

```text
bd72  MOVS r4,#0        ; logical x base
be34  MOV.W fp,#0       ; packed byte offset
bf98  ADDS r4,#4
bf9a  ADD.W r0,fp,#6
bf9e  UXTH.W fp,r0
bfa2  LDRH extent (0x200004a6)
bfa6  CMP fp,extent
bfa8  BLT.W be3a
```

The four direct calls to comparison helper `0xbbbc` are VAs `0xbedc`,
`0xbf18`, `0xbf5a`, and `0xbf90`. Their surrounding code extracts four
unsigned 12-bit lanes and supplies indices `r4`, `r4+1`, `r4+2`, and
`r4+3`. With a strict `fp < 2880` continuation, group starts are
`0,6,...,2874`: exactly 480 groups and 1,920 logical lane ordinals
`0..1919`.

There is an additional corroborating calculation not needed by the report's
arithmetic: VA `0xcb42..0xcb4e` computes `(R+0x2402 << 3) / 12` and stores it
at CPU `0x200004a8`; for 2880 this is also 1920. This does not prove a
physical panel width.

## Detail-row emission ordering

Formatter prologue VA `0xc5d8` moves incoming `r2` (`y`) to `r8`. The detail
row call is VA `0xc638`. Its argument setup includes `r8` on the stack and
the `RGB`/`x` registers in the documented positions.

The root range is tested substantially later:

```text
c7e8  load R+0x244e and require 1
c7f2  load R+0x2452; reject when lower > y
c7fc  load R+0x2454; reject when upper < y
```

The branch mnemonics are signed `BGT`/`BLT` after zero-extending root
halfwords; for retained defaults 2157 and 2160 this is equivalent to the
reported inclusive interval `2157 <= y <= 2160`. Because `0xc638` precedes
`0xc7f2`, this range cannot be presented as the filter that emitted the 31
retained detail rows. The final report explicitly makes that ordering
distinction.

The retained 1,756-byte V6 delta is correctly pinned and parses to 31 rows,
all `RGB=0`, all `y=2159`, with the exact logged `x` set
`{570,571,620,621,630,631}`. Those are observations of emitted detail rows,
not a census of every packed lane or a physical-coordinate proof.

## Verifier quality and residual limits

Normal and optimized executions are byte-identical, and bytecode compilation
passes. The verifier contains meaningful positive checks: exact input-copy
instructions, literal destinations, callback/direct-call relationships,
four comparison-helper calls, complete unpacker hash, loop reset/advance,
AP_RTP mapping, retained values, formatter argument preservation, and V6 row
parsing.

Residual limits are correctly preserved:

- the selected package is a retained candidate, not a complete immutable
  hash of the currently executing controller image;
- sequential retained reads are not event-time snapshots;
- `y` may be generated as a scan-related quantity outside image 1, but the
  observed image-1 code does not establish that physical meaning;
- the physical bottom-edge spot and vertical band cannot be mapped using
  numeric coincidence with 2159 or the logged `x` values.
