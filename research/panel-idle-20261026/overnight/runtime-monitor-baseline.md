# Actual QD monitor counters and repeatable runtime reader

This is a new **physically unobserved**, parent-operated baseline on October26.
It does not establish emitted light, a new blackout, a repeated module reset,
recovery or prevention. The goal remains unfinished.

## Captured process state

[`qd-monitor-baseline-20261026t122239z.json`](qd-monitor-baseline-20261026t122239z.json)
preserves all five root responses, exact remote commands, source and process
identities, maps, Base64 memory blocks and decoded words. SHA-256:
`37fc4c07f5f25988ffa291f207167500b9ca679bc159278a3d7d2f5094af3d9c`.

- Remote time:12:22:40..12:22:42 UTC; monotonic uptime38970.07..38971.83.
- Boot ID: `00000000-0000-4000-8000-000000000000`.
- PID706, `/usr/bin/avocd`, process start tick603 throughout.
- Disk AVE hash `a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777`
  matches before/after every stage. This is not a live-text hash.
- Exact offset-zero executable map yields AVE bias `0xf6b77000`.
- All maps match within and across this particular capture's five stages.
- Reads total356bytes:0+12+32+40+272. All bytes decode at validated readable
  addresses; all20 final before/after pairs match. This remains non-atomic.

| Field | Observed value | Meaning boundary |
| --- | --- | --- |
| ERR_DET / VDD / ELVDD fault counters | 0 / 0 / 0 | Clearable host bookkeeping; zero is not a fresh electrical fault test |
| ERR_DET / VDD / ELVDD recovery counters | 2 / 0 / 0 | ERR count is at the code's `>1` threshold; no event time or unique cause is established |
| `qd_tcon_off` history latch | 1 | A monitor invocation while unchanged takes the report/return route |
| Monitor restart / monitor on | 0 / 1 | Does not prove actual thread scheduling or physical panel power |
| Remembered previous monitor-on value | 1 | Context for whether the normal helper requests a bookkeeping reset |
| `si_ok_count`, `onetime_execution`, `ip_status_count`, `fault_occurred` | 4 / 1 / 7 / 0 | Preserved local words; not expanded into a hardware health verdict |
| Final-duty cache / working fields | 207 / 207 / 207 | Equal-value skip applies if dispatched unchanged; no failed send is observed |
| Raw AutoDim request | 0 | A sampled request field, not an emission measurement or historical exclusion |

The second monitor range also contains the unnamed word at state+0x64; it is
retained as raw1 and has no assigned meaning. The active chain remains
QDDimming→DimmingBackendRoseMQD, with the actual relocated output slot equal
to `bias+0x1c6275`. The nearby PIC anchor is not a combined backend-state object;
the final-duty cache at VMA0x5ab958 is one named function-local static.

## What this changes in the diagnosis

The [exact monitor map](../tcon-research/qd-monitor-runtime-map.md) now gives
the actual latch, counters and control fields, rather than relying only on
repeated log text. A latch1 invocation exits before normal fault checks;
therefore these zero fault counters cannot be used as evidence that a live
electrical fault is absent. The captured state is consistent with a previous
terminal monitor branch, but it does not establish that branch's timing,
exclusive writer history or connection to the owner's latest physical event.

The formerly opaque clear condition is now resolved through the actual GOT
relocation: `g_tcon_monitor_restart == 1`. The QD monitor's guarded clear resets
its bookkeeping and latch, then clears that restart flag. The ordinary
`ave_tcon_monitor_onoff` helper sets restart when its argument differs from
its remembered previous value. This identifies a conditional host-state reset,
not a supported recovery operation, a fresh fault test or a panel power-on.
No flag, latch or counter was written or toggled.

The [cache lifecycle audit](../tcon-research/qd-rosem-cache-lifecycle.md) also
examines RoseMQD construction, destruction, configuration, initialization and
resume. The only positive cache-initialization evidence recovered is the
file-backed `-1` initializer in a fresh process image. Those bounded method
checks do not establish standby/wake or resume as a natural cache reset, and
are not a global writer census. No process restart or forced retry was used.

## Repeatable tool and access-path correction

[`snapshot-qd-runtime.py`](snapshot-qd-runtime.py) defaults to a dry-run contract.
With `--run`, it derives current mappings, follows/type-checks the pointer
chain, and captures paired cache/duty/gate/monitor fields. It rejects a changed
boot/PID/start time, library bias/hash, unsupported object/backend/slot, bad
range, incomplete read, unexpected output or differing pair. Error responses
are preserved with `accepted=false`. Examples from this directory:

```sh
python3 snapshot-qd-runtime.py next-qd-baseline
python3 snapshot-qd-runtime.py qd-new-baseline --run --physical-label unobserved
```

Use a fresh execution label each time; existing capture labels are refused.
For a real observed comparison, use `apps-visible` or `black-audio` only when
the operator has that current physical observation. A label is an annotation,
not a sensor. Pair the captures with the finite transport/onset procedure in
[next-observed-session.md](next-observed-session.md).
The root channel is serialized. Take these standalone samples before and
after the finite onset trace; do not invoke the reader concurrently with the
blocking trace helper. This records stable-state comparisons around an onset,
not memory values at the exact instant of a transition.

Review found that the shared access wrapper could otherwise bootstrap root
through temporary staging when its persistent controller was unavailable.
The wrapper now has an additive `--persistent-only` option; this reader uses
it and cannot take that fallback. It also checks the controller-reported
source-system invariant. Normal SDK/root wrapper routing remains available
without the new option. The invariant is controller-reported and does not
replace the exact source hash or establish a full live filesystem hash.

The reviewed capture uses only process/source reads through the existing root
agent. It submits no TV keys, D-Bus operations, ioctls, tracing, memory writes,
process controls, service restarts or power commands. Root remains host-assisted.

## Verification and independent review

The new [reader integrity tests](test-snapshot-qd-runtime.py) pass7 cases,
including real retained108/120-byte records, malformed/partial memory blocks,
mapping bounds, duplicate output, PID reuse, changed maps and changed bias.
The wrapper's four new mocked routing cases cover absent/non-ready/failed
persistent access and one execution through a ready controller; combined
with existing wrapper tests,18 pass. No test contacts the TV.

The independent read-only reviewer also decoded every Base64 block in the
new baseline, recalculated all addresses and20 pairs, verified each dd record
and byte count, and checked the complete command allowlist. This paragraph
is the parent's record of that review, not reviewer-authored test output.
Its conclusion is integrity PASS with the physical/onset/causality limits
above. Static monitor and cache/path reproductions are separately hash-gated.
