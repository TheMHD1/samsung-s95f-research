# AV host-orchestration review

Review scope was limited to the host orchestration in `run-stock-bracket.py`.
No helper was imported or executed, and no TV, network, USB, native build, or
target operation was performed during this review.

## Pinned bytes reviewed

- `run-stock-bracket.py`: SHA-256
  `c127fe9d496e7ed27b1a657ca7cfe27db96a4ecedf65fad520859493223b668f`
- imported unchanged `sleep-investigation-20261027a/stock-mode2-experiment.py`:
  SHA-256
  `da66959e8024a661a9877f21c796297fa59eb262260a05a147bcb7c41f019898`

The latter is the previously reviewed stock orchestrator. Its `identities()`
check pins the unchanged 60-second collector and each of the status, pin,
duty, and MODE2 runner sources before the new trial directory is created.
Execution clearance is conditional on both hashes above still matching at
dispatch; the new script records, but does not itself compare, the imported
orchestrator hash to a literal expected value.

## Result: clear for the single reviewed invocation

I found no host-orchestration blocker for one invocation with the externally
bound hashes above and the already established clean USB/parser lineage.

- Invocation is exact (`--run --reviewed`), and both the destination and
  collector label must be fresh. Once the destination exists, the same trial
  cannot be repeated through this script.
- Static call census finds one collector `Popen` and exactly one
  `old.helper('mode2', ...)` call. The only `while` loop polls for the single
  collector's authenticated launch receipt; it does not launch or retry a
  helper. `attempted` and `dispatch.json` are written before MODE2 dispatch,
  so an ambiguous dispatch remains visible and is not retried.
- The fresh X baseline must be accepted, `AlreadyFaulted`, cleaned to
  `STAGE_ABSENT`, and contain an initial `Faulted` RT state. The first
  readiness check requires a nonnegative baseline age below 600 seconds.
  The fixed boot ID is checked by readiness and by every imported helper.
- Before MODE2, the script requires the private 60-second capture to be
  active, more than 43 seconds remaining before the added public preflight,
  and more than 30 seconds remaining after pre-status, pre-pin, and pre-duty.
  The inherited transport additionally refuses each actual helper execution
  unless more than 15 seconds remain. These are fail-closed admission gates,
  not a claim that the measurements are simultaneous.
- The immediate public preflight requires update status `0`, power state
  `lcdon`, screen state `1`, burn-in/maintenance result `0`, the fixed USB
  identity/configuration, and all three interfaces unbound. Pre-status then
  requires `kernel_output_changed_from_sentinel is True`; pre-pin must be
  asserted. The acknowledged update-scheduling race remains unresolved and
  is correctly recorded in `intent.json` rather than described as atomic
  exclusion.
- After the one MODE2 request, only the inherited post-status, post-pin, and
  post-duty helpers are called. No X capture, recovery action, power retry,
  or automatic cleanup action is added.
- `bracket-exit.json` records whether MODE2 dispatch was attempted, the
  collector exit code, any sequence exception, and that post-action X was not
  executed. Individual helper records retain their accepted/cleanup/boot and
  result schemas through the inherited `helper()` validation.

## Explicit interpretation and lifecycle limits

- The 600-second baseline-age cap is only a bounded freshness check. It is
  not scientific simultaneity or event alignment.
- The public getter results and changed status sentinel are instantaneous
  observations. They do not prove a private MCU update gate stayed idle
  through MODE2; that residual race is the accepted limitation for this
  trial.
- Unlike the old orchestrator, this wrapper deliberately does not parse and
  accept the collector's final `record.json` in-process. It waits for the
  collector and preserves its exit code, but a zero script exit must not be
  called a technically accepted capture until the separately planned raw
  lifecycle/cleanup audit validates the collector record.
- A collector wait timeout can prevent `bracket-exit.json` from being written.
  The finite collector retains its own reviewed cleanup path, and the wrapper
  neither retries MODE2 nor sends a recovery command in that case; retained
  raw artifacts must be treated as unresolved.

Focused offline verification: Python AST parsing confirmed one `Popen`, one
poll loop, and the helper call order
`pre-status`, `pre-pin`, `pre-duty`, `mode2`, `post-status`, `post-pin`,
`post-duty`. Root's syntax check of the reviewed orchestration hash is noted;
this review did not create bytecode or run the program.
