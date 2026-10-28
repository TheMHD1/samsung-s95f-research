# Lane-table writers, publication and lifetime

The two eligibility tables have distinct stock lifetimes. The primary
halfword table is a publication containing a flag and counter-derived bits;
the secondary byte table is a directly tested, sticky flag array. **Neither
is disposable memory, and neither is an established physical-pixel mask.**
This is a host-only selected-source audit. It implements no target operation,
write helper, operation route, UI action, reset or persistent change.

All addresses below are image1 linked addresses, file offset `VA+0x40200`.
The package SHA256 is
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
CPU SRAM addresses use the separate DW-qualified image1 alias for the bus
view; for example CPU`0x20010000` corresponds to bus`0x47010000`. This is
not a claim that every instruction in this source has been live-attested.
DX sampled the unpacker entry, not this later table-gate or writer body.

## Correction to the initial trainer lead

The parent initially suggested that `c01e -> c058` was gated by CPU`4aa`.
It is gated by **u16 CPU`0x200004a2 == 1`**:

```text
bfe0  ldr r0,[pc,#0x6c]   -> literal c050 = 0x200004a2
bfe2  ldrh r0,[r0]
bfe4  cmp r0,#1
bfe6  bne c024           -> skips training
...
c01e  bl c058
```

CPU`0x200004aa` is a different literal at`c030`, used earlier to select
category4 dispatch at`bfae`. AA0/AC2 does not by itself disable this trainer.
The separate secondary override SB still depends on AA/AC and byte4cc.
`training-gate-correction.json` is the immutable early correction, SHA256
`fd8cfacff023f4850f358b80d2585b40946e8827cf184381b992553b3f7ff8aa`.
It preserves source ranges and the earlier retained sample:4a2=0,4a8=1920,
AA0/AC2,4cc0 and root246a/246c=0/0. That sample supports a disabled trainer
at its read time, without establishing the history of either table.

## Counter and secondary-flag producer

The unpacker saves its original second pointer B on entry. At`be42` it
loads that pointer and at`be4a..be88` decodes each six-byte packed group into
four local u16 values. It accumulates these B values at stack`+0xf14`.
When4a2 equals1, the tail divides that sum by u16 CPU`0x200004a8` and passes
the quotient plus the local vector to`c058`. Channel-specific quotient
mirrors are root`+247c/+247e/+2480`.

This quotient is only a full-vector mean if the loop reached and decoded
the whole vector. An earlier comparator returning0 can exit at`bfac` before
later lanes are decoded. The training tail is not independent proof that
all local values were fresh, nor proof of a physical mean or sensor unit.

`c058` reads factor root`+246a` and threshold root`+246c`. Its exact integer
arithmetic, modeled in `lane_model.py`, is:

```text
delta = ((u32(mean) * u16(factor)) modulo 2^32) >> 8
upper = u16(mean + delta)
lower = u16(mean - delta)
outside = value > upper or value < lower
```

Both comparisons are strict outside a band with inclusive endpoints. There
is no recovered12-bit saturation or clamp. For each outside observation it
increments the u16 counter at **CPU`0x2000ba4c + 2*lane`**. The truncated
counter is reread and compared strictly `> threshold`. If exceeded, the
secondary byte at **CPU`0x2000c95c + lane`** is set to1. If that byte was
previously0, u16 CPU`0x200004a4` is incremented; a mirror is stored at
root`+2482` after the loop.

The four unrolled secondary stores are`c0cc/c118/c164/c1b0`; nearby
`c15e/c1aa` are immediate setup instructions, not the final stores. There
is **no in-band counter reset in this function**. Counts accumulate across
nonconsecutive outside observations; flags remain set on an in-band sample.
Counter and aggregate wrap at16 bits. Counter wrap occurs before the
threshold test, and does not clear an already set flag. Factor0/threshold0
would make the first unequal observation sufficient **if this trainer ran**;
their captured zeros do not prove that it ran.

A second low-SRAM writer exists at`c314`. It decodes a supplied packed
vector and uses root`+245a/+245c` for a similar band/counter/flag update
against the same arrays. Its caller`c470` is reached at`c2da` only when
root`+2458==1`, and its body requires root`+2460==1` and a nonzero
separate context field`+202`. The bounded source records only the low-SRAM
effects. The storage/provider/control path supplying that vector was not
followed, invoked, packaged or proposed as an experiment.

## Primary publication owns all16 bits

Two proved stores populate the primary table through the current root:

- `b912`, after root getter`b8aa`, when global4a2 equals1 and
  root`+246e==1`.
- `c53c`, within the separate`c470` path, after its control conditions
  and end-of-sequence condition.

Both publish, for each lane below CPU4a8:

```text
u16[root + 2*lane] =
    (u8[secondary + lane] + 2*u16[counter + 2*lane]) modulo 65536
```

On these publisher paths bit0 equals the secondary byte's low bit. The
remaining bits carry counter-derived data. If the secondary byte is the
known0/1 form, the halfword retains only the low15 counter bits: counter0
and counter32768 can publish the same word. Thus a zero primary word does
not prove an empty counter history. The source does not justify assigning
all primary bits a generic exclusion meaning.

`b8a8` subsequently sets4a2 to2 and calls`ca84`. The latter clears record
metadata and other processing arrays; it **does not clear the BA4C counters
or C95C flags**. Their directly referenced addresses differ. This means
record reset/zero N is not proof that these eligibility tables were reset.
Primary and secondary samples can also disagree because publication and
updates occur at different times. EB correctly retains both rather than
assuming equality.

## Initialization and known clears

| Source path | Known effect |
|---|---|
| Selected image0 scatter row9 | Writes zeros to alias`0x47010000+0x47bc`, including the complete1920-entry primary region`root..root+0xf00`. |
| Selected image1 BSS scatter | Zeros`0x200004f8..0x2000e19c`, covering the complete1920-counter BA4C and1920-byte C95C arrays. |
| Runtime initializer`cb2c`, loop`cb66..cb7a` | Explicitly clears BA4C u16 counters and C95C bytes up to current4a8. It does not republish the primary low region. |
| `c470` reset branch`c4da..c4ee` | Clears the same counter/flag arrays under its own conditions, without a simultaneous primary publication in that branch. |
| `ca84` | Clears other arrays and record metadata, with no direct BA4C/C95C clear. |

The root pointer is initialized by image1's decompressed startup data at
CPU`0x200004e0`. The primary cold-zero output is independently reproduced
with the existing hash-pinned scatter decoder. These establish packaged
startup writes, not a guarantee that MODE2 executes both startup domains
or restores every current table. DZ's unclosed reset/storage boundary
continues to apply. No zero run, initializer name or successful stock
recovery alone supplies a restoration proof for a later diagnostic write.

`source-audit.json` includes all32 syntactic PC-relative literal references
to BA4C/C95C in the examined image1 interval. Their coherent uses fall in
the reader, publishers, two update families and known clears described
above. This is a **bounded direct-reference census**, not a complete
reachable-writer proof: computed bases, indirect copies, DMA, other CPU
writers and externally supplied operations remain outside it. No other
bits or addresses are declared free on the strength of that census.

## Completed ED data and the next bounded diagnostic

The coordinator's completed `ED/table-read-01` was separately accepted with
16 headers/32 bulks and clean stage removal. This audit independently
checks the retained raw hashes, without rereading the TV:

- All68 primary words and secondary bytes for lanes568..635 are0.
- M has4a2=0,4a8=1920, AA0/AC2,4cc0 and root0x20010000.
- R has operating mode4,2458=1,2460=0,246e=0,246a/246c=0/0;
  start/end R bytes match.

At these sequential values SB is false and all68 lanes are **locally**
admitted if execution reaches them. The known trainer and the two primary
publication paths are inactive at the sampled control values. This is not
proof of continuous writer quiescence throughout a later transition. The
BA4C counters themselves were not captured by EB. Actual field metadata and
original-file hashes are in `completed-ed-context.json`; no OEM raw sample
is duplicated here.

These actual zeros permit designing a small, separately reviewed volatile
diagnostic; this audit does not implement it. For example, a documented
fault-prefix lane570 has its fixed primary halfword at CPU`0x20010474`,
bus`0x47010474`. Setting only bit0 in a freshly verified original word
would test the source's unconditional primary skip for **that lane**, even
when SB is true. It does not predict prevention of an aggregate fault from
other lanes or attest any electrical safety. A useful outcome would compare
that lane's comparator/tuple evidence under comparable current references,
not merely whether the whole panel darkens.

A concrete future design must preserve the other15 bits, retain exact
originals, qualify the current gate body/context, recheck the known writer
controls and both tables immediately before action, and stop on any
unexpected change. It must have one fixed action and a separate bounded
restore with guarded readback, same-device/phase/receipt cleanup provenance
and no retry after an ambiguous transfer. Restore must not overwrite a
legitimate newly published word or clear a newly produced secondary flag.
If originals, controls or phase cease to match, central reconciliation is
required; MODE2 must not be called a guaranteed mask restore. Current source
does not justify opening a persisted/high-bank operation route, bypassing
all lanes or treating this as a root-cause fix.

## Reproduction

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/tcon-capstone python3 audit.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/tcon-capstone python3 -O audit.py
PYTHONDONTWRITEBYTECODE=1 python3 test_lane_model.py
PYTHONDONTWRITEBYTECODE=1 python3 -O test_lane_model.py
```

The source checker verifies exact instructions/literals, source intervals,
cold-init outputs, immutable correction, bounded reference census and saved
ED context. The pure tests cover target integer widths, wrap, strict band
edges, cumulative counters, sticky flags, packed publication, preserved
primary bits and the local-admission predicate. Explicit exceptions remain
active under`-O`. Input provenance and the frozen inventory pin all used
artifacts. No helper, controller I/O or live observation is generated by
these scripts.
