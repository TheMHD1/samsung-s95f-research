# AW: the post-lifecycle state includes a changed ordinary diagnostic input

Recorded 2026-10-27 UTC. This follow-up preserves AV's frozen evidence and
the TV's UI/power state. It adds offline pre/post interpretation and exactly
one unchanged pointer-gated W read. No UI, power, firmware or controller
configuration action was sent in this follow-up. Physical picture is still
unobserved.

## What changed in the saved RT samples

The AV pre-X and retained post-X cycle80 samples differ at only12 of256 R
bytes. The known stored limit candidates remain `[200,0,0,200,40]`, and the
mode selectors remain `aa=0, ac=2`, conditionally selecting mode1 in both
samples. The changed fault tuple is accompanied by other selective state:

| Field or source-backed relationship | Earlier faulted set | Delayed clean set |
| --- | --- | --- |
| stop / fault / ordinary gate | `1 / 0x1001 / 0` | `0 / 0 / 1` |
| alternate selector C+7 and its M mirror | `1` | `0` |
| conditional mode1 limit source | `R+0x24c4 = 40` | `R+0x2430 = 200` |
| mode1 aggregate/history/non-mode6 latch | `44 / [6,0,0,6] / 44` | zero |
| scan-enable argument | `0` | `1` |
| shared mode4/mode6 latch | `54` | `48` |

Thus this is not an isolated fault-word clear, a rewrite of stored limits,
or a wholesale zeroing of retained state. Some other changed halfwords remain
unnamed. The clean R window still differs from the packaged AP_RTP payload
at15bytes; it is not a match to that initialization template.

These are sequential sampled states. They do not identify which initializer
or writer ran, when the changes occurred, whether MODE2 exclusively caused
them, or whether physical panel light returned. Only post-X cycle80 raw is
retained; the earlier79clean cycles exist in the native summary.

## New later ordinary/derived snapshot

The existing unchanged W helper ran once after fresh same-boot USB46/config1,
unbound-interface and zero-userspace-holder checks. It matched live pointer
anchors before reading the824-byte ordinary AP_EXCO prefix and1004-byte
derived object. All three reads/six bulk transfers were exact; release/close,
terminalReady and stage removal passed. The independent audit replayed all20
authenticated root calls. No helper or new background collector remains.

Its wrapper terminal anchor is Linux uptime137706.50, about13minutes after
AV's last retained clean R. W does not timestamp each individual transfer and
does not read RT. Therefore this snapshot is not a simultaneous RT/input
tuple or proof that RT was still clean at that later time.

Compared with the older AK W snapshot, the later data show:

| Ordinary/derived field | Older post-fault AK | Later post-lifecycle AW |
| --- | --- | --- |
| gates ca / cc / ce / recomputation116 | `1 / 1 / 0 / 1` | same |
| comparison quantities P0/P1/P2 | `7,464,960` each | same |
| P3 | `8,128,512` | same |
| initial indexes / recomputed indexes | `3/3/3`, `6/6/6` | same |
| caps / common multiplier | `6/6/6`, `900` | same |
| recomputed sum mirrors X0/X1/X2 | `8,254,590 / 8,251,261 / 8,250,967` | `31,868 / 21,738 / 35,229` |
| debounce threshold / counter e2 | `30 / 30` | `30 / 0` |
| output e6 / other output2fc | `1 / 0` | `0 / 0` |
| derived byte3d8 | `1` | `0` |
| derived bytes0 /1 | `3 / 10` | `3 / 8` |

For the captured ca=cc=1, ce=0 case, the selected-source first helper's
condition is `any(P[i] < X[i])` for lanes0..2. That condition is true in the
older snapshot and false in the later snapshot. A mature true condition is
numerically consistent with old counter30/output1; a false condition is
consistent with new counter0/output0. The separate2fc operand is zero in
both snapshots. The derived formula `bool((e6 & 1) || u16[2fc])` therefore
matches saved derived3d8 in each case.

This supplies a false-condition comparison to the previously reconstructed
true-condition case. Under the selected-source model it is compatible with
the ordinary diagnostic route producing a different derived Boolean. The
image1 callback can copy that Boolean into the alternate-selector byte.
There is no invocation record or atomic source/mirror pair here: this does
not prove callback consumption or directly explain the separate M+0x2a word.
The source words themselves, their producer, cadence and physical units
remain unidentified. A saved sum mirror is not a direct read of that table.

## What this changes in the diagnosis

The evidence now includes both a positive and negative ordinary diagnostic
condition with the same sampled comparison setup and index fields. The
changed sums and Boolean provide a concrete input path to focus on during
the next controlled content comparison. There is no need to infer that a
stored threshold was changed in order to account for these sampled values.

The observations do not distinguish content-driven refresh, reinitialization,
stale mirrors, other writers or another selected code path. Active whole
image0 identity remains unproved; image0 numerical interpretation is
conditional. AV's selected/older image1-slot equality qualifies the separate
image1 layout comparison without extending that identity to image0.

The next discriminating physical test still needs a visible Apps control,
fresh RT measurement and a known failing transition with owner annotation.
No repeat W or automatic MODE2 is indicated by this accepted read.

## Physical-observation timing correction

A later owner report of a black panel must not be combined with AV's earlier
20-second clean result as if they were simultaneous. AV's frozen next-test
paragraph describes a potential counterexample, which requires a **fresh RT
read while the owner confirms the physical state**. Until then, a later black
report alone cannot establish clean RT and darkness together. The pending
question asks for picture state before changing power/navigation so the next
capture can start from a known physical state.

## Reproduction and reviews

- [RT delta and source qualification](rt-state-delta.md), including the three
  unnamed changed halfwords and reset-template limits.
- [Selector, score and timing comparison](selector-state-delta.md).
- [W eligibility and independent runtime audit](post-lifecycle-input-read-assessment.md).
- [Restricted ordinary-input reproducer](ordinary-input-delta-reproduce.py),
  which pins both raw pairs and the selected source bodies, compares the
  captured ca=cc=1/ce=0 branch and retains the timing/identity limits.
- All three AW reproducers pass under normal and optimized Python with
  byte-identical output. These are offline checks; they do not add target
  tests or demonstrate a physical repair.
