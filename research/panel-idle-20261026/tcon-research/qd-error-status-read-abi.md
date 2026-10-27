# QD TCON error-status read: ABI and side-effect boundary

This is an offline reconstruction of one existing stock diagnostic route.  It
does **not** call `/dev/tztv_tcon`, perform an ioctl, access the TV, change a
driver flag, or clear a fault.  The question is whether a future, single stock
error-status query while the panel is physically black could yield useful
evidence, and what that query would actually do.

## Result

A single query is a technically viable diagnostic candidate, but it is not a
passive memory read and it is not self-authenticating evidence.

* Opening `/dev/tztv_tcon` reaches `fop_tcon_open` at
  `tztv_frc_tcon.ko:.text+0x26a8`, whose entire body is `mov w0,#0; ret`.
  The exact 264-byte `tcon_drv_fops` object has relocations only for owner,
  native ioctl, compat ioctl, and open.  Every other slot is zero, so this
  driver supplies no read, write, or release callback.  No TCON-specific
  power, PM, reset, acknowledgement, allocation, or clear occurs on this
  open/close path.  Generic VFS permission, file-reference, and module-owner
  accounting still occur.
* The ioctl path can perform a real controller transaction.  When all QDF
  gates allow it, it sends six bytes `f3 80 00 00 00 08` to adapter5/address
  `0x76`, receives four bytes, reverses them to a host `uint32`, and writes the
  result to request word1.  Thus calling it is not equivalent to reading an
  already-cached host word.
* No explicit host-side power, reset, recovery, fault-clear, monitor-latch
  clear, or QDF state-cache store exists in the bounded getter and read-helper
  bodies.  They lock the QDF mutex, perform/log the query, write caller output,
  and unlock.  This does **not** prove that the controller's proprietary
  `F3:0x08` status query is not read-to-clear or otherwise stateful.  No
  specification or paired repeated-read experiment establishes its controller
  semantics.
* Several paths return success without issuing the transaction or without
  writing word1.  Therefore a request initialized with output zero cannot
  distinguish a fresh zero response from a skipped call.  A future probe must
  initialize word1 to a conspicuous sentinel and retain the ioctl result,
  errno, kernel logs, and preferably the already-developed passive I2C trace.
* Even a changed word1 is only evidence that a kernel callback wrote output.
  QDF's optional debug override can replace the result after the raw-status
  log.  A changed word is not by itself proof of a controller response.

The existing AVE monitor's historical `qd_tcon_off` latch is userspace state.
Calling this public kernel ioctl from a separate process bypasses that
userspace monitor branch, but neither clears nor updates its historical latch,
retry counters, or recovery policy.

## Exact sources

| File | SHA-256 | Architecture / role |
| --- | --- | --- |
| `binaries/libave.so.0.1` | `a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777` | ARM32 vendor wrapper |
| `binaries/tztv_frc_tcon.ko` | `aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd` | AArch64 character device and ioctl bridge |
| `binaries/tztv_frc_tcon_api.ko` | `3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6` | AArch64 ioctl buffer and operation dispatcher |
| `binaries/qdf_tcon.ko` | `97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63` | AArch64 QD getter and I2C transport |

Offsets below are ELF virtual addresses for `libave` and section-relative
offsets for relocatable kernel modules.  They are not live addresses.

## Userspace ABI

The ioctl request is `0xc010749f`.  Standard `_IOC` decoding gives:

| field | value |
| --- | ---: |
| direction | read and write (`3`) |
| encoded size | 16 bytes |
| type | `0x74` |
| number | `0x9f` |

`ave_tcon_get_err_det_status(int *)` is the Thumb function at `0x25d164`
(symbol value `0x25d165`, size164).  It constructs a 16-byte stack request,
stores operation `0x1f` in word0 and zero in word1 at `0x25d188..0x25d18a`,
calls `tcon_ioctl` with `0xc010749f`, then loads request word1 at `0x25d192`
and stores it through the caller's `int *` at `0x25d194`.  Importantly, it
copies word1 before checking whether the ioctl result is negative.  Its two
remaining request words are uninitialized stack data; operation31 never reads
them.

The ABI can be represented for a controlled future probe as four little-endian
32-bit words:

```text
offset  size  direction  meaning for operation 0x1f
0x00    4     input      operation = 31
0x04    4     output     error-status word
0x08    4     opaque     ignored by operation31; initialize zero
0x0c    4     opaque     ignored by operation31; initialize zero
```

The future probe should intentionally depart from AVE's zero initialization
only at word1:

```text
[ 0x0000001f, 0xa55a5aa5, 0x00000000, 0x00000000 ]
```

The sentinel is not sent to the controller.  The QDF callback receives only
the address of word1 and the transport sends its own fixed command.  A
sentinel makes unchanged-output success detectable; it is not a cryptographic
proof that a coincidentally identical controller or debug value is impossible.

The stock wrapper's `tcon_ioctl` at `0x2ad830` caches a descriptor.  When it is
negative, `0x2ad8a0..0x2ad8ae` resolves the literal
`/dev/tztv_tcon`, passes flags2 (`O_RDWR`) to `ave_open`, and stores the result.
It then calls libc `ioctl` at `0x2ad872`.  A standalone one-shot probe can use
one `open(O_RDWR)`, one ioctl, and one close; it need not share or alter AVE's
cached descriptor.

### ARM32 managed guard

The installed CLR previously verified on this TV is ARM32.  That matters:
`unsigned long` in libc's ioctl ABI is 32 bits and the driver selects its
compat handler.  Any future managed program must fail before opening the
device unless all of these hold:

* `IntPtr.Size == 4` and process architecture is ARM;
* little-endian execution;
* a sequential, pack4 request has `Marshal.SizeOf == 16`;
* word1 has `Marshal.OffsetOf == 4`;
* the P/Invoke ioctl request parameter is a 32-bit unsigned value containing
  exactly `0xc010749f`;
* the payload is pinned/by-reference for the entire call.

Record `open` result/errno, ioctl result/errno, all four words before and after,
and close result/errno separately.  libc normally exposes a kernel error as
return `-1` plus errno; the copied word must never be interpreted after a
negative ioctl merely because it looks plausible.  There must be no retry.

## Kernel dispatch

### Character-device bridge

The exact `tcon_drv_fops` object is `.rodata+0x890`, size264.  Its only four
relocations are:

| object offset | callback |
| ---: | --- |
| `+0x00` | `__this_module` |
| `+0x50` | `fop_tcon_ioctl` (`.text+0x28e8`) |
| `+0x58` | `fop_tcon_compat_ioctl` (`.text+0x2758`) |
| `+0x70` | `fop_tcon_open` (`.text+0x26a8`) |

The raw object is otherwise all zero and has no other relocation.  This is the
basis for the bounded no-driver-release/read/write statement; it is not an
assumption from callback names.

Because the future CLR is ARM32, `fop_tcon_compat_ioctl` is the relevant first
handler.  For ordinary ioctls other than its separate `0xc0047417` case, it
loads the dynamically resolved `tztv_tcon_ioctl` pointer at BSS+`0x40` and
calls it with `(request, user_pointer, 1)`.  The native handler uses the same
pointer with third argument0.  Both hold `tcon_ioctl_mutex` around dispatch.

The platform probe calls `get_fn_ad` at `.text.unlikely+0x2f30`.
`get_fn_ad` resolves the exact string `fop_tcon_ioctl_export` at
`.rodata.str1.8+0x4dc8`; `0x5488` stores that result in BSS+`0x40`.  If the
pointer is absent, the outer fop returns zero without touching the request.
This is another success-with-unchanged-output case.

### API module

`fop_tcon_ioctl_export` starts at `.text+0x3048`.  The compat jump-table entry
for ioctl number `0x9f` targets `0x37c8`, which falls back to the common
dispatcher with the original request unchanged.  Thus the ARM32 route still
uses exact `0xc010749f`; there is no alternate compat structure.

The request case at `0x3b78` validates the user range, copies 16 bytes in at
`0x3be4..0x3bec`, calls `TCON_Request` at `0x3bfc`, then copies the same 16-byte
stack object back at `0x678c..0x67ac`.  Its returned status is the signed
`TCON_Request` result; copy failures become `-EFAULT`.

`TCON_Request` uses operation word0.  The jump-table entry for operation31 is
index30 at `.rodata+0x6dc`; its signed halfword `0x0107` gives target
`.text+0xec20`.  That case loads the QDF interface callback at offset
`0x3e8` (1000), passes request+4, and returns the callback result.  A missing
interface or slot returns `-1` and leaves word1 unchanged.  QDF module init
stores `QDFTcon_GetErrDetStatus` into this interface position at
`.init.text+0x2e8`.

## QDF transaction and all relevant gates

`QDFTcon_GetErrDetStatus` is `.text+0xa000`, size316.  With a non-null output
pointer and `tcon_flash_update` (BSS+`0x6c`) not equal to1, it builds exact
packed command `0xf38000000008` at `0xa030..0xa040` and calls the locking
`m_read_cmd` at `0x9b88`.

`m_read_cmd` serializes through `frc_tcon_lock`.  Depending on the configured
transport mode it either:

* invokes raw write then raw read on adapter5/address`0x76`, with six transmit
  and four receive bytes (`0x9c48..0x9c80`); or
* invokes the combined common read callback with the same adapter, address,
  six-byte transmit, and four-byte receive sizes (`0x9cf0..0x9d0c`).

Only a zero lower result reaches `0x9c88..0x9c90`, where the four response
bytes are reversed and stored through the output pointer.  The bounded helper
does not call a power, reset, recovery, clear, sensing, or GPIO routine and
does not write the QDF gate words.

The following outcomes must be distinguished:

| condition in exact path | ioctl-facing result | word1 before debug override | evidence meaning |
| --- | ---: | --- | --- |
| base `tztv_tcon_ioctl` callback absent | `0` | unchanged | no API/QDF call |
| API interface or `+0x3e8` callback absent | negative | unchanged | no QDF call |
| `tcon_flash_update` BSS+`0x6c` equals1 | `0` | unchanged | QDF query deliberately bypassed |
| `m_suspend_status` BSS+`0` equals1 | `0` | unchanged | transport skipped |
| `m_command_skip` BSS+`0x10c` equals1 | `0` | unchanged | transport skipped; only exact command `...0c` is exempt, not this `...08` query |
| `m_tcon_state` BSS+`0x10` is not1 | `-1` | unchanged | transport skipped |
| transport callback absent or lower transfer fails | nonzero (normally negative) | unchanged | no valid response copied |
| transport succeeds | `0` | four-byte response | kernel output written |

After all of those, `QDFTcon_GetErrDetStatus` logs the current word at
`0xa05c..0xa074`.  If `m_err_debug` at BSS+`0x28` equals1, it then overwrites
word1 from `m_err_det_status_debug_status` at BSS+`0x120` and emits a second
debug log (`0xa0d0..0xa0fc`).  The raw-before-debug ordering is useful, but
absence of a retained log is not proof that debug was disabled.

This command is specifically `F3 80 ... 08`.  It must not be conflated with
the independently corrected panel-mute read constant `F3 00 ... 0164` or with
a mute decoder's semantic-shape rules.

## Evidence classification for one possible future call

The minimum honest classification is:

1. `ioctl_ret < 0`: failed.  Preserve errno and the unchanged/changed payload,
   but do not decode word1 as a fresh status.
2. `ioctl_ret == 0` and word1 is still the sentinel: no fresh kernel output
   was demonstrated.  This includes multiple accepted-but-skipped paths.
3. `ioctl_ret == 0` and word1 changed: a kernel callback wrote output.  It may
   be a successful controller response or the QDF debug override.  Correlate
   the two exact QDF log forms and the passive I2C trace before calling it a
   controller response.
4. A trace-complete `F3 80 00 00 00 08` transaction, lower return0, raw QDF
   log, no debug log, and changed word together support a fresh controller
   status sample.  They still do not show visible OLED emission, panel health,
   or the initiating cause of the blackout.

If a fresh raw word has bits0..7, the matching existing build labels are EL
OCP, EL OCP2, BLACK OCP, FFC Connection OCP, RT Protect, DSI Protection,
AC_DET pin low, and PMIC fault.  A nonzero sample is telemetry at that instant;
it is not the separate one-bit ERR_DET GPIO and does not itself trigger the
userspace monitor's recovered reset logic.  A fresh zero sample does not rule
out a physical fault, a deasserted/intermittent fault, or a problem outside
this eight-bit status family.

Because controller read-to-clear behavior remains unresolved, static analysis
does not authorize silently running even this one query.  If authorized later,
it should be one ordinary call, no retries, no state setters, no protection
changes, with owner-visible state and passive evidence preserved before and
after.

## Reproduction

`qd-error-status-read-abi-reproduce.py` hash-checks all four copied ELF files,
asserts the ioctl shape, ARM wrapper instructions/PLT identities/device path,
the complete file-operations relocation set, compat dispatch, 16-byte copies,
operation31 jump target, QDF table registration, fixed command, and transport
sizes.  It prints bounded local disassembly only.  It has no device, target,
root, network, `/proc`, ioctl, or mutation path.

