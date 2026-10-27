# BX: synchronized normal-key onset candidate

This additive fork addresses BH's missed navigation interval. It performs one
fixed `Left` down/up after the first complete clean `R,M,C,H,L,R` cycle. A
separate bounded worker runs the unchanged stock key utility; the original
thread remains the only USB reader. The first clean trigger baseline is
retained separately from rolling last-clean retention. No reset, firmware
write, threshold change or additional navigation key is in this program.

The working tree contains source, a portable .NET 6 IL build and fake host
tests. **No target execution is established by this build.** A future trial
must qualify the current USB instance/first-header premise and calibrate
Apps/header focus with ordinary keys beforehand. Cached Apps alone is not
focus proof. The one Left is expected to select Live; it cannot silently add
another key if the result differs. Physical light requires an independent
observation. The original Apps-selected recovery remains separate.

## Build and host validation

Use the retained .NET 6 SDK to build `SynchronizedOnset.csproj`, then run the
DLL with `--self-test` and `--key-self-test`. Both paths use fake transport;
the key tests also use a real worker with a fake blocked key sender. They do
not invoke the TV, real USB, D-Bus, or the target key utility. There are 75
original transport cases and 22 additional synchronization/worker cases.
Default invocation is dry. `--execute` refuses on the x64 host.

The key worker attempts one Down, holds for a requested 150 ms, and attempts
one Up even after Down/hold failure. Each child gets a 1.5-second wait, a
process-tree kill on timeout, a 0.75-second reap wait and a 0.5-second pipe
reconciliation wait. Drains use fixed buffers. The observer continues its
original 20-second/80-cycle bounds; matching IN is never suppressed after an
accepted OUT. USB release/close occur before a separate seven-second worker
join. A join failure is rejected and cannot establish released input or
global descendant absence. The outer root-process deadline is a further
containment layer, not rollback.

## Evidence interpretation

Transfer times and key dispatch/return brackets use the same target monotonic
clock interface. They do not timestamp compositor consumption or physical
loss of light. Compare actual intervals: an `OnsetObserved` flag can describe
a recurrence before the worker actually dispatched Down. This is not proof
that the key caused it. All windows remain sequential, not an atomic event
tuple. Unchanged transport failure/phase rules apply.

`ObservationAccepted` records the original transport/cleanup result in live
output. Overall `Accepted` additionally requires a completed key workflow
with no recorded error. `UiReceiptObserved` and `PhysicalPictureObserved`
remain false. The immutable trigger-baseline is a duplicate of cycle 1,
not extra USB traffic; global transfer counters must not count it twice.

The largest tested successful retained result with the extra baseline is
14,476 bytes, below the 24,576-byte cap. This is a tested shape, not a proof
that every exception text has identical size. Error strings are individually
bounded and serialization enforces the cap before output.

See [parent provenance](parent-provenance.json),
[independent design review](reviews/independent-design-review.md), and the
implementation review when present. The original frozen passive observer
has not been edited. A centrally reviewed wrapper/result parser and actual
target trial remain unfinished; this source is an instrument candidate,
not a blackout fix.
