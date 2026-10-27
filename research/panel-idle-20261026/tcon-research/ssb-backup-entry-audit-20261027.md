# SSB backup entry: exact initialization and ioctl boundary

This is a static, offline supplement. It did not open an SSB device, invoke
an ioctl, attach USB, or modify the controller. It replaces an earlier,
too-general supplement with the actual guard and dispatch facts needed to
evaluate a later, separately reviewed acquisition design.

## Input and coordinates

The only inspected input is
`overnight/sdp-pqe-frc-provider-copy-20261026a/sdp_pqe_frc.ko`, SHA-256
`1a312cf33a0ca67c170b9dc73a56a58fa03a0f05bbfb6277a72740dd8e7328a4`.
Coordinates are section-relative `.text` addresses in that relocatable
AArch64 module. `R_AARCH64_CALL26` names are resolved from its `.rela.text`;
the copied zero immediate is not treated as a zero-address call.

## Result: two separate initialization roots

The SSB character-device ioctl is not a bootstrap root where no SSB node is
already present. `ssb_ioctl` requires a non-null pointer loaded from the
file object at offset `0xc8` before dispatch. Retained metadata had no
`/dev/ssb1`/`/dev/ssbs1` or corresponding usbmisc node.

There is a separate exported PQE root: `tcon_ex_proc` (`.text+0x58048`, with
`__ksymtab_tcon_ex_proc`). It calls `_ssb_init_func` before inspecting its
low-16-bit selector. A consumer of that export could therefore reach setup
without first opening a character node. The copy does not identify a live
caller or prove a particular PQE operation is appropriate for backup.

`_ssb_init_func` can request and register an SSB USB driver. This is an
active setup path, rather than a passive availability check.

## `_ssb_init_func`: exact predicates and state

The local initializer is `.text+0x573e8`, size 272. Its state pointer is
relocation-resolved at `0x573ec/0x573f8` to `.bss+0x44a0`.

| CFG site | exact machine condition | consequence |
|---|---|---|
| `0x573fc..0x5740c` | Load byte `state+4`; a nonzero value takes only a log detour. Load `u32 state+8`; nonzero returns `0`. | `state+8 != 0` is the direct no-work success bypass. This audit does not assign a semantic name to `state+4`. |
| `0x57420..0x5742c` | Two relocation-resolved calls to `frc_pqe_sys_get_dimming_info`; `TBNZ w0,#1`, then `TBNZ w0,#2`. | Either set bit returns `-1` at `0x5747c..0x5749c`; no registration occurs. Bit meanings are not inferred from the function name. |
| `0x57454..0x57458` | Call `resolve_usb_symbols`; branch toward registration only if returned `w0 != 0`. | Zero returns `-1` at `0x5745c..0x57478`. |
| `0x574d4..0x574ec` | Call `ssb_usb_register_driver`; compare result exactly with `1`; store the matching `1` at `state+8`. | Only exactly `1` yields initializer return `0`; any other result returns `-1`. |

`ssb_usb_register_driver` (`.text+0x5b9f8`) calls `__symbol_get` at
`0x5ba10`. If absent, it calls `__request_module` at `0x5ba54`, repeats the
lookup at `0x5ba5c`, and invokes the non-null result indirectly at `0x5ba34`.
Its inputs include relocation-backed pointers `.data+0x450` and
`__this_module`. Thus the initializer crosses a kernel registration boundary;
the live symbol target and resulting probe effects are not resolved by this
static copy.

## PQE root and selector facts

`tcon_ex_proc(w0, x1, w2)` saves `w0` at `0x58060`, calls the initializer at
`0x58080`, and returns `-19` after an initializer failure
(`0x58084..0x581f4`). On success it masks the saved selector to 16 bits at
`0x58094`, then takes a mutex before dispatch.

| selector after `& 0xffff` | exact path | recovered behavior |
|---|---|---|
| `0x20` | `0x580b8..0x58100` | Calls `ssb_usb_device_ready` at `0x580cc`; if that returns zero, writes zero to `x1+30` and returns `-19`. |
| `0x21` | `0x5811c..0x583a4` | Calls `ssb_usb_device_ready` at `0x58368`, stores its low byte at `[x1]`, and returns through the common unlock path. |
| `0x24` | `0x58154..` | Enters a file-path/data-processing worker, not reconstructed further in this focused bootstrap audit. |

These are not backup operations. They demonstrate the non-fops initializer
caller and immediate readiness checks. A later design would need to bind a
real consumer to the exported ABI rather than invent an operation selector.

## Character-device ioctl ABI and circular fops dependency

The `ssb_fops` object contains an absolute relocation at offset `0x50` to
`ssb_ioctl` `.text+0x591a8`. Its read branch has this exact ABI:

| site | exact action |
|---|---|
| `0x591b8..0x591c8` | Preserve ioctl argument `x2` in `x21`, file context `x0` in `x20`, and command `w1` in `w19`. |
| `0x591d4..0x591d8` | Load `[x20+0xc8]`; null returns `-19` at `0x5922c`. (`objdump` renders this immediate as decimal `#200`.) |
| `0x591dc..0x59228` | `w1 == 0x0a`: move original `x2` unchanged to `x0`, preset wrapper return `0`, then call `tcon_read_backup_data` at `0x59224`. `w1 == 0x0b` calls restore at `0x59214`; other commands return `-1`. |
| `0x591f0..0x59208` | Return the preset wrapper status, not the read/restore callee status. |

So the recovered read form is **command `0x0a` plus an unmodified pointer in
`x2`**. It is not a reconstructed fixed C struct. The target first calls
`_ssb_init_func` (`0x58a78`), checks the pointer, then copies `0xfa` bytes
from it into a stack buffer (`0x58adc..0x58ae8`). It calls `file_open` with
literals flags `0x241` and mode `0x1b6` (`0x58b50..0x58b5c`), allocates
`0x2000` bytes (`0x58b74`), then uses transfer literals target `0x203`, chunk
`0x2000`, total `0x500000` (`0x58b90..0x58bb8`). This rejects describing the
operation as a no-effect getter, but is not an invocation recipe.

The fops bootstrap dependency is concrete:

```
open existing ssb character node
  -> ssb_open populates file-object field + 0xc8
  -> ssb_ioctl(command 0x0a)
  -> tcon_read_backup_data
  -> _ssb_init_func
```

With no node, the first step cannot reach the ioctl. `tcon_ex_proc` is the
separate root that can reach initialization first. No evidence here shows it
calls `tcon_read_backup_data` itself.

## Bounded conclusion

The missing edge is not a vague “how to initialize SSB”: the exported
`tcon_ex_proc` provides a concrete static initialization root. Still missing
are a live caller/validated ABI for that root, successful registration/probe,
and a content-integrity plan for the 5-MiB transfer. The ioctl's zero wrapper
return cannot validate a completed backup because it discards the callee
status. No conclusion asserts that backup repairs the panel or that its USB
transport lacks controller side effects.
