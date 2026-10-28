# W live ordinary-input snapshot

One fixed read-only acquisition completed on2026-10-27 at terminal Linux
uptime125699.16, boot00000000-0000-4000-8000-000000000000. It returned the
expected pointer anchors, an824-byte ordinary AP_EXCO prefix and the1004-byte
derived object. All six USB bulk transfers were exact. The native helper
ended ReadyForHeader, released and closed the interface, and verified removal
of its exact five-file private stage. No gate, threshold, UI, power state,
protection or firmware setting was changed. Physical light was not observed.

## New measurements

| Field, ordinary object unless stated | Value |
| --- | ---: |
| ca / cc / ce | 1 / 1 / 0 |
| e0 debounce threshold / e2 counter | 30 / 30 |
| e4 counter / e6 output | 0 / 1 |
| 116 recomputation gate | 1 |
| 10a / 10c, low/high pair | 62590 / 125 |
| 2cc / 2ce | 1 / 2 |
| 2fc other candidate output | 0 |
| 300 / 302 counters | 0 / 0 |
| derived bytes0 /1 /3d8 | 3 / 10 / 1 |

The sampled composite `bool((ordinary.e6 &1) || ordinary.u16[2fc])` is true
and numerically equals derived3d8=1. In these sampled bytes, e6 bit0 provides
the true operand; 2fc is zero. The selected-code model therefore has a
concrete, debounced first-helper output compatible with the alternate
selector. It no longer needs to treat both candidate operands as unknown in
this late snapshot. This is not proof that a specific writer ran between
these reads or that the same condition held at the V6 event.

The live e2=30 equals the selected/helper debounce threshold30. The runtime
aggregate X is nonzero, confirming why the earlier initializer-X assumption
was inappropriate. Full aggregate arithmetic and source interpretation are
being checked separately; no physical unit or sensor name follows from these
fields alone.

The prior corrected O snapshot had derived3/10/1 at uptime123267.81; the new
derived3/10/1 matches those fields2431.35seconds later. That is a comparison
at two sampled instants, not continuous immutability or an event tuple.

## Independent runtime audit

An independent read-only reviewer reconstructed all20 authenticated root
calls: exact uploaded runtime files, one target self-test, one native
execution and final guarded cleanup. Every response has uid/euid0, matching
command, no timeout, exit0 and empty stderr; the largest retained raw root
response is12685bytes. Native stdout is4454bytes with two classified GC rows.
All10 lifecycle/transfer rows, exact six bulk counts, raw Base64 payloads and
three standalone binary hashes match. The audit reported CLEAR with no
concrete finding and made no target or network calls.

| Evidence | SHA256 |
| --- | --- |
| pointer32 | 7634f63e1eace3b6da5f287655f1b1ef3ebdb81b22909605a467c2472af43cd3 |
| ordinary824 | 0f7884892da5714a9adcb97cdc033c4d5b24201b1ac570dabcc6771c01a7e271 |
| derived1004 | de263b1ebda47b3d1c306f87017b4961e1f25473d43b7ee7964345002b3a90f0 |
| record.json | 0a9a35106d6d2ce35d3212d51775fe2fd2a8e68ccf4d2c08c150677e6b7cf1c9 |
| result.json | 83cd349d84ef397074f36c5b80e2cc72ad8b00bbeebae5dae978a21f11935171 |

All evidence is under `capture-once/`; the reviewed source/build pins remain
unchanged. The final build manifest is
5d760fbdabf7b23b6e57f13fc40914a8ede43bf1b488738dc7c42f203321ca69.

## Scope of progress

This read closes the missing *late ordinary-input* observation. It does not
close event-time mode/limit/aggregate, physical onset, physical output-control
semantics, writable code, recovery, prevention, autonomous root or a repair.
The next observer is being built to retain a bounded last-clean/first-fault
RAM sequence without arming a logging gate or modifying firmware.
