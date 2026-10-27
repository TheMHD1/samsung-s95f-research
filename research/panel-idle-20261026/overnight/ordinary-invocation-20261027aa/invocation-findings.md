# Ordinary aggregate updater: indirect invocation and timing boundary

Recorded 2026-10-27 UTC. This is an offline trace of retained selected image-0
bytes. No TV, network-to-TV, root, USB, MMIO, write, reset, protection,
threshold, storage or firmware operation was performed. Arm's public CMSIS
header was consulted to identify a standard core-register operation.

The new positive edge is an indirect callback path into the ordinary updater.
The earlier direct-call trace stopped at `0x13710` inside `0x13464`; the
selected image also registers that routine in descriptor index 28 and contains
a matching indirect wrapper in its stored vector table. This gives a concrete
invocation mechanism in the selected image. It does not prove the currently
executing vector base, callback pointer, invocation count or cadence.

## Byte-bound path

The package is `selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin`,
SHA-256 `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
All following coordinates are linked image-0 VA; FILE = VA + `0x200`.

| selected-code edge | evidence |
| --- | --- |
| descriptor lookup `0x38c24` | returns `0x20000948 + index * 20` |
| registration `0x1e7aa..0x1e7f9` | passes index 28, saves returned descriptor in r4, loads literal `0x13465` at `0x1e8a8`, stores it at descriptor `+8` |
| wrapper `0x26988` | checks callback at table `+0x238`; when nonzero, passes table `+0x230` in r0 and BLXes callback |
| stored vector word `0x12c` | `0x26989`; under standard Cortex-M indexing this is external IRQ 59 |
| ordinary callback `0x13464` | r7 preserves its descriptor argument; call `0x13710 -> 0x2fb44 -> 0x2f5d8` at `0x2fb52` reaches the first helper |
| completion | `0x13758` branches to `0x134e4`, the stack/VFP restore and return epilogue; this is not an internal endless update loop |

Descriptor index 28, IRQ 59 and any physical interrupt source are distinct
concepts. Neither this table nor its numeric indexes establish a frame-sync
name or physical pin. The descriptor's calculated CPU address is `0x20000b78`,
callback field `0x20000b80`; no live read or new transport plan for those fields
was made. These are selected-code CPU coordinates, not qualified bus aliases.

The callback's earlier control flow can skip the helper, including its
descriptor-control bit-3 test. Several first-pass branches also return early.
The trace does not establish that every interrupt or wrapper entry executes
one aggregate update. No proposed alteration of these controls is part of
this work.

## The apparent tail call is an interrupt acknowledgement, not a delay

At `0x1374e`, the callback loads the signed byte at descriptor `+4`, calls
`0x1b024`, then returns. The helper computes a bit from `r0 & 31`, indexes by
`r0 >> 5`, and writes to base `0xe000e280`. Its finite body has no sleep,
timer wait or counted delay. This matches the standard NVIC clear-pending
operation: Arm's CMSIS defines NVIC at `0xe000e100`, ICPR at offset `0x180`,
and its clear-pending function writes exactly this indexed bit pattern.
See [Arm CMSIS core_cm4.h](https://github.com/ARM-software/CMSIS_6/blob/main/CMSIS/Core/Include/core_cm4.h)
for `NVIC_Type`, `NVIC_BASE`, and `__NVIC_ClearPendingIRQ`.

This standard-register identification does not identify the controller's
exact Cortex-M model or Samsung's device-specific IRQ source. The helper
lacks CMSIS's explicit nonnegative guard; its caller argument has not been
sampled. No register was accessed in this investigation.

## Debounce counts are not wall time

With the captured W conditions `+cc=1`, `+ce=0`, and a true `P<X` expression,
the first helper compares counter `+e2` against threshold `+e0` **before**
incrementing. Starting at zero and assuming those conditions remain true,
calls 1 through 30 increment the counter while returning F0=0; call 31
returns F0=1. Calls with a false evaluated condition reset the counter.

The late W counter value 30 does not prove thirty seconds, thirty frames,
thirty uninterrupted display updates, or the time at which the condition
became true. Gates and earlier callback returns can bypass particular work;
`+ca` is applied after the helper's first-condition counter logic. A counter
can therefore mature without that final gate enabling its output. No frame
cadence or causal three-second timeout is derived here.

## Consequence for the next capture

The current passive recorder can bracket a new RT transition, but its nominal
250 ms poll interval does not guarantee a sample of every helper invocation.
We should not promise to reconstruct the entire 0-to-30 counter ramp from
that recorder. The ordinary-input control and post-event snapshot remain
valuable, while a time-aligned invocation/counter series would be a separate
instrumentation requirement if the first pairing leaves ambiguity. This
report does not implement such an extension or change the reviewed recorder.

`verify-invocation.py` pins the package and complete bounded getter,
registration, wrapper, callback and acknowledgement slices, checks the
registration/indirect/direct edges, vector arithmetic, return epilogue and
conditional debounce arithmetic. It makes zero target operations. These are
selected-code facts and measurement limits, not a demonstrated blackout cause
or a proposed firmware patch.
