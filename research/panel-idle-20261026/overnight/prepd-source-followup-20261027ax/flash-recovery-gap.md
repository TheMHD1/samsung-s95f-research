# Flash/recovery evidence gap

Recorded 2026-10-27 UTC. This is an offline reconciliation of retained local
evidence. It made no TV, network, root, USB, device-node, updater, TEE,
controller, firmware, flash, reset, or protection operation. Owner willingness
to flash if necessary does not change the requirement that a recovery route be
proved before a write that could strand the controller.

## Decision

We possess one strong, hash-verified **readback** of the QD 5 MiB target, but
we do not possess a proved **restoration path**. No retained evidence shows
that the relevant write/restore transport remains reachable after an
interrupted or corrupt controller image, or that it can restore and verify the
saved bytes before normal controller firmware is running.

That is the single most important missing recovery proof. A backup that can be
read only through the firmware being overwritten is not, by itself, brick
recovery.

## What is actually retained

| Artifact | Concrete retained evidence | What it is not |
| --- | --- | --- |
| Current target-`0x203` storage readback | `firmware-fingerprint-20261027d/full-backup-recovered/fixeddata.bin`, exactly 5,242,880 bytes, SHA-256 `f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562` | Not a main-TV eMMC image, not a proved 2 MiB F77 SPI image, and not proof of an active/executing slot |
| Acquisition transcript | One 12-byte request followed by 640/640 exact 8,192-byte replies; all chunk hashes/counts/order retained; release/close succeeded; full stage removed | Not proof that the firmware's ignored leaf storage-read status succeeded or that every byte was fresh physical storage |
| Cross-checks | First 32 KiB matches the independently acquired continuation probe; six fixed sectors match; all 5 MiB were replay-audited; independent review reproduced the final hash | Not an independent device-side checksum, signed image verification, or post-restore readback |
| Selected QD profile file | `selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin`, exactly 5 MiB, SHA-256 `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0` | It is an ordinary TV file and comparison candidate, not a backup of the current target contents |
| Selected/current comparison | Complete second 256 KiB slot matches; header differs at 13 bytes, first slot after the header at 217,090 positions, and tail at 39 positions; 217,142 positions differ overall | It does not authorize substituting the selected file for the current readback or prove which image is executing |
| Official main update member | Complete host-only `upgrade.msd`, 1,493,538,434 bytes, SHA-256 `790584c7a91391bc6e9964c8f1c4649c225d2f9e6aeffabfc5e58e8a64fb7fc3`; ZIP-member CRC32 `a8e4a70a` and clear nine-section extent reproduce | Not decrypted, not Samsung-signature-verified, not proven to contain the current QD target image, and never applied to the TV |
| Copied runtime artifacts | Hash-pinned kernel modules, selected QD file, `libteec.so`, logs and bounded controller/RAM captures | Not a full main-TV block backup, bootloader backup, secure-world backup, or complete controller nonvolatile-state backup |

The full QD readback is therefore valuable and should be preserved unchanged.
Its transport, host reconstruction, and file hash are substantially verified.
The remaining limitation is at the controller/storage boundary: the selected
operation ignores the underlying storage-read return, and no independent
device-side integrity value establishes physical target identity, freshness,
or active-slot use.

## Storage and firmware areas not backed up

The current evidence does **not** contain:

- a block-level image of the main TV's eMMC partitions, boot chain, recovery
  partitions, or secure storage;
- a recovered/decrypted set of the official MSD partitions or a verified
  Samsung package signature;
- a validated dump of the separately advertised 2 MiB F77 controller SPI
  image (`F77ABU2D20`); the copied QD modules do not contain that payload;
- a complete backup of controller EEPROM/history/configuration outside the
  unknown coverage of target `0x203`; or
- any software backup capable of repairing the physical OLED/panel defect.

The 5 MiB current readback must not be relabelled as any of those areas without
an address-space/layout binding.

## Existing write/update paths are not proved recovery paths

### SSB backup/restore pair

The copied `sdp_pqe_frc.ko` has static backup and restore functions, and its
ioctl dispatch contains separate read-backup and restore branches. That is
positive evidence that Samsung implemented a restore-shaped application path.
It is not yet a qualified recovery route:

- the dispatcher presets its wrapper return and discards the backup/restore
  callee result, so a nominal wrapper success cannot prove restoration;
- the path depends on Linux, driver registration, USB interface binding, and a
  live controller-side vendor parser;
- retained metadata initially showed the named SSB character nodes and class
  devices absent, although later bounded direct vendor reads succeeded after
  separate qualification;
- the restore body has not been validated end to end for exact input length,
  target/address extent, interruption behavior, erase/write ordering, device-
  side checksum, readback verification, or rollback; and
- no evidence shows the SSB parser is a boot-ROM/recovery service that remains
  available when controller application storage is invalid.

The existence and function hash of `tcon_restore_backup_data` are therefore
static implementation evidence, not proof that the saved file can unbrick the
controller.

### QDF file updater

The copied QDF module resolves an external firmware filename and contains an
I2C flash-upgrade implementation with write/read activity and an error-path
power cycle. Several public-looking upgrade exports are stubs returning `-1`
in this build. No current filesystem candidate has been bound to the installed
F77 image, and no updater path is established as a recovery transport that
works before the normal controller application starts.

### Stock main-TV updater

The running main-TV software reports `T-RSMFAKUC-0090-1301.0`, build
`T-RSMFAKUC-0090-REL-202607141953`. The official main archive also identifies
version `1301.0`, build date 2026-07-14. This is a strong family/version match,
but there is no positive evidence that the stock updater accepts a same-version
repair/reinstall, that it would rewrite the QD target or F77 SPI image, or that
its recovery UI/boot path remains usable after a controller-flash failure.
The package's transport CRC and section geometry are verified; its Samsung
signature and installed-state eligibility are not.

### Cipher-only route

The reviewed SWU client exposes a source-level decrypt-only command sequence,
not an installation or recovery flow. The exact trusted application/backend,
authorization, and package signature behavior remain unbound. Decrypting an
official section, even if later qualified, would improve inspection; it would
not by itself prove a safe flash or rollback path.

## Most important missing proof

Before any persistent controller write, evidence must establish an
**independent recovery boundary**:

> A transport or boot mode that is available without the controller's normal
> application image, positively targets the same nonvolatile range represented
> by the retained 5 MiB backup, accepts the exact saved image, detects short or
> interrupted writes, and provides a device-side or readback integrity check
> before handing control back to the rewritten image.

None of those properties follows from the successful read-only backup. The
critical part is independence from the image being changed; otherwise the
first failed write can remove the only known route to restoration.

## Next non-destructive qualification

The next feasible step is one bounded **offline** control-flow audit using the
already copied `sdp_pqe_frc.ko`: reconstruct `tcon_restore_backup_data` and
its direct write/verification callees far enough to answer only these points:

1. exact source-file size and target/address extent expected by restore;
2. whether short input/output and lower-layer failures reach the caller;
3. erase/write ordering and whether any readback/checksum is mandatory;
4. interruption cleanup/rollback behavior; and
5. whether initialization reaches a ROM/recovery endpoint or merely the
   already-running application vendor parser.

This uses bytes already retained locally and performs no updater invocation,
driver registration, USB request, flash write, reboot, bypass, or new firmware
extraction. If item 5 remains application-dependent, the no-brick prerequisite
is still unmet even if items 1–4 look correct. Stock-updater same-version
eligibility and Samsung signature verification remain separate main-TV
questions; neither should be used as an assumed fallback for the controller.

## Evidence boundary

This report consolidates, without repeating their scans or acquisitions:

- `code-write-readiness-20261027r/code-write-readiness.md`;
- `firmware-fingerprint-20261027d/progress.md`, `README.md`, and
  `independent-review-record.md`;
- `firmware-profile-progress-20261027.md`;
- `tcon-research/qd-ssb-readback-acquisition-boundary.md` and
  `ssb-backup-entry-audit-20261027.md`;
- `tcon-research/qd-firmware-acquisition-map.md`; and
- `tcon-research/swu-decrypt-feasibility.md`.

No claim here treats owner authorization, a readable mapping, a matching hash,
an updater function name, or an available official archive as proof of safe
restoration.
