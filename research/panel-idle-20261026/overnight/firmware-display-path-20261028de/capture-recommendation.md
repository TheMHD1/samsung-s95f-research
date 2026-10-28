# Existing-log acquisition, without a producer change

The concrete reader invocation, now used successfully by the central coordinator, is:

```sh
/usr/bin/vlogutil -v kerneltime -t 2 '*:S' 'AVE:I'
```

DE did not invoke the TV. The central coordinator subsequently executed this exact filtered argv and retained the accepted result under DH `ave-baseline-01/`. It is a finite historical read, with reader-side tag/priority selection. It deliberately omits `-s`, `-P`, `-p`, dump-to-USB, configuration options, and debug setters. The installed-help artifact confirms these options, and the retained target run qualifies this exact filtered argv as a finite historical reader. Do not use its successful completion or empty filtered output as proof that the producer was enabled or the complete incident window retained. A previous `-P` attempt returned `VLOG_SET_PID_FILTER: Invalid argument`; the long streaming route also has failed-completion history.

Use the coordinator's bounded native child supervisor: fixed argv, fresh private output, at most 8 seconds, combined stdout/stderr cap256KiB, exact child PID/start identity, PROGRAM_16 and exit-status capture. An output limit or deadline makes that acquisition incomplete. The TV has no qualified `timeout` CLI; a host timeout alone is not a child-PROGRAM_16 guarantee. The short historical reader needs no new display action. Do not silently change it to a future streaming reader. If a supervisor is not already qualified, the finite stock command remains usable as an ordinary read with an explicit hard-deadline qualification gap; do not call a bare shell command hard-bounded.

Before and after each invocation retain boot ID, `/proc/uptime`, UTC and, when the harness supplies it, `CLOCK_MONOTONIC` microseconds. Retain the entire selected output before host filtering. Record host request start/end and source hashes. Parse only the timestamp between thread-name colon and `[VDIWEF]/tag`; preserve continuations without inventing timestamps. Retain header/footer counts, reported time interval, first/last actual rows, exit code, truncation/deadline state, and filtered match count. With no fresh event, two-second history can truthfully return no relevant transition.

Host selection, after saving raw output:

```text
Compen ratio|Set NPC LUT|t_SetNpcLut|ScreenProtect|t_SetQdSeneDetect|DimLvl|ERR Detect|QD_TCON_OFF|reboot tcon
```

The full AVE-selected source must remain available; this string selection is not a producer switch. Obtain the existing kernel/vlog driver messages in their own established read path as well: `panel dpms`, `TCON_MUTE`, `SetQdTconPowerControl`, `ERR DET`, `PMIC`, and off-sensing distinguish software power sequencing from the content setters. A kernel-log filter does not supply the missing AVE message, and AVE selection does not cover all Deviced/kernel events.

## Source and actual time evidence

- Extracted stock `vlogutil`: 43,352 bytes, SHA256 `858251f22546ebd34e0081fb2079f7020f35a6b5537d86a2e94344b443eda6c9`. It was inspected, never executed on the host. Current installed identity must be refreshed by the coordinator if this pin is required for a run.
- `vlogutil-help-discovery-20261026T145901Z.json` confirms `-t` means last seconds, `-v kerneltime`, tag-priority filters, monotonic absolute streaming bounds and default `*:V`.
- Actual unfiltered `-t 2` in `vlogutil-kerneltime-format-20261026T150016Z.json`: 6,327 timestamped rows, 936,079 shell-output bytes, actual timestamps48421.831..48423.827, request uptime48423.82, footer48426.669. It took approximately2.84seconds after query start. The later exact filtered argv returned 1,631 bytes, two monitor rows at173626.227 and173627.227, exit0 and no root-output truncation. Its advertised history was173626.178..173628.178; footer173631.372 follows query start by3.194seconds. The VLOG footer nevertheless retains `not_complete:4`; transport acceptance is not lossless driver-history proof. Physical light was unobserved and producer settings were unchanged.
- Extracted `libdlog.so.0.0.0`: 15,592 bytes, SHA256 `9549f8819ffd46a1b299b4e5eea480e6d392f04619b47a0c0177b364c45aeb94`. `vlog_write` at ELFlinkVA0x432e13ac calls `clock_gettime` with clock ID1 at0x432e13dc (file0x13dc). This is the Linux `CLOCK_MONOTONIC` ABI. `vlog_is_init` references `/dev/vlog` and opens/maps its log resources. This file's linked base is not an assumed live mapping.
- Tool output is millisecond-formatted and advertises an `ns_offset`; do not equate an AVE formatted row with the exact controller sample time or physical light transition. Use the native/controller measurement's full transaction brackets and independently bracket the displayed condition. `/proc/uptime` and monotonic clocks can diverge over suspend; recheck alignment and boot for every capture.

## Producer gates, distinct from the reader

The `npc-change` message at AVE ELF0x1c7444 and its address companion0x1c75a0 use numeric buffer0, priority6, tag `AVE` (consistent with retained `E/AVE` rows). They execute after a selected-LUT change, independently of the backend debugmask. They will not repeat just because a reader was started. Existing library-level priority/tag rejection still applies.

The repeated `npc-repeat` message at0x1c764a uses buffer0, priority4, tag`AVE`; it is gated by backend state word0 bit6 (`0x40`) and can run on every invocation. Optional `print_usb_file` at0x1c7684 additionally requires AVEshm+0x68 nonzero. Do not enable either flag for the first acquisition.

`__dlog_print` calls `vlog_is_init` and `vlog_is_allowed`, then `vlog_write` at0x432e25d8. `vlog_is_allowed` at0x432e1758 checks the mapped priority threshold at map+0x10008; sufficiently high numeric priority passes, while lower priority requires a tag-hash/strncmp lookup (0x432e1776..17de). Without a mapped configuration, its fallback accepts numeric priorities above2. `__dlog_print` also has initialization/backend/global-priority gates. Static branch existence does not prove their live settings. A reader `AVE:I` filter cannot bypass these gates.

The local QD backend setter0x1c5a2c is only a store to the backend state word. `QDDimming::SetDebugPrintFlag`0x170dec can OR/clear requested masks for selector2 and dispatch backend vtable slot8 at0x170e68. That is a candidate for future, separately technically qualified runtime-only logging enablement with exact old-state/rollback. An external invocation route, active object/vptr, all consumers of bit6, volume, and callback effects have not been closed here. No enable command or memory patch is supplied. A silent existing read does not justify enabling a whole dimming debug parser, changing per-frame controller flags, or replacing a global trace configuration.
