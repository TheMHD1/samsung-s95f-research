# EF stock MODE2 reinitialization control

This is an executable **host-only design**, with mocked actions and no live,
root, subprocess, network or device adapter. It prepares the finite automatic
control requested by the parent coordinator. No target action, mask write,
threshold write, code patch, flash operation or publication was performed.
The historical directory name contains “cold”; the protocol establishes a
**stock MODE2 reinitialization control**, not a cold boot, reset of all domains,
instruction reload, known reference contents or physical panel recovery.

Use two concrete entry points: `initialize()` and `observe(ticket)`. The same
sole-owner coordinator may call them consecutively without a person approving
between them. The split is an evidence boundary: observation requires accepted
MODE2 execution **and** positive old-disconnect/new-enumeration evidence tied to
that execution. A zero ioctl return alone does not authorize a first header.
`coordinator.py` implements these entry points through a fixed action enum;
`test_coordinator.py` exercises their complete clean/fault and failure paths.
There is deliberately no target-capable command-line entry point.

## Fixed sequence and boundaries

| Step | Concrete frozen constituent / admission | Next action on failure |
|---|---|---|
| Host preparation | Verify pinned originals, manifests, parser dependencies and payload bytes; allocate fresh private output directories and persist run/owner lease. Do this before timing-critical observations. | No target submission. |
| Apps preparation | Reviewed `apps_gate`, or bounded normal Apps preparation, exactly once. Cached Apps and reaped key workflow; no physical-picture inference. | Stop; no MODE2. |
| Public checks | Upgrade0, power `lcdon`, screen1, burn-in0 via `public_gate`. These are rejection signals, not universal maintenance proof. | Stop. |
| Initialization | `run-deadline-mode2.py:contract/execute`, one stock operation41/mode2, native alarm12s, foreground receipt and exact cleanup. | Preserve record/stage; no retry or observation. |
| Fresh identity | Same boot; retained disconnect→enumeration/configuration timeline after this request; fixed bus7/interface2/descriptors/configuration; positive current unbound/no-holders census and exact instance metadata. | Stop. Devnum change alone is insufficient. |
| Apps/header | Frozen v2 workflow once: optional wake, optional one Right from Live, two Up, bounded read-only settle; all key children reaped. Run **after** reinitialization and before EB. | Stop. No key retries. |
| EB baseline | Fresh EB-schema readiness bound to fresh-instance evidence; exactly16 headers/32 bulks, full raw hashes/strict parser/binding, Ready/release/close and `STAGE_ABSENT`. Both R samples clean, c4=40. | Stop before DP; no automatic reset. |
| DP | Fresh DP-schema readiness names baseline as last vendor boundary. Fixed20s/80-cycle maximum/250ms, same eight windows; one Left down/up after complete clean cycle1. Strict synchronized trial, reaped key child, unchanged sampled c4=40, exact cleanup. | Stop; no EB header, UI or recovery after ambiguity/refusal. |
| EB post | Immediately prepare fresh EB readiness naming DP, then one unchanged EB capture. No intervening analysis, key, reset or vendor request. Require both R samples match DP terminal class, c4=40 and accepted complete cleanup. | Stop for central reconciliation. |
| Apps return | After accepted post-read only, normal bounded Apps return once. | Stop; do not compensate with another key or reset. |
| Fault recovery | Only qualified `TransitionCaptured`/fault terminal + accepted post-fault EB: public rejection checks, one separate stock MODE2, positive fresh identity. | Preserve rejection/ambiguity; never retry. |
| Clean completion | Accepted clean DP + clean EB: return Apps and finish. | No recovery MODE2 is issued. |

All action slots are consumed and journaled **before** submission. Any exception,
missing or rejected receipt, short/ambiguous transfer, lost owner lease, pending
key worker, non-Ready terminal, release/close failure or missing exact cleanup
halts this instance. A new call cannot replay a consumed slot. Restart is not a
resume mechanism: a future live adapter must inspect retained intents centrally;
EF supplies no replay/recovery-from-ambiguity path. The `journal` callback must
provide durable persistence before returning; the mock journal does not prove
filesystem durability or lock ownership.

The only controller protocol actions are the frozen read-only EB and DP calls.
The coordinator neither implements a header nor receives an address/value
argument. EB's native Controller and DP's read-pair phase machine must fulfill
matching IN after an exact accepted OUT and stop on short/error/unknown phase;
EF does not issue a speculative “restoring” header or MODE2 to clear a queue.
A complete metadata census and closed-world ledger are **premises**, not endpoint
queue proof. The single USB owner remains the native read loop; DP's sole normal
key worker can run concurrently inside that frozen helper, is joined there, and
has no separate controller-USB path in this coordinator.

## Timing, reference age and comparison limits

`enumerationToBaselineUs`, `baselineToDpUs` and `dpToPostUs` use retained
same-boot **target monotonic** read/lifecycle brackets, never host elapsed time
subtracted from target timestamps. For EB use first start-R header-before and
last end-R IN-after. For DP use the first actual header and **last completed IN**
from all transfers, including current-partial and post-fault captures; native
`EndUs` includes key-worker join and is not that boundary. Retained trigger
baseline duplicates cycle1 and adds no I/O. DP can issue at most647 headers
(80×8 plus at most7 post-fault pairs), not necessarily80 complete cycles.

Existing wrappers perform final checks/census/cleanup and then EB uploads three
payloads and runs exclusive-file fake selftests. These operations impose a real
gap. The pure design budgets30s per inter-capture gap and180s enumeration→first
baseline; these are proposed **quality ceilings**, not measured performance or
claims of an instantaneous post-read. A negative/cross-domain time is rejected.
An exceeded positive budget preserves a completed protocol run but marks
`comparisonQualified=false`; otherwise qualified fault recovery still runs.
Large analysis and disassembly work must wait until the observation sequence
ends. Pin/load host bytes before starting; no live adapter should silently skip
frozen staging, selftests, current census, strict parsing or exact cleanup just
to meet the budget. If a substantially smaller gap is essential, a new reviewed
aggregate native reader could append EB-equivalent read windows to DP; that is
a distinct derivative, not something these frozen wrappers support today.

Reinitialization age is not reference age. Retain initial and post raw R/M/C/P/N,
D/columns, primary and secondary gate tables, fixed top/bottom candidates, and
all their individual brackets/hashes. Compare reference bytes, selectors,
operating/category modes, training/global counters and publication metadata;
never assume post-MODE2 zeros or infer an epoch from equal R/N. EC proves partial
clears and distinct initializer/publisher lifetimes; stale B/Diff and nonzero
ordinals are permitted admission facts. Gate samples describe **local table
permission conditional on reaching the lane**, not historical comparator calls,
full comparator coverage or a physical pixel/line mapping. EB568..635 does not
cover every possible faulting lane. DX sampled code identity does not fingerprint
the gate body. DZ does not prove that MODE2 reloads instruction RAM.

Later EG work reports reference-counter seed1 then two qualifying boundary
events; do not rename this “distinct top and bottom initialized.” EF does not
substitute a reference-event count for actual captured state. It retains the
uncertainty for analysis. EH's newer60-cycle logger is outside this frozen DP80
design; switching helpers requires a new explicit source/schema review.

Every sampled R c4 in EB and DP raw captures **and every compact checkpoint**
must equal40. DP itself permits other limits; EF's adapter must impose this
additional control condition. It cannot infer no limit change between polls.
This protocol compares software state, not emitted light: all physical fields
remain unobserved and no root cause or protection bypass is claimed.

## Future live binding contract

`adapter-contract.md` maps normalized mock facts to original artifacts and
lists the concrete work still required. `Receipt` is a trust boundary: it must
be constructed only after original strict parsers, hashes, lifecycle evidence,
and exact schema-specific readiness succeed. Setting booleans from a wrapper's
final `accepted` field is insufficient. EF's mocks prove control logic, not a
live adapter or the TV's state. Parent serialization and one owner lease must
cover the complete critical sequence; the existing root adapter's per-command
transport lock alone is not a transaction lease across wrappers.

Run host-only checks without importing a target-capable adapter:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 verify_inputs.py
PYTHONDONTWRITEBYTECODE=1 python3 test_coordinator.py
PYTHONDONTWRITEBYTECODE=1 python3 -O test_coordinator.py
```

`input-provenance.json` pins scoped reviewed sources with paths relative to the
overnight directory. No raw OEM bytes, root envelopes, device identifiers,
authentication values or copied captures are included. `source-audit.json` and
`validation.json` record reproducible source/mocked checks; `source-inventory.json`
covers authored EF deliverables only. Existing frozen files were read, not modified.
