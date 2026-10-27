# Independent source review: fixed RTP mode-window reader

Date: 2026-10-27 UTC  
Scope: offline source/build/wrapper review only; no TV, root, USB, network,
UI, reset, write, or execution of the ARM target path

## Decision

No P0 or P1 blocker was found for one bounded native invocation of manifest
SHA-256
`4d3e0ac655aff8eac8d1d2f3835d96597f74d5c45c751e67323ea36805663446`.
That invocation is exactly two target-`0x101` memory reads and four bulk
transfers:

```text
OUT 01010000a004004744000000 / IN 68
OUT 01010000c00b004710000000 / IN 16
```

Clearance is limited to that fixed read-only geometry, current boot, pinned
binary/wrapper, and one-shot no-retry state machine. It does not clear a
second invocation after any ambiguous result.

## P1 checks passed — fixed geometry and memory bounds

The two headers decode exactly as:

| order | target | DMA/bus address | length | end, inclusive |
| ---: | ---: | ---: | ---: | ---: |
| 1 | `0x101` | `0x470004a0` | `0x44` | `0x470004e3` |
| 2 | `0x101` | `0x47000bc0` | `0x10` | `0x47000bcf` |

There is no caller-controlled address, length, target, timeout, interface, or
request direction. `RealOps.Bulk` accepts only 68/16-byte IN buffers or one
of the two exact 12-byte headers. The helper contains no memory write, reset,
signal, UI action, firmware operation, or retry.

The proposed CPU spans are wholly within the selected image-1 scatter
allocation: the first span is within decompressed
`0x20000000..0x200004f7`; the second is within zero-filled
`0x200004f8..0x2000e19b`. The non-A mapper predicts the two `0x4700...` bus
addresses, and the previously returned `0x470004c0/64` response supplies the
specific root anchor for the first span. AP_RTP does not cover either range
and was not used to widen or justify them.

For the first 68-byte response the decoded offsets are exact:

```text
+0x0a  candidate aa halfword    -> proposed CPU 0x200004aa
+0x0c  candidate ac halfword    -> proposed CPU 0x200004ac
+0x22  numeric mirror halfword  -> proposed CPU 0x200004c2
+0x24  nonzero-state halfword   -> proposed CPU 0x200004c4
+0x40  root word                -> proposed CPU 0x200004e0
```

Independent Thumb decoding confirms that VA `0xc250` reads context byte
`+0x6c7`, stores its numeric value as a halfword at `0x200004c2` when it
changes, and stores zero/nonzero state at `0x200004c4`. Those fields provide
useful sequential consistency observations; they are not event-time or alias
proof.

The second 16-byte candidate also has a static local fingerprint: ordinary
startup writes little-endian halfwords `0x0870`, `0x0780`, and `0x0b40` at
CPU offsets `+0..+5`, while the callback writes AP_EXCO-derived bytes at
`+7/+8`. The independently pinned layout verifier, SHA-256
`3c2d7bfff46cae7a8b648f08c05d5cfecb8c28cbbd9d26c0047847c0993a797a`,
passes normally and under `python3 -O`. These values can provide offline
corroboration after acquisition, but are correctly absent from the helper's
transport acceptance rules.

## P1 checks passed — protocol phase and stop behavior

The native `Read` function requires `ReadyForHeader`, sets the phase to
`Unknown` before each bulk call, and advances only on an exact return count.
The first IN must return exactly 68 and restore `ReadyForHeader` before the
second header can be sent. A negative, zero, short, over-count, or exception
at the first OUT or IN therefore prevents every later vendor packet. The
same rule applies to the second read. There is no catch-path retry.

The two destination arrays are allocated before open/claim. The only
per-header clone is attempted after phase becomes `Unknown`; an allocation
exception there safe-stops rather than authorizing a fresh header. Interface
release and descriptor close are attempted in `finally` but are not treated
as protocol recovery. Native acceptance requires stage `complete`, final
`ReadyForHeader`, both raw artifacts, successful release, and successful
close.

The fake suite covers all four transfers with negative, zero, short,
over-count, and exception outcomes. It expressly checks that first-header
failure prevents first IN, first-IN failure prevents the alternate header,
and alternate-header failure prevents alternate IN.

## P1 checks passed — transport and interpretation remain separate

The first response is interpreted as a conditional image-1 mode sample only
when the same response contains root word `0x20010000` at offset `0x40`.
A different root does not relabel an exact completed USB transaction as
unknown: the native result remains transport-accepted, preserves both raw
artifacts, and marks `root-anchor-mismatch` with
`InterpretationAccepted=false`.

The second response is never promoted by native code. The wrapper result
always labels it `candidate-bus-bytes-only`, reports byte `+7` raw, and fixes
`consistency_promotes_alternate_cpu_alias=false`. Equality between that byte
and the first window's mirror is only a numeric consistency field. Even a
full match to the three startup constants and AP_EXCO bytes remains
corroboration rather than proof of the live non-A core tag or a universal
CPU/bus alias.

The reads are sequential. Neither root match nor mirror agreement makes them
atomic or reconstructs V6 event-time mode. The later ordinary gating trace
also means previously retained score latches need not have refreshed after
the fault; this helper makes no contrary claim.

## P1 checks passed — wrapper retention, accounting, and cleanup

The wrapper requires explicit `--execute`, an exact reviewed manifest hash,
a fresh absolute output directory, and the pinned 45-second remote / 75-second
host adapter. It stages exactly three build artifacts in a unique root-owned
0700 directory with 0600 files, exact inventory, size, and SHA-256 checks.
The target self-test completes in a separate root call before the one and
only active native invocation.

Before the active call, the retained record changes from zero operations to
`target_operations=null` and `inflight_or_unknown`. The complete authenticated
envelope is saved before parsing. Only an exit-zero, empty-stderr, exact
eight-step native result in final `ReadyForHeader` changes accounting to two
accepted read operations.

Both binary responses are written locally before cleanup. Cleanup is allowed
only after that exact native parse; it revalidates the complete five-file
remote inventory and hashes, removes only those files and the private
directory, and requires `STAGE_ABSENT`. Any malformed, partial, timed-out, or
otherwise ambiguous result leaves the private stage, raw call record, and
unknown-operation accounting intact. There is no retry, signal, reset, or
fallback path.

## Independent build and test evidence

All 12 manifest rows independently match current local file sizes and
SHA-256 values. Material pins are:

| artifact | SHA-256 |
| --- | --- |
| `Program.cs` | `6770c29a29cd0751448f2c9ba6da8dbfdd00d01765914df13df2d87bab7d9e63` |
| target DLL | `7fa038ade1036df274fd33785ba287db0042b986846b9b6326ab5a9a8e2100c3` |
| `run-once.py` | `67a485873f318323f89d337cdecd8a83c0c3238f5bfb8ac9b861b253e1f954ad` |
| `test-wrapper.py` | `62acb222f5b0fe46eec4856e5d2855e567ef2bfd55f6bfe5a5b187b161493e5c` |
| `build-derivative.py` | `45da7c20409e230b54787c833f46872e884dde4bcafece416f5e0df326115e9f` |
| `build-offline.py` | `b925468925f3f435ab6c8610eec47804fcf2c47e4d691babc722306b4de7b094` |

Independent zero-I/O executions produced:

```text
native self-tests       35, targetOperations 0
wrapper normal          22, targetOperations 0
wrapper optimized       22, targetOperations 0
host --execute          REFUSED_ARM32_ABI, exit 64
native/wrapper dry      exact two-read geometry, writes 0, retries 0
manifest verification   12/12 rows exact
```

The diff from the previously reviewed fault-context reader changes fixed
geometry, result names/decoding, root-gated interpretation, and associated
tests/wrapper output. Device identity, FD validation, claim/release/close,
bulk ioctl shape, descriptor checks, boot pin, timeout, and root adapter are
retained.

## Remaining limits

- The live secondary core tag is still unobserved.
- The alternate window remains raw candidate bus evidence even if all static
  fingerprints match.
- A matching first root anchors only that small sampled block.
- Both values are late and sequential, not incident-time state.
- No physical picture, cause, protection consequence, or repair is proved.

