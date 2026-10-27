# RT Protect (`0x10`) and host recovery boundary

## Scope

This is an offline analysis of the accepted, retained status query and copied
firmware.  It does **not** issue a power, mute, GPIO, monitor, reset, TCON, or
network action.  In particular, it does not turn off protection, clear the
AVE monitor latch, or call a private recovery function.

Inputs used here are the accepted record
[`../overnight/tcon-status-actual-result-20261026.md`](../overnight/tcon-status-actual-result-20261026.md),
`libave.so.0.1` SHA-256
`a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777`, and
`qdf_tcon.ko` SHA-256
`97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63`.
AVE addresses below are static ELF virtual addresses; QDF addresses are
module-section offsets.  Neither is a live address.

## What the accepted `0x10` proves

The reviewed, one-shot ARM32 operation-31 query completed with output changing
from its sentinel to `0x00000010`, ioctl return zero, and this matching QDF
kernel line:

```text
[75262.252253] [TCON:QDF] QDFTcon_GetErrDetStatus[3216:TconStatusRead.]: ERR DET Status:0x10
```

The PID and timestamp match the query.  `QDFTcon_GetErrDetStatus` logs its raw
`F3 80 00 00 00 08` result before an optional debug override, so this is
positive evidence of that raw word at that time, not merely a client-side
buffer value.  The exact QD decoder maps bit 4 (`0x10`) to the literal string
**RT Protect** at AVE `0x268d86`.

That is deliberately the full semantic conclusion.  It does not expand “RT,”
prove a particular rail, temperature, panel component, or physical-black
instant, or establish whether the controller's status query is live, latched,
or read-to-clear.  There was no simultaneously retained I2C trace.  The direct
query did not invoke the AVE monitor, and the status word is not the monitor's
fault input.

## Status bit versus the host monitor's recovery predicate

The QD monitor is `ave_tcon_monitor_ddr_pmic_check_qd_oled` at AVE
`0x2695fc`.  Its ERR path first calls the distinct
`ave_tcon_qd_err_detect_check` at `0x268ffc`, which in turn uses
`ave_tcon_get_err_det_fault` at `0x25d01c` (AVOC/TCON ioctl operation `0x1d`).
Only a nonnegative getter result with a nonzero returned ERR GPIO output is a
counted monitor fault.  A negative getter return is converted to zero by the
AVE checker before the predicate.  The monitor obtains/decodes the status word
only as diagnostics after that GPIO fault branch has already been selected.
The decoder's returned word is not the retry or reset condition.

The lower QDF ERR getter itself has an important power gate.  If its cached
`m_tcon_power_state` is zero, it returns a zero output without asking the GPIO
provider.  If powered, the copied provider requests the DT `err_det` GPIO,
sets its direction to input, reads the raw value, stores that value through the
caller output, and frees it.  Consequently, a new direct ERR-GPIO query is
not a passive memory read: it may acquire and reconfigure GPIO ownership.  It
would bypass the AVE history-latch branch, but cannot establish an electrical
sample if QDF's cached power gate is off, and it is not an ordinary public UI
recovery operation.

| Evidence item | Exact role | What it does **not** show |
| --- | --- | --- |
| status `0x10` | raw TCON diagnostic label `RT Protect` | asserted ERR GPIO, a monitor retry, or a reset request |
| ERR operation `0x1d` output | current QDF/provider-side GPIO result, subject to QDF power gate and provider errors | a passive/no-side-effect test, or panel emission |
| `err_det_reboot_try` | AVE retry-cycle bookkeeping | raw status-word value or present electrical fault |
| `qd_tcon_off` | terminal AVE history latch | a current instruction powering the TCON off |

## Exact monitor recovery and its skip boundaries

For an asserted ERR GPIO, the monitor performs three consecutive samples with
two explicit 100-ms sleeps.  It logs/decodes the status at `0x2696aa`; it does
not branch on the decoded bit value.  The third asserted sample increments
`err_det_reboot_try` (`state +0x48`) at `0x269812..0x269820`.  On the recovered
fault branches, calls at `0x269ae0` and `0x269b26` invoke the stock private
wrapper `ave_tcon_qd_set_power_control(2)`.  QDF operation 2 is its internal
off-then-on wrapper: it calls lower power control with zero then one.  This is
the exact host-side recovery sequence, but it is a monitor-private protection
path, not a user-callable reset API.

Two early monitor conditions matter more than a new diagnostic status word:

1. If `g_tcon_monitor_restart == 1`, `0x269a54..0x269a88` coherently clears
   monitor bookkeeping (`state +0x3c` through `+0x5c`) and the restart flag,
   then rejoins ordinary monitor entry.  It sends no QDF power, mute, DPMS,
   or TCON command.  The needed start/restart request is only known as an
   in-process AVE API; no owner-facing/public binding is established.
2. If `qd_tcon_off == 1`, the test at `0x269640..0x269644` jumps directly to
   reporting/return at `0x269b98`.  It skips the ERR GPIO getter, status
   decoder, operation 0, operation 2, mute, and all TCON setters.  The current
   passive monitor tuple has this latch set, so a later monitor log does not
   constitute a fresh status or GPIO sample.

At the terminal retry threshold, the monitor instead calls operation zero at
`0x26977a` and sets `qd_tcon_off=1` at `0x269786`.  This explains a historical
latch; it is not a continuing off loop.  Clearing either latch/counter by
memory write, forcing GPIO output, or calling operation 2 directly would evade
the host's ownership and protection sequencing and is not an acceptable
recovery experiment.

## What stock normal lifecycles can reapply

There are two separate, ordinary stock behaviors worth distinguishing:

* A normal owner-controlled power-off/on or wake lifecycle has retained
  Deviced/QDF evidence for `QDFTcon_SetQdTconPowerControl(On)`,
  `m_check_tcon_status(2)`, `m_tcon_recovery_frame_mode`,
  `QDFTcon_Resume`, and TCON mute release.  The QDF on path first samples the
  ERR GPIO.  If that sample is nonzero, QDF sets cached power/PVCC and returns
  **without** its normal status-check/frame-recovery tail.  If zero (or a
  provider failure leaves the sample zero), it runs the normal tail.  This is
  a stock lifecycle, not a documented on-demand recovery interface.
* Public `SetPanelMute(0)` is only an output-gate request.  On its QD route it
  can query/re-send `F3:0x164=0`, but PVCC/cache/transport guards can suppress
  a wire transfer while returning success.  It does not write the monitor
  latch/retry fields, call the ERR status decoder, or request QDF operation 2.
  Therefore it cannot be represented as an RT-Protect reset or latch rearm.

The frame-mode helper sometimes reached during normal Resume is also distinct:
it reads `F3:0x160` and, only on a read failure or cached-mode mismatch, makes
a temporary mute/frame-mode/unmute bracket.  It has no status-bit-4 dispatch.
Likewise, the QDF status query that produced `0x10` does not call that helper.

## Bounded recovery assessment

No public, owner-facing action is statically proven to mean “recover RT
Protect,” to clear `qd_tcon_off`, or to guarantee that a black panel returns.
The only supported, bounded **normal** candidates are:

1. an owner-initiated ordinary power/wake lifecycle, observed rather than
   injected, with its stock QDF/Deviced logs retained; and
2. a separately reviewed single public `SetPanelMute(0)` request only when
   owner-observed physical state and Screen Optimization status are freshly
   recorded.  One such request is already retained, so automatic repetition is
   not justified.

Neither candidate should be promoted to a fix.  In particular, a normal wake
can reapply standard QDF initialization, but no recovered edge proves it
restarts the AVE monitor, clears its history latch, or succeeds when the ERR
GPIO remains nonzero.  The next useful discriminator is a fresh, separately
authorized ERR-GPIO observation with full ioctl return/output provenance; it
should not be treated as harmless because its stock provider requests and
changes the GPIO direction.  Before any owner action, retain the monitor
tuple, QDF cached power state, normal-lifecycle markers, and an owner-timed
physical-black/audio observation.  Do not infer physical recovery from cache
zeros/ones or an accepted API return.

## Relationship to controller-side analysis

This report deliberately stops at the host monitor and normal QDF lifecycle.
It makes no claim about the controller's internal RT-protection mechanism,
whether the status is latched, or the electrical condition behind `0x10`.
Those are controller-side questions and must not be inferred from matching
names or proximity in the logs.
