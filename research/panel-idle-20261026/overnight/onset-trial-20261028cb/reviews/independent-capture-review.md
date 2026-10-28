# Independent CB synchronized-onset capture review

**Accepted within the declared scientific scope.** CB is an actual synchronized one-Left trial that passes the frozen transport, key-workflow and observation-window contracts. It is strong handoff evidence for a clean-to-fault controller RT transition after a normal Apps-to-Live stimulus, with a separate owner-reported physical blackout. It does not prove the exact time of light loss, UI event-consumption time, key causation, the complete threshold/producer mechanism, or unconditional endpoint queue liveness.

This is the first actual synchronized one-Left capture reviewed here that meets both transport and temporal qualification. This is not a claim that no earlier instrument ever observed an RT transition. Prior rejected collectors/trials retain their original classifications. No TV, root, USB, UI, reset or network operation was performed by this reviewer; only this review and its owned offline verification artifacts were written.

## Independent acceptance checks

`independent-capture-artifacts/verify_capture.py` reran the exact SHA-pinned strict parser against the original 12,572-byte native stdout, checked the saved empty stderr and execute framing, and compared parsed qualification/captures with stored results. It independently decoded the RT stop/fault/gate halfwords from raw bytes at offsets0/10/14. All18 saved raw windows match both embedded bytes and SHA-256 values, with no missing or extra retained-window files. Six R windows independently decode as four Clean `(0,0,1)` observations followed by two Faulted `(1,0x1001,0)` observations.

The exact reviewed manifest remains `8cb73c48ff6ef21e13e563efc96b59aa7f6353054d3f433cd3962d24523515ff`. Current frozen source/payload checks reproduce those exact manifest bytes. The readiness copy hashes to `9c4ee8958b453d944f9dbf8279c86704e97bcca8be2bc7a7766768d7da7aacac`; all11 referenced evidence files match their pinned hashes, including the CA v2 phase statement, visible-Apps owner record and normal-key header refresh. The decision binds fresh instance54 and keeps endpoint queue proof false.

All31 authenticated recorded shell calls have exact command echoes, zero shell exit, no timeout and empty stderr. There is one native execute and one later cleanup, with no wrapper UI/reset/forced-collector command. Terminal native exit0, ReadyForHeader, release/close and exact `STAGE_ABSENT` are verified from the original returned envelope, not only result flags. The three census receipts show10984/10986/10986 operands, zero observed holders/errors and postcheck one ENOENT churn; they retain their non-continuous, non-atomic meaning.

Both normal and optimized Python runs pass **280 explicit independent capture checks**. The verifier has no root adapter import or target/network call. Its derived artifacts preserve hashes and scientific summaries without copying the private authenticated transport envelope.

## Counter and retention accounting

| Quantity | Verified result |
| --- | --- |
| Native terminal reason | `TransitionCaptured`, cycle6 |
| Completed clean cycles | 5 |
| Discarded rolling clean cycles | 4 |
| Global headers / completed inputs / bulk transfers | 36 / 36 / 72 |
| Global request accounting | 5×6 clean-cycle pairs + 1 transition R + 5 post-fault pairs =36 |
| Retained windows | 6 cycle-one baseline + 6 cycle-five last-clean + 1 transition + 5 post-fault =18 |
| Key workflow | Exactly one Left down/up, both exit0, reaped, no timeout |
| Final transport state | ReadyForHeader, released=true, closed=true |
| Remote stage cleanup | `STAGE_ABSENT` |

The cycle-one trigger baseline is retained independently of rolling LastClean. It is a duplicate retained copy of already counted I/O, not six extra requests. Global counters are unchanged by parsing. Cycles2..4 are not retained as raw windows; their completed-clean status is native counter/source evidence, not independently recovered discarded bytes. Full retained cycle1 and cycle5 establish actual clean baselines before the fault.

## Actual monotonic ordering

All times below are target monotonic microseconds. USB intervals encompass OUT-before through matching IN-after; they are conservative sampled intervals, conditional on reply freshness.

| Event | Before / after or time |
| --- | --- |
| Cycle-one full clean baseline ends | 167670015753 |
| Action armed | 167670018061 |
| Left down child call/return | 167670020734 .. 167670151007 |
| Left up child call/return | 167670302109 .. 167670327726 |
| Latest retained clean R pair, cycle5 | 167671010145 .. 167671010211 |
| First retained fault R pair, cycle6 | 167671260342 .. 167671260439 |
| Native observation/reconciliation ends | 167671262404 |

The conservative software transition bracket is **167671010145..167671260439**, width **250,294µs /250.294ms**. Both its clean and fault observations are strictly after down **and up** returned. Its start is859.138ms after down return and682.419ms after up return; first fault OUT begins1109.335ms after down return. This closes the earlier missed-key-window problem: the key did not begin after the recorder's last completed read, and a completed R pair exists after dispatch. It does not mean the physical panel lost light in this250ms interval or that the key caused the RT change.

The exact native/parser contract calls the trial qualified while explicitly retaining false UI-receipt, physical-picture and key-causality claims. A separate post-capture ordinary UI snapshot reports cached `d/ug.tab@Live`, CSFS present and no saver. That supports navigation having occurred by that later snapshot; it does not timestamp consumption of the key within the RT bracket.

## Readiness and physical evidence

CA contains a directly observed53 disconnect→54 enumeration/configuration and matching identity; the retained BS premise remains conditional on vendor configuration callback/state stores, with receive-submission success and global actor absence unproved. The serialized decision includes completion of the same unchanged MODE2 I2C tail, later cached metadata, and the separately recorded normal-key header refresh. It does not impose an unsupported all-I2C-return2 gate or claim an endpoint queue measurement. The successful exact OUT/IN sequence carries modeled subsequent ReadyForHeader transitions within this accepted capture; it does not retroactively remove the initial premise's qualification.

The owner confirmed populated Apps visible after CA initialization. A later screensaver occurrence was handled by separately recorded normal-key wake/Up/Up preparation; its final cached state was Apps/CSFS with no saver. Those preparation actions are in the v2 ledger, not hidden native interventions. After the capture the owner reported “panel went dark” and suggested navigation outside Apps as an explanation. The physical observation is valuable; that explanatory suggestion remains a hypothesis. The retained owner record correctly gives no instantaneous transition timestamp and no proof that physical light changed within the software bracket.

## Later recovery is a distinct, rejected harness outcome

The subsequent operational recovery does not alter the already completed CB capture. `verify_recovery.py` independently passes16 checks normal and optimized: the MODE2 top-level record is **accepted=false**, cleanup=true, error `ContractError: Remote command stderr`. Its single returned native execution reports helper exit0, operation41/mode2, ioctl0 and close0, but the remote lifecycle also emits an ENOENT stderr from reading the exited helper's `/proc/PID/stat`. The quickpath child exits1 and has no completed `recovery/result.json`.

Keep those native lines as narrow retained observations; they do not rehabilitate top-level acceptance. The owner separately reported visible Apps again. No exact physical return time is provided. The parent classification retains zero retries and no post-MODE2 key. Neither that physical return nor the recovery harness rejection changes the accepted earlier onset result.

## Handoff and provenance

Use CB as the accepted synchronized software-onset case, with its18 exact raw windows, first-clean baseline, delayed clean/fault ordering after the completed key pair, explicit CA premise and independent physical observation. Preserve missing facts for the next analysis: actual event operands/producer units, exact physical-light timing, exact UI consumption and causal mechanism. Do not recast a later recovery or an old rejected trial as part of this accepted recorder.

| Input / derived artifact | SHA-256 |
| --- | --- |
| Original native stdout | `9536615e385ac7b489460d2db1e3770ad7532953b51ec29f3e623f8c1b0a39f2` |
| Original execute envelope | `45ee77be970d4f49ab0f733dbaae91857d0019fa95cd1774798513b4ff2a0f0b` |
| Original private transport record, not reproduced | `d627bbaac5baeffd302a1a7e5abe0903be97396198de47a0b32da8bf677724c3` |
| Stored wrapper result | `a505eed4e3045c273ad48e2de580f6a1b49263d7f357942ce7525421c5d6281d` |
| Owner blackout record | `523376660ba8a3b7e424c517a9f7b0a7ac15aef02c702a3a5aa1684e84553a0c` |
| Independent verification.json | `7f10ba16284942b2832268ab35cdf966ae464a55c605f7f10204a7fff684a158` |
| Independent parsed-result.json | `1512153dd4c27b58b533ca1c2eb6876c6b88d6b640d3fd35dcc2c2773e6b4d65` |
| Independent later recovery verification | `79ebacf4d7e7e30ab78582898167f87e8afa3b54ab406da901c984366b5fd3be` |
