# Deferred Home-exit restoration in the Rosem output driver

## Source and scope

This offline continuation resolves a deferred consumer left open by [newhome-frc-output-policy.md](newhome-frc-output-policy.md). Source `binaries/rosem_frc.ko` is 304,006 bytes, SHA-256 `c646b45d8ab5028defca91b5f8188bf905b8d29f8927fae292be591c94cdbd34`. The hash-gated helper `overnight/trace-newhome-exit.py` verifies function bounds and produces [newhome-exit-resolution-disassembly.txt](newhome-exit-resolution-disassembly.txt), with original instruction bytes and actual ELF relocation annotations. Run with `PYTHONPATH=/tmp/tcon-capstone python3 overnight/trace-newhome-exit.py`; it prints local analysis only and contacts no TV. All addresses below are section-relative, not live kernel addresses.

This does not prove an observed Home/Apps transition called these routines, changed physical timing, or caused a blackout. No output-control or factory function was invoked.

## Flag creation

`RosemFrc_SetNewhomeMode` at .text+0x7bd8 compares requested and remembered `m_newhome_mode` (.bss+0x18c). Equal requests return without calling the lower helper. On a changed request it stores the requested mode at 0x7ca8 before calling `m_rosem_set_newhome_mode` at 0x7cc0 (with a special entry skip for the vfreq_144 flag).

The lower routine at 0x37b8 handles input other than 1 by logging its skipped immediate-off operation and storing 1 into `m_newhome_exit_flag` (.bss+0x190) at 0x3a20. It does not itself perform a complete restoration. Thus a remembered Home-off value is not proof that output timing has already been restored.

## Actual consumer and restoration path

`RosemFrc_SetResolutionInfo` (.text+0xb280, 1,804 bytes) establishes x21 as the .bss base using relocations at 0xb284/0xb294. Its upgrade/EW-test gate at 0xb2a0..0xb2b4 can return before copying or applying new resolution information. On the ordinary route it copies a 0x7c-byte incoming structure at 0xb2f0 and updates current resolution/rate/source fields. It compares them against remembered values later in the function.

The Home-exit flag is a reason to reapply output configuration even when some resolution values have not changed:

- If current and remembered input vertical frequency differ (0xb4b8..0xb4c4), a nonzero exit flag branches from 0xb4c8..0xb4cc to its clear at 0xb56c, then enters the common application path at 0xb4d0.
- On the same-frequency path with matched resolution and scan prerequisites, the check at 0xb618..0xb620 similarly forces that clear/application path when the flag equals 1.
- Other low-input/VRR branches read or clear the same flag at 0xb564..0xb56c and 0xb7e0..0xb7e8. These branches must be evaluated with their input flags; they are not a universal unconditional restore.

The common path considers low-input-lag, VRR/QMS, cloud-game and ambient flags before optionally calling `m_rosem_low_input_lag(0, ...)` at 0xb6b0..0xb6b4. It calls `m_rosem_set_2d_video` at 0xb4dc and ORs that result into the accumulated return status at 0xb4e0. Depending on configuration it may also invoke the registered monitor-mode callback at table slot +0x5c8. The function records current resolution, frequency, scan and rate-policy fields into its remembered comparison fields at 0xb504..0xb538. Unless the WOLED-cell-type-3 branch skips it, it then calls `m_rosem_set_tcon_frame_rate` at 0xb544 and includes that result in its accumulated return status.

For comparison, if fields match, the exit flag is not set, remembered Home mode remains 1, and `m_vfreq_144` is zero, 0xb624..0xb638 can reapply the Home-entry helper with argument 1 before joining later processing. This is separate from the exit-flag route.

## Failure and retry boundary

The exit flag is cleared before common output work, not after independently proving successful physical restoration. No rollback of that flag appears in this function if `m_rosem_set_2d_video` or the final TCON-rate helper returns an error. Remembered resolution fields are also updated before the final rate-helper result is known. The already analyzed rate helper separately remembers its requested rate even when its callback fails or is absent.

This is a concrete cache/error-propagation boundary: software can remember an attempted configuration without that proving accepted hardware timing or emitted light. It is not proof that any such error occurred during the owner's incident. Further resolution changes or different branches may reapply configuration; this analysis does not claim that all future retry is suppressed. An identical `SetNewhomeMode` request alone can be skipped by its separate equality check.

The final frame-rate helper can reach the previously mapped QDF frame-mode implementation, including its panel-mute bracket. That downstream possibility is already documented; no new mute or power-off call is established merely by reading the exit flag. Two different tabs within Home are not automatically Home entry/exit transitions, so this path does not by itself explain the owner's dense-versus-sparse distinction.

## What to correlate next

A physically observed transition should retain existing Home-mode/resolution/frame-rate logs, raw QD frame/mute transactions and fault-state samples together. A failure in these calls with caches advancing would support investigating replay/recovery of one missed configuration. A blackout without the corresponding calls/transactions would direct attention elsewhere. There is no justification yet to force a mode, patch the flag, or repeatedly send unmute commands.
