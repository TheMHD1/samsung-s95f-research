# Owner progress update: reverse engineering and remaining fault attribution

No incident-aligned root cause, permanent prevention, or recovery from the latched black state has been verified. This status distinguishes reconstructed code paths from physical observations. Root remains host-assisted; untethered persistence is unverified.

## What is established

- Owner-observed sparse For You/Live pages can precede a persistent black physical panel while audio continues; populated Apps often keeps the picture visible. The physical damage and the failure predate root. This is a reproducible association, not proof that tile count is the underlying cause.
- Retained owner-observed black-state captures contain rich/changing software frames while the display pipeline continues reporting active state. That narrows the problem beyond an empty application drawing a black page, but cannot distinguish final buffer selection, downstream programming, or a panel/controller fault.
- Exact-binary static analysis now follows content-dependent dimming through AVOC, its userspace API, kernel dispatch, the FRC extension bridge, SDP register access, and the allowed-access ARM64 register-store instruction. The normal immediate dimming candidate is clamped above zero. Neither finding establishes which branch ran at blackout onset.
- Save/replay paths, cached output state, error-monitor interpretation, and several dispatch/access gates have been reconstructed. A cache can advance before successful output programming is established, and a zero return can accompany a skipped request. These are candidate mechanisms requiring runtime evidence, not diagnosed incident causes.
- A finite read-only device-tree metadata capture supplies explicit parent cell widths and the bus range. The offline decoder passes byte-length/hash/framing and translation checks: the DT-described FRC resource is CPU address 0x00b90000 through 0x00beefff; selector 0x42b48 falls at 0x00bd2b48. This is a resource-description calculation, not an MMIO read/write or proof of output application. The new decoder has not yet received independent review.

## Important limits

- We have not tied a specific instruction, command, controller response, or fault signal to the moment the physical panel goes black.
- We have not established whether the damage triggers a hardware fault, software mishandles/replays state after a fault, or both.
- No successful physical recovery or permanent prevention has been demonstrated. Previous redraw, menu, composition and setting experiments did not recover the observed latched-black state.
- The latest actual five-second combined capture remains rejected. Raw evidence and cleanup are preserved. A corrected observer passed 57 offline tests but has not run on the TV.
- The newer pre-roll design was independently cleared as a design only (SHA256 1e0935d8ad62161d3ee00c194265f0a771f97ef84379b5470f8c7fd2710565cc). Implementation, tests and runtime validation remain outstanding; the rejected trace is not retroactively accepted.

## What would move the diagnosis forward

Implement and validate the reviewed pre-roll design, then capture an owner-observed transition from visible populated Apps to a sparse page and physical blackout. Correlate that transition with paired calls, typed state, controller traffic and fault indications. A proposed prevention change then needs an observed reboot-and-trigger test as well as a stable visible control. No percentage completion or repair-time estimate is supported by the evidence.

Detailed evidence is linked from [the current investigation entry point](../../CURRENT-INVESTIGATION.md), especially the SDP register path, monitor provenance, cached/replayed output analysis, and observer smoke reports. Historical reports and frozen evidence manifests remain unchanged.
