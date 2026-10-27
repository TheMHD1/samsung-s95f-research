# Offline log analysis of `owner-power-on-20261026a`

Analysis performed 2026-10-26 from already rescued host files. I made no TV,
root, network, device, trace, getter, setter, or control call. The original run
remains rejected (`accepted:false`, `technical_capture_complete:false`,
`diagnostic_eligible:false`, `physical_state:unobserved-or-incomplete`, and
`absence_claim_supported:false`). Rescue and offline decoding do not change
those classifications.

## Provenance and parsing method

The seven rescued files are bound by the independently audited
[`manifest.json`](owner-power-on-20261026a-rescue/manifest.json). The files
used most directly here are:

| File | Bytes | SHA-256 |
|---|---:|---|
| `trace` | 19,310,261 | `44f68ebd1fb301c74cab501a04e84b73b95223e96c977062ed6db0b92977b575` |
| `meta.txt` | 254,743 | `3f36476bea2b434e7364ee86f019708290ed118f3123e4b993ba46d573c9ba0b` |
| `samples.txt` | 117,490 | `38931ba5c3eab82233d534e0de39e6cd279835d0b8d559b1e6244b86a8212a2f` |
| `sample-errors.txt` | 201,684 | `98d132e7f83e86b7d724586d7f73e05898edbf6f578522d4ecd5249b13b11c50` |
| `artifacts.txt` | 3,570 | `978bcadf1d6808708f4d0bcff3cdc977f9e95d4cd91dc9c96ec127b4d6181372` |
| `fds.txt` | 4,690 | `93684e83a3293716db9a5252283a78efbaa2cc12a937eb12e1e04fff7ea11b66` |
| `vlog-after.txt` | 67,108,864 | `eac02d7bf3a4fb216295edba8be99466d7b80c7a43f7535841f882b052c1c3d3` |

The independently generated transaction decode
[`owner-power-on-20261026a.qd.json`](owner-power-on-20261026a.qd.json), SHA-256
`aaf7557ec5b63d1bd03ab6aa7c5c4a27506870261f9a8c882d3263b7e52d5bb4`,
binds the exact trace hash above. It reports `172200/172200` retained/written
events, no parse errors, 264 structurally complete transfers, no partial
transfer, and no orphan result. Its qualification is important: these are
observed host I2C bytes and transport results, not proof of panel-controller
acceptance or emitted light.

`vlog-after.txt` is not strict UTF-8: byte offset `42,951,709` contains `0x8d`.
The raw SHA and gzip retrieval checks pass, so this is an encoding property,
not evidence of corruption. All timestamp and keyword analysis below operated
on the original bytes. Replacement decoding was used only to render selected
text for human reading; no record was dropped because it could not be decoded
as UTF-8.

## Time coverage and the hard vlog truncation

The ftrace marker clocks are:

| Marker | Uptime |
|---|---:|
| `TRACE_ARMED` | 73050.982300 |
| `PREROLL_START` | 73051.217140 |
| `CAPTURE_START` | 73052.233218 |
| `CAPTURE_END` | 73137.840506 |
| `CAPTURE_DRAIN_END` | 73138.033049 |

The vlog command requested unfiltered kernel-time streaming from `73050.210`
through `73140.210`. A byte regex matching the actual record form
`:<space><uptime><space><severity>/` found 447,407 timestamped records. Their
timestamps are nondecreasing from `73050.001` through `73137.803`; the largest
adjacent timestamp difference in the retained records is 0.047 seconds.
Those facts describe the retained prefix only and do not certify source-side
delivery completeness.

The file is exactly the configured 64 MiB limit and ends in the middle of the
text `ConnectionControlSer...`, with no normal vlog footer. The last complete
record timestamp is:

- 37.506 ms before `CAPTURE_END`;
- 230.049 ms before `CAPTURE_DRAIN_END`; and
- 2.407 seconds before the requested vlog end.

This is a conclusive **vlog sidecar truncation**. In particular, log searches
cannot support any absence claim at the physical-window endpoint or afterward.
The timestamp prefix covers almost all of the physical window, including the
power transition described below, but not its last 37.5 ms and not the drain.

## Observed software and wire sequence

The following is an ordering inventory, not a causal or physical-state model:

| Uptime | Retained evidence |
|---:|---|
| 73131.296 | Input logs record `XF86PowerOff` press from `Smart Control 2016`. |
| 73131.297--73131.310 | `tvctx-manager` begins `ProcessPowerOff`; welcome mode sets its power-animation state; AVOC receives an audio-mute request and logs main-out mute on. |
| 73132.411--73132.420 | Welcome-mode outro completes and requests power off. Deviced logs that OLED off-sensing is required before power off. Ftrace then records `[frc-tcon] panel dpms: off` at 73132.419734. |
| 73132.587104 | The decoded bus trace records deviced writing selector `0x164` (`panel-mute`) with value 1. |
| 73132.637539--73132.637543 | Two `clk_disable` rows name `MFD_CLK_EN` and `dummy`. Their downstream electrical meaning is not established here. |
| 73132.792043 | Ftrace records `[frc-tcon] panel dpms: off end`. |
| 73132.801590 | AVEMonDIM writes selector `0xc4` (`screen-saver-brightness`) with value 7. |
| 73132.844--73132.850 | Deviced/application logs describe `lcdon` to standby / background standby. |
| 73132.865027 | GPIO 425 is set to 0. GPIO 425 is not identified here as PVCC and must not be relabeled as such. |
| 73135.074--73135.163 | Wake/source preparation logs identify source `0xc0000`, `P_MODE_NEW_HOME`, and `UNIPLAYER(0xc0000)/S:0xc0008`, 1080p30. These are software/source fields, not picture visibility. |
| 73135.226 | AVEMonDIM logs `ave_tcon_power_level` IOCTL error `Operation not permitted` with tag `AVOCD_AVE_INIT`. This is a concrete failed call, not by itself the root cause of the black picture. |
| 73136.352122 | GPIO 425 is set to 1. The same scope qualification applies. |
| 73136.537901--73136.555632 | Deviced writes screen-saver method 1, brightness 7, waiting policy 2, slope 2, factory-low-power-policy 6, VRR-DIA enable 0, and VRR control 0. |
| 73136.593759 | Deviced writes selector `0x128` (`dimming-level-request`) with value 207. |
| 73136.652149 | Ftrace records `[frc-tcon] panel dpms: on`. |
| 73136.725190 | Deviced writes `panel-mute` value 0. |
| 73137.317873--73137.318289 | Ftrace records `panel dpms: on end`; vlog records `@picture_on_time/frc-tcon/664/msec`; AVEMonDIM then writes screen-saver-brightness value 0. |
| 73137.332 onward | Software power callbacks report standby to normal/lcdon. Audio logs around 73137.49--73137.69 report unmute/master-mute 0 state changes. |

The decoded bus set contains no focused `0x180` off-sensing or `0x1a0`
EL-sensing write. That is a statement about this filtered, decoded trace, not a
claim that sensing did not occur by another path. The literal deviced message
that sensing was needed is not evidence that the action completed.

The retained vlog includes five `Thread Vsync Over` rows: AVEMonVE/AVEMonDIM
gaps of about 0.364/0.368 seconds around DPMS-off and 0.657/0.658 seconds around
DPMS-on, plus a later 0.036-second DIM gap. These are AVE worker timing
messages. Separately, 5,185 `drm_vblank_event` rows were retained. They continue
at roughly 60 Hz during DPMS-off, the standby interval, and DPMS-on (23, 231,
and 40 rows in those three intervals respectively). Neither worker-vsync logs
nor DRM vblank activity establishes panel light emission.

The tcon monitor prints the literal `[QD_TCON_OFF] = 1` 83 times, regularly
through 73131.419 and once more at 73137.606. The source-level meaning and
freshness of that monitor value have not been proven here, so it is not a
physical-state label. Earlier periodic `sp-kpi` rows at 73052.454 and 73112.462
report TCON status 1, PMIC-init info 0, and Vx1 lock 1, while a demura getter
fails with `Operation not permitted`; those periodic queries precede the
73131--73137 power sequence and do not establish its result.

## Source, maintenance, recovery, and fault searches

The retained prefix contains no literal `RTProtect` or `PVCC`. Because the
vlog is capped before `CAPTURE_END`, that is **not** evidence that an RTProtect,
PVCC, TCON, or recovery event was absent. The captured GPIO number 425 must not
be renamed to PVCC without an exact binding.

The `maintenance_mode` text appears in configuration queries returning 0,
including during the late wake path. Those application/configuration queries
do not prove that hardware maintenance or compensation was inactive.
`pvodservice` periodically enters and leaves a function named
`CheckRecoveryShutdown` through uptime 73128, before the observed power-key
sequence; the function name is not evidence that a recovery occurred. A later
network message about stopping connection recovery on power-on concerns its
own network state. No hardware recovery can be inferred from either.

At 73135.163 AVE identifies `P_MODE_NEW_HOME` and the UNIPLAYER source noted
above. Around 73137.759 application logs identify fullscreen app
`com.samsung.tv.csfs` and a software source type of TV. These software states
do not prove that a picture was emitted. The dimming messages and wire writes
likewise show inputs/requests, not completion of a physical-output path.

## Sampling and human-observation limits

`samples.txt` contains 370 monitor rows from 73052.32 to 73137.17 (about
4.349 Hz) and 85 Q rows whose read intervals run from 73052.26--73052.74
through 73136.23--73136.66 (about 1.000 Hz by Q-start spacing). The final Q
read ends approximately 1.181 seconds before `CAPTURE_END` and just before the
DPMS-on interval completes. Therefore the sampled branch fields do not cover
the late brightness-0 write or prove a final steady state. All such rows are
non-atomic samples in any case.

The record contains two notes, neither an eligible ordered picture timeline:

- a prior owner-chat summary mapped near uptime 73061.879 says For You was
  briefly visible after an ordinary off/on and then black within about one
  second, but it has no reaction or clock uncertainty and is not wholly
  in-window evidence; and
- the note near 73093.717 is an instruction asking for one ordinary off/on,
  not confirmation that the action or a physical observation occurred.

The later report that audio was on has no calibrated TV-uptime interval. It is
consistent with late software unmute logs but cannot be synchronized to them
or used to prove causality. No local observer annotation establishes a
visible-to-black transition for this run.

The separate accepted public `SetPanelMute(0)` request at approximately
72719.20--72719.24 belongs to the earlier
[`stock-unmute-once-runtime-audit.md`](stock-unmute-once-runtime-audit.md). It
preceded this capture by roughly 333 seconds and lies outside this vlog, whose
first timestamp is 73050.001. It must not be conflated with the later
73131--73137 ordinary power sequence or relabeled as its probe/startup event.

## Why the original capture remains rejected

The trace itself is unusually strong salvage: all five markers are present;
the four CPU entry counts sum to 172,200; retained equals written; and every
CPU reports zero overrun, commit overrun, and dropped events. The decoded I2C
transactions also pass their raw/semantic structural checks. This does not
repair the collector protocol.

`artifacts.txt` reaches its end sample at uptime 73141.06. After that source
step, the collector waits for and accounts for vlog, then should write final
hash, identity, capture-window, map/pointer, global-trace, FD/TID, and sidecar
manifest blocks before `CAPTURE_COMPLETE`. Recovered `meta.txt` stops after
per-CPU PM stats and `fds.txt` stops at arming; those required final blocks and
`CAPTURE_COMPLETE` do not exist. The original record correctly reports
`ValueError: capture completion missing`.

The exact 64 MiB size, mid-record ending, missing footer, and source ordering
make the vlog limit/shutdown boundary the strongest bounded explanation. It is
not proven to be the **sole** collector failure: the retained files contain no
final vlog exit/status tuple or collector exit reason, so an undrainable-vlog
path, identity/stop race, or coincident external termination cannot be
excluded. It is safe to say that the vlog cap is a definite sidecar failure;
it is not safe to say that it alone caused every missing end artifact.

The record's original cleanup flags also remain false. A later, separately
authenticated cleanup returned exit 0 with stdout
`0`, `CLEAN`, `RESCUE_DIRECTORY_ABSENT`, empty stderr, and global tracing off;
its evidence is under
[`owner-power-on-final-cleanup-20261026`](owner-power-on-final-cleanup-20261026/).
That establishes later residue cleanup after rescue, not successful cleanup or
technical acceptance at capture time.

## Bounded conclusion

The salvage establishes a complete retained trace and an ordered software/wire
power sequence: mute 1 and DPMS-off, standby, wake/source and dimming setup,
duty request 207, DPMS-on, mute 0, then screen-saver-brightness 0 at the
DPMS-on endpoint. It also retains one failed `ave_tcon_power_level` call and
AVE worker timing gaps around both DPMS transitions. These facts narrow where
future source analysis can look, but they do not choose among a classifier
policy, panel/output gate, TCON/panel fault, or another mechanism, and they do
not prove the panel became lit.

The owner-reported black picture remains real human evidence but cannot be
time-aligned as an eligible observation in this run. The capped vlog prevents
endpoint and afterward absence claims, including claims about RTProtect,
PVCC, maintenance, sensing, recovery, or later TCON status. No repair,
recovery, automatic retry, or causal result is claimed.
