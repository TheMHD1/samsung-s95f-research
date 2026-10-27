# Independent re-review: stock MODE2 orchestrator, revision 3

Reviewed 2026-10-27 UTC, offline only. This is a new review of
`stock-mode2-experiment.py`, SHA-256
`da66959e8024a661a9877f21c796297fa59eb262260a05a147bcb7c41f019898`.
It supersedes neither the prior rejection record nor its hash; it evaluates
the revised bytes. No TV, root, network, media, controller, or display call
was made.

## Verdict

The two prior evidence-correctness blockers are fixed in this revision.
Subject to the already pinned helper/capture sources remaining unchanged, the
orchestrator is technically ready for its single reviewed run. This is not a
claim that MODE2 will actuate hardware, recover a picture, clear a fault, or
prove a physical causal theory.

The revision now does all of the following:

* injects the private-trace and remaining-window gate into each helper's
  **actual remote execute command after staging**, rather than relying only on
  a host-side launch-time estimate;
* requires `execute_uptime < end` from each accepted helper before permitting
  the next action;
* stops the sequence on any gate, helper, cleanup, boot, or timing failure;
* waits for the collector, then requires exit code zero plus collector
  `accepted`, `technical_capture_complete`, and `cleanup_verified` before it
  records an accepted sequence;
* writes `accepted_sequence: false` whenever an exception is active or the
  passive bracket is rejected, without manufacturing a physical result.

An unexpected trace failure that happens after a successful action gate cannot
be prevented retrospectively, but is now classified as a rejected bracket at
the end rather than being presented as an accepted trial.

## Exact wrapper-path review

`helper()` imports each pinned runner directly and uses its `run_once()` plus
`contract()` rather than launching a helper CLI. The factory selection is
correct for the four helper shapes:

| Helper | Runner integration shape | Wrapped object carrying `root()` |
| --- | --- | --- |
| pre/post pin | direct runner | `run-errpin-cdev-input-once.py` module |
| MODE2 | `lifecycle_module()` | status-lifecycle module returned by that factory |
| post status | direct runner | `run-status-read.py` module |
| post duty | `mod()` | status-lifecycle module returned by that factory |

For direct runners, `configure_transport(runner, end)` replaces that runner's
`root`. For factory runners, the selected factory is replaced before
`run_once()` so every lifecycle module instance returned to the helper has its
own wrapped `root`. The wrapper leaves preflight/create/stage/postflight and
cleanup commands byte-for-byte unchanged; only a command containing the exact
`echo EXECUTE_COMPLETE` marker is transformed.

The injected prefix, placed immediately after `set -eu`, is:

```sh
test "$(cat /sys/kernel/debug/tracing/instances/researcher-hdmi-onset-sleep-mode2-20261027a/tracing_on)" = 1
awk -v e=<captured-end> '{exit !($1+15<e)}' /proc/uptime
```

Thus the same authenticated remote request that launches the managed execute
step fails before that execute step if the private tracer is not on or fewer
than 15 seconds remain. The established helper parser then requires the
returned `execute_uptime` to be strictly before the same captured end before
another helper is invoked. This does not infer an I2C transaction or panel
result from a managed return value.

## Size, source, and mock checks performed

All checks below were local-only.

| Check | Result |
| --- | --- |
| Recomputed orchestrator hash | Matches `da66959e8024a661a9877f21c796297fa59eb262260a05a147bcb7c41f019898`. |
| Dry invocation | Passed; emitted plan only and made no transport call. |
| Pinned source identities | The dry invocation completed its five SHA-256 checks before emitting output. |
| Rendered collector launch form | Retains one authenticated numeric target in `-- <target>) >` and the 60-second private capture. |
| Status direct execute | Original 7,885 bytes; guarded 7,890 bytes; under 8,192. |
| Pin direct execute | Original 7,476 bytes; guarded 7,481 bytes; under 8,192. |
| Duty `mod()` execute | Original 7,960 bytes; guarded 7,965 bytes; under 8,192. |
| MODE2 `lifecycle_module()` execute | Original 8,050 bytes; guarded 8,055 bytes; under 8,192. |
| Wrapper behavior mock | Verified non-execute command is unchanged; execute command gains the trace gate before `EXECUTE_COMPLETE`. |

The compacting transformation removes only full lines whose left-stripped form
starts with `#`. It then requires the transformed command to start `set -eu`
and rejects any result over 8,192 bytes. The above exact executions contained
the recognized completion marker and were transformed; no generic command is
being widened into a target action.

## End-of-capture acceptance

In `finally`, the revision records the process exit and parses the capture
record. Its acceptance predicate is:

```text
capture.returncode == 0
and record.accepted == true
and record.technical_capture_complete == true
and record.cleanup_verified == true
```

`outcome.json` sets `accepted_sequence` only if that predicate holds and no
exception is active. `diagnostic_eligible` is copied as information only; it
is not required for technical acceptance and does not substitute a human
physical observation. This resolves the earlier flaw where a partial/rejected
collector could be mistaken for a usable bracket.

## Residual limits

* A technically accepted bracket is not a physical picture observation.
* MODE2's zero return remains only the fixed helper's documented kernel-level
  classification, not action acknowledgement or recovery.
* A late gate failure or final capture rejection leaves raw trial artifacts
  but intentionally prevents an accepted sequence claim.
* `capture.wait(timeout=180)` can itself raise on an unexpected collector hang;
  that is a run failure, not an acceptance path. It does not synthesize a
  successful outcome record in that exceptional case.

