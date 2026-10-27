# What the retained evidence can establish about QD command gates

This note combines exact copied-module control flow with retained traces and
new read-only metadata/log snapshots. It does not establish current physical
picture state, a permanent repair, or a successful unmute.

## Stock query as an indirect constraint

`passive-black-i2c.trace` records complete bus5/address0x76 transfers at
uptime8988.809: command-status read, `F3:0174` payload1 write, command-status
read, and `F3:800000000d` read/reply1. The issuing thread is AVEMonDIM.
The existing AVE ioctl attribution and exact QDF sequence match the stock
`QDFTcon_GetPowerLevel` route at `.text+0xd088`:

```text
d0b4..d0c4  m_send_cmd_with_lock(F30000000174, payload1, lock1)
d0cc..d0d4  m_read_cmd(F3800000000d, output)
```

On this attributed stock route, actually reaching the observed write requires
the write helper to pass its suspend, command-skip and TCON-state gates. The
subsequent locking read of0x0d is neither the command-skip exception0x0c nor
the bad-state exception0x00, so it too passes those gates. Thus, **at the corresponding checks**, the inspected code requires:

- `m_suspend_status != 1`;
- `m_command_skip != 1`;
- `m_tcon_state == 1`.

This is a conditional control-flow inference from the matched stock path,
not a direct RAM measurement or an exhaustive exclusion of other dynamically
constructed callers. It does not prove values for the entire two-second
capture, at the earlier initiating blackout, now, or under arbitrary races.
It weighs against a hypothesis that one of those broader gates remained
continuously asserted throughout the observed query. A transient earlier
suppression could still have left another state latched.

It **does not constrain** `m_panel_dpms_pvcc_status`: the special guard skips
only `F3:0164` payload0, while this observed write is0x174 payload1. It also
does not measure mute readback, frame mode, controller-internal protection,
or emitted light. The capture filename is historical: it was obtained after
the last reported blackout without a fresh simultaneous physical confirmation.

## Real older skip logs need lifecycle context

`existing-gate-sensing-log-extract.json` records a fingerprinted scan of stdout
from140 saved root-result JSON files, yielding120 matches but only36 distinct
lines. Repeated copies of the same ring history are not independent events.
Interface names in dumped XML are not runtime calls.

Three unique timestamped write-skip/read-state pairs appear:

| Uptime | Source/context | What can be concluded |
| --- | --- | --- |
| 1803.266962/966 | `tcon-deep-probe.json`: nearby `turn off TCON`, then deviced `Tcon Power On`, off-sensing ready/power-normal, status checking | Real state0 skips near power lifecycle; this file's header lacks a boot ID, so do not establish cross-file alignment solely from uptime |
| 1834.698328/344 | Same file: preceding explicit deviced power-off at1826.601; subsequent power-on at1835.640 and init-check OK at1836.483 | State0 can accompany an intentional power-off interval; these logs alone do not identify a spontaneous panel fault |
| 6196.672722/732 | `recovery-reboot/capture-00.json`: boot34f419d2-6256-4e1f-a7a9-8d46b875857d; nearby wake-reason change and `lcdon` at6196.680540 | Real skips near wake, before the later visibleApps7206/black7393 comparison; not a captured initiating failure for that pair |

`off sensing available[val:1]` means the availability getter's result, not proof
that sensing was active. Likewise OledDeviceTimer's minute-based elapsed-time
updates do not themselves establish an active maintenance cycle or a sensing
setter call. No PVCC-specific skip or command-skip start was found in the
saved stdout scan; sources were already filtered or ring-limited, so this is
not evidence that they never occurred.

## Fresh read-only baseline and memory-observer boundary

`gate-log-baseline-20261026T055728Z.json` confirms at05:57:28UTC:
same boot ID34f419d2-6256-4e1f-a7a9-8d46b875857d, uptime15857.89,
HWC `deactive:0`, global tracing0 and no private instance listed. The last2000
dmesg lines contain no selected gate messages. This short rolling tail and
software state do not establish the current physical picture or onset cause.

Two metadata-only discoveries are retained:

- `kernel-ram-read-interface-20261026T055853Z.json`: `/proc/kcore`,
  `/dev/kmem`, `/dev/mem`, and `/sys/module/qdf_tcon/sections` are absent;
  `kptr_restrict` reports1. The composite shell's last read exits0, but earlier
  individual reads fail explicitly in stderr; do not call those reads successful.
- `module-address-observability-20261026T055914Z.json`: `/proc/modules`
  confirms `qdf_tcon`, `rosem_frc` and related modules loaded, with printed
  addresses all zero. `/sys/module/qdf_tcon` exists, but its section directory
  was absent. This corrects any inference that a missing section directory
  means the module is not loaded.

No direct cached-word RAM read was obtained. No policy was relaxed, module
loaded, memory interface created, live text/flag patched, device node created,
or MMIO/private hardware read attempted. The three live commands were ordinary
read-only metadata/log queries; no panel setter, remote key or power command ran.

Independent review confirmed this conditional inference against both the exact
module and trace: the stock-matching exchange spans8988.809591..8988.810610
(about1ms). It does not establish continuous gate values outside those checks.
The0x174 immediate occurs only in this getter in the inspected module, while
dynamic/external producers remain outside that finite attribution proof.
