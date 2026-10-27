# Independent review: SSB firmware-acquisition boundary

## Outcome

**CLEAR for the bounded offline conclusions in the two reviewed reports.**  I
found no remaining material factual blocker after the reports were corrected
to include the USB runtime-PM calls and to limit the live USB evidence to the
device-parent and named paths that were actually sampled.

This is not clearance to invoke the backup/update paths.  The exact module
does contain a byte-return mechanism, but the reviewed evidence does not show
an ordinary passive or currently exposed route for acquiring a validated copy
of the controller's advertised 2 MiB F77 firmware.

## Exact reviewed bytes

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| `sdp_pqe_frc.ko` | 1,015,070 | `1a312cf33a0ca67c170b9dc73a56a58fa03a0f05bbfb6277a72740dd8e7328a4` |
| `qd-ssb-readback-acquisition-boundary.md` | 15,433 | `911c230c3509752f318af6e8ca7aa846547510c41c28a4fcdcbb02f6c72c7607` |
| `qd-ssb-readback-acquisition-boundary-reproduce.py` | 11,594 | `346c57dfb64e29f56baa41dd1e62a62b68ba20e43e868247fc6b9f27393ea4b0` |
| `ssb-transport-driver-binding.md` | 10,997 | `c35361bce02aae2946b5b0f4e22cab80af20c348c63a4cafd9267f3cfb05bbe7` |
| `ssb-transport-driver-binding-reproduce.py` | 5,047 | `5ac6dd6b87e37fd9e0369f5923f0a5f4acb32cbe0dd42c1f21a563b565b7404c` |
| registration metadata response | 5,209 | `2807922e63b27c2aef8d9b3ad9c9b5eb3b20a49f5d6e2808928784b6bff48351` |

The older named-node metadata response was also checked at SHA-256
`a306d32dfa3dfd1e214fbcb22625bff5ade0d26957cbdf6e2516a26b2f759952`.

Both checkers passed under ordinary and optimized Python; both compiled with
`py_compile`.  I also checked the relevant module bodies, relocations, and
strings directly rather than treating checker PASS as proof of the complete
control flow.

## Material findings independently confirmed

1. **The apparent read paths are not a passive firmware dump.**
   `tcon_read_fw_data` at `.text+0x588b8` has only the two recovered callers
   inside `_upgrade`, at `0x472c` and `0x4940`; their corresponding regions
   call `_write_data` first at `0x46b0` and `0x4880`.  The separate backup path
   at `.text+0x58a68` is reachable through the module's SSB ioctl dispatch, but
   `_read_data` opens `/dev/ssb1` or `/dev/ssbs1` with `O_RDWR`, transmits a
   12-byte target/address/length header, and only then performs a bulk-in read.
   The higher-level backup also creates or truncates its host output with
   `O_WRONLY|O_CREAT|O_TRUNC`.  This is active controller-facing I/O plus a
   host-file side effect, not an ordinary read-only filesystem acquisition.

2. **Open/close has an additional power-management side effect.**
   `resolve_usb_symbols` stores `usb_autopm_get_interface` at callback-table
   `+112` (`0x5b258..0x5b26c`) and `usb_autopm_put_interface` at `+48`
   (`0x5b118..0x5b12c`).  `ssb_open` calls the first at
   `0x5a138..0x5a140`; `ssb_release` calls the second at
   `0x5aaa0..0x5aab0`.  A successful open can therefore resume the USB
   interface, and release drops that runtime-PM reference.  The corrected
   reports accurately limit their narrower negative claim to no explicit
   vendor/controller power helper, reset, erase, restore, or replacement-data
   writer in the selected backup body.

3. **The nominal 5 MiB result has insufficient transfer validation.**
   `_read_data` checks only whether the 12-byte header write and response read
   are negative; zero or positive short transfers are accepted.  Its caller
   copies the requested chunk size from a `vmalloc`, not `vzalloc`, buffer.
   `_backup_data` similarly accepts a nonnegative short host-file write, and
   `ssb_ioctl` discards the backup callee's status.  Consequently neither an
   ioctl success nor a nominal 5 MiB output length proves complete or fresh
   endpoint bytes.  The reports correctly describe the extent as nominal and
   do not claim that a short transfer occurred on the TV.

4. **Static USB matching is not live endpoint identity.**
   The module's first USB ID record matches vendor/product `04e8:2001`, and
   the retained metadata contains a cached Samsung `STL1 CDC and Bulk` device
   with those IDs.  However, the sampled `driver` link belongs to the
   device-parent and resolves to the generic `usb` driver.  The command did
   not inspect `7-1:1.x` child-interface driver links.  It did show the exact
   named `/dev/ssb*`, `usbmisc/ssb*`, and USB-driver `*ssb*` paths absent and
   `sdp_pqe_frc` live/refcount zero at that timestamp.  This does not prove all
   interfaces unbound, explain the missing named interface, identify the
   endpoint as the QD MCU, or bind target `0x203` and the 5 MiB address space
   to the 2 MiB F77 image.

## Bounded conclusion

The retained binary establishes a driver-registration path, a matching USB
ID, and controller-facing readback machinery.  It does not establish a
passive, integrity-checked, currently available acquisition path for the RT
Protect producer firmware.  Invoking the backup ioctl would add USB-driver
registration when needed, repeated runtime-PM get/put, repeated bulk-out
request headers, bulk-in transfers, and host-file creation/truncation.  No
such invocation was performed during this review, and none of these findings
establish incident causality or a repair.
