# Current readiness of the stock unmute-zero capture

Independent offline review, 2026-10-26. No TV, root, network, D-Bus, trace, or
display-control action was performed for this review.

## Files reviewed

- `unmute-zero-capture.py`: 8,747 bytes,
  SHA-256 `13d6d111d6a0a05c1e619f0402efe56ef52fbe44d849cc0ddbb43a9e2dbbe12f`.
- `diagnostic-trace.py`: 4,512 bytes,
  SHA-256 `d8dc48fb719601c2868cb85167d2486470334d207a62ede8bfd1ba6e1ea2d7be`.
- `next-observed-session.md`: 17,990 bytes,
  SHA-256 `16c88a68de30bd0503adecf90b10e11300d5fdba64d905919df1c05d1f3dc2dc`.
- Preserved generated shell `next-unmute-zero.review.sh`: 4,222 bytes,
  SHA-256 `5773dc8ce965d18f52ce4684d1c0257f98807b29f1ddcb29a4d654bc5e5dafc0`.
- Current root client `../root-access/s95f-access.py`: SHA-256
  `3a92e02003ce51d2faeace231191f6f0c73731f2bfca9caa196e05b195b439a5`.
- The current passive-observer pattern considered for the replacement was
  `observed-quiescent-pm-onset-capture.py`, SHA-256
  `8390e85eff9a40fe774c5e2bd7488ebaaa703c734af20a19fd0a780b58cdc43f`.

## Verdict

The preserved helper is **not execution-ready** under the current root-access,
provenance, cleanup, and physical-annotation contracts. Do not run the command
printed at `next-observed-session.md:69-72` as it stands. Its intended stock
call remains useful, but it needs a new, reviewed runner around the unchanged
one-zero operation.

The body has no second display setter hidden in it. Its device-facing calls are:

1. preflight `GetPanelMute` and `GetPanelMuteCaseStatus`;
2. exactly one `SetPanelMute int32:0` between the two trace markers; and
3. post-call `GetPanelMute` and `GetPanelMuteCaseStatus`.

It contains no `SetPanelMute int32:1`, power call, factory/service call, sensing
request, retry, or persistent configuration write. Its other effects are
private tracefs configuration, creation of exact `/tmp` evidence files, and a
detached expiry process. Those trace/process/file effects are material because
the present lifecycle and cleanup are incomplete.

## Blocking findings

### P0 — root transport and command bound

`unmute-zero-capture.py:103-106` invokes `s95f-access.py root` without
`--persistent-only`. That permits the root helper's fallback/bootstrap branch,
contrary to the established host-assisted persistent-root-only boundary.
`diagnostic-trace.py:57-59` has the required option, but the unmute helper does
not use that function when it actually runs.

The combined shell is submitted synchronously at lines121-125 with controller
timeout `seconds + 40` (52 seconds at the prepared 12-second duration). That is
outside the current 25-second bounded controller contract. The operation does
not need that expansion: five D-Bus calls each have a 1.5-second reply timeout,
the trace sleep totals 12 seconds, and setup/readback is small. A new runner can
retain one blocking combined shell and use an exact 25-second controller
timeout, failing closed if it does not finish. It must not retry the setter.

The 131,072-byte fetch chunks at lines145-147 expand beyond the persistent
controller's bounded response envelope when base64/framing is included. Use
at most 32,768 raw bytes per fetch and validate every chunk's index, decoded
length, aggregate size, and final SHA-256.

### P0 — no authenticated, command-bound result validation

`root()` merely loads `commands[0]`; it does not require one command, exact
command equality, authenticated true, expected model, uid/euid0,
`root_persistence == "host-assisted"`, or
`global_system_files_unchanged_at_acquisition == true`. It also does not bind
the response to pinned root-client and generated-shell hashes. The fetch path
repeats the same weakness. Raw controller stdout/stderr is only partially saved
and later fetch responses are not retained at all.

The public reply classifier uses a first regex match and accepts one status and
one integer inside that match. It does not require exactly one reply section,
exact marker multiplicity/order, a single recorded setter occurrence, or exact
pre/post getter sections. Public `return0` must remain labeled only
`public-accepted`; it does not establish lower I/O, panel acceptance, or emitted
light.

### P0 — physical-black and no-sensing eligibility are not recorded

`--physical-black-confirmed` is only a Boolean CLI assertion. It has no timed
local annotation and can become stale before the request. The helper cannot
establish that the panel was physically black immediately before the marker or
whether it became visible afterward.

The helper also does not establish the requested **no sensing** condition.
Panel-mute getters do not identify an off/EL-sensing cycle. Trace or log silence
would not prove its absence. Do not add `GetQDDisplayState` as a preflight: the
documented getter can acknowledge saved results. The minimum admissible
qualification is a fresh owner assertion immediately before launch that no
Screen Optimization warning/countdown or known ten-minute maintenance cycle is
active, recorded alongside the black/audio observation. This is an
owner-qualified exclusion, not a software proof.

The evidence must include timed local annotations for at least:

- pre-call picture black and audio present/absent;
- warning/countdown not visible, or explicitly unknown;
- post-call picture visible/black and audio present/absent; and
- host reaction-time and host/TV clock uncertainty.

The pre-call black interval must end after the capture baseline begins and
before the `BEFORE_SINGLE_UNMUTE_ZERO` marker. The post-call observation must
begin after `AFTER_SINGLE_UNMUTE_ZERO`. Otherwise physical outcome stays
unclassified.

### P0 — expiry, residue, and local-output lifecycle are incomplete

`diagnostic-trace.py:27-30` starts a detached expiry and records only its PID.
Neither the normal path nor `unmute-zero-capture.py` terminates, waits for, or
verifies death of that exact process/group. Immediate cleanup removes only the
trace instance. It does not remove or verify absence of the remote trace,
probe, `.mute`, `.case`, or `.expiry.log` files.

Only the trace directory and trace output are checked absent before execution.
The probe and derivative files may preexist and are opened with truncating
redirections. Locally, the initial collision check covers only `.json`,
`.trace`, and `.sh`; later `.stderr`, `.probe.txt`, `.probe.json`, cleanup, and
error paths can overwrite existing evidence.

A replacement must use a private `0700` local directory and `0600` exclusive
files, a private remote output namespace with owner/mode/symlink guards, and an
owned expiry PID/start-time/process-group record. Normal and error cleanup must
TERM, bounded-wait, KILL if necessary, verify group death, disable/remove only
the private trace instance, remove the exact stage/output paths after salvage,
and recheck global tracing remains `0`/`nop`. A lost controller response must
not trigger another setter.

### P1 — trace completeness is too weak for wire-level interpretation

The only trace validation is one aggregate
`entries-in-buffer/entries-written` equality. The helper does not retain or
validate per-CPU stats, event formats and filters, clock/config readback, row
counts, owned marker source/PID, marker order/timing, boot/process identity, or
source-process lifecycle. The private ring is only 512 KiB per CPU. A quiet
12-second run may fit, but fitting cannot be assumed.

Use the current passive collector's fail-closed 4 MiB-per-CPU accounting and
marker/source guards, with exact configured-event/filter readback. Any loss,
malformed marker, missing sidecar, identity change, or unresolved event makes
wire classification incomplete. Silence never proves that a gate or sensing
path was absent.

### P1 — remote and host provenance are incomplete

The generated shell is written but no intent record binds its byte length/hash,
the reviewed source hashes, exact CLI, current boot, or root-client hash. The
preflight checks only a build-id string; it does not authenticate the relevant
process start identity or preserve maps/source identity. Probe/trace fetches do
not retain their individual root results. The statement in
`next-observed-session.md:39` that transfer and cleanup are verified is true
only of the old helper's narrow checks, not of the current evidence contract.

## Minimal replacement plan

Build a **new** dedicated runner; do not edit or invoke these preserved files.
Keep its scope to one 12-second, owner-observed attempt.

1. Default dry. Require `--run --reviewed --physical-black-confirmed` and a
   separate `--no-sensing-confirmed` operator assertion. Refuse existing labels
   and create one exclusive local result directory.
2. Pin the exact root client, new runner/tests, generated shell, and any passive
   collector modules it imports. Write an intent record before target access.
3. Reuse the existing generated operation body semantically: two baseline
   getters, one and only one stock `SetPanelMute int32:0`, then two post
   getters. Keep it in the same trace shell so serialization cannot move the
   request outside the evidence window. Assert the rendered shell has exactly
   one setter and no mute-one/power/factory/sensing request.
4. Invoke only `root --persistent-only --timeout 25`. The single combined
   12-second shell may remain blocking; do not enlarge the controller timeout.
   Preserve the full raw root response before validation and require the exact
   authentication, persistence, system-file, command, exit, timeout, stdout,
   and stderr schema.
5. Give the trace and expiry finite owned lifecycles. Capture the expiry PID,
   start time and process group; stop and verify it after normal completion.
   On error, salvage bounded artifacts, clean once, and never retry the setter.
6. Frame the baseline getters, setter reply, and post getters separately with
   exact marker counts and monotonic/UTC anchors. Preserve raw D-Bus stdout,
   stderr, and exit status. Treat public acceptance, observed wire emission,
   and physical recovery as three separate results.
7. Use the current strict private-trace configuration/readback, per-CPU loss
   checks, process identity, and owned-marker validation. Do not claim that a
   quiet trace excludes sensing or lower hardware activity.
8. Fetch only manifest-listed sidecars in chunks no larger than 32,768 raw
   bytes. Validate each size/SHA and retain every controller response. Then
   perform exact residue and global-baseline cleanup verification.
9. Record owner annotations locally around the two TV markers. If black/no-
   sensing qualification is stale, annotations are missing, or the physical
   timing does not bracket the call, preserve the technical result but mark the
   recovery question ineligible.

Only one actual attempt is justified. A timeout, lost response, public reject,
quiet wire trace, or unchanged black picture is a retained result, not a reason
for an automatic or manual repeat in the same session.
