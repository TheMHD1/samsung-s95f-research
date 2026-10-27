# Observed branch-onset capture: bounded design

This is a new, offline-prepared observer. It hash-pins `observed-onset-capture.py`
at SHA-256 `17a30cbee3d0d6ce5d4b23ffd1333b359b124bb4c1caaac253e1a6bc0f9999d5`
and preserves that tool's private ftrace, vlog, annotation, ARM32 syscall, drain,
transport, resource, and cleanup contracts. It does not modify the frozen tool.
It is dry by default and requires `--run --reviewed`; this document is not live
clearance.

The exported run entrypoint temporarily installs the branch-specific builder
and validators into the frozen orchestration module. Calls back into the frozen
builder and metadata validator use immutable references captured before that
installation; they do not dynamically resolve the patched names. An offline
entrypoint regression executes generation, metadata validation, sample
validation, and dd accounting under the active compatibility context while a
transport sentinel rejects any external call.

Process identity helpers first capture and check the `p4` result, then validate
its four-field shape before using positional parameters. A missing or vanishing
PID therefore returns status 1 without emitting an unbound-variable diagnostic
under either `set -e` or `set +e`. The regression uses the same nested
`/bin/sh -c "$(cat DATA)" -- target` argument layout as the controller and covers
a dead PID, a disappearing child, and a live `/proc/PID/stat` comm containing a
space and `)`.

The five retained `--: line 2: $1: unbound variable` diagnostics in the 1901
smoke came from the outer collector (`$0` was `--`) after the vlog process had
exited naturally: the terminating `while vg` and following `if vg` supplied two
failed lookups, and the EXIT trap's `stopv` supplied three more `vg` lookups.
The Q child stderr was empty. The old `p2` used `set -- $(p4 "$1")`, whose
successful `set` masked a failed `p4` before unsafe positional reads; the status
and field-count checks above address that exact outer-vlog path.

## Added sampler

The monitor loop remains about 5 Hz. A second DATA script samples the supported
branch state at about 1 Hz. Its exact bytes and SHA-256 are embedded in the
collector, reconstructed into the private root-owned output directory, checked
before execution, checked again at both metadata endpoints, and executed as
`/bin/sh -c` rather than as a staged executable.

The branch sampler runs in a distinct `setsid` process group. It writes a
root-owned mode-0600 ready record only after checking that its PID, process
group, and session are identical. The collector binds PID and start ticks from
that record, retains both sampler identities in metadata, imposes a capture-end
plus three-second deadline, and uses bounded TERM then KILL escalation. A group
signal is sent only while the original leader/start/group/session still
validates; after that first signal, continuously observed group membership is
used to remove a TERM-ignoring child even if the leader exits. A stale leader
with only a numerically reused group is rejected, not signalled. Collector trap,
900-second expiry, host quiesce, and host cleanup all cover the sampler PID file
before the collector. Every path verifies death or fails cleanup.

The sampler checks `pidof`, executable link, robust final-`) ` `/proc/PID/stat`
start ticks, and ELF load bias for both `avocd` and `deviced` for every row. Each
memory read is exact-allowlisted and immediately range-checked against the live
`/proc/PID/maps` using fixed-width canonical ARM32 map endpoints. Full endpoint
maps, PIDs, starts, executable/source hashes, and pointer chains must remain
equal. This cannot exclude a transient change-away-and-back between sequential
reads.

## Accepted runtime type and raw fields

Only the exact base `QDDimming` vptr `A+0x59f2e8` and source-backed
`DimmingBackendRoseMQD` vptr `A+0x5a152c`, whose `+0xd8` slot equals Thumb target
`A+0x1c6275`, are eligible. MNT and untyped backends are rejected. Every row
re-reads the seven-word Q header and requires its vptr, inner pointer, backend
pointer, and initialized low byte to remain bound.

Rows retain start and end uptime plus raw little-endian words for:

- backend cache `A+0x5ab958` and Q header/backend identity;
- inner `+0`, `+0x38` (low byte interpreted only for the guard), `+0x88`,
  `+0x98`, `+0xa4..+0xac`, `+0xf8..+0xfc`, `+0x188..+0x18c`,
  `+0x2a4..+0x2a8`, `+0x450`, and `+0x458..+0x484`;
- globals `A+0x5ad94c`, `A+0x5bf6d0..+0x5bf6d4`, and the exact-base-QD
  AutoPowerOff static `A+0x5be420`;
- the frozen deviced guard chain.

These are sequential, non-atomic observations. No unit, current branch,
brightness, emitted light, mute, power transition, policy decision, or causal
relationship is inferred from them.

## Timing and completeness

The physical/annotation eligibility window remains exactly `CAPTURE_START` to
`CAPTURE_END`; the syscall drain retains its frozen purpose and does not extend
physical eligibility. A Q row must start and finish inside that window. The old
minimum 0.7 Hz Q rate, 2.0-second inter-row gap, and endpoint thresholds are not
weakened.

Each row's actual duration is retained and summarized. A predeclared two-second
operational ceiling (twice the nominal cadence) rejects diagnostic completion;
it is not derived from, and does not reinterpret, the prior unloaded 0.77/0.88
second baselines. A passive smoke may measure capacity but cannot certify
incident-time performance. Missing, partial, over-duration, boundary-crossing,
rebound, uninitialized, malformed, or extra-dd rows fail closed while raw
sidecars remain available through the frozen incomplete-capture path.

The retained `branch-smoke-20261026t1901` evidence remains incomplete for an
independent trace reason: one AVOC ioctl began before `CAPTURE_START` and
returned after it. This revision does not reclassify or waive that boundary
crossing. The frozen trace accounting continues to reject every call crossing
the start marker. A future pre-start syscall-drain design would require its own
bounded architecture and review; the process-helper and dd-accounting fixes do
not supply one.

## Security and execution boundary

The tool performs only `/proc` reads, private-instance trace configuration,
vlog capture, and the existing passive artifact queries. It invokes no keys,
getters, setters, device ioctls, service/power actions, or policy changes. It
introduces no custom/acquired helper ELF and invokes no target native control
binary; stock shell/read utilities and the already-audited vlog source remain
necessary. It uses no fallback root bootstrap. Remote scripts and temporary objects remain
inside distinct root-owned mode-0700 namespaces. The existing persistent-only
root wrapper and its command ceiling are unchanged; no retry is implemented.
