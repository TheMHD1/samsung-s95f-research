# Selected QD profile image 1: RTP scan, thresholds, and local event path

## Scope and result

This is a bounded offline trace of the second Cortex-M/Thumb image embedded in
the already copied selected profile.  No TV, root, network, controller,
emulation, EEPROM, SSB, firmware-update, or display operation occurred.

The image contains executable RTP scan/state code, not just diagnostic text.
It has a concrete progression from scan-mode gates to per-sample thresholds,
local counters, three local event codes, and state writes.  The recovered
events are **`0x338`, `0x344`, and `0x351`**, not `0x10`.  Their common setter
only writes fields in image-1's RAM object and emits diagnostics in the
decoded body; it has no recovered wire, flash, EEPROM, host, or image-0 call.

There is therefore no valid static basis to claim that RTP scanning produced
the host `RT Protect` status or image-0's internal selector `0x10`.  The two
images are independently linked from address zero, so equal-looking linked
addresses cannot be treated as an inter-image call without the missing
loader/install/runtime binding.

## Pinned input and address convention

| item | value |
| --- | --- |
| selected container | `overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin` |
| whole-file SHA-256 | `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0` |
| image-1 stored range | file `0x40000..0x5ffff` |
| image-1 range SHA-256 | `c97865a60fcf0112b0547d41dca99bcad79d5411f90d26f4048cab926a9c4a5f` |
| linked-address convention | linked image address = stored file offset − `0x40000` |
| vector table | stored `0x40200`, linked `0x200`; reset vector `0x00000369` |

All addresses below are **image-1 linked Thumb addresses**, unless an explicit
stored file offset is given.  The mapping and independent executable evidence
are in `qd-selected-profile-content.md`; this report does not reclassify the
container or claim image-1 is current/running.

## RTP strings have real instruction references

The following strings are not inferred from a bulk strings scan. Each has a
PC-relative `adr` instruction that passes the exact string pointer to the
same local diagnostic helper at `0x1bac8`:

| `adr` site | string linked address | exact string | enclosing recovered routine |
| ---: | ---: | --- | --- |
| `0xb86c` | `0xb99c` | `[RTP]START` | scan orchestrator `0xb844..0xb998` |
| `0xb952` | `0xb9d8` | `[RTP]END` | same |
| `0xbabc` | `0xbb7c` | `[RTP]Frame end` | a local scan-stage routine ending before `0xbbf4` |
| `0xbaf0` | `0xbb90` | `[RTP]On scan end` | same |
| `0xbb36` | `0xbbb8` | `[RTP]ONSEN Mode end` | same |
| `0xbb52` | `0xbbd4` | `[RTP]IO Mode end` | same |
| `0xbc14` | `0xbcfc` | `[RTP]On scan start` | mode/state update `0xbbf4..0xbcf2` |
| `0xbc30` | `0xbd14` | `[RTP]ONSEN Mode start` | same |
| `0xbc4c` | `0xbd30` | `[RTP]IO Mode start` | same |
| `0xc6d0` | `0xc784` | `[RTP]Fab scan start` | analysis wrapper `0xc670..0xc77a` |
| `0xc724` | `0xc7bc` | `[RTP]Fab scan end` | same |
| `0xc836` | `0xca58` | `[RTP %3d]RGB:%d x:%4d y:%4d/c:%4d/diff:%d/m:%s` | per-sample decision body `0xc7d0..0xca40` |

The string labels show the firmware author called this an RTP process and
named several modes.  They do not expand `RTP`, `ONSEN`, `IO`, or `Fab`, nor
identify a panel electrical fault.

## Scan mode and local state setup

The scan orchestrator at `0xb844..0xb994` obtains a local object from
`0x3afc`, tests several object/global fields, logs `[RTP]START` before its
main path (`0xb862..0xb87a`), and later logs `[RTP]END` on its exit path
(`0xb94a..0xb95c`).  It calls the mode/state update at `0xb8ce` and local
helpers such as `0x18ee0`, `0x1c32c`, and `0xcd2c`; those calls are all to
linked image-1 addresses in this decoded component.  Their semantic names are
not recovered.

`0xbbf4..0xbcf2` has actual gates for three scan labels:

* object halfwords at `+0x2468`, `+0x2436`, and `+0x24b4` each equal to one,
  coupled with separate global halfword-zero tests, select the `On scan`,
  `ONSEN`, and `IO` start logs at `0xbc14`, `0xbc30`, and `0xbc4c`;
* it derives a local mode value `6`, `4`, or `1` at `0xbc8a..0xbca6`, calls
  helper `0x1b92c`, and logs `[RTP:%s][%d]` at `0xbcae..0xbcb6`;
* it increments a local halfword counter and, after it exceeds `0x270f`,
  stores one to another local halfword (`0xbcba..0xbcd4`); and
* it clears six object halfwords beginning at `+0x2486` and `+0x249a`
  (`0xbcd6..0xbcee`).

Those are demonstrable local mode/counter operations. The meanings of the
object fields and the units of `0x270f` are unproved.

## Difference gate to per-sample processing

Routine `0xbdbc..0xbf2e` accepts two compared values in `r0` and `r1`, keeps
their unsigned absolute difference in `r6` at `0xbe20..0xbe4a`, and obtains
two threshold-like halfwords (`sl` and `fp`) from literal-addressed state.
It uses different gate combinations and passes modes to `0xc7d0`:

| branch range | precondition before call | mode argument passed on stack | call |
| --- | --- | ---: | ---: |
| `0xbe4a..0xbe74` | a global halfword is `1` and `abs(r0-r1) > fp` | 4 | `0xbe74` |
| `0xbe80..0xbea8` | a different global halfword is `1` | 6 | `0xbea8` |
| `0xbeb2..0xbede` | object `+0x2410 == 4` and difference exceeds `sl` | 1 | `0xbede` |
| `0xbee8..0xbf1e` | object `+0x2410` is 1 or 3 and difference exceeds `sl` | 1 | `0xbf1e` |

Before every call it sets bit zero of object halfword `+0x248c` or `+0x2486`.
The callee return determines whether this routine returns success-like zero or
one.  These are real threshold comparisons, but neither input value is bound
to an electrical/pixel measurement by this static trace.

## Per-sample counters and events

The called decision body starts at `0xc7d0` and has reachable continuations
through `0xca40`.  It first bounds an input index (`r7`) against two global
halfwords at `0xc7e6..0xc7f4`, checks an index-mapped word against another
halfword at `0xc7f6..0xc804`, and rate-limits the RGB diagnostic using a byte
counter below four at `0xc806..0xc838`.  That log's arguments include the
input index and local values, but its labels alone do not assign their physical
meaning.

The same routine conditionally stores samples into five local arrays at object
base `+0x1000`, `+0x1400`, `+0x1800`, `+0x1c00`, and `+0x2000`
(`0xc852..0xc8a6`), increments per-index counters, and selects several fields
for indices 1, 4, and 6.  This is concrete local collection/bookkeeping, not
a proven panel-output command.

Three threshold-and-event tails are recoverable:

| event constant passed to `0xc3e0` | exact gate summary | local effect before event |
| ---: | --- | --- |
| `0x338` at `0xc98e..0xc992` | selected counter exceeds a mapped halfword; helper `0x37a4` returns zero | calls `0x1c2c8` with `(index, 4)` |
| `0x344` at `0xc9a8..0xc9e0` | object `+0x244a == 1`; per-index counter exceeds object `+0x244c`; helper `0x37a4` returns zero | sets object `+0x249a = 1` |
| `0x351` at `0xc9e8..0xca36` | object `+0x244e == 1`; input `r8` is within inclusive object `+0x2452..+0x2454`; a global counter remains below object `+0x2450`; helper `0x37a4` returns zero | sets object `+0x249c = 1` |

The first tail's exact field identities are not named, so “counter/mapped
halfword” is deliberate. In all three cases, the source shows a finite local
predicate and event literal; it does not establish a hardware-side threshold
or physical failure condition.

## Event setter boundary

Common helper `0xc3e0..0xc412` receives the event code in `r0`. It:

1. obtains an object from `0x3afc`;
2. stores `1` to object `+0x2400`;
3. stores `0` to `+0x240e`;
4. stores `0x1001` to `+0x240a`; and
5. passes the event code to local diagnostic helper `0x1bac8` twice.

There is no branch, call, literal, or store in that bounded body identifying
an I2C transfer, GPIO/rail operation, EEPROM write, controller reset,
host-protocol serializer, or image-0 error-mask setter.  This is a scoped
positive statement about this exact helper body—not an absence claim for the
full image or a runtime guarantee.

The only other direct `BL` to this helper found in the bounded image-1 code is
at `0x223a`; it too passes a local event literal.  It does not provide a
bridge to image 0.

## Image-0 / host-status boundary

Image 0 contains the separately documented EEPROM-derived `0x10` error
selector. Image 1's RTP routines above use a different object layout
(`+0x2400`-range fields) and emit `0x338`, `0x344`, and `0x351` locally. Both
images are linked from zero, so apparent numeric function addresses are
ambiguous across images. No loader, mailbox, shared-RAM ABI, or code/data
relocation in the retained bytes binds this image-1 state to image-0's
selector, to QDF's `F3 80 00 00 00 08` query, or to the host's observed
`0x10`.

The selected container's executable content makes this a meaningful source
lead, not a repair procedure. It does not prove this image was installed or
executing, that RTP ran during a blackout, that an RTP event caused display
loss, or that any threshold/counter should be changed.
