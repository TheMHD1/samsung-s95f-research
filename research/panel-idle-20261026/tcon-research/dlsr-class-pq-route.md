# Base RoseM DLSR-class route: conditional PQ-index policy, not a panel-power path

## Result

For the statically selected **base** `RoseMVideoEnhancer` implementation,
type-0's `SetDlsrClass` ultimately invokes the base virtual
`m_SetDlsrClass` slot.  The recovered downstream effect is a finite,
conditional **PQ-index policy** route:

```text
PQE type 0 value
  -> RoseMVideoEnhancer::SetDlsrClass(value)
  -> shared DLSR class at m_pShm + 0xb0
  -> virtual slot +0x428: RoseMVideoEnhancer::m_SetDlsrClass()
       -> PictureVendorAPI::ReadPictureReg(0x007c037c, 1, &local)
       -> gated selection of a shared table word
       -> virtual slot +0x230: RoseMVideoEnhancer::m_SetPQData(index, 0)
       -> existing deferred PQ-data / data-loader route
```

The base vtable bindings are exact.  The code has no direct call in this
bounded function to a named panel-power, TCON-power, panel-mute, or Dimming
Backend duty setter.  This is a finite classification of the recovered
direct calls; it is not an unsupported claim that PQ data can never affect
rendered output through its unresolved data-loader/backend consumers.

No live object, DLSR payload, register result, virtual invocation, transport,
panel response, physical-black transition, or failure was observed here.  No
TV/device/network action occurred.

## Exact offline input and addressing

Input is `binaries/libave.so.0.1`, 6,657,066 bytes, SHA-256
`a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777`.
All addresses in this report are ELF virtual addresses, not live ASLR
addresses.  Thumb symbols carry bit 0; code begins at the preceding even
address.

| Function | Symbol / size | decoded range | byte SHA-256 |
| --- | ---: | --- | --- |
| base `m_SetDlsrClass` | `0x0ad199` / 2100 | `0x0ad198..0x0ad9cc` | `12fce62378deb2b0ba5a878b885ec1c3aa23c96b14647060db419232b269995e` |
| base `m_SetPQData` | `0x0a6a31` / 392 | `0x0a6a30..0x0a6bb8` | `9b8f507b259ff069df1e23608092a94dadcb8fb447424e6c7b9469ba2c356867` |

The active baseline identifies the base RoseM vtable address point.  Statically,
the base vtable symbol is `0x59cbf0`, whose address point is `+8`:

| Slot | relocation address | target |
| ---: | ---: | --- |
| `+0x428` | `0x59d020` | `RoseMVideoEnhancer::m_SetDlsrClass()` (`0x0ad199`) |
| `+0x230` | `0x59ce28` | `RoseMVideoEnhancer::m_SetPQData(int,AVEScalerPath_k)` (`0x0a6a31`) |

This resolves the base table, not a new live-vptr read.  MNT has its own
`m_SetDlsrClass` implementation and is deliberately not substituted here.

## Entry cache and the first direct policy gate

The public base entry `RoseMVideoEnhancer::SetDlsrClass(unsigned)` is
`0x0a3245`, size 128.  Its prior-class static is ELF `0x5a8da8`.  On a value
change it follows GOT `0x5a6a28` to
`RoseMVideoEnhancer::m_pShm` storage `0x5b24e0`, dereferences the state
pointer, writes the requested value at state `+0xb0`, and then invokes vptr
`+0x428`.  The previous-class static is written before that virtual call.

Therefore an identical later type-0 class is suppressed by the outer equality
test even if the inner policy did not select an index or a later PQ path
reported an error.  This is software bookkeeping only; no type-0 payload or
failure has been captured.

## `m_SetDlsrClass`: bounded branch and call structure

The routine first loads `shared+4` at `0x0ad1ba..0x0ad1be` and applies a
large set of integer-family filters.  Those raw values are not named by the
binary evidence, so this audit does not assign display-mode semantics to
them.  All rejected families return normally through `0x0ad1ec..0x0ad202`.

For the surviving families, the explicit hardware-adjacent *read* gate is:

```asm
0x0ad234: r3 = &local_result
0x0ad238: r0 = *(this + 0x114)
0x0ad23c: `mov.w r1,#0x37c`; `movt r1,#0x7c` → r1 = 0x007c037c
0x0ad244: r2 = 1
0x0ad246: PictureVendorAPI::ReadPictureReg(r0, r1, r2, r3)
0x0ad24a: local_result
0x0ad24c: status
0x0ad24e..0x0ad258: require status == 0 and local_result != 1
```

The imported PLT target `0x08fd80` is exactly
`PictureVendorAPI::ReadPictureReg(unsigned,unsigned,unsigned*)`.  The third
argument here is the literal one and the output is local stack memory.  This
does not establish the register's meaning, a successful live read, or a
panel effect.

The main selection routes then use the DLSR class at `shared+0xb0` (loaded at
`0x0ad25c`) together with raw shared words including `+4`, `+0x194`, `+0xe4`,
and `+0xe8`.  Gate failures take logging/normal-return branches; they do not
call the lower virtual policy method.  On a representative selected path,
the code loads a scalar from a state-indexed table at
`0x0ad2f4..0x0ad2fc`, then makes the only non-logging indirect call in this
function:

```asm
0x0ad32e: r3 = this->vptr
0x0ad330: r2 = 0                    ; AVEScalerPath_k argument
0x0ad332: r1 = selected shared scalar
0x0ad334: r0 = this
0x0ad336: r3 = *(r3 + 0x230)
0x0ad33a: call r3
```

Other accepted raw-value families converge on this same call after selecting
different table slots (`0x0ad42c`, `0x0ad618`, `0x0ad780`, and related
bounded branches).  The report intentionally does not turn these raw table
values into brightness, duty, or mode names.

Immediately after the call, `0x0ad33c..0x0ad354` masks state `+0xe4` and
`+0xe8` down to their low nibbles.  The call's return is not inspected before
this continuation, and the public `SetDlsrClass` caller does not branch on
the virtual-call return before returning.  This audit does not assign a
stable success meaning to the large routine's normal return register.
Together with the outer previous-class prewrite, the recovered route has
requested/cache ordering rather than an applied-state acknowledgement.

## PQ boundary and scope

Base vtable slot `+0x230` resolves to `m_SetPQData`, whose finite queue and
writer behavior is documented in
[the existing GSR PQ-edge audit](gsr-npu-pq-edge-review.md).  In brief, it
can defer a selected index into a shared staging array when its readiness word
is zero; when ready it routes indexes through vptr `+0x528` to
`m_WritePQData`, where further gates precede `TDDataLoader::SetData`.
`m_SetPQData` discards lower writer status and returns zero on its normal
paths.  The selected scalar here is consequently a PQ index/policy input,
not a proven brightness, duty, register setting, or panel-applied result.

No bounded direct edge from `m_SetDlsrClass` leads to the separately known
QDDimming Weber/duty path, `DimmingBackendRoseMQD`, `ave_frc_write_i2c`,
the FRC/TCON mute controls, or device/panel-power interfaces.  That narrow
source-derived statement does not rule out effects beyond the recovered
PQ-data/data-loader boundary.

## Reproduction limits

`dlsr-class-pq-reproduce.py` hash-gates the input ELF and asserts symbols,
base-vtable relocations, PLT binding, and direct instruction landmarks for
the cache write, read gate, and `+0x230` virtual call.  Its PASS verifies
those finite static landmarks only.  The large raw-value family decision tree
and its selected table-slot semantics are manually reviewed CFG/dataflow,
not an assertion that any particular live branch ran.
