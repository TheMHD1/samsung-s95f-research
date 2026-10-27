# X retained-state decode

Recorded 2026-10-27 UTC. This is an offline decode of the already completed
X passive-observer capture. The decoder made no TV, network, root, USB,
controller, UI, firmware, setting, or filesystem operation outside reading
the retained local evidence and writing its ordinary host output.

## Result in one sentence

Under the qualified CPU aliases and selected-code interpretation, the returned
bytes form a numerically self-consistent **late mode-1 candidate**: the sampled
selector fields would choose `R+0x24c4 = 40`, sampled mode-1
`A32` has low half `44`, and `44 > 40`; but this was sampled almost three
hours after V6, sequentially rather than atomically, and therefore does not
recover the V6 event tuple or prove a physical cause.

## Acquisition bound

The pinned wrapper result is `AlreadyFaulted`, with `onset_missed=true` and
`onset_observed=false`. It reports six fixed read requests, twelve exact bulk
transfers, zero writes/retries, a final `ReadyForHeader` phase, successful
release/close, and `STAGE_ABSENT`. The initial and final R windows are
byte-identical. This validates the retained read outcome; it does not turn it
into an onset capture.

The capture terminal Linux uptime was `126642.16`. Native monotonic time ran
from `126641969582` to `126641984282` microseconds. Within the post-fault set,
the first M header transfer began at `126641982704` and the final R data
transfer ended at `126641983131`, a 427-microsecond host request sequence.
The header is included because the controller may schedule/sample its IN
response before the host starts the matching data ioctl. These host timings
do not measure a controller-wide latch or establish freshness of every field.
M, C, H, L, and R remain sequential observations, not an atomic state.

The V6 logger interval was Linux uptime `115887.39..115907.45`. Compared with
X's Linux terminal uptime, the elapsed range is 10734.71..10754.77 seconds,
approximately three hours. This compares the same kind of uptime record; it
is not a microsecond event-age bound on the earlier X reads. Native monotonic
timestamps and /proc/uptime have not been independently established as the
same clock domain across suspension. X must not be described as the missing
V6 event-time tuple.

## Byte-pinned decode

The new H window is 96 bytes with SHA-256
`d94f16ac03ed209ece31c6e35b49d89a81755681fabf296b3bc5a37013c3fe42`.
The decoder also pins the wrapper result, record, native output, and all six
retained windows before interpreting any field.

The decoder also pins U's `rtp-observer-feasibility.md` qualification. M's
same-response root anchor supports consistency but does not establish every
CPU alias. C remains raw candidate evidence. H lies within an allocated
extent but has no sampled live core tag or same-response anchor. CPU meanings
for L and R remain conditional on the non-A mapper interpretation. The field
names and arithmetic below depend on these mapping assumptions; byte equality
does not independently establish the running core or its active addresses.

| window | decoded retained values |
| --- | --- |
| M | `aa=0`, `ac=2`, alternate mirror `1`, companion `0`, scan argument `0`, root anchor `0x20010000` |
| C | raw byte `+7=1`; exact 16 bytes `70088007400b5c010300000000000000` |
| H `A32[1..6]` | `[44, 0, 0, 0, 0, 0]` |
| H `q[1..6]` | `[0, 0, 0, 0, 0, 0]` |
| H four-entry history | mode 1 `[6,0,0,6]`; modes 2 through 6 all `[0,0,0,0]` |
| L | latest subtractor `0`, mode-6 latch `54`, shared non-mode-6 latch `44` |
| R | stop `1`, fault `0x1001`, logger gate `0`, ordinary gate `0` |
| R limits | mode-dependent candidates `[200,0,0,200,40]` at `+0x2430,+0x2432,+0x2440,+0x24c0,+0x24c4` |
| R action buckets | mode 1 `7`, mode 2 `0`, shared mode 4/6 `0` |

The H values are aggregate/history state, not the detailed V6 row amplitudes.
No physical or electrical units are assigned here.

## What the late candidate establishes

The recovered ordinary selector rule is conditional. Only a selector value
equal to one chooses mode 4 or mode 6. At X, `aa=0` and `ac=2`, so that rule
would select mode 1 under those assumptions. With the separately returned C byte `+7=1`, its threshold
branch selects `R+0x24c4`, whose late value is `40`.

For this conditional late mode-1 candidate:

```text
A32[1]                 = 44
low16(A32[1])          = 44
selected late limit    = 40
shared non-mode6 latch = 44
comparison             = 44 > 40
```

This adds a sampled array to the earlier latch-only evidence: the array,
selector candidate, selected late limit, and shared latch agree
numerically. The mode-1 action bucket is also nonzero (`7`). These are facts
about the returned late bytes. They do **not** prove that V6 used mode 1, that
these exact operands coexisted at its taken predicate edge, or that the
numeric predicate caused the OLED picture to disappear.

## Sequential mode-6 observations need separate interpretation

H returned `A32[6]=0` before L returned the mode-6 latch `54`. Modes 2 through
6 also returned zero `q` and zero four-entry histories. Static code provenance
identifies L as a last-write latch, which requires separate interpretation
from an aggregate array. The sequential difference is consistent with retained
latch state, but does not prove simultaneous divergence, that `54` was stale
at the L read, or that no writer intervened. No reset, clearing, overwrite,
or lifecycle explanation is established.

## Discrete repetition, not continuous immutability

- M and C exactly match their prior retained bytes at terminal uptime
  `119358.55`.
- L and R exactly match reads at terminal uptimes `117834.25`, `124639.19`,
  and X `126642.16`.
- X is the first retained H96 sample in this comparison, so no earlier H
  equality is claimed.

These matches show identical returned bytes at named epochs. They do not
prove that the fields were unchanged continuously between reads, nor that an
intervening scan or writer could not have changed and restored a value.

## Reproducibility and limits

`decode-retained-state.py` uses only Python's standard library. It verifies
all pinned SHA-256 values, result/record accounting, exact transfer order and
counts, retained Base64-to-file equality, field values, prior discrete
repetitions, and the V6 timing bound before emitting one compact JSON line.
It reports `target_operations:0`, `samples_sequential_not_atomic:true`,
`physical_cause_inferred:false`, and `event_time_tuple:false`.

Normal and `python3 -O` executions are byte-identical; the verifier does not
use removable `assert` statements. Its conclusion is deliberately bounded:
X supplies a conditional late candidate and sequential aggregate/latch samples.
It does not supply the decisive event-time record that the onset observer missed.
The final alias-qualified JSON outputs supersede the earlier `retained-decoder`
outputs, which are retained as review history.
