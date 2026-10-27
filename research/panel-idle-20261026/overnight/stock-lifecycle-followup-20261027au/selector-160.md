# Selector `F3:0x160` in the stock MODE2 tail

Recorded 2026-10-27 UTC. This is a bounded offline interpretation of one
already retained ordinary transaction. It made no TV, root, network, I2C,
USB, controller, firmware, update, maintenance, or target request.

## Result

Selector `0x160` is the ordinary **TCON frame-mode scalar** in the retained
QDF/controller pair. It is not source-backed as firmware-update progress,
panel-maintenance state, parser readiness, generic controller readiness, or a
fault-clear result.

The historical MODE2 normal-on tail retained one complete Linux I2C transfer
at uptime `94422.680802..94422.681151`:

```text
bus 5, address 0x76
write  f3 00 00 00 01 60
read   00 00 00 00
ret    2
```

The returned word zero is source-consistent with frame-mode value `0`. It
does not mean “maintenance idle,” “update complete,” “ready,” “healthy,” or
“panel lit.” The frozen trace decoder called this shape semantically
unclassified because its older whitelist did not label the generic F300 read;
that does not erase the exact two-message bytes or Linux `ret=2` accounting.

## Ordinary QDF caller and use

The copied `qdf_tcon.ko`, SHA-256
`97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63`,
contains local symbol `m_tcon_recovery_frame_mode` at `.text+0x107e8` and
object symbol `m_tcon_frame_mode` at BSS `+0x13c`.

The helper's exact ordinary sequence is:

| module `.text` offset | action |
| ---: | --- |
| `0x107ec..0x107f0` | construct command key `0xf30000000160` |
| `0x1080c` | initialize output word to zero |
| `0x10810` | call `m_read_cmd.constprop.0` |
| `0x10844` | branch on read return |
| `0x10850..0x10858` | compare returned word with BSS `m_tcon_frame_mode` |
| `0x1088c..0x10890` | on mismatch, call `m_tcon_set_frame_mode(cached mode)` |

The module's retained diagnostic strings explicitly say `read frame mode`,
`frame mode register`, `current frame mode`, `Same frame mode`, and `Set Frame
mode for recovery`. These names agree with the dataflow rather than supplying
an interpretation from the numeric selector alone.

The stock power-on path calls this helper at `.text+0x11930`, after
`m_check_tcon_status(2)` and before cached-register replay at `0x11934`.
Therefore the MODE2 `0x160` transfer is the frame-mode comparison step in the
normal on-tail. A readable value equal to the QDF cache avoids reprogramming;
a read failure or mismatch can delegate to the frame-mode setter. The parent
power routine discards the frame-recovery return, so completion of MODE2 is
not proof that any requested correction succeeded.

The same helper also has ordinary callers from temperature monitoring,
Resume, EL sensing, and off sensing. That broader reuse reinforces a lifecycle
frame-mode role, but does not prove any one of those paths ran in this event.

## Selected-controller getter

The selected 5 MiB package is SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
For image 0, `FILE = linked VA + 0x200`.

The ordinary F300 read table begins at FILE `0x219b0`, uses linked table PC
`0x217b0`, and indexes aligned selectors from `0x24` with signed 32-bit
entries. Selector `0x160` is entry 79. Its displacement is `0x576`, giving
leaf VA `0x21d26`.
That leaf calls getter VA `0xfda6` and returns through the common response
path VA `0x2178e`:

```text
21d26  bl    0xfda6
21d2a  b     0x2178e

0fda6  push  {r4,lr}
0fda8  bl    0xe670
0fdac  ldrh  r0,[r0,#0x37a]
0fdb0  uxtb  r0,r0
0fdb2  pop   {r4,pc}
```

Accessor VA `0xe670` supplies the common object. The getter reads its
halfword `+0x37a` and returns only the low byte. It does not consult an update
state, maintenance record, USB state, fault selector, or readiness flag in
this selected leaf.

The separate ordinary F300 write table maps selector `0x160` to VA `0x2cdfc`.
That leaf passes the incoming low byte to helper VA `0x2555c`. Under its local
conditions, the helper accepts only values below 3 and can update common
object `+0x37a`; it compares companion halfwords `+0x37c/+0x37e` first. This
corroborates a small mode/state field but does not assign physical refresh
rates to values `0`, `1`, or `2`.

Exact selected-image slice pins are:

| role | linked VA / bytes | SHA-256 |
| --- | --- | --- |
| `0x160` read-table leaf | `0x21d26 / 6` | `8ad54a970aef52f5a0adffd03adce5c1277d3e40d0c2823e8e04b401a7d359c7` |
| scalar getter | `0xfda6 / 14` | `97a453599947649f4a5e7a20a1766b5363d7090ee33cc40e51de7bb3281f5b82` |
| `0x160` write-table leaf | `0x2cdfc / 14` | `4cf388a15173bfa7a9e87f164e13b7bff549030336abfdbc97aba080e788c527` |
| conditional scalar helper | `0x2555c / 62` | `8cc1f62b890d966202f387a1c9e5c53432f4d3f6fc13edd1fcab313f02eade99` |

## Update/maintenance boundary

The copied QDF module has distinct update symbols and state, including
`m_get_tcon_update_command`, `tcon_flash_update`,
`QDFTcon_GetUpdateUsbStatus`, `QDFTcon_DoUpdate`, and
`QDFTcon_DoTconCadUpdate`. The bounded `m_tcon_recovery_frame_mode` body does
not call those APIs, and the selected controller `0x160` getter above only
returns common-object `+0x37a` low byte.

Accordingly, the retained zero cannot close AU's maintenance-idle or
vendor-parser-ready prerequisites. Its useful meaning is narrower: at that
sample the completed ordinary read returned frame-mode scalar zero, and QDF
used that value for a cached-frame-mode comparison during the normal MODE2
on-tail. Whether it matched the QDF cache at that instant is not retained in
the wire transaction alone.

This report does not infer a physical refresh rate, panel emission, hardware
acceptance, repair, current live value, or causal connection to the blackout.
