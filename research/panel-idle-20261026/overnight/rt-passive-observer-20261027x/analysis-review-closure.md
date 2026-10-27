# X analysis review closure

Recorded 2026-10-27 UTC. This review and decoder rerun made zero target or network operations.

Root corrected two material interpretation boundaries identified by independent review:

- CPU meanings for C/H/L/R are conditional. U's mapping-qualification report is pinned by the decoder. M's same-response anchor does not prove all aliases; H has no live core tag or same-response anchor. The mode-1 / 44 > 40 candidate explicitly depends on those assumptions and the selected-code interpretation.
- H returned mode-6 A32=0 before L returned latch54. This is sequential evidence, not proof of simultaneous divergence, staleness at the L read, or absence of intervening writes. Static last-write latch provenance requires separate interpretation.

Earlier root timing corrections remain: the 427us request sequence includes the first M header; Linux uptime is compared with Linux uptime for the 10734.71..10754.77s terminal gap. No cross-clock event-age bound is established.

Final read-only independent re-review passed with no material issues. The reviewer verified the final source/report hashes, U qualification pin and identical normal/optimized output. Runtime source/transport audit remains recorded separately in runtime-review.md. No physical onset or repair is inferred.

`alias-qualified-retained.normal.json` and `alias-qualified-retained.optimized.json` are the accepted current outputs. Earlier `retained-decoder.normal.json` and `.optimized.json` are preserved as superseded review history; they omit the explicit CPU qualification and overstate the sequential mode-6 comparison. Do not use them as current conclusions.

| final artifact | SHA-256 |
| --- | --- |
| `decode-retained-state.py` | `5aa7dd8c16520ca62065df9bab134328b7b1aa42b70c431f807003cb8767d1f6` |
| `retained-state-findings.md` | `ec8cc0ab0906ac34cd84de6a4f3f383febccb3d9c8e19c1ea570594edc540658` |
| `alias-qualified-retained.normal.json` | `0f67a6828a7b9296abeda988d7fa22bc92a5133ebd5ebbc8918fd5f0aec49b72` |
| `alias-qualified-retained.optimized.json` | `0f67a6828a7b9296abeda988d7fa22bc92a5133ebd5ebbc8918fd5f0aec49b72` |
