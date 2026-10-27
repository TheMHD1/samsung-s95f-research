# QDF firmware resolver: exact paths and bounded acquisition plan

## Result

The pinned `qdf_tcon.ko` contains an exact, finite search policy that was not
covered by the earlier four-root inventory.  Its principal roots are
`/factory_peq/tcon_data/QD/` and 20 removable-media `TCON/` directories under
`/opt/media`.  Neither root family was in that earlier inventory.  The later
depth-eight inventory closes `/prd/lib/firmware/tcon`: it contains only two
zero-byte `dummy.bin` files.  It does not close the QDF resolver roots.

The factory directory is now closed at its immediate-entry level: it contains
nine distinct, regular 5 MiB `F_RSM1_BN..._COMMON.bin` assets and no file whose
name matches the separate `TconFw...` MCU-executable grammar.  These are exact
flash-data candidates, but the owner-specific active candidate is still
**not selected** and no candidate's bytes have been acquired locally.  In
particular,
`QN77S95FAFXZC` and the controller-reported `F77ABU2D20` do not occur as
resolver constants and are not direct inputs to the path builder.  The missing
runtime gates differ by route: executable-firmware selection uses the QDF
driver's stored panel-type string, `m_tcon_type`, and `m_is_monitor`; CAD data
selection uses `m_year_tag`, `m_chip_type`, and a ten-character controller-read
string.  A separately observed userspace energy log prints panel type
`77A3OUSOF`; no acquired evidence proves that this is byte-identical to the
kernel callback value stored by QDF, so it is only a useful filename
hypothesis.

This is an offline reconstruction.  It does not call an updater, open a TCON
device, query the controller, or read controller flash.

## Exact source binding

The source is `binaries/qdf_tcon.ko`, 403,294 bytes, SHA-256
`97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63`.
The relevant exact function bodies are:

| ELF address | Size | Function | Function-byte SHA-256 |
| ---: | ---: | --- | --- |
| `.text+0x4db0` | 108 | factory `m_get_upgrade_path` | `537069e091c1cead34cd7ce2bedc711125659a78df2445a55ba3988891bfdebf` |
| `.text+0x82a8` | 540 | `m_get_cad_upgrade_file_name` | `d1d91a64e0973f337b179237554d0fe74436632bc73ae37c1524e1ae35edfa59` |
| `.text+0x8c00` | 116 | table `m_get_upgrade_path` | `d2c8d27f386844542244b1ab3b8f0486af712cd15f23a5c827e3930ec338a3bf` |
| `.text+0x8c78` | 968 | `m_tcon_flash_upgrade_se` | `c1c426cfbb86e26fa81a2d5eef7e7f51894143df187098d236563d294cd2dac2` |
| `.text+0x9200` | 444 | `QDFTcon_UpgradeFlashFirmware_se` | `0165c6d41f98d2905ab42a1a164ea4dddfe3652933c6ad29764530f2791811f1` |
| `.text+0x93c0` | 620 | `m_get_tcon_fw_file_path.isra.0` | `3b5349db232ded45b11bd1b2195c7407abbf1ca12922c8a05f0b1362b8a09f07` |
| `.text+0x12c98` | 464 | `QDFTcon_UpgradeFlashData` | `041ae8f52fadd8bb7e2b02c31a44b6a86ab40c6bcf0e170f8ab9291e318a90f0` |
| `.text+0x12e68` | 348 | `QDFTcon_UpgradeFlashDataOtp` | `6a359cbd69bdbffbcf12effe58431581d40e0d7cb6c92e7afcfc89caf5b86cb1` |
| `.text+0x13298` | 720 | `m_tcon_upgrade_data_cad` | `4618554a949d9cb72471e1eaf1e7ff16b2e906842ceb25a986e8343d4d1e1d47` |
| `.text+0x13568` | 152 | `QDFTcon_UpgradeFlashDataCAD` | `ec61b2d0b08192814460a0a16801ef9db00716aa65e8b0c79a17a8264dd8fa51` |

The companion offline checker
`tcon-research/qd-firmware-resolver-exact-paths-reproduce.py` pins those bytes,
the symbol sizes, the table and strings, the resolver/caller relocation
landmarks, and all four new read-only filesystem responses.

## Resolver algorithm at `.text+0x93c0`

The arguments are an integer source selector, an output path buffer, and an
already-selected basename.  The function first formats
`<basename><literal .bin>`.  It then takes one of two branches:

* selector zero copies literal `/factory_peq/tcon_data/QD/`, formats the
  directory plus filename, and returns without testing the file;
* selector nonzero iterates the 20-entry table below.  Each entry is exactly a
  255-byte record in `.rodata+0x2120`.  Indexing is `index * 255`.  The helper
  appends literal `TCON/`, the resolver appends the filename, and
  `ft_file_open(path, 0)` probes it.  It closes and stops on the first non-null
  file handle.

The loop checks indices 0 through 19.  A subtle but important limit is that
both “found” and “all 20 probes failed” return zero.  After total failure the
output buffer holds the final `USBDriveD4/TCON/...` candidate.  Consequently,
the resolver's return value and a printed candidate path are **not** existence
proof.  Only independent regular-file metadata can establish a payload.

The 20 literal roots, in exact search order, are:

```text
/opt/media/USBDriveA/
/opt/media/USBDriveA1/
/opt/media/USBDriveA2/
/opt/media/USBDriveA3/
/opt/media/USBDriveA4/
/opt/media/USBDriveB/
/opt/media/USBDriveB1/
/opt/media/USBDriveB2/
/opt/media/USBDriveB3/
/opt/media/USBDriveB4/
/opt/media/USBDriveC/
/opt/media/USBDriveC1/
/opt/media/USBDriveC2/
/opt/media/USBDriveC3/
/opt/media/USBDriveC4/
/opt/media/USBDriveD/
/opt/media/USBDriveD1/
/opt/media/USBDriveD2/
/opt/media/USBDriveD3/
/opt/media/USBDriveD4/
```

The actual candidate directories are each root plus `TCON/`; for example,
`/opt/media/USBDriveA/TCON/` through
`/opt/media/USBDriveD4/TCON/`.  These are ordinary filesystem paths, not a
controller-flash namespace.

## Basename and gate reconstruction

### Flash data and OTP data: the `0x93c0` resolver callers

`QDFTcon_UpgradeFlashData` passes a panel-type string, not the Samsung retail
model and not the F77 firmware identifier.  For the factory branch it copies
the 20-byte QDF global `m_strPanelType` (`.bss+0x1d0`), populated by
`QDFTcon_Tcon_SetPanelInfo`.  For the removable-media branch it calls the
imported `tztv_get_panel_type` into a 20-byte local buffer.  The resulting file
shape is:

```text
/factory_peq/tcon_data/QD/<panel-type>.bin
/opt/media/USBDrive{A,A1,...,D4}/TCON/<panel-type>.bin
```

`QDFTcon_UpgradeFlashDataOtp` formats stored `m_strPanelType` plus literal
`OTP`, then gives that basename to the same resolver:

```text
/factory_peq/tcon_data/QD/<panel-type>OTP.bin
/opt/media/USBDrive{A,A1,...,D4}/TCON/<panel-type>OTP.bin
```

These are flash-*data* routes.  The `OTP` suffix identifies the code's OTP
data variant; it does not mean the file is the controller MCU executable, an
OTP dump, or a safe extraction of one-time-programmed contents.

The CAD caller is also a flash-data route.  At `.text+0x82a8` it invokes
`m_i2c_burst_read(0, -0x3000, 0x20, buffer)`, requires the returned buffer to
be an exactly ten-character C string, and formats
`%c%s%s%s`.  The four components are:

1. QDF global `m_year_tag` (`.bss+0x19c`);
2. a family selected by `m_chip_type` (`.bss+0x48`): 8 -> `_PML1_`,
   3 -> `_OCS1_`, 11 -> `_RSP1_`, 7 -> `_PTM1_`, otherwise `_RSM1_`;
3. the exact ten-character controller-read string;
4. `_MAIN` only for chip type 3, otherwise `_COMMON`.

This is not selected from `m_tcon_type`, the retail model, panel diagonal, or
the printed firmware version.  Deriving the middle component executes a
controller I2C read, so this report does not propose it as an acquisition
method.  Its exact owner filename remains unresolved from passive host
metadata.  The nine actual filenames show year tag `F`, fallback family
`_RSM1_`, and `_COMMON` in the packaged set, but package membership does not
prove the current live `m_year_tag`/`m_chip_type` or which controller string is
active.

The nine discovered names all conform to the CAD grammar:

```text
F_RSM1_BN9658111C_COMMON.bin
F_RSM1_BN9658112C_COMMON.bin
F_RSM1_BN9659920A_COMMON.bin
F_RSM1_BN9659920B_COMMON.bin
F_RSM1_BN9659932A_COMMON.bin
F_RSM1_BN9659932B_COMMON.bin
F_RSM1_BN9659934A_COMMON.bin
F_RSM1_BN9659934B_COMMON.bin
F_RSM1_BN9660751A_COMMON.bin
```

That is format-level evidence that this directory contains inputs intended for
the CAD flash-data path.  It does not identify which ten-character middle
component the owner's controller would return.  None of the locally acquired
ordinary files, modules, reports, or logs contains a mapping from
`QN77S95FAFXZC`, `77A3OUSOF`, or `F77ABU2D20` to one of these nine BN codes.
Selecting by the shared `77` diagonal alone would be a guess.

### MCU executable firmware: separate function, same roots

Controller executable firmware does **not** enter through `.text+0x93c0`.
`QDFTcon_UpgradeFlashFirmware_se` selects a basename and passes it to
`m_tcon_flash_upgrade_se`, which appends the same `.bin` suffix and uses the
same factory root or 20-root removable-media search.  The exact selection is:

| `m_tcon_type` | Additional gate | Exact basename |
| ---: | --- | --- |
| 14 | `m_is_monitor == 1` | `TconFwRoseM2` |
| 14 | otherwise | `TconFwRoseM1` |
| 8 | `m_is_monitor == 1` | `TconFwPontusML3` |
| 8 | otherwise | `TconFwPontusML4` |
| 7 | none | `TconFwPontusM3` |
| 3 | `m_is_monitor == 1` | `TconFwOscarS4` |
| 3 | otherwise | `TconFwOscarS5` |
| other | stored panel type | `TconFwQd<panel-type>SE` |

Thus the literal factory executable candidates are:

```text
/factory_peq/tcon_data/QD/TconFwRoseM1.bin
/factory_peq/tcon_data/QD/TconFwRoseM2.bin
/factory_peq/tcon_data/QD/TconFwPontusM3.bin
/factory_peq/tcon_data/QD/TconFwPontusML3.bin
/factory_peq/tcon_data/QD/TconFwPontusML4.bin
/factory_peq/tcon_data/QD/TconFwOscarS4.bin
/factory_peq/tcon_data/QD/TconFwOscarS5.bin
/factory_peq/tcon_data/QD/TconFwQd<panel-type>SE.bin
```

Each basename is also tested under every literal removable directory above.
For example, the first and last locations for RoseM1 are
`/opt/media/USBDriveA/TCON/TconFwRoseM1.bin` and
`/opt/media/USBDriveD4/TCON/TconFwRoseM1.bin`.

For this owner unit, substituting the independently observed but unbound
`77A3OUSOF` yields three useful **hypotheses**, not validated active paths:

```text
/factory_peq/tcon_data/QD/77A3OUSOF.bin
/factory_peq/tcon_data/QD/77A3OUSOFOTP.bin
/factory_peq/tcon_data/QD/TconFwQd77A3OUSOFSE.bin
```

The retail model `QN77S95FAFXZC` is obtained by a different imported model
getter and stored at `m_strModel` (`.bss+0x1b8`), but these reconstructed path
builders use `m_strPanelType`, not `m_strModel`.  `F77ABU2D20` is controller
image information printed at startup; this binary does not use it in these
filename formulas.

## What the new live metadata closes

The retained authenticated response
`overnight/firmware-route-metadata-20261026a/client.stdout`, SHA-256
`a076292b45588add9e671728f973185f97788d7ab668b426db521f548ea82201`,
ran one read-only command on the same boot.  `/prd/lib/firmware/tcon` through
depth eight has exactly six rows: the root, `default_tcon`, two subdirectories,
and two regular `dummy.bin` files.  Both files are zero bytes with the empty
SHA-256 `e3b0c442...b855`.  This is a complete bounded negative for that tree,
not for `/factory_peq` or `/opt/media`.

The older usable inventory searched only `/lib/firmware`,
`/prd/lib/firmware`, `/usr/share`, and `/prd/usr/share`, only to depth four,
and filtered filenames.  A file named merely `77A3OUSOF.bin` under the exact
factory root would therefore have been missed for both root and name reasons.

The retained authenticated factory-root response
`overnight/firmware-resolver-roots-metadata-20261026a/client.stdout`, SHA-256
`17628f7c724548d20b9886d75d50ab3b2dbdcdca2ff7bf31dd678341ab727cf2`,
ran one bounded read-only command on the same boot.  It proves that
`/factory_peq/tcon_data/QD` is a directory with exactly the nine immediate
regular files listed above.  It also records all 20 literal removable-media
`TCON` directories as absent or not directories.  That closes the resolver's
currently mounted USB search roots; it does not say what a later inserted USB
device could contain.

The next authenticated metadata response,
`overnight/factory-qd-data-metadata-20261026a/client.stdout`, SHA-256
`730b84fb929779223e989b7d01e56619bf5531c00605b3ded83b54e8b8e2e5da`,
records every candidate as a non-symlink regular file owned by `0:0`, mode
`0644`, and exactly 5,242,880 bytes (`0x500000`).  Its deliberate 4 MiB first-
pass ceiling printed `HASH_SKIPPED_SIZE` for all nine; that was a bounded policy
result, not an I/O or integrity failure.  Every sampled 64-byte header is the
four bytes `5a 5a a5 a5` followed by 60 zero bytes.  On this little-endian
target those first four bytes decode as unsigned 32-bit magic `0xa5a55a5a`.

The purposeful follow-up
`overnight/factory-qd-data-hashes-20261026a/client.stdout`, SHA-256
`4d6a58d152c6cd4dfb31059ba09d336e33bf624299bf26054cea31ccee542897`,
read the 45 MiB total in 0.67 seconds and recorded nine distinct SHA-256 values:

| Filename | SHA-256 |
| --- | --- |
| `F_RSM1_BN9658111C_COMMON.bin` | `b5fd9a19ce23b59ed5e8c8951c36b5ab3f10f24f513377ead9885d0f6a2f043a` |
| `F_RSM1_BN9658112C_COMMON.bin` | `89af82818de1430b7bd86ea36c219dd4021745e180d30c53abb41c72ffd2c8bf` |
| `F_RSM1_BN9659920A_COMMON.bin` | `02cc716b603b0b084b97a9d9749ac1f82de868f65d4bb507e82ce63577e08a56` |
| `F_RSM1_BN9659920B_COMMON.bin` | `5af9dfa525a97f511ebf5c153b75c5657e1ce241992fa3f7850bf2473c762829` |
| `F_RSM1_BN9659932A_COMMON.bin` | `053e7c0b55100863e55e24b803d9d0466f949512d967856234a13637aae71f9d` |
| `F_RSM1_BN9659932B_COMMON.bin` | `735d93d2fb050b38dea7b3e47edc562b7043e714933f0d45540b5dbf5a7cad53` |
| `F_RSM1_BN9659934A_COMMON.bin` | `2e2ec0a105d1575a71a171ad9e5eb5a8563e8b4340c0b5d98d6702038127da89` |
| `F_RSM1_BN9659934B_COMMON.bin` | `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0` |
| `F_RSM1_BN9660751A_COMMON.bin` | `aee6240fce4172ffb9e72bcd669800fcbe05c50b8099241da460e4058611143f` |

Thus these are populated, distinct assets, not an empty/padded reference file.
The identical first 64 bytes do not establish identical internal layout.

## What is and is not recovered about the 5 MiB format

Only the following container facts are proven: exact length `0x500000`, the
common 32-bit little-endian magic `0xa5a55a5a`, zero bytes at offsets 4 through
63 in the sampled header, and a distinct whole-file hash for each candidate.
No length, version, checksum, section table, payload offset, or executable-code
field has been recovered from these header samples.

The exact CAD path does **not** call the SE command-9 helper in this build.
`m_tcon_upgrade_data_cad` passes its resolved pathname through
`m_tcon_flash_upgrade` to `m_tcon_update_send_cmd`.  That non-SE helper sends
operation `0x20` in a 48-byte envelope through imported `tztv_tcon_ext_cmd`.
The copied bridge binds that variable to `_tztv_tcon_ext_cmd`, whose cold path
resolves literal `tcon_ex_proc`.  No copied module exports that exact symbol;
`sdp_tcon_ex_proc` is a different name and cannot be substituted.

A separate SE helper, `m_tcon_update_send_cmd_se`, does send operation 9
through `tztv_frc_tcon_ext_cmd`.  The copied SDP chain for that route is now
recovered through a pathname loader and fixed `0x30000`-byte message packer,
but it is not the caller used by the exact CAD function above.  The full route
split, exact function hashes and loader limits are in
[`qd-cad-command9-consumer.md`](qd-cad-command9-consumer.md).  The selected
loader/packer bodies do not parse the sampled magic or a 5 MiB section table;
neither byte ordering of the magic occurs literally in the six pinned modules.
That bounded negative does not exclude a computed parser or a parser in the
missing `tcon_ex_proc` provider.

Accordingly, `0xa5a55a5a` is reported only as an observed container magic.  It
must not be treated as a recovered parser contract, and the 5 MiB size must not
be relabeled as the separately named MCU firmware payload.  The smallest
source gap is the exact operation-`0x20` `tcon_ex_proc` provider/binding used
by the CAD route (or a copied candidate plus a format-aware offline parser
tied to that implementation).

## Ranked minimal read-only next acquisition

These are proposed commands for a parent-operated, separately reviewed
metadata acquisition.  They are not executed here.  None invokes a QDF API,
opens `/dev/tztv_tcon`, or reads controller buses/flash.

1. **Recover the owner profile key from passive host evidence.**  Search
   ordinary configuration databases, package metadata, or retained logs for
   an exact mapping to one of the nine full BN codes.  Require the whole
   ten-character component; do not match only `77`, `S95F`, or a size class.
   This is now more valuable than copying all nine indistinguishable-by-header
   files.

2. **Recover passive QDF gates from retained logs, if still present.**  Search a
   bounded dmesg/log snapshot for the exact QDF formats
   `PanelType[...]`, `tcon:%d, is_monitor[%d] platform[%d], inch(%d)`, and
   `QDFTcon_Tcon_SetPanelInfo`'s `PanelType[...] / TconYear[...]` messages.
   Also search for the CAD filename-builder messages that print the composed
   name.  This consumes existing logs only.  It may bind panel type,
   `m_tcon_type`, monitor selection, or an already composed CAD name; absence
   from a finite ring proves nothing.  It cannot independently establish a
   currently live `m_year_tag`/`m_chip_type` when those messages are absent.

3. **Acquire the exact CAD downstream provider before interpreting fields.**
   Locate the module that exports literal `tcon_ex_proc`, or retain exact
   runtime symbol-binding evidence for that name, then copy the ordinary
   module with hashes.  Static analysis should first prove the operation
   `0x20` envelope consumer, a file read, any magic comparison, and bounded
   offsets before naming header fields.  Do not invoke operation `0x20`,
   command 9, or an updater.

4. **Copy only a source-bound candidate.**  Once an exact profile mapping has
   selected one BN code, copy that ordinary file with the already retained
   source hash and verify the destination hash.  If parser recovery requires a
   content comparison before selection, a separately reviewed bounded copy of
   all nine is 45 MiB, but it still must not be described as active firmware.

An implementation should fail closed on symlinks, non-regular candidates,
entry-cap overflow, path truncation, changing size/mtime during hashing, boot
change, or source hash mismatch.  Directory listing and ordinary file hashing
are the limit of this recommendation.

## Evidence limits

* A host file path is only a package/source candidate.  It is not proof of the
  bytes currently executing on the external controller.
* The resolver's zero return does not distinguish a found removable file from
  complete search failure.
* The QDF globals that select the exact F77 route have not been passively read
  in this phase.  RoseM naming is suggestive in this platform but does not
  substitute for the numeric `m_tcon_type`/`m_is_monitor` gates.
* `77A3OUSOF`, `QN77S95FAFXZC`, and `F77ABU2D20` are different identifiers from
  different evidence sources.  They must not be silently substituted for one
  another.
* The `/prd/lib/firmware/tcon` placeholders are not referenced by the exact
  resolver functions above and contain no payload.
* The nine factory assets are distinct and match the CAD flash-data filename
  grammar.  Their active owner selection and internal section layout remain
  unresolved.
* No safe controller-flash extraction interface is established here.  The
  upgrade functions are consumers with write-capable downstream behavior, not
  read-only acquisition tools.
