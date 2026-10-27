# Independent review — managed ERR_DET cdev metadata probe

Review date: 2026-10-26 UTC

## Outcome

**CLEAR for one finite metadata-only invocation of the exact package below.**

This clearance is deliberately narrow.  It does not clear the compiled
`--input-once` branch, does not clear an 85/90-second capture, and does not
authorize a retry or loop.  An accepted result would establish only current
GPIO-chip/line metadata.  It would not request the line, sample its value,
lock its ownership, establish a physical panel state, or identify the cause
of the black panel.

## Exact reviewed bytes

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `Program.cs` | 6,881 | `266b0cc7e74c2265f4839d24b363f7db535c4864f5376147bc54f390aafaa01a` |
| `ErrPinCdev.csproj` | 431 | `b36c8c28566c3dd5e50bdd47b905ced7cb617356068c0656a85d0303f2fef77e` |
| `run-errpin-cdev.py` | 25,553 | `91b292f607bca3f9e150548d9b3f8a2173a35f8e8dc9ce507d755025ed66524a` |
| `build-manifest.json` | 1,233 | `c34ac1153af5fc7e3e39fac6337b4be8243448b6f59dba675ea18b21fd9abf46` |
| `ErrPinCdev.dll` | 11,264 | `2d2c243d32100811de1c3fcf34e7e258871d74b908a0aafb093f853f294ac0c1` |
| `ErrPinCdev.deps.json` | 400 | `2bae0530a20c2c2d41856ced54a681c0f94d3e7facb8eb394db3686960e7fa9b` |
| `ErrPinCdev.runtimeconfig.json` | 242 | `aeb46a15366e38511c192ccf65312442c64e8753b3c16fd2ca0b4cb34a5c59f3` |

The runner also pins:

- the cdev ABI report as `2e569fee229a30f291d0b4712344f5e5694b1430ea62e0c4f20dbe1000337170`;
- the paired-Image `set_config == NULL` report as `4985f8a6e3508479436c51f1980ec6d7ed49278cc29ccca8afe73637163dcd77` in the build manifest; and
- the persistent-root client as `3a92e02003ce51d2faeace231191f6f0c73731f2bfca9caa196e05b195b439a5`.

## Action and identity audit

The public live path stages the hash-pinned portable managed payload and
executes it with **no arguments**.  Therefore the reviewed live command cannot
select the compiled `--input-once` branch.

The no-argument branch performs exactly this device sequence:

1. open `/dev/gpiochip15` with `O_RDONLY | O_CLOEXEC`;
2. issue `GPIO_GET_CHIPINFO_IOCTL` (`0x8044b401`);
3. issue `GPIO_GET_LINEINFO_IOCTL` (`0xc048b402`) for offset 5; and
4. close the chip descriptor.

It does not issue `GPIO_GET_LINEHANDLE_IOCTL` or
`GPIOHANDLE_GET_LINE_VALUES_IOCTL`.  Accordingly, it does not request the
descriptor, call the provider's direction-input path, read the pin, or set an
output/value/active-low flag.  The v5.4.261 line-info path copies metadata and
checks whether the pin may be used; it does not claim the line or configure
the provider.

The corrected preflight now proves the complete route identity rather than
checking two disconnected facts:

- `/dev/gpiochip15` is the nonsymlink character device `fe:f`, mode 0600,
  owned by root;
- `gpiochip120` reports label `gpio15`, base 120, and 8 lines, and its device
  resolves to `/sys/devices/platform/soc/4630000.pinctrl`;
- TCON `samsung,err_det` is exactly phandle 36, offset 5, flags 0; and
- `/soc/pinctrl/gpio15` has phandle 36, `#gpio-cells = 2`, the
  `gpio-controller` property, and exact NUL-terminated name `gpio15`.

The managed process independently requires ARM32, four-byte pointers, little
endian layout, exact v1 structure sizes/offsets, root UID/EUID, chip name and
label `gpiochip15`/`gpio15`, 8 lines, returned offset 5, flags zero, and an
empty consumer.  Host acceptance additionally requires exact output-field
inventory, successful chip-info/line-info/close returns, empty managed
stderr, stable boot anchors, helper identity/deadline success, postflight
payload identity, and confirmed private-directory cleanup.

The transport uses the pinned host-assisted persistent root path with a
25-second remote timeout.  Its private directory is root-owned mode 0700;
staged and generated files are mode 0600.  The helper uses a PID/start-tick
ready/GO handshake and guarded TERM/KILL cleanup.  Cleanup accepts only the
fixed allowlist of staged/output filenames.  All controller responses are
retained in the unique result before interpretation.

## Independent checks performed

- Recomputed every hash above from the local reviewed files.
- `python3 -m py_compile` passed for the runner.
- Normal and `python3 -O` dry plans were byte-identical.
- The dry plan contained 11 root commands; the largest was 7,813 bytes, under
  the root client's 8,192-byte limit.
- Generated all 11 shell commands and checked each with `/bin/sh -n`.
- Confirmed the exact execute command contains no `--input-once` argument.
- Exercised the result parser with a complete successful metadata fixture.
  It accepted only `metadata_only`.
- Confirmed parser rejection for a nonempty consumer, nonzero line flags,
  and an extra/duplicate managed field.

## Limits retained

- The metadata is point-in-time and is not an ownership reservation.  A
  later input request can still race another consumer.
- Metadata-only execution does not exercise `gpio_chip.direction_input`,
  `.get`, or `.set_config`.  The paired-Image NULL `.set_config` evidence is
  relevant to a future request analysis, not needed to classify this run.
- The compiled `--input-once` implementation remains **HOLD**.  It would be a
  distinct, side-effecting request: descriptor ownership, direction-input
  provider work, one value read, and a transitory software flag until close.
- Successful-call errno checks can conservatively reject an otherwise valid
  run if the runtime exposes stale errno.  That is a possible false negative,
  not a path to false acceptance or an extra device operation.
- No accepted metadata result would support a panel-recovery, controller
  health, electrical-level, or fault-causality claim.
