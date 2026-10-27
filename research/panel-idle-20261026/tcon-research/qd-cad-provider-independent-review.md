# Independent review: QD CAD `tcon_ex_proc` provider

## Outcome

The corrected provider report is clear for its stated **offline static-analysis
scope**.  It closes the named static provider edge and establishes a host-side
file parser plus SSB byte-stream writer.  It does not establish a live callback
binding, an incident invocation, an active factory asset, the meaning of the
sampled container magic, or the physical endpoint behind the SSB transport.
Nothing in this review authorizes or recommends invoking operation `0x20`.

Reviewed frozen artifacts:

| Artifact | SHA-256 |
| --- | --- |
| `sdp_pqe_frc.ko` | `1a312cf33a0ca67c170b9dc73a56a58fa03a0f05bbfb6277a72740dd8e7328a4` |
| provider report | `d7ab562a52f2a33d5c5446a2ceffccc5afe486f4bd7d53fc828060e580e2a575` |
| offline checker | `bc470ab6bd92d226cbc82defec3cac9e1f3578ab9773e9d8d6695bf21aeff1be` |
| retained disassembly | `4338abf21f13cb6f11b41ff51838ecfe670ee8639aca6536dd8f46a078e981db` |

The checker passed under normal Python and `python3 -O`; its result is a
hash/landmark check, while the control-flow conclusions below were reviewed
manually against the exact ELF.

## Independently confirmed call and data flow

- The symbol table gives global `tcon_ex_proc` at `.text+0x58048`, size
  `0x59c`, with the matching kernel export records.  At `0x58094` it masks the
  operation to 16 bits, compares operation `0x20` at `0x580c4`, and calls the
  named `ssb_usb_device_ready` at `0x580cc`.  A false result clears request
  status byte `+30` and returns `-ENODEV`.
- On the accepted branch, `tcon_ex_proc` places the request pointer and caller
  length at stack `+0x90/+0x98`; the relocation at `.text+0x58630` binds the
  created thread to `_upgrade` at `.text.unlikely+0x3ed8`.  `_upgrade`'s first
  length comparison at `0x3fa4` requires `0x30` bytes.  This is the envelope
  length, not request command `0x30`.
- The request command is independently loaded from request `+0`.  The
  command-`0x30..0x33` dispatch is at `0x4b54..0x4b60`.  Its file-size gate
  subtracts `0x500000` at `0x4140` and accepts an unsigned remainder no larger
  than `0x100000`, giving the inclusive range `[0x500000,0x600000]`.
- `_read_data_file` opens the supplied pathname, obtains its declared length,
  allocates a buffer rounded upward to `0x200`, zeroes that buffer, and asks
  `kernel_read` for the declared length.  This is a requested whole-file read,
  not a proven complete read: `0x577f4` truncates the result into `w23`, and
  `0x57800` treats every nonzero low 32-bit result as nominal success.  There
  is no equality check and no signed-error rejection.  A positive short count
  or negative errno can therefore enter the helper's nominal-success path;
  no retained execution says either occurred.
- The comparison strings are not inline at request `+32/+41/+52`.
  Instructions `0x4c2c`, `0x4c60`, and `0x4ca0` load the same 64-bit pointer
  from request `+32`, then use pointee offsets `+0`, `+9`, and `+20` with
  bounded destination buffers.  Therefore these accesses are not beyond the
  48-byte envelope, but the pointee allocation, lifetime, and available source
  bytes are not established by the provider body.
- The file-side offsets are exact.  For commands `0x30/0x31`, the caller's
  `0x60000` bias plus the helper returns gives `0x8000a` and `0x80100`; for
  commands `0x32/0x33`, it gives `0xb000a` and `0xb0100`.  The tail field is
  `0x4ff000 + 0xe00 = 0x4ffe00`.
- For this branch, `_upgrade` supplies the buffer base, packed header value
  with target word `0x300` and initial address word zero, and the rounded
  length to `_write_data`.  `_write_data` selects the main-target path,
  resolves `/dev/ssb1`, writes a 12-byte target/address/length header for each
  transfer, and emits data in chunks no larger than `0x2000`.  `/dev/ssbs1`
  is the distinct sub-target literal.  These exact names and mechanics do not
  identify the downstream physical endpoint as a QD MCU.

This is materially more than filename forwarding: the host loads the file,
extracts fixed-offset version/profile fields, runs compatibility and CRC
logic, and then writes data.  Conversely, the selected bodies do not recover
a general section-table parser or a named check of `0xa5a55a5a`.  Literal
absence of that value in the module does not exclude a computed check or an
unreviewed helper.

## Independent audit of the 45 retained field slices

The field acquisition is preserved at
`overnight/factory-qd-data-fields-20261026a`:

| Artifact | SHA-256 |
| --- | --- |
| intent | `dceecea3167946a40dfb93c3f31e2dd5bf66688228503bf8a43996d82c0d0d0c` |
| authenticated raw response | `ad0090732901edfadd0c202e855a7bacd660af5acd1e94967710b360a849cdd0` |
| decoded field manifest | `b1f0df94dfc81d7774293314e03e668b3056709169985fc31defa0c4ea8dc327` |

The raw envelope reports authenticated UID/EUID 0, host-assisted persistent
root, unchanged global system files, exit status zero, no timeout, and empty
remote and host stderr.  The executed command is byte-identical to the intent.
Its start/end boot IDs match; uptime is `80110.13..80111.04`.  It contains one
start/end frame, nine unique file frames, and exactly 45 offset frames.  For
each source the command required a regular non-symlink 5,242,880-byte file and
the known whole-file SHA before and after the five reads.

Each decoded local slice is exactly 64 bytes, its SHA matches its manifest
row, and its bytes match the pinned raw response.  The human-readable fields
support the recovered command-family offsets: the first eight files have the
reported five-character version and nine-character VD strings at
`0x8000a/0x80100`; `BN9660751A` instead has zeros there and the reported
`06240`/`F32AHUME2` values at `0xb000a/0xb0100`.  All nine have the reported
nine-character tail at `0x4ffe00`.

These slices classify fixed bytes in candidate files only.  They do not show
which request command was selected, which file was active, or what comparison
metadata the caller supplied.  In particular, sampled values `F77ABU0D2` and
`F77ABUAE2` are not the ten-character startup text `F77ABU2D20`; the prefix
similarity is not an active-profile binding.

## Remaining limits

1. The exact provider/export closes the static name edge, but no live bridge
   pointer or invocation was observed.
2. The code proves a host parser and write-capable SSB route, not the physical
   identity, health, current contents, or execution state of the recipient.
3. The nine exact-size files are plausible inputs.  Their names, headers, and
   extracted fields do not identify the owner's active asset.
4. A passive binding would require an already-existing artifact containing
   the actual invocation pathname and comparison-metadata pointee.  Replaying
   the updater, loading modules, opening SSB targets, or copying a whole asset
   cannot supply that missing observation safely or logically.

No target, root, network, device, updater, or controller operation was used in
this independent review.
