# Private HDMI resume and OCIF availability follow-up

No incident-aligned fault, permanent prevention, or recovery from a latched
black physical panel is established. The active objective remains unchanged.
This phase adds exact-binary provenance and prepares improved passive capture;
it does not deploy a panel repair. Root remains host-assisted, with untethered
persistence unverified.

## New reconstructed paths

- [Private HDMI resume registration and dispatch](../tcon-research/hdmi-private-resume-dispatch.md):
  the probe supplies suspend/resume callbacks to Samsung's named
  `sdp_runtime_pm_*` mechanism. The saved kernel Image stores and directly
  invokes those callbacks. A conventional-looking PM table has no recovered
  relocation-backed attachment in the acquired module. This means standard
  Linux PM tracepoints alone cannot exclude this private path.
- [OCIF cached-byte producers](../tcon-research/ocif-cache-producer.md):
  the exported “lock” getter returns an availability byte. Probe initializes
  it to zero; a suspend-side path clears the passed object's byte; an
  AckPolling callback path can set it to one after a nonnegative result.
  These are static function/object relationships, not measured physical lock
  or live binding. The generic setter is global but not kernel-exported.
- [Board support boot-input provenance](../tcon-research/serdes-support-boot-provenance.md):
  exact kernel code connects `ffinfo=` to a word read by the module's probe
  initializer. Captured `ffinfo=00000401` conditionally enables the support
  predicate. This does not sample the module's current cache.
- [Stock private-power log markers](../tcon-research/hdmi-private-power-log-markers.md):
  exact IN/OUT strings surround one exported caller's private HDMI get/put.
  The logger calls `trace_early_message`, whose event the existing observer
  already collects. These messages can provide positive context if emitted;
  an OUT row is not hardware success and silence cannot exclude another
  private caller.
- [Resolved AckPolling provider](../tcon-research/ocif-ack-polling.md):
  the newly copied module exports the exact callback. Its message has flags
  zero, length one and a zero data byte: it requests a **write**, despite the
  “check” name. It returns the raw transfer result, and the caller accepts
  any nonnegative result without requiring one completed message. Neither
  callback was invoked for research. This reinforces why cached availability
  cannot be called a direct lock or panel-health measurement.
- [Private PM return/state outcomes](../tcon-research/private-rpm-state-outcomes.md):
  the dispatcher ignores saved callback returns, advances state and increments
  its software use count. Positive-count gets can then skip resume. The HDMI
  callback has a separate context-state gate that can return zero without its
  substantive resume path. Two stock trace messages identify substantive
  resume entry and elapsed-time reporting when emitted. These are candidate
  mechanisms and trace interpretation rules, not incident execution proof.
  The apparent disable helper does not recover output, and its getter-shaped
  record lookup can allocate state; neither was invoked.

The dispatch and OCIF negative-reference checks were hardened to include
named and section-symbol relocations, the explicit unwind-metadata exception,
and fixed-width direct-branch scanning rather than trusting disassembler
coverage. The existing frozen reports and all earlier capture evidence remain
unchanged. Corrections to intermediate offset/export interpretations are
recorded in the new reports.

## Finite new target reads

All newly acquired physical states are **unobserved**. None of these requests
invoked a hardware getter, callback, module load, display control, power
transition, service restart, or firmware/factory write.

| Capture | Same-boot uptime | Result and limitation |
| --- | --- | --- |
| `formfactor-boot-metadata-20261026` | `66546.21..66546.22` | Authenticated root; exact module hash and bounded canonical `/proc/cmdline`; conditional boot input only. |
| `pm-idle-tracepoint-format-20261026` | `67237.64..67237.65` | Read `rpm/rpm_idle` format, ID 129; global trace stayed `0/nop`; no event enabled. |
| `private-rpm-log-baseline-20261026` | `67350.82..67350.89` | Non-clearing `dmesg` snapshot with a bounded filter: zero matching retained rows. This cannot prove no private HDMI transition occurred. |
| `ocif-ack-provider-discovery-20261026` | `67417.25..67417.57` | Two fixed directories, 67 module files; substring matches are discovery only, not definitions, exports, or execution. |
| `serdes-ack-copy-20261026` | `67448.64..67451.27` | Nineteen fixed file chunks reconstruct exact `sdp_ocl_jp.ko`; sequential/non-atomic on-disk evidence, not a live-text or callback-binding read. |

Each remote request reported authenticated UID/EUID zero, model
`QN77S95FAFXZC`, boot `00000000-0000-4000-8000-000000000000`, exit zero,
and no timeout/stderr. Raw intent/client/result sidecars are retained.
The copied callback-candidate module is 594,110 bytes, SHA-256
`e5a064da2cfbd37194f5e97463c3519126a09aedaf4b3c95107b08ab0680aa2c`.
The parent independently reconstructed it from all nineteen raw chunk
responses with the pinned parser and checked the manifest metadata. Its
callback definition and actual kernel export were then verified separately;
the initial substring match was not treated as the resolved export.

## Capture implementation status

The existing accepted pre-roll capture remains frozen and available. A new
PM/RPM extension is implemented in separate files. Its first independently
cleared five-second passive TV smoke was **rejected** by semantic validation;
the run and its exact source are preserved, with cleanup verified.

Review rejected the first candidate before any live attempt because unresolved
early operations could overlap the whole physical window while being labeled
outside. It also showed that omitting `rpm_idle` can misassign a same-task,
same-device idle return to a pending resume. A seventh captured event and
new design addendum address that ambiguity. PID reuse/task identity and the
exact hyphenated `sdp-hdmi` driver name are additional review requirements.

The actual `pm-smoke-20261026t2023.onset` run retained all 10,521 trace events,
with zero per-CPU loss. Its physical window was trace time
`67731.868178..67736.883437`, followed by drain through `67736.990035`.
Two valid CPU-2 idle-context suspend/return pairs triggered the parser's
overly strict positive-PID/numeric-TGID guard. This was an instrumentation
classification failure, not an observed HDMI or panel failure. The raw
record remains `accepted=false`, `technical_capture_complete=false`,
`diagnostic_eligible=false`, with zero owner annotations.

The exact rejected source/tests/addendum are archived under
`observed-pm-rejected-eabe5bde`. Quiesce and cleanup returned successfully;
the authenticated cleanup output was `0` then `CLEAN`, with no collector
stderr and no owned trace/staging/expiry resources left. No automatic retry
was made. A bounded idle-identity correction passed 108 offline tests and
independent review: only runtime
events with exact `<idle>`, PID zero and literal dashed TGID qualify, keyed
by CPU to distinguish idle tasks. Callback/system PID-zero rows remain
rejected. Any offline replay with a corrected parser must remain separate
from the original rejected record.

A separate, independently cleared five-second passive run,
`pm-idle-smoke-20261026.onset`, ran from
`2026-10-26T20:31:09.157769+00:00` through
`2026-10-26T20:31:33.129166+00:00`. It was rejected with
`ValueError: capture completion missing`; partial metadata and other
sidecars are retained. It did not produce an accepted complete trace and
does not validate the parser correction on the TV. Independent offline
[runtime audit](pm-idle-smoke-runtime-audit.md) located the rejection before
physical START: the per-thread sweep encountered syscall 54 on TID 1011 at
uptime `68292.35`, and the generated shell intentionally exited 86 rather
than accept an unanchored operation. The scheduled target was `68293.530`.
The earlier FD snapshot maps fd 33 to `/dev/dri/card0`, but no later FD
snapshot establishes endpoint stability. This is an instrumentation gate,
not a newly observed panel failure or proof of the operation's completion.
Its record
reports `accepted=false`, `technical_capture_complete=false` and
`diagnostic_eligible=false`, with zero physical annotations. Authenticated
cleanup returned exit zero, stdout `0\nCLEAN\n`, and empty stderr;
quiescence and cleanup were verified. No automatic retry was launched.

The [bounded pre-start quiescence review](pm-prestart-quiescence-review.md)
recommends retaining and retrying an intermediate numeric syscall-54 row
within the existing eight-attempt/two-millisecond and absolute half-second
prelude bounds. Only a later numeric non-54 point sample could qualify that
thread; an unanchored trace exit cannot substitute. Independent review
cleared the design only. A derivative implementation is a separate pending
work item, and this design neither accepts the failed run nor clears a new
TV capture.

The upstream reference for the nested idle call is
[Linux v5.4 runtime PM implementation](https://raw.githubusercontent.com/torvalds/linux/v5.4/drivers/base/power/runtime.c):
`rpm_resume` invokes `rpm_idle` before its generic return event. This is a
framework reference, not proof that the vendor kernel executed that path at
the owner's blackout. The vendor event's captured format supplies the actual
acquisition contract.

Neither passing offline tests nor an eventual passive smoke can establish
physical panel behavior. A full owner-observed visible-to-black transition,
with aligned raw evidence and subsequent reboot/prevention and recovery
tests, remains necessary before calling any candidate a repair.
