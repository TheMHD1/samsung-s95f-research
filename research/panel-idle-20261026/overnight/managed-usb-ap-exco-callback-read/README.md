# Fixed AP_EXCO callback-source read

This is an offline-built, fixed-geometry derivative of the reviewed
`managed-usb-ap-exco-source-read` transport. It has not been run on the TV.
A live invocation requires separate independent review and explicit root
authorization.

The native program can issue only these three target `0x101` reads, in order:

1. bus `0x470002c0`, 32 bytes, header
   `01010000c002004720000000`;
2. bus `0x450158a8`, 16 bytes, header
   `01010000a858014510000000`;
3. bus `0x45015c70`, 32 bytes, header
   `01010000705c014520000000`.

Each read is one exact 12-byte OUT followed by one exact IN. There are no
writes, resets, retries, caller-selected addresses, dynamic pointer
dereferences, UI operations, or storage operations. A short, long, failed, or
exceptional transfer makes the protocol phase unknown and prevents every
later USB request. Release and close are cleanup only, not recovery.

## Geometry qualification

The additive M lineage correction identifies callback getter slot
`0x200002cc`, conditionally observed at pointer-window offset `0x0c`, with the
expected mapped object pointer `0x450158a8`. The corrected AP_EXCO registry
entry has object extent `0x3ec`, so its inclusive mapped extent is:

```text
0x450158a8 .. 0x45015c93   object offsets +0 .. +0x3eb
```

The base window covers offsets `+0..+0x0f`. The tail starts at object offset
`+0x3c8` and ends at `+0x3e7` inclusive (`+0x3e8` exclusive), leaving the
last four qualified object bytes unread. Callback source offset `+0x3d8` is
therefore returned at tail offset `0x10`, not `0x0c`.

The native result records raw source bytes `+0`, `+1`, and `+0x3d8`. The
ordinary callback copies source `+0x3d8` to retained context `+0x6c7` and
source `+0` to context `+0x6c8`; source `+1` is separately loaded into `r8`
and remains semantically unnamed here.

The pointer window is still a content gate rather than a global alias claim.
All exact raw windows are preserved regardless of pointer equality. A pointer
mismatch accepts complete raw transport but rejects callback-object
interpretation.

## Interpretation boundary

The three reads are sequential and non-atomic. If the pointer gate matches,
the two monitored source bytes may be compared numerically with the earlier
saved context candidate (`source +0 == 3`, `source +0x3d8 == 1`) only as a
late sequential correlation. No tuple, event-time equality, writer, mutation,
causality, physical unit, or field meaning is inferred. Source `+1` has no
context-default comparison.

This helper intentionally makes no comparison with the ordinary AP_EXCO
`20/0` package values: those belong to different objects at `0x4500ff14` and
`0x4501024e`. It does not use them as callback-source defaults.

The retained N capture returned exact selected-package bytes for three
nonadjacent selector-1 code windows. That strongly corroborates this code
view but does not prove current execution, whole-image/core identity, or that
the captured instructions ran during the physical fault.

Pinned qualification inputs include:

- M checkpoint manifest
  `26b5cc4faa8a3c03917b92ac48254ba359362bd201830cdf29fb229154b3dd0b`;
- M source-lineage erratum
  `d2e4492bbdb7042479ebfed6a5e2300feb5f97387d68700f14924651f9c1030f`;
- M pointer-layout verifier
  `ccbc619eb4ddba2078f162bc1de520f9cb90aec0a9422d13015cbf13d393b1cd`;
- N capture result
  `3119fb85c08b970794adcdf975313d825c80a301b995e293f2fc5cb458df57c1`;
- N raw code windows
  `8be303fddfa4aefd0f2d307f05c7522213f8017ae15b374a4fd7178aeca2bb49`,
  `0483a632a5e65f8eba8bd623411d6f955705d012c831eac9347e7f9564d944cb`,
  and `035d13a7c17ac9b303ee5739a421a84d0ceec46167d6efce13f4723fc701d9b8`.

## Host wrapper

`run-once.py` uses the pinned margin adapter, stages a private fixed
inventory, performs one completed self-test call, and then at most one native
execution. Before execution its target-operation count is recorded as
`inflight_or_unknown`; the exact count of three is recorded only after strict
terminal-envelope and native-outcome validation. Raw transport is saved before
parsing. Cleanup occurs only for a fully validated known-ready result;
ambiguous or rejected results retain the stage and authenticated record.

The default is dry-run only. `build-offline.py` pins the parent and evidence,
runs the native FakeOps tests, wrapper tests under normal and optimized
Python, exact dry geometry, host-ABI refusal, and the mechanical derivative
check without contacting the TV.
