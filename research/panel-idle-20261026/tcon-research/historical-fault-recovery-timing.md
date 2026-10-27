# Historical ERR_DET recovery timing and latch boundary

Scope: offline analysis of the copied, exact `libave.so.0.1`, `qdf_tcon.ko`, and `tztv_frc_tcon.ko`. No TV command, setter, protection bypass, monitor suppression, or kernel export invocation was performed.

## Separate facts that must not be collapsed

The historical October 12 event contains an asserted ERR_DET GPIO and a TCON status response `0x10` (the QD label for its bit 4 is `RT Protect`). The present physical-black incident has **no aligned fresh ERR_DET transition**. The current `QD_TCON_OFF=1` messages are a monitor-history latch, not a current TCON-off instruction: the exact `qd_tcon_off` storage is `libave` BSS `0x005bfc78`, set by the terminal monitor path and subsequently only logged on later ticks.

Thus this note explains the old monitor recovery path only. It neither attributes a new blackout to RT Protect nor establishes what RT expands to electrically.

## The only exact short retry interval

`ave_tcon_monitor_ddr_pmic_check_qd_oled()` begins at Thumb link VA `0x002695fd` in `libave.so.0.1`. Its ERR_DET branch calls `ave_tcon_qd_err_detect_check()` at `0x00269666`; that helper reduces the raw fault GPIO to success/failure and does not use the TCON's returned status word for the recovery decision.

For an asserted fault, the monitor follows this bounded in-call loop:

```text
0x26967c  fault path / increment ERR_DET counter
0x2696aa  read and decode TCON status for logging
0x2696b4  compare local retry index with 2
0x2696bc  r0 = 0x186a0
0x2696c4  call usleep(r0)                 # 100,000 microseconds
0x2696c8  retry index++
0x2696cc  re-read raw ERR_DET GPIO
```

The retry index starts at zero. Therefore the terminal branch at `0x269812` is reached after **three consecutive asserted GPIO samples**, separated by **two explicit 100-ms sleeps** (roughly 200 ms plus GPIO/I/O/logging time). The code does not contain a three-second delay in this loop.

This is the only exact timing established here. The subsequently traced [outer monitor](monitor-task-cadence.md) uses a nominal one-second condition timed wait. Its actual execution cadence at the historical fault is not measured; multiplying inner retries by an assumed fixed outer tick rate would be invented. In particular, the owner's approximate three-second sparse-screen threshold does not fit any demonstrated host-side timeout in this historical ERR_DET branch.

## Recovery counter and operation-2 route

After the third asserted sample, `0x269812..0x269820` increments monitor state `+0x48` (`err_det_reboot_try`). This is distinct from the per-sample counter at `+0x3c` (`err_det_cnt`). The same function owns separate VDD and ELVDD counters at `+0x40/+0x44` and their reboot counters at `+0x4c/+0x50`; do not label those as ERR_DET counts.

The reset request appears at two monitor call sites:

| Callsite | Argument | Static condition boundary that is known |
|---|---:|---|
| `0x00269ae0` | `2` | A monitor fault branch after the counter/status processing. |
| `0x00269b26` | `2` | A later branch after another status decode at `0x00269b20`; it is the branch matching the retained historical second query followed by reset. |

Both call `ave_tcon_qd_set_power_control(int)` (`0x0025c2e1`; Thumb instruction stream starts `0x0025c2e0`). The wrapper sends AVE ioctl `0xc010749f` with operation command `0x29` and preserves the supplied operation value in its request payload. The corresponding exact kernel function is `QDFTcon_SetQdTconPowerControl` at `qdf_tcon.ko:0x11c48`:

```text
operation 2:
  0x11ce0  m_set_power_control(0)
  0x11cec  m_set_power_control(1)
  0x11cf0  OR the two return values and return
```

There is no delay instruction between those two calls in this wrapper. Any physical settle time comes from the called power-control implementation or downstream hardware and has not been derived here. It would be unsafe to treat operation 2 as a user-callable refresh or to emulate it externally.

## Terminal latch is not a repeated recovery loop

The monitor's terminal classification path starts at `0x00269746` when any recovery threshold is exceeded (`state +0x48 > 1`, `state +0x4c > 3`, or `state +0x50 > 3`; the third comparison is at0x269ae6..269aea). It calls power control with operation `0` at `0x0026977a`, then stores `1` in `qd_tcon_off` at `0x00269786`.

On later calls, `0x00269640..0x00269644` sees `qd_tcon_off == 1` and jumps directly to the reporting path at `0x00269b98`; that path logs and returns. It does not call operation 0, operation 2, QDF mute, DPMS, or a TCON register setter. A `QD_TCON_OFF` history line therefore cannot be used as timing evidence for a new power control action.

## What remains unknown

* The exact source-level condition selecting the two operation-2 branches is not fully named by the stripped/proprietary surrounding state machine; the addresses and argument are established, but no semantic label should be invented.
* The outer monitor has a configured one-second timed wait as documented separately; actual historical/onset cadence remains unmeasured, so there is no proven three-second host timer.
* `RT Protect` is only the literal bit-4 label in the QD error decoder. No expansion, electrical threshold, panel subassembly diagnosis, or causal relation to the current black state follows.
* The historical reset route shows vendor fault handling for a GPIO assertion. It does not establish that suppressing/resetting the monitor would preserve output, and it must not be bypassed.

The appropriate discriminator for any future event remains an aligned, passive record of raw ERR_DET/fault logs and the stock power-control markers. Without that, a current black state must not be classified as this historical recovery branch merely because `QD_TCON_OFF` is still logged.
