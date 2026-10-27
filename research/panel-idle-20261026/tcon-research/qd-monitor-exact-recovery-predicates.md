# QD monitor: exact recovery predicates

## Scope

Offline static review of `binaries/libave.so.0.1`, SHA-256
`a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777`.
The reviewed function is the complete 1,928-byte Thumb body of
`ave_tcon_monitor_ddr_pmic_check_qd_oled` at `0x2695fc`. No TV operation,
memory write, protection change, or network action occurred.

This closes the earlier narrow gap around operation-two sites. It does not
make those private monitor branches a recovery procedure. A previous
visible-Apps control already had `qd_tcon_off=1`; that stale latch cannot by
itself explain a later physical panel-off event.

## Entry paths that cannot issue a new power action

| Predicate / range | Destination | Consequence |
| --- | --- | --- |
| Opaque local-global word at `r5+8` is `-1`, `0x269622..0x269628` | `0x269a14` | QD fault branches below do not run. Its semantic name is unresolved. |
| `g_tcon_monitor_restart==1`, `0x269630..0x269636` | `0x269a54` | Clears monitor bookkeeping, then rejoins entry; no power/mute/DPMS/TCON call in the clear block. |
| `qd_tcon_off==1`, `0x269640..0x269644` | `0x269b98` | Report/return; skips GPIO, status decode, operation zero and both operation-two sites. |
| `si_ok_count>9`, `0x269648..0x26964c` | `0x269994` | Clears selected counters and sets `onetime_execution=1`; does not clear `qd_tcon_off`. |
| incremented `ip_status_count==10`, `0x269656..0x26965e` | `0x269b2c` | Clears only that count, calls an auxiliary routine, and rejoins. |

The restart block `0x269a54..0x269a88` clears QD state through `+0x58`,
including all three retry counters and `qd_tcon_off`, then clears the restart
global at `0x269a7a`. It leaves `ip_status_count` outside that range. This is
bookkeeping reinitialization, not a display recovery transaction.

## ERR sample and retry predicate

`ave_tcon_qd_err_detect_check` returns at `0x269666`; its value is held in
`r4`. Nonzero enters `0x26967c`, while zero enters `0x2696d6`. This predicate
is separate from the decoded TCON status word: bit4 `RT Protect` neither
selects the loop nor changes its thresholds.

For a nonzero ERR predicate, the exact sequence is:

```text
26967c..26968e  err_det_cnt++
2696aa           status decoder/log only
2696b4           local retry index == 2?
2696bc..2696c4  usleep(100000)
2696c8           retry index++
2696cc           recheck ERR predicate
269812..269820  third consecutive nonzero: err_det_reboot_try++
```

Thus it has three consecutive samples and two explicit 100-ms waits.

## Operation-zero predicate

The terminal action at `0x269746` requires that the common classification
path reach one of these strict comparisons:

| Field | Comparison | Branch |
| --- | --- | --- |
| `err_det_reboot_try` (`state+0x48`) | `>1` | `0x269738..0x269746` |
| `vdd_det_reboot_try` (`state+0x4c`) | `>3` | `0x26973e..0x269742` |
| `elvdd_i2c_reboot_try` (`state+0x50`) | `>3` | `0x269ae6..0x269aea` |

It passes zero to `ave_tcon_qd_set_power_control` at `0x269778..0x26977a`,
then stores `qd_tcon_off=1` at `0x269786`. Later calls take the stale-latch
return rather than repeat operation zero.

## Operation-two predicates

| Site | Exact static predecessor | Result boundary |
| --- | --- | --- |
| `0x269ae0` | The no-current-ERR side enters at `0x2696d6`. The PIC base at `0x2696da` resolves to monitor state `0x5bfc20`; `ldr [base,#0x48]` / `cmp #1` at `0x2696dc..0x2696e0` requires **`err_det_reboot_try == 1`** and branches to `0x269ab8..0x269ade`, which passes literal `2`. | Returns to `0x2696e4` for common bookkeeping. It is not status-bit selected. |
| `0x269b26` | The current-ERR result must be nonzero at `0x26971e..0x269720`, so execution continues to `0x269724`. The PIC literal then resolves `0x5ad9f0`; the load at `0x26972a` is the named local `isProductionMode` at `0x5ad9f8`. It must be **not equal to 1** (`0x26972c..0x26972e`), otherwise it diverts to `0x269bc0`. None of the terminal retry comparisons may select operation zero. It then decodes/logs status at `0x269b20` and passes literal `2`. | Branches to `0x269788`, after the operation-zero/latch store. This path does not set the latch. |

The useful distinction is now exact: a fresh current ERR below terminal
retry thresholds and with `isProductionMode != 1` can take operation two at
`0x269b26`; a terminal retry takes operation zero and latches instead. A
separate no-current-ERR condition, exactly `err_det_reboot_try == 1`, reaches
`0x269ae0`. Neither is reachable through the entry latch.

`onetime_execution` (`state+0x5c`) gates entry to the ordinary common path at
`0x26970a..0x26971e`. The QD model/production conditional is the named local
`isProductionMode` at `0x5ad9f8`; equality with one diverts at
`0x269724..0x26972e` away from both operation-two sites. The function itself has no mutex
acquisition instruction. A normal wake is not statically proven to run this
function, meet its conditions, or clear the latch.

## Interpretation limit

The finite signatures are now: three 100-ms-spaced ERR samples and retry
increment, an operation-two call, or a terminal threshold followed by
operation zero and latch store. Do not infer any one from a stale latch or a
raw GPIO-high sample alone. This analysis supports no latch/counter write,
protection bypass, direct operation-two call, or automatic recovery action.
