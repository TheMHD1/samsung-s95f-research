# Five-second SDP checkpoint: runtime audit

## Verdict

The retained checkpoint is an **accepted, finite static-event/log record**.
It shows no per-CPU trace loss, a five-second uptime-bounded interval, clean
private-instance removal, and no `sdpsoc` event rows.  It does not establish a
panel state, a QD/TCON function call, or a reboot/crash.

| retained item | SHA-256 |
| --- | --- |
| raw client response / trace | `67a23c8d1c00c39aa2c75c2ff52bb40d878b091ec2967b28cacb32bf998566ab` |
| decoded artifact | `01e43a195109336330d6b609db1eae37d5f7f69d212aa65a953cffd8f2e0a42a` |
| exact remote probe | `76c1881452353a5a447351510dc7ba5d8a2d76f59e09327406c767a01b45f0eb` |
| intent | `9992cb08a5cdd44e445510461e0a568176c880b3b7452ef7601dbb32acf150ab` |

No TV/root/network action was taken for this audit.

## Transport, guards, and cleanup

The authenticated root response reports the expected model, `uid=euid=0`,
host-assisted persistence, `global_system_files_unchanged_at_acquisition=true`,
one command with exit code zero, no timeout, and empty host/remote stderr.
The probe itself:

* pins boot ID `00000000-0000-4000-8000-000000000000` before creating a
  unique private trace instance;
* requires global `tracing_on=0` before and after;
* enables only four discovered `sdpsoc` memory events plus `printk/console` in
  that instance, with `nop` tracer and 64 KiB per-CPU buffers;
* uses a shell EXIT/HUP/INT/TERM trap to turn off that instance, disable its
  events, and remove it; and
* retains the trace text and each CPU's stats before verified removal.

The command performs no device-node open, ioctl, controller transfer,
GPIO/rail write, module operation, dynamic-debug change, or global trace
write.  It does change a private tracefs instance temporarily; that is the
intended observability action.

The record says `48/48` entries written and all four per-CPU `overrun`,
`commit overrun`, and `dropped events` counters are zero.  `TRACE_BYTES=7942`
is below the exported `dd` ceiling (two 65536-byte blocks).  Those facts make
this record complete for the selected events during its retained interval;
they do not cover unselected trace events, a suppressed/rate-limited printk,
or an event before/after the window.

## Clock discipline

There are two incompatible timestamp domains:

* `/proc/uptime` brackets the requested window at `92517.48` to `92522.49`
  (5.01 seconds); embedded printk timestamps are in the same approximate
  domain, e.g. `[...92517.6076]` shortly after the start.
* Trace-header/marker timestamps are approximately `92455.976109` through
  `92460.974516`, roughly **61.5 seconds earlier** than the uptime/embedded
  printk domain.

The marker interval itself is about 4.998 seconds, so it validates tracer
duration.  It must not be numerically merged with `/proc/uptime`, prior
onset-capture timestamps, or the bracketed console timestamps without a
separately measured mapping.

## What was observed

* **No selected `sdpsoc` rows:** all 48 records are the two markers or
  `printk/console` rows.  This means the selected memory-event tracepoints did
  not emit in this short interval; it is not a negative census of SDP memory,
  QDF, or TCON activity.
* **Graphics heartbeat:** `S_GFX ... GFX V sync is working fine` appeared
  repeatedly in the embedded printk clock.  Consistent with prior analysis,
  this is a host graphics message, not physical light/emission evidence.
* **One DRM-DP histogram burst:** the console prints Y/R/G/B input-bin values
  plus DE(SAC) and VE(CE_) histograms.  It is evidence only that a stock
  driver emitted formatted histogram text; bin units, source surface, update
  trigger, and relation to QD protection are unknown.
* **One signal row:** at embedded time `92518.8580`, the kernel reports signal
  11 to `.NET ThreadPool(29567)` with a nonzero handler address.  There is no
  retained process exit, kernel Oops, panic, call trace, or reboot evidence.
  The same form recurred in the earlier retained For You window with another
  ThreadPool PID and nonzero handler.  This record does not classify it as a
  crash, intentional CLR fault, or blackout cause.  A later read-only process
  identity record reports PID 29567 still alive/asleep, UID 5001,
  `dotnet-loader`, and 55 threads; that is compatible with handler-based
  signal delivery, but is not same-epoch survival evidence because this
  checkpoint did not retain that process's pre-signal start time/identity.
* Repeated OCL clock/cable, SemRF, audio, bus-monitor, WLAN, and HDMI switch
  lines are contextual stock logs only.  They have no demonstrated causal
  link to the panel event.

## Narrow next source focus

The only newly useful source target is the exact producer of the
`[DRM-DP] [HISTOGRAM INP(...)]` print in the already copied `sdp_drm.ko` and
its immediate data source.  The question is whether those values are input
frame/PQ statistics, a display-output statistic, or a diagnostic snapshot.
That limited static trace can determine field format and caller/gates without
opening a new live interface.  Do not infer brightness, panel current, or
content causality from this single console dump before that binding exists.

The SIG11 text does not justify a broad CLR/crash investigation without a
paired process-lifecycle record or a source-backed signal producer path.
