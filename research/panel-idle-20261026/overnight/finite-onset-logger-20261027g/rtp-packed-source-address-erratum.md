# Correction to the frozen packed-source selector interpretation

The frozen `rtp-incident-record-format.md` and its accompanying verifier
retain an incorrect semantic statement about one fallback source. They said
that packed source A could be `*(uint32_t *)0x2000ba40 + 8`. The correct
fallback is:

```text
A = *(uint32_t *)0x20000494 + 8
B = *(uint32_t *)0x20000498 + 8
```

The original report and verifier remain unchanged as frozen evidence. This
additive note and `rtp-score-input-provenance.md/.py` supersede the incorrect
fallback-pointer interpretation. The retained raw controller bytes, event
log, and package have not changed.

The error was resolving the wrong member of an adjacent Thumb literal pool.
For the 16-bit literal load at VA `0xb884`, the effective literal address is
`Align(0xb884+4,4)+0x0c = 0xb894`. That pool word is `0x20000494`.
Pool word `0xb890` is `0x2000ba40`, but it is referenced by the earlier
count-reset load at `0xb7fe`, not the fallback-pointer load. Both words are
present in the source, so finding the right constants alone did not verify
their individual uses. The new verifier checks the actual load encodings
and their PC-relative targets.

There is consequently no pointer/count overlap in this path. The halfwords
at `0x2000ba40+2*i` are six per-invocation qualifying counts: cleared before
the scan and incremented by exactly one for each accepted category path.
The final accumulator consumes delayed history of those counts; it does not
add each printed lane's difference amplitude.

This correction does not alter the packed four-12-bit-lane format, the
`abs(A_lane-B_lane)` arithmetic, the printed fields, the two fixed source-A
choices, the independently traced event predicate, or any live capture
acceptance. The V6 record still does not identify which source-A selection
was active. It must not be used to infer physical pixel coordinates or
assign electrical units to either source.
