# Overnight QDF/FRC reverse engineering — policy, wire path, and safe evidence

Scope: static analysis of the copied, SHA-verified `qdf_tcon.ko`,
`tztv_frc_tcon.ko`, and `tztv_frc_tcon_api.ko` only.  No command was sent to
the television, no module was modified, and this is not a recommendation to
call undocumented ioctls.

## 1. What `Low Power Mode Level = 6` actually means in host code

The factory item `170802` maps to QDF factory UID `0x5021`.  In
`QDFTcon_SetFactoryData` (`qdf_tcon.ko:.text+0xf498`), case `0x5021` stores the
requested integer in `m_lpm_level` and calls `m_set_lpm_level`
(`.text+0xe4c0`).  The latter is a very small routine:

```
e4c4  cmp   w0, #8                  // only 0..8 accepted
e508  mov   x0, #0x140
e50c  mov   w1, w19                 // requested level
e510  movk  x0, #0xf300, lsl #32    // 0xf30000000140
e514  mov   w2, #1
e518  bl    m_send_cmd_with_lock
```

It has no host-side branch that assigns a semantic such as “off”, “normal”,
or “brightness” to levels 0–8.  The string is only `lpm onoff : %d`, while the
factory label is “Low Power Mode Level”; the semantic is implemented by the
TCON firmware receiving command `F3 00 00 00 01 40` with a one-byte payload.

Most importantly, there are exactly three direct calls to `m_set_lpm_level`:

| Caller | `.text` call site | Meaning |
|---|---:|---|
| `QDFTcon_SetFactoryData` | `0xf680` | Factory setting application |
| `QDFTcon_Tcon_InitDevice` | `0xfcb0` | Normal QDF initialization |
| `m_register_recovery_noFramerate` | `0xf770` | Restore policy during no-framerate recovery |

There is **no QDF caller from APL, AVEMonDIM, screen-saver brightness, a UI
tab, or a per-frame path**.  This disproves a host-code theory that sparse
For You / Live content changes `LPM=6` at the moment of a blackout.  It does
not disprove that panel firmware, once configured to level 6, reacts to image
content internally.

The available binaries contain no matching TCON firmware image or command
table (`FA024C300` / `F77ABU2D20`).  Therefore level `0` cannot honestly be
called “LPM disabled.”  Its only proven meaning is “send payload 0 to the
opaque TCON LPM command.”  That makes a factory write an unsuitable first
experiment, especially because the factory-service persistence behavior is
outside this module.

## 2. Content-related QDF controls versus actual power and mute

The module has separate command families, all sent through the same locked QD
transport:

| Function | command word | accepted range | host relation |
|---|---:|---:|---|
| `m_set_ss_method` (`0xece0`) | `0xf300000000c0` | 0..2 | Screen-saver method |
| `m_set_ss_sensitivity` (`0xe740`) | `0xf300000000c8` | 0..64 | Screen-saver threshold/policy |
| `m_set_ss_waiting_time` (`0xe9e8`) | `0xf300000000cc` | 0..2 | Screen-saver timing |
| `m_set_ss_slope` (`0xe870`) | `0xf300000000d0` | 0..2 | Screen-saver transition policy |
| `m_set_ss_brightness` (`0xeb60`) | `0xf300000000c4` | 0..7 | Screen-saver brightness command |
| `m_set_lpm_level` (`0xe4c0`) | `0xf30000000140` | 0..8 | TCON low-power policy |
| `QDFTcon_t_Tcon_SetMute` (`0xce00`) | `0xf30000000164` | boolean-like caller value | Actual QD mute gate |

This makes the separation concrete: AVEMonDIM’s observed screen-saver command
is `…00c4`; it is not a TCON power command and it is not QD mute (`…0164`).
Likewise LPM (`…0140`) is a different persistent policy word.  The prior
negative 7→0→7 factory Screen Saver Brightness trial is therefore only a
negative *post-black recovery* result; it does not test LPM and cannot prove
screen saver caused the blackout.

`QDFTcon_t_Tcon_SetMute` tracks `m_mute_state` at BSS offset `0x140`, writes
the `…0164` command only when state changes, and on unmute performs reads of
`F3 80 00 00 00 20`, `…21`, and `…22` before deciding whether to re-send mute
zero.  This is an actual panel gate, unlike the already-observed black state
where AVOC and QD-level mute indicators are zero.  It must not be used as an
assumed reset.

`QDFTcon_SetQdTconPowerControl` (`0x11c48`) is distinct again:

* argument `0` calls `m_set_power_control(0)`;
* `1` calls `m_set_power_control(1)`;
* `2` calls `m_set_power_control(0)` followed by `(1)`.

This is the real TCON off/on route with rail/GPIO effects.  It is deliberately
excluded from any workaround proposal.

## 3. Exact QD transport framing for a passive trace

`m_send_cmd_with_lock` (`0xbba0`) and `m_read_cmd` (`0x9b88`) form six-byte
requests from the 48-bit command value, then call mapped functions
`tztv_i2c_write_raw` / `tztv_i2c_read_raw` or their `*_common` equivalents.
The raw branch calls its handler with fixed arguments:

```
x0 = 5
w1 = 0x76
x2 = command-buffer
w3 = 6                 // write request bytes
```

For reads it subsequently uses the same `x0=5, w1=0x76` and a four-byte reply
buffer.  Thus a passive kernel I²C trace can identify this QD transport by the
driver argument `0x76` and six-byte write length.  Do **not** label `0x76` a
7-bit slave address: static code establishes only the value passed to the
vendor helper; whether that helper expects 7- or 8-bit addressing is not
shown here.

Examples of wire-order command bytes established by the byte construction:

```
LPM level:     F3 00 00 00 01 40  + payload 0..8
SS brightness: F3 00 00 00 00 C4  + payload 0..7
QD mute:       F3 00 00 00 01 64  + payload 0 or 1
Status read:   F3 80 00 00 00 00  -> four-byte reply
```

The “payload” is carried by the vendor command transaction; the static QDF
caller passes it separately to `m_send_cmd_with_lock`.  A generic
`i2c_write`/`i2c_read` trace can show ordering, length, address argument and
returned bytes without issuing any new command.

## 4. What existing replies can and cannot establish

`m_check_tcon_status` uses `F3 80 …00` and then related `…03` / `…01`
status-read paths, retrying the `…00` reply against the exact marker
`0xABABABAB`.  QD mute uses `…20/21/22`.  These are
communication/status registers used by stock recovery.  They can establish
that the TCON answers and whether its driver-visible state changed.  They are
**not an OLED-emission or pixel-light sensor**: no code in the copied QDF
module maps any reply byte to luminance, APL, or a successful physical image.

The previously observed physical-black state with advancing composition,
LVDS-on, logical screen-on, TCON power, PMIC/HSM normal and mute zero is
therefore compatible with a panel-side/content-dependent failure that these
status queries do not measure.  It is not evidence that an error detector,
TCON power state, or software compositor stopped.

## 5. Next-day minimal evidence plan — passive only

Before considering any persistent setting, capture two **read-only** windows
with the existing ftrace events only (no raw I²C command and no undocumented
ioctl):

1. Stable full Apps / screen-saver-visible control window.
2. A naturally occurring For You / Live physical-black window, with the same
   bounded duration and aligned surface/DRM state capture.

For each, correlate only:

* QD transport transactions (helper argument `0x76`, six-byte write /
  four-byte read) and the command bytes above;
* existing GPIO/regulator/clock/DRM events;
* kernel QDF/AVEMonDIM logs and the already-safe AVOC mute/video-gray getters.

The discriminator is not a single reply byte.  It is whether black windows
show an actual `…0164` mute command, `…0140` LPM reprogramming, power/rail
event, or only continued normal transport/composition.  If none differ, the
evidence favors a panel-internal response to content rather than a host
policy transition.  At that point an extracted matching TCON firmware image
would be required to assign level-6/0 semantics; blind factory writes remain
unjustified.
