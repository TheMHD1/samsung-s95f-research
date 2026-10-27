# QD monitor / QDF function-logging plan — bounded offline design

## Decision

There is **no currently validated way to attach function-entry/return probes**
to either the AVE QD monitor or `qdf_tcon.ko` on this build.  The retained
runtime-observability inventory establishes `nop` as the only tracer and no
available function/function-graph tracer, kprobe events, uprobes, kallsyms, or
kernel config endpoint.  A proposed kernel patch, replacement module,
eBPF program, ptrace breakpoint, or direct controller logger is therefore not
a ready diagnostic mechanism.

The safe, reversible plan is instead an **isolated static-trace window plus
start/end kernel-log snapshots**, correlated with already-decoded wire
traffic and owner-timed physical observations.  It can establish whether a
stock QDF/rail/GPIO/HDMI path coincides with onset.  It cannot directly prove
that any named function ran, nor whether pixels emitted light.

This is a design document only.  It performs no TV/root/network action.

## Exact code questions and useful evidence fields

| Question | Static source anchor | Evidence needed during a future naturally occurring event | Interpretation limit |
| --- | --- | --- | --- |
| Did the AVE QD monitor select its ERR path rather than merely report an old latch? | `libave.so.0.1` SHA `a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777`; `ave_tcon_monitor_ddr_pmic_check_qd_oled` Thumb `0x2695fc`; stale-latch test `0x269640..0x269644` | A pre/post, identity-guarded AVE monitor tuple: retry counters `+0x48/+0x4c/+0x50`, `qd_tcon_off +0x58`, and restart state, plus relevant stock log rows. | `qd_tcon_off=1` is history, not a contemporaneous power-off.  The visible-Apps control already had it set. |
| Was fresh ERR GPIO input involved? | AVE getter `ave_tcon_get_err_det_fault` `0x25d01c`; QD helper `0x268ffc`; QDF provider `_tztv_frc_tcon_read_err_det_status` `.text+0x1af0` in `tztv_frc_tcon.ko` SHA `aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd` | Generic GPIO trace rows, provider/kernel error messages, and an independently authorized single current pin observation only if separately reviewed. | The provider requests the line and sets direction input; a direct read is not passive.  Trace absence cannot prove no GPIO path ran. |
| Was the controller status word read, and what did it say before debug override? | QDF `QDFTcon_GetErrDetStatus` `.text+0xa000` in `qdf_tcon.ko` SHA `97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63`; fixed query `F3 80 00 00 00 08` | Filtered I²C request/reply/result sequence and matching kernel line `QDFTcon_GetErrDetStatus ... ERR DET Status:0x...`. | The getter can be stateful at the controller boundary; no repeated query is justified merely for logging.  `0x10` is only the host label “RT Protect.” |
| Did host monitor recovery request QDF operation 0 or 2? | AVE operation-2 callsites `0x269ae0`, `0x269b26`; terminal operation-0 `0x26977a`; wrapper `ave_tcon_qd_set_power_control` `0x25c2e0` | Static I²C/GPIO/regulator/clock evidence and QDF/`frc-tcon` logs around a natural transition. | There is no function tracepoint for the operation argument.  Wire/lower-callback correlation is not a proof of the AVE caller. |
| Did actual QDF power lifecycle execute and which branch did it take? | QDF `m_set_power_control` `.text+0x11848`; on ERR branch `0x11994`; ordinary on tail `0x1192c..0x11938`; off entry `0x11a28` | GPIO, regulator, clock events; lower-driver `frc-tcon` messages; I²C recovery/status/mute traffic; start/end log snapshots. | Its cached `m_tcon_power_state`, `m_tcon_state`, and PVCC words are not safe physical-panel indicators and are not currently exposed as passive fields. |
| Did an adjacent HDMI runtime-PM path occur? | `tztv_hdmi_switch_api.ko` SHA `c586a2601665a778a1e7401cd6b7553e03684f2e4536a282047b17059b7eec97`; stock `trace_early_message` paths documented in `hdmi-private-power-log-markers.md` | Private-instance `early_trace:early_event` rows with the exact `[HDMISW]` IN/OUT strings, paired PM tracepoint rows. | These markers cover only that caller and omit callback status; their absence excludes neither other HDMI paths nor panel-side events. |

## Available observability and hard limits

The accepted inventory in `overnight/diagnosis-20261026.md` and
`overnight/kernel-observability.json` establishes the following for the
current paired kernel lineage:

* **Available static events:** I²C write/read/reply/result, DRM vblank,
  `early_trace:early_event`, GPIO, clock, regulator, sched exec/exit, and raw
  syscalls.  Existing private trace instances have already recorded these
  without sending a panel command.
* **Unavailable for this plan:** function and function-graph tracers,
  `kprobe_events`, `uprobe_events`, `/proc/kallsyms`, and `/proc/config.gz`.
  There is no source-backed runtime address for a QDF/AVE function probe.
* **Existing stock log channel:** `QDFTcon_GetErrDetStatus` emits the raw
  status-word line before optional debug substitution.  `tztv_frc_tcon.ko`
  includes ERR-GPIO/power error strings.  Preserve the kernel/vlog rows rather
  than assuming every function logs.
* **Not a substitute:** `/sys/kernel/debug/tcon/tcon_micom_log` is a
  read-only internal-TCON shared-memory log.  It is not bound to the external
  QDF controller, its RT state, or the QD image's UART ring.

## Proposed passive capture envelope

Use the already reviewed onset-capture architecture, not a new tracer.  A
future revision must remain a dry-run-default, owner-triggered, finite capture
with a unique private trace instance and a target-side expiry/cleanup guard.
It must never enable global tracing, clear dmesg, create kprobes/uprobes,
open a controller/TTY endpoint, issue an ioctl, or synthesize I²C traffic.

### Window and ordering

1. Record a pre-window owner annotation with an uncertainty bound: visible or
   black, audio state, source/app, overlay/full-screen state, and whether a
   Screen Optimization cycle is active.  Software state is not a physical
   label.
2. Validate boot ID, exact AVOC/deviced process identity/start-times, copied
   binary hashes, and the expected trace-event formats before arming.
3. Snapshot the retained kernel ring into the capture artifact **before**
   arming; preserve boot ID and uptime around that snapshot.  This is
   non-clearing (`dmesg`, not `dmesg -c/-C`).
4. Enable only the existing static-event set in a private instance, with I²C
   filtering constrained to the known QDF adapter-5/address-`0x76` path.  Keep
   full I²C payload/result syntax so `F3:0x08`, mute, frame-mode, and status
   families can be decoded offline.
5. During a naturally occurring content/UI transition, retain DRM vblank,
   GPIO, clock, regulator, early-event, and PM/static events alongside the
   I²C stream.  No state query is injected at the presumed onset.
6. Stop after the fixed expiry; drain/export the trace; remove the private
   instance; then take a second non-clearing kernel-ring snapshot immediately
   before lengthy vlog transfer.  Both compressed snapshots require base64,
   gzip CRC, nonempty, boot/uptime, and explicit coverage validation offline.
7. Record a post-window owner annotation with the same timing/uncertainty
   requirements.  Reject a record with changed boot/process identity, trace
   loss, malformed transport, failed cleanup, or insufficient physical
   annotation rather than filling gaps from later logs.

### Minimum retained fields

| Layer | Retain | Reason |
| --- | --- | --- |
| Trace framing | private-instance config, monotonic markers, CPU/ring loss counters, window bounds, cleanup result | distinguishes a complete bounded record from a partial one |
| QDF transport | timestamp, task/TGID, direction, result, full bytes for each filtered transaction | distinguishes status query, mute, frame, power-adjacent handshake, and unknown traffic without issuing any |
| Kernel logs | raw start/end snapshot bytes plus parsed QDF/`frc-tcon`/HDMI rows and uptime bounds | preserves messages which static tracepoints do not contain |
| Host output side | DRM vblank, clock/regulator/GPIO events, HDMI early events | can exclude or identify a visible host-side transition; does not measure OLED emission |
| AVE userspace bookkeeping | only the existing identity-guarded sampled monitor tuple if the observer is separately reviewed for the exact new build | distinguishes a stale history latch from a counter change; values are race-prone snapshots, not atomic state |
| Human observation | owner physical annotation and reaction/clock uncertainty | only source for “picture was visibly black/visible” |

## Interpretation rules

* **Strongest host-side sequence:** a fresh nonzero ERR GPIO sample, then the
  status query/log, then QDF lower rail/reset evidence and operation-related
  transport, all inside an owner-bounded onset interval.  Even that would
  show correlation and stock host response—not controller cause or repair.
* **Status only:** a raw `0x10` row without the GPIO/recovery sequence shows
  only the controller status label at that time; it must not be promoted to a
  shutdown command or a crack diagnosis.
* **No host transition:** continuous vblank/composition plus no QDF/rail/mute
  delta confines the observation to the captured host surfaces.  It supports,
  but cannot prove, a controller/panel-internal response because the trace
  does not instrument OLED emission or all proprietary hardware paths.
* **Historical latch alone:** `QD_TCON_OFF=1` reports are explicitly excluded
  as fresh-transition timing evidence.

## Deliberately excluded approaches

| Approach | Why it is not ready/safe |
| --- | --- |
| Kernel source/module patch to print function arguments | Requires a matching build/config/signing/load path and changes kernel code; no source-to-running-text identity or rollback validation is present. |
| Dynamic kprobe/fprobe/eBPF function attachment | The retained target inventory lacks required tracer/probe surfaces and symbols.  A guessed address/module offset is unsafe under relocation and module lifetime. |
| AVE uprobe/ptrace/GDB hook | No uprobe surface is retained; ptrace changes timing/stops the compositor process and is not a passive monitor. |
| Direct QDF status or ERR-GPIO polling | The status getter can send controller I²C; the GPIO getter requests/reconfigures input direction.  Repeated logging polls would become interventions. |
| QD UART/USB console opening | Neither has a proven host binding; opening can affect session/DTR/runtime-PM state. |
| Writing monitor latches/counters or calling operation 2 | Those evade protection/recovery sequencing and are not logging. |

## What remains missing before function-level instrumentation

1. A live, build-matched export/symbol or debug surface that supports
   function attachment without patching code.
2. A source-backed ABI for return/argument capture at `m_set_power_control`,
   QDF status read, and the AVE monitor, including the actual loaded module
   bases and lifetime safeguards.
3. A tested rollback that restores every tracing/probe setting after timeout
   even if the collector fails.
4. A clear assertion that added logging is acceptable on the live faulted
   panel; this must include its timing/performance effect, not merely code
   correctness.

Until those facts exist, static events plus stock logs are the actionable,
reversible diagnostic tier.  They should be used only for an owner-authorized
natural transition, never as a recovery mechanism or protection bypass.
