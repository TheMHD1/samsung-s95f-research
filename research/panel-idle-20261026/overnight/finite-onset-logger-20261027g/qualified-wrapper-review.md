# Independent review: qualified detached onset wrapper

Recorded 2026-10-27 UTC. This was a read-only review of the offline candidate
`managed-usb-secondary-logger-onset-qualified`. It made no TV, root, network,
USB, controller, UI, or process-lifecycle request.

Reviewed aggregate manifest:
`aa4fc99a5cd22f86736e49487322b1c6aa6996eae482c8fda3a1971049b386d6`.
The native manifest remains
`316d92b64be47767cb8461d4cbde30b9446d901060b2de798da605d9f1c8131c`;
the pinned native `Program.cs` and DLL remain `db45feac...` and `4870eed0...`.

## Prioritized findings

### P1 — Deployment remains blocked by unresolved controller protocol lineage

The qualified wrapper correctly states this block. Control-smoke-v2 has a
launch receipt but no supervisor/native terminal evidence, and absence of its
old process or stage cannot reveal firmware parser phase. The stock mode-2
evidence proves a host USB disconnect/re-enumeration, not initialization of the
vendor parser to `ReadyForHeader`.

The new wrapper neither performs nor proves a parser reset. It must not be
executed until a separate closed-world no-transfer lineage or independently
proved parser reinitialization closes that prerequisite. This is an execution
block, not a defect in the candidate's detached-launch implementation.

### P2 — The 19-case suite does not implement every negative case required by the D7 plan

Normal and optimized test runs both pass the exact 19-case result pinned in the
aggregate. The tests cover a real local `setsid -f` child, one inherited-FD
closure, one pre-native collision, wrong group, stale handshake/READY/probe,
child and command-line mismatch, ambiguous launch, absent completion, output
limits, diagnostic residue, READY/final binding, and cleanup failure.

They do not individually fault-inject all cases listed under “Offline
verification required before review” in `qualified-supervisor-plan.md`:

- each handshake create/write/chmod/read/rename failure;
- missing/partial/malformed fields, stale boot, zombie state, PID reuse,
  changed start ticks, or death before the 200-ms recheck;
- unexpected terminal names or a leftover temporary file; and
- descriptors 0, 1, and 2 individually, rather than one inherited descriptor
  above 2.

The fake `cleanup-residue` case injects failure when the cleanup request is
made; it does not exercise the real exact-inventory shell against an extra
terminal name. The source is fail-closed for these cases through `set -eu`,
absent-final checks, exact inventory, repeated `/proc` identity checks, and
the root adapter's exception propagation, so no concrete unsafe branch was
found. This remains a test-evidence gap relative to the published plan and
should not be represented as full coverage of that plan.

## Source and call-path result

No additional implementation blocker was found in the reviewed wrapper.

- The staged supervisor uses `set -eu`, a fixed private working directory,
  mode-0600 atomic PID/stat/start files, and creates the native child only
  after those three publications succeed.
- The launch path treats the mode-0600 script as data, closes numeric inherited
  descriptors above 2, redirects standard descriptors explicitly, and makes
  exactly one `nohup setsid -f /bin/sh -c` dispatch.
- `$!` is retained only as a dispatch receipt. The same authenticated launch
  request validates the actual supervisor's PID, process group, session and
  start ticks, then checks the live identity again after 200 ms.
- The native command starts immediately after the supervisor publishes its
  handshake; it does not wait for host-side receipt validation. Therefore a
  malformed or timed-out launch response can coexist with a native process
  that may already have run. The wrapper handles this correctly as ambiguity:
  it performs no retry, status poll, signal, fetch, or cleanup.
- READY is broadcast only after a fresh target-uptime check, live
  supervisor/child binding, exact child command line, and absence of the exit
  marker. No root request occurs during the following 22-second local grace.
  The wrapper itself sends no UI action.
- Completion is bound to the saved supervisor; stdout/stderr sizes and hashes
  are checked before fetch; READY is rebound to the final native outcome;
  accepted completion additionally requires empty launch diagnostics.
- Cleanup is possible only for an accepted parsed outcome after exact host
  retention. Its terminal allowlist contains exactly four inputs and ten
  outputs. Every rejected, partial, malformed, or ambiguous path leaves the
  private stage intact.

The generated fixed-path command sizes are within the root adapter's 8,192-byte
limit: the actual launch command is 7,879 bytes, cleanup is 6,152 bytes, and a
status poll is 2,093 bytes. The launch margin is only 313 bytes, but the
reviewed paths and names are fixed. `build-wrapper.py` checks a minimal launch
command using `true` as its integrity body rather than the actual 7,879-byte
command; the adapter still enforces the real command bound before dispatch.

## Offline evidence checked

- Aggregate, native, and every nested manifest row matched the current file
  size and SHA-256.
- `run-once.py`:
  `25b942ae2dbca8b210d9b195bb79b2b509d7501825e0b8d107ddc718911b6bd6`.
- `test-wrapper.py`:
  `adc62341f046850402df8c929742bdc936176b002fd8f7e42e8c920684daf9c1`.
- `build-wrapper.py`:
  `0c443b28315b3cc288c2d5d3f8cd777a517c14592c0b4d0bca1b6c41b8c06992`.
- `README-qualified.md`:
  `edb1166d7c0488749f4a155efef4cde7be8574bc1d5e790c44fd5a3c50d4cb08`.
- Python compilation passed. The wrapper suite independently passed 19 cases
  in normal and optimized modes, both with `target_operations=0`.
- The frozen D7 runtime evidence manifest
  `2d1d1427ea37c70e5b6ee37e301488027f6b2a0ff64f7d591884ca6faa252534`
  was verified read-only: all 84 rows, 4,515,096 bytes, sizes, and SHA-256
  values matched. This new review is intentionally outside that frozen
  inventory.

## Review disposition

The detached-launch and terminal-retention source is suitable as the
orchestration successor to the failed control-v2 wrapper. It is **not cleared
for target execution** because P1 remains open. The missing negative test
coverage in P2 must remain explicit if the aggregate is retained unchanged;
it did not reveal an unsafe source path during this review.
