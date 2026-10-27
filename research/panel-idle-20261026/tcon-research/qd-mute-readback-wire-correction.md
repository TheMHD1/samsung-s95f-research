# QDF mute readback: exact command correction and rescued wire evidence

This is an offline correction to the older panel-mute report. Older reports,
decoder source and frozen evidence are preserved. No TV call or control was
issued for this analysis.

The older `overnight-panel-mute-gates.md` describes the stock zero-setter's
readback command as `F3 80 00 00 01 64`. The exact copied QDF code instead
constructs **`F3 00 00 00 01 64`**, and the I2C transfer's second message is a
four-byte **read**. The opcode prefix alone therefore cannot classify this
specific command as a write.

In hash-identified `qdf_tcon.ko` SHA-256
`97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63`,
section `.text`, `QDFTcon_t_Tcon_SetMute` contains:

| Offset | Instruction | Effect |
| --- | --- | --- |
| `0xcf98` | `add x1, sp, #0x30` | Four-byte output storage address |
| `0xcf9c` | `mov w2, #0xff` | Output initializer |
| `0xcfa0` | `mov x0, #0x164` | Low command bits |
| `0xcfa4` | `str w2, [sp, #0x30]` | Initialize the output word |
| `0xcfa8` | `movk x0, #0xf300, lsl #32` | Full command `0xf30000000164` |
| `0xcfac` | `bl 0x9b88` | `m_read_cmd.constprop.0` |

The [new bounded verifier and decoder supplement](../overnight/trace-qd-mute-readback.py)
pins both the module and original decoder. It verifies the six instruction
words, extracts the command and branch target, and recognizes only a complete
two-message bus5/address118 transfer with this exact command and a four-byte
read reply. Thirteen malformed/valid/provenance checks passed locally. It leaves
the original decoder unchanged.

The [rescued run's supplemental decode](../overnight/owner-power-on-mute-readback.json)
finds one such read by deviced at uptime73137.280043--73137.280396, returning
bytes `00 00 00 00`. The Linux transfer reported both messages transferred.
This follows the recorded mute-zero write at73136.725190. It supplies a
concrete returned zero for this stock mute-status transaction during wake.

It does not establish that the physical panel was black at that exact instant,
that the failed public unmute test at72719 used the same lower path, that every
gate was open, or that the controller/panel was healthy. The owner reports
brief picture then black with audio, but chat timing is not calibrated. The
original 85-second capture remains rejected for missing completion/end-state
evidence, despite this intact trace segment. No extra request was sent.

This does not change `QDFTcon_GetErrDetStatus`'s separately constructed
`F3 80 00 00 00 08` command. Each command form needs its own exact provenance.
