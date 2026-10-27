# QD TCON firmware acquisition map

This is an offline reconstruction from copied, hash-identified host binaries
and previously saved read-only inventory/log artifacts. It does not read a
panel flash chip, invoke an upgrade API, write eMMC, alter a firmware file, or
claim that a kernel module contains the panel controller firmware.

## Result

The visible boot identifier `F77ABU2D20` is **not embedded** in the copied
`qdf_tcon.ko`, `tztv_frc_tcon.ko`, `tztv_frc_tcon_api.ko`, or `sdp_tcon.ko`.
It appears in `overnight/tcon-firmware-log-prefix.txt`, whose startup text
also says `SPI Flash : 2048KB`, `TCON Image Info : F77ABU2D20`, and `Main
Loop`. That is evidence of a controller-side image/version announced during
startup, not a recovered firmware payload.

The copied QDF module contains an update implementation, but it is a **file
consumer and transport writer**, not an embedded 2 MiB image:

* `m_get_tcon_fw_file_path.isra.0` at `.text+0x93c0` builds candidate paths,
  opens each through `ft_file_open` at `0x9538`, then closes a successful
  probe. It does not contain or return firmware bytes.
* `QDFTcon_UpgradeFlashDataOtp` at `0x12e68` calls that path resolver at
  `0x12ed8`, derives an update command, then calls `m_tcon_flash_upgrade` at
  `0x12f38`.
* `m_tcon_flash_upgrade` contains I2C burst write/read calls and an explicit
  power-off/on sequence on an error branch (`0x12b1c..0x12b30`). It is an
  update path and is not a safe diagnostic/readback interface.
* Several public-looking `QDFTcon_UpgradeFlashFirmware*` exports at
  `0x408`, `0x450`, and `0x498` are stubs on this build: each logs and returns
  `-1`. Their names alone do not prove a usable updater.

The QDF module has only about `0x16de0` bytes of `.text`, `0x3539` bytes of
`.rodata`, and `0xcaef` bytes of string data. It has no separate allocatable
firmware/blob section, and its full on-disk module size is below the startup
log's stated 2 MiB controller flash capacity. This strongly rules out a
complete raw F77 image being packaged in this copied QDF module. It does not
rule out a different filesystem package, partition, encrypted container, or
controller flash.

## Official package: bounded, offline container evidence

The exact Canadian-model support page lists the official archive
`T-RSMFAKUC-0090_TB-RSWF4AKUC-0090.zip` as version `0090-1301.0`, dated
2026-09-08.  Only archive metadata, both small `info.txt` entries, and a
65,494-byte *decompressed prefix* of the main `upgrade.msd` were captured.
The 2,439,527,748-byte archive was **not** fully downloaded, and none of its
contents were placed on or applied to the TV.

The saved central directory validates that the main package member is:

| ZIP member | ZIP method | Compressed bytes | Uncompressed bytes | What was validated |
| --- | ---: | ---: | ---: | --- |
| `T-RSMFAKUC-0090/image/info.txt` | deflate | 310 | 511 | Whole member CRC-32 |
| `T-RSMFAKUC-0090/image/upgrade.msd` | deflate | 1,493,772,708 | 1,493,538,434 | Only a 65,494-byte decompressed prefix |

The CRC-checked `info.txt` identifies the main package as model
`T-RSMFAKUC-0090`, version `1301.0`, build date `2026-07-14`, and states
`cipher suite: aes-256-cbc-sha512`.  Its build family/date match the observed
running-build date, but that is **not proof** that the archive's partitions or
bits match the TV's installed state.  The same file lists a partition-label
string (`123456789101213141518192223`); it does not define its mapping to the
bytes in the partial MSD prefix.

The prefix artifact has SHA-256
`01821f40cf70841649c856090e23b35be6173659fb54be11f3b661a3e37bf92d` and
contains these directly reproducible observations:

* bytes `0x0000..0x0005` are the literal ASCII magic `MSDU11`;
* the literal `T-RSMFAKUC-0090` occurs at offset `0x00db` (219);
* the literal `Salted__` occurs at offset `0x00f2` (242);
* it contains no literal `F77ABU2D20`, `TconFwQd`, `qdf`, or `tcon` marker.

Those observations establish only that the sampled `upgrade.msd` begins with
an `MSDU11`-marked opaque header/prefix and soon contains encrypted- or
container-looking data.  They do **not** validate a partition directory, an
MSDU field layout, any partition boundary, a resource filename, an encryption
boundary, or a TCON/QDF firmware member.  `Salted__` alone does not identify a password, key derivation parameters or a validated decryption format.  The whole `upgrade.msd` CRC and any package signature are unverified
because only the prefix was decompressed.

This is therefore a useful acquisition lead, not a recovered external-MCU
payload.  Further offline parsing requires a documented container layout or independently validated decryption method; the acquired prefix does not provide either. Ordinary package-byte acquisition can continue within the existing investigation authorization. The updater and panel-controller operations are not extraction interfaces.

## Exact external-file evidence

The module's update/debug strings name force/automation inputs including:

```text
usb/TCON/TconFwQd%s.bin
usb/TCON/%s.bin
usb/TCON/tcondata.bin
```

`TconFwQd` is an in-module filename component. The code constructs candidate
paths from a table and calls the file opener; it does not establish which
candidate is active on this particular TV, nor that USB inputs correspond to
the installed controller image.

The earlier successful read-only filesystem inventory
`overnight/firmware-inventory-2.json` found only these matching local files:

```text
/prd/lib/firmware/tcon/default_tcon/tcon_flash_data/dummy.bin
/prd/lib/firmware/tcon/default_tcon/tcon_flash_fw/dummy.bin
```

It found no filename containing `tcon`, `qdf`, `rheam`, `fwfa`, or `f77abu`
other than those firmware placeholders and unrelated ordinary files in the
searched roots. The previous attempted inventory in `firmware-inventory.json`
failed before searching because shell escaping made its `find` expression
invalid; it must not be interpreted as a negative search. The second inventory
is the usable result, but it was bounded to four roots/depth four and a
filename filter, so it cannot prove the TV has no matching firmware elsewhere.

## Read-only acquisition options, ranked by evidence

1. Re-run a bounded filename inventory of existing filesystem firmware roots,
   then record path, byte count and SHA-256 before copying any candidate. This
   can recover an ordinary package if one exists, but no candidate above is a
   recovered F77 payload.
2. Inspect the update resolver's generated candidate path in an already
   observed update log, if the product ever emits one naturally. Do not invoke
   the resolver or debug menu merely to make it log a path.
3. Obtain a signed Samsung firmware bundle through an official model-specific
   update package and inspect it offline. Its relationship to the running
   panel/TCON image must be verified from headers/signatures; a main-TV update
   package must not be assumed to contain this controller image.

There is no demonstrated read-only stock API in the copied modules to dump the
TCON's 2 MiB SPI flash. The identified `F3` commands and update routines are
write/control protocols; synthesizing them as a “read” could alter state or
enter update mode. No such operation was tried.

## Provenance

| Input | SHA-256 | Relevant role |
| --- | --- | --- |
| `binaries/qdf_tcon.ko` | `97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63` | File resolver and update transport |
| `binaries/tztv_frc_tcon.ko` | `aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd` | Central TCON lifecycle module; no F77 string found |
| `binaries/tztv_frc_tcon_api.ko` | `3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6` | TCON API bridge; no F77 string found |
| `binaries/sdp_tcon.ko` | `9b7c1cb8e2bb8d11e5465a41fa402e71bd8d15a5dabd6b3d76de98a7a42549ee` | TCON-facing module; no F77 string found |
| `overnight/samsung-official-firmware-archive-metadata.json` | `5cd6f20cb1a05fc0c21703baa5725698eeea40b70e77594e7efd5370154e4087` | Bounded ZIP-directory and `info.txt` evidence for the official package |
| `overnight/samsung-official-T-RSMFAKUC-0090-msd-prefix.bin` | `01821f40cf70841649c856090e23b35be6173659fb54be11f3b661a3e37bf92d` | 65,494-byte decompressed `upgrade.msd` prefix; not a whole validated member |

`qd-firmware-acquisition-reproduce.py` verifies the four module hashes,
prints only the bounded resolver/update windows and searches the copied module
bytes for the two startup identifiers. It also hash-checks the saved official
MSD prefix and prints the four literal-offset observations above without
parsing/decrypting it. It has no TV or network access.

## Boundary for the blackout investigation

The startup identifier confirms a distinct controller firmware layer remains
opaque. It does not explain the menu-dependent blackouts, prove corruption,
or justify updating/reflashing the controller. The useful next diagnostic
remains a time-aligned passive capture of a visible-to-black transition,
correlated with the documented QD gate/lifecycle logs.
