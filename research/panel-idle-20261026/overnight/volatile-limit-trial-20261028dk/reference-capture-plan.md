# Next bounded read-only reference discriminator

Purpose: test whether source-compatible reconstructed amplitudes in the mode1
fault records match the retained fixed top or bottom packed reference buffers.
The former RAM-limit experiment remains held; no writer runs in this plan.

DR qualified the fixed payload bases CPU20015000/20015f10, four12-bit lanes per
sixbytes, no8-byte header and no channel stride. For captured xbase0, candidate
positions570/571,622/623,624/625,632/633 are covered by group-aligned lanes568..635.
The exact candidate windows are top bus47015354/104 and bottom47016264/104;
decode102bytes and ignore the last2bytes. They fit the established low-SRAM
alias. No alias is inferred for dynamic ringCPU20253002. Source/readiness and
transport review of the new fixed reader must finish before target execution.

1. With fresh USB59 identity/census and explicit closed-world completed-DM
   lineage, execute the new fixed reader once on normal Apps. Retain all original
   twelve DM windows plus top/bottom candidates; validate every exact pair,
   source contexts, readback hashes, release/close/cleanup, profile and xbase0.
2. Prepare the previously calibrated Apps/header context using normal keys,
   bounded read-only settle observations and no key retries. Fresh DP readiness
   follows the completed fixed-reader pairs. Execute one unchanged40 DP onset
   trial, with one normal Left inside the recorder. A clean20second run is a
   valid negative observation; do not manufacture a fault by extra keys.
3. If a qualified software fault is captured with exact closed protocol,
   collect one fixed-reference snapshot before any UI recovery. Compare start/end
   R/N/context against the retained DP endpoint. Interpret candidates by x only
   if xbase remains0 and geometry matches. Preserve unknown epochs, mixed-type
   records, sequential reads and all raw tails. If the first48 prefix saturates
   or differs, report it rather than forcing the earlier41-record shape.
4. Compare both candidate windows with the prior clean windows and reconstructed
   12-bit A candidates. A later exact match is supporting evidence, not proof
   that historical comparison used that buffer. The actual B-header row, selected
   A pointer and producer epoch remain missing and motivate a reversible
   executable-checkpoint feasibility audit; no unqualified code patch is added.
5. After a qualified, released, closed fault capture, select normal Apps and
   issue one separately recorded bounded stockMODE2 request if public rejection
   gates permit. Retain disconnect/re-enumeration identity/census; read actual
   RAM state afterward before any future intervention. If a capture is ambiguous
   or phase Unknown, send no additional vendor header, automatic retry or reset.

The parent alone performs target/root/USB/UI calls. No controller code, persistent
filesystem, boot configuration, flash, arbitrary register or power setting is
modified. A successful software receipt is not physical-light verification.
