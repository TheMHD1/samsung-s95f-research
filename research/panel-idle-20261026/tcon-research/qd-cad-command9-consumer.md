# QD CAD assets and extension-command 9: exact consumer boundary

## Result

The copied modules close extension-command **9** farther than the earlier
resolver report, but they also expose an important non-equivalence: the QDF
CAD upgrade function that constructs the `F_RSM1_BN..._COMMON.bin` pathname
does **not** call the command-9 helper in this build.  It calls QDF's non-SE
update helper, which sends operation `0x20` through a different dynamically
resolved name, `tcon_ex_proc`.  No copied module exports that exact name, so
the live consumer of the nine factory CAD assets remains missing.

The separately recovered command-9 route is complete through the copied SDP
modules.  It is a host-side pathname/file loader followed by a fixed-size
message packer: it opens the supplied pathname, asks for the whole file
length, reads that many bytes into a mapped update-image buffer, and copies
the first `0x30000` bytes into a message payload.  The examined bodies do not
parse the sampled `0xa5a55a5a` magic or a 5 MiB section table.  Interpretation
of that magic, if this route were given such a file, lies beyond the recovered
host packer.  The downstream message endpoint is not proven to be the QD MCU,
and the CAD route is not proven to use this packer.

No already-retained passive artifact selects one of the nine ten-character
`BN...` keys.  The key is still a runtime output of the QDF controller-read
name builder, not something derivable from the retail model, panel diagonal,
or `F77ABU2D20`.  This report performs no device access, updater call,
controller command, or network operation.

## Exact sources and reproducibility

All addresses are ELF `.text` offsets, not live kernel addresses.

| Copied module | SHA-256 |
| --- | --- |
| `binaries/qdf_tcon.ko` | `97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63` |
| `binaries/tztv_frc_tcon.ko` | `aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd` |
| `binaries/tztv_frc_tcon_api.ko` | `3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6` |
| `binaries/sdp_frc.ko` | `05dea2eaad34a23def837fb86d2f7a4e99ef630066ad6fed18d0cf55ba37063d` |
| `binaries/sdp_tcon.ko` | `9b7c1cb8e2bb8d11e5465a41fa402e71bd8d15a5dabd6b3d76de98a7a42549ee` |
| `binaries/rosem_frc.ko` | `c646b45d8ab5028defca91b5f8188bf905b8d29f8927fae292be591c94cdbd34` |

The offline checker
[`qd-cad-command9-consumer-reproduce.py`](qd-cad-command9-consumer-reproduce.py)
pins all six whole files, selected function bodies and instruction/relocation
landmarks.  It also performs a bounded literal census for both byte orders of
the sampled magic.  It does not execute ELF code or prove every control-flow
path.

The filename grammar and factory-file observations were inherited from the
exact prior report now preserved as
`qd-firmware-resolver-exact-paths-prior-command9-inference-631e2e9e.md`,
SHA-256
`631e2e9ef0c29d1e2aeb67b42b94a8ff4b890c4bf3d66f6d677849fde25cd0a9`.
The current primary
[`qd-firmware-resolver-exact-paths.md`](qd-firmware-resolver-exact-paths.md)
has been corrected to link this route analysis rather than retaining the old
command-9/CAD inference.
Its three material retained responses are independently pinned as follows:
factory-directory inventory `17628f7c724548d20b9886d75d50ab3b2dbdcdca2ff7bf31dd678341ab727cf2`,
size/header metadata `730b84fb929779223e989b7d01e56619bf5531c00605b3ded83b54e8b8e2e5da`,
and nine full-file hashes
`4d6a58d152c6cd4dfb31059ba09d336e33bf624299bf26054cea31ccee542897`.

```sh
python3 tcon-research/qd-cad-command9-consumer-reproduce.py
```

Selected exact function bounds and byte hashes:

| Module | Offset | Size | Function | Function-byte SHA-256 |
| --- | ---: | ---: | --- | --- |
| QDF | `0x3f98` | 492 | `m_tcon_update_send_cmd_se` | `e8675eaf203e7ebafa4f7f2104447e260a8d9788d39a1f71150d0dafbdc88028` |
| QDF | `0x9630` | 980 | `m_tcon_update_send_cmd` | `52d8be1c3a1963c4cdb7b182657600fb2c7809b360176def0b344e7d97c1e2d4` |
| QDF | `0x12218` | 2688 | `m_tcon_flash_upgrade` | `6057aae74b1f8e4a4a3c9c248b4feeb7feaa3f587bd226624a34f8cc58973cd1` |
| QDF | `0x13298` | 720 | `m_tcon_upgrade_data_cad` | `4618554a949d9cb72471e1eaf1e7ff16b2e906842ceb25a986e8343d4d1e1d47` |
| bridge | `0x2d78` | 352 | `_tztv_frc_tcon_ext_cmd` | `d789b6d3e363fc4490bbefea796cde2dfae584daee61788bf36372a8237cb5fb` |
| bridge | `0x3090` | 216 | `_tztv_tcon_ext_cmd` | `3fbed38cc476f58f8ba6a2d721d1e031d53a08872a42d1c0928fd409e76f1ad7` |
| SDP FRC | `0x2258` | 4656 | `sdp_frc_ex_proc` | `834fc29b621b5ad222de7181942859309fc3660020b7f63876c242eb9560f92e` |
| SDP FRC | `0x1c060` | 76 | `tcon_mediation_proc` | `334ff21409898ed56a9a2db7a794046d5b9fc165ae818a12321daeb90eeddd52` |
| SDP FRC | `0x1c0e8` | 104 | `tcon_mediation_init` | `af7431c66247542b10aa07d6f76bba44783c9337dcc0a145ae050284bdeab389` |
| SDP TCON | `0x1678` | 752 | `sdp_tcon_ex_proc` | `8b1a390d3d831437ee695ad6c86ae87f537530881c19e0d67e4abb3a775f46be` |
| SDP TCON | `0x1160` | 1300 | `sdp_frc_ex_proc_for_tcon` | `4b94bcaab937207f54ab0e47d4e273d7ba5243e1a2c4aeb47ca7a0ccd2b82c01` |
| SDP TCON | `0xcd80` | 308 | `sdp_tcon_load_update_image` | `adb3d71e163ce8725ec5cfb61ff15a2336994d6d8377cb80c888f73702253168` |
| SDP TCON | `0xb350` | 540 | `msgbox_pack_execute_update` | `b720dbf4f8754ed7c01e521b47cede3e70d6d90d31d244ce6b827fbd7a468efd` |
| SDP TCON | `0xdbf8` | 612 | `tcon_update` | `38236e4b9af0cc8db56db6b3e95dae737dcf565c9fb3c442a1e87fbb6a4f3cd4` |
| SDP TCON | `0x79e0` | 288 | `__sdp_tcon_send_msgbox` | `bec410032d2440598bb8026d117c9828f2cde7eb291df0d9e537f27d72dc4870` |

## The two update routes are distinct

### Extension-command 9 route

`m_tcon_update_send_cmd_se` constructs a 32-byte request whose relevant
fields are a command word at `+0`, pathname pointer at `+8`, pathname length
at `+16`, and status byte at `+30`.  At `0x40b0..0x40c8` it loads imported
`tztv_frc_tcon_ext_cmd`, sets `(operation,length)` to `(9,32)`, and calls it.
The function does not prove that any particular public QDF entry point took
this branch at runtime.

The bridge variable is initialized by the copied `tztv_frc_tcon` probe to
`_tztv_frc_tcon_ext_cmd`.  The bridge's ordinary compiled chip value is 14,
so its cold resolver selects literal `sdp_display_ex_proc`; the exact
selection proof and its initialization caveats are documented independently
in `frc-extension-and-sdp-register-path.md`.

The downstream static chain is:

```text
m_tcon_update_send_cmd_se: operation 9, 32-byte request
  -> _tztv_frc_tcon_ext_cmd
  -> sdp_display_ex_proc
  -> display coordinator/device tables (conditional initialized state)
  -> sdp_frc_ex_proc
  -> tcon_mediation_proc
  -> dynamically resolved sdp_tcon_ex_proc
  -> sdp_frc_ex_proc_for_tcon
  -> tcon_update
  -> sdp_tcon_load_update_image
  -> msgbox_pack_execute_update
  -> __sdp_tcon_send_msgbox
```

At SDP FRC `0x268c..0x26a0`, the operation mask is assembled as
`0x80360200`; bit 9 is set.  The accepted branch calls
`tcon_mediation_proc` at `0x270c`.  `tcon_mediation_init` resolves literal
`sdp_tcon_ex_proc` using `__symbol_get` and stores it at BSS `+0x6c1c8`.
If that pointer is null, `tcon_mediation_proc` logs and returns zero without
forwarding, so a zero result alone is not downstream-execution proof.

The copied `sdp_tcon.ko` exports the named callback.  Its operation-9 branch
at `0x1258/0x1384` validates the request command word against its finite
update-command set and calls `tcon_update` at `0x13b8`.  This closes the
named static binding but not live initialization, policy gates, or incident
execution.

### Actual QDF CAD-path route in this build

`m_tcon_upgrade_data_cad` is the function that calls the recovered CAD name
builder and path resolver.  At `0x13394` it obtains an update-command word;
at `0x1339c..0x133a4` it passes that word and the resolved pathname directly
to `m_tcon_flash_upgrade`.

That function later calls `m_tcon_update_send_cmd`, not the `_se` helper.
The non-SE helper calls a different imported callback variable,
`tztv_tcon_ext_cmd`, with operation `0x20` and a 48-byte envelope.  The bridge
initializes that variable to `_tztv_tcon_ext_cmd`, which resolves literal
`tcon_ex_proc`.  The copied module set contains the string but no exported
symbol with that exact name.  `sdp_tcon_ex_proc` is a different name and must
not be silently substituted.

Therefore the recovered command-9 consumer is **not proof of how the nine CAD
files are consumed**.  The smallest missing edge is the module that exports
`tcon_ex_proc` on this build, or retained runtime symbol-binding evidence for
that exact name.  Without it, calling the CAD assets “command-9 inputs” or
assigning them the SDP packer's `0x30000` behavior would be an unsupported
merge of two routes.

## What the command-9 host loader does and does not parse

For update commands 14 through 17, `sdp_tcon_load_update_image` uses an
in-memory pointer at request `+32` and length at `+40`; it accepts only a
nonnull pointer and lengths 1 through `0x30000`, then copies into the mapped
update image at instance `+880`.  That is not the pathname branch.

For the other accepted update commands, the pathname branch:

1. takes the pointer at request `+8` and the u16 count at `+16` and calls
   `strncpy` into a 150-byte local buffer (the examined body has no explicit
   `count <= 150` check);
2. zeros `0x30000` bytes at the mapped update-image pointer;
3. opens the pathname with `fio_fopen(path,0)`;
4. seeks to end, retains the returned length in the low 32 bits, seeks back,
   and calls `fio_fread` using that length;
5. closes the file and returns zero without checking `fio_fread`'s result.

The examined pathname branch has no explicit `file_length <= 0x30000` check.
This is an observed static safety limitation, not a recommendation to invoke
the path with any file.

`msgbox_pack_execute_update` then zeros a `0x30014`-byte message buffer and
copies exactly `0x30000` bytes from the mapped update image to message offset
`+0x10`.  It chooses small header fields from the update-command word and
returns the packed size.  `tcon_update` supplies this packer to
`__sdp_tcon_send_msgbox`, which calls another driver-local send routine and an
optional unpack callback.  The acquired code does not establish that this
message endpoint is the QD controller MCU.

No compare, branch, or table walk over `0xa5a55a5a` occurs in these selected
loader/packer bodies.  Neither byte sequence `5a 5a a5 a5` nor its reverse
occurs literally anywhere in the six pinned module files.  That bounded
negative cannot exclude a computed magic or a parser in missing code, but it
does establish that the recovered host command-9 path is a file loader and
fixed-size packer rather than the sought 5 MiB format decoder.

The actual factory candidates are `0x500000` bytes.  If one were supplied to
this pathname branch, the body would request a full-length read while the
packer would copy only the first `0x30000`; this mismatch is further reason
not to infer that these CAD assets use this route.  It does not prove the
remaining bytes are unused by the real CAD consumer.

## Active ten-character key remains unresolved

The exact CAD name builder in QDF performs
`m_i2c_burst_read(0,-0x3000,0x20,buffer)`, requires an exactly ten-character
C string, and places it between the family and suffix.  None of the acquired
host modules provides a retail-model-to-BN table.

A bounded local search found the nine `BN...` names only in the three retained
factory-directory metadata/hash responses and the already-written resolver
analysis.  The rescued 64 MiB vlog
`overnight/owner-power-on-20261026a-rescue/retained/vlog-after.txt`, SHA-256
`eac02d7bf3a4fb216295edba8be99466d7b80c7a43f7535841f882b052c1c3d3`,
contains no exact `F_RSM1_` or any of the nine full BN tokens.  That finite log
absence is not evidence that the controller never reported the key; it only
means the current retained data does not avoid the missing runtime selection.

The least invasive next evidence is an already-existing boot/update log line
that prints QDF's composed CAD `file_name`, or a read-only binding/copy of the
missing `tcon_ex_proc` provider.  This report does not propose another I2C
read, a controller-flash protocol, or an update attempt.

## Diagnostic limits

- Static callback initialization is conditional; no live pointer table or
  command-9 invocation was captured.
- Zero return can mean the mediation callback was null and nothing was
  forwarded.
- The command-9 SDP path is separate from the exact CAD caller in this QDF
  build.
- The 5 MiB asset layout, section table, checksum scheme and meaning of the
  sampled magic remain unrecovered.
- The `0xa5a55a5a` value identifies a file header only; it does not establish
  MCU executable code, OTP contents, active selection, or safe applicability.
- No finding here explains, clears, or repairs the owner's live `0x10`
  protection status or black picture.
