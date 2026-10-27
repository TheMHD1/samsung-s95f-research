# QD RT-status producer versus internal-TCON/RHEA identity boundary

Recorded 2026-10-27 UTC. This is a bounded, offline audit of already copied
ELFs and retained evidence. It made no TV, root, network, I2C, message-box,
firmware, display, power or controller call and modified no prior evidence.

## Result

The exact copied code does **not** bind the raw `F3:08` RT-status producer to
the `Int.Tcon`/RHEA firmware. It positively separates the two host routes:

1. The QDF error-status getter sends `f3 80 00 00 00 08` to Linux I2C adapter
   5, address `0x76`, receives four bytes and exposes that word as the QDF
   status. The accepted one-shot value was `0x10`.
2. The `[Int.Tcon]FW[...]DATA[...]` identity is obtained through an extension
   command, the SDP display/FRC bridge and `sdp_tcon.ko`. Its version fields
   come from `sdp_tcon`'s mapped `samsung,tcon_info` shared-memory resource.
   The RHEA MICOM text is exposed from another mapping of that same reserved
   resource, at base plus `0xa0000`.

The apparent unity of the retained `[TCON INFO]` line is not endpoint proof.
`qdf_tcon.ko` explicitly formats one line from values gathered by those two
different routes. The copied code therefore supports this bounded model:

```text
external QDF/module-controller route
  QDF FW/MD and RT status
  -> tztv raw/common I2C callbacks
  -> adapter 5, address 0x76

internal-TCON route
  Int.Tcon FW/DATA and RHEA startup log
  -> tztv FRC extension operation 9
  -> SDP display/FRC mediation
  -> sdp_tcon shared state / message-box subsystem
  -> samsung,tcon_info reserved-memory regions
```

This is source-backed **host-stack and transport separation**, not proof of
two different physical packages. One physical device could in principle
offer both interfaces, but no copied source, live binding, shared protocol or
endpoint identifier establishes that here. Conversely, a common word
"TCON" or one combined log line cannot establish such a bridge.

Accordingly, acquiring the 2 MiB image named by the RHEA/internal-TCON log as
the producer of QDF RT bit `0x10` is a wrong-layer **assumption**. It is not
proved to be the wrong physical silicon, and the image could still matter to
other internal-TCON behavior, but it is not the source-justified next artifact
for the `F3:08` producer. The closer unresolved artifact is the firmware or
protocol implementation behind the bus-5/address-`0x76` QDF endpoint. The
matching 5 MiB factory asset is closer to that identity boundary, but its
packaged bytes are not yet a live-firmware binding or fault-cause proof.

## Exact inputs

| Input | SHA-256 | Role |
| --- | --- | --- |
| `binaries/qdf_tcon.ko` | `97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63` | QDF getters, combined information formatter and transport calls |
| `binaries/tztv_frc_tcon.ko` | `aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd` | I2C callbacks and dynamic extension bridge |
| `binaries/tztv_frc_tcon_api.ko` | `3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6` | exported callback storage / public ioctl dispatch |
| `binaries/sdp_tcon.ko` | `9b7c1cb8e2bb8d11e5465a41fa402e71bd8d15a5dabd6b3d76de98a7a42549ee` | internal-TCON shared-memory and message-box provider |
| `qd-error-status-read-abi.md` | `3812ca30cd846e0aee4e85da0716577c781939972d1836eeca41624b2ef0e3d1` | independently reproduced status ABI and bounded getter |
| `qd-error-status-read-abi-reproduce.py` | `ce08ad96c1e7908274c1b82b8ebbe199783dace74d77fbcc19fb261a3e32270e` | hash-gated status-path checker |
| `tcon-micom-log-cache-producer.md` | `26d87ff90ef77b5f66f2a54db608171f4867e84943be4f5ccb26b92ffead84ef` | shared-log mapping/read analysis |
| `tcon-micom-log-cache-producer-reproduce.py` | `68b7b1142252b4f101334c0a95cc42410e907c8d42be39acf33c79a489c07bd7` | hash-gated MICOM-log checker |
| `frc-extension-and-sdp-register-path.md` | `eb20c468e9b313b1b7c5b308f984eca2c6f259c1fff57263f9d86f74f0c37a4a` | SDP bridge initialization and callback route |
| `qd-cad-command9-consumer.md` | `19b3f88815cff664b7452115d242a52b3626e46fbadc09422d399d5663986d6a` | operation-9 SDP mediation boundary |

Both existing offline reproducers completed normally during this review. Code
addresses below are ELF section-relative offsets unless stated otherwise; they
are not live kernel addresses.

## The combined information line contains two deliberately different sources

The exact strings reside in `qdf_tcon.ko`, not in the RHEA log reader:

```text
[QDF]FW[%s/F:%s]MD[%s/F:%s]
[Int.Tcon]FW[%02X%02X]DATA[%s]
[TCON INFO] PANEL[%s] %s ... [TCON INFO END]
```

`QDFTcon_Tcon_GetTCONFlashVersion` (`qdf_tcon:.text+0x47a0`, size 792)
builds the middle `%s` placed in the periodic information line.

### QDF side of the formatter

At `0x4838..0x4900`, it performs four `m_i2c_burst_read` calls:

| Call site | selector | length | formatted field |
| ---: | ---: | ---: | --- |
| `0x4848` | `-348` | 9 | first QDF FW field |
| `0x488c` | `-349` | 9 | `F:`-labelled QDF FW field |
| `0x48b4` | `-412` | 16 | first QDF MD field |
| `0x48ec` | `-413` | 16 | `F:`-labelled QDF MD field |

The values are printed at `0x4930..0x4938` using the exact QDF-format string.
The retained runtime values are:

```text
[QDF]FW[FA024C300/F:FA024C300]
MD[F77ABUAE20312300/F:F77ABUAE20312300]
```

These four reads use the QDF I2C machinery. They are not reads from the
`sdp_tcon` reserved-memory version table.

### Internal-TCON side of the formatter

When the internal-TCON gate is enabled, the same function calls
`m_tcon_update_send_cmd_se` with command 4 at `0x495c` and command 5 at
`0x4974`. The helper (`qdf_tcon:.text+0x3f98`) builds a 32-byte request and at
`0x40b0..0x40c8` invokes imported `tztv_frc_tcon_ext_cmd` with operation 9.

The exported pointer is installed by the copied `tztv_frc_tcon` probe as
`_tztv_frc_tcon_ext_cmd` (`.text+0x2d78`). Its build-specific chip value 14
selects exact symbol name `sdp_display_ex_proc`; the already audited static
chain reaches `sdp_tcon_ex_proc`. That provider takes operation 9 at
`sdp_tcon:.text+0x1384` and calls `tcon_update` at `0x13b8`.

`tcon_update` (`0xdbf8`) treats request commands 4 and 5 as version queries at
`0xdc04..0xdc14` and calls `tcon_get_version` at `0xdcd8` rather than the
firmware-update/image-load path. `tcon_get_version` (`0xca48`) then:

* for command 4, calls `sdp_tcon_get_curr_version.part.0` (`0xb848`), which
  copies ten bytes from `tcon_get_tcon_info_ptr(0xf40)`; and
* for command 5, reads `tcon_get_tcon_info(0xf4c)` and writes the two firmware
  version bytes into the reply.

The caller prints those results at `qdf_tcon:0x49a0..0x49b0` as
`[Int.Tcon]FW[%02X%02X]DATA[%s]`. The retained output is:

```text
[Int.Tcon]FW[F20D]DATA[F77ABU2D20]
```

Finally, `QDFTcon_MonitorTemperatureSensor` prints the encompassing
`[TCON INFO]` format at `qdf_tcon:0x10bdc..0x10be4`, passing separate QDF
module state and the already formatted version string. Juxtaposition is thus
an intentional aggregation, not evidence that every field came from one
firmware image.

## The internal identity and RHEA log are positively linked to `sdp_tcon`

`sdp_tcon_resource_init` (`sdp_tcon:.text+0x920`) reads the
`samsung,tcon_info` reserved-memory description and maps several regions from
one physical base. The relevant stores are:

| Code | mapping | instance field | consumer |
| ---: | --- | ---: | --- |
| `0xc90..0xcac` | base, `0x20000` bytes | `+816` (also `+912`) | `tcon_get_tcon_info[_ptr]`; internal FW/DATA identity |
| `0xcc8..0xcdc` | base + `0xa0000`, `0x20000` bytes | `+888` | `tcon_micom_log` debugfs reader |

`tcon_get_tcon_info` (`0x21b0`) loads instance `+816`; the command-4 and
command-5 version functions above index that mapping. The MICOM log reader
loads instance `+888`. Thus these are separate regions but the same exact
module and reserved-memory resource, not a match inferred only from names.

The retained 1,477-byte MICOM artifact
`overnight/micom-log-read-20261026b/micom-log.bin` (SHA256
`bd600476b7a081b58759128cff8bacd8f4fef8d8c45c33327cc575a1c65d7110`)
contains:

```text
RHEA_M_TCON_FW_20250103_1715
SPI Flash : 2048KB
TCON Image Info : F77ABU2D20
```

The exact `F77ABU2D20` equality with the independently reported
`[Int.Tcon]...DATA[...]` plus their shared `sdp_tcon` resource path is positive
evidence that the RHEA text describes the internal-TCON side of the combined
information. It does not make that text the QDF I2C endpoint's firmware.

The debugfs read path only copies the `+888` mapping; it is a mapped
shared-memory read. It does not call the QDF I2C getters, send `F3:08`, or
bridge into `qdf_tcon`.

## The accepted RT word remains on the external QDF I2C route

The exact public getter route is independently pinned from ARM32 AVE through
the TCON ioctl and API table to `QDFTcon_GetErrDetStatus`
(`qdf_tcon:.text+0xa000`). The QDF function constructs packed command
`0xf38000000008` at `0xa030..0xa040` and calls `m_read_cmd`
(`qdf_tcon:.text+0x9b88`). On the transport path:

* raw mode calls imported `tztv_i2c_write_raw` and
  `tztv_i2c_read_raw` with adapter 5, address `0x76`, six transmit bytes and
  four receive bytes at `0x9c48..0x9c80`; or
* common mode calls imported `tztv_i2c_read_common` with the same endpoint and
  lengths at `0x9cf0..0x9d0c`.

Only a zero lower result reverses the four bytes and writes the caller output.
There is no `sdp_tcon_ex_proc`, `tcon_get_tcon_info`, reserved-memory or
message-box call in this bounded getter/read-helper route.

The accepted result
`overnight/managed-tcon-status-read/result-20261026c.json` (SHA256
`5ccac8a789fd83b3b276b39e6bf33201087c8e4354d580f7bb316075ed04bea6`)
records ioctl return zero and output word `0x10`. The matching retained dmesg
response (SHA256
`d454a04995c5298f31693260f1243e7dcb4f5cf8335312e798b3e99e27b7e9f9`)
contains the same helper PID/time and `ERR DET Status:0x10`. This establishes
the live route's kernel output and log, subject to the already documented
raw/debug distinction. It does not identify the physical chip or firmware
which generated the four response bytes.

The module symbol boundaries agree with the call graph:

* `qdf_tcon.ko` imports the `tztv_i2c_*` callbacks and
  `tztv_frc_tcon_ext_cmd`; it does not directly import an `sdp_tcon_*`
  symbol.
* `tztv_frc_tcon.ko` supplies the local I2C implementations through Linux
  `i2c_get_adapter`/`i2c_transfer`, and separately implements the dynamic
  extension bridge.
* `sdp_tcon.ko` exports `sdp_tcon_ex_proc`, uses shared mappings/message boxes
  and imports no Linux I2C transfer function in this copied build.

These import facts are corroboration, not a global proof that the subsystems
can never affect one another. The positive route-specific disassembly above
is the basis for the identity boundary.

## Diagnostic and acquisition consequence

The following claims are supported:

* QDF FW/MD and RT status share the QDF module's external-I2C side.
* Internal FW/DATA and the RHEA log share the `sdp_tcon` reserved-resource
  side; their exact `F77ABU2D20` data identifier agrees.
* The QDF periodic log intentionally combines both identities.
* No source-backed bridge from the `F3:08` response producer to the
  RHEA/2-MiB firmware was recovered in the bounded route.

The following claims are **not** supported:

* that bus 5/address `0x76` and the SDP internal TCON are definitely separate
  physical chips;
* that RHEA firmware cannot indirectly influence QDF/panel behavior;
* that the QDF status is necessarily fresh electrical truth rather than a
  controller-side cached/debug/policy value;
* that the 5 MiB matching asset is currently executing; or
* that any firmware, profile, RT bit, owner-visible blackout or photographed
  panel damage caused another one.

For RT-producer attribution, the missing discriminator is a binding from the
bus-5/address-`0x76` endpoint to an exact executable/protocol implementation.
Continuing to seek the RHEA 2 MiB image can answer internal-TCON questions,
but it must not be presented as acquisition of the RT producer absent that
bridge. No firmware apply, controller readback, updater, I2C probe or hardware
control follows from this report.
