# QDF debug input transport and fixed-exit path

## Result

The exact copied QDF module does not implement an interactive `t2ddebug`
input channel.  Both input helpers are local, eight-byte constant-return
functions:

```
t2ddebug_get_decimal (0x16648): mov x0,#0x99 ; ret
t2ddebug_get_hex     (0x16650): mov x0,#0x99 ; ret
```

The corresponding helpers in the copied `rosem_frc.ko` and
`tztv_frc_tcon_api.ko` are the same constant-return stubs.  No copied module
provides a non-stub definition.  Therefore there is no evidence here for an
interactive prompt, a shared mutable command buffer, or a caller-provided
selector in the QDF debug routine.

## Consequence for `QDFTcon_Tcon_Debug`

After its menu prints, the routine calls `t2ddebug_get_hex` at `0x1442c`.  Its
returned `0x99` fails the `1..0x91` jump-table range test and arrives at the
default block.  That block prints diagnostic context, compares the saved value
with `0x99` at `0x14474`, and returns at `0x1447c..0x14498`.

The named cache loads are instead in a selector branch beginning at `0x1454c`:
for example, loads from QDF BSS offsets `+0x0`/`+0x10`/`+0x40` occur at
`0x14670`/`0x146c0`/`0x147b0`, and `+0x10c` at `0x14acc`.  That branch is not
reached by the constant `0x99` helper.  Thus the fixed exit path is only a
menu/exit path, not a passive cache dump.

The direct external calls before the parser (`0x13c30..0x1442b`) are only:

| Call | Count |
|---|---:|
| `ft_current_pid` | 47 |
| `ft_current_comm` | 47 |
| `printk` | 47 |

This is positive, build-specific evidence that the compiled fixed-exit path
logs the menu/exit context rather than entering any selector branch.  It is not
a claim about a modified module or a different firmware build.  The same
function contains cache, flash, sensing, and panel-command branches beyond the
fixed exit, so it must not be treated as a cache observer.

## Entry/transport boundary remains unresolved

QDF initialization stores `QDFTcon_Tcon_Debug` into a provider operation table
at offset `+24` (`0x3bc..0x3c4`, then `0x430`).  That establishes an internal
registration point only.  It does not establish:

- a public device node;
- an ioctl number or payload ABI;
- a sysfs/debugfs file; or
- a caller that isolates this specific operation.

The copied `tztv_frc_tcon.ko` generic ioctl handlers dispatch through a
different handler-table pointer.  There is no direct relocation from those
handlers to `QDFTcon_Tcon_Debug` in the copied objects.  Static inspection thus
establishes no reachable passive cache-observer implementation path and no
verified runtime observer surface.  No TV command should be
derived from this report.

## Integrity bound

All addresses above refer only to `qdf_tcon.ko` SHA-256
`97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63`.
Use the companion offline verifier to re-check the fixed helper, parser gate,
cache symbols, operation registration, and examples of latent mutating branch
targets.
