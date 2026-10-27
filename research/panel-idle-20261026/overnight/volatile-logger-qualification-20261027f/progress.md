# Controller diagnostic logger: actual qualification

Recorded 2026-10-27 UTC. The owner permits active unattended testing and
firmware changes if needed, while retaining the requirement to avoid bricking
the TV. The owner is asleep; the physical panel was not observed in this run.

## What changed

One finite native invocation enabled a volatile controller diagnostic logging
gate, held it for three seconds, restored it, and read back restoration. This
is the first live write in this work block. It did not flash firmware, change
panel protection thresholds, alter EEPROM, reset the panel, open Home, or
change the TV's user settings. No helper or logging gate from this experiment
is left intentionally enabled.

The reviewed build manifest is
`150189300d1fb78507e8dcad330cc1ca2ebbef05617d5741506a062986445b8b`.
The authenticated root record is
`839658033dfd2adf20ded0c1d266df1dd0fa81d47430bbb64121c8118e4d32a4`.
Exact source, native binary, wrapper, transport adapter and supporting
evidence are copied under `reviewed-helper/`. The first wrapper candidate was
blocked before use for insufficient outer timeout margin and is preserved
under `blocked-wrapper-revision/`; see `review-history.md`.

## Actual result

- All 25 authenticated root calls completed, including a separate zero-I/O
  74-test target self-test and exactly one active invocation.
- All 16 USB bulk transfers returned the exact expected counts, with errno
  zero. The final protocol phase was `ReadyForHeader`.
- Fresh full halfword readbacks at secondary RT offset `+6` were `0, 1, 0`.
  The armed 64-byte RT snapshot differs from the initial snapshot only at
  byte 6. Initial and restored 64-byte snapshots are identical.
- The observation hold was exactly 3,000 ms in the helper's monotonic clock.
  Arm was verified at 87 ms, observation ran 88–3,088 ms, restoration was
  verified at 3,093 ms, and the post-ring read completed at 3,097 ms.
  Outer TV uptime framing was 110089.19–110092.56 seconds on the pinned Linux
  boot. These clocks do not provide an emitted-light observation.
- The diagnostic ring header changed from write/read/flag `5/5/0` to
  `11/11/0`. Six bytes in the cursor span read `t[10]\n`. The only changed
  bytes in the complete 15,372-byte object were header offsets 0 and 4 and
  data offsets 17–22. Full wraps cannot be excluded solely from endpoints;
  other retained tail bytes are not treated as new messages.
- The sampled RT fault halfword at `+0x0a` was zero in all three snapshots;
  mode at `+0x10` was four throughout. These were not incident-time samples.
- Interface release, FD close and private-stage removal succeeded.
  `cleanup_deferred` is false and the final authenticated cleanup result is
  `STAGE_ABSENT`.

`audit-smoke-runtime.py` verifies the exact reviewed manifest, staged bytes,
authenticated envelopes, command replay, output artifacts, native counts,
gate readbacks, hold and cleanup entirely offline. It passed. An independent
reviewer replayed it with report writes suppressed, checked the binary
differences directly, and found no blocking issue. The separate
`byte-comparison.json` preserves the bounded byte-level interpretation.

## What this adds to the diagnosis

The secondary controller's diagnostic output can now be enabled and collected
through a tested, finite path without a persisted modification. The gate is
not merely inferred from disassembly: its change and restoration were read
back, and the log object changed during the window. This removes an
instrumentation gap before a future working-to-failing capture.

Earlier owner-observed Apps versus For You and Ugoos playback comparisons
associated blackouts with host `RT Protect` status and an asserted fault
input. They did not identify the initiating controller event. This run did
not reproduce an observed blackout and does not identify that event either.
The [bounded format trace](new-log-format-trace.md) now locates a matching
packaged formatter and its direct numeric producer: an unsigned byte is
incremented, stored, reloaded and printed. This supports a counter-like
mechanism in the selected code, not a temperature or a fault-code label.
Live execution of that exact body is not proved by the text alone.

The working symptom model remains content-dependent panel failure: populated
Apps or an overlay can keep the picture visible, while a sparse page or some
full-screen content can produce persistent black with sound continuing. The
small impact-damaged region and vertical line remain relevant hardware
context. Removing recommendations changed displayed content; it has not been
proved to create a Linux crash or to be the original physical fault.
Brief HDMI/live losses that pause audio and recover may be a separate event.

## Remaining evidence needed

A useful next capture starts from an owner-confirmed visible Apps picture and
clear fault state, enables the qualified logger for a finite window, records
the owner-triggered page/content transition, then restores logging and
collects the ring plus fault samples. Its start marker must be observable
before the owner acts; a synchronous response returned only after capture
cannot be used as a ready signal. Reboot belongs before arming, not inside
an active USB transaction. No next capture is represented as already built
or deployed here.

There is no demonstrated panel recovery, blackout prevention, permanent root
installation or permanent repair from this run. The stored/running firmware
generation discrepancy still prevents treating the first stored image as a
qualified flash target. Owner authorization to flash is retained; no
compatible, recoverable repair image has yet been established.
