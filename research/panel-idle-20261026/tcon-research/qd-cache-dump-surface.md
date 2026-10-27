# QDF "cache dump" surface: static safety finding

## Scope and result

This is an offline, hash-bound inspection of `binaries/qdf_tcon.ko` only.  It
does not call the television, load a module, change a debug flag, or send an
ioctl.

The module SHA-256 is
`97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63`.

`QDFTcon_Tcon_Debug` (`.text+0x13c30`, symbol size `0x1f48`) contains code to
print the useful cached values, but the routine's normal unmodified path does
**not** reach that code.  Its `t2ddebug_get_hex` helper is an eight-byte
constant-return stub for `0x99` (exit), so the normal path prints the debug
menu then exits before the jump-table branches containing the cache loads.  A
runtime public transport is also not established; this finding supplies no
command to invoke.

## The requested caches are distinct globals

The module's local symbol table gives these `.bss` offsets:

| Cache | Offset | Meaning for this analysis |
|---|---:|---|
| `m_suspend_status` | `+0x000` | Printed only in dormant selector0x30. |
| `m_tcon_state` | `+0x010` | Printed only in dormant selector0x30. |
| `m_pvcc_status` | `+0x040` | Printed only in dormant selector0x30. |
| `m_command_skip` | `+0x10c` | Printed only in dormant selector0x30. |
| `m_panel_dpms_pvcc_status` | `+0x194` | A different variable; it is not an alias of `m_pvcc_status`. |

The strings at file offsets `0x51e41`, `0x51ec1`, `0x52041`, and `0x52579`
name the first four values in a dormant selector branch.  The final row is
deliberately kept separate: other QDF command paths use the panel-DPMS PVCC
variable as a gate, so substituting it for the ordinary PVCC status would be
incorrect.

## Exact control flow

At function entry (`0x13c30`) the incoming `x0` is overwritten while the
routine builds pointers to its built-in format strings; thus this is not an
ordinary argument-selected getter.  It establishes the BSS base in `x20` at
`0x13cf0..0x13df4`, emits the menu prints, then reaches this command
parser:

```
0x14428  ldr  x0, [sp,#392]       // built-in debug-input format/source
0x1442c  bl   t2ddebug_get_hex
0x14430  mov  x26, x0
0x14434  sub  w0, w0, #1
0x14438  cmp  w0, #0x90
0x1443c  b.hi 0x14454             // default/no-match path
0x14440  ldr  x1, [sp,#408]
0x14444  ldrh w0, [x1,w0,uxtw #1] // jump-table index
0x14448  adr  x1, 0x14454
0x1444c  add  x0, x1,w0,sxth #2
0x14450  br   x0                  // selected debug operation
```

The valid selector range is therefore `0x01..0x91`; `0x99` is separately
recognized as the menu's “exit debug” value.  The selector is obtained through
the vendor `t2ddebug_get_hex` helper, not from a C ABI function argument.  In
this exact module, that helper is `mov x0,#0x99; ret`; it reads neither an
interactive channel nor a shared command buffer.  The `0x99` default path at
`0x14454..0x14498` logs and returns before cache block `0x1454c` (which loads
the named BSS values, including offsets `+0x0`, `+0x10`, `+0x40`, and
`+0x10c`).  The precise public caller remains unrecovered, so no runtime
request follows from this analysis.

The dormant dispatch body nevertheless demonstrably contains
non-observational targets.  Examples from the same function are:

| Site | Target/effect class |
|---|---|
| `0x15250`, `0x1525c`, `0x15268`, `0x15274` | QDF flash upgrade routines |
| `0x1578c` | `QDFTcon_SetOffSensing` |
| `0x15a28` | `m_send_cmd_with_lock.constprop.0` (panel command transport) |
| `0x144b4` | Store to QDF BSS after decimal parsing |

These are positive examples of mutating targets in the dormant dispatch CFG;
they are not effects reached by the unchanged constant-input invocation.
Independent review resolves selector0x30 to0x1454c. Its cache loads at
0x14670/0x146c0/0x147b0/0x14acc read BSS+0/+0x10/+0x40/+0x10c.
The block ends at0x15248 with a branch back to0x13e34. Review found84calls
each to `ft_current_pid`, `ft_current_comm` and `printk`, no other direct-call
target and no store in this block. The block itself is read/log-only; the
unchanged helper cannot select it. This distinction supersedes both the
initial reachable-mutation assessment and the later cache-prefix assessment.

## Registration and public transport boundary

During QDF module initialization, the pointer to `QDFTcon_Tcon_Debug` is
written into its provider operation table at `x19 + 24`:

```
0x3bc..0x3c4    form QDFTcon_Tcon_Debug address in x9
0x430           str x9, [x19,#24]
```

That proves registration as an internal operation, but not a safe user-facing
ABI.  The copied `tztv_frc_tcon.ko` exposes generic ioctl file operations
(`fop_tcon_ioctl` at `0x28e8`, compat version at `0x2758`) which call a handler
through another table (`.bss+0x40`).  The QDF debug pointer is not a direct
relocation target of those functions in the copied objects, and this inspection
does not establish a device node, an ioctl number, payload, or a selector that
would reach only cache reads.

Therefore the narrow conclusion is:

> The vendor cache-print code exists only behind a selector branch.  In the
> exact copied module, the fixed `0x99` helper takes the menu/exit path before
> that branch.  The public transport boundary is also unresolved.  Do not infer
> an ioctl/debug request from this result; no invocation recipe is supplied.

## Reproducibility notes

The evidence can be reproduced offline with:

```sh
python3 tcon-research/qd-cache-dump-surface-reproduce.py
sha256sum binaries/qdf_tcon.ko
readelf -sW binaries/qdf_tcon.ko | rg 'QDFTcon_Tcon_Debug|m_(suspend_status|tcon_state|pvcc_status|command_skip|panel_dpms_pvcc_status)'
aarch64-linux-gnu-objdump -dr --start-address=0x13c30 --stop-address=0x15b78 binaries/qdf_tcon.ko
```

The last command is inspection only.  It must not be treated as authorizing a
runtime `t2ddebug` request or ioctl.
