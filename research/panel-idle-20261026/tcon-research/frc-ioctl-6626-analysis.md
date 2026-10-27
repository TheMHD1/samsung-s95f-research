# FRC ioctl `0xc0086626`: fixed 8-byte read ABI

## Result

The repeated AVOC calls on fd 21 (`/dev/tztv_frc`) use one specific
**read/get** operation.  It is not a generic setter and this ioctl number is
not multiplexed by the kernel handler:

```text
0xc0086626 = _IOWR(type 0x66, number 0x26, 8)
user buffer = { u32 selector; u32 result; }
```

The `W` part supplies `selector`; the `R` part returns `result` in the same
eight-byte buffer.  The static name of the dispatch target is
`FRC_ReadI2CData`, but that name alone must not be read as proof that every
successful captured syscall reached a device bus or produced a meaningful
register value.  The central dispatcher can return success without a
registered callback, and the statically paired Rosem callback has further
success/no-transfer paths.

This is an offline reconstruction only.  No ioctl, FRC/TCON operation,
setting, or TV/network operation was performed.

## Inputs and address convention

Kernel-module offsets below are ELF section-relative link addresses, not live
kernel addresses.  `libave` values are ELF virtual addresses (with Thumb
function-entry symbols carrying bit 0); they are likewise not live process
addresses.  The exact copied inputs are:

| File | SHA-256 |
| --- | --- |
| `binaries/libave.so.0.1` | `a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777` |
| `binaries/tztv_frc_tcon_api.ko` | `3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6` |
| `binaries/tztv_frc_tcon.ko` | `aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd` |
| `binaries/rosem_frc.ko` | `c646b45d8ab5028defca91b5f8188bf905b8d29f8927fae292be591c94cdbd34` |

The API-module hash is the one recorded by
`overnight/newhome-frc-input-manifest.json`; it is distinct from the
`tztv_frc_tcon.ko` bridge-module hash.

## Exact kernel dispatch

`tztv_frc_tcon_api.ko:fop_frc_ioctl_export` constructs `0xc0086623` at
`.text+0x195c..0x1964`, adds three at `+0x196c`, and branches on equality at
`+0x1970..0x1978`.  That makes `0xc0086626` a distinct handler arm rather
than a number subsequently decoded as a subcommand.

The selected arm is bounded as follows:

```asm
fop_frc_ioctl_export +0x1978: local = sp + 0xd0
                         ...  _copy_from_user(local, user_arg, 8)
                         +0x1994: w0 = *(u32 *)(sp + 0xd0) ; selector
                         +0x1998: x1 = sp + 0xd4           ; result slot
                         +0x199c: bl FRC_ReadI2CData
                         +0x19a0: saved_return = w0
                         ...  validate user range
                         +0x19e0: branch to +0x2cd4 on valid range
                         +0x2cf4: copy length = 8
                         +0x2cfc: __arch_copy_to_user(user_arg, local, 8)
                         +0x2d04: on copy failure return -EFAULT; else return saved_return
```

`+0x1990` and `+0x19e4` return `-EFAULT` on the respective input/output
copy/range failures.  Thus this particular ioctl copies both words in
and both words out on its normal path; there is no write/set callback in that
arm.

`FRC_ReadI2CData` at `.text+0x94b8` makes the lower layer explicit:

```asm
+0x94dc..94e0: load p_frc_drv_obj from API BSS +0x618
+0x94e4..94ec: if table or table[248] is null, go to +0x951c
+0x94f0..94f8: table[248](selector, result_pointer)
+0x951c..9530: return 0                    ; no table/callback
```

Therefore syscall return zero alone does not prove that `result` was written
or that a lower FRC transaction occurred.

## Matching userspace constructor

The exact `libave` copy exports
`ave_frc_read_i2c(unsigned int, unsigned int *)` as
`_Z16ave_frc_read_i2cjPj`, Thumb address `0x243ee9` (instruction address
`0x243ee8`).  Its local construction at `0x243f28..0x243f3a` is:

```asm
request = 0xc0086626
local.word0 = first_argument
local.word1 = 0
frc_ioctl(request, &local)
```

Only for a nonnegative `frc_ioctl` return, `0x243f42..0x243f44` loads the
local second word and stores it through the caller's output pointer.  The
PLT call resolves through jump slot `0x5a60b8` to the exported
`frc_ioctl(unsigned long, void *)` (`_Z9frc_ioctlmPv`, Thumb `0x2ad6e5`).
That wrapper reaches the imported libc `ioctl@GLIBC_2.4` jump slot at
`0x5a510c`.

This proves the matching library ABI initializes the output word to zero and
uses this request for a read result.  The passive trace contains syscall
arguments but no user-buffer bytes, instruction pointer, or userspace stack;
it does not itself prove that each captured caller entered this particular
public libave function, nor expose either word's value.

## Statically paired FRC implementation and its success caveats

`rosem_frc.ko:.init.text+0x38..0x70` materializes
`RosemFrc_ReadI2CData` and stores it in the Rosem FRC operation table at
offset `+248`.  Its module initializer then passes that table to
`map_frc_functions` at `.init.text+0x3c8`.  In the matching API module,
`map_frc_functions` (`.text+0x7c48..0x7c50`) stores the supplied table at
API BSS `+0x618`, precisely the table and slot used by `FRC_ReadI2CData`.
This is static pairing, not a live inspection of the callback pointer or a
claim that the initializer completed during the capture.

If that static pairing is live, `RosemFrc_ReadI2CData`
(`rosem_frc.ko:.text+0x868`) calls `m_rosem_reg_read` (`+0x780`) only unless
two BSS state fields (`+68` or `+108`) equal one.  The latter branch returns
zero without calling the helper.  Within `m_rosem_reg_read`, BSS state
`+20|+412` controls whether it calls the dynamically imported
`tztv_frc_tcon_ext_cmd`:

```asm
m_rosem_reg_read +0x7a8..0x7c8:
    request = { 0, 0, selector, 0 }         ; 16-byte local request
    tztv_frc_tcon_ext_cmd(2, &request, 16)
+0x7d4..0x7dc: on return 0, result = request.word1
```

When that control condition is clear, `+0x7ec..0x7f0` reaches the normal
zero return without the external-command call and without writing the result
pointer.  The `str w0,[x20]` at `+0x7d8` belongs only to the callback-return
path reached through `+0x7d4` (including its error-log continuation), not the
`+0x7f0 → +0x7dc` no-log branch.  Consequently, the libave constructor's
initial zero can survive a successful no-transfer call.  The kernel's exported
`_tztv_frc_tcon_ext_cmd` exists in the separately copied
`tztv_frc_tcon.ko` at `.text+0x2d78`; it can itself return zero when its
resolved downstream callback is absent (`+0x2dfc..+0x2e18`) and dynamically
resolves a callback when needed (`+0x2e30..+0x2ed4`).  This reinforces the
limit: success is not evidence of a bus transfer, a panel state transition,
or a valid returned measurement.

The selected `RosemFrc_ReadI2CData`/`m_rosem_reg_read` branch is a read-result
flow; it does not turn ioctl `0xc0086626` into a setter.  What the unknown
selector values mean, whether the external callback was live, and whether it
caused any I2C traffic are not recoverable from this passive trace.

## What the retained trace establishes

The exact raw source is
`overnight/capacity-20261026t1648.onset/trace`, SHA-256
`403d6951854ae14e312d894534a02b1fe42bb59e576ef58fe9ef8a44994058e7`.
`fds.txt` (SHA-256
`5b7e89cb8c52b3031ca03f499c4489f6ac3faa034ac3402723376b4c6c9ff4ac`)
maps fd 21 to `/dev/tztv_frc` for the retained process descriptor snapshots.

The capture accounting identifies **26,103** calls as its normal 90-second
target-set inventory.  The raw trace itself carries the associated capture
tuple in `meta.txt` (`54765.200 54765.21 54855.37 ...`), but endpoint inclusion
is accounting policy: a simple inclusive comparison against rounded printed
times includes four final frame calls.  This report therefore preserves the
26,103 target-set count rather than falsely presenting that rounded-time test
as an independent derivation.  Every raw paired exit is zero.  The raw trace
uses five stable argument pointers:

| Thread label | Pointer | Calls in the raw retained trace |
| --- | ---: | ---: |
| `AVEMonDIM-1013` | `f4afc1dc` | 5,462 |
| `AVEMonDIM-1013` | `f4afc3d4` | 5,462 |
| `AVEMonDIM-1013` | `f4afc284` | 5,462 |
| `AVEMonVE-1012` | `f4cfd3bc` | 5,462 |
| `metadata self m-1010` | `f52fe4e4` | 4,539 |

The full retained trace has 26,387 fully paired calls from
`54764.256505` through `54855.379688`, including setup/tail records outside
that strict analytical window.  That difference is intentional and must not
be interpreted as missing returns.  The trace format records only syscall
register arguments and returns: it does **not** capture the eight bytes at
any of the five pointers, a callback target, or hardware/I2C completion.

Accordingly, the repeated calls establish heavy polling of a fixed read ABI.
They do not establish a specific selector, result, FRC/TCON health condition,
hardware transaction, cause of the physical-black state, or a safe recovery
operation.
