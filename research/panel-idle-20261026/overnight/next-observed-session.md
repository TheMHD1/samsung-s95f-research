# Next observed session: discriminate entry, gate state, and recovery

Prepared from exact matching code; nothing here has been executed as a recovery test. No additional authorization is needed for the already requested diagnosis, but a physical observer is needed to establish whether emitted light changed. The latest photos are not a current-state confirmation.

The later [ARM32 CLR probe](managed-kernel-abi-probe/README.md) was an executed
instrumentation-availability check, not a recovery operation. BPF and perf
returned ENOSYS and its private files were removed. Do not base the next
observed capture on these unavailable ARM32 interfaces. The factory-setting
and notification-delete candidates remain subject to their full receiver and
callback contracts; no setting or notification has been changed by this pass.

The [legacy notification contract](../idle-research/stock-notification-cancellation-contract.md)
now links successful deletion/count>0 to client event1 and local countdown
destruction, conditional on active identity/subscription/registration. A future
observed test must occur while the warning is visible and before expiry, with
the actual target identity and delivery captured. It cannot cancel a sensing
request already issued or permanently suppress reinforcement. No cancellation
helper or live deletion test has been deployed here.

## Existing evidence to preserve

- Do not label a later software screenshot or zero getter as physical recovery. Earlier B0/B1 are the owner-confirmed black/control pair.
- Menu persistent-black, Settings flicker and spontaneous Ugoos/JBL picture-audio pauses remain separate incidents.
- HWC before-wake prevention remains unclassified because its physical trigger time relative to expiry was unknown.
- The one HDMI CRC diagnostic read may have retained a proprietary busy reference; it postdates the captured failures. Its ten-second suspend timeout is not the owner-estimated three-second menu latch. Exclude that getter going forward.

## One stock unmute-zero diagnostic while already black

This is a newly code-grounded recovery candidate, not a deliberate blanking pulse. Keep the same native source/page, record physical black and whether audio continues, confirm no Screen Optimization cycle is running, and save the baseline public getters. If the observer is unavailable, continue offline work instead of launching it.

The exact public operation is:

```sh
dbus-send --system --print-reply --reply-timeout=1500 --dest=org.tizen.tv.avoc /org/tizen/tv/avoc org.tizen.tv.avoc.AvOutputControl.SetPanelMute int32:0
```

One zero request only. Do not first request one, retry, change factory LPM, cycle rails, restart services, send GPIO/I²C commands, or install a loop. It routes through the stock controller/AVE/QDF gate, including a live mute-status read. AVOC ret0 may still mask a lower failure.

Use one private finite trace with the already reviewed bus5/address118 filters and cleanup mechanism. Put the single D-Bus call inside that same bounded root shell after a short baseline period, with monotonic markers before and after and its output saved separately. Do not start the existing blocking helper and attempt a second concurrent root call: the serialized root transport will reject it. The prepared native comparison helper is unchanged and contains no setter. `unmute-zero-capture.py` now prepares that combined shell in dry-run mode; `next-unmute-zero.review.sh` preserves it. Shell syntax, Python compilation and five public-reply classification fixtures passed. Trace/probe transfers verify size/SHA, and cleanup verifies private-instance absence plus the unchanged global baseline; a failure is preserved separately and causes a nonzero exit unless an earlier error is already propagating. It has not been executed on the TV. The helper requires an explicit physical-observation flag, checks both public baseline getters for0/ret0, submits exactly one zero request, preserves reply failure without retry, and includes independent finite cleanup. Its observer flag is an operator assertion, not a measurement.

The newly verified [PVCC guard](../tcon-research/qd-unmute-pvcc-guard.md) can suppress **every** zero send when its cached `.bss+0x194` word is zero, returning success before I2C or the mutex. Therefore even a public read/re-send attempt can be a no-op on the wire. Preserve the literal `m_panel_dpms_pvcc_status` / `qd command skip` logs and `SetPvccFlag`/`Pvcc`/DPMS lifecycle messages with timestamps and issuing thread. Do not force the flag: its setter can invoke real power-on. Also preserve suspend/command-skip/TCON-state skip logs: broader helper gates can suppress either mute payload while returning0. These logs and the guard were not observed at an aligned blackout onset.

Compare F3 80…0164 reply, any F3 00…0164 zero write, subsequent20/21/22 status reads, source/FRC events and physical outcome. A captured on-wire `0x164` read reply of zero with no re-send is evidence against a persistently asserted value of this specific gate at that instant; it cannot exclude other emission/power faults. A recovery is evidence for gate-state mismatch, not a permanent repair. If the screen stays black, preserve that result and avoid repeating the same request.

## Capture the initiating transition after ordinary picture recovery

Later preparation supersedes the separate short captures below for a full
maintenance-expiry/onset comparison: [onset-capture-requirements.md](onset-capture-requirements.md)
requires one85–90second combined trace, passive memory sampler, producer-log
stream and in-window physical annotations. The new observer is still a draft
under [independent review](onset-capture-review.md); do not execute it as an
observed test until its corrected version is cleared. A5/10second unobserved
smoke test, if cleared, verifies instrumentation only. It cannot diagnose a
60tick warning expiry or establish a physical recovery.

The installed vlog format and real6327records/2second rate are grounded in
[vlog-capture-contract.md](vlog-capture-contract.md). A successful retrospective
dump does not prove full90second coverage. Resource limits, log termination,
trace accounting, sample endpoints and physical timing all need validation.

Leave full Apps visibly stable and capture25seconds with `diagnostic-trace.py`. With the same state/settings, capture another25seconds containing exactly one Apps→ForYou transition and the observer's physical black time. Avoid Live for the first comparison because it changes video/source planes. Keep factory/HWC values fixed. Review I²C command differences and AVOC controller logs around the physical edge. Preserve existing SetNewHome and ResetSpecialModes entries separately, Rosem `New Home setting` / `new home mode` / `new tcon_frame_rate` / `[error] frame rate set` logs, and QD screen-saver00c0/c4/cc/d0 commands. In particular, compare F3:0164 gate-on/off around F3:0160 frame-mode programming; downstream frame-mode errors and the final ungate can be hidden by success-returning higher wrappers. Existing logical mute0 does not exclude that separate timing-path gate. The callbacks differ, the QD NewHome virtual edge is a no-op, and cached output rates can mask backend failure; do not infer a physical gate/timing change from those cached fields.

If no initiating host command differentiates the states, the next useful visual test keeps the same app/source and varies only displayed content. Distinguish brightness/content distribution, motion, overlay entry and tab/source changes separately; a populated Apps page currently confounds them. Do not infer a universal brightness threshold from one trial or treat a static software image as a measured OLED current.

## Separate Ugoos/JBL capture

Confirm the current chain/TV input and synchronize TV logs, mapped HDMI IRQs, lock/TX cache snapshots and Ugoos/Kodi playback/HDMI logs. Have the observer distinguish TV picture, JBL audio and playback-clock continuity. Use actual FRC counter path `/sys/kernel/debug/frc/frctest/irq_status`; compare u32 deltas. Never use HDMI crc or stub blink-error getters. No direct cable/GPIO action is required for capture.

Prepared command, only when a physical observer has confirmed the described state:

```bash
python3 ${S95F_EVIDENCE_ROOT}/panel-idle-20261026/overnight/unmute-zero-capture.py unique-unmute-session --seconds 12 --physical-black-confirmed --run
```

This command has not been run. The corresponding preparation without either execution flag is a host-only dry-run.

## Decode retained traces without inventing acknowledgement

Use `decode-qd-trace.py` on the acquired trace after its transfer size/SHA check. It preserves per-thread transfer boundaries, command/payload/reply bytes, Linux results, and ring completeness. Missing/truncated/overflowed evidence cannot establish that an unmute was omitted. A full Linux transfer is not MCU acceptance or emitted light. The `F3:01` words remain raw; the recovered transport checks a selected byte rather than decoding the whole word as panel health.

## Lifecycle gate context

Preserve sensing start/done, `Set Suspend Flag`, `i2c master busy is detected 2 times`, state-skip and actual power-on/off messages. Historical `tcon state[0]` can occur near ordinary power/wake; availability1 and minute counters do not establish active sensing. On the matched stock0x174→0x0d query route, observed wire traffic constrains broader gates at those particular checks, while leaving the special PVCC unmute-zero guard unconstrained. Use [gate evidence constraints](qd-gate-evidence-constraints.md) when interpreting quiet or active traces. No direct QDF kernel-module RAM observer is available; do not treat a cached public getter as one. The separate userspace dimming observer below does not expose those kernel gates.

Suppressed driver reads can leave caller output untouched. In particular,
locking-read bad-state normally returns-1 while send/no-lock-read bad-state
returns0; exact command exceptions differ. Preserve raw wire replies and
returns rather than interpreting a caller's initialized0 or0xff as readback.

The decoder now also preserves a separate maintenance list: F3:0180
(`off-sensing-control`) andF3:01a0 (`EL-sensing-control`). Compare their raw
payload1/0 requests and ordering with frame-mode0x160, the500ms gap in the
matched setter start path, command-skip logs and the physical edge. This can
observe an actual host control transaction without assuming the private ioctl
buffer is available. A label or completed Linux transfer does not establish
MCU acceptance, active sensing, completion, or unique runtime caller.

## Content/duty discriminator added after the dimming audit

Also review `dimming_focus` and all raw transfers for the exact QDMNT
dimming request `F3 00 00 00 01 28`, separate from the mute/frame and
maintenance focus lists. The host final-duty route contains an arithmetic
300-invocation ramp controlled by `SetAutoDim`; the function name
`m_AutoPowerOff` is not evidence of a power-off action. Its ordinary QDMNT
caller clamps the desired scalar to12 or51 minimum and1023 maximum. Those
numbers are not measured panel luminance/current, and no incident-aligned
value has been recovered. Preserve any AutoDim/final-duty/scene-policy log
change, without forcing the scalar or treating a factory brightness change
as a known bypass. Backend and driver caches can advance despite a failed
or suppressed write, so requested/read-cached values are not applied proof.
See [the exact content/duty path](../tcon-research/qd-content-duty-policy.md).

## Newly available userspace dimming discriminator

The [runtime baseline](runtime-dimming-baseline.md) directly sampled
`ave_dimming::m_pDimmingPanel`'s relocated pointer chain: active `QDDimming`,
initialized low byte1, inner `+0x2a8` AutoDim request0 at11:28:59 UTC.
That sample has no physical-state confirmation and cannot be used as an Apps
control or black-state observation. Client/provider slot `+0x98` matches;
the rejected ABI-mismatch draft is not an incident hypothesis.

For a new paired capture, derive fresh library bias and readable mappings,
follow GOT→global→object, validate the exact vptr before accessing the inner
field, and bracket the raw AutoDim read with matching pointer/header reads.
Keep the values tied to monotonic markers and the owner's physical transition.
The [observer map](../tcon-research/qd-runtime-observer-map.md) documents exact
offsets. Hardcoded addresses and the old map are not reusable across boots.
This is a small read-only observer, not a field write or a brightness bypass;
the request value does not measure emitted light or confirm a duty command.

Also record the public `GetPowerState` string separately from integer
`GetScreenState`. The recovered EL-start guard requires `standby` (enum3),
not `lcdon` (enum1). A successful `RequestELSensing(1)` stores a request;
its later consumption and actual EL-enable remain separate, conditional
events. Reason `0x4000002a` is not unique to that stored request because
the passed-run-cycle path can produce it too. Do not invoke these controls
merely to improve observation.

## Actual RoseMQD cache and local maintenance fields

The [combined control-state report](runtime-control-state.md) now identifies
the actual base QDDimming backend as RoseMQD. Freshly derive its vptr and
`+0xd8` slot, and compare the backend `siDimLvl` cache (ELF VMA0x5ab958)
with the inner working duty`+0xa8/+0xac`. The11:53:06 unobserved sample
contained207 in all three fields; it does not serve as the visible control.
The backend caches before I/O, does not roll back errors, and the vsync
caller ignores the result. Thus a failed write followed by an unchanged
candidate is a concrete retry-suppression hypothesis requiring an observed
failure, not a reason to force or clear the cache.

Capture raw gates`+0x39/+0x5c/+0x1b4`, control`+0x18c`, AutoDim`+0x2a8`
and the exact backend slot with monotonic markers. Bracket pointer/cache/duty
reads and preserve changing values; do not claim an atomic snapshot. Pair
these with the finite I2C record to distinguish cached request, actual command
emission, Linux result and physical picture. A reported software success can
still mask a kernel suppression gate; a cache-after-success fix alone would
not resolve that separate case.

The new [repeatable reader and monitor baseline](runtime-monitor-baseline.md)
also maps the actual monitor counters/latch and restart/on fields. Its
12:22:42 **unobserved** baseline has ERR recovery counter2, history latch1,
restart0/on1 and unchanged cache/duty207; it is not the Apps control. Run
`snapshot-qd-runtime.py qd-apps-before-new --run --physical-label apps-visible`
only while Apps is physically confirmed visible, then complete the existing
finite onset trace, then take a separately labeled `black-audio` sample only
if that state is physically confirmed. Use a fresh lowercase label each time.
Do not start either standalone reader during
the trace's serialized root call. These samples bracket stable states; they
do not sample memory at the exact onset instant. Preserve any rejection/raw
changing fields rather than relabeling it as stable or automatically retrying.

Compare the ERR/VDD/ELVDD counters, recovery counts, latch and restart flag
across those states. The exact latch-clear condition is restart==1 in the QD
routine; ordinary on/off helper calls can request that reset when their input
differs from the remembered state. None of this establishes a panel recovery
action. Do not write the flags, clear the latch, restart avocd, or treat a
zero fault counter as a fresh hardware test.

The finalized lifecycle audit additionally recovers normal monitor-start and
guarded Instant On caller chains. Neither is an observed standby/wake reset
or a supported recovery command. Do not invoke monitor-start merely to clear
history: its broader initialization and repeat-call behavior are unvalidated.
The QDF debug callback is not the missing gate observer: its exact input
helpers return exit0x99 before reaching the dormant selector0x30 cache dump.
The ordinary path prints its menu/default log and exits. No helper patch,
guessed debug selector or ioctl is part of this observed-session procedure.

The automatic warning now has an exact native path: tv-viewer forced/reinforce
ID0x0f, ongoing countdown, automatic off-sensing request at its60th callback.
For the next onset record, preserve app-control/tv-viewer logs matching
`off.sensing`, `show_qd_display`, `NOTIFICATION_QD`, `1 min timeout`,
`RequestQdDisplayOffSensing`, and `cancel_reinforce` in addition to the
existing AVOC/QDF/Deviced markers. Match notification creation, cancellation
or expiry to the physical edge and actual wire traffic. A60-tick UI request
is not proof that the panel accepted sensing or that it caused the blackout.
Do not invoke a sensing request merely to identify its log signature.

Do not use GetQDDisplayState as a pure-read preflight: its classifier can
acknowledge saved EL/off results. Use the documented direct stored-key reads
and qualified object-state samples instead. Offsensing TEST Period factory
item200802/UID506e is only a candidate: current service0, absent named DB key,
and a code predicate for6. No factory write is part of this capture procedure;
all-route control and setter semantics still need proof.

Also use the [daemon observer map](../tcon-research/deviced-runtime-observer-map.md)
to read EL/off selector and selected local-state fields with G1→object reads
twice→G2. Validate child vptrs and fresh readable maps; support flags or a
nonzero pointer alone do not prove an active object. The11:45:01 sample had
EL0/off0/powerlcdon but no physical-state confirmation. Preserve public getters
separately because they execute outside the memory bracket. Do not invoke
maintenance, suspend or power controls to obtain these observations.
