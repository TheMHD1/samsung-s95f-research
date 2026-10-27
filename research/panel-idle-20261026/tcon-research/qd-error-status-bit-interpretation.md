# QD ERR-DET status word: bit interpretation and monitor boundary

This is a static, exact-build interpretation of a *potential future fresh*
ERR-DET status word. It does not obtain one. The inputs are
`binaries/libave.so.0.1`, SHA-256
`a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777`, and
`binaries/qdf_tcon.ko`, SHA-256
`97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63`.
No TV, network, root, monitor, GPIO, TCON command, power control, setting, or
process was invoked.

## Decoder for a fresh raw word

For the QD product path, `ave_tcon_qd_err_detect_status()` (Thumb code
`0x268cbc`) calls the ordinary status getter then tests the raw result with
each mask below. Each asserted bit produces its literal vendor label; bits are
independent, so a multi-bit word has multiple labels. The function returns the
unmodified raw word. These labels are not expanded into electrical thresholds,
component diagnoses, or an emission/power state.

| bit | mask | literal label | AVE test branch |
| ---: | ---: | --- | ---: |
| 0 | `0x01` | EL OCP | `0x268d00` |
| 1 | `0x02` | EL OCP2 | `0x268d2c` |
| 2 | `0x04` | BLACK OCP | `0x268d4a` |
| 3 | `0x08` | FFC Connection OCP | `0x268d68` |
| 4 | `0x10` | RT Protect | `0x268d86` |
| 5 | `0x20` | DSI Protection | `0x268da4` |
| 6 | `0x40` | AC_DET pin low | `0x268dc2` |
| 7 | `0x80` | PMIC fault | `0x268de0` |

For example, a fresh raw `0x10` decodes precisely as the literal bit-4 label
`RT Protect`; it does not establish what “RT” expands to. Bits above seven are
not given labels by this bounded QD decoder. The separate WOLED model branch
must not be substituted: matching historic logs identify the QD product path.

The word comes from `ave_tcon_get_err_det_status(int *)` at `0x25d164` through
the AVE ioctl (`0xc010749f`, operation `0x1f`) to QDF
`QDFTcon_GetErrDetStatus` at module `.text+0xa000`. QDF constructs TCON query
`00:00:00:00:00:00`, reverses the returned four-byte order, logs the raw word,
and only then can apply its optional debug-return override. Therefore a future
record must retain whether it is the ordinary raw log or an explicitly marked
debug override; the status is a query result, not a memory-mapped register
value proved by this analysis.

## Status word versus recovery input

The monitor does **not** decide whether to retry or reset from these status
bits. `ave_tcon_monitor_ddr_pmic_check_qd_oled()` starts at `0x2695fc` and
gets the separate one-bit ERR GPIO signal through
`ave_tcon_qd_err_detect_check()` (`0x268ffc`). That helper reduces the
registered GPIO-provider result to success or failure. On an asserted GPIO it
uses `ave_tcon_qd_err_detect_status()` for diagnostic logging, but the returned
status word is not used as the reset predicate.

The in-call GPIO behavior is exactly three consecutive asserted samples with
two `usleep(100000)` waits: status decode at `0x2696aa`, retry decision at
`0x2696b4`, sleep at `0x2696c4`, then GPIO recheck at `0x2696cc`. The third
assertion increments `err_det_reboot_try` (`AVE BSS 0x5bfc68`) at
`0x269812..0x269820`. A later monitor branch can call stock
`ave_tcon_qd_set_power_control(2)` at `0x269ae0` or `0x269b26`; operation two
is QDF's stock off-then-on implementation. This establishes vendor recovery
for a GPIO assertion, not a supported external reset API or evidence it ran at
the current menu blackout.

There are three different kinds of retained state, which must not be merged:

| item | scope/behavior |
| --- | --- |
| Fresh status word | TCON query response decoded for labels; no persistent AVE latch is written by the decoder itself. |
| `err_det_cnt` / `err_det_reboot_try` | AVE BSS monitor bookkeeping at `0x5bfc5c/+0x48`; the first counts asserted samples, the latter terminal retry cycles. |
| `qd_tcon_off` | AVE BSS history latch at `0x5bfc78`, set on terminal monitor handling after operation zero; it is not the fresh status word or a current TCON-off order. |

The terminal threshold condition is `err_det_reboot_try > 1` (with separate
VDD/ELVDD thresholds). At the terminal operation-zero path, the monitor stores
`qd_tcon_off=1` at `0x269786`. Later monitor invocations test that latch at
`0x269640..0x269644` and jump directly to the reporting/return route
`0x269b98`. That route does not call the GPIO checker, status decoder,
operation zero/two, mute, DPMS, or a TCON setter. Thus the currently sampled
history latch one explains why a later monitor tick is not a fresh status read;
it does not classify the original fault or prove a new power action.

## Ordinary stock recovery boundary

The source-proven recovery entry is the monitor's own asserted-GPIO branch;
there is no established public API that safely requests its operation-two
recovery. It would be unsafe to invoke the private AVE/QDF functions directly,
clear the latch, force a GPIO result, or bypass protection in an attempt to
make a fresh status word “recover.”

The owner-controllable ordinary path is instead the TV's normal user power
off/on or wake lifecycle, which has separately retained stock Deviced/QDF
DPMS/mute/power-on markers. That can be *observed* as an ordinary user action
without patching, factory writes, rail forcing, or protection bypass, but this
static ERR-DET analysis does not prove it re-arms the monitor latch or treats a
new error word. A meaningful future owner-observed comparison is therefore:

1. retain the normal stock lifecycle markers and a physical observation;
2. retain any fresh `ERR DET Status` line and whether its one-bit GPIO-fault
   precursor was asserted; and
3. compare the monitor counters/latch before and after only through a reviewed
   passive reader.

That distinguishes a fresh monitored ERR event from stale `QD_TCON_OFF=1`
reporting, while preserving all factory, rail, kernel, and protection state.
It still cannot prove that any decoded label caused the physical blackout.
