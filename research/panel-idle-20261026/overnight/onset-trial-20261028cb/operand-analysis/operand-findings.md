# CB operands: mode 1, selected threshold 40, score 0 → 38 → 44

Offline analysis recorded 2026-10-28 UTC. No TV, USB, root-client, network, write, reset, or firmware operation was performed by this analysis. The transport audit is separate. The owner told the parent that the panel went dark; that observation has no native timestamp and is not an atomic physical event marker.

The captured operands match the selected profile's mode-1 aggregate comparison with alternate threshold **40**. The baseline score was 0, the last-clean score was 38, and the post-fault score was 44. The mode-1 action bucket changed 0 → 3 → 7. The first fault R already contains stop=1, fault=0x1001, ordinary gate=0, and bucket=7. This narrows the software path considerably. CB did not collect `rtp_act_736`, so the exact event identity remains a source-conditioned inference rather than a directly logged CB event.

## Inputs, mapping, and reproduction

`analyze_operands.py` reads the native first JSON line, result manifest, and 18 retained raw windows. It checks each raw length/SHA against both manifests, pins the complete selected package SHA, checks the predicate-body SHA, decodes every byte/halfword and records all byte differences. Normal and `python3 -O` output are byte-identical. `decoded-operands.json` contains complete values and timestamps, including unknown fields, rather than discarding bytes without assigned meanings. `source-pins.json` pins the inputs and supporting reports; `artifact-inventory.json` freezes this directory.

Selected source: `../../selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin`, SHA256 `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`. Image-1 FILE=VA+0x40200. CPU root pointer at 0x4e0 is 0x20010000 in all M samples. Meanings below assume the retained selected code/layout is the running one and that the observed 0x4701 bus allocation aliases its 0x2001 CPU data. Matching layout, initializers, live state, and prior V6 event capture strongly support this interpretation; a full live executable hash and hardware alias proof are absent.

## Observed values

R=0x47012400/256, M=0x470004a0/68, C=0x47000bc0/16, H=0x4700d0e0/96, L=0x47010f00/64. “Post” M/C/H/L were read after the first fault R; they are not simultaneous event operands.

| Field | Baseline | Last clean | First fault R / later post |
|---|---:|---:|---:|
| R stop / fault / ordinary gate | 0 / 0 / 1 | 0 / 0 / 1 | 1 / 0x1001 / 0 |
| M flags aa / ac; selected mode | 0 / 2; 1 | 0 / 2; 1 | 0 / 2; 1 (post) |
| C byte+7 alternate selector | 0 | 1 | 1 (post) |
| R normal mode1 / alternate fp | 200 / 40 | 200 / 40 | 200 / 40 |
| R mode2 / mode4 / normal mode6 fp | 0 / 0 / 200 | unchanged | unchanged |
| M selected record-ID bound mirror | 200 | 40 | 40 (post) |
| H six A aggregates | all 0 | [38,0,0,0,0,0] | [44,0,0,0,0,0] (post) |
| H six q states | all 0 | all 0 | all 0 (post) |
| H mode1 four-count history | [0,0,0,0] | [4,0,2,0] | [4,0,4,0] (post) |
| L non-mode6 score latch / T latch | 0 / 0 | 38 / 0 | 44 / 0 (post) |
| L mode6 score latch | 50 | 50 | 50 (post; historical) |
| R mode1 action bucket +0x2486 | 0 | 3 | 7 |
| R mode2 / mode4-or-6 action bucket | 0 / 0 | 0 / 0 | 0 / 0 |
| R mode1 record-ID latch | 0 | 40 then 41 within R pair | 41 |
| R aggregate enable / BP count limit | 1 / 160 | 1 / 160 | 1 / 160 |
| R T selector / helper count limit | 1 / 10 | 1 / 10 | 1 / 10 |
| R events 344 / 351 enable and latches | all 0 | all 0 | all 0 |
| M ordinary scan-enable byte 0x4d8 | 1 | 1 | 0 (post) |

The scan counter 4→5→5 and unchanged post-fault score fit ordinary scan gating after the setter. The mode6 latch 50 alongside a zero baseline aggregate array demonstrates that these latches are historical outputs, not a coherent cross-mode sample. C+7=1 and M+0x4c4=0 are compatible: the callback copies the numeric selector, while helper 0x1c12c also increments and resets 0x4c4. It is not a permanent Boolean mirror.

## Exact active comparison and competing common-setter callers

Predicate VA 0x1e68..0x203e selects mode 4 only when aa==1, mode 6 only when ac==1, and otherwise mode 1. ac=2 therefore means ordinary mode 1. For mode1, C+7 nonzero selects root+0x24c4 (40); zero selects +0x2430 (200). Mode2 selects +0x2432, mode4 +0x2440, and mode6 selects +0x24c4 or +0x24c0. Root+0x2410=4 controls upstream scanning; it does not mean predicate mode4.

With root+0x249e==1 and wait field 0x35a4==0, the predicate processes slot mode−1. It shifts q as `(2*q)&31`, rotates the four-count history, appends the current s, and increments q if s>root+0x24a0 (160). Unless q is one of {8,9,10,12,24,25}, it adds the new oldest history count to the 32-bit A and subtracts T once when A>=T. T comes from helper 0xca10 when root+0x24d2 is nonzero, otherwise 0xc8a0; both publish the T latch. It takes low16(A), publishes the mode6/non-mode6 score latch, and compares against fp:

```
202a cmp r7, fp
202c ble 203e             # clean when score <= fp
2030 movs r1, #4
2032 bl 1c0c8             # OR bit4 into the mode's output bucket
2036 mov.w r0, #0x2e0     # decimal736
203a bl c1e0
```

The score and threshold are zero-extended halfwords. The signed BLE instruction therefore has the same ordering as unsigned comparison here. Common setter 0xc1e0 stores root+0x2400=1, +0x240e=0, +0x240a=0x1001, then logs the event twice. The selected-image exact direct-BL census finds four callers: 0x203a (736), 0xc792 (0x338), 0xc7e0 (0x344), and 0xc836 (0x351). The latter three require respectively aggregate gate !=1; event344 enable==1 with its count bound exceeded; or event351 enable==1 with its Y/count conditions. The latter two set their separate latches. All sampled CB gates/latches exclude these alternatives under stable-state assumptions. The 3→7 mode1 bucket transition and 44>40 support the 736 edge. Transient gates, indirect calls, different running code, or other writers are not excluded by this finite direct-call census.

The output bucket +0x2486 is **not an enable mask** on this path. Inline difference qualification ORs bit1; formatter 0xc640 calls the helper with bit2; the event edge calls with bit4. The helper only accumulates bits. Clearing the bucket does not change the comparison or common-setter stores.

## What contributes to the score

The formatter counts qualifying packed-lane comparisons. It excludes B lanes in the inclusive 500..3183 band and uses ordinary absolute-difference limits 500 (mode4 limits here are zero). The resulting s is a count of qualifying lanes, not the measured difference amplitude or an established electrical/physical quantity. The record-ID bound at CPU0x4ca is a separate publication bound: once ID>40, the formatter bypasses ID update/publication but still reaches s increment at 0xc708. Thus ID 41 staying fixed does not cap aggregate growth at 40.

A shortest compatible same-slot, no-reset model from H=[4,0,2,0], A=38 to H=[4,0,4,0], A=44 uses four invocations with s=[4,0,4,0], q=0 and T=0: A becomes [38,40,40,44]. Equality at 40 remains clean; the fourth invocation crosses the threshold even though its new s is zero, because the delayed history adds 4. This is a compatible model, not a reconstructed unique trace: H reads are sequential and the last-clean H preceded the final clean R.

The packed-buffer provenance reaches a three-slot ring (base0x20253002, stride0xb68), two dynamic payload copies, descriptor-selected copies from the 0x60000000 aperture, and optional fixed A buffers at 0x15000/0x15f10. C+7 and 0x4c4 participate in source selection and copying. Without the selected B header and pointers, C+7=1 does not prove that the fixed A branch was used. The physical meaning of the aperture is still unproved. The separate unresolved image0 0x584109a4 producer must not be identified as this RTP source without a dataflow bridge.

## Time bracket and smallest further read

The final clean R is bracketed 167671010145..167671010211 us; the first fault R is 167671260342..167671260439 us. The conservative outer bracket is **250294 us**; the gap between those read brackets is 250131 us. These are host transfer software timestamps, conditional on reply freshness and without atomic memory-copy or endpoint-queue proof. The first fault read began 1.109335 s after Left-down returned and 0.932616 s after Left-up returned. Last-clean reads also occurred after both key calls. This establishes temporal order, not UI receipt, key causality, or a light-output transition time.

Post M/C/H/L begin at167671260689/757/846/921 us, after the first fault R. Final R167671261002..261084 matches first fault R. Do not promote later histories into exact event registers.

The smallest missing count window is a separately qualified fixed **0x4700ba28/36** read: six u32 record IDs followed by six u16 current s counts. Pairing it with H and R brackets would distinguish ID publication saturation from continuing count production, subject to the same sequential sampling limit. A second small pointer window 0x47000490/16 would expose A/B pointers at494/498. To close the physical producer boundary requires descriptor/aperture dataflow work, not blind reads of the unrelated 0x5841 region. No next read was executed or prepared here.
