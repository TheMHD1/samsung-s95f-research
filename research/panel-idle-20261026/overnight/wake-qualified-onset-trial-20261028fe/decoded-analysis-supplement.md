# Completed FE scientific decode supplement

This additive record supersedes the preliminary “detailed replay pending” wording in the parent checkpoint without changing the original observations, receipts or checkpoint.

The [capture replay](capture-analysis/README.md) verifies 110 pinned inputs and 442 explicit checks. There are 43 Clean/Clean compact rows and two Quiescent/Quiescent rows (20 and 21), followed by the first fault R in cycle46. Last-clean45 samples H0low16=40 and scan1; the later postfault context samples H0low16=42 and scan0. Both contexts retain AA0/AC2, C7=1 and the sampled root20010000. Those windows are sequential; actual comparison FP, selected-A and caller are still unobserved.

The last-clean R header begins at193956100871us and the first-fault R data completes at193956126149us, a conservative software read span of25278us. Native observation span is1168146us; median H-header start spacing25861.5us. These native clock coordinates do not measure the optical black edge and cannot be subtracted from host monotonic or remote uptime coordinates. Compact maximum40 excludes the separately retained postfault42.

An independent reviewer reconstructed the key claims from original raw evidence in FG/reviews/fe-claim-check.json. Capture analysis inventory: bd9f5632df1310c57ac1ce9a4a1d144d8bf7fe3cf44cc5036dd8dc59ce73114b.

The [separate recovery replay](recovery-analysis/README.md) verifies 220 pinned inputs,1197 checks and11 malformed refusals in normal and optimized modes. It binds both EB workflows, one stock MODE2 request, positive same-boot USB64→65 and clean40/N-allzero validation. X/Y/RGB/B remain nonzero after recovery (48/48/26/22 nonzero u16 entries), so universal clearing is disproved by these samples. Final Apps+saver is cached UI, not physical-light proof. Recovery inventory:6df2bebc82b1ed3ca261f9cbf95de7a93e6eecf0ff40ba61b2f9997b68a70e62.

The scan1→0 observation changed the combined logger cleanup design: fresh cleanup admits only source-qualified scan0/1 and does not require the initial scan1 after a deliberate fault. FG remains a separate instrumentation experiment. No instruction, kernel, boot, flash or permanent prevention change is established here.
