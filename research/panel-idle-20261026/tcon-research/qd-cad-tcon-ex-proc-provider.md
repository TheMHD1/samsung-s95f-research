# QD CAD `tcon_ex_proc` provider and 5 MiB consumer boundary

## Result

The exact installed candidate closes the previously missing named edge.  The
ordinary module file
`/lib/modules/5.4.261/kernel/soc/sdp_pqe_frc.ko`, copied byte-for-byte as
`overnight/sdp-pqe-frc-provider-copy-20261026a/sdp_pqe_frc.ko`, exports
`tcon_ex_proc`.  Its operation `0x20` branch gates on the module's
`ssb_usb_device_ready` helper and starts `_upgrade` with the caller's 48-byte
envelope.  `_upgrade` opens the pathname supplied in that envelope, requests
a whole-file read into host kernel memory, extracts version/profile strings at fixed
offsets, performs version/CRC policy, and passes selected regions to
`_write_data`.  For commands `0x30..0x33`, `_write_data` uses the module's main
SSB target and a 12-byte target/address/size header followed by data writes.  This
is a host-side parser and byte-stream writer, not a handoff of a filename to a
controller-side file loader.

The nine factory files are therefore plausible inputs to this exact consumer:
each is exactly `0x500000` bytes, while the `0x30..0x33` path admits files from
`0x500000` through `0x600000` inclusive.  Plausibility is not active-profile
proof.  The per-invocation request carries pointers to the pathname and to
comparison metadata; the pointee storage, size, and lifetime are not recovered,
and no persistent selected-BN cache was found.  The
retained 64 MiB incident vlog contains none of the nine complete BN tokens or
the `F_RSM1_` prefix.

The common first word `0xa5a55a5a` remains only an observed container marker.
Neither byte order occurs literally in this module, and the bounded selected
CFG does not establish a magic check or the semantic meaning of that word.
These files are controller flash-data candidates; nothing here relabels them
as the separately discussed MCU executable image.

No module was loaded, no operation was called, and no controller or TV access
was performed for this analysis.  The recovered path is write-capable and is
not proposed as an acquisition or repair interface.

## Exact provenance and reproducibility

All code addresses below are relocatable ELF section offsets, not live kernel
addresses.

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| copied `sdp_pqe_frc.ko` | 1,015,070 | `1a312cf33a0ca67c170b9dc73a56a58fa03a0f05bbfb6277a72740dd8e7328a4` |
| accepted 31-chunk copy manifest | 9,513 | `54cc98708203cee3778ba329ab8e2219c91fcb4fc82eb9f3076f283fdaad2f4d` |
| installed-module provider scan | — | `43d62d1f13fa7b4ece51ae0ddf83c530dd255b0d30ed6a2364a5e257dd11a240` |
| rescued incident vlog | — | `eac02d7bf3a4fb216295edba8be99466d7b80c7a43f7535841f882b052c1c3d3` |
| nine-file field manifest | — | `b1f0df94dfc81d7774293314e03e668b3056709169985fc31defa0c4ea8dc327` |
| authenticated field-read response | — | `ad0090732901edfadd0c202e855a7bacd660af5acd1e94967710b360a849cdd0` |

The authenticated scan examined 195 installed `.ko` files and found the
literal name only in this module and the already-known bridge
`tztv_frc_tcon.ko`.  That finite name census plus the export table identifies
the provider file; it does not by itself prove that the module or bridge
callback was live-bound during the incident.

The offline checker
[`qd-cad-tcon-ex-proc-provider-reproduce.py`](qd-cad-tcon-ex-proc-provider-reproduce.py)
pins the whole module, copy manifest, provider scan, selected function bytes,
export records, operation/worker/file/parser/writer landmarks, exact offset
arithmetic, the bounded magic census, the retained-vlog BN-token census, and
all 45 exact 64-byte field slices from the nine assets.  It does not execute
target code or replace manual CFG review.

```sh
python3 tcon-research/qd-cad-tcon-ex-proc-provider-reproduce.py
python3 -O tcon-research/qd-cad-tcon-ex-proc-provider-reproduce.py
```

The retained bounded disassembly is
[`qd-cad-tcon-ex-proc-provider.disasm`](qd-cad-tcon-ex-proc-provider.disasm).

Selected exact function identities:

| Section | Offset | Size | Function | Function-byte SHA-256 |
| --- | ---: | ---: | --- | --- |
| `.text` | `0x57678` | 180 | `_get_file_path.isra.0` | `0b1b5e374a958b24ce232f3167c37a9c75a1c55eb01ad8e8634dcc1538913239` |
| `.text` | `0x57748` | 424 | `_read_data_file` | `fd08e47a18ea7dfa71c1145d606b06abe642e66c0b0a131f3dcad6d30189ddb9` |
| `.text` | `0x57c90` | 116 | `getDataVersionAddr` | `4a07043d19b5b4c453c48a84476b7df4da218a14023c718dbb900a9221e65191` |
| `.text` | `0x57e58` | 76 | `getFWType` | `0aa8855a05edf5ffbfc0f34ea1bc5004571093bc5782ac1ea037e46610184642` |
| `.text` | `0x57f48` | 96 | `getDataregionAddr` | `e5fe21284b023486f6f573759137d37a644dc2283d2f89f30d480c6a4c0fb1e5` |
| `.text` | `0x57fa8` | 156 | `getVDAddr` | `9655989c6fce2e1a67eec8a61bfcb95858a889a28b7cd72c0c7ba886697e42a1` |
| `.text` | `0x58048` | 1,436 | `tcon_ex_proc` | `a205411955a4cb87bf9352f15feef212a6ace2d4189a9613dd0dc1e0c6165da4` |
| `.text` | `0x586e0` | 184 | `calculate_CRC` | `03443d926679211ea793ea88e5507a9f4c87b1a79264bbd86c1df70f0e15aaba` |
| `.text` | `0x588b8` | 392 | `tcon_read_fw_data` | `f1c7532c75eaf0c1bdd0f9c864d12d3f03b68219e51442a71af21d447e75231b` |
| `.text.unlikely` | `0x2b90` | 704 | `_write_data` | `a767ce1ad034ffd0f8b4a334c32755a89b7a74233bf0de8b13de60f903c5cecf` |
| `.text.unlikely` | `0x3a48` | 1,052 | `_check_version_compatibility_crc` | `eeb5c256cea273fe9c8e9fabf91e9ffaaeac76ba38ac6fdaf52aee1796066a56` |
| `.text.unlikely` | `0x3ed8` | 4,044 | `_upgrade` | `b3651bd27a4b7e246d3102f096d965917d4fd1049073cc109123ddd3f589bb1e` |

## Exact provider and operation `0x20`

The symbol table contains global function `tcon_ex_proc` at
`.text+0x58048`, size `0x59c`, along with `__ksymtab_tcon_ex_proc` and
`__kstrtab_tcon_ex_proc`.  This is the exact name that the copied
`tztv_frc_tcon` ordinary bridge resolves; it is not the distinct
`sdp_tcon_ex_proc` command-9 endpoint.

At `0x58094`, `tcon_ex_proc` masks the operation to 16 bits.  The `0x20`
compare is at `0x580c4`.  Its accepted branch:

1. calls `ssb_usb_device_ready` at `0x580cc`; a false result clears request
   status byte `+30` and returns `-ENODEV`;
2. retains the request pointer and length at stack `+0x90/+0x98`;
3. creates `_upgrade` with that stack pair as worker data at
   `0x58250..0x58268`, wakes it at `0x5829c..0x582ac`, and polls status/global
   completion in 100 ms steps;
4. uses ten-step countdown batches and a separate timer/hang path.  This is
   bounded control flow in the caller, not evidence that an invocation is
   harmless or that the worker cannot write.

The first `_upgrade` guard at `.text.unlikely+0x3fa4` requires worker-context
length `0x30` (48 bytes).  This is the envelope length, **not** CAD command
`0x30`.  The request command is loaded separately from request word `+0`.
`_get_file_path(request+8, request+16)` validates or resolves the supplied
pathname, after which `_upgrade` opens it and obtains its length with
`vfs_llseek`.

The other accepted top-level operations in this function are `0x21` (ready
status) and `0x24` (file/info diagnostics).  They are not interchangeable with
operation `0x20`, and this report does not propose invoking any of them.

## File-size and request-command routing

After opening the path, `_upgrade` enforces command-dependent size bounds.
For request commands `0x30..0x33`, the CFG reaches
`.text.unlikely+0x4140`, subtracts `0x500000`, and accepts only when the
unsigned remainder is at most `0x100000`.  Thus the admitted interval is
exactly `[0x500000,0x600000]`.  Each retained factory asset is exactly the
lower endpoint `0x500000`.

The request-command dispatch at `0x4b54..0x4b60` accepts only `0x30..0x33`
in this branch.  It calls `_read_data_file`, which opens the host pathname,
seeks to obtain its size, allocates a buffer rounded upward to `0x200` bytes,
zeros it, and requests the low 32 bits of the whole file size from
`kernel_read`.  For the observed `0x500000` size the rounded and actual lengths
coincide.  At `.text+0x577f4` the function truncates the return to `w23`, and
at `0x57800` it treats any nonzero low 32 bits as its success branch.  It does
not distinguish a positive short count from the requested count, and it does
not make the usual signed-error rejection: even a negative `kernel_read`
return has nonzero low 32 bits.  Thus a positive short read can leave a
zero-filled remainder, while either a short positive count or an error return
can enter this helper's nominal-success path.  This is a static control-flow
fact; no retained execution proves that either condition occurred.

The QDF-side analysis independently established why this branch is relevant:
the CAD caller composes `F_RSM1_<ten-character-key>_COMMON.bin`, chooses an
update command from runtime gates, and sends operation `0x20` with a 48-byte
envelope through the callback named `tcon_ex_proc`.  See
[`qd-cad-command9-consumer.md`](qd-cad-command9-consumer.md) for the upstream
split from the unrelated command-9 route.

## Recovered 5 MiB fields used by commands `0x30..0x33`

The worker does not merely copy a filename to a remote loader.  It requests a
whole-file host read and forms bounded strings from both request and file
memory:

| Purpose | Comparison-metadata source | File source for `0x30/0x31` | File source for `0x32/0x33` |
| --- | --- | ---: | ---: |
| first profile/version component (9 characters) | pointer loaded from request `+32`, pointee `+0` | `0x4ffe00` | `0x4ffe00` |
| VD component (9 characters) | same pointee `+9` | `0x80100` | `0xb0100` |
| data-version component (5 characters) | same pointee `+20` | `0x8000a` | `0xb000a` |

The file offsets come directly from caller bias `0x60000` plus
`getVDAddr`/`getDataVersionAddr`; the tail string is literal arithmetic
`0x4ff000 + 0xe00`.  The 48-byte envelope contains an eight-byte pointer at
request `+32`; the three strings are read from that pointer's separate
pointee, not from bytes beyond the envelope.  That pointee is comparison
metadata supplied by the caller, not a recovered persistent active-profile
cache.  This static path does not establish the allocation size or lifetime
contract of the pointee beyond the accesses above.

The path then either skips compatibility under its enforced-update predicate
or calls `_check_version_compatibility_crc`.  On the write path it supplies
the loaded buffer, target word `0x300`, address word zero, and the rounded file
length to `_write_data`.  Commands `0x30..0x33` classify as the helper's main target;
the writer opens literal `/dev/ssb1`, writes a 12-byte target/address/size
header, and streams data in chunks up to `0x2000`.  A separate literal
`/dev/ssbs1` exists for the sub target.  The module's own logs call this SSB
and USB transport, but the copied code does not establish the downstream
physical endpoint as the QD MCU, nor does it prove incident execution.

The worker also contains controller/SSB readback and CRC comparison paths
(`tcon_read_fw_data`, `calculate_CRC`, and `calculate_CRC_data_reg`) and status
updates at request `+30`.  Those are upgrade verification mechanics, not a
safe read-only acquisition API.

## What remains unknown about the header and active profile

All nine sampled files begin with bytes `5a 5a a5 a5` followed by 60 sampled
zero bytes, i.e. little-endian word `0xa5a55a5a`.  The provider contains
neither that byte sequence nor its reverse as a literal.  The selected branch
uses the offsets above and CRC/version helpers, but this bounded review did
not recover a compare that names or validates the first word.  It would be an
overclaim to label offsets 4 onward a section table, length, checksum, or
executable header.

No retained passive evidence chooses among the nine BN filenames.  The exact
rescued vlog was searched bytewise (important because it is not strict UTF-8)
for `F_RSM1_` and all nine full BN tokens; none occurs.  This finite negative
does not prove the profile was never selected or printed.  It only means the
existing ring cannot bind an asset.

There is also no source-backed retail-model-to-BN table here.  `QN77S95FAFXZC`,
`F77ABU2D20`, `77A3OUSOF`, and the ten-character `BN...` keys remain distinct
identifiers.  No one may be substituted for another to choose a factory file.

That bounded comparative acquisition has now been performed.  Each source
file's known size and hash was checked before and after, and 64 bytes were
retained at each of `0x8000a`, `0x80100`, `0xb000a`, `0xb0100`, and
`0x4ffe00`.  The fields used by the selected command families are:

| Asset suffix | `0x8000a` version | selected VD field | `0x4ffe00` tail |
| --- | --- | --- | --- |
| `58111C` | `12210` | `F55ABU1D2` at `0x80100` | `FA224C240` |
| `58112C` | `12220` | `F65ABU1D2` at `0x80100` | `FA224C240` |
| `59920A` | `12200` | `F55ABU0D2` at `0x80100` | `FA124C190` |
| `59920B` | `12200` | `F55ABUAE2` at `0x80100` | `FA024C190` |
| `59932A` | `12210` | `F65ABU0D2` at `0x80100` | `FA124C190` |
| `59932B` | `12210` | `F65ABUAE2` at `0x80100` | `FA024C190` |
| `59934A` | `12230` | `F77ABU0D2` at `0x80100` | `FA124C190` |
| `59934B` | `12300` | `F77ABUAE2` at `0x80100` | `FA024C300` |
| `60751A` | all zero at `0x8000a` | `F32AHUME2` at command-`0x32/0x33` offset `0xb0100` | `FB925620A` |

The first eight rows show the command-`0x30/0x31` fields; their sampled
command-`0x32/0x33` regions are binary rather than these displayed strings.
For `60751A`, the command-`0x30/0x31` version and VD fields are zero, so the
table instead reports the string recovered from its command-`0x32/0x33` VD
offset.  These distinctions are data observations, not proof of which command
would be selected for any file.

The retained controller startup text `F77ABU2D20` is ten characters and is not
an exact match for any sampled nine-character VD field, including the two
`F77...` values.  More fundamentally, that startup log and the request's
comparison-metadata pointee are different evidence sources; the static path
does not prove that the log text is what the caller supplies.  The comparison
therefore selects no owner profile and does not establish incompatibility.

The remaining useful passive binding would be an ordinary artifact that
supplies the exact invocation pathname and the caller's comparison-metadata
pointee.  Without that, copying a complete asset would add bytes but would not
identify the active one.

Neither step requires, nor justifies, operation `0x20`, `/dev/ssb1`, a
controller read protocol, an updater, module loading, or flash writes.

## Evidence limits

- The exact installed file and export close the static named-provider edge;
  they do not prove a live bridge pointer or incident invocation.
- A qualifying size and filename make the nine assets plausible inputs, not
  proof that any one was selected, flashed, or currently executing.
- The recovered parser consumes version/profile strings and CRC data but does
  not establish the semantic contract of the sampled magic/header.
- SSB writer destinations and success statuses are not panel-state evidence.
- No result explains, clears, or repairs the owner's live RT-protection bit or
  black-picture symptom.
