# Request-replay follow-up review and corrections

This records bounded offline review of the new phase, separate from the immutable earlier evidence. No repair, firmware/kernel patch, target call, factory setting, cache write or physical test was performed by these reviews.

## Send-buffer dataflow

The monitor/lifecycle reviewer independently checked the parent-authored one-command buffer report/helper against the exact acquired library and ran the checker successfully. It confirmed that Send dereferences the caller pointer once at `0x2519f4`, replaces the register with the scalar, constructs an envelope in its own stack frame, and has no caller-pointer preservation or output store. The adjacent Read method preserves the pointer and copies back at `0x251af8` after a nonnegative result. The interprocedural conclusion is limited to defined copied stock execution, with no runtime PLT/GOT binding, concurrent corruption, transmitted value or physical result established.

The parent corrected its initial disassembly split before preserving generated output: the backend literal pool begins at `0x1c634c`, not `0x1c6350`. Literal bytes are retained as data rather than misleading branch instructions. No erroneous draft was run on the TV.

## Userspace resume-record audit

The parent inspected raw instruction sequences in `t_SetQdResumeData`, `t_DevQdDrv_Write_Data` and `QDDimming::m_SetResumeData`, then ran the corrected reproducer. Review caught two draft CFG/address errors before acceptance:

- `inner + ((0x115+i)<<3)` is command base `inner+0x8a8+8*i`. There is no extra `+0x8a8` base. The draft's `+0x1430` was incorrect; the helper now pins the arithmetic.
- `QDDimming inner+0x398 != 1` returns without clearing. Only the exact-one route clears the gate after the optional backend call, including its null-backend case.

The current report distinguishes backend-inner storage from QDDimming-inner storage and the 16-slot table from the final-duty static and kernel table. It preserves the producer's signed upper-bound-only check rather than inventing a lower-bound validation. The intended slots are 0..15; reachability of negative input or actual corruption is unobserved. The checker verifies static landmarks and a bounded direct-call inventory; table contents and incident execution remain unknown.

## Kernel replay audit

Parent review and the local checker support the exact positive edge: a 226-key table includes F3:0x128 at index 218, generic sends cache first, and six direct recovery call sites reach generic replay after frame-mode recovery. The recovered normal power-control off path does not clear the record arrays; eligible on tails attempt replay. Individual lower results are discarded, and the separate userspace FRC write leg is not established by this mechanism.

A draft's cross-component absence wording was narrowed before acceptance. No direct userspace-cache write or explicit invalidation event was recovered in the bounded bodies, but external callbacks and other-process reactions are not fully traced. The positive result is kernel request retention/replay, not proof of global userspace-cache lifetime, actual reset behavior, lower success or physical light.

## Expanded reader and actual capture

The separate [branch-baseline review](pqe-branch-baseline-independent-review.md) preserves the independent pre-run clearance and raw-result audit. The parent performed exactly one finite authorized read at the frozen source/test hashes. It returned accepted in 0.88 seconds. No physical state was observed. A conditional arithmetic match to working/cache 256 is useful consistency evidence, not proof of branch execution, command emission or panel state.

The previous 81-file, 176-file and 43-file snapshots remain historical evidence; new corrected interpretations are additions rather than edits to those files. Hash indexes and checker PASS results preserve/reproduce bounded evidence; they do not turn manual CFG interpretation into physical fault diagnosis.
