# Fresh `0x10` TCON status: host interpretation and controller boundary

## Result

The accepted one-shot read returned the exact 32-bit word `0x00000010`.
In the matching QD AVE decoder, bit 4 has the literal vendor label **RT
Protect**.  That is the complete supported interpretation.  Neither the
copied host code nor the retained controller startup text expands “RT”, names
an electrical threshold, identifies a damaged part, or proves why the owner
saw a black picture.  No such expansion is made here.

The fresh result is stronger than an unchanged output buffer: the reviewed
helper's sentinel `0xa55a5aa5` changed to `0x00000010`, ioctl
`0xc010749f`/operation `0x1f` returned zero, and the separately retained kernel
buffer contains the same QDF raw-status line with the same helper PID and
time:

```text
[75262.252253] [TCON:QDF] QDFTcon_GetErrDetStatus[3216:TconStatusRead.]: ERR DET Status:0x10
```

QDF emits that line before its optional debug-return override.  No
`ERR DET Status Debug` row was retained by the bounded filter.  This supports
an ordinary QDF raw response for this call; it does not prove whether the
controller value was live, latched, or consumed by reading it.  Attempt `b`
may already have issued a query and remains explicitly unresolved, so this
must not be called the first read.

This is offline analysis only.  It issued no new query, GPIO read, setter,
reset, power operation, protection change, root command, TV command, or
network request.

## Pinned inputs

| Input | SHA-256 |
| --- | --- |
| `binaries/libave.so.0.1` | `a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777` |
| `binaries/qdf_tcon.ko` | `97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63` |
| `binaries/tztv_frc_tcon.ko` | `aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd` |
| `binaries/tztv_frc_tcon_api.ko` | `3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6` |
| `binaries/libdisplay-panel-impl-sec.so.0.1` | `40df6d6e83da608e47d0143c268a964d97fddc7010972b5842f0e21f9b058ca4` |
| accepted `result-20261026c.json` | `5ccac8a789fd83b3b276b39e6bf33201087c8e4354d580f7bb316075ed04bea6` |
| filtered dmesg bytes | `d454a04995c5298f31693260f1243e7dcb4f5cf8335312e798b3e99e27b7e9f9` |
| retained controller-startup prefix | `39b72938ffc5aec8238417fce72cdd131864040dea137a1cbbc5e3191116e846` |

The accepted execution and its limits are recorded in
`overnight/tcon-status-actual-result-20261026.md` (SHA-256
`4e1f9049d248e6e35e16ba2538e440ec29187fbff3e60b148d910b1d319670af`).
Selected instruction evidence is preserved in
`rt-protect-controller-path.disasm`; ELF addresses below are link-time VAs or
module `.text` offsets, not live addresses.

## Exact read and decode chain

The supported chain is:

```text
ave_tcon_get_err_det_status(int *)             libave 0x25d164
  -> ioctl 0xc010749f, operation 0x1f
  -> QDFTcon_GetErrDetStatus                   qdf_tcon .text+0xa000
     -> m_read_cmd(0xf38000000008, output)
     -> log raw output word                    .text+0xa05c..0xa074
     -> optional debug override only if
        m_err_debug (BSS+0x28) == 1            .text+0xa078..0xa0fc

ave_tcon_qd_err_detect_status()                libave 0x268cbc
  -> tests bits 0..7 independently
  -> bit 4 extraction at 0x268d86
  -> literal string at file/link string VA 0x567dbc:
     "ERR Detect Status RT Protect:%d"
  -> returns the unmodified word
```

The command is a proprietary controller transaction, not a proved
memory-mapped register read.  QDF's helper receives four bytes, reverses their
order, and returns the 32-bit word through the 16-byte ioctl structure.  The
driver's raw log precedes the optional debug overwrite, which is why the
matching `0x10` dmesg row materially corroborates the helper output.

## Bounded host reader/writer inventory

“All” here means the copied exact-build host objects and the recovered direct
call forms.  It does not include unrecovered controller firmware, an external
library, indirect calls through unknown pointers, corruption, or a different
build.

### Readers and consumers

* `ave_api_qd_tcon_error_status` (`0x28f440`, exported) calls the same ordinary
  getter at `0x28f4a4`.  It is a diagnostic read boundary, not a recovery
  action.
* The QD decoder calls the getter at `0x268cea`; its second model branch calls
  it at `0x268e44`.  Only the QD bit labels are applied to this owner's QD
  product.  The separate WOLED interpretation is not substituted.
* The QD monitor calls the decoder for logging at `0x2696aa`, `0x26990e`, and
  `0x269b20`.  These calls do not use bit 4 as the retry/reset predicate.
* A complete direct-call census also finds WOLED-monitor status calls.  They
  are model-specific and are excluded from the QD-policy conclusion.

### Values that can be written into the returned host word

* A successful QDF `m_read_cmd` response writes the four-byte controller
  result.
* If QDF BSS `m_err_debug` at `+0x28` equals one, QDF overwrites the result with
  the debug word at BSS `+0x120`, after logging the raw word.  No debug setting
  was changed, and the retained row is the raw form.
* The ioctl API copies the 16-byte structure back to ARM32 userspace.  The AVE
  decoder itself does not store this status into a persistent fault latch; it
  logs bit labels and returns the word.

No host-side writer that clears controller bit 4 was found.  A second query
might clear or consume a proprietary controller latch, but the copied host
code does not establish that semantic.  Therefore another read is not a safe
or necessary “clear” operation and is not recommended by this report.

## Status word is not the monitor's recovery predicate

The automatic QD monitor at `0x2695fc` makes recovery decisions from the
separate one-bit ERR_DET GPIO through `ave_tcon_qd_err_detect_check()` at
`0x268ffc`.  On an asserted GPIO it reads the controller word to label/log the
fault.  The `0x10` bit itself does not select the recovery branch.

The recovered stock sequence is:

1. Sample the ERR_DET GPIO three times with two explicit 100-ms sleeps.
2. After the third consecutive assertion, increment `err_det_reboot_try`
   (AVE BSS `0x5bfc68`).
3. Fault-state branches can call `ave_tcon_qd_set_power_control(2)` at
   `0x269ae0` or `0x269b26`.  QDF implements operation 2 as off followed by on;
   the lower function changes real GPIO/reset/rail-facing callbacks and is not
   a passive or generally safe command.
4. When a terminal retry threshold is exceeded, the monitor calls operation 0
   at `0x26977a`, then sets the userspace history latch `qd_tcon_off=1` at
   `0x269786`/BSS `0x5bfc78`.
5. Later monitor ticks seeing that latch take the report-and-return path.  They
   do not repeat the status query or power action.

The latch is host bookkeeping, not controller bit 4 and not a current power
order.  The accepted fresh `0x10` alone does not show that the ERR_DET GPIO was
asserted, that the monitor ran this sequence, or that this sequence caused the
owner's black picture.

## Ordinary stock entry boundaries

Two different ordinary boundaries exist and must not be conflated.

First, the AVE monitor is the source-backed automatic fault-recovery entry.
Its asserted-GPIO path owns operation 2 and its terminal operation-0/latch
path.  Normal AVE monitor start/Instant-On lifecycle calls can request a later
bookkeeping reset (`g_tcon_monitor_restart=1`); the monitor then clears its
counters and `qd_tcon_off`.  That reset does **not** clear the controller's
bit-4 source and does not itself command panel power or light.

Second, the normal display-panel backend exposes a non-factory control
boundary:

```text
displaypanel_impl_set_tcon_power(mode)             0x81fc
  -> DisplayPanelImplSec::setTconPower(mode)       0x5ab0
  -> PLT 0x4780 / GOT 0x1b0e8
  -> ave_api_set_qd_tcon_power_control(mode)
  -> ave_tcon_qd_set_power_control(mode)
```

`DisplayPanelImplSec::setTconPower` preserves its input mode and tail-forwards
it.  This proves a stock product interface reaches the hardware-affecting AVE
power-control family.  It does **not** prove which enum value is a safe user
recovery, that an ordinary UI invokes mode 2, or that this interface ran during
the incident.  The separate complete `DisplayPanelImplSec::setPower(bool)`
body is an ioctl-heavy whole-panel lifecycle and contains no direct call to
`setTconPower` or `ave_api_set_qd_tcon_power_control`; its name cannot be used
to bridge that missing call.

Consequently, the only source-backed automatic recovery for this fault class
is the existing monitor's GPIO-driven policy.  The display-panel export is a
control boundary, not a recommended experiment.  Directly invoking it,
operation 2, operation 0, monitor rearm, GPIO forcing, or a protection bypass
would change hardware state and is outside this analysis.

## Controller-firmware boundary

The retained startup prefix names controller firmware
`RHEA_M_TCON_FW_20250103_1715`, reports a 2048-KiB SPI flash and image/board
metadata, but it is log text, not the firmware payload.  The exact acquisition
map (SHA-256
`16ae2b40324ab25cd1ebb15c8da8bf81e0d8b54193b8b769117203155c512354`)
records that the matching F77 controller payload was not recovered.  No
already-copied object defines the MCU's bit-4 producer, threshold, persistence,
clear condition, or recovery success criterion.

An external report for a different firmware build does not supply this
missing exact-build meaning and, in any case, does not define RT Protect.  No
large firmware download or decryption was performed.

## What the positive result does and does not establish

It establishes that the matching host stack received and raw-logged a word
whose QD decoder labels bit 4 `RT Protect` during the accepted call.  It does
not establish:

* what “RT” expands to or which component/threshold asserted it;
* whether the controller value is current, latched, sticky, or read-to-clear;
* the simultaneous state of the separate ERR_DET GPIO;
* that the host monitor attempted, completed, or succeeded at recovery;
* that the owner-visible black picture was caused by this bit; or
* that any stock power-control entry is safe to invoke as a remedy.

The smallest useful next discriminator is passive, aligned evidence of the
separate ERR_DET GPIO/monitor path and ordinary lifecycle markers during an
owner-observed event.  A further status query, setter, reset, latch clear, or
protection change is neither required nor authorized by this report.
