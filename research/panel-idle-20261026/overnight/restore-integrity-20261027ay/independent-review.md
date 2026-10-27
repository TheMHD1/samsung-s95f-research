# Independent review of the AY restore-integrity audit

Recorded 2026-10-27 UTC. This was a bounded offline review of the copied host
module and AY report/reproducer. It made no TV, root, network, USB,
device-node, controller, restore, write, flash, reset, protection, storage,
or persistence operation. It did not inspect excluded VA `0x2f5a8` or any
high-storage/protection/POFLG/return-guard branch.

## Result

**PASS with no material source/control finding.** The report's conclusion is
supported: this ordinary host restore route is not qualified as a no-brick
fallback. The bounded code accepts non-exact input sizes and positive short
source reads, tests the four header/payload write results only for negativity,
does not require host-side readback/checksum/rollback, and loses the parent's
return value at the ioctl wrapper.

This is a negative qualification of the known host route, not proof about
the remote endpoint. It does not establish whether target word `0x300` maps
to the target-`0x203` readback address space, whether the remote endpoint
performs internal verification, whether data is durably committed, or whether
an endpoint outside normal controller firmware exists. The report states
those limits correctly and provides no invocation recipe.

Reviewed pins:

| artifact | SHA-256 |
| --- | --- |
| `restore-integrity.md` | `60f870b6b0c28b9fd18801b2f531574cd29afab452c90d63d74776ad93b733e9` |
| `restore-integrity-reproduce.py` | `afcddc664de92de6fabd39ac495ee606f0f7e68b751803db150ad64710a2fe75` |
| copied `sdp_pqe_frc.ko` | `1a312cf33a0ca67c170b9dc73a56a58fa03a0f05bbfb6277a72740dd8e7328a4` |

## Parent size and chunk behavior

Independent disassembly of complete `tcon_restore_backup_data` at
`.text 0x58dc8..0x59113` confirms:

- the first `vfs_llseek` result is retained as `x19`, while the reset seek's
  return is ignored;
- `cmp x19,#0x500000` plus unsigned `csel ...,ls` implements
  `min((u64)seek_result, 0x500000)`, not an exact-size requirement;
- a negative seek result therefore becomes a large unsigned value and is
  capped to 5 MiB rather than rejected;
- values below 5 MiB, including zero, are admitted;
- the loop requests full `0x2000` chunks and makes one unconditional final
  call with the remainder, so exact 5 MiB yields 640 8-KiB requests and zero
  reaches a final zero-length request; and
- both restore-call results are accepted with `tbz bit31`, with negative
  results stopping cleanup and nonnegative results advancing by the requested
  amount.

The report properly qualifies the zero-length case: downstream allocation
behavior decides the actual result. It does not claim that a zero-byte
restore succeeds.

## Source reads and retained-buffer effect

Complete `_restore_data` at `.text.unlikely 0x2ed0..0x2ff7` confirms that it:

1. obtains the requested length from descriptor `+8`;
2. calls `kernel_read` into the caller's reusable parent buffer;
3. tests only bit 31 of the returned count;
4. reloads the original requested length and address from the descriptor; and
5. calls `_write_data` with that requested length, not the actual read count.

The separately allocated request-sized buffer is freed but is not the buffer
passed to `kernel_read` or `_write_data`. Because the parent buffer came from
`vzalloc` and is reused, the report's short-read consequences follow:
untouched bytes are initially zero, later untouched bytes can retain prior
chunk data, and a zero-byte full-size read can retransmit a prior 8-KiB
buffer. For a shorter final request, only that request's prefix would be sent;
the report uses “can,” so it does not overstate every EOF geometry.

## Write results, completion boundary, and wrapper return

Complete `_write_data` at `.text.unlikely 0x2b90..0x2e4f` contains exactly
four static calls to `file_write.part.0`: header/payload calls for the repeated
full-piece path and header/payload calls for the final piece. The exact
post-call checks are:

- `0x2d58: tbz w19,#31`;
- `0x2d84: tbz w0,#31`;
- `0x2dcc: tbz w0,#31`; and
- `0x2dfc: tbz w0,#31`.

There is no requested-count equality comparison at these sites.
`file_write.part.0` returns `kernel_write`'s result unchanged in `w0`.
The target word is fixed to `0x300` by the parent; relocation/string binding
and the `cmp/csel` at `0x2cb4..0x2cc8` select the module label `EMMC_write`
for that word, not the `EMMC_writeCRC` label. This is string/control-flow
evidence only, not a physical partition or remote implementation map.

The complete bounded parent/direct-writer chain has no mandatory post-write
bulk-in, device readback, content comparison, checksum, signature validation,
or rollback. The lower `ssb_write` body waits for the USB bulk-out path and
can return a negative transport error or the requested count after its local
completion logic. That establishes a host USB-transport boundary only; it
does not expose remote storage commit or equality. Absence of a returned
remote check does not prove the endpoint lacks internal checks.

Finally, `ssb_ioctl` sets its own result to zero before calling
`tcon_restore_backup_data` and returns that preset value, discarding the
parent's result. Thus even errors that propagate through the parent are not a
reliable ordinary ioctl success/failure result. Host file close, descriptor
close, and buffer frees are cleanup, not remote abort or rollback.

## Initialization and recovery limits

`_ssb_init_func` either uses existing initialized state or consults current
platform state, resolves USB symbols, and registers the SSB USB driver.
`_write_data` opens the SSB character path and depends on its probed per-file
context. These are positive dependencies on the running Linux/module/USB
stack. They do not identify the controller-side implementation as application
firmware or ROM, and the absence of an alternate service in these bodies is
not a universal absence proof. The report stops at that correct boundary.

## Reproduction quality

Normal and `python3 -O` self-test executions both exit zero and emit identical
JSON. The six focused checks reproduce the unsigned size/chunk boundary,
first/later short-read tail effects, exact function pins, cap branch,
source-read sign check, and write-call inventory. The verifier additionally
pins the eight relevant complete function bodies, the two string relocations,
all four sign-only write sites, initialization calls, lower transport body,
and ioctl result-discard edge.

The compact JSON reports `target_operations:0` and the intended conservative
booleans: no exact-size requirement, no negative-size rejection, no positive
short-read rejection, no explicit short-write equality rejection, no host
readback/checksum, no observed remote commit/verify, and no proved independent
recovery endpoint. Root's saved normal/optimized output hash is
`6c784a7168d83147c19ad6bb3bfd7516ca947a148926dab951dd59aeeecd80e7`.

No restore, flash, or further source expansion is justified by this audit.
