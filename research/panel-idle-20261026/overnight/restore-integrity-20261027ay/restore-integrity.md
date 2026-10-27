# SSB restore-integrity audit

Recorded 2026-10-27 UTC. This is a bounded offline reconstruction from the
already copied `sdp_pqe_frc.ko`. It performed no TV, network, root, USB,
device-node, updater, controller, flash, reset, protection, or persistence
operation. It does not provide an invocation recipe.

## Result

The static restore path is not integrity-safe enough to qualify as a no-brick
fallback. It has a concrete bounded write path, but it does **not** require an
exact 5 MiB source, does not reject positive short source reads, does not
compare header/payload write counts with requested counts, and performs no
host-side device readback or checksum after writing.

The most important new positive fact beyond AX is the exact restore dataflow:

```text
host file prefix, capped at 0x500000 bytes
  -> repeated requested chunks through _restore_data
  -> fixed header target 0x300, labelled "EMMC_write" by this module
  -> one header write plus one payload write per chunk
```

This establishes an ordinary application-side *write-shaped* counterpart to
the saved target-`0x203` readback. It still does not prove that target `0x300`
writes the identical physical address space read through `0x203`, that the
remote endpoint commits the data, or that the endpoint is available without
normal controller application firmware.

## Parent input-size behavior

`tcon_restore_backup_data` calls `_ssb_init_func`, copies a caller pathname,
and opens it read-only. It obtains the apparent file size with a seek to end,
then issues a second seek to offset zero. The second seek's return is ignored.

At VA `0x58f00..0x58f20`, the file size is compared **unsigned** with
`0x500000` and selected as:

```text
effective_size = unsigned(file_size) <= 0x500000
               ? unsigned(file_size)
               : 0x500000
```

Consequences:

- a file smaller than 5 MiB is accepted and only its apparent prefix length
  is requested;
- a file larger than 5 MiB is silently capped and its tail ignored;
- exactly 5 MiB produces 640 requested 8 KiB chunks;
- zero produces one final restore call with requested length zero; allocation
  behavior below that call still determines its eventual result; and
- a signed-negative seek result becomes a large unsigned value and is capped
  to 5 MiB instead of being rejected.

There is no magic, version, structure, hash, or exact-size validation of the
input file in this complete parent body. The path therefore cannot establish
that an input is the retained `f410...e562` backup merely because its pathname
was supplied.

## Source-read handling

For each requested chunk the parent passes a single 8 KiB buffer allocated by
`vzalloc`. `_restore_data` calls `kernel_read` for the **requested** length but
tests only the sign bit of its return. Any zero or positive short read is
accepted, and `_write_data` is still called with the original requested
length—not the actual source count.

The buffer is reused across chunks and is not cleared between reads. Thus:

- an initial short read leaves zeros in the untouched suffix because the
  parent buffer began zeroed;
- a later short read can leave bytes from the preceding chunk in the untouched
  suffix; and
- a zero-byte early EOF can retransmit an entire prior buffer while advancing
  the destination by the requested length.

`_restore_data` also allocates and frees a second buffer sized to the request,
but the retained instructions read into and write from the caller's buffer;
the extra allocation does not repair the short-read behavior.

## Header and payload writes

The parent descriptor fixes target word `0x300`, address, and requested
length. `_write_data` aligns the address down to a 512-byte boundary, splits
requests into at most 8 KiB pieces, and sends a 12-byte header followed by the
piece payload. Parent-provided addresses advance in aligned 8 KiB steps, so
the alignment operation does not change the normal parent sequence.

The module's exact string selection labels target `0x300` as `EMMC_write`;
other target values at that print site select `EMMC_writeCRC`. The restore
parent uses `0x300`, so this path does not select the CRC-labelled variant.
The label is useful implementation evidence, not a physical partition map.

All four header/payload call sites in `_write_data` test only bit 31 of the
returned count. `file_write.part.0` returns `kernel_write`'s result unchanged.
The exact bound SSB file operation normally returns the requested count after
USB bulk-out completion or a negative transport error, but `_write_data`
itself contains no equality check. More importantly, the complete restore
chain performs no bulk-in response, storage readback, byte comparison, CRC,
or signature check after a chunk or after the full file.

This supports a precise boundary:

- lower `ssb_write` observes USB submission/completion status and can return a
  negative transport error;
- the host restore chain does not observe remote storage commit or remote
  content equality; and
- absence of host readback does not prove that the remote endpoint performs no
  internal checks—it means those checks, if any, are not returned or validated
  by the audited chain.

## Error propagation and wrapper loss

Within `tcon_restore_backup_data`, negative source-read/write results stop the
loop, and the file and parent buffer are cleaned up. Nonnegative chunk returns
advance by the requested size. No rollback or restoration of already written
chunks appears in the complete parent or its direct chunk writer.

The SSB ioctl dispatcher calls `tcon_restore_backup_data` but discards its
return in favor of a preset wrapper result. Consequently, even the negative
errors that the parent does produce are not a reliable success/failure result
to that ordinary caller. Cleanup closes host/SSB files and frees buffers; it is
not a protocol abort, remote rollback, or proof of durable completion.

## Recovery independence remains unproved

The direct initialization path is ordinary running-Linux module code:

- `_ssb_init_func` consults current platform state;
- it dynamically resolves USB helpers and can register the SSB USB driver;
- `_write_data` opens the SSB character node read/write; and
- the bound file operation requires a probed per-file USB context and waits
  for bulk-out completion.

There is no direct boot-mode switch, ROM-service binding, recovery signature,
or alternate endpoint in these bounded bodies. That does not prove the remote
USB endpoint is application firmware rather than ROM; endpoint implementation
is simply outside the copied host module. It does prove that the known host
route depends on a running main-TV Linux/module/USB stack, and supplies no
positive evidence that the remote service survives corruption of the image it
is asked to write.

The no-brick prerequisite from AX therefore remains open. A write transport
that merely completes USB transfers is not yet a demonstrated recovery path.

## Scope boundary

This audit stops at the direct parent, `_restore_data`, `_write_data`,
`file_write.part.0`, `ssb_write`, file open/close, initialization, and ioctl
result boundary. It does not follow controller storage implementation,
protection, POFLG, high-bank, return-guard, bootloader, or persistence paths;
does not inspect the excluded VA `0x2f5a8`; and does not infer the remote
endpoint's internal behavior.

The next missing fact cannot be obtained by invoking this restore path safely.
It requires independent static/vendor evidence that target `0x300` is backed
by a recovery service outside the normal controller image and maps exactly to
the saved target-`0x203` range, including interruption and readback semantics.
Without that evidence, no restore or flash is qualified.

## Reproduction

Run offline:

```sh
python3 restore-integrity-reproduce.py --self-test
python3 -O restore-integrity-reproduce.py --self-test
```

The checker pins the whole copied module and exact function bodies, verifies
the parent cap/loop, source-read sign check, fixed write target, all four
header/payload sign checks, lack of host readback, initialization dependency,
USB completion boundary and ioctl result discard. Its six focused checks cover
size/chunk boundaries, first/later short-read buffer effects, function-byte
mutation, cap-branch mutation, source-count mutation, and write-call mutation.
It performs zero target operations.
