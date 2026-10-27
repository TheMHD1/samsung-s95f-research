# QD command-skip lifecycle

This is an offline static reconstruction of the copied `qdf_tcon.ko` only.
The module SHA-256 is
`97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63`.
No TV command, trace, setter, GPIO, power control, or network action was used.
Offsets are `.text` / `.init.text` ELF offsets, not live addresses.

## Result

`m_command_skip` is the four-byte BSS object at `+0x10c`. When it equals1:

* `m_send_cmd_with_lock` logs `qd command skip` at `0xc140..0xc16c` and
  returns0 without I2C. Its check occurs at `0xbbf8..0xbc00`, before mutex
  acquisition. This is the helper used for normal QD writes including mute and
  frame-mode commands.
* `m_read_cmd` returns0 without the read transaction for every command except
  exact `0xf3800000000c`. The check is `0x9bb8..0x9bcc`, and skip/log/return
  path is `0x9dd8..0x9e10`.
* `m_read_cmd_no_lock` also checks this flag at `0xb8c8..0xb8d0` and
  returns0 via `0xb9e8..0xba24` without a transaction for **every** command.
  It does not share locking-read's exact0x0c exemption.
* `m_ew_send_cmd` likewise returns0 at its skip path (`0x69d8..0x69e0` →
  `0x6d3c`), before its normal transaction.

These skipped read paths do not write caller output. A later value comes from caller initialization or stale storage, not a fresh response.

Thus a return0 during an active skip window is not I2C emission, controller
acceptance, panel state, or visible light. The read exemption is a precise
protocol exception, not a general health check. Its vendor meaning has not been
recovered.

The transport's PVCC-zero mute special case is separate and earlier in the
write helper: it applies only to zero `F3:0164` payload under its own cached
flag. Command skip can suppress either mute payload and other writes.

## Explicit writes in this module

The finite instruction scan found these direct stores to the BSS word:

| Writer | Value and branch | What is established |
| --- | --- | --- |
| `QDFTcon_InitVariable` | zero at `0x108c` (`x0=bss+0x108`; pair store reaches `+0x10c`) | Initialization default only, not live state. |
| `QDFTcon_GetOffSensingDone` | zero at `0xa990` after its off-sensing-done result equals1 | A completion-related clear. The status source/meaning remains separate. |
| `QDFTcon_GetElSensingDone` | zero at `0xabac` only after external done result1 and cached EL sensing state at `+0x104` equals1 | A completion-related clear. |
| `QDFTcon_MonitorTemperatureSensor` | zero at `0x10c84` after off-sensing done1; zero at `0x10d48` before an EL-sensing status read | Monitor/recovery lifecycle clearing. |
| `QDFTcon_Resume` | zero at `0x11034` before status/recovery frame-mode handling | Resume lifecycle clearing, not a proof that every resume completes output recovery. |
| `QDFTcon_SetElSensing(1)` | stores1 at `0x11ecc` after its EL sensing command/status sequence, then waits10ms and caches EL state1 | A sensing-start path deliberately enables command skip. The store follows helper return capture; it is not conditional on proven physical completion. |
| `QDFTcon_SetElSensing` non-1 route | zero at `0x12038` before its command | A stop/other-state clear. |
| `QDFTcon_SetOffSensing(1)` | stores1 at `0x1380c` after its off-sensing command/status sequence, then waits10ms and caches off state1 | A sensing-start path deliberately enables command skip. As above, no physical completion is established by the store. |
| `QDFTcon_SetOffSensing` non-1 route | zero at `0x13970` before its command | A stop/other-state clear. |

This inventory covers direct scalar/pair stores reached by the bounded scan of
this matching module. It does not prove that no alias/bulk write, another
module, the controller firmware, or arbitrary live-memory modification can
change this state.

## Reachability and observations

Both sensing setters are registered in the QDF function table during module
initialization: `SetElSensing` is materialized at `.init.text+0x98/+0xa0`; the
same table contains `SetOffSensing` at `+0x130/+0x134`. This proves callable
API slots, not a specific UI caller. The local debug parser has a direct
`QDFTcon_SetOffSensing` call at `0x1578c`; it is not evidence that it ran.

`QDFTcon_MonitorTemperatureSensor`, Resume, and sensing completion helpers
can clear the word. Their static paths are useful log/correlation targets but
do not establish a particular transition from Home, Live TV, HDMI, or Ugoos.
The visible-black cases occurred without an onset-aligned capture, so no live
value or causal activation of command skip has been proved.

The normal skip log is the distinct literal
`qd command skip[%d], cmd =[0x%llX]` (`.rodata.str1.8+0x4540`); readers use
the same family. Preserve PID/thread, timestamp, command, sensing start/stop,
completion, Resume, and mode/mute traffic in an observed capture. A missing
transfer is meaningful only if capture accounting and parser completeness pass.
It cannot by itself identify the writer that set the flag, MCU acceptance, or
OLED emission.

## Consequences for the prepared one-zero test

The public unmute-zero test must treat a public accepted reply plus no `0164`
wire write as ambiguous: it may be this general skip, the PVCC special skip,
suspend, TCON-state gating, lost trace data, or a route that did not reach QDF.
Do not clear/force the word, invoke sensing setters, or modify a driver cache
to resolve that ambiguity. Those change panel-control state and could hide the
real condition.

## Reproduction

`qd-command-skip-lifecycle-reproduce.py` hash-checks the exact module then
prints only the relevant disassembly ranges. It has no TV/network access.

## Independent review correction

The no-lock read gate and its lack of the locking-reader0x0c exception were
added explicitly. Both variants leave caller storage untouched on skip; a
zero return does not initialize that storage to zero.
