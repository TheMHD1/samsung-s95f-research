# Independent review: stock MODE2 experiment orchestrator

Reviewed 2026-10-27 UTC, offline only. Reviewed source:
`stock-mode2-experiment.py`, SHA-256
`1f3c10fb9c6f43d9cd37928debfdb3d64a5d8adbec2bb810b5a16133da8e0ee4`.
No TV, root, network, media, controller, or display call was made during this
review. This review does not authorize or execute the experiment.

## Verdict: not ready unchanged — two correctness blockers

The script has useful one-shot and identity controls, but it does not yet
establish the required technical capture acceptance or preserve a bounded
in-window association for the complete requested sequence. These are evidence
correctness blockers, not claims about the physical panel or MODE2 safety.

1. **The finite collector is waited on, but never accepted.**  The `finally`
   clause uses `capture.wait(timeout=180)` and writes only its return code to
   `capture-exit.json`. It neither requires zero nor reads
   `<LABEL>.onset/record.json` to require the collector's technical fields
   (at minimum its technical completion and verified cleanup) while leaving
   human annotation / `diagnostic_eligible` independent.

   This matters concretely: retained onset collectors can end with
   `accepted: false` and an acquisition error after producing partial
   artifacts. The orchestrator's early `tracing_on`/marker probe can have
   succeeded before such a later collector failure. In that case this script
   could run the one MODE2 request and print a trial path without a technically
   accepted passive bracket. Waiting for a nonzero child is not a technical
   acceptance check.

2. **Only the pre-MODE2 point is time-gated.**  The second readiness probe
   requires more than 30 seconds remaining before it starts the fixed MODE2
   helper. There is no whole-helper deadline that follows from that check:
   `helper()` permits a 90-second host subprocess timeout, and the inherited
   lifecycle contains multiple staged root commands. Nor is there a remaining-
   window recheck before the requested post-status, post-pin, and post-duty
   helpers. Consequently the MODE2 helper, and especially the three post
   reads, can occur after `CAPTURE_END` despite the earlier private-trace
   proof. The code should either bound and prove the complete requested
   sequence fits the window, or explicitly record post-window actions as
   outside the paired capture and reject an in-window interpretation.

Both issues should be corrected and independently re-reviewed before a live
run. In particular, a new exact source hash is required after any correction.

## Controls that do pass static review

| Area | Evidence in reviewed source | Review result |
| --- | --- | --- |
| Default behavior | `--run` is false by default; `--reviewed` without `--run` is rejected. | Pass. |
| Immutable inputs | Five source SHA-256 pins are checked before the run branch. | Pass, subject to the source pins being the intended reviewed versions. |
| Unique run/capture locations | Existing `<LABEL>.onset` is refused; `DEST.mkdir()` has no `exist_ok`; each helper output is opened with exclusive creation. | Pass. |
| Passive capture first | The passive 60-second collector is spawned before readiness or any helper. | Pass. |
| Active private-window probe | Exact private instance path is used; `tracing_on == 1`, exactly one `CAPTURE_START`, and zero `CAPTURE_END` are required. | Pass as a point-in-time readiness check. |
| Precondition | Exactly one `pre-pin` helper is requested; result must be accepted, cleanup-confirmed, same boot, and raw value `1`. | Pass. |
| Fixed action | The MODE2 helper is fixed by a hash-pinned relative path and its own reviewed CLI gate; no selector/mode argument is accepted by this orchestrator. | Pass. |
| Retry policy | Helpers are called once in the listed order; failure raises and no retry branch exists. | Pass. |
| Helper cleanup | Every helper result must report `accepted` and `cleanup_confirmed`; the same expected boot is required. | Pass. |
| Capture cleanup wait | A finite 180-second `wait` is attempted in `finally`, including after a helper failure. | Partial pass: finite wait is good, but timeout/error/exit acceptance is not verified. |

## Ordering actually enforced

The source establishes this order if all calls succeed:

```text
launch 60-second passive collector
  -> active-marker readiness
  -> pre-pin (must return 1)
  -> active-marker readiness and >30 seconds remaining
  -> one fixed MODE2 helper
  -> one post-status helper
  -> one post-pin helper
  -> one post-duty helper
  -> wait for collector process
```

The readiness command is scoped to
`/sys/kernel/debug/tracing/instances/researcher-hdmi-onset-sleep-mode2-20261027a`.
The launch-command parser extracts the frozen collector's single numeric
target from the emitted `-- <uptime>) >` form. Static rendering confirms that
form for the pinned 60-second HDMI collector.

The sequence above does **not** imply that all helper completions fall between
`CAPTURE_START` and `CAPTURE_END`; blocker 2 is why no such claim is justified.

## Offline checks performed

* Recomputed the reviewed file SHA-256; it matches the stated source identity.
* Ran the orchestrator without `--run`. It emitted the dry plan only; no
  transport was attempted.
* Rendered the pinned HDMI collector offline and verified its launch command
  retains the one numeric `-- <target>) >` target form and the 60-second
  `CAPTURE_START`/`CAPTURE_END` window.
* Ran an in-memory mock of `readiness()` and `helper()`. The mock verified that
  readiness requires private tracing plus START/no-END text, parses uptime,
  and that helper invocation uses `--run --reviewed --output`, a 90-second
  subprocess timeout, an accepted/cleanup-confirmed result, and the fixed
  boot ID. This mock used a temporary local directory and no transport.

## Scope and limitations

This review did not execute the live branch, call the root transport, inspect
the panel, manufacture a human physical annotation, or infer recovery. A
technical capture can be complete while the physical state remains unobserved;
conversely, a human physical report cannot repair a failed technical capture.
