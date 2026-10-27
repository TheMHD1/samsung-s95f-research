# Runtime HWC prevention trial — 2026-10-26

Purpose: distinguish recovery of an already-black panel (failed) from prevention when fallback is active before an owner power cycle. One variable only; no factory/firmware changes.

Exact mapping, agreed by live readback and corrected static branch tracing: `enlightenment_info -hwc 0` sets `deactive:1` (client composition fallback); `-hwc 1` restores `deactive:0` (normal HWC). Parent disabled the historical inverse-mapping probe; its artifacts are not relabeled.

Started 03:52:41 UTC, boot `00000000-0000-4000-8000-000000000000`, uptime8370.89. `active.json` verifies deactive1. Same boot/deactive1 at03:56:03 and03:56:43. At03:55 owner was told to ordinary remote power-off/on then visit Live. A true OS reboot can remove this runtime change, so post-wake readback is required before interpretation. No owner outcome received at time of this note.

Host trial finally restores CLI1 after300sec; independent TV shell after330sec also restores CLI1. Root command failures are saved. `restored.json` must show deactive0; a successful API call does not prove physical picture. Do not rerun trial.py: it refuses existing evidence.

Host restoration completed at03:57:44 UTC: same boot, command exit0, `deactive:0`; host trial exited. Owner outcome had not been received before expiry; no valid prevention result yet. Parent informed owner at03:58 that fallback was no longer active and to hold off if not yet power-cycled.
