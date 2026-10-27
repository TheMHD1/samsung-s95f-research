# QDF power-control hardware sequence

## Scope and result

This is an offline analysis of copied `qdf_tcon.ko` SHA-256
`97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63` and its
copied lower `tztv_frc_tcon.ko` provider.  No TV connection, power operation,
GPIO access, I2C transfer, or runtime trace occurred.  ELF offsets below are
not live addresses.

`m_set_power_control` (`qdf_tcon .text+0x11848`, 832 bytes) is a real
hardware-affecting lifecycle function, not a cache setter.  It invokes
registered DVDD/ELVDD/ACDET/reset callbacks and waits between phases.  Its
return value is only the accumulated lower callback status; several QDF cache
updates happen before those callbacks or despite an error indication.  It
does not directly send QDF I2C commands, and it does not write
`m_suspend_status`.

The public wrapper `QDFTcon_SetQdTconPowerControl` maps operation 0 to off,
1 to on, and 2 to off followed immediately by on.  That wrapper relationship
is included solely to identify the implementation entry; this report does not
provide a runtime procedure.

## State words written by the implementation

| QDF BSS word | Off (`m_set_power_control(0)`) | On (`m_set_power_control(1)`) | Interpretation limit |
|---|---|---|---|
| `m_suspend_status` `+0x0` | no direct write | no direct write | This lifecycle does not clear transport suspension. |
| `m_tcon_power_state` `+0x4` | cleared at `0x11a68` before rail work | set to 1 at `0x11938` on normal path; also at `0x11998` on nonzero ERR_DET sample | Cached intent/lifecycle state, not proof of a live rail or lit panel. |
| `m_tcon_state` `+0x10` | cleared at `0x11a6c` before rail work | no direct set; normal path calls `m_check_tcon_status(2)` at `0x1192c` | Status check is a distinct mechanism and its return is discarded here. |
| `m_pvcc_status` `+0x40` | cleared at `0x11a70` before rail work | set to 1 at `0x11900` before status check, or `0x1199c` on ERR_DET nonzero path | This is not `m_panel_dpms_pvcc_status` at `+0x194`; that other guard is not written here. |

The pre-action off stores are important: a later lower hardware failure does
not roll them back.  Conversely, the on route can report cached power/PVCC=1
after an error indication without reaching `m_check_tcon_status` or recovery
frame-mode setup.  Neither cache pattern by itself identifies the physical
cause of a dark panel.

## On path: `m_set_power_control(1)`

The nonzero branch begins at `0x1185c`.  It selects a board/configuration
path using `m_is_monitor` (`BSS+0x1a8`) and `m_platform_type` (`+0x1ac`):

1. If `m_is_monitor == 1`, call registered `tztv_frc_tcon_set_dvdd` at
   `0x118ac`, then wait **700 ms** at `0x118b4..0x118b8`.
2. Otherwise, if `m_platform_type == 4`, call registered
   `tztv_set_sdp_jp_tcon_power_reset(0)` at `0x119ec`, wait **100 ms** at
   `0x11a1c..0x11a20`, then join the 700-ms phase.  On other configurations it
   calls `tztv_frc_tcon_set_elvdd` at `0x11978` or `0x11988`, selecting the
   value from the monitor configuration; it then joins the same phase.
3. Call registered `tztv_frc_tcon_set_acdet(1)` at `0x118cc`.
4. If registered, call `tztv_frc_tcon_read_err_det_status(&local)` at
   `0x118e8`.  A nonzero sampled word takes `0x11994`: it sets only cached
   power/PVCC to 1 and returns accumulated callback status.  This branch does
   **not** call the TCON status checker or recovery-frame helpers.
5. If the status sample is zero, or the ERR_DET callback is absent, store
   `m_pvcc_status=1` at `0x11900`; call `m_check_tcon_status(2)`,
   `m_tcon_recovery_frame_mode`, and `m_register_recovery_noFramerate` at
   `0x1192c..0x11934`; then store `m_tcon_power_state=1` at `0x11938`.

The callback pointer may be null.  Null DVDD/ELVDD/ACDET/reset pointers are
generally treated as no lower action with the current accumulated value; that
is not proof that the requested rail transition happened.  The ERR_DET word is
also separate from the provider return code: before the call QDF initializes
the local sampled word to zero.  If the provider fails before writing it (for
example, GPIO request failure), QDF ORs the negative callback status into its
accumulator but sees the still-zero sample and enters the normal status/recovery
tail.  A negative raw GPIO read is nonzero and instead selects the short
cached-power/PVCC-only branch.

## Off path: `m_set_power_control(0)`

The zero branch starts at `0x11a28` and first clears power/state/PVCC caches
at `0x11a68..0x11a70`, before hardware callbacks.  It then:

1. Calls `tztv_frc_tcon_set_acdet(0)` at `0x11aa8` when registered.
2. If `m_is_monitor != 1`, waits **10 ms** (`0x11abc..0x11ac0`), then either
   calls ELVDD using the monitor configuration or, for `m_platform_type == 4`,
   calls `tztv_set_sdp_jp_tcon_power_reset(1)` at `0x11b14` followed by a
   **100 ms** wait at `0x11b40..0x11b44`.
3. If `m_is_monitor == 1`, it waits **1000 ms** at `0x11b4c..0x11b50`, calls
   DVDD with zero at `0x11b60..0x11b64`, and then takes the common final
   **1000 ms** wait at `0x11af4..0x11af8`. Non-monitor configurations have
   the earlier 10-ms wait and this final 1000-ms wait; platform type 4 adds the
   separate 100-ms reset wait.

Return errors from ACDET and subsequent chosen rail/reset calls are ORed into
the result (`w19`/`w22`).  There is no compensating restoration of the three
already-cleared caches on this error path.

## Lower hardware boundary

QDF imports the five callback objects; it does not define the hardware drivers.
`tztv_frc_tcon_api.ko` exports the callback-pointer globals, and the copied
TCON provider contains the lower routines:

| QDF callback | Lower implementation evidence | Hardware class established statically |
|---|---|---|
| ERR_DET read | `_tztv_frc_tcon_read_err_det_status` `+0x1af0` | Looks up a DT GPIO, requests it, makes it input, calls `gpiod_get_raw_value_cansleep`, writes that raw result to caller storage, frees it. Request failure returns an error without writing caller storage; direction/get return values are not separately checked by this provider. |
| ELVDD | `_tztv_frc_tcon_set_elvdd` `+0x7ec8` | Depending on platform, calls STBC GPIO helper ID `0x45`, or requests a DT GPIO and uses `gpiod_direction_output_raw` plus `gpiod_set_raw_value_cansleep`. |
| ACDET | `_tztv_frc_tcon_set_acdet` `+0x80b0` | Same pattern, with STBC GPIO IDs `0x47` or `0x64`, or a DT GPIO raw output. |
| DVDD | `_tztv_frc_tcon_set_dvdd` `+0x8f08` | Uses STBC GPIO ID `4` or `0x30` on its supported configuration; otherwise delegates to ELVDD implementation. |
| reset | imported `tztv_set_sdp_jp_tcon_power_reset` | Its definition is not in the copied modules, so only QDF's callback use and timing are established here. |

The STBC helper resolves an external symbol at runtime and calls it; the copied
objects do not establish the electrical polarity, rail voltage, controller
acceptance, or panel emission result. QDF itself has no I2C write/read call in
the body of `m_set_power_control`; its direct lower effects recovered here are
GPIO/reset and the ERR_DET GPIO read. The normal on tail is nevertheless
transitively capable of QDF transport: it calls `m_check_tcon_status`,
`m_tcon_recovery_frame_mode`, and `m_register_recovery_noFramerate`; the
recovered chain includes QDF reads at `0x10810`, frame-mode work at
`0x10890`/`0x1091c`, and command transport at `0xf880`. Those tail return
values are discarded by `m_set_power_control`, so its result is not a complete
success/failure verdict for the overall on sequence.

The direct-GPIO ELVDD path (`0x7ff4..0x8024`) and ACDET path
(`0x81c4..0x81f4`) have another error-reporting limit: their saved `w20`
is only the `gpio_request` status. They discard the direction-output return
at `0x800c`/`0x81dc`, and the following set operation has no checked status.
After a successful request they can return0 even if direction setup failed.
Consequently the QDF accumulator is an incomplete lower-hardware verdict
even before considering its discarded status/recovery-tail results.

## Interpretation boundary

The sequence can explain why cached state can look “off” even if a lower phase
fails, or look “on” even when ERR_DET blocked the normal status/recovery tail.
It does not establish that this sequence caused any observed blackout, that a
black panel is recoverable through it, or that executing it is safe.  Operation
2 has no wrapper-level delay between off and on; any timing is solely the
implementation waits above.  No control, reset, or workaround is recommended
from this static analysis.

## Reproduce offline

The hash-gated script below verifies exact source hashes and textual
instruction/symbol landmarks. The branch placement, two monitor waits,
sample-versus-return flow and discarded error paths were independently
reviewed manually; they are not all structural assertions in the script.

```sh
python3 tcon-research/qd-power-control-hardware-sequence-reproduce.py
aarch64-linux-gnu-objdump -dr --start-address=0x11848 --stop-address=0x11d78 binaries/qdf_tcon.ko
aarch64-linux-gnu-objdump -dr --start-address=0x1af0 --stop-address=0x1c30 binaries/tztv_frc_tcon.ko
aarch64-linux-gnu-objdump -dr --start-address=0x7ec8 --stop-address=0x82a8 binaries/tztv_frc_tcon.ko
aarch64-linux-gnu-objdump -dr --start-address=0x8f08 --stop-address=0x8fc0 binaries/tztv_frc_tcon.ko
```

These commands only inspect copied ELF files.
