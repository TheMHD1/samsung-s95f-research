# FE capture replay: a wake-qualified40→42 software fault observation

The completed FC capture has43 Clean/Clean compact rows and two
Quiescent/Quiescent rows20/21, followed by the first fault R in cycle46.
Last-clean45 has H0 low16=40; later post-fault H is42. The conservative
last-clean-R-header→first-fault-R-data bracket is25,278us. These are
software read observations, not a measured comparison instruction or
physical blackout timestamp.

`python3 -B analyze.py` recomputes the corrected FC admission, verifies110
pinned inputs and independently decodes the58-byte compact records and
retained full windows. Normal and optimized output agree byte for byte:
442 explicit checks. It performs no target/root/network operation. The
strict FC admission supplies private transport/readiness/envelope/raw-file
and terminal nine-file cleanup checks; this analyzer adds an independent
scientific decode. Original private evidence remains necessary for replay.

## Actual sequence

- One explicit wrapper VOLUP down/up and one cached snapshot qualified
  Apps/noSaver/CSFS text. Host query-return→root-dispatch-attempt age is
  5,176,258ns. This does not attest window grammar, focus, identical rendered
  scene, target service latency or key consumption.
- Baseline1 is AA0/AC2, scan1, C7=0, H0, publication mirror200 and clean40.
- Quiescent rows20/21 have C7=1 and selector mirror1. Refresh counter is0
  then1; clean row22 still samples1, row24 samples2, row25 samples0. The
  counter/writer meanings are source-conditional and sequential; this is
  not a complete event history or CPU-idle observation.
- Last-clean45 retains AA0/AC2, scan1, C7=1, H40, history[4,0,2,0],
  publication mirror40 and ordinal0=41, between clean R samples at40.
- Cycle46 first reads fault1/0x1001/0. Its later post-fault context is
  AA0/AC2, **scan0**, C7=1, H42 and history[2,0,0,0]. The control byte
  changed; this is not direct electrical or optical scan acknowledgement.
- A separate ordinary cached query after native completion reports Live.
  It is evidence separate from the native key's subprocess exit.

All retained M root samples are20010000. Do not project complete M/AA/AC
context back into every compact row. H, M, C and R windows were read
sequentially. The publication-bound mirror is not an observed live FP
register. Two quiescent cycles remain distinct from clean cycles.

## Counts and timing

46 cycles started;45 compact rows completed. Native transfer counts are
368 headers/736 bulks:45 complete eight-pair cycles, one first-fault R
pair and seven post-fault context pairs. Every retained window is complete,
all sampled limits are40, native writes/retries are zero, and the accepted
phase is ReadyForHeader with release/close and exact stage removal.

| Native Stopwatch coordinate | Value, us |
| --- | ---: |
| Last-clean R header before |193956100871|
| Last-clean R data after |193956100952|
| First-fault R header before |193956126056|
| First-fault R data after |193956126149|
| Conservative software read span |25278|
| Whole recorded native observation span |1168146|
| Median H-start spacing |25861.5|

The requested25ms is not a guaranteed rate. Native Stopwatch coordinates,
remote uptime and host monotonic nanoseconds are different clock domains;
no cross-domain subtraction is performed. The bracket does not timestamp
the setter call, comparison, scan hardware or light loss.

## What the logger still cannot see

Logger halfword+2406 is0 in every retained R. That is a sampled fact, not
a continuous-off proof against stock temporary writers. This capture does
not collect an event ring, event argument, caller LR, actual selected A or
actual comparison FP. Post-fault42 supports the source hypothesis but is
not a direct measurement of the operand used at the earlier comparison.

The observed scan1→0 is now a concrete input to FG's logging-cleanup
design: a cleanup gate must not incorrectly require the initial scan1
after an intended fault. A source-qualified finite scan/state policy must
also account for sequential snapshots and updater lag. No new instruction
hook or stock logging gate was installed by FE.

This analysis freezes only the capture scope. The later EB fault,
stock recovery, new identity, EB validation and final Apps+saver are replayed
separately in the sibling recovery-analysis; they are not additional onset
samples. Physical output and permanent prevention remain unproved.
