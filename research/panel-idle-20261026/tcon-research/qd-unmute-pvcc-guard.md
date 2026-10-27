# QD unmute's cached-PVCC guard and its lifecycle callers

Offline analysis of the copied modules; no live memory, GPIO, power, factory,
or TV command was used. Addresses below are section-relative ELF offsets,
not live kernel addresses. This is a static mechanism, not a diagnosed incident.

## Why an attempted unmute need not reach the bus

In `qdf_tcon.ko`, `m_send_cmd_with_lock.constprop.0` reads
`m_panel_dpms_pvcc_status` (`.bss+0x194`) at `.text+0xbbec`. If both this
cached word and the payload are zero, the branch at `0xbbf4` checks the full
command against `0xf30000000164` at `0xbe80`. A match logs a command skip and
returns zero, before taking `frc_tcon_mutex` or issuing I2C.

The literal is `m_panel_dpms_pvcc_status:%d qd command skip[%d], cmd =[0x%llX]`.
This applies to the frame-mode cleanup zero and the ordinary mute setter's
zero attempts. A mute-one cannot take this particular zero-payload branch; broader suspend, command-skip and TCON-state gates can still suppress either payload, as documented in the transport audit. The
[transport audit](qd-command-transport-failure.md) and
[concurrency audit](qd-mute-concurrency.md) preserve the exact branches.

This adds a successful **no-operation** possibility to the previously identified
failed final-unmute possibility. It does not show the cached flag was zero at
any owner-observed blackout, or that the temporary mute bracket ran then.

## Identified writes to the guard

`m_pvcc_status` at `.bss+0x40` is distinct from the guard at `+0x194`.

| Function | Exact operation | Limit |
| --- | --- | --- |
| `QDFTcon_InitVariable`, `.text+0xf98` | `w2=1`; `x13=bss+0x19c`; `stp w2,wzr,[x13,#-8]` at `0x10c8` initializes guard to1 and neighbour to0 | Defaults are not measured rail/panel state |
| `QDFTcon_t_Tcon_SetPvccFlag`, `.text+0x11b88` | stores input at `0x11ba8` to `+0x40` and at `0x11bac` to `+0x194` | Plain cache stores, no guard mutex shown in this function |

These are identified explicit scalar/pair writes in the inspected module.
This is not a proof excluding arbitrary alias/bulk writes, other modules,
firmware, or live memory modification.

The flag setter is not a harmless diagnostic: input1 also clears `+0x70`, and
if `m_pvcc_status==1` while `m_tcon_power_state` (`+4`) is zero, it logs
`Tcon Power On by PVCC on` and calls `m_set_power_control(1)` at `0x11c3c`.
The return from that power call is discarded before the setter returns zero.
No such setter was invoked by this investigation.

## API wiring and central lifecycle path

`tztv_frc_tcon_api.ko:TCON_SetPvccFlag` (`.text+0xc020`) looks up its registered
TCON table from `.bss+0x620`, takes slot112 at `0xc048`, and calls it at
`0xc054`. An absent table/slot returns zero. QDF module initialization puts
`QDFTcon_t_Tcon_SetPvccFlag` in that slot: `.init.text+0xe8/0xf0` materializes
the function, `+0x144` stores it at table+112.

In `tztv_frc_tcon.ko`, the resolver loads string `TCON_SetPvccFlag`
(`.rodata.str1.8+0x4d60`), calls `resolve_symbol` at `.text+0x5428`, and stores
the result at `.bss+0x2d0` (`tztv_tcon_set_pvcc_flag`) at `0x5438`.
`tztv_frc_tcon_set_power` (`.text+0x60d0`) calls that pointer with1 at
`0x6168` on its on route, or0 at `0x6274` on its off route. Other operations
in this function change actual clocks/power; it is not a diagnostic getter.
If the incoming state equals its `dpms_mode` cache (`.bss+0x284`), the entry
comparison at `0x60e4..0x60ec` takes a log/return-zero path and skips the work.

The normal DPMS lifecycle includes these calls:

- `_tztv_frc_tcon_dpms_on` is **`.text.unlikely+0x1114`**, not `.text+0x1114`.
  Its applicable normal route calls `tztv_frc_tcon_set_power(1)` at
  `.text.unlikely+0x12d4`; other guarded/resume routes exist. At `+0x1470` it
  stores `dpms_mode=1`. It does not prove every on invocation refreshes the guard.
- `_tztv_frc_tcon_dpms_off` is `.text+0x6328`. Its applicable normal route
  calls `tztv_frc_tcon_set_power(0)` at `0x6404`, then later writes
  `dpms_mode=0` at `0x6438`. Other branches exist here too.

ELF section identity matters: this relocatable file contains different code at
the same numeric offsets in `.text` and `.text.unlikely`. Symbol-section indices
were checked with `readelf -Ws/-SW` before attributing the DPMS-on call.
This establishes a lifecycle route capable of changing the guard; it does not
prove an exhaustive caller inventory or a menu-triggered power transition.

## What an observed test must distinguish

Keep public API acceptance, cached intent, actual I2C write/readback, and visible
light separate. A single public unmute-zero can read live `0x164` and attempt
a re-send, yet every zero send still passes this guard. If a complete capture
contains readback1 and no zero write, preserve the command-skip/PVCC and
lifecycle logs; absence of a write alone does not prove this specific branch.
If it contains a zero write, preserve raw transfer result and subsequent
readback rather than treating the Linux result as MCU or emission success.

The existing short post-onset passive samples contain no mute/frame command
and do not establish the flag's value at onset. Do not force the flag to1,
patch the guard, or call a power routine to compensate for this uncertainty.
An aligned initiating capture remains necessary before selecting a repair.

## Reproduction and provenance

`qd-unmute-pvcc-reproduce.py` prints bounded, hash-checked disassembly from:

- `qdf_tcon.ko`: `97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63`
- `tztv_frc_tcon_api.ko`: `3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6`
- `tztv_frc_tcon.ko`: `aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd`

It has no TV/network access. The separate writer map limits its inventory to
explicit immediate `F3:0x164` command construction; no external MCU firmware
or panel-internal protection algorithm was acquired.
