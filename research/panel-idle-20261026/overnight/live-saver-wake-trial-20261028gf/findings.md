# GF: recorded clean-to-fault transition during an intended Live saver wake

The GA recorder actually captured the previously missed interval. A natural cached Live+saver+CSFS snapshot appeared without a key or reset. A separate fresh EB66 capture then verified all 16 raw windows: equal clean R0/0/1 at the original alternate limit40, logger0, C8=3 and scan1. GA repeated its own strict cached context and native clean-baseline guards before arming. Its wrapper sent no keys; the unchanged native sent its sole planned Left only after the first full clean cycle.

The accepted observation contains 26 complete rows: 24Clean, oneQuiescent and a final Faulted row. It accounts for 220headers,218INpayloads,440bulk transfers and two fixed logger payloads. The whole native operation lasted810,583microseconds. Logger readback returned to zero while preserving the fault state; the exact11-file stage and both retained sidecars passed accepted cleanup.

## What changed during the capture

C7 changes0→1 at cycle14, the sole Quiescent checkpoint. The publication mirror is sampled200 through cycle17 and40 from18; this mirror is distinct from the R alternate limit, which remains40. Mode1 H in cycles20–26 is8,16,24,24,32,40,48. Cycle25 is still Clean with H40; cycle26 has both R snapshots Faulted1/0x1001/0 with H48. The publication ordinal reaches41 in cycle25 and remains41; current source counts are zero at the retained fault boundary. These fields have different lifetimes.

The first full fault-R read is bracketed207683297072–207683297221us in the native clock. The immediately preceding clean row does not retain its end-R timestamp. A conservative adjacent-status enclosure uses its earlier H-read completion207683271745 through the first fault-R completion, a25,476us interval. This is neither the comparator's instruction timestamp nor a physical blanking edge.

The ring moves from tuple2270/2270/0 to3466/3442/1. Its cursor-selected1,196-byte candidate contains NORMAL header56,21detail records and two `rtp_act_736` lines. All changed data bytes fall within that candidate; backing bytes outside it are unchanged. The second cursor points before the final24bytes containing the two event lines. Consumer ownership, no-lap history and exact record-to-dispatch epoch remain unproved. Header56 is source-compatible with the invocation counter, not the score or FP.

The selected source's mode1 path compares the low16 aggregate against its selected threshold and calls the common setter with736 after a strict greater-than branch. That setter can emit the same event twice from one invocation. This capture is consistent with that path under sampled C7/mode/limit context and prospectively bounded logging. It does not capture actual FP, selected-A, caller PC/LR, the physical packed-data producer or emitted light. It does not prove that two log lines mean two fault invocations.

The native key-overlap qualifier passed. The later cached UI is Live+CSFS without saver windows. There is no observed ForYou transition or physical picture report. The intervention is correctly described as an intended saver wake from cached Live, rather than a proved Live-to-ForYou trajectory.

The [independent capture replay](live-analysis/README.md) seals1,254checks/136negative cases over224pinned inputs and78unique retained requests, including all44GA requests and28baseline-EB requests with byte-exact artifacts. Its scope ends at post-capture UI.

## Separate fault confirmation and recovery

A later EB66 read independently confirms stable full R1/0x1001/0 at40/logger0, with all16raw windows verified and exact cleanup. Ordinary Apps preparation and unchanged public reject gates then precede exactly one fixed stock operation41/mode2. The helper reports kernel return zero and confirmed cleanup; that alone is not physical recovery proof.

Fresh metadata positively records USB66 disconnect before67 enumeration with unchanged Linux boot/descriptors and only four instance fields changed. The recorded dmesg values fall numerically within the helper's foreground uptime bracket. Fresh EB67 verifies all16raw windows, equal full Rclean0/0/1 at40/logger0, C8=3/scan1, both N windows zero, ReadyForHeader/release/close and exact cleanup. X/Y/RGB/Diff are zero, while B retains22nonzero entries; no universal RAM clearing or instruction reload is inferred. Final cached UI is Apps+CSFS+saver. No target process/root request remains pending.

The [independent recovery replay](recovery-analysis/README.md) separately seals1,880checks/69negative cases over202pinned inputs and86source-exact requests through final UI. Physical light remains unobserved. One local postprocessor tuple-unpacking correction is documented in [host-check-correction.md](host-check-correction.md); it caused no extra target read.

## Diagnostic implication and next experiment

GC supplies a completed Apps-to-Live control with H no higher than36 and no captured fault. GF supplies an armed, sampled wake-to-fault sequence crossing40 and fresh paired736 text. This narrows the software path considerably and removes the prior pre-arm timing ambiguity. Different UI/reference history and asynchronous samples still prevent a matched threshold-causality claim.

GD's actual-instruction host oracle explains the selector-dependent200/40 branch under supplied inputs. GG is a host-built fixed200 recorder for a future matched wake contrast, not a deployed fix. Before any such target test, restoration/recovery for a possible Faulted200 outcome must be qualified: FA restoration requires Clean state and scan1, and the existing EI recovery admits Faulted40 only. GH addresses that separate host-side prerequisite. No threshold, executable, kernel, boot or flash write occurred in GF. Permanent prevention and the overall goal remain incomplete.
