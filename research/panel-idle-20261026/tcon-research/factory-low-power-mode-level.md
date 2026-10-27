# Factory Low Power Mode Level — exact offline mapping

## Identity

The read-only FactoryService record identifies `170802`, current value `6`, as
`Low Power Mode Level`.  It maps to the QDF factory UID `20513` (`0x5021`):
the neighbouring verified mapping is `60802 -> 20505 / 0x5019` for Screen
Saver Brightness, and QDF's `QDFTcon_SetFactoryData` case `0x5021` is the LPM
setter.

## Exact QDF behaviour

`QDFTcon_SetFactoryData(0x5021, value)`:

1. stores `value` in QDF's in-RAM `m_lpm_level`;
2. calls `m_set_lpm_level(value)` at module offset `0xe4c0`.

`m_set_lpm_level` accepts only values `0..8`; values above `8` return an
error.  For an accepted value it sends one QDF TCON command:

```
command: 0xf30000000140
payload: requested LPM level (0..8)
```

The function does not call the TCON power-control/reset path, fault counters,
thermal handling, voltage/ELVDD setting, calibration, or factory test code.

## Important scope limits

This is not merely a UI/display-compositor option.  QDF reapplies the scalar
as part of both its TCON initialization and its no-framerate recovery register
restore sequence, alongside screen-saver, IPS, pixel-shift, and tone-mapping
configuration.  It therefore changes a genuine panel-firmware low-power-mode
policy.

The label and accepted range do **not** prove that value `0` means “disabled.”
The panel microcode that interprets command `0xf30000000140` was not acquired.
No conclusion can be drawn that setting `0` is safe, that it avoids only
content-sensitive LPM, or that it will repair a damaged panel latch.

FactoryService setters may persist the value.  A write would be a real,
hardware-policy factory change and is not justified by the completed captures
until a separately authorized, bounded plan specifies persistence, exact
restore behaviour, and physical observation criteria.

## Relation to AVE LPM/NewHome

AVE has separate high-level `SetLpmModeFlag`, `gLpmState`, and NewHome/low-power
art code.  No direct static call edge in the copied binaries connects those
AVE state functions to QDF UID `0x5021`; they should not be conflated.  The
factory level is sent to TCON during QDF init/recovery, while AVE NewHome
changes FRC/render context.
