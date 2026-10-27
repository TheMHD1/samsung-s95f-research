# Device-tree GPIOs: exact driver chain and safe observation boundary

Scope: static analysis of the supplied device-tree mapping and matching
`tztv_frc_tcon.ko` / `qdf_tcon.ko`. No GPIO was exported, read through a
private entry point, or written.

## Resolved mapping is not a connector pinout

The device tree resolves Linux GPIO identities only. It does not disclose a
One Connect cable pin, panel flex pin, wire colour, voltage, or a safe manual
test point. GPIO 272 seen in an earlier trace is `gpio34.0`; it is not one of
the TCON signals below and must be removed from any TCON causal claim.

| DT property | Linux GPIO | DT active-low flag | Driver role established from code |
|---|---:|---:|---|
| `sw-pvcc` | 144 | yes | PVCC output candidate |
| `ffc_cable_check` | 148 | no | FFC check property; no QDF consumer established here |
| `tcon_on` | 429 | no | gated output candidate |
| `tcon-i2c-en` | 259 | no | I²C-enable output |
| `err_det` | 125 | no | raw fault input |
| `vdd_det` | 126 | no | raw fault input |
| `sync_done` | 127 | no | raw status input |
| `s_done` | 128 | no | off-sensing status input |
| `err_det_w` | 129 | no | present in DT; no matching consumer established in this pass |
| `tcon_pmic_fault` | 121 | no | raw PMIC-fault input |
| `el_vdd` | 431 | no | gated output candidate |
| `tcon_dpc` | 435 | no | present in DT; no matching consumer established in this pass |
| `ac_det` | 425 | no | gated output candidate |
| `qsmen` | 182 | no | gated output candidate |

The sole `active-low` DT specifier is PVCC. This is not a tested statement of
which electrical level powers the panel: the matching setters use
`gpiod_*_raw`, and their calls to `of_get_named_gpio_flags` deliberately pass
a null flags output. Therefore they do not automatically invert according to
the DT flag; their callers choose the raw output level.

## Fault/status inputs: normal code is not a passive external probe

The exact functions below all use the same sequence on first/current use:

1. resolve/cache the DT GPIO by property name;
2. `gpio_request` it;
3. call `gpiod_direction_input`;
4. call `gpiod_get_raw_value_cansleep`;
5. `gpio_free` it.

That sequence is present in:

* `_tztv_frc_tcon_read_pmic_status` (`0x1730`) for `tcon_pmic_fault` 121;
* `_tztv_frc_tcon_read_sdone_status` (`0x19b0`) for `s_done` 128;
* `_tztv_frc_tcon_read_err_det_status` (`0x1af0`) for `err_det` 125;
* `_tztv_frc_tcon_read_vdd_det_status` (`0x1c30`) for `vdd_det` 126;
* `_tztv_frc_tcon_read_sync_done_status` (`0x1d70`) for `sync_done` 127.

All five mapped input properties have zero flags, so the raw samples are not
polarity-inverted by the DT. Their physical interpretation remains
panel-specific and cannot be inferred merely from a high or low sample.

`QDFTcon_GetErrDetFault` (`qdf_tcon.ko:0x5608`) conditionally calls the
registered `read_err_det_status` callback. That confirms a real
DT → TCON-driver → QDF fault path. It does **not** make a new external call
safe: taking the private ioctl/export path would execute the direction-input
step above and can contend with the normal driver. Existing kernel/AVE fault
logs or an already-reviewed stock read-only status surface are the only
acceptable ways to observe these inputs.

## Outputs and gates

Every output helper requests the line, drives it with
`gpiod_direction_output_raw` and `gpiod_set_raw_value_cansleep`, then frees
it. These are control operations, never diagnostics.

* `_tztv_gpio_set_tcon_i2c_en` (`0xa50`) directly controls `tcon-i2c-en` 259
  with the supplied raw value; there is no safe read counterpart here.
* `_tztv_frc_tcon_set_tcon_on` (`0xb78`) only takes its GPIO path when an
  internal platform/model selector equals `7` or `14`. A DT property alone
  does not prove that this S95F activates that path.
* `_tztv_frc_tcon_set_qsmen` has the same `7`/`14` selector gate.
* `_tztv_frc_tcon_set_elvdd` (`0x7ec8`) only follows the direct GPIO branch
  for selector `7`, `8`, or `14`; other selector values use a different STBC
  control route or reject the call.
* `_tztv_frc_tcon_set_acdet` (`0x80b0`) has equivalent selector gates, with
  alternate STBC routes for selectors `3` and `11`.
* `_tztv_gpio_set_pvcc_en` (`0x5e20`) is part of a power sequence with
  nreset handling and model flags. It is not an isolated “turn panel on” bit.

The supplied evidence identifies the board as QD/RheaM, but does not include
the in-memory selector value used by these gates. Therefore none of the
gated lines may be asserted to be actively controlling this unit merely from
their DT presence.

## Consequence for the black-screen investigation

The resolved signals strengthen, rather than weaken, the safety boundary:
they show that TCON on, I²C enable, PVCC, ELVDD, AC detect, and QSMEN are real
low-level controls with platform-specific sequencing. They must not be
toggled to attempt recovery. The recent physical-black captures already show
no host-visible PMIC/HSM/ERRDET transition; the next useful observation is a
normal, already-exposed read-only driver log/status comparison between a
visible and black state, not direct GPIO sampling or forcing.
