# Independent review: F300 staged-write gate provenance

Reviewed 2026-10-27 UTC, offline only. This review did not use a TV, root,
network, controller transport, capture, helper deployment, or command.

## Inputs reviewed

| artifact | SHA-256 |
| --- | --- |
| selected profile | `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0` |
| gate reproducer | `4127947c8d7850dc28f345cadc5ccc22862029b3bae065de4c91d6354feae8ee` |
| generated evidence JSON | `5981bda42e6e68c618dfbbf73b13c00548a2f325e771394d2c8c7052ccffb3f0` |
| reviewed provenance report | `53c8389ee21baddd86acc9d94cc36be08e377d991fdc9d6725630cc287ff1fda` |

The checker completed normally under both ordinary Python and `python3 -O`;
`py_compile` also succeeded. It hashes the full 5 MiB input, verifies 32
instruction landmarks, five PC-literal targets for `0x200008e8`, the two
object-root literals, PTM strings, and table targets for selectors `0x128`,
`0x160`, and `0x180`. Its evidence JSON is reproducible from the pinned
source.

## Manual CFG result

The report's central gate interpretation is correct.

```text
gate = *(u8 *)0x200008e8
if gate == 1:
    return                         # before selector dispatch
if gate == 2:
    special = *(u16 *)(0x2000ff14 + 6)
    if special == 0:
        gate = 0
        continue ordinary dispatch # any selector remains subject to later checks
    if selector != 0x180:
        return
    continue ordinary dispatch
continue ordinary dispatch
```

This follows `0x2c750..0x2c778`: `beq 0x2c75e` covers gate one;
`gate == 2` reaches the special halfword test; its zero branch writes zero at
`0x2c76c` then branches to `0x2c778`; its nonzero branch only allows
selector `0x180`. Therefore selector `0x128` is suppressed under gate one,
and under gate two only when the special halfword is nonzero. The phrase
“continue” is deliberately not “accepted”: range, alignment, and leaf checks
remain downstream.

The selector table arithmetic independently maps `0x128` to `0x2cc96`, whose
leaf masks the scalar to ten bits and stores it through the `0xef9c` root at
effective RAM address `0x2000d7c2`. The reviewed source separately maps the
reader leaf to the same `+0xa6` field. Neither static fact establishes a live
readback, panel-drive application, or incident-time gate state.

## Producer-path review

The named paths in the report are supported by their local code:

* `0x96cc` and `0xb654` respectively write literal-addressed byte one and
  zero to the same gate.
* `0x5798..0x57c4` conditionally logs `Start PTM`, calls `0x96cc`, and writes
  its separate state byte. It is not correct to read that as every invocation
  necessarily setting the gate; the report retains the mismatch/helper-return
  conditions.
* The `End PTM` branch at `0x4fcc` and the separate state path at `0x2e56e`
  call the zero helper.
* Selector `0x160` reaches `0x2555c`; its field comparisons and incoming
  value restriction precede the byte-one store. Selector `0x180` has the
  described `EXCO+6` and payload branches, including setting byte two only
  on the recovered payload-one path.

The main-loop-call context and the exact semantic meaning of `PTM`, EXCO, or
these state values were manually reviewed but are not exhaustive runtime
proof. The checker is a hash-gated landmark verifier, not an emulator or a
complete writer census.

## Verdict and limits

**CLEAR for the report's bounded static conclusion.** The firmware has a
real pre-dispatch RAM gate capable of suppressing an F300 `0x128` write, and
the report accurately distinguishes the gate-two special-selector exception.

It remains unproved whether any producer ran during the observed incident,
whether the selected package is the currently executing controller image,
whether a host frame was accepted on the live controller, and whether the
staged value affects panel output. The result does not make a read or write
safe or ready, and it supplies no basis for a protection bypass, threshold
change, or recovery action.
