# Independent review — one-shot ERR_DET cdev input reader

Review date: 2026-10-26 UTC

## Outcome

**CLEAR for one separately intentional execution of these exact bytes.**

This clearance does not cover retries, a loop, an output request, a SET-values
ioctl, a sysfs fallback, or any recovery action.  The operation is not a
passive read: it temporarily owns the line, clears the descriptor's software
transitory flag, invokes the vendor direction-input path, reads once, and
frees the line.

## Exact reviewed inputs

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `run-errpin-cdev-input-once.py` | 26,700 | `cd0a34ffd719945bb369ecae16f4ca0672dbbaddea11be068e0f31465e185cde` |
| `build-manifest-input-once.json` | 1,403 | `2c9b1283e718c34e40656099ff9181c9481208fd669d6adda0d4558cc5a46d9f` |
| `Program.cs` | 6,881 | `266b0cc7e74c2265f4839d24b363f7db535c4864f5376147bc54f390aafaa01a` |
| `ErrPinCdev.dll` | 11,264 | `2d2c243d32100811de1c3fcf34e7e258871d74b908a0aafb093f853f294ac0c1` |

The runner also pins the cdev ABI report
`2e569fee229a30f291d0b4712344f5e5694b1430ea62e0c4f20dbe1000337170`,
the paired-Image vendor-callback report
`4985f8a6e3508479436c51f1980ec6d7ed49278cc29ccca8afe73637163dcd77`,
and the persistent-root client
`3a92e02003ce51d2faeace231191f6f0c73731f2bfca9caa196e05b195b439a5`.

## Exact operation

The live command contains exactly one `--input-once` selector.  After the
same route-identity and metadata gates reviewed for the accepted metadata
probe, the program submits one zero-initialized 364-byte request containing:

- offset[0] = 5;
- flags = `GPIOHANDLE_REQUEST_INPUT` (`1`) only;
- lines = 1;
- fd = -1; and
- the bounded ASCII consumer label `researcher-errdet`.

It issues exactly one `GPIO_GET_LINEHANDLE_IOCTL` (`0xc16cb403`) and one
`GPIOHANDLE_GET_LINE_VALUES_IOCTL` (`0xc040b408`).  No SET-values constant or
call exists in the reviewed source.  OUTPUT, ACTIVE_LOW, OPEN_DRAIN,
OPEN_SOURCE, and unknown request flags are absent.

The 64-byte GET buffer is initialized to `0xa5`.  Acceptance requires byte 0
to be 0 or 1 and bytes 1..63 to be zero, which demonstrates complete kernel
replacement of the bounded output structure.  The handle closes in `finally`
before the chip descriptor, and host acceptance requires both close returns
and errnos to be zero.

Before the handle request, acceptance requires the exact GPIO route identity,
chip `gpiochip15`/label `gpio15`/8 lines, line offset 5, flags zero, and empty
consumer.  A racing owner causes the request to fail; there is no retry.

## Independent verification

- `py_compile` passed.
- Normal and `python3 -O` dry plans were byte-identical.
- All 11 generated target shells passed `/bin/sh -n`.
- The largest root command was 7,826 bytes, under the 8,192-byte contract.
- The generated execute shell contained exactly one `--input-once` selector.
- An independent positive parser fixture was accepted.
- Independent negative fixtures rejected nonzero tail bytes, failed handle
  close, a nonempty consumer, nonzero initial flags, extra handle flags, and
  an output value outside `{0,1}`.
- UTF-16 string inspection of the exact DLL recovered the input selector,
  bounded consumer label, GET/value fields, and input-completion marker.

## Side-effect and interpretation boundary

The exact paired boot Image shows `gpio_chip.set_config == NULL`, so clearing
the transitory flag does not deliver a persistence configuration request to
vendor code in that Image.  This is paired-Image evidence, not a live kernel
text hash.  The Linux descriptor flag itself remains cleared after close.

The vendor direction-input callback performs an MMIO read/modify/write even
for an input request.  Closing the line handle synchronously releases its
ownership and consumer label, but does not restore prior direction or the
software transitory flag.

With DT flags zero, pre-request line flags zero, and no ACTIVE_LOW request, a
successful returned 0/1 is a raw GPIO logic-level sample on gpio15 offset 5.
It does not prove connector polarity, OLED emission, panel recovery,
controller health, blackout cause, or the meaning of another subsystem's
cached fault word.
