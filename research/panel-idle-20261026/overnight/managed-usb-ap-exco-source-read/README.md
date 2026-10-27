# Fixed AP_EXCO source read

This is an offline-built, fixed-geometry derivative of
`managed-usb-rt-mode-read`. It has not been run on the TV. A live invocation
requires a separate independent review and is owned by the root operator.

The native program can issue only these three target `0x101` memory reads, in
this order:

1. bus `0x470002c0`, 32 bytes, header
   `01010000c002004720000000`;
2. bus `0x4500ff14`, 16 bytes, header
   `0101000014ff004510000000`;
3. bus `0x450102e0`, 32 bytes, header
   `01010000e002014520000000`.

Each read is one exact 12-byte OUT followed by one exact IN. There are no
writes, resets, retries, caller-selected addresses, dynamic pointer
dereferences, UI operations, or storage operations. A short, long, failed, or
exceptional transfer makes the phase unknown and prevents every later USB
request. Release and close are cleanup only; they are not protocol recovery.

## Evidence and interpretation boundary

The first window contains the image-1 CPU pointer slot `0x200002cc` at offset
`0x0c`. The proposed `0x470002c0` bus binding remains conditional: it is used
as a raw read, and a returned word equal to `0x4500ff14` supplies the local
self-anchor needed to interpret the other fixed windows as a contemporaneous
AP_EXCO source sample. That equality does not prove a global image identity,
the whole `0x4700...` alias, a physical condition, or a semantic setting.

The other two windows are positively inside the two contiguous AP_EXCO
startup allocations mapped through the fixed main-controller selector. The
first starts at the allocation boundary. The second contains source offset
`0x3d8` at window offset `0x0c` without reading below an allocation.

All three results are raw, sequential, non-atomic samples. The program stores
each exact returned window and its SHA-256 in the outcome immediately after
that IN completes. A later transfer failure therefore retains prior raw
evidence in native stdout. Pointer mismatch is not a transport failure: all
three raw windows remain accepted as transport evidence, while the AP_EXCO
interpretation is explicitly rejected. No live tuple or source-field meaning
is inferred.

## Host wrapper

`run-once.py` uses the already pinned margin adapter, stages a private fixed
inventory, performs one completed self-test call, and then at most one native
execution. Before that execution its operation count is recorded as
`inflight_or_unknown`; the exact count of three is recorded only after strict
validation of the terminal envelope and native outcome. Raw records are saved
before parsing. Cleanup occurs only for a fully validated, known-ready result;
ambiguous or rejected outcomes retain the stage and record for inspection.

The default behavior is dry-run only. `build-offline.py` performs the native
FakeOps tests, wrapper tests under normal and optimized Python, dry geometry
checks, host-ABI refusal, and a pinned derivative check without contacting the
TV.
