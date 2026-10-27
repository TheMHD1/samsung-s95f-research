# Finite logging qualification: review decisions

The owner authorizes unattended active testing, diagnostic system changes,
protection bypass and flashing if necessary, while retaining the requirement
to avoid bricking the TV. Authorization does not establish compatibility or
diagnose the fault. This experiment concerns a volatile diagnostic logging
gate only. No physical panel output can be observed while the owner sleeps.

## First candidate blocked before live execution

The independent reviewer checked manifest
`6293e99052cac89be90b7d90a5654673106bcf5f16a853d0fd6ee3d02ba6f21b`,
native source
`abbfd7bbfafe11c4204934187600983379db1a93de9fde4fe9ac1fe3736a6991`,
and DLL
`03296496c42c01453d05a02678ef7a79d121e5822ff17097f7f6ae8b34eea3b5`.
The core passed review and all 74 simulated tests. Live use of its wrapper
was blocked for an engineering issue: the outer remote command timeout was
25 seconds, while the native ordinary deadline was 20 seconds and an urgent
restore could add up to four seconds. CLR startup, the separate self-test
process, output serialization and shell framing were outside that clock.
The wrapper therefore lacked sufficient outer completion margin.

The parent accepted this finding and sent no logging write with that wrapper.
The implementer preserved the candidate under `blocked-wrapper-revision/`.
The replacement separates the zero-I/O target self-test and uses an explicitly
pinned local transport adapter with a 45-second remote timeout and a
75-second host timeout. The original shared root runner stays unchanged.
The adapter must retain raw outcomes and never retry the native execution.
Replacement review remains separate from this record of the blocked revision.

The reviewer also noted two limits: a managed allocation failure after an
exact header may leave an explicit pending phase rather than literal
`Unknown`, although both prohibit a new header; and the success-path runtime
auditor must pin the final reviewed manifest. A failed or incomplete live
record requires separate failure analysis and must never be presented as a
successful restoration.

## Earlier core fixes retained

Parent review found a double-clock-sample hold loop that could pass `-1` to
`Thread.Sleep`, creating an unbounded hold. The implementation now samples
remaining time once per iteration and accepts only positive 1–50 ms slices.
Parent review also found that an expired logical deadline could suppress a
restore despite a known ready protocol boundary. The fixed urgent restore
retains bounded individual transfers, records rejection/deadline violation,
and does not override an uncertain or pending protocol phase.

These are instrumentation fixes, not evidence that the panel was repaired.
