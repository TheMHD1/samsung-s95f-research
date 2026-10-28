# Reference refresh control and missing checkpoint fields

This host-only audit narrows a concrete observability gap. The stock code
seeds a short reference-copy sequence when the selector changes. Existing
DP reads already include its controls and dynamic pointers on every cycle,
but the compact history discards these fields. The proposed EH derivative
retains them without adding controller reads or writes. This directory
installs no hook and performs no target, network, UI or reset operation.

## Source findings

Selected image1 is file VA+0x40200 of package SHA256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
The exact instruction/literal checks and range hashes are in
`source-audit.json`. This is selected-package semantics; the later code
bodies were not among DX's four 16-byte live fingerprints.

The context getter at0x38f4 returns CPU0x20000500. Its selector byte at
offset0x6c7 is therefore CPU0x20000bc7, the previously captured C+7.
At0xc27c..0xc2a2, stock code compares that byte against the u16 mirror at
CPU0x200004c2. If they differ, it updates the mirror and stores either1
(new selector nonzero) or0 (new selector zero) to u16 CPU0x200004c4.
An unchanged selector does not rearm that counter. The direct caller at
0x4446 is conditional on another context byte; this audit does not prove
execution frequency or scheduling.

The dispatcher publishes dynamic A and B pointers at CPU0x20000494 and
CPU0x20000498. When actual B header byte+1 is nonzero it calls0x1c12c.
That function requires the refresh counter and C+7 both nonzero. Header
row0 increments the u16 counter and copies2912 bytes from B+8 to the fixed
top buffer. Otherwise a row equal to height−1 does the same for the fixed
bottom buffer. Afterward a counter greater than2 is cleared to0. The
dispatcher skips ordinary comparison while the counter remains nonzero.

**The counter counts qualifying boundary events, not distinct buffers.**
Starting at1, two qualifying events reach2 and then3, which is cleared.
The bounded code permits top/top, bottom/bottom, top/bottom or bottom/top;
it contains no recovered “one of each” test. This does not prove that
normal producer scheduling ever supplies a repeated boundary during this
window, or that a buffer was stale in an actual fault. It identifies an
event-order question that retained reference values and a later zero
counter cannot answer. A selector falling to0 can also cancel the sequence.

The overlapping halfword literal scan finds10 syntactic references to
CPU0x200004c4 in the selected image interval. It does not establish a
complete reachable writer census, exclude computed/other-CPU writes, or
prove MODE2 initializes this state in a particular way.

## Existing data and new taps

Ten retained clean-boundary samples cover the two faulting40 runs, the
200 observation, its restored40 rechallenge, and the latest warm40 control.
They all have refresh counter0 and trainer gate0. Their Apps baselines have
C7/mirror0; their later Live samples have C7/mirror1. These boundary values
do not distinguish the faulting and nonfaulting runs or recover the copy
sequence in between. Dynamic A/B pointers rotate among the retained ring
addresses; a sampled pointer is not the header that a historical call used.

Proposed per-cycle taps all come from the existing eight DP windows:

| Value | Existing raw offset | Meaning and limitation |
|---|---|---|
| u16 CPU4a2 | M+2 | Known trainer control at this read |
| u16 CPU4a4 | M+4 | Trainer aggregate at this read |
| u16 CPU4c2 | M+34 | Selector mirror; not an event counter |
| u16 CPU4c4 | M+36 | Refresh sequence counter; no buffer identity |
| u16 root2460 | end-R+0x60 | Known writer control sampled later than M |
| u16 root246e | end-R+0x6e | Known publisher control, not quiescence proof |
| u32 CPU494 | P+4 | Captured dynamic A pointer |
| u32 CPU498 | P+8 | Captured dynamic B pointer; header unobserved |

The original34-byte record plus these20 bytes gives54 bytes. The original
80-cycle worst-case receipt would exceed its fixed24576-byte cap. EH must
therefore use a separately labeled, shorter60-cycle/15-second observation
at the same250ms cadence, and prove the complete serialized success and
failure bounds before deployment. No cap increase or truncated receipt is
authorized by this source audit.

Sampling at250ms can miss the entire short copy sequence. Zero counters in
every new sample would not disprove these source paths or identify the
buffer refresh order. Capturing every call would require an execution hook
or a separately qualified hardware trace. DZ has not established owned
scratch storage, instruction-installation safety or deterministic hook
rollback, so no such hook is installed.

## Reproduction

Run `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/tcon-capstone python3 audit.py`
and repeat with `python3 -O`. Run `python3 -m unittest -v test_refresh_model`
from this directory, also normally and with `-O`. The pure model covers
selector edges, nonzero values other than1, repeated boundary kinds,
nonboundary events, entry guards, u16 wrap and height subtraction edges.
It assumes stable input fields within each modeled block and does not
model interrupt races, the raw copy implementation or physical scheduling.

This work provides source-directed logging targets. It establishes neither
the physical damage mechanism nor a prevention fix.
