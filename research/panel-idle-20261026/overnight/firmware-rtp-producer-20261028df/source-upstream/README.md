# Selected AP_EXCO selector inputs and content-dependent branches

The selected package closes a control edge from image0 AP_EXCO decisions to image1's alternate-A selector. It does not close the physical producer of packed RTP pixels at aperture 0x60000000. These are different data paths. The positive cross-core bridge is documented in `../cross-core-slg-addendum.md`: image0 context+3d8 receives `bool((data[e6]&1) | u16(data+2fc))`; the image1 AP_EXCO lookup/translation reads that context field into CPU20000bc7 (C+7). C+7 permits a fixed-A path for particular B-header rows, while other branches still use the dynamic A slot.

All source addresses below are selected image0 linked addresses, FILE=VA+0x200. Package SHA256 is `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`; the authenticated firmware package and earlier selected copy are byte-identical. Source identity is not complete attestation of running instructions. No target operation or firmware modification was performed for this analysis. The two function models are original host tools with 27 checks, normal and optimized Python both passing.

## First selector helper

`0x2f5d8..0x2f970` has source SHA256 `428c93783eeb93bec0a363d29043bca4c8aecdbf5e7339542ccd5c70ba537b45`. Its table/tail inputs were already established by `ap-exco-helper-inputs-20261027s`, `ap-exco-input-snapshot-20261027w` and `npc-ap-divisor-provenance-20261027af`; this addendum connects those inputs to the cross-core consumer rather than claiming a new physical table producer.

The three lanes at register base 0x584109a4 are spaced 0x40 bytes, with sixteen u32 words each. The helper sums a selected upper tail. Upper index is 15 when AP_EXCO+e8 is nonzero, otherwise14. The initial lower indices derive from 15 minus fields ea/ec/ee. With field116 enabled, it recomputes each tail index k using floating-point `(ea*f0)/NPC_AP_divisor`, adds0.5 and converts to integer, truncates to16bits and caps with the respective f2/f4/f6 cap. The same ea*f0 numerator is used for all three recomputed lanes. The inclusive lower bound is then 15−k. Final k indices are mirrored at104/106/108 and the three sums X0..X2 at10a..114. Units, the physical writer and sampling cadence remain unproved; a distribution or histogram interpretation is an inference from this arithmetic and data, not a measured semantic label.

P0..P2 are the u32 little-endian halfword pairs at d0/d2, d4/d6, d8/da; P3 is dc/de. When ca is zero the helper clears e6 but retains debounce counters e2/e4. Otherwise:

- With cc enabled, C0 is any `Xi > Pi`. When ce is also enabled, it additionally requires any `Xi <= P3`. A true comparison sets F0 when the existing e2 counter is at least e0; otherwise it increments e2. A false comparison clears e2. With cc disabled it bypasses that counter write and leaves F0 false.
- With ce enabled, C1 is any `Xi >= P3`, including equality, debounced through e4 against the same e0. With ce disabled this counter write is bypassed and F1 is false.
- The result is e6=F0|(F1<<1). The cross-core selector consumes only e6 bit0; F1 has separate register/control effects and is not that bit0 condition.

At zero initial counters, e0=30 matures on the31st continuously true evaluation. No wall-clock duration follows without an independently measured evaluation cadence. AP+206 mirrors F0 and +208 counts its rising transitions; these fields are not assigned an electrical meaning here.

## Second selector helper and stale-bit behavior

`0x2f980..0x2fb44` has source SHA256 `7376c3c5ccb05a94ba00860bdace59dfb67599cf9e47dfb580c97cbde6af8241`. Outer writer0x2fb44 calls it only when ca is nonzero. Thus turning ca off can preserve an old2fc. Within the helper, a zero2cc enable or zero2ce mask clears the entire2fc value, while counters are not cleared at that branch. Mask bits independently select updates and do not implicitly clear bits for branches that were skipped.

Mask bit0, at0x2f9ba, compares AP_AG+92 and AP+37a:

`(AG92 <= AP_EXCO.2d0 && AP37a == AP_EXCO.2d2) || (AG92 <= AP_EXCO.2d4 && AP37a == AP_EXCO.2d6)`.

It debounces with counter300 versus e0. A false comparison clears bit0 and resets its counter; a true but immature comparison increments its counter while retaining any old bit0. A mature true comparison sets bit0.

Mask bit1, at0x2fa38, samples raw index15 in all three lanes (register offsets3c/7c/bc) into fields2d8..2e2, with high halfword stored before low halfword. It requires all six strict bounds: lane1>2e8/2ea; lane2>2ec/2ee; X0>2f4/2f6; X0<2f8/2fa; lane0>2e4/2e6; lane0<2f0/2f2. It debounces through302/e0 and uses the same retain-old-bit while true-but-immature behavior. The host model intentionally uses lane numbers instead of asserting physical RGB ordering.

## Upstream objects and the frame-mode negative

Image0 getter e660 resolves AP_AG at CPU2000dc5c; e670 resolves AP at CPU2000f0e0. These are separate from AP_EXCO data CPU2000ff14 and context CPU200158a8. Positive AP_AG+92 writer0x256c is called from0x1330a: when globalu32 CPU200007bc is nonzero and index=(u16CPU200007c0−1)<32, it copies AP_AG table+46+2index to AP_AG+92. This belongs to the previously identified resource2/dynamic interrupt boundary. No physical gain/brightness unit or NPC-LUT-to-AG92 dataflow has been established. A textual ldrh offset92 inside another function whose base was advanced is not a direct writer to AP_AG+92.

AP+37a is a frame-mode field. Setter0x2555c accepts a value below3 only when fields37a/37c/37e are equal and the requested value differs, then stores37a and marks the CPU200008e8 update gate. The F300:0x160 dispatcher route is established by the earlier `tcon-research/qd-f300-write-gate-provenance.md` and its independent review. This addendum connects that field to the second helper's bit0 branch; it does not claim the F300 switch is newly discovered.

The important negative is concrete: the packaged AP_EXCO initializer at FILE0x182200 is826bytes, SHA256 `c50e438b4882c04e62542fa718cda662b56c3ea0930e20d54944a949e2e3afbf`. Its fields ca/cc/ce=1/1/0, e0=30, 2cc=1, **2ce=2**, and all four2d0/2d2/2d4/2d6 constants are zero. The prior W ordinary824byte snapshot, SHA256 `0f7884892da5714a9adcb97cdc033c4d5b24201b1ac570dabcc6771c01a7e271`, independently has that same enable/mask/constants. Mask2 disables the frame-mode comparison branch. Therefore a proposed frame-mode-only explanation or fix is not justified by these inputs. W is a prior late sample, not contemporaneous with CB or either DH onset; its mask does not prove the later runtime mask never changed.

In W, P0..2=7,464,960 (90% of3840×2160), P3=8,128,512 (98%), while X0/1/2=8,254,590/8,251,261/8,250,967, with recomputed k=6, lower bound9 and tail9..14. e6=1 is consistent with the first helper. The raw index15 mirrors are only24,279/20,628/20,628; their bit1 lower-bound conditions fail, consistent with2fc=0. The first helper alone can therefore account for the selected selector value in that prior sample. This is a source/data consistency result, not a trace of the onset event.

## What this explains and what it leaves open

The selector depends on content-related table tails and debounced history, so different content can follow different branches despite the same nominal display timing. That structure can accommodate full Apps, a screen saver, sparse Live navigation and individual HDMI titles behaving differently. It does not yet predict those titles: no contemporaneous table/EXCO-field capture spans the failing and successful content cases, and the physical table producer and units are unknown. The packed-pixel difference/history path is also necessary: DH retained a clean sample with C+7 already1 and A0=0, proving that this selector alone is insufficient for the observed fault.

The next discriminators are source-qualified low-SRAM AP_EXCO fields and the actual retained formatter inputs, with fresh provenance and bounded reads. A threshold increase tests the final policy response; it does not identify the reason that different content produces the antecedent packed differences. No protection-disable or permanent-fix claim follows from this addendum.

`source-anchors.json`, `positive-upstream-anchors.disasm.txt`, the two bounded helper listings, `verify_upstream.py`/`byte-verification.json` and `slg_model.py`/`test_slg_model.py` make these statements reproducible. `field-reference-candidates.json` and `ap-context-writer-candidates.disasm.txt` remain candidate scans, not a complete reachable-writer census.
