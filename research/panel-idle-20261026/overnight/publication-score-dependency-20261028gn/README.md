# GN: publication helper effects and the remaining score dependency gap

`1c0c8` is a RAM status-OR helper. Its only callee is the root getter; it performs no direct hardware operation in the inspected closure. This supersedes the earlier GD/design shorthand **“hardware action”** for that address. The predicate calls the helper **before** the separate fault setter. The setter does not call the helper. Frozen GD, its reviews and publication history remain unchanged.

This narrows a confound; it does not establish that changing c4 affects only the comparison. c4 also supplies the publication bound. Publication admits additional log calls, status updates and record stores, and a different configuration directly couples publication saturation to a fault path. Full score/reference independence remains unresolved.

All work here is host-only source analysis. No target, root, network, control, executable patch, binary installation or firmware modification was performed. The retained OEM asset is read in place; no OEM binary is copied into this directory. This is an author source audit, not an independent review.

## Source and coordinates

The selected 5,242,880-byte `selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin` is SHA256 `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`. Image1 is FILE `0x40200..0x60200`, linked VA `0..0x20000`; **FILE = VA + 0x40200**. Addresses below are image1 VAs, CPU addresses or explicit root-relative offsets. `source-audit.json` pins exact exclusive-ended spans, decisive instructions and literals. `input-pins.json` pins retained dependencies and existing decoder/emulator files. Source identity does not attest the executing image.

## Direct helper closure and callers

| Edge or operation | Exact coordinates and meaning |
|---|---|
| Helper inputs | `1c0ca/1c0cc` save r0 mode and r1 OR-mask value. |
| Root | `1c0ce→38fc`; `38fc..3900` dereferences CPU `200004e0` (literal `3904`). This root is mutable. FN guards the sampled root `20010000`; it is not a continuous attestation. |
| Status update | Mode1: read/OR/store root+2486 at `1c0e6..1c0f2`; mode2: +2488 at `1c0f6..1c102`; modes4/6: +248c at `1c106..1c122`. Other supplied modes return without a status store. |
| Publication | `c63c` supplies mask **0x2**, `c63e` supplies formatter r4 mode, `c640` calls the helper. The print-budget bypass also reaches this call. |
| Aggregate fault | After strict `R7>FP`, `202e/2030/2032` supplies mode and mask **0x4**. `2036/203a` then calls setter `c1e0` with event736. |
| Setter | `c1f0/c1f8/c200` writes stop1 / ordinary gate0 / fault0x1001 at root+2400/240e/240a. `c206/c20e` separately logs the same event twice. Its direct callees are root getter and logger, not `1c0c8`. |

The status helper's complete body `1c0c8..1c12c` contains only four alternative halfword stores and one direct call to `38fc`; there is no indirect call in that body. For a root in guarded RAM these stores are RAM flags, plus the function's stack writes. There is no direct H/current-count/reference/record-array store in this closure. This does **not** resolve readers of those flags elsewhere or downstream electrical effects.

Positive additional flag writers are header clears `badc/bae0/bae4`, and unpacker OR-mask **0x1** stores `bc64/bc96/bcce/bd0e`. The identified reads in these helper/unpacker slices are read-modify-write reads. GN does not claim a complete writer or consumer census.

## Publication and score paths

| Source-backed path | Consequence |
|---|---|
| `bdf0..be0a` copies C7-selected root+24c4, otherwise +2430, into CPU200004ca (literal `c03c`). `1e98..1eac` separately selects the comparator FP. | c4 has both comparison and publication uses. |
| `c5f6..c604` admits ordinal `<= bound`. `c606..c638` conditionally formats a detail log; `c640` ORs status; `c64c/c650` independently requires ordinal<512 for five record stores `c666/c676/c686/c696/c6a6`. `c6b8` increments the ordinal. | Stable bound200 permits ordinal0..200, below the recovered array capacity. Capacity is a finite index argument, not global safety or causality. |
| Publication bypass `c604→c6de→c708` still increments u16 current count at `c718`. Both admitted and bypass paths update lane state: `c72e` increments CPU2020af10[x] when root24d2!=0; otherwise `c736` sets CPU2020b698[x]=1. | For entries reaching this qualifying path, saturation does not cap qualifying-count or lane-state production. Earlier B qualification can bypass this whole path. |
| `bbdc..bc1e` transfers prior lane state through CPU2020a788 and CPU2020a000. `c8a0`/`2740` or `ca10` uses CPU2020a000 and CPU2020be20 with root24d4/24d6 to compute T, mirrored at root+f04. | There is a positive lane-state→later-T path beyond the publication gate. T helpers also update their per-lane counters. |
| Predicate `1e68..2042`, under root249e==1 and busywait availability, moves current count into history, filters q, adds oldest history to H (`1fd4`), conditionally subtracts T (`200a`), and compares H low16 (`2012/2016`) against FP at `202a`. | These bounded predicate/T slices have no identified direct read of status+2486/2488/248c or the publication record arrays. That is a local dataflow result. |
| `c738/c740` skips the nonaggregate publication test when root249e==1. Otherwise `c742..c792` tests ordinal against bound and can adjust ordinal or call status-OR4 then setter event824. | Publication state can directly affect fault selection in another configuration. Global independence is false; this branch is bypassed by the sampled aggregate profile249e==1. |

## Reference and alias boundary

A positive root-base per-lane table store is `b912`: when CPU200004a2==1 and root246e==1, `b8e8..b91e` writes `root[2*i] = byte(CPU2000c95c[i]) + 2*u16(CPU2000ba4c[i])`. It is outside the helper closure. Frame-end `b8cc/b8d4/b8dc` and initialization `cb8c/cb94/cb9c` clear X/Y/RGB publication arrays; these are distinct from that root-base store. Their existence does not identify the input/reference epoch of an actual comparison.

The upstream dispatcher resets six current counts (`b800` loop), obtains two dynamic buffers through `18ce0` at `b80e/b818`, and passes selected pointers to unpacker `bd58` at `b84c/b874/b88a`. GN stops at that concrete input/selector boundary. It does not close those buffers' producer, alias, DMA or crosscore relationships to root-base tables or diagnostic arrays. It also does not close logger `1b8c8`, busywait `35a4`, caller scheduling, unknown flag readers, bulk/computed copies, or other executing images. No exhaustive alias or whole-firmware electrical claim follows from direct-store absence.

## Experimental implication and reproduction

The frozen GJ analyses report max sampled H36 at200 and H48/fault at40. Entry C/N/H/L matched, while R latch/c4 and M/P/history differed. These are retained observations, not actual FP-register measurements or a matched reference/input epoch. GN provides no clean200 score>40 witness and no causal, physical-image, fix or electrical-safety conclusion. Raising c4 can change diagnostic work and timing even though the helper is only a RAM OR.

Run from this directory:

```sh
python3 -B audit.py
python3 -O -B audit.py
```

All 3850 checks use explicit exceptions. The auditor verifies external pins, 17 source spans, 92 decisive instructions and20 literals, then executes the **real unmodified helper and real root getter**, without callee stubs, in128 finite host cases: two RAM roots, eight mode values, masks2/4 and four initial status values. It checks return, callee-saved registers, SP, every memory write and resulting statuses. Only four prologue stack writes plus the selected halfword OR occur; the bounded runs take at most26 instructions including return sentinel. This is synthetic helper qualification, not a target invocation or firmware-loop equivalence test. Normal and optimized outputs are byte-identical. `build-derived.py` reproduces only derived coordinates/hashes/pins; it writes no OEM bytes. The existing cached tools are required; this package does not install them.
