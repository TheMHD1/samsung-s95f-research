# QD SSB readback acquisition boundary

## Result

The exact copied `sdp_pqe_frc.ko` contains two distinct readback-shaped paths,
but neither establishes a passive, currently available way to recover the
owner controller's advertised 2 MiB F77 executable image.

1. `tcon_read_fw_data` can request selected address ranges in 8 KiB chunks,
   but its only two callers are inside `_upgrade`, after a corresponding
   `_write_data` operation.  In this module it is update verification, not a
   standalone firmware-dump entry.
2. `tcon_read_backup_data` is reachable through the module's SSB character
   driver's ioctl dispatch and nominally copies exactly 5 MiB to a caller-
   supplied host pathname.  It does not visibly call the erase, replacement-
   data writer, reset, or restore helpers.  It is nevertheless **not a
   read-only controller operation**: every 8 KiB request opens an SSB node
   read/write, writes a 12-byte target/address/length header to the USB-backed
   endpoint, and then reads the response.  Opening that node invokes the
   dynamically resolved `usb_autopm_get_interface`; closing a successfully
   opened file invokes `usb_autopm_put_interface`.  The get can resume the USB
   interface.  It also creates/truncates the host output file, and its
   initialization can register the USB driver.

The selected code calls target value `0x203` “EMMC_read”/“EMMC OTP read” in
logs.  Those names and the 5 MiB extent do not prove that the returned address
space is the QD controller's SPI flash, that a 2 MiB subrange is executable
firmware, or that reading it has no controller-side state effect.

Current authenticated metadata further shows `/dev/ssb1`, `/dev/ssbs1`, both
corresponding `usbmisc` class devices, and every named `*ssb*` USB-driver path
absent from the sampled globs.  A cached USB device at `7-1` does match the static ID
(`04e8:2001`) and reports product `STL1 CDC and Bulk`; its **device-parent**
driver link resolves to the generic `usb` driver.  The sample did not enumerate
the `7-1:1.x` child-interface driver links, so it does not establish their
binding state.  No named SSB driver path, class device, or node was printed,
no node was opened, and no USB transaction occurred.  The static route is
therefore not presently exposed as an ordinary filesystem read; whether SSB
registration/exposure is restricted to an update/service state remains
unproved.

This report is offline analysis only.  It gives no invocation recipe and does
not authorize the ioctl branch, SSB header, USB driver registration, updater,
restore, controller reset, or flash operation.

## Exact inputs and reproducibility

All addresses are relocatable ELF section offsets, not live kernel addresses.

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| copied `sdp_pqe_frc.ko` | 1,015,070 | `1a312cf33a0ca67c170b9dc73a56a58fa03a0f05bbfb6277a72740dd8e7328a4` |
| accepted module-copy manifest | 9,513 | `54cc98708203cee3778ba329ab8e2219c91fcb4fc82eb9f3076f283fdaad2f4d` |
| authenticated SSB-node metadata | — | `a306d32dfa3dfd1e214fbcb22625bff5ade0d26957cbdf6e2516a26b2f759952` |
| authenticated module/USB-registration metadata | — | `2807922e63b27c2aef8d9b3ad9c9b5eb3b20a49f5d6e2808928784b6bff48351` |

The offline checker
[`qd-ssb-readback-acquisition-boundary-reproduce.py`](qd-ssb-readback-acquisition-boundary-reproduce.py)
pins those inputs, selected function bytes, the SSB file-operations table,
USB match ID, read/write/count-handling landmarks, the 5 MiB loop, and the
actual absent-node evidence.  It executes no target code.

```sh
python3 tcon-research/qd-ssb-readback-acquisition-boundary-reproduce.py
python3 -O tcon-research/qd-ssb-readback-acquisition-boundary-reproduce.py
```

Selected exact identities:

| Section | Offset | Size | Function | Function-byte SHA-256 |
| --- | ---: | ---: | --- | --- |
| `.text` | `0x573e8` | 272 | `_ssb_init_func` | `1fb8e07d0e19581ac4288c5d02f67bc33ed4191d5ab6a953b4360a7ed60da8e0` |
| `.text` | `0x588b8` | 392 | `tcon_read_fw_data` | `f1c7532c75eaf0c1bdd0f9c864d12d3f03b68219e51442a71af21d447e75231b` |
| `.text` | `0x58a68` | 776 | `tcon_read_backup_data` | `44588f4b9831a2b9f87f390bb294bdc9194bfaff4ab106c1a118d40f7c056d04` |
| `.text` | `0x58dc8` | 844 | `tcon_restore_backup_data` | `ee25c0d85f4b2bfd30a6f7144e52cd53c6bb9a7adf6c5b9e2dbf6c5e0359b05d` |
| `.text` | `0x591a8` | 196 | `ssb_ioctl` | `82ed53a7b15f665257fd40a0855808b2bb9851d6aa1f25581983fa58b129dc84` |
| `.text` | `0x59290` | 388 | `ssb_do_read_io` | `cde4a51e9da347b97f05061de4dcdde0d880daaa7964c9feafaacbc2072e1adc` |
| `.text` | `0x597b0` | 1,016 | `ssb_read` | `1cb6459ded7b794e8376c50b9ac9e030cd460ba274974a71600022e26124ba91` |
| `.text` | `0x5a0d0` | 536 | `ssb_open` | `f9c0d13b752037828a497bcf8c524c16dbe0af06f0d9cb4c6e97b308f85ebfb4` |
| `.text` | `0x5a3d0` | 1,460 | `ssb_probe` | `4c6c75095f20441d2f0498a3c6424547c4ea8078d413c75833d5f89ba5b02175` |
| `.text` | `0x5aa78` | 260 | `ssb_release` | `f091a46f1d6be4b4eb1171a7fe7d4d12adfd545216c73a60bf208aa60be67c24` |
| `.text` | `0x5aba8` | 1,156 | `ssb_write` | `c56f4214239e61ba01fb90ba2ad2d0b5caf156e72bc3b9c0966720b9007328a6` |
| `.text` | `0x5b098` | 1,944 | `resolve_usb_symbols` | `b848c7dd7e94c95aa93c46c5ee842dc059b4407f68ebe9f3077583d27ffb3bca` |
| `.text.unlikely` | `0x2388` | 104 | `file_write.part.0` | `feb9ab932ea4ccd40e82f3a58a88a4f41f1bb4a43f3407045daff8cfa25f07b2` |
| `.text.unlikely` | `0x2440` | 740 | `_read_data` | `2fc860d845ca3662587f932a5f68d3c85ee26aeb75061cfb6af0f27da005a21b` |
| `.text.unlikely` | `0x27c0` | 176 | `_backup_data` | `6f91f42089233e46bc2c30d58482f11354c9437809808359c4f65f648107651d` |

`tcon_read_fw_data`, `tcon_read_backup_data`, and
`tcon_restore_backup_data` are global ELF symbols but have no `__ksymtab` or
`__kstrtab` records.  They are not kernel exports in this file.  The backup
pair is instead reached from `ssb_ioctl` through the module's own file-
operations table.

## Common SSB request/response primitive

`_read_data` is the common primitive.  Its behavior is important because the
function name alone sounds passive while the implementation is not:

1. A selector chooses literal `/dev/ssb1` or `/dev/ssbs1`; any other selector
   fails.  The node is opened with `O_RDWR` (`w1 = 2`) at `0x24f4..0x2500` or
   `0x2564..0x2570`.
2. It forms three 32-bit words from the caller's target, address, and length.
   At `0x2638..0x2650` it clears the low nine address bits and writes all 12
   bytes to the opened node through `file_write.part.0`.
3. Only after that write succeeds non-negatively does it call `kernel_read` at
   `0x26a4` for the requested response length.
4. It closes the node on every terminal path shown in the function.

That open/close pair has a further transitive side effect.  In
`resolve_usb_symbols`, the literal `usb_autopm_get_interface` is resolved and
stored in the dynamic table at offset `+112` (`0x5b258..0x5b26c`), while
`usb_autopm_put_interface` is stored at `+48` (`0x5b118..0x5b12c`).
`ssb_open` calls table slot `+112` at `0x5a138..0x5a140` and rejects a nonzero
result; `ssb_release` calls table slot `+48` at `0x5aaa8..0x5aab0`.  Thus each
attempted chunk open participates in USB runtime PM, a successful open can
resume the interface, and its corresponding release drops that runtime-PM
reference.  This is not an explicit controller reset or vendor power helper,
but it means the path cannot be described as free of power-state effects.

The module's `.rodata+0x1e18` file-operations table binds read to
`.text+0x597b0`, write to `.text+0x5aba8`, ioctl to `.text+0x591a8`, open to
`.text+0x5a0d0`, flush to `.text+0x59ce0`, and release to `.text+0x5aa78`.
`ssb_write` builds/submits a USB bulk-out transfer; `ssb_read` and
`ssb_do_read_io` build/submit the bulk-in side.  Thus the 12-byte write is not
merely a local file-position operation.

The exact USB ID table at `.rodata+0x1f20` starts with match flags `3`, vendor
`0x04e8`, product `0x2001`.  The later metadata sample found an actual cached
USB device with that vendor/product pair, Samsung manufacturer text, product
`STL1 CDC and Bulk`, and revision `0250`; it did not find an SSB interface-
named driver path, class device, or node for it, but it did not enumerate
child-interface driver links.  Probe strings say “USB SSB device” and create
`/dev/ssb%d` or `/dev/ssbs%d`.  This proves the implementation is a Samsung
USB SSB transport with bulk endpoints and identifies a currently cached
device that satisfies its top-level ID criterion.  It does **not** prove that
the appropriate interface would bind, bind the device to the owner QD MCU,
establish which physical storage target `0x203` names, or prove the
meaning/state effects of a request header.

### Error and byte-count limitations

The primitive checks only the sign bit of both `kernel_write` and
`kernel_read` results:

- it does not require the header write to equal 12 bytes;
- it does not require the response read to equal the requested length;
- a zero or positive short response is returned to its caller as status zero.

The 8 KiB temporary buffer used by both higher-level readers is allocated with
`vmalloc`, not `vzalloc`, and is not cleared in the selected path.  Therefore
a nominally successful short response can leave stale/uninitialized bytes in
the copied range.  This is a static integrity limitation, not evidence that a
short transfer happened on the owner TV.

## `tcon_read_fw_data`: update-verification-only binding

`tcon_read_fw_data` constructs target word `0x203`, a caller-selected start
address, and length, then invokes `_read_data` in chunks of at most `0x2000`.
After `_read_data` returns zero it copies the **requested** chunk size from the
temporary buffer, because the primitive does not return the actual USB byte
count.

The only calls in this exact module are `_upgrade+0x854` (`0x472c`) and
`_upgrade+0xa68` (`0x4940`).  In both CFG regions an `_write_data` call occurs
first (`0x46b0` and `0x4880` respectively), followed by the readback and CRC
comparison.  No fops entry, kernel export, or independent top-level operation
calls `tcon_read_fw_data` directly.

Consequently this helper demonstrates that the SSB protocol can return
addressed bytes, but its recovered callers are post-write verification.  It
does not supply a normal standalone firmware acquisition path and cannot be
separated from the update state machine merely by calling the internal symbol.

## `tcon_read_backup_data`: standalone entry, active transaction

`ssb_ioctl` has two small numeric branches at `0x591dc..0x59224`: one calls
`tcon_read_backup_data`, the other calls `tcon_restore_backup_data`.  The
constants are retained in the checker as disassembly evidence, but this report
intentionally does not turn them into an invocation recipe.  A notable status
bug is that the dispatcher sets its return value to zero before either call
and ignores the callee's return.  A successful ioctl return would therefore
not prove that a backup succeeded.

The read-backup branch itself:

- calls `_ssb_init_func`, which checks module/dimming state and can resolve USB
  symbols and register the USB driver if it was not already initialized;
- copies or initializes a 250-byte pathname;
- opens that pathname with flags `0x241` (`O_WRONLY|O_CREAT|O_TRUNC`) and mode
  `0666`, so it creates or truncates a host file;
- allocates one 8 KiB buffer and repeatedly calls `_backup_data`;
- uses target word `0x203`, addresses from zero in `0x2000` increments, and an
  `0x2000` requested response at each step;
- loops through the chunk starting at `0x4fc000`, then issues a final chunk at
  `0x4fe000`, for nominal output extent `0x500000` bytes.

`_backup_data` calls `_read_data` with the main SSB selector and then writes
the requested length to the host output.  That host `kernel_write` is also
tested only for negative error, not exact byte count.  Combined with the SSB
short-read issue, neither a zero ioctl return nor even a nominal 5 MiB output
length proves that every byte came freshly and completely from the USB
endpoint.  Independent length, content structure, and cryptographic integrity
would be required after any separately reviewed acquisition.

Unlike `_upgrade`, the selected backup CFG contains no call to `_write_data`,
erase, restore, reset, or an explicit vendor/controller power helper.  That
narrow fact does not make it passive: driver registration, USB runtime-PM
get/put (which may resume the interface), output-file truncation, repeated USB
bulk-out request headers, and bulk-in transactions are all observable side
effects, while controller-side read-to-clear/session behavior is unknown.

## Current availability and the 2 MiB F77 question

Two retained authenticated metadata samples were collected on the same
continuing boot and exited zero with empty stderr.  The first reported all
four expected artifacts absent:

```text
ABSENT /dev/ssb1
ABSENT /dev/ssbs1
ABSENT_CLASS=/sys/class/usbmisc/ssb1
ABSENT_CLASS=/sys/class/usbmisc/ssbs1
```

The second recorded `sdp_pqe_frc` loaded/live with module reference count zero
and only its two platform-driver links.  No `/dev/ssb*`, `usbmisc/ssb*`, or
USB driver path matching `*ssb*` was printed.  It also recorded cached USB
device `7-1` as `04e8:2001`, product `STL1 CDC and Bulk`, manufacturer
`Samsung`, revision `0250`, with its device-level driver link resolving to the
generic `/sys/bus/usb/drivers/usb`.

Together these samples prove a matching top-level USB device existed while
the named SSB character interface was unexposed.  They do not establish the
unsampled child-interface bindings, prove why the names/classes were absent,
or show whether updater/service state, driver registration, interface
claiming, or another condition would expose them.  They also do not prove the
matching device is the QD MCU endpoint.

The controller startup log separately reports “SPI Flash : 2048KB” and image
identifier `F77ABU2D20`.  The backup function instead requests a fixed 5 MiB
address interval from protocol target `0x203`.  Static code provides no table
mapping that interval to the reported 2 MiB SPI flash, no executable-image
boundary, no F77 header/signature binding, and no guarantee that the endpoint
is the same controller that emitted the startup log.  A nominal backup could
therefore be flash data, a composite address space, cached/eMMC content, or
something else; the names are insufficient to decide.

The bounded conclusion is:

- **technical byte-return capability exists** inside the SSB protocol;
- **a fixed 5 MiB backup entry exists**, without an erase/write-data/reset or
  explicit vendor/controller power-helper call in its own CFG, but with
  transitive USB runtime-PM get/put on every chunk's open/close path;
- **no demonstrated passive or currently available path exists** to obtain a
  validated 2 MiB F77 MCU executable image;
- registering/exposing the SSB interface and sending its request headers is
  active controller-facing work that is not technically ready from this
  evidence: endpoint identity, controller semantics, and output integrity are
  unresolved.  That limitation is distinct from the owner's existing broad
  diagnostic authorization.

Until a naturally existing backup artifact, protocol specification, or
independently validated endpoint/layout binding closes those gaps, the actual
RT-protection producer firmware remains unrecovered.
