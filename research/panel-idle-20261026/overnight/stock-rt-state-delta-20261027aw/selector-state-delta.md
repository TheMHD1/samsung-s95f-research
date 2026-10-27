# Selector and score-state delta across the stock lifecycle

Recorded 2026-10-27 UTC. This is a bounded offline interpretation of the
frozen AV pre-X and post-X raw windows. It made no TV, root, network, USB,
native-helper, firmware, power, reset, protection, patch, or storage
operation. It neither adds a collector nor changes the frozen AV evidence.

## Result

The delayed clean sample is **not** associated with a rewrite of the five
stored candidate comparison limits or with a change in the `aa/ac` mode
selectors. Both samples conditionally select mode 1 from `aa=0, ac=2`, and
the five R-window limits remain `200,0,0,200,40`.

It is also not merely an isolated history clear. Three related classes of
sampled state differ:

1. the alternate selector and its mirror change from 1 to 0, changing the
   conditional mode-1 limit source from `R+0x24c4=40` to
   `R+0x2430=200` without changing either stored limit;
2. the mode-1 aggregate, its four-entry history, and the shared non-mode-6
   latch change from `44`, `[6,0,0,6]`, and `44` to zero; and
3. the ordinary scan-enable argument changes from 0 to 1.

Thus the strongest supported description is a **combined selector/control
and retained score/history-state delta**. It is not an event-time predicate
record, an identified reset routine, or proof that the stock lifecycle caused
any one field change.

## Which retained epochs are being compared

The pre-X M/C/H/L values are the `post-fault` auxiliary set from cycle 1.
They were acquired after an initial R had already classified the state
faulted and before a final faulted R. They are not bytes from the original
fault onset.

The post-X M/C/H/L values are from the rolling observer's sole retained
`last-clean` set, cycle 80. Post-X discarded the raw bytes of the 79 older
clean cycles under its reviewed retention policy. In particular, there are
no raw M/C/H/L bytes from the first post-X cycle, so this comparison cannot
show the immediate post-lifecycle state or when any field changed.

The exact response intervals were:

| window | pre-X post-fault IN (`us`) | post-X cycle-80 IN (`us`) |
| --- | ---: | ---: |
| M | `136101805333..136101805366` | `136922042180..136922042220` |
| C | `136101805406..136101805447` | `136922042261..136922042302` |
| H | `136101805489..136101805529` | `136922042343..136922042384` |
| L | `136101805571..136101805612` | `136922042426..136922042467` |

These are sequential host transactions, not one controller-wide atomic
snapshot. The R brackets support the per-cycle faulted/clean classifications;
they do not make the intervening M/C/H/L bytes simultaneous.

## Source-backed field comparison

Interpretation below remains conditional on the already-qualified image-1
aliases and selected-code maps. Both M responses carry the same-response root
anchor `0x20010000`. Both C responses preserve the three startup fingerprint
halfwords `0x0870,0x0780,0x0b40`. This supports the same bounded field layout;
it is not a live core-tag or whole-executable identity measurement.

### M — selectors, mirror, and ordinary scan argument

| qualified field | pre faulted set | post clean cycle 80 | result |
| --- | ---: | ---: | --- |
| status/scan counter at M `+0x00` | 396 | 11 | changed; software counter only |
| `aa` at `+0x0a` | 0 | 0 | unchanged |
| `ac` at `+0x0c` | 2 | 2 | unchanged |
| alternate numeric mirror at `+0x22` | 1 | 0 | changed |
| mirror companion/progress at `+0x24` | 0 | 0 | unchanged |
| `y` diagnostic scalar at `+0x30` | 0 | 708 | changed; no physical unit assigned |
| `RGB` diagnostic scalar at `+0x34` | 0 | 0 | unchanged |
| ordinary scan argument byte at `+0x38` | 0 | 1 | changed |
| root word at `+0x40` | `0x20010000` | `0x20010000` | unchanged anchor |

The selected ordinary code chooses mode 4 only when `aa==1`, mode 6 only
when `aa!=1 && ac==1`, and mode 1 otherwise. Consequently both sampled pairs
take the conditional mode-1 fallback. The `ac` value 2 is an ordinary
post-scan state; it is not mode 6.

The scan-argument difference is consistent with the R brackets: the
qualified ordinary caller generates one only for stop/event flag 0 and
ordinary gate 1, whereas the fault setter's retained `1/.../0` state yields
zero. This is a sampled code/data consistency, not an instruction trace or a
claim that every scan path ran.

### C — alternate-threshold selector

The complete pre/post C responses differ at exactly one byte:

```text
pre   70 08 80 07 40 0b 5c 01 03 00 00 00 00 00 00 00
post  70 08 80 07 40 0b 5c 00 03 00 00 00 00 00 00 00
                                  ^
```

Candidate byte `+7`, conditionally the ordinary alternate-threshold selector,
changes `1 -> 0`. Its sequentially sampled M mirror also changes `1 -> 0`.
Byte `+8` remains 3 and the three startup halfwords remain unchanged. The
agreement between M and C is useful local consistency, but does not make the
two reads atomic or prove every CPU/bus alias globally.

For conditional mode 1, nonzero selects `R+0x24c4`; zero selects
`R+0x2430`. The R windows show that all five candidate stored limits are
unchanged:

| limit source | pre | post |
| --- | ---: | ---: |
| `R+0x2430` | 200 | 200 |
| `R+0x2432` | 0 | 0 |
| `R+0x2440` | 0 | 0 |
| `R+0x24c0` | 200 | 200 |
| `R+0x24c4` | 40 | 40 |

Therefore the conditional selected source/value changes from `+0x24c4=40`
to `+0x2430=200`; the underlying limit storage itself does not change.

### H — per-mode aggregate, q state, and history

The qualified H layout gives:

| field | pre faulted set | post clean cycle 80 |
| --- | --- | --- |
| `A32[1..6]` | `[44,0,0,0,0,0]` | `[0,0,0,0,0,0]` |
| `q[1..6]` | `[0,0,0,0,0,0]` | `[0,0,0,0,0,0]` |
| mode-1 history | `[6,0,0,6]` | `[0,0,0,0]` |
| mode-2..6 histories | all zero | all zero |

Only three H bytes differ because each nonzero pre value fits in one low
byte. The post H window is entirely zero. Existing code contains a broad
initializer capable of clearing these arrays, but no recovered edge binds
that initializer to this MODE2 lifecycle. These bytes therefore prove the
sampled before/after state, not which writer or reset produced it.

### L — last-write score latches

| qualified field | pre faulted set | post clean cycle 80 |
| --- | ---: | ---: |
| latest subtractor at `+0x04` | 0 | 0 |
| mode-6 latch at `+0x06` | 54 | 48 |
| shared non-mode-6 latch at `+0x08` | 44 | 0 |

The shared mode-1-class latch agrees with `low16(A32[1])` in each sampled
set: `44/44` before and `0/0` after. The mode-6 latch changes but is not
cleared, which is another reason not to describe all retained predicate state
as globally zeroed. Latches are last-write fields, not event-exclusive
records, and the sequential H-before-L order cannot prove simultaneous state
or staleness.

## Conditional numeric comparison, not an onset reconstruction

Under the reviewed maps, the late pre-action candidate is:

```text
mode 1, alternate selector 1, selected limit 40,
A32[1] low half 44, shared latch 44; 44 > 40
```

The delayed post-action candidate is:

```text
mode 1, alternate selector 0, selected limit 200,
A32[1] low half 0, shared latch 0; 0 <= 200
```

This is a useful state separation, but neither row is a retained compare
edge. The pre sample occurred long after the original V6 event and before the
stock lifecycle; it must not be relabelled as the actual onset tuple. The
post sample is the last retained clean cycle, not the first post-lifecycle
cycle. Selector, aggregate, latch, and threshold reads are sequential, and
the selected code allows independent writers/refresh timing. No exact event
mode, compare time, causal writer, physical panel state, or repair follows.

## Unnamed raw deltas

Raw changed-byte counts are M=15, C=1, H=3, L=2. The source-backed fields
above account for every C/H/L changed byte. The changed M bytes at offsets
`+0x12,+0x13,+0x14,+0x15,+0x26,+0x2a,+0x32,+0x33,+0x36` remain unnamed in
the selected field maps and are preserved only as raw deltas. Numeric
coincidence—especially M `+0x2a` changing 40 to 200—is not used to assign a
threshold or physical meaning.

## Reproduction

`selector-state-delta-reproduce.py` pins the selected 5-MiB package, the
reviewed mode/score/gating reports, both native terminal outputs/results, and
all pre/post M/C/H/L/R raw files. It verifies retention roles, exact base64
and SHA bindings, sequential transfer timestamps, field values, raw delta
counts, and the conditional route calculation before emitting one compact
JSON line. It uses no removable `assert` and performs no external operation.

```sh
python3 selector-state-delta-reproduce.py
python3 -O selector-state-delta-reproduce.py
```

Both modes produce byte-identical 1,754-byte output with SHA-256
`1f5d6a43d28d7d15826db396596eac124f78315f6e1abc0918cdc9c9def0d4ca`.

