# DF: RTP producer provenance and bounded capture candidate

This host-only investigation binds the selected controller source to the official firmware payload and narrows the next observations. It does not establish a root cause, the complete running controller image, or a prevention fix. No device request, UI action, reset, MMIO write, deployment, or firmware execution was performed.

## Source identity

`factory_peq.img` from the authenticated/extracted nine-item official update contains `tcon_data/QD/F_RSM1_BN9659934B_COMMON.bin`. `unsquashfs -cat` produces exactly 5,242,880 bytes with SHA256 `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`, byte-identical to the previously selected copied package. `verification.json` records source ranges and hashes. Image1 linked address mapping remains FILE=VA+0x40200. This closes official-package source lineage, not live executable attestation. No firmware byte copy is intended for public export; `private/` is retained locally.

## Positive dataflow and remaining physical gap

Image1 refresh VA0x3934 reads register root 0x58601408 (matching EXCO_PAR2_S0 metadata base0x58601400+8), carries the previous descriptor tail into record0 and current tail into record1 at CPU0x2000a60c/0x2000a616. Producer VA0x18ae8 computes source `0x60000000 + descriptor.u8(+2)*0x195*0x10000 + descriptor.s16(+6)*3*0x400`, modulo32-bit arithmetic. VA0x334 copies exactly0xb60 bytes using eight-word CPU loads/stores into each ring slot's payload after its eight-byte header. Two consecutive slots are written in a three-slot ring at CPU0x20253002 with stride0xb68; selection advances twice. Dynamic A selects the remaining slot; B selects the first slot written by that producer call. This temporal selection does not prove which samples represent an intended baseline.

The physical writer, validity/cadence, and units of the 0x60000000 aperture remain unclosed. A separately found aligned word0x60000000 at VA0x16488 lies among floating-point math constants, not a proven producer reference. The positive aperture source is the decoded immediate at VA0x18aec. The all-halfword literal-reference scan is a candidate index, not proof of exhaustive reachable code or absence of other writers. Image0's unrelated 0x584109a4 table has no demonstrated bridge to this image1 producer; it must stay separate.

A useful upstream connection is exact: getter VA0x38f4 returns CPU0x20000500; getter VA0x38e8 returns `*(CPU0x200002cc)`. Refresh VA0x394a..3958 copies byte `runtime_context+0x3d8` to CPU0x20000bc7 (the existing C+7 read) and runtime_context byte0 to CPU0xbc8. Resource initialization VA0x1bcde..1bce8 resolves the name AP_EXCO at VA0x1bd4c through VA0x1bc24 (selector0x1000c), then assigns that returned pointer to CPU0x200002cc. That establishes C+7's selected-source origin as an AP_EXCO resource-context mirror; the upstream writer and meaning of +0x3d8 remain unknown. It is not established to mean HDR, protection disable, brightness, or user mode.

Dispatcher VA0xb7ec stores selected A/B slot pointers at CPU0x20000494/498. When CPU0x4c4 is zero, C+7 is nonzero and B header halfword+6 equals0, fixed A payload CPU0x20015000 is used; the corresponding terminal row selects CPU0x20015f10. Otherwise the dynamic A payload is used, except the nonzero-counter branch skips processing. Snapshot VA0x1c12c can copy dynamic B+8 into those fixed buffers, increments CPU0x4c4 and resets it after>2. Thus CPU0x4c4 is a cycling counter; C+7 alone cannot establish which A buffer an observed predicate used. The proposed pointer window exposes stored dynamic pointers, **not the actual final A argument** on a fixed-buffer branch. B header+6 and context geometry would still be required to decide that branch; no new indirect reads are included here.

Descriptor change flag VA0x18d84 compares descriptor-tail halfword D+0x18 against its saved D+0x1e and ORs a pending D+0x2b condition, storing the result at D+2 (record0's flag), then saving the latest halfword. Initialization VA0x18d1c zeros ring/header state. These are software consistency flags; they are not physical provenance for aperture data.

## What the accepted CB capture supports

The separately frozen CB operand report establishes sampled mode1, alternate threshold40, A0 score0→38→44 and bucket0→3→7, ending in stop1/fault0x1001/gate0. Selected source compares the low16 score to the threshold and takes the fault path only when greater. A four-history invocation model is compatible with the samples, but is not a unique event trace; a delayed history value can cross the threshold while the current source count is zero. The actual event code736 was not captured directly. User-reported darkness has no instantaneous hardware timestamp. No correction here retroactively changes accepted CB transport or rejected recovery-harness classifications.

The failures on some PROGRAM_LABEL and program_b HDMI playback, the working behind-Ugoos-Home state, movies/saver/fullApps negatives, and many working titles constrain a mechanism. Plausible descriptor/baseline mismatch, content-dependent count accumulation, or upstream mode/pipeline differences are hypotheses. A global threshold change or disabling the stop path does not explain those contrasts and is not proposed. Static dataflow plus sampled arithmetic does not establish damaged hardware or a safe remediation.

## Fixed next observations, qualification and host tests

Two additions only:

| Name | Fixed bus window | Conditional selected-image interpretation |
|---|---|---|
| P |0x47000490,16 bytes| raw neighbor490, dynamic A slot494, dynamic B slot498, raw neighbor49c |
| N |0x4700ba28,36 bytes| sixu32 per-mode qualifying-record ordinal/counters atba28; sixu16 source counts atba40 |

The N ordinals are gated against CPU0x4ca: VA0xc5fa loads the mode-indexed word, VA0xc602 branches around record publication/increment when it exceeds the bound. VA0xc708 increments the corresponding source-count halfword even on that bypass. Therefore a stable ordinal/latch around41 does not imply no further qualifying sources. Array index0 corresponds to mode1 because callers use mode−1. These counters are not globally timestamped event identifiers.

`private/logger/` is an additive source fork of the frozen BX recorder with an **absent execution entrypoint**. It retains the single USB owner, complete OUT/IN pairs, terminal failure without retry, deadline/cleanup rules, immutable first-clean baseline, rolling last-clean retention, and bounded one-Left worker logic for host tests. Cycle is R,M,C,P,N,H,L,R; post set M,C,P,N,H,L,R. Window/transfer capacities become8/16; R-end indexes and fault-injection ranges were updated. Exactly these two addresses are added; the source does not add aperture/MMIO or dynamic pointer dereferences. Period250ms,20s/80cycle limits remain. Added traffic may change actual cycle timing and is not assumed negligible.

Build succeeds with0 warnings/errors. `--self-test`:93 cases; `--key-self-test`:22 cases. Negative/throw injection covers all16 transfers of a clean cycle and all14 transfers of the post set, including P/N; no following traffic after failure, cleanup, pending-IN deadline completion, and USB progress during a blocked fake key are checked. Worst tested output with immutable baseline is17,748 bytes below24,576. Python verifies exact new 12-byte little-endian headers, decoder offsets,12 malformed/arbitrary window refusals, official member identity and source anchors. `--execute` returns63 with a fixed host-only refusal. These tests perform zero target operations.

Before any centrally coordinated target capture, the new windows require exact current bus-alias/length qualification and a fresh first-header premise; source literals alone are insufficient. No hardware meaning is assigned to neighboring words. A matching strict parser and wrapper must be derived for the eight-window schema, with all manifest pins and independent review. Frozen BX/CB parsers are incompatible and must not be reused unchanged. Runtime image qualification remains conditional: current profile selection plus source/layout matches are evidence, not proof that all executing code equals this package. The next result should preserve raw bytes, transfer brackets, key timing and clean/fault chronology, while leaving source interpretation conditional.

Run `python3 verify.py` from this directory for the existing build's host verification. `evidence-graph.json` uses the DG contribution schema and labels static, observed, inferred and unknown edges explicitly. Paths are research-relative where possible; private OEM contents are excluded from graph material.
