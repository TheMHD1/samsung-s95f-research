# Parser design note: duplicate AVOC syscall-enter isolation

## Scope and invariant

This is an offline design note based on the rejected
`sleep-mode2-20261027a.onset` record.  It does **not** alter a collector,
reinterpret that record as accepted, or establish a hardware or physical-panel
effect.

The current rejection remains correct.  A future revision may expose a
separately-qualified *typed transport inventory*, but must never silently turn
an AVOC syscall pairing anomaly into a capture-level success or an absence
claim.

## Observed fact set

The trace is complete according to its own accounting (`104917/104917`) and
has the expected five markers.  The relevant raw records are:

```text
trace line 4532  94415.763058  AVEMonMain-1011 (TGID 706)
  sys_enter NR 54 (21, c010643a, f4efe4ac, 170d0, 0, f4efe4ac)
trace line 4538  94415.863044  AVEMonMain-1011 (TGID 706)
  sys_enter NR 54 (21, c010643a, f4efe4ac, 170d0, 0, f4efe4ac)
trace line 4540  94415.867624  AVEMonMain-1011 (TGID 706)
  sys_exit  NR 54 = 0
```

The capture window begins at uptime `94414.110`; the duplicate occurs before
the pre-pin helper execution (`94417.71`) and the MODE2 helper execution
(`94422.87`).  It consequently cannot be assigned to the MODE2 action.

Identity evidence is internally consistent at the coarse level available:

| Evidence | Start | End | Meaning / limit |
| --- | --- | --- | --- |
| Boot ID | `00000000-0000-4000-8000-000000000000` | same | Same boot only. |
| AVOC PID / executable | `706` / `/usr/bin/avocd` | same | Process identity snapshot, not a syscall-pair explanation. |
| AVEMonMain TID | `1011` | retained in `TIDS_END` | No tracked AVOC `sched_process_exit` or replacement appears through drain. |
| Thread stack map | `[tstack: AVEMonMain: 1011]` | same map text | Supports identity snapshot; it is not a per-event starttime. |
| Raw FD `0x21` | decimal 33, `/dev/dri/card0` at start/pre-roll/end | stable | Syscall-register fields are hexadecimal (`%lx`-style): raw `21` is not decimal 21. The `0xc010643a` value is consistent with a DRM wait-vblank encoding, but numeric decoding alone is not a causal interpretation. |

The raw command filters are symmetric: both `sys_enter` and `sys_exit` filter
only syscall 54 for the same frozen TID set, including 1011.  The trace shows
an eventual zero exit after the second enter.  A single thread cannot execute
two syscalls concurrently, but the trace alone cannot tell whether this is
restart/re-entry representation, a dropped/mis-associated exit, or another
target-kernel tracing detail.  It is not evidence by itself of a crash,
process restart, controller reset, or transport failure.

The current parser at `observed-preroll-onset-capture.py:388-409` keeps one
pending syscall per TID and raises on the second enter.  That is a sound
fail-closed rule for its stated whole-trace AVOC-pair inventory.  It should be
retained for the existing collector and all frozen records.

## What can be separated safely

There are two different evidence domains in this trace:

1. **AVOC syscall inventory.**  This needs a well-formed one-enter/one-exit
   model if a report attributes user-space ioctl activity, duration, FD, or
   return code.  The duplicate makes that domain `ambiguous`, not clean.
2. **Typed I2C transport records.**  These are independently emitted trace
   events and can be grammar-checked without assuming an AVOC syscall pair.
   For example, line 2836 begins a syntactically complete adapter-5/address
   `0x76` group, followed by write/read/reply/result records.  Their presence
   says only that those raw trace records were emitted; it does not establish
   panel state, I2C transaction completeness unless the group rules pass, or a
   causal relation to the ioctl anomaly.

Thus a future parser can produce a structure like:

```json
{
  "capture_eligibility": "rejected",
  "rejection_reasons": ["avoc_syscall_pairing_ambiguous"],
  "avoc_ioctl_inventory": {"eligibility": "ambiguous", "usable_for_attribution": false},
  "typed_transport_inventory": {"eligibility": "eligible-or-rejected-independently"},
  "physical_inference": "not-derived"
}
```

`typed_transport_inventory=eligible` must **not** imply
`capture_eligibility=accepted`, diagnostic eligibility, an absence claim, or a
physical label.  It merely permits an explicitly limited inventory of typed
records for later comparison.

## Proposed future typed-transport eligibility

Run this as a distinct pass only after immutable basic trace integrity checks:

* strict UTF-8 decoding; exact marker count/order and collector identity;
  marker clocks and configured window bounds valid;
* trace accounting complete (`retained == written`); no broadened window;
* each typed event has a recognized event name and a strict grammar;
* adapter 5/address `0x76` constraints remain exact; payload length, byte
  syntax, and result adapter number are validated;
* retain original line number, trace time, CPU, PID/TGID, event kind, and raw
  body for every accepted typed item; never back-fill a missing item;
* construct a transport group only from an adjacent, ordered sequence with
  the expected message indexes (`#0`, `#1` where applicable), compatible
  address/flags, expected declared lengths, and a terminal `i2c_result` whose
  `n` equals the group message count and whose return is recorded verbatim;
* groups may not cross `CAPTURE_START`, `CAPTURE_END`, or `DRAIN_END`.
  Inventory labels must distinguish fully-in-window, start-boundary,
  end-boundary, and drain-only groups.  Only fully-in-window groups are
  eligible for a window comparison;
* any malformed/partial/ambiguous typed group is retained as a rejection row
  for that group, never merged with a neighboring group.

The present parser only validates I2C syntax and reports raw in-window counts;
it deliberately does not yet implement those transaction-group conditions.
No future revision should claim that syntax validation alone proves a bus
transaction or hardware outcome.

## AVOC treatment in that design

Keep a separate typed state machine per `(boot_id, AVOC PID, TID, thread
starttime-if-captured)`.  The existing snapshots give boot ID/PID/TID/maps but
not a reliable per-thread starttime, so a future collector must capture an
explicit `/proc/<pid>/task/<tid>/stat` starttime at the same guarded snapshots
if it wants to use that component.  Absence of the new field means
`identity_strength=coarse`, not substitution with a guessed value.

For a syscall state transition:

* `enter` while idle -> pending record;
* `exit` while matching pending -> completed pair;
* `enter` while pending -> preserve both raw rows and mark that TID
  `ambiguous_duplicate_enter`; do not pair the later exit to either enter;
* an orphan exit, identity change, lifecycle exit, out-of-scope TID, or a
  pending call that overlaps a protected boundary -> ambiguous/rejected for
  AVOC attribution;
* no heuristic may discard the first enter, pair the second enter by request
  equality, or call the result a retry/restart without target-kernel evidence.

The ambiguity should be local to the AVOC domain.  It still blocks any future
claim that depends on AVOC ioctl sequencing or no-ioctl absence, but it need
not erase independently complete typed transport groups.

## Test matrix required before any collector revision

All tests must be offline fixtures; existing collector code and frozen records
remain unchanged.

| Fixture | Expected capture | Expected AVOC | Expected transport |
| --- | --- | --- | --- |
| clean pairs plus complete in-window group | accepted only if all existing gates pass | clean | eligible |
| this exact duplicate enter before MODE2 | rejected | ambiguous | may be independently eligible if every group passes |
| duplicate enter inside an otherwise complete transport group | rejected | ambiguous | transport group may be inventory-only, never causally attributed to that ioctl |
| duplicate enter plus malformed/partial I2C group | rejected | ambiguous | rejected |
| ring count mismatch | rejected | not usable | not usable |
| typed group crossing START/END or drain | capture result unchanged by this check | independent | boundary/drain-only, excluded from in-window comparison |
| changed TID/starttime or tracked thread exit | rejected | rejected | transport may be retained raw but not attributed to AVOC |
| orphan syscall exit | rejected for AVOC claims | ambiguous | independently evaluated only |

Acceptance tests should assert that the final JSON has separate fields and
that no combination of `typed_transport_inventory=eligible` with
`capture_eligibility=rejected` can be rendered as an accepted experiment.

## Evidence provenance

All inputs were local and read-only:

| Artifact | SHA-256 |
| --- | --- |
| `sleep-mode2-20261027a.onset/trace` | `5ade657ba4c253e70cbb26eab2431a0a8bde2acd73f85386d9e7d1fce78633ab` |
| `meta.txt` | `64cf663811e29e7a2ff8da0ffec0d4643a5140fa734604e5008eff7e173355d5` |
| `fds.txt` | `fe6cea5257805af725f62bb944f3db14151a584b27b8596a1140547f0e95ec6b` |
| rejected `record.json` | `357e7f517ff019c1f185de4233a87f1a8ccd44e9716f5ccdf9e82e003eb86df0` |
| current parser inspected | `355d98bc04ab26b962fb3e92dc0953dd2aa6ccc837456efd49fbdd5b4329e697` |
| current offline tests inspected | `144f0a4dc188542180c4a66f4853ba31d61e5909073a9480756527caf6c22de1` |

No target, network, TV, media-server, root transport, or collector call was
made while preparing this note.
