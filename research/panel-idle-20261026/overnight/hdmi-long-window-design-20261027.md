# HDMI onset: bounded long-window design review

Recorded 2026-10-27 UTC from retained local records and frozen source only.
No TV, root, network, capture, server, playback, or control operation was
performed for this design review. It does not rehabilitate the rejected program_b
capture or infer a physical state from software.

## Why a longer window is warranted

The retained `ugoos-program_b-20261027a.onset` private trace spans
`90501.62..90561.78` (about 60.16 seconds; marker trace timestamps
`90501.630636..90561.782582`). Private tracing was verified ready at
`90532.58`. The parent-coordinated GO annotation falls about 31 seconds into
the capture; the owner's later “running” report and later black report are not
wholly in that trace interval. The record was rejected because the complete
AVOC maps text changed, despite retained sidecars and cleanup.

The separately acquired post-event status `0x10` and ERR_DET pin-high result
are strong state observations at their own later timestamps. They do not place
fault onset within this 60-second capture. A next capture must therefore cover
a longer owner-observable playback interval, while keeping the same rule that
only explicit, ordered human annotations establish visible-to-black timing.

## Actual retained 60-second volume

The following are sizes of the retained rejected record, divided by its
nominal 60-second physical window. They are capacity observations, not a
guarantee for another content session.

| sidecar | actual bytes | observed bytes/s | 180-second linear estimate | existing final cap |
| --- | ---: | ---: | ---: | ---: |
| trace | 12,564,510 | 209,409 | 37,693,530 | 128 MiB |
| vlog-after | 18,641,372 | 310,690 | 55,924,116 | 64 MiB |
| sample-errors | 144,738 | 2,412 | 434,214 | 256 KiB |
| samples | 84,840 | 1,414 | 254,520 | 2 MiB |
| meta | 494,761 | 8,246 | 1,484,283 | 4 MiB |
| artifacts | 162,224 | 2,704 | 486,672 | 2 MiB |

`vlog-after` actually has approximately five seconds of configured margin
beyond the physical window. Scaling its measured 65-second interval instead
predicts roughly 53.0 MiB for a 180-second capture plus margin, still close to
the fixed 64 MiB cap. The linear 240-second estimate is already 74.6 MiB
before that distinction, above the cap. `sample-errors` is an earlier and
unambiguous 180-second blocker: its 434 KiB estimate exceeds the current 256
KiB cap. The current trace ring had no demonstrated overflow here, but its
128 MiB export cap is not the limiting file at either duration.

The two compressed kernel-ring snapshots are in `artifacts.txt`; their cost
is principally fixed per capture rather than demonstrated as a linear rate.
The linear artifact row is consequently conservative and should not be used
to justify adding more snapshots.

## 180 seconds versus 240 seconds

**180 seconds is the one supportable next design target.** It gives three
times the current observation duration while retaining positive headroom in
the observed trace and vlog volumes, subject to a new zero-loss capacity
qualification. It requires increasing the sample-error writer/final validator
budget together, for example to a reviewed 1 MiB bound; that is a cap change,
not a reduction in complete-dd accounting.

**240 seconds is not supported by this record.** The current vlog cap is
exceeded by direct linear scaling, and its eventual retrieval/validation time
would also grow materially. It should not be implemented as a mere duration
constant change.

The current 900-second target expiry/watchdog is nominally larger than an
180-second physical window plus the existing finite drain and local cleanup.
That is not a proven end-to-end fetch budget: the previous 60-second record
finished much later than the physical interval while sidecars were retrieved.
The next offline test must retain the 900-second expiry contract and must
exercise the existing staged-script/sidecar-fetch cleanup path, rather than
assuming that a bigger window has no lifecycle cost. The root launch timeout
is only a bounded launch operation, not the window duration.

## Why full `/proc/<pid>/maps` equality rejected program_b

The frozen validator currently requires byte-for-byte equality of the complete
start/end AVOC and deviced maps sections before it performs target-map and
pointer-chain checks. That preserves a very strong whole-process epoch
condition, but it also rejects ordinary unrelated allocator/library-map
activity. It is the stated reason program_b was marked incomplete, not trace loss,
an identity change, or a proven display transition.

The complete maps nevertheless have two distinct roles and must not simply be
dropped:

1. At start, they locate the AVE and deviced load bases and demonstrate each
   saved target is readable.
2. During sampling, shell `mapok` re-reads current process maps for every
   `dd` sample, so an unmapped/reused target fails the collector rather than
   being blindly read. At end, the parser checks identities, hashes, start/end
   pointer chains, and selected map readability.

## program_b fixture check: the changed heap was not sampled

The program_b AVOC maps differ in exactly one paired row:

```text
start  020cd000-022d4000 rw-p 00000000 00:00 0 [heap]
end    020cd000-022d7000 rw-p 00000000 00:00 0 [heap]
```

All other AVOC rows compare equal; all deviced rows compare equal. The saved
program_b `P=0xf7203698` and `I=0xf63895d8` pointers are not in that low heap range.
Nor is any exact sampled span in it. The current retained remote sampler's
maximum AVOC spans are:

| group | exact maximum span |
| --- | --- |
| monitor words | `A+0x5bfc5c`, 152 bytes |
| static AVE fields | `A+0x5a69ec` (4), `A+0x5ab958` (4), `A+0x5ad94c` (4), `A+0x5bf6d0` (8), `A+0x5be420` (4) |
| panel object | `P`, 28 bytes |
| secondary object | `B` (4), `BV+0xd8` (4) |
| QD inner object | `I..I+0x487`; the widest individual read is `I+0x458`, 48 bytes |

The corresponding deviced sampler spans are `DG` (24 bytes),
`D+0x12aeb8` (4), `EP+0x30` (16), `OP+0x24` (4), and `EC`, `ET`, `EA` (four
bytes each). Each individual read is still guarded at capture time by
`mapok` against the then-current `/proc/<pid>/maps` before `dd` reads it.

Thus, on this fixture, a target-dependent closure comparison would not itself
depend on the growing heap row. More importantly, the raw maps show a safer,
smaller relaxation than accepting arbitrary unrelated mappings.

## Restricted map-drift policy

The next revision should retain exact full-map equality except for **one
AVOC `[heap]` row's high endpoint**. It may accept that row only when all of
the following are true:

1. it is the sole start/end row difference in AVOC maps; deviced maps remain
   byte-for-byte equal;
2. both rows have path exactly `[heap]`, identical low address, permissions,
   file offset, device, and inode; only the high address differs;
3. the end high address is greater than or equal to the start high address;
4. every retained AVOC sampled span that maps to either heap row is wholly in
   their common intersection `[low, min(start_high,end_high))`; and
5. every AVOC/deviced target span, load-base row, pointer/vptr identity, and
   process/hash/boot guard otherwise passes exactly as it does today.

No other added, removed, resized, permission-changed, path-changed, device/
inode-changed, or reordered meaningful map row is accepted. A shrink is also
rejected. This is intentionally narrower than the earlier idea of allowing
any mapping outside a target closure: it admits the exact normal heap-growth
shape observed in program_b while preserving the stronger whole-process epoch guard
for every other row. It cannot claim full heap-content stability.

To implement this safely, the parser must retain the currently discarded
device and inode columns from each raw maps row, not merely bounds,
permissions, offset, and path. It must derive the sampled-span list from the
generated remote sampler rather than a hand-maintained subset.

The static target-dependent closure that must still be checked is larger than
only the final scalar:

| process | map-dependent items to retain as exact start/end map-row identities |
| --- | --- |
| AVOC | the `libave` load-base row used to derive `A`; every static AVE span listed above; rows containing `P..P+0x1b`, `B`, `BV+0xd8`, and `I..I+0x487`; and the QD vptr/code address. |
| deviced | the `deviced` load-base row used to derive `D`; rows containing `D+0x12af7c`, `D+0x12aeb8`, `EP+0x30`, `OP+0x24`, `EC`, `ET`, `EA`, and their expected `D+0x128a28`, `D+0x128a90`, `D+0x128ab0` targets. |

For each closure address, comparison must bind the entire parsed map row
`(lo, hi, permissions, file offset, device, inode, path)`, require one unambiguous readable
covering row at both endpoints, and require the same row at both endpoints.
The existing process PID/start-ticks/executable/hash checks and the complete
start/end pointer/vptr chain equality must remain unchanged. Raw complete maps
must still be retained for later audit even when unrelated rows differ.

This restricted rule permits only the defined monotonic heap-end extension,
not general unrelated mappings. It must reject a changed/missing/
permission-changed closure row, an ambiguous covering row, a changed
AVE/deviced base row, any pointer-chain change, identity/hash/boot change,
sampling map failure, trace loss, or cleanup failure. It cannot support a
claim that the entire AVOC heap or process map was stable.

## One concrete next revision

Create a **new, uniquely namespaced 180-second HDMI derivative** from the
reviewed 60-second source, leaving all frozen collectors and rejected records
untouched. Its only functional deltas should be:

1. fixed physical duration `180` and matching vlog temporal bounds;
2. a reviewed increased `sample-errors` writer and final-sidecar cap (target
   1 MiB), with all dd accounting still exact;
3. the restricted one-row heap-end policy above, including full parsed map
   identity and generated-sampler span coverage, while retaining complete raw
   maps and every existing PID/start/hash/pointer/trace/cleanup guard; and
4. a capacity rule that rejects rather than truncates if any sidecar or ring
   reaches its cap or reports loss.

Before any future capture, the revision needs offline tests that mutate each
closure map row independently; grow/shrink the heap; change heap permissions,
offset, device, inode, path or base; add any other map row; alter each pointer
or identity field; force sample-error/vlog cap behavior; and exercise the full
staged launch/fetch/cleanup chain at the new duration. A short passive
capacity validation remains required before using it for an owner-observed
window. No 240-second derivative is recommended from the present data.

## Boundaries

This is a capture-integrity design, not a diagnosis or repair. It neither
attributes the black screen to HDMI, QD, software maps, or `RT Protect`, nor
changes the interpretation of the rejected program_b sidecars. Any future record
would still need wholly in-window human physical annotations and its own
separate technical acceptance.
