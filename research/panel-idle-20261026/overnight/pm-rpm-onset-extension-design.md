# Passive PM/RPM trace extension for a future onset observer

Status: design only. This file does not modify or reinterpret the accepted
pre-roll observer, its tests, its design, archives, or retained captures. It
authorizes no TV, root, network, trace, power, service, display, or device
action.

## Question and bounded purpose

The proposed extension adds six existing Linux PM-framework tracepoints to a
future revision of the private-instance onset trace:

- `power/device_pm_callback_start`
- `power/device_pm_callback_end`
- `power/suspend_resume`
- `rpm/rpm_resume`
- `rpm/rpm_suspend`
- `rpm/rpm_return_int`

The only new conclusion these events can support is positive, time-bounded
framework activity: a named device/driver entered a printed PM action, a
matching printed callback returned with an error value, a named runtime-PM
operation began, or its matching framework return was recorded. The extension
does not call a PM callback, query device state, or observe an internal vendor
function directly.

The hash-gated static report
[`serdes-probe-resume-path.md`](../tcon-research/serdes-probe-resume-path.md),
SHA-256 `7601c32b11800cb3d53fb37cd7e01a096386de5b9db475f1402d883e5ea29552`,
establishes two positive relocation-backed callers of the dynamic SerDes-lock
wrapper: `.text+0x4cd4` inside `sdp_hdmi_resume_fxn` anchored at
`.text+0x48f8`, and `.text.unlikely+0x13b8` inside `sdp_hdmi_probe`. The helper
permits up to 300 requested ten-millisecond sleeps **per invocation**, plus
callback and scheduler overhead. The resume outer loop can invoke the helper
again and has separate exit logic, so neither an exact three-second timeout nor
a whole-path duration bound is established. This document does not rederive
those anchors or equate a framework trace row with execution of either call.
The callback registration must remain bound to its separate source analysis
before any report names the internal path.

## Evidence and source binding

The authoritative trace-format acquisition is
`overnight/pm-tracepoint-formats-20261026/remote-stdout.txt`, SHA-256
`97581bdd24c81dbd69e3c5edd6fef81b071d31284d95bc0cd203b98c3db5ad4e`.
It was read on boot
`00000000-0000-4000-8000-000000000000`, between monotonic uptimes
`65493.04` and `65493.05`. Its global trace baseline was `tracing_on=0` and
`current_tracer=nop`. The acquisition only read the six format files and the
global baseline; it did not enable an event.

The matching acquired HDMI module is:

- `/lib/modules/5.4.261/kernel/soc/sdp_hdmi.ko`
- size `3,299,534` bytes
- SHA-256 `f7cffd19934ef459b0263ceddddf003306b399e01d0ddee48df3f64a86667994`

A future implementation must embed the exact six captured format texts, not
only event names or IDs. Before configuring its private instance it must:

1. retain the six live format files verbatim;
2. require exact equality to the reviewed format contract, including field
   offsets, widths, signedness, IDs, and print formats;
3. retain the boot ID, kernel release, trace clock, global trace endpoints,
   and the already-required process/module identities; and
4. refuse PM semantic classification if the format contract differs.

Tracepoint IDs (`119`, `120`, `121`, `127`, `130`, and `131` in the acquired
build) are provenance, not portable identifiers.

## Exact printed fields and permitted interpretations

| Event | Captured printed body | Normalized fields | Narrow interpretation |
|---|---|---|---|
| `device_pm_callback_start` | `driver device, parent: parent, pm_ops[event]` | raw strings `driver`, `device`, `parent`, `pm_ops`; symbolic event | The PM framework emitted a callback-start row for these printed identities and action. |
| `device_pm_callback_end` | `driver device, err=N` | raw strings `driver`, `device`; signed `error` | The PM framework emitted a callback-end row with this printed return value. |
| `suspend_resume` | `action[val] begin|end` | raw action, unsigned printed `val`, phase | A system suspend/resume trace phase began or ended; it is not a device callback. |
| `rpm_resume` | `name flags-X cnt-N dep-N auto-N p-N irq-N child-N` | device name, hexadecimal flags, six signed integer state fields | The runtime-PM resume entry tracepoint captured this framework state snapshot. |
| `rpm_suspend` | same field grammar as `rpm_resume` | same | The runtime-PM suspend entry tracepoint captured this framework state snapshot. |
| `rpm_return_int` | `ip:name ret=N` | raw rendered IP/symbol prefix, device name correlated from a pending entry, signed return | A runtime-PM framework operation returned; the event alone does not encode resume versus suspend. |

The parser must retain every complete raw event body in addition to normalized
fields. It may normalize repeated padding spaces in the RPM numeric layout,
but it must not rewrite names or symbol text.

Dynamic strings in formatted ftrace text are not length-delimited after
rendering. A future parser must therefore be conservative:

- device/driver/name tokens qualify for semantic parsing only under a reviewed
  unambiguous token grammar; otherwise the row remains raw and the PM semantic
  extension is incomplete;
- `device_pm_callback_start` is parsed from its exact final `[event]`, then the
  fixed `, parent: ` and final `, ` delimiters; the event must be one of the
  eight symbols in the captured format;
- the matching callback end must repeat the exact driver and device strings;
- `rpm_return_int` is first split from the right at exact ` ret=SIGNED`. The
  pending runtime entry supplies the exact `name`; the remaining prefix must
  end in `:` plus that name. The preceding text is retained as `ip_raw` rather
  than assumed to be a trustworthy resolved function; and
- any delimiter ambiguity, unknown symbolic action, overflow, non-finite
  timestamp, or malformed signed/hexadecimal field rejects PM semantic
  completeness. Raw preservation does not turn an ambiguous row into proof.

## Private-instance acquisition contract

The future implementation must derive from the independently accepted
pre-roll observer and preserve its source hashes, private namespaces, staged
script identity, exact TID/syscall quiescence, five markers, sampling, vlog,
annotations, watchdogs, cleanup, and no-control behavior.

Only these trace configuration changes are proposed:

1. In the new private trace instance, set each of the six event `enable` files
   to `1`. Never write a global trace event, tracer, buffer, clock, or
   `tracing_on` control.
2. Do not install an unreviewed name filter. The formatted device identity is
   part of the evidence, and filtering before exact live names are known could
   silently discard relevant context.
3. Read back and retain all six enables plus all six format files after
   configuration. Re-read their enables and retain every
   `per_cpu/cpu*/stats` file before teardown. A missing event, differing
   readback, nonzero overrun/drop statistic, or missing CPU statistic rejects
   the extension.
4. Start and stop tracing at the existing TRACE_ARMED and DRAIN_END lifecycle.
   The physical and owner-observation window remains exactly
   `CAPTURE_START..CAPTURE_END`; no marker moves.
5. Preserve raw rows before semantic parsing. The existing requirement
   `entries-in-buffer == entries-written == decoded event rows` remains
   mandatory. Any loss rejects the entire technical capture, not merely the PM
   addendum.

No kprobe, function tracer, function-graph tracer, perf/BPF program, ioctl,
sysfs power write, active getter, callback invocation, key, service action, or
module load/unload is allowed. Stock tracepoint enablement inside the owned
private instance is the entire acquisition change.

## Region and lifecycle accounting

Every PM/RPM row is assigned by trace line order to the accepted observer's
regions: `enable-slop`, `trace-prelude`, `pre-roll`, `capture-window`, `drain`,
or `post-drain`. Marker rows are never PM rows. Counts are reported by event,
region, CPU, task PID, and normalized identity when parsing is unambiguous.

Three independent state machines are required:

### Device callback pairs

Maintain an ordered per-task stack of callback starts. An end qualifies only
when the stack top has the same driver and device. Preserve start/end lines,
times, CPUs, task identity, parent, PM-ops text, action, duration, and signed
error.

- a pre-roll start ending in the physical window is a separately reported
  start-boundary callback;
- a physical-window start ending in drain is a separately reported tail
  completion;
- a start from enable-slop/trace-prelude ending in the physical window is
  unbounded and rejects PM semantic completeness;
- an orphan end in the physical window or drain rejects;
- a pending callback that overlaps the physical window at DRAIN_END rejects;
  and
- outside-only and drain-only pairs are retained and excluded from physical
  counts.

This pairing proves only that both framework tracepoints were retained. An end
with `err=0` is the callback's printed framework result, not proof that every
internal hardware check passed.

### System suspend/resume phases

Pair exact `action`, `val`, and begin/end rows with a per-task ordered stack.
Report complete intervals, orphan ends, pending begins, cross-boundary flags,
and raw action values. Do not infer a full system sleep/wake cycle from one
action pair; the action vocabulary and nesting are kernel-controlled.

### Runtime-PM operations

Push `rpm_resume` or `rpm_suspend` entries on a per-task ordered stack. A
`rpm_return_int` closes only the current top entry when its suffix contains the
same exact device name. Retain entry flags and state fields, operation kind,
raw IP/symbol prefix, duration, and signed return. A mismatched, orphan,
duplicate, or cross-cutoff return must not be forced onto an entry.

`rpm_return_int` is a generic return event and the selected six-event set does
not include `rpm/rpm_idle`. An unmatched return can therefore belong to an
unrecorded runtime-idle entry; it is retained as
`unassigned_return_unknown_operation` and is not, by itself, evidence of trace
loss or a resume/suspend lifecycle error. It cannot support a resume, suspend,
or absence claim. A pending recorded resume/suspend entry that overlaps the
physical window at DRAIN_END still rejects, as does any attempt to close that
entry with a mismatched name; the unassigned return remains a separate row.

The state machines do not merge the three event families. A runtime-PM resume,
a system `suspend_resume` phase, and a device callback near one another are
reported as temporal neighbors unless their own pairing rules prove more.

## Positive `sdp_hdmi` correlation

A report may call a callback pair an `sdp_hdmi framework callback` only when
the trace itself contains an exact reviewed driver identity for `sdp_hdmi`, a
specific device, a recognized `resume` action, and a matching end row. It must
show the raw identity and signed error. Static association with the acquired
module additionally requires the pinned module/source contract; the printed
driver name alone is not a binary hash.

For each positive pair, report:

- start/end monotonic trace clocks and region;
- device, driver, parent, PM-ops label, action, duration, and error;
- overlapping/nearest runtime-PM and system phase records without merging
  their semantics;
- signed distance to each uncertainty-expanded owner annotation interval; and
- whether the callback started before, within, or after the physical window.

The report must use language such as “a framework resume callback for the
printed sdp_hdmi identity overlapped the owner-annotated interval.” It must not
say that SerDes lock polling ran, that a lock failed, that the HDMI module
cycled power, that the panel went black, or that the callback caused the
observation. A duration near three seconds is not proof of the statically
identified poll loop.

## Absence and causality limits

`absence_claim_supported` remains `false` for the entire capture. In
particular, zero matching rows means only:

> No matching rows from these six enabled PM/RPM framework tracepoints were
> decoded in the retained interval.

It never means that `sdp_hdmi` did not resume, did not poll SerDes, or did not
change hardware state. These tracepoints do not cover, among other paths:

- direct vendor callbacks or function calls that bypass these framework
  tracepoints;
- vendor ioctls, custom workqueues, timers, IRQ-driven recovery, firmware, or
  autonomous hardware behavior;
- a callback already in flight before tracing that emits no retained start or
  end during the interval;
- internal branches within a traced callback, including the dynamic SerDes
  callsite; or
- state changes represented by other kernel, userspace, or hardware APIs.

The pre-roll reduces some boundary ambiguity but cannot turn generic PM silence
into negative proof. Owner annotations remain the sole physical-state source.

## Resource and ring-budget gate

The accepted observer currently budgets `4096 KiB` per CPU, no more than
`16384 KiB` total, and fails on any ring loss. Adding six global framework
events changes the event mix and must receive a separate capacity review; their
apparently low idle rate is not evidence of their rate during a resume burst.

Before any full observed run, a future implementation must provide:

1. exact generated-shell and trace-config hashes and all inherited offline
   tests;
2. a reviewed five-second, zero-annotation, passive smoke with the six events,
   used only to validate format, parser, cleanup, and baseline volume;
3. per-event/per-CPU counts, maximum formatted row length, total PM formatted
   bytes, total trace events/bytes, retained/written counts, and ring occupancy
   from that smoke;
4. a conservative 90-second capacity calculation combining the accepted
   observer's measured per-CPU load with the measured PM rows and an explicit
   resume-burst allowance justified from positive evidence—not an arbitrary
   post-hoc factor; and
5. independent confirmation that the unchanged trace and sidecar limits retain
   headroom. If evidence cannot justify the burst allowance, full-run
   clearance remains blocked rather than increasing buffers or weakening loss
   checks.

The private per-CPU/total ceiling, tmpfs and `MemAvailable` minimums, trace
sidecar limit, controller deadline, staging command ceiling, and cleanup
deadlines remain unchanged unless separately reviewed. Regardless of a budget
projection, a live `retained != written`, decoded-count mismatch, truncated
sidecar, or event timestamp reversal rejects.

## Proposed report schema

```json
{
  "pm_extension": {
    "format_contract": {
      "source_sha256": "97581b...",
      "six_formats_exact": true,
      "private_enable_readback": true
    },
    "counts_by_event_region_cpu": {},
    "device_callback_pairs": [],
    "system_phase_pairs": [],
    "runtime_pm_pairs": [],
    "unmatched": [],
    "malformed_rows": [],
    "sdp_hdmi_positive_correlations": [],
    "semantic_complete": true,
    "absence_claim_supported": false,
    "limits": [
      "framework tracepoints do not cover direct vendor paths",
      "positive timing is not causation",
      "software does not label physical panel state"
    ]
  }
}
```

Each normalized pair must retain its raw row bodies and source line numbers.
The top-level technical capture can be accepted only when the existing trace,
sample, vlog, observer, identity, and cleanup contracts pass and this extension
has no loss or relevant ambiguity. Diagnostic onset eligibility still requires
the existing ordered, uncertainty-qualified, wholly in-window human
visible-to-black transition.

## Required offline and passive validation before implementation use

1. Pin the six complete acquired format texts and reject missing, changed, or
   duplicate fields, IDs, print formats, enable readbacks, and event rows.
2. Provide valid and adversarial printed-body fixtures for all six events,
   including signed errors/returns, padded RPM fields, delimiter ambiguity,
   unknown actions, malformed hex flags, and overflow.
3. Test callback pairing by task, exact identity, nesting/order, nonzero error,
   pre-roll-to-window, window-to-drain, orphan end, pending overlap, and
   unbounded prelude start.
4. Test system phase begin/end pairing without assuming that one pair is a
   complete sleep/resume cycle.
5. Test runtime resume/suspend entry-to-return pairing by task and exact name,
   including colons in raw symbol text, name mismatch, nesting, negative
   return, and cutoff ambiguity. Test that an unmatched generic return is
   preserved as an unknown-operation return (including the omitted
   `rpm_idle` possibility), never synthesized into a resume/suspend pair.
6. Prove START..END event, sample, vlog, and annotation counts are unchanged by
   pre-roll/drain PM rows. Pre-window owner context alone remains ineligible.
7. Reject ring overflow, decoded-count mismatch, timestamp reversal, malformed
   PM rows, wrong trace source, lifecycle ambiguity, and incomplete relevant
   pairs. Preserve all raw failure evidence.
8. Test zero PM rows and unmatched outside-only rows produce no absence or
   no-cycle claim.
9. Test a positive printed `sdp_hdmi` resume pair yields only the narrow
   framework correlation, and that a near-three-second duration still does not
   assert SerDes polling or physical effect.
10. Re-run every accepted pre-roll-observer regression: no setters/getters,
    private tracing only, source/identity/maps/pointers, exact syscall filters,
    quiescence, five markers, owned child cleanup, controller bounds, raw 1901
    preservation, annotation ambiguity, and cleanup downgrades.

No implementation or passive smoke is authorized by this design. Exact-byte
independent review is required before either.
