# Selector `0x0c` in the retained `tcon-monitor` traffic

This note is an offline interpretation of the four selector-`0x0c` reads in
`overnight/capacity-20261026t1648.onset/trace`.  It does not execute a getter
or any other command on the TV.

## Inputs and bounded result

| Input | SHA-256 |
| --- | --- |
| `binaries/qdf_tcon.ko` | `97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63` |
| retained capacity trace | `403d6951854ae14e312d894534a02b1fe42bb59e576ef58fe9ef8a44994058e7` |
| retained decoder derivative | `17e4671e5472b94c36e3cc34c9367320ecf3d62b59e81df4a019abd5993f11a9` |
| disassembly scratch: `selector0c-qdf-monitor.raw.disasm` | generated offline from the above module |
| disassembly scratch: `selector0c-read-helper.raw.disasm` | generated offline from the above module |

The selector is a **read-only external-PCB-temperature getter** in this exact
module—not a mute, dimming, power, frame, or optimization command.  The four
captured replies (`0x00170017`) split by the getter into two unsigned 16-bit
fields, each `0x0017` (23 decimal).  The routine's symbol name supports calling
them two external PCB temperature outputs; the copied code does not establish
their unit, sensor placement, calibration, accuracy, or relationship to OLED
emission.

## Exact mapping

`m_get_ext_temperature_pcb` begins at `.text+0xacd8`.  On its ordinary
non-null-output, non-skipped path it constructs and reads the exact packed QD
command:

```text
0xad24  mov  x0, #0xc
0xad28  add  x1, sp, #0x4c       ; u32 reply storage
0xad2c  movk x0, #0xf380, lsl #32
0xad30  bl   .text+0x9b88        ; m_read_cmd.constprop.0
```

After the read, `.text+0xad50..0xad5c` performs:

```text
output_0 = reply >> 16
output_1 = reply & 0xffff
```

`QDFTcon_GetExtTempPcb` at `.text+0xaeb0` is the public wrapper.  It forwards
two caller output pointers to that helper at `0xaec8`; only if the helper
returns nonzero does it zero both wrapper outputs (`0xaed0..0xaed8`).  The
module's symbol table names the helper `m_get_ext_temperature_pcb` and wrapper
`QDFTcon_GetExtTempPcb`.  This is the source of the temperature interpretation,
not a conclusion from the `tcon-monitor` task name.

The only retry in this helper is data-specific: it checks the reply's low byte
against `0xff` at `0xad3c..0xad44`, sleeps 10 ms, and repeats the exact `0x0c`
read at `0xae50..0xae64` on that sentinel.  `0x00170017` has low byte `0x17`,
so the observed reply does not select that retry branch.  No immediate retry
appears in any of the four retained read sequences, consistent with that
control flow.

The static module contains two actual constructions of `0xf3800000000c`, both
in this helper (`0xad24..0xad30` and retry `0xae5c..0xae64`).  The separate
`0x9bbc..0x9bcc` occurrence is a comparison in `m_read_cmd` for its
command-skip exception; it does not issue a selector-`0x0c` command.

## Trace correlation

The decoded capacity trace records four complete read transactions with comm
`tcon-monitor`, PID 1019:

| Uptime | Command | Reply |
| ---: | --- | --- |
| 54773.721788 | `f3800000000c` | `00170017` |
| 54794.734453 | `f3800000000c` | `00170017` |
| 54815.745316 | `f3800000000c` | `00170017` |
| 54836.755079 | `f3800000000c` | `00170017` |

Each retained two-message Linux transfer has `ret == n == 2`; this establishes
the traced kernel transport result, not MCU-level acceptance.  The `~21.01 s`
cadence is observed behavior only.  The comm name and trace do not expose the
userspace/kernel caller stack, so they do not prove which external user of the
public wrapper made each call.  Static relocation entries at module offsets
`0x27c` and `0x284` expose `QDFTcon_GetExtTempPcb` through the module's
function mapping; they do not bind an individual captured process call.

## What it does not establish

- The two `23` fields are not independently calibrated as degrees C (or any
  other unit) by this evidence.
- Successful Linux I²C transfer is not a controller health verdict, a
  sensor-validity guarantee, panel-power proof, or emitted-light proof.
- This getter neither writes a QD control selector nor proves that no separate
  suppressed/internal/other-address action occurred outside its four records.
- The capacity capture remains technically incomplete due to its unmatched
  AVOC ioctl boundary and has no human physical picture annotation.  Its
  temperature reads cannot diagnose or exclude the sparse-menu blackout.
