# X passive observer: independent runtime audit

One reviewed fixed read-only run completed at terminal Linux uptime126642.16,
boot34f419d2-6256-4e1f-a7a9-8d46b875857d. Independent read-only audit passed
with no discrepancies and made no target/network calls.

The auditor reconstructed all24 authenticated root calls: each raw response
matches the stored decoded response, model/host/root identity, echoed command,
exit0, no timeout, empty stderr and45s/75s supervision. Commands stay within
8192bytes. Uploads reproduce the pinned52736-byte DLL and exact deps/runtime
files. One target zero-I/O self-test reported75/0/10541 with two classified GC
rows. Exactly one native execute followed.

The complete envelope and4544-byte stdout reproduce the retained native
files and record hashes; stderr is empty. Native result is accepted
AlreadyFaulted/OnsetMissed, with opened/claimed/released/closed true,
ReadyForHeader, writes0, retries0, one started cycle, six headers and six exact
IN responses (12bulk transfers). This is not a fresh event capture.

Actual monotonic microsecond bounds:

```text
start       126641969582
first bulk  126641974989
last bulk   126641983131
end         126641984282
```

Every transfer falls inside start/end and is ordered correctly, so the
wrapper's documented P3 timestamp-containment gap does not affect this run.

Initial and final RT256bytes are identical (SHA91055b0c...), including
stop1/fault1001/ordinarygate0. Mode68, context16 and latch64 repeat their earlier
hashes exactly. Newly read H96 has SHA256
d94f16ac03ed209ece31c6e35b49d89a81755681fabf296b3bc5a37013c3fe42.
Every raw artifact matches Base64, declared size/hash, result inventory and
its uniquely named saved binary.

Under U's qualified CPU aliases, the selected-code decode gives A=[44,0,0,0,0,0], allq0,
mode1history=[6,0,0,6], otherhistories0; modefields aa0/ac2 and alternatebyte1.
The current mode1 candidate therefore selects40 with lowA44, matching the
shared latch44 and satisfying44>40. H returned mode6A0 before L returned
latch54. This is a sequential difference, with no proof of simultaneous
divergence, staleness at the L read, or absence of intervening writes.
No live core tag was sampled; C/H/L/R CPU meanings remain conditional.

Cleanup revalidated all five exact staged files, ownership/modes/sizes/hashes,
removed only those files and their private directory, and returned
STAGE_ABSENT. The record has cleanup_required=false. No collector remains
running from this finite run. No TV reset, logging-gate/protection/threshold
write, UI action or physical observation occurred.

The run validates the recorder's real target ABI, Samsung GC handling,
already-faulted path, raw retention, timing and cleanup. Clean-start,
transition-detection and20-second duration behavior were tested offline, not
on a new live onset here. The late numerical consistency is stronger than
the earlier latch-only sample, but it is not V6 event-time, atomic CPU-register,
physical-blackout or repair proof.
