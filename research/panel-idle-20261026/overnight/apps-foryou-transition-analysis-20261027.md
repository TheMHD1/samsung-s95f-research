# Owner Apps-to-ForYou transition: retained evidence analysis

Recorded 2026-10-27 UTC. This is an offline analysis of the completed
`apps-foryou-20261027c.onset` capture and the already retained, separately
bounded post-cleanup status samples. It made no TV, root, network, controller,
GPIO, key, getter, setter, power, or cleanup call. It did not modify any raw
capture or prior record.

## Result

The capture contains a real software transition into the For You tab and one
new controller-facing measurement:

* the Home state changes to exact value `d/ug.tab@ForYou` at uptime
  `84433.223`;
* the stock host API named `QDFTcon_GetPowerLevel` returns raw value `1` at
  `84419.767` and `84429.794`, then raw value **`0`** at `84439.838`; exact
  selected-profile code identifies controller selector `0x0d` as a computed
  ratio clamped to 100, not a Boolean controller-power flag;
* the 135 sampled AVE monitor blocks and 30 sampled QD branch/cache bodies do
  not change, and are byte-identical to the immediately preceding Apps
  baseline capture; and
* after the capture was completely cleaned up, separate one-shot reads in the
  owner-reported black context returned controller status `0x10` and raw
  ERR_DET GPIO value `1`. The earlier owner-reported working Apps state had
  returned status `0` and pin `0` on the same boot.

This is useful evidence of a ForYou-associated measurement transition not
represented by the sampled userspace policy/cache fields. It does **not**
establish the physical onset time, prove that the controller was powered off,
prove that raw ratio zero means zero emitted light, prove that RT protection
caused rather than reacted to the blackout, identify the electrical source of
RT protection, or establish that the selected packaged controller firmware
equals the image currently executing.

The original capture remains, correctly, `accepted=false`,
`technical_capture_complete=false`, and `diagnostic_eligible=false`. The raw
PM rows expose a conservative parser false-negative, but this report does not
rewrite or retroactively accept that record.

## Exact inputs and integrity

The original record is
`apps-foryou-20261027c.onset/record.json`, SHA-256
`9f06519a295acfbb0f7dda124e327c56251f19a826eea75aaf151f4ee605e322`.
Its seven salvaged sidecars match the collector-advertised byte counts and
hashes:

| sidecar | bytes | SHA-256 |
| --- | ---: | --- |
| `partial-trace` | 5,722,930 | `9f8c7d1fa029f28c39fe4c23139f69cbbc6faa7a7763f63529a4b35d9510ca86` |
| `partial-meta.txt` | 494,781 | `27d37052458be44cd928df4fa38e0f530683aec7f504ff935018b6a47dbc120d` |
| `partial-samples.txt` | 42,420 | `12b1b3cbb73d7fe2dc48ab63e7f7bba501a68e56f5e0343d9b8332a72b073536` |
| `partial-sample-errors.txt` | 73,798 | `6e9a8284d0f12cb69f549f6c00d1be62c7cb3ce65c79570531c15562816d04af` |
| `partial-vlog-after.txt` | 8,766,607 | `00896fb0ef73bee12ecf35b9264eac85f343a290a9abc61c3c667e1b5e1fe56f` |
| `partial-artifacts.txt` | 3,739 | `bb57c228fc1e4ece995f8d6e387de0095906555fbd02eed1ff5cecf36a80d9c3` |
| `partial-fds.txt` | 5,710 | `305925a9384436f423c84950f83c87d13aaa338b291df5e2828466b5c9d95e48` |

Collector stderr is empty, collector stdout reaches `CAPTURE_COMPLETE`, and
authenticated quiesce and cleanup both succeed. Cleanup returns global tracing
`0` and `CLEAN`. All four per-CPU trace statistics report zero overrun,
commit-overrun, and dropped events. The trace retains and reports all 51,383
events. This establishes loss-free retained raw data and verified cleanup,
not acceptance under the existing higher-level PM contract.

The exact ordered marker clocks are:

| marker | trace uptime |
| --- | ---: |
| `TRACE_ARMED` | 84415.771444 |
| `PREROLL_START` | 84416.024507 |
| `CAPTURE_START` | 84417.022988 |
| `CAPTURE_END` | 84447.184305 |
| `CAPTURE_DRAIN_END` | 84447.289390 |

The physical marker window is about 30.161 seconds. The vlog source exits
normally and contains timestamps `84415.001..84449.996`. Its footer reports
60,580 records, `overflow:0`, `corrupted:0`, and `not_complete:860`.
Consequently it has useful endpoint coverage, but it cannot support a general
log-absence claim.

### Independently retained raw kernel window

An authenticated, read-only `dmesg` acquisition made before the rolling ring
advanced further retained the numeric uptime interval `84413..84452` in
`paired-restart-20261027a/foryou-kernel-window-b.txt`, 43,911 bytes, SHA-256
`21048d338b089df2a860e59e5bf09872dcda32d49f292e06dc93a7454bf67a2b`.
Its acquisition record has SHA-256
`5f1bc6a510adcc22ac97cd9de07ce76dc35968dc6961eac5a165076cf74c11cc`.
The one authenticated command exits zero with empty stderr and matching boot
ID at both endpoints. At collection time the retained ring edges were
`84404.004879..84898.857634`, so the requested transition interval was inside
the retained ring. The snapshot is non-atomic and cannot prove that a
facility did not suppress or rate-limit a message. The earlier attempted
regex extraction selected zero bytes and is preserved as a failed attempt;
it is not negative evidence. The preceding Apps baseline had already rolled
out, so there is no symmetric full-kernel baseline window.

The selected window adds bounded context rather than an onset timestamp:

* QDF logs screen-saver brightness 0 at `84414.847584..84414.848683`, before
  `TRACE_ARMED`. This reconciles the raw kernel log with the absence of that
  write from the later ftrace interval; it does not assign the write a causal
  role.
* `GFX V sync is working fine` appears once per second through `84441.707648`,
  followed by `mixer_sys_disable_vblank` at `84442.370919`. These are host
  graphics-control messages, not a pixel-light sensor or proof that the panel
  went black at that time.
* No raw QDF `ERR DET Status`/RT-protection line occurs in this selected
  interval. The later exact `0x10` line is at `84517.921691`, outside it. This
  bounded text inventory cannot exclude a silent controller assertion or a
  driver path that did not log.
* Eight `send signal from KERNEL, SIG : 11` lines recur about every five
  seconds from `84413.856857` through `84448.855342`, all for the same
  `.NET ThreadPool(16391)` and all naming the same nonzero handler address.
  They are kernel signal-delivery diagnostics; this report does not classify
  them as process crashes. The same window contains no `Oops`, kernel panic,
  or call trace.
* Opaque `TZDEV/TEE/ERR` payloads occur in bursts at `84415.276..84415.278`
  and `84447.495..84447.526`. Their contents and relevance are not decoded,
  so the `ERR` tag alone is not a TCON-fault attribution.

## Human and UI timeline

The human annotations and software logs have different evidentiary roles:

| uptime / interval | retained evidence |
| ---: | --- |
| 84428.413--84430.602 | Uncertainty interval for the local `GO` note. The annotation says one manual Apps-to-ForYou transition and no restart. |
| 84430.641 | First retained remote key press after GO: `Left`. More navigation follows. |
| 84431.601--84433.341 | Retained `Right`, `Up`, and `Left` key events move through Apps/Live/ForYou tabs. These are owner actions, not commands generated by the collector. |
| 84433.223 | Home writes exact current-tab value `d/ug.tab@ForYou`; logs then report focus changing from Live to ForYou. |
| 84442.976--84445.164 | Uncertainty interval for the owner's `done` acknowledgement, wholly inside the trace window. |
| 84452.295--84454.484 | Mapped uncertainty interval for the later `picture=black` annotation. It is wholly **after** `CAPTURE_END`. Reaction and chat uncertainty were not supplied. |

There is no structured visible-picture annotation before the black annotation.
The owner's report establishes that the panel was black after the acknowledged
manual transition, but it does not establish when inside—or after—the capture
the physical change occurred. Software state is not substituted for that
missing physical timestamp.

## The controller-facing change

Offline decoding used `decode-qd-trace.py`, SHA-256
`cc69c38cb78c94b3e044dc546ce1d0d6328b0c2f5aace308499ead0baf375be3`.
It reports 13 structurally complete Linux I2C transfers, no partial transfer,
no orphan result, and no parse error. Every transfer is on bus 5/address
`0x76`, with `ret == n == 2`. That establishes the recorded Linux transfer
result only; it is not a generic controller acknowledgement or proof of
physical output.

The three attributed stock selector-`0x0d` query sequences are:

| uptime | exact relevant wire sequence | raw result |
| ---: | --- | ---: |
| 84419.766579--84419.767616 | `F3:0174` write payload 1, followed by `F3:800000000d` read | 1 |
| 84429.793256--84429.794295 | same | 1 |
| 84439.836625--84439.837638 | same | **0** |

Each sequence also has the expected surrounding `F3:0100000000` command
status reads. Their changing raw replies are retained, but the exact QDF
module does not label those handshake bit patterns as brightness, fault, or
light state.

The exact copied QDF implementation identifies `F3:0174` plus selector
`0x0d` as the host API `QDFTcon_GetPowerLevel`. The final raw transport rows
are an address write `F3-80-00-00-00-0d`, a four-byte read reply
`00-00-00-00`, and an I2C result `n=2 ret=2`; the enclosing QDF ioctl exits
zero. Thus zero is present on the captured bus reply and is not merely the
caller's pre-zeroed output surviving a missing read. Conversely, the QDF
getter ignores its internal helper return, so ioctl return zero alone would
not establish a successful read; the complete raw transfer is essential.
The copied QDF body forwards the returned word and contains no post-read
debug override on this path.

The selected packaged controller image gives a more precise, but conditional,
meaning: selector `0x0d` calls image-0 function `0x10e40`, which computes a
ratio and clamps it to at most 100. It is not a Boolean powered-on/off getter.
That image is a uniquely matched packaged profile but has not been proven
byte-identical to the firmware currently executing, so even the ratio
interpretation remains a source-backed candidate for the live response—not a
live-image proof. At minimum, the wire value changed from 1 to 0 on the exact
same stock request shape. It is not a pixel sensor, emitted-light verdict, or
direct proof that the controller powered off.

Reaching these observed transactions conditionally passes the QDF suspend,
command-skip and TCON-state gates at those particular checks; it does not
exclude an earlier transient, the separate PVCC mute-zero guard, a
controller-internal protection state, or a later change.

The final change occurs 6.614 seconds after the logged ForYou tab value and
about 4.23 seconds before the midpoint of the owner's `done` annotation. The
correlation is therefore temporally useful, but there is no calibrated black
onset against which to order it.

The contemporaneous AVEMonDIM logs also show how userspace reports the
measurement without turning it into a power-state proof. Each query is
immediately followed by `m_SetSTEnergyPicMode :5`; `m_CalcPowerConsumption`
reports `ANA:1` at `84419.769` and `84429.794`, then `ANA:0` at `84439.838`.
It reports `ANA:0` again at `84449.864`, just beyond the trace window but
inside vlog coverage. The other printed calculation inputs are already zero
in these rows and `Lamp:0` is present even in the earlier `ANA:1` rows, so
neither `ANA` nor `Lamp` can be promoted here to a physical-light verdict.

The only other controller read is `F3:800000000c` at `84432.532493`, replying
`00180018`. Exact module analysis maps selector `0x0c` to two external-PCB
temperature fields, both raw decimal 24 here. Units, placement, calibration,
and relevance to light output remain unproved. No immediate retry follows.

The decoder reports no recognized mute, frame-mode, maintenance, or dimming
focus operation in this finite ftrace interval. No screen-saver-brightness
write is present after tracing starts; the separately retained kernel window
places a brightness-0 write at `84414.848`, before `TRACE_ARMED`. This is a
bounded inventory, not proof that no untraced, internal, other-address, or
other pre-window action occurred.

### Contrast with the immediately preceding Apps baseline

The preceding baseline trace has SHA-256
`c30a812cc51126b7da3b2448227ddb3ed1ead4736a78a6210abad337dcd50414`.
The same offline decoder finds three stock selector-`0x0d` results in that run,
all raw `1` at `84289.370`, `84299.415`, and `84309.440`. Its last additional
QD write is screen-saver brightness 7 at `84311.125`. Run `c` instead has two
raw 1 results followed by raw 0 and has no screen-saver write in its ftrace
interval; its independent kernel window records brightness 0 before tracing.

This is not a claim that the screen-saver write prevented failure in the
baseline, or that its absence caused the transition result. The strong
comparison is only the repeated raw selector value.

## State that did not change

### AVE monitor history

All 135 monitor payloads are byte-identical, from uptime `84417.10` through
`84446.96`. The source-backed fields remain:

| field group | value throughout |
| --- | --- |
| ERR/VDD/ELVDD consecutive counters | `0 / 0 / 0` |
| ERR/VDD/ELVDD recovery counters | `2 / 0 / 0` |
| `si_ok_count` | 4 |
| `qd_tcon_off` | 1 |
| `onetime_execution` | 1 |
| `ip_status_count` | 7 |
| `fault_occurred` | 0 |

`qd_tcon_off=1` is already present before `CAPTURE_START`; vlog prints it
once per second from `84415.523` through `84449.544`. Exact AVE control flow
defines it as a userspace history latch. Once set, the monitor's ordinary
entry logs and returns before fresh GPIO/status checks. It does not describe
a new power-control operation at each log line and cannot time this event.
The immediately preceding Apps baseline has the same entire monitor payload,
so this latch and its retry history are pre-existing rather than a new
ForYou discriminator.

Zero current sample counters also cannot establish current electrical health:
the history-latch branch suppresses the normal fresh monitor path.

### QD branch/cache sampler

All 30 Q rows have identical payloads and stable process/object identities.
They cover `84417.04..84446.40`; each sequential row takes 0.38--0.49 seconds.
The stable headline values include requested/backend cache 207, working duty
207/207, Weber gain and target 1023, Weber count 0, raw AutoDim 0, and
AutoPowerOff count 0. These sample bodies are also byte-identical to the Apps
baseline.

The fields are sequential and non-atomic. Stability excludes neither a change
away and back between rows nor a controller/kernel state not represented by
these userspace words. It does show that the new raw selector zero was not
accompanied by a persistent change in this sampled branch/cache set.

## Host power, display, and PM context

No ordinary host power-off transition is recorded in this window:

* `acm-service` repeatedly logs `isPoweroff=[0]` through `84446.003`;
* deviced shared power state remains `1` in its retained reads;
* the end artifact at uptime `84449.72` still reports `LVDS-0 connected
  DPMS_ON`;
* the compositor records commits through `84437.319`; absence of later
  commits is not meaningful for a static UI; and
* the artifact's raw HWC summary changes from mode 0/three listed windows to
  mode 2/one listed window. Those raw compositor values are retained but are
  not a physical-light measurement.

Selected generic PM tracepoints record no `device_pm_callback_*` or
`suspend_resume` row and no `sdp-hdmi` row. Runtime-PM rows inside the marker
window are dominated by MMC and audio devices. Generic PM tracepoint silence
does not cover Samsung's proprietary callback route, and therefore cannot
exclude a private module lifecycle call.

The formal PM rejection is caused by three adjacent idle-thread
`rpm_suspend mmc0:0001` entry/return pairs. For example:

```text
84421.716006  <idle>-0 CPU2 d.h2  rpm_suspend mmc0:0001
84421.716013  <idle>-0 CPU2 dNh2  rpm_return_int ... ret=0
84441.315136  <idle>-0 CPU2 d.h2  rpm_suspend mmc0:0001
84441.315143  <idle>-0 CPU2 dNh2  rpm_return_int ... ret=0
```

The existing parser includes the printed ftrace state token in its pairing
key. Because `d.h2` changes to `dNh2`, it conservatively leaves the entries
pending and rejects the run. These tokens are mutable printed state, not an
authoritative execution-context identity. The raw adjacent durations are
microseconds, not operations actually pending until drain. Nevertheless, the
original fail-closed classification is preserved.

## Post-cleanup fault context

Only after collector cleanup completed, two separately bounded one-shot
samples were made in the owner-reported black context:

| evidence | uptime | result |
| --- | ---: | --- |
| `paired-restart-20261027a/black-foryou-status.json`, SHA-256 `5e53af507ffac67cd33a709900275bee72d6c5510e9b29011d6e740551205830` | 84517.99 | kernel output `0x00000010` |
| matching kernel text, SHA-256 `af08e1d09120a08121bb4471ec049b7a2a8e873dae74c69c31b829e78e1e9714` | 84517.921691 | exact QDF raw-status log `ERR DET Status:0x10` with helper PID 13669 |
| `paired-restart-20261027a/black-foryou-pin.json`, SHA-256 `1a7edb74f6d1580c4e50415df87aafead1cfb1273b6892c994e852436e4c4e72` | 84549.36 | independent raw GPIO input value 1 |

The status sample occurs about 70.81 seconds after `CAPTURE_END`; the GPIO
sample occurs about 102.18 seconds after it. They are not simultaneous with
the transition or with each other. The prior owner-reported working Apps
samples on the same boot returned status 0 and pin 0; their records have
SHA-256 `4dd3f5cb6c414f1f1f90d6ec40713b31e791379e93c5dfe3279f6e5b46d872d2`
and `76cea107152dbfa4d21e39f1f58accf2673b5a46ee603c781c2870b2471be577`.

The exact host decoder labels status bit 4 `RT Protect`. The same raw status
and asserted pin in the black context, against zero/zero in the working Apps
context, substantially strengthens their association with this fault state.
It still does not establish direction of causality, the electrical producer,
the time the bit was set, or whether the bit initiated or merely recorded the
loss of light.

The selected packaged controller image provides a coherent static producer
and non-clearing selector-8 read path for value `0x10`. Current controller
flash identity has not been read back, so that packaged path cannot be
silently promoted to proof of what this live controller executed.

## Smallest useful next discriminator

The old AVE monitor block is no longer a useful onset clock while
`qd_tcon_off=1`: it returns through the history-latch route, and both captures
show identical counters. The ordinary QD branch/cache sampler likewise did
not separate working Apps from the transition. The useful next question is
therefore temporal:

> Does a fresh controller status change from 0 to `0x10` before, with, or
> after the stock selector-`0x0d` ratio changes from 1 to 0 during an
> owner-annotated visible-to-black transition?

A future design could answer that with a separately reviewed, finite status
sampler correlated with the existing passive kernel I2C trace and exact raw
QDF log. Each status request would need the existing out-of-domain sentinel,
ioctl return/errno, no retry, exact `F3 80 00 00 00 08` trace bytes, the raw
pre-debug QDF log, fixed maximum count/cadence, and complete trace loss
accounting. A visible baseline annotation and promptly calibrated black
annotation must bracket the physical transition. The raw selector-`0x0d`
query can continue to be observed from the stock AVEMonDIM thread rather than
actively invoked.

That proposal requires a new implementation/review; none was built or run
here. It is not harmless by assumption:

* the host getter has success-without-output skip paths for flash-update,
  suspend, command-skip, and missing callback cases; the sentinel and passive
  wire trace are needed to distinguish them;
* the bounded QDF getter has no explicit host reset, clear, recovery, or
  monitor-latch store;
* the selected packaged image's selector 8 is a non-clearing `LDRH`, but live
  flash equality is unproved; and
* controller read-to-clear/statefulness therefore remains unexcluded for the
  actual executing image, making an aggressively repeated poll unjustified.

A low-rate, predeclared finite series could be diagnostically valuable after
exact-byte review. It would still not replace owner physical annotations,
prove emitted light, or identify the RT electrical subcause. GPIO samples are
useful paired context but their current one-shot acquisition claims the input
line and changes its generic software transitory handling; they should not be
silently turned into a continuous sampler.

## Bounded conclusion

This event closes one important evidence gap: the owner-triggered Apps-to-
ForYou transition is logged, the controller selector-`0x0d` result changes
from 1 to 0 inside the capture, and the later black-context status/pin are
`0x10`/1 instead of the working Apps 0/0. At the same time, Linux power flags,
DPMS, userspace dimming/cache state, and the old AVE history block do not show
a corresponding persistent transition.

The strongest defensible interpretation is a controller-measurement change
followed, at a much later sample, by a protection-associated fault state below
the sampled host policy layer. The data do not yet order those events against
physical light loss or prove that selector `0x0d` is a live power-state bit.
The exact physical onset, electrical cause, ordering of RT assertion versus
loss of light, and a safe recovery or prevention remain unresolved.
