# One unchanged primary-log read after the mute-consumer reconstruction

Recorded 2026-10-27 UTC. This follow-up reused the existing fixed reader once;
it did not build or deploy new instrumentation, change firmware, bypass a
protection, navigate the UI, or perform a power/reset action.

## Result

The read returned all 3072 requested bytes from target `0x101`, address
`0x20205000`. The strictly accepted native outcome reports one exact 12-byte OUT,
one exact 3072-byte IN, successful release and close, and `HELPER_EXIT=0`.
The wrapper retained 16 authenticated root calls and `STAGE_ABSENT` cleanup.
Strict offline acceptance and mutation-check results are recorded separately
by [parse-primary-log.py](parse-primary-log.py),
[parsed-result.json](capture-once/parsed-result.json), and
[validation.json](validation.json).

The returned block SHA-256 is
`e0ae7ea8a5cdbef12a1cd3637ecfb78d01bc1dacf64e122fa4855c10064fb0b4`.
It contains 3072 printable/whitespace bytes, 151 newlines, and no NUL bytes.
Routine text includes `deadPool`, `framework_ch`, and `LOG Buffer Copy`.
The block begins and ends within text fragments. No separate cursor was
read, so byte zero is not established as the chronological start.

There are no byte occurrences of `Failmode:`, `F-Set`, `F-Clr`, or
`RT-P activate!` in this block. This does **not** rule out execution of any
fault path. The logger is finite and can wrap; this is a late, sequential
snapshot with no event-aligned cursor or physical-picture annotation. Some
consumer paths also skip a message when the pre-read already matches.
The `RT-P activate!` search is only an extra raw-byte inventory: its mapped
caller uses a separate formatted-output path, not the qualified primary-ring
writer. It must not be treated as a marker expected in this buffer.
No causal branch, physical recovery, or blackout prevention was established.

## Execution boundary and lineage

The [reuse assessment](reuse-assessment.md) pins the unchanged manifest,
wrapper, native helper, and root transport. The current helper is the same
one previously accepted in E. Its older shell wrapper does not itself
validate native acceptance; wrapper exit zero alone is insufficient.

Before this attempt, [fresh host metadata](host-preflight.json) confirmed the
same Linux boot `00000000-0000-4000-8000-000000000000`, USB device 46 at
`7-1`, `04e8:2001`, revision `0250`, active runtime status, authorization,
configuration 1, all three interfaces unbound, and zero usbfs descriptor
holders. Metadata spanned uptime `141131.83..141157.44`.

The last vendor operation before this read was the accepted AW W snapshot,
ending in `ReadyForHeader` at uptime `137706.50`. Root performed no intervening
vendor operation; child agents completed offline-only work. This transaction
lineage, rather than USB metadata alone, supplied the first-header premise.
The one-shot intent is retained in [read-intent.json](read-intent.json).

The new execution envelope spans uptime `141177.35..141177.84`; these are
whole-command bounds, not timestamps of individual fields or messages.
No retry, index companion, recovery header, UI action, or power action followed.

## Relationship to the source trace

The [BA source reconstruction](../mute-request-consumer-20261027ba/findings.md)
maps `Failmode:%d` to request staging and `F-Set`/`F-Clr` to later consumer
branches. Those consumer messages follow attempted writes but have no
post-write acknowledgement. Even a retained occurrence would not establish
electrical acceptance, current light output, or freshness by itself.

Bounded sink review further distinguishes the paths: the three mute-related
strings call primary logger `0x39394`, which writes this ring. The RT-P poll
instead calls `0x56c`, supplying object `0x200002b0` and continuing through
`0x1350`/formatter `0x12e2` to a retained `0x388e0` stub. That slice has no
positive connection to the primary ring; its ultimate external destination
is unqualified. A poll message must not be assumed available here merely
because the firmware contains its text.

This attempt supplies a retained late log reference and validates reuse of
the unchanged reader. It supplies no new positive evidence that those
branches ran during a physically observed blackout. The next discriminating
test remains a fresh controller-state observation paired with the owner's
confirmed visible/black state, then one controlled failing transition if a
visible control is available. AV's old clean window cannot substitute for a
new simultaneous observation.

Permission for deeper changes persists. The unresolved technical gaps are
the exact event-time branch and a qualified writable/executable/recovery
route; permission alone does not resolve them. No firmware write or flash
was attempted in this pass.
