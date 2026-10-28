# ES accepted Quiescent-to-fault observation

The original ES baseline → ER → admission → post-EB sequence is independently verified as an accepted software observation. ER records28 complete compact cycles (26 Clean,2 Quiescent), then an R-start fault at cycle29:232headers,464bulks, ReadyForHeader, released/closed and exact stage removal. Both separate EB reads also pass their original16/32 contracts and cleanup. No writer, mask, recovery or second key workflow is part of this observation.

This is a new case, independent of the rejected EO UnexpectedRt record. It is not a physical blackout observation or proof of UI consumption, actual selected threshold, comparator call, callback execution, source epoch or root cause. The native key intends the Apps-header transition, but dispatch success does not identify the resulting destination. Later UI/recovery observations are outside this original-capture snapshot.

The complete28-row timeline, retained raw-window metadata and hashes, key times, read brackets, lifecycle receipts, baseline/post samples and trace events are in `decoded.json`. `input-pins.json` binds284 retained inputs without copying raw root envelopes or OEM byte windows. The checker verifies both frozen source inventories, original strict parsers, exact saved raw inventories and envelopes, root command completion receipts, readiness/evidence hashes, admission, all10 orchestration completions and cleanup. All47 ER source files and the EB source inventory remain frozen. It performs no root-adapter or network import/call and submits no subprocess or target operation.

## Sampled sequence

| Complete cycle(s) | R boundaries | C7 / end-R+ca | M+22 mirror / M+24 counter | M publication mirror | H A0 / N ordinal0 |
| --- | --- | --- | --- | --- | --- |
|1–14|Clean / Clean|0 /0|0 /0|200|0 /0|
|15|Quiescent / Quiescent|1 /1|0 /0|200|0 /0|
|16|Quiescent / Quiescent|1 /1|1 /1|200|0 /0|
|17–18|Clean / Clean|1 /1|1 /1|200|0 /0|
|19|Clean / Clean|1 /1|1 /2|200|0 /0|
|20|Clean / Clean|1 /1|1 /0|40|0 /8|
|21|Clean / Clean|1 /1|1 /0|40|8 /8|
|22|Clean / Clean|1 /1|1 /0|40|8 /14|
|23–25|Clean / Clean|1 /1|1 /0|40|14,20,26 /20,26,34|
|26–28|Clean / Clean|1 /1|1 /0|40|34,34,40 /34,40,41|

Offsets22/24 in the table are hexadecimal M offsets (CPU4c2/4c4). All rows retain alternate limit40 at both R boundaries. Quiescent means exact0/0/0 at40; it is neither Clean nor Faulted. Cycle29 first-R is1/4097/0. No full cycle29 compact record is invented.

The last compact H read is40 at187705386145..187705386226us, history[0,0,8,0]. Its preceding N read already has ordinal0=41 and all six source counts0. The later, separately retained post-fault H reads **48** at187705412784..187705412866us, history[8,0,0,0], Q0=0. Thus compact maximum40 does not mean the retained state never exceeded40. Nor does H48 establish the exact selected FP or other historical predicate operands.

The mirror/counter sequence0→1→2→0 is consistent with selected-source seeding and two qualifying boundary events. It does not show distinct top/bottom refreshes, actual headers, which buffer was copied, every callback, exact reference age or a causal reason for failure. The source permits repeated boundary kinds. The M publication mirror200→40 is an observed sequential value change; it is not proof of the actual comparator argument at an unobserved call.

Trainer M+2/+4, end-R+60/+6e/+68, Q0 and other explicitly listed compact controls are zero in all28 complete rows. They are sampled controls, not proof that every related writer was inactive between reads. Dynamic pointers use three observed values20253002,20253b6a and202546d2 (strideb68); the post-fault pair is A20253b6a/B202546d2. These are pointer values rather than captured B headers or active/historical branch proof.

## Timing and workflow

One Left down/up starts only after full Clean cycle1. Down runs187704635459..187704890042us; Up runs187705041179..187705079231us; both children exit0 and are reaped, with no retry. Key dispatch is not UI receipt or physical light.

The retained software transition is bracketed by last Clean end-R OUT-before187705386309us and first Faulted R IN-after187705412276us: **25,967us**. The last Clean read itself ends187705386393us; the first Faulted pair starts187705411512us. These whole-request brackets are conditional on reply freshness and do not provide an instantaneous controller/physical sample. Both retained nonfault and fault reads occur after Down returns; causation is not established.

Native duration is797374us. Across27 H-start intervals, minimum17,701us, median25,804us and maximum95,238us; the largest gap is cycle5→6. The requested25ms pacing is not a guaranteed rate and can miss shorter events. Complete compact rows preserve H pair brackets only; intermediate R/M/C/P/N pair times are not retained. The original full raw cycle15/16 was overwritten by the bounded rolling slot, so no exact Quiescent R pair brackets are reconstructed from H times.

Same-native-clock gaps are13,558,641us from baseline EB last-IN to first ER OUT, and10,862,131us from ER final-IN to post-EB first-OUT. The post-table observation therefore cannot be an atomic post-fault sample. These calculations use the byte-identical retained native clock implementation, not ftrace timestamps.

## Baseline, post tables and binding

Baseline EB is Clean0/0/1 at40, C7=0, M mirror200, N ordinals/counts0 and both fixed-reference windows zero. Post-EB is Faulted1/4097/0 at40 at both boundaries, C7=1, M mirror40 and ordinal0/latch41 with counts0. Its fixed reference windows are populated. All68 primary halfwords and secondary bytes are zero in both observations: local eligibility at those sequential table samples, not proof that the comparator actually reached any lane. AA0/AC2/override4cc0 makes captured SB false; operating mode4 is a separate field from the category/type selector.

The post columns contain41 coordinated nonzero X/Y entries (Y2159), RGB0, changed B and unsigned differences. Remaining X/Y/RGB/Diff entries are zero while B can remain nonzero. N count0 and latch41 do not establish a current valid prefix or historical epoch; no selected-A value or branch is inferred here. The original48 tuples and descriptor halfwords are retained in derived metadata for later conditional analysis.

Both EB receipts independently validate the complete three binding stages: native driver absence before opening, kernel ENODATA61 on the unclaimed FD, then owned same-FD GETDRIVER usbfs plus matching canonical native device/inode after claim. Successful ER intentionally retains `bindingQualified=true` rather than the large full audit, according to its frozen reviewed source. The baseline/post full audits corroborate their own invocations; they are not substituted for absent ER success-stage metadata. Cached readiness and empty holder censuses remain non-atomic metadata, not endpoint queue proof.

## Private kernel trace

The accepted trace is3393bytes, SHA256576c8e602d7e78be8b873a0e6c1526503c6fff768aaa84d1db0101a8553752b7. It contains28 events forming14 ordered IRQ30 entry/exit pairs, all9c0400.msgbox. Each of four CPU statistics reports zero overruns, commit overruns and dropped events; CPU2 accounts for all28 entries. No IRQ84, configured GPIO or suspend_resume event is retained. This absence applies only to the selected event/filter scope; it excludes neither uninstrumented paths nor controller-local changes.

The start receipt selects ftrace mono and preserves global tracing0/nop; stop again preserves0/nop and removes the private instance. Kernel trace timestamps span187680.104905..187715.126247 in their own domain. No mapping to the native observation clock is demonstrated here, no trace/native timestamp subtraction is performed, and task-name coincidence does not become a controller callback trace. Source-directed GPIO/IRQ filters are pinned; they are not a physical power measurement.

## Reproduction and source provenance

Run `PYTHONDONTWRITEBYTECODE=1 python3 analyze.py` and again with `python3 -O`. Both modes reproduce `decoded.json` byte-for-byte, check284 pinned files and refuse12 malformed clones of the actual receipt. No raw OEM window is duplicated in this directory. The first `--write` creates the derived JSON; normal checking requires the existing byte-exact output.

The principal pinned source anchors are ER `ScoreCheckpoints.cs` (58-byte layout; end-R+ca/+68 at offsets54/56), `Program.cs` (exact state classification and eight read pairs), its three decoder layers, EB `parse-result.py` (table/tuple/reference offsets and three-stage binding), and the frozen ES admission/coordinator. EG source-audit covers image1c250 and1c12c seeding/copy semantics; EJ covers3934/394e/3952 and39fc/3a02 for C7 and root24ca; EC covers the separate trainer control. Their exact file hashes are included in the input manifest. Source semantics, sequential observations and unproved execution are kept separate.
