# Combined observed onset capture: requirements from independent review

The current25second diagnostic trace does not encompass a complete force
notification's intended60ticks. A separate runtime snapshot cannot execute
during the same blocking serialized root call. Thus neither the old control/
black pair nor a quiet short trace identifies a maintenance producer or an
intermediate monitor clear/re-set. Physical emission still needs an observer.

Prepare one new default-dry observer, `observed-onset-capture.py`, with these
requirements. No unobserved capture may claim a physical state. No remote key,
setter, ioctl invocation, power action, active QD getter or service restart.

1. One85–90second collector shell, launched as an owned detached process
   group through a short persistent-only command, with bounded status polls.
   The controller accepts at most120seconds per command and its serial gate
   prevents a second command cancelling a still-blocking capture. Killing the
   local client is not cancellation. Require PID/start/group guarded stop and
   finite private cleanup independent of the host connection.
   Modeled test fixtures may use a shorter interval;
   a real maintenance-expiry classification requires full coverage. Root/model/
   source hash/boot/PID/exe/startticks/maps and pointer chains are verified at
   start/end. Record realtime/uptime synchronization and trace markers.
2. Private mono-clock trace instance with an explicit total-memory budget:
   buffer_size_kb is per CPU, so4096KiB across four CPUs is about16MiB,
   subject to the actual buffer_total_size_kb readback. Existing bus5/address118 I2C
   write/read/reply/result, early_trace, CRTC1 vblank, GPIO/clock/regulator,
   process exec/exit, and raw ioctl syscall enter/exit for captured AVOC TIDs
   (ARM32 ioctl54 for the exact captured AVOC; native ioctl29 is not applicable
   to those threads). Save AVOC fd targets. A generic
   ioctl number does not decode its user buffer or establish MCU acceptance.
3. A bounded sampler inside that same shell reads the already-audited AVE
   monitor counter/latch/fault/restart/on/previous block about5Hz; QD userspace
   cache/duty and selected deviced object state about1Hz. Every row has TV
   uptime and raw bytes/words. No kernel-gate state is invented from userspace
   fields. Validate ranges/identities/pointers; retain raw failure. Before/
   after validation alone cannot prove a pointer never changed mid-interval.
4. Preserve unfiltered `vlogutil -v kerneltime` logs for the full capture plus
   margin, with lengths/hashes/limits. Inspect available timestamp coverage
   locally; incomplete coverage cannot support absence of a warning/request.
   Match viewer/app-control countdown/request/cancel and Deviced/AVOC/QDF
   markers while preserving full source. Time-window option semantics must be
   established from captured usage/source rather than guessed. Subsequent
   installed help and a real2second sample now establish that contract in
   [vlog-capture-contract.md](vlog-capture-contract.md). That sample is936079
   stdout bytes/6327 records; plan bounded streaming/coverage rather than
   assuming a90second retrospective dump fits the finite history.
5. Baseline/end read-only HWC/software-frame/FRC irq_status artifacts may use
   already established interfaces. Avoid HDMI crc and QD getters that add wire
   traffic or have known PM defects. These artifacts do not measure emitted
   light or timestamp the physical transition.
6. Local observer annotations, accepting host UTC while the remote call is
   running, identify visible Apps, warning-visible, and black/audio state.
   They require no second root call. Keep reaction and clock uncertainty;
   never derive the physical label from a PNG or getter.
7. Verify retained/written trace count, decode completeness, every sidecar's
   exact length/hash/max size, exact private-instance/file cleanup, and
   unchanged global tracing settings. No automatic retry. Keep partial results
   with explicit failure/incompleteness rather than classifying absence.

## Decision limits

Ordered countdown expiry/request and F3:0180 can associate an automatic
maintenance request with the incident, without alone proving physical cause.
A request plus a specific QDF gate/skip log and no wire narrows suppression;
without such a marker, a missing transaction remains ambiguous.

Fresh monitor counter/restart/latch transitions plus ERR_DET, recovery or
terminal-action evidence distinguish an actual monitor action from repeated
history reports. A latch1 seen in both visible and black states is not a new
off command on each log line. Sampled gaps can still hide transitions.

A physical black edge with continued composed frames/vblank/FRC progression
and no captured host off/mute/maintenance/terminal signature narrows the loss
to after composition. Tracepoint absence covers only enabled Linux APIs and
cannot prove a particular rail/MCU/OLED failure. If multiple signatures occur,
preserve ordering rather than forcing one cause.
