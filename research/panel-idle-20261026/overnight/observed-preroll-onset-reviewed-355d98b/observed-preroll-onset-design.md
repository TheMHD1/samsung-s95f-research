# Bounded trace pre-roll for observed onset capture

Status: design only. This document proposes a new observer revision; it does
not modify or reinterpret the frozen observer, the branch observer, archives,
or retained captures. It authorizes no TV, root, network, trace, or physical
action.

## Problem and evidence anchor

The retained `branch-smoke-20261026t1901` trace is complete at the ring level
(`9750/9750`) but correctly fails the frozen start-boundary rule. The exact
ARM32 AVOC sequence is:

- TID 1011, saved TGID 706, `AVEMonMain`;
- `sys_enter NR 54` at trace time `62733.646733`;
- raw arguments `21, c010643a, f4efe4ac, f50e, 0, f4efe4ac`;
- owned `CAPTURE_START` marker event at `62733.650478`, with body uptime
  `62733.64`;
- `sys_exit NR 54 = 0` at `62733.651341`.

Tracing had already retained about 0.968 seconds before START: its first event
is at `62732.682366`. An orphan TID1011 exit at `62732.683683` proves tracing
was enabled while an earlier call was already in flight, but that return is
about 0.967 seconds before the physical window and cannot describe window
absence. At the other boundary, a complete call enters at `62738.685067`
before END, crosses END at line 9646, and returns at `62738.689704`; the frozen
post-END drain already handles that symmetry.

The entry and return are both retained and ordered, but the call began before
the physical capture marker. Accepting it as an ordinary in-window call would
erase a real boundary. Rejecting every such fully recorded call makes a start
race likely for busy AVOC threads. The proposed solution is a declared,
bounded, separately accounted trace pre-roll. It makes a full boundary pair
classifiable without moving `CAPTURE_START` or treating pre-roll as physical
observation.

## Non-goals and invariants

- The physical and human-observation window remains strictly
  `CAPTURE_START .. CAPTURE_END`.
- The existing post-END syscall drain remains bounded and unchanged in
  purpose. Pre-roll does not lengthen it.
- An entry missing before the retained trace that can overlap START, an
  unreturned call entered in pre-roll/window (or otherwise overlapping the
  physical window), a trace drop, ambiguous PID/TID lifecycle, or unstable
  relevant FD remains a rejection. A call entered only after END may remain
  pending at drain cutoff under the existing reported/excluded drain-only rule.
  This is not a waiver for an unmatched physical-overlap row.
- Pre-roll software activity cannot establish picture state, warning state,
  panel light, absence of an event, policy choice, or causation.
- The raw syscall-54 filter, ARM32 qualification, private trace instance,
  source hashes, pointer/process guards, ring accounting, sampled-state rules,
  and cleanup rules remain fail-closed.
- No key, getter, setter, ioctl invocation, device action, service action, or
  retry is added.

## Proposed acquisition sequence

The sequence below is relative to the already scheduled target uptime. The
implementation must use TV monotonic uptime, never wall clock, for waits.

1. Perform the existing source, process, maps, memory-range, resource, TID, and
   initial FD guards while private tracing is off.
2. Build and read back identical ARM32 `id == 54 && common_pid == ...` enter and
   exit filters from `TIDS_PRE`. Enable unfiltered sched fork/exit events before
   tracing starts, as today.
3. Begin this arming sequence early enough (nominally target minus 1.75 seconds)
   to accommodate the bounded 0.500-second prelude and still provide at least
   0.750 seconds of declared pre-roll. Use shell builtins to read uptime
   immediately before and after setting the
   private `tracing_on=1`; require the enable bracket to be finite, ordered, and
   no wider than 50 ms. Immediately write an owned
   `CAPTURE_TRACE_ARMED utc=<integer> uptime=<post-enable-mono>` marker. The
   trace-event clock and marker body must agree within the existing 100 ms
   tolerance. This records rather than assumes the start of the trace prelude.
4. Enumerate `TIDS_ARM` and require `TIDS_START == TIDS_PRE == TIDS_ARM`.
   Perform one read-only quiescence sweep over exactly those sorted TIDs by
   reading `/proc/$ap/task/$tid/syscall`. Preserve every attempt and its uptime.
   Literal `running` is indeterminate, not evidence of quiescence: retry it at
   most eight times for that TID with a predeclared 2 ms interval, while also
   enforcing the global 0.500-second prelude ceiling. Qualification requires a
   terminal raw row beginning with a parseable signed numeric syscall other
   than 54 for every exact PRE TID. Numeric 54 rejects immediately. Exhausted
   `running`, read failure, malformed output, duplicate/missing TID, or TID-set
   change after the sweep rejects. These counts and intervals are fixed before
   an incident and may not be relaxed afterward. A pre-trace ioctl still in
   flight must therefore be sampled as numeric 54 or remain indeterminate and
   fail; a call beginning after its qualifying sample has a retained enter.
5. Any PRE-parent fork or PRE-TID exit from the first retained row through
   `CAPTURE_DRAIN_END` rejects the run. Record an exact `FDS_PREROLL` snapshot,
   then write an owned
   `CAPTURE_PREROLL_START utc=<integer> uptime=<mono>` trace marker. This marker
   is emitted only after the ARM TID check, quiescence sweep, post-sweep TID
   equality, and FD snapshot succeed. Accept only when the TRACE_ARMED to
   PREROLL_START event-clock duration is finite, positive, and at most 0.500
   seconds. Record the bracket, marker clocks, sweep start/end, and duration.
6. Wait until the unchanged scheduled target and write the existing exact
   `CAPTURE_START`. The requested pre-roll is 1.000 seconds. Accept only a
   marker-to-marker duration from 0.750 through 1.250 seconds; record the actual
   duration. A late start or out-of-bound pre-roll rejects the run.
7. Run the physical window, `CAPTURE_END`, 100 ms return drain,
   `CAPTURE_DRAIN_END`, trace disable/export, and end guards exactly as before.
   Record `FDS_END` without reducing the existing start/end inventories.

Rows from `CAPTURE_TRACE_ARMED` to `CAPTURE_PREROLL_START` form a bounded
`trace-prelude`. Rows in the small enable-to-TRACE_ARMED bracket are separately
counted as `enable-slop`; tracefs does not offer an atomic enable-and-marker
operation. The 50 ms monotonic bracket, complete ring, quiescence sweep, and
lifecycle checks are all required; the slop is never treated as pre-roll. These
rows expose in-flight calls and lifecycle races, but a call originating before
PREROLL_START may not be promoted to a bounded start-boundary pair.

The exact marker contract becomes:

1. `CAPTURE_TRACE_ARMED`
2. `CAPTURE_PREROLL_START`
3. `CAPTURE_START`
4. `CAPTURE_END`
5. `CAPTURE_DRAIN_END`

All five must appear exactly once, in order, with the same trace event token
(`tracing_mark_write` or one identical hexadecimal IP), numeric finite ordered
trace clocks, owned collector PID and saved TGID, exact body grammar, and body
uptime within 100 ms of the event clock. The metadata synchronization anchors
must bracket all five.

## Region and pairing state machine

Region assignment uses marker line order, not the rounded body uptime:

- `enable-slop`: retained row before `CAPTURE_TRACE_ARMED`;
- `trace-prelude`: strictly between TRACE_ARMED and PREROLL_START;
- `pre-roll`: strictly between PREROLL_START and START;
- `capture-window`: strictly between START and END;
- `drain`: strictly between END and DRAIN_END;
- `post-drain`: after DRAIN_END.

Every enter and exit from TRACE_ARMED through drain must have numeric saved
TGID 706 (the independently validated AVOC PID for this example) and a TID in
the exact PRE filter set. Enable-slop syscall rows are parsed and retained; any
one that remains paired across START rejects as unbounded. Pairing is per TID,
ordered, and non-nesting. Raw enter arguments and signed return values are
retained.

| Enter | Exit | Classification | Acceptance effect |
|---|---|---|---|
| enable-slop or prelude | prelude or pre-roll, before START | `outside_or_unbounded_context` | report; not a window pair |
| enable-slop or prelude | window or drain | `unbounded_start_overlap` | reject |
| pre-roll | pre-roll | `preroll_complete` | report; exclude from physical counts |
| pre-roll | window | `start_boundary_completed_in_window` | accept as a fully recorded overlap; report separately |
| pre-roll | drain | `start_boundary_completed_in_drain` | accept only when fully closed by DRAIN_END; report both `crosses_start` and `crosses_end` |
| pre-roll | unresolved at DRAIN_END | `start_boundary_unresolved` | reject |
| window | window | `window_complete` | existing relevant pair |
| window | drain | `window_tail_completed` | existing bounded tail completion |
| window | unresolved at DRAIN_END | `window_unresolved` | reject |
| drain | drain or pending at cutoff | `drain_only` | report/exclude under existing rules |

An orphan exit before START is retained as unmatched outside context and cannot
support an absence claim. The quiescence sweep must still show that no
unobserved NR54 remains in flight before PREROLL_START. An orphan exit in the
window or drain rejects because its entry may have begun before the bounded
pre-roll. Duplicate enters, TGID
changes, reversed pairs, malformed syscall IDs, or a pair crossing the drain
cutoff reject. Rows after DRAIN_END are reported but cannot close an earlier
pending call.

At DRAIN_END, pending entries from enable-slop, prelude, pre-roll, or window
reject. A pending entry whose enter is strictly drain-only remains explicitly
reported/excluded, matching the frozen drain contract.

`start_boundary_completed_*` is deliberately not added to
`window_originated_pairs`. It is evidence that a known call overlapped the
physical boundary, not that the request began during physical observation.

## ARM32 request and FD attribution

For every validated AVOC `NR 54` enter, parse exactly the retained six ARM32
register tokens as hexadecimal values. Preserve the original argument string
as well as normalized `fd`, `request`, third argument, and remaining registers.
Only the validated ELF32 AVOC scope permits calling syscall 54 `ioctl`; no such
meaning is assigned to unrelated/native rows.

The FD snapshots must retain their complete raw `fd -> target` maps at
`FDS_START`, `FDS_PREROLL`, `FDS_ARM` (if distinct from PREROLL), and `FDS_END`,
not only a boolean change summary. For a start-boundary pair:

- the numeric FD must exist at `FDS_PREROLL`;
- its target must be identical at PREROLL and END, and at ARM if that separate
  snapshot is retained;
- a missing, changed, or reused relevant FD rejects boundary eligibility;
- the known endpoint equality still cannot prove that the FD did not close and
  reopen to the same target between snapshots, so that limit remains explicit.

Request labels are conditional on both request and guarded FD target. For the
1901 pair, fd `0x21`/33 maps to `/dev/dri/card0` and request `0xc010643a` may be
reported as the public DRM wait-vblank request. The established
`/dev/sdp_pqe_dp` plus `0xc004510a` combination may be reported as the PQE query
event request. Every other combination remains raw. A label does not establish
kernel completion semantics beyond the retained return, downstream policy, or
physical effect.

## Accounting and output schema

The report should contain counts and full records, not only a single
`complete` flag. A minimal schema is:

```json
{
  "trace_windows": {
    "trace_enable_bracket": [0.0, 0.0],
    "trace_armed": 0.0,
    "preroll_start": 0.0,
    "capture_start": 0.0,
    "capture_end": 0.0,
    "drain_end": 0.0,
    "preroll_duration_seconds": 0.0,
    "prelude_duration_seconds": 0.0,
    "physical_window_unchanged": true
  },
  "syscall54": {
    "window_originated_pairs": [],
    "window_tail_completed_pairs": [],
    "start_boundary_pairs": [],
    "preroll_complete_pairs": [],
    "drain_only_pairs": [],
    "outside_pairs": [],
    "unmatched_by_kind_and_region": {},
    "request_fd_counts": {},
    "pending_at_drain_end": []
  },
  "scope": {
    "filter_tids": [],
    "tid_sets_equal": true,
    "avoc_forks": [],
    "avoc_exits": [],
    "syscall_quiescence": {
      "tids": [],
      "attempts_by_tid": {},
      "terminal_numeric_rows": [],
      "active_nr54": [],
      "indeterminate_exhausted": [],
      "max_attempts_per_tid": 8,
      "retry_interval_seconds": 0.002,
      "duration_seconds": 0.0,
      "complete": true
    },
    "relevant_fd_targets_stable": true
  },
  "ring": {
    "retained": 0,
    "written": 0,
    "decoded": 0,
    "dropped": 0,
    "complete": true
  },
  "event_counts_by_region": {},
  "absence_claim_supported": false
}
```

Each pair record includes TID, saved TGID, enter/exit line and timestamp,
duration, both regions, raw and normalized arguments, signed return, FD targets
at every snapshot, whether the target was stable, and whether completion was
after END. A pre-roll-to-drain pair sets both `crosses_start=true` and
`crosses_end=true`; it is never silently merged with either ordinary window
pairs or window-originated tail pairs. `dropped` is zero only when retained equals written and decoded event
rows equal retained. Any nonzero or unparseable accounting rejects the run.

I2C inventories, annotations, monitor/branch samples, and vlog summaries remain
strictly START..END. Drain and pre-roll rows get separate counts. Neither
bracketing nor a fully paired boundary request makes generic event absence
provable; `absence_claim_supported` remains false.

## Owner-observation contract

The operator should trigger the capture only after visually confirming the
intended visible control state and entering a timestamped annotation during the
scheduled countdown. That pre-window annotation is retained as setup context;
it does not satisfy physical-onset eligibility. The existing requirement for
an ordered, uncertainty-qualified `picture visible -> picture black`
transition wholly inside START..END remains unchanged. Software samples and
pre-roll events never fill a missing human observation.

## Required offline tests before implementation review

1. Exact five-marker ownership, source-token, grammar, order, clock, the 50 ms
   trace-enable bracket, at-most-0.500 second prelude, and 0.750..1.250 second
   pre-roll bounds; missing/duplicate/wrong collector and
   too-short/too-long fixtures reject.
2. A synthetic pair entering pre-roll and returning in-window is accepted only
   as `start_boundary_completed_in_window`; raw args and return must be exact
   and physical event counts must not include its enter.
3. Pre-roll enter/drain return is separately classified with both boundary
   flags; unresolved at drain rejects. Window enter/drain return keeps the
   existing tail contract.
4. Enable-slop/prelude enter followed by a window return, orphan exit in
   window/drain, duplicate enter,
   reversed/TGID-changed pair, wrong syscall ID, malformed six-register enter,
   and post-drain attempted closure all reject.
5. Prelude orphan exit that completes before START is counted but cannot become
   a boundary pair or absence proof. A quiescence fixture with any PRE TID
   reporting syscall54 rejects, as do unreadable, malformed, duplicate, missing,
   or changed TID rows. Literal `running` is retained only as a retry attempt;
   one or eight `running` rows with no terminal numeric non-54 row never
   qualify. Tests cover success after bounded `running` retries and rejection on
   exhaustion. A modeled call that began before tracing and remains active at
   the sweep must be caught as 54 or indeterminate; a call beginning after its
   qualifying numeric sample must have a trace enter.
6. Exact filter TIDs must equal PRE; START/PRE/ARM/post-sweep/END sets must match. Any
   PRE-parent fork or PRE-TID exit anywhere from tracing-on through drain
   rejects, including during pre-roll.
7. Relevant FD missing at PREROLL, changed at END, mapped to a different device,
   or request/FD target mismatch rejects boundary eligibility. Stable raw maps
   and unknown request combinations are retained without semantic labels.
8. Ring overflow, decoded-count mismatch, event timestamp reversal, and rows
   outside saved-TGID/TID scope reject. Region counts must sum exactly with
   markers and explicitly excluded rows.
9. Annotation tests prove pre-window visible context alone is ineligible and
   that only an ordered uncertainty-complete visible-to-black transition wholly
   inside START..END can enable observed-onset classification.
10. Retained 1901 raw trace remains rejected because it has neither TRACE_ARMED
    nor PREROLL marker or quiescence sweep. A byte-pinned in-memory fixture may
    add exact owned trace-armed and pre-roll markers plus a complete synthetic
    quiescence record, and increment only the trace header accounting; the resulting analysis must
    classify the exact TID1011 fd33/request `0xc010643a` pair as one boundary
    completion, leave START..END event counts unchanged, and preserve every
    other raw row. This is a parser test, never a reclassification of the raw
    capture.
11. Existing END-drain, marker, thread-race, I2C syntax, observer, vlog,
    cleanup, resource, and no-control regression suites remain mandatory.

## Open implementation decisions

- Confirm the exact placement and worst-case latency of `FDS_PREROLL` before
  choosing whether a separate `FDS_ARM` snapshot is necessary. Correctness must
  not depend on an unmeasured shell-duration assumption.
- Confirm the stock kernel's exact `/proc/PID/task/TID/syscall` forms for the
  pinned AVOC tasks and measure the full sorted-TID sweep. The implementation
  must keep every raw attempt and reject an unrecognized form or a TID without
  a numeric non-54 terminal sample; it must not increase the fixed eight
  attempts, 2 ms interval, or 0.500-second prelude ceiling after observing a
  slow incident run.
- Measure added one-second trace volume in a passive smoke; retain the current
  16 MiB total ceiling and fail on any ring loss rather than projecting success.
- The pre-roll parser should be a coherent revision of the existing single-pass
  state machine, not a normalization that deletes or moves START. Independent
  review is required before implementation or any live use.
