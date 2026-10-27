# Runtime QD profile line: exact producer and field provenance

## Result

The retained composite line is made by the **QDF kernel module**, not by AVE,
the MICOM shared-memory log producer, or a CAD-file parser.  In the exact
`qdf_tcon.ko`, `QDFTcon_MonitorTemperatureSensor` conditionally calls
`QDFTcon_Tcon_GetTCONFlashVersion`, passing its own instance buffer at
`+0x328`.  The callee fills that buffer with:

```text
[QDF]FW[%s/F:%s]MD[%s/F:%s] 
[Int.Tcon]FW[%02X%02X]DATA[%s]
```

and the caller immediately supplies that buffer as the second `%s` in its
own kernel `printk`:

```text
[TCON INFO] PANEL[%s] %s T[%d] TSt[%d] H[%d] P[%d] U[%d][TCON INFO END]
```

This is the static source of the observed combined line.  It makes the four
displayed QDF/MD values from four freshly zeroed local buffers and four calls
to the registered `tztv_i2c_read_common` reader.  No ordinary file is opened
or parsed in this bounded producer path.

Accordingly, the runtime line is stronger than a mere cached CAD filename:
when its buffers contain the observed nonempty strings, those characters came
through this query callback during the call.  It is **not** proof that the
underlying device values identify a currently executing image, a particular
flash partition, an applied CAD asset, or the producer/clear path for RT
Protect.  Those meanings require the downstream I2C provider/controller ABI.

## Exact inputs

| item | value |
| --- | --- |
| module | `binaries/qdf_tcon.ko` |
| module SHA-256 | `97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63` |
| machine | AArch64 relocatable kernel module |
| full-line entry | `QDFTcon_MonitorTemperatureSensor`, `.text+0x10928`, 1,472 bytes |
| QDF/MD formatter/query | `QDFTcon_Tcon_GetTCONFlashVersion`, `.text+0x47a0`, 792 bytes |
| registered lower reader | `m_i2c_burst_read`, `.text+0x2220`, 552 bytes |

The relevant format strings reside in `.rodata.str1.8` and are referenced by
relocations at the instruction sites below.  This report is offline static
analysis only; no QDF entry, I2C callback, controller read, CAD operation, or
file operation was invoked.

## Full-line call and buffer chain

`QDFTcon_MonitorTemperatureSensor` begins at `0x10928`.  Its periodic branch
at `0x10b74..0x10b94` is reached only after the unsigned jiffies delta is
greater than `300000` ms at `0x10950..0x10968`, with the observed instance
gates at `+0x328` byte zero, `+0x6c` word zero, and `+0x10 == 1` (the last
comparison is `0x10b8c..0x10b94`).  The exact semantic names of those fields
are not recovered here.

On that path, `x0` is the instance buffer at `+0x328` from `0x10b78`; the
call at `0x10e28` invokes `QDFTcon_Tcon_GetTCONFlashVersion`.  The latter
keeps that input pointer in `x21` at `0x47c4`, then writes the composite
QDF/Int.Tcon text to it with `ft_vsnprintf` at `0x4a18..0x4a30`.

Control returns to `0x10b98`.  At `0x10bd4` the caller sets the second `%s`
argument to `instance+0x328`; at `0x10bd8..0x10be4` it resolves and calls the
`[TCON INFO] PANEL...%s...` format through `printk`.  The panel string itself
is `instance+0x1d0` at `0x10bd8`; that field's initial writer is outside this
bounded trace.  This establishes composition and logging, but not a semantic
identity for `PANEL[77A3OUSOF]`.

The same formatter has only two direct calls in this module's relocation
table: the monitor call at `.text+0x10e28` and a debug command call at
`.text+0x152cc` in `QDFTcon_Tcon_Debug`.  The latter allocates a 128-byte
temporary output buffer at `0x152bc..0x152cc` and prints it, so it is not a
file/profile-loader path either.

## The four exact QDF/MD field sources

The formatter zero-initializes each local destination before use.  It then
calls `m_i2c_burst_read` with operation argument zero, 16-bit address, byte
count, and destination as follows:

| final format argument | call site | 16-bit address after mask | bytes | local output passed to final formatter |
| --- | ---: | ---: | ---: | --- |
| `FW[%s` | `0x4848` | `0xfea4` | 9 | `sp+0x62` via `ft_vsnprintf` at `0x4860..0x4868` |
| `FW[/F:%s]` | `0x488c` | `0xfea3` | 9 | `sp+0x6c` via `ft_vsnprintf` at `0x4898..0x48a0` |
| `MD[%s` | `0x48b4` | `0xfe64` | 16 | copied to `sp+0x86` at `0x48b8..0x48c4` |
| `MD[/F:%s]` | `0x48ec` | `0xfe63` | 16 | copied to `sp+0x97` at `0x48f0..0x4900` |

`m_i2c_burst_read` masks the passed address to 16 bits at `0x223c`, reverses
that 16-bit value at `0x2270`, and, on its selected normal path, calls the
registered `tztv_i2c_read_common` function pointer at `0x2294..0x22b8` with
bus `5`, address `0x76`, a two-byte address field, caller byte count, and
caller buffer.  The helper has state/error gates before that call; in
particular it can return without a provider transfer.  The formatter does not
check the four helper return values before it emits its strings.

This gives a precise reading of the observed value:

```text
MD[F77ABUAE20312300/F:F77ABUAE20312300]
```

The complete 16 characters on each displayed side—including the previously
unsourced intervening `03`—are a 16-byte output buffer from `0xfe64` and a
separate 16-byte output buffer from `0xfe63`, respectively.  They are not
assembled in this QDF formatter from the first-nine and final-five strings in
the retained CAD asset.

Likewise the equal `/F:` strings show that the two queried output buffers were
equal in that logged call.  The static format provides no expansion for the
letter `F`; calling it “factory”, “flash”, “fallback”, or an on-disk profile
would be an unsupported interpretation.

## What this changes—and what it does not

The retained CAD has a unique three-field textual match with the runtime
tuple, and newly recovered contents show that it includes executable regions.
That remains useful candidate evidence.  But the QDF line's producer does not
open that CAD pathname or read its bytes: its bounded dataflow is four I2C
reader calls into a temporary buffer.  The tuple therefore cannot establish
that the CAD file was selected/applied this boot, nor that the controller's
running image is byte-identical to it.

The static module also cannot prove what the downstream I2C provider reads:
it may address live controller memory, a controller-exposed cache, or another
device-defined region.  The module's own `QDFTcon_Tcon_GetTCONFlashVersion`
name and `F:` labels are not enough to choose among those meanings.  Its
nonempty raw log values establish only that the temporary output buffers held
those characters when `printk` formatted the line; because helper return
values are ignored, they do not by themselves prove four successful
normalized transfers.

Thus the correct current conclusion is a **QDF monitor-time query record**,
not an active-profile, file-open, firmware-flash, or RT-Protection causality
record.  The next source boundary, if it becomes useful, is the exact
registered `tztv_i2c_read_common` provider and its address semantics—not a
new CAD acquisition or a TEEC operation.
