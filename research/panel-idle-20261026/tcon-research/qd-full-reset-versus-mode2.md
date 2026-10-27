# QDF Mode 2 versus stock PM reset routes

## Scope

This is a static, offline comparison of copied kernel modules.  It neither
invoked a TV operation nor read live kernel memory.  It answers a narrower
question than “which route fixes the panel”: whether the recovered Mode-2
route and the stock FRC suspend/resume route reach the same lower reset entry.

| file | SHA-256 |
| --- | --- |
| `binaries/qdf_tcon.ko` | `97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63` |
| `binaries/tztv_frc_tcon.ko` | `aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd` |
| `binaries/tztv_frc_tcon_api.ko` | `3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6` |
| `overnight/serdes-ack-copy-20261026/sdp_ocl_jp.ko` | `e5a064da2cfbd37194f5e97463c3519126a09aedaf4b3c95107b08ab0680aa2c` |

All addresses below are ELF section-relative offsets, not loaded addresses.
The `tztv_frc_tcon` PM offsets are in `.text.unlikely`.

## Result

The recovered code has **two distinct dynamically resolved lower callbacks**:

| caller route | resolver string | destination storage | proven call site | lower body available? |
| --- | --- | --- | --- | --- |
| QDF `m_set_power_control`, including Mode 2 | `sdp_ocl_reset_tcon_power` | exported API pointer `tztv_set_sdp_jp_tcon_power_reset` | QDF on `0x119ec` with `0`; QDF off `0x11b14` with `1` | yes, in copied `sdp_ocl_jp.ko` |
| stock FRC PM suspend/resume | `set_power_mode` | FRC state object `+0x330` | suspend `0x2bb4..0x2bbc`; resume `0x1698..0x16a8` | no provider with that symbol in the retained module corpus |

Thus a Mode-2 off/on cycle is **not statically the same callback sequence** as
the ordinary FRC PM callbacks.  That does not prove either route removes a
controller fault latch, changes a rail, or restores panel light.  In
particular, the callback named `set_power_mode` is an unresolved dynamic edge,
and the recovered mailbox write says nothing by itself about the receiver’s
state-machine semantics.

## Mode 2’s actual recovered reset binding

`QDFTcon_SetQdTconPowerControl` maps operation 2 to
`m_set_power_control(0)` then `m_set_power_control(1)`; the preceding
hash-pinned power-sequence audit establishes that relationship.  On the
platform-type-4 / non-monitor branches, QDF loads the exported function pointer
and calls it with:

* `1` on its off side at `qdf_tcon .text+0x11b04..0x11b18`, after ACDET off;
* `0` on its on side at `0x119dc..0x119f0`, before its 100-ms wait and ACDET
  on.

The API module only exports an eight-byte callback object; its `.data+0x88`
initializer is not a useful provider-body attribution.  The important binding
is in `tztv_frc_tcon:get_fn_ad`:

```
.text+0x57e4  BL  resolve_symbol
.text+0x57f0  x0 = ".rodata.str1.8+0x51b8" = "sdp_ocl_reset_tcon_power"
.text+0x57e8  x2 = resolver return
.text+0x57ec..0x57f8  store x2 into tztv_set_sdp_jp_tcon_power_reset
```

`sdp_ocl_jp.ko` exports exactly that symbol.  Its `.text+0x2b38`
`sdp_ocl_reset_tcon_power(int value)` retains `value` as one stack byte and
calls:

```
SDP_OCL_I2C_MBox_Write(op=1, command=0x3f, length=1,
                       unknown_or_flags=0, payload=&value)
```

The helper begins at `.text+0x7d60`; after its initial gate checks it builds
an I2C message and calls `i2c_transfer` at `0x7e54..0x7e60` (then has further
packet handling).  This proves a lower mailbox-transfer attempt on the path
where the function is bound and its internal gates permit it.  It does **not**
decode mailbox command `0x3f`, prove the live resolver result, prove transfer
success, or establish reset polarity, electrical rail behavior, MCU RAM loss,
or fault-latch clearing.

Consequently, it would be wrong to describe Mode 2 as merely ELVDD/ACDET
toggling: on this static platform-type-4 branch it has a separate reset
mailbox callback.  It would also be wrong to call that command a complete
controller reset without the receiver protocol.

## Ordinary PM path: distinct callback plus additional conditional work

`_tztv_frc_tcon_pm_ops_suspend` and `_tztv_frc_tcon_pm_ops_resume` both first
load the state-object function pointer at `+0x330` and, when non-null, call it
with their incoming PM argument:

```
suspend: .text.unlikely+0x2bac LDR x1,[x19,#816]
         +0x2bb4 CBZ x1, skip; +0x2bb8 MOV w0,w20; +0x2bbc BLR x1
resume:  .text.unlikely+0x1698 LDR x1,[x19,#816]
         +0x16a0 CBZ x1, skip; +0x16a4 MOV w0,w21; +0x16a8 BLR x1
```

`get_fn_ad` resolves `set_power_mode` immediately after it resolves the QDF
callback and stores that independent return at state `+0x330`:

```
.text+0x57f0..0x57f4 x0 = ".rodata.str1.8+0x51d8" = "set_power_mode"
.text+0x57fc          BL resolve_symbol
.text+0x5800          STR x0,[x19,#816]
```

No retained copied ELF exports `set_power_mode`; this is a precise missing
lower-body boundary, not evidence that PM does nothing.

The PM implementation also has work not present in the bounded QDF
`m_set_power_control` body:

* suspend’s non-already-suspended path invokes `tztv_frc_tcon_set_power(0)`
  at `0x2c64..0x2c68`, waits 200 ms, saves GPIO state, and invokes optional
  callbacks at state `+0x310` and `+0x318` with `1`;
* resume conditionally invokes `tztv_frc_tcon_set_power(1)` at
  `0x1748..0x174c` or `0x17bc..0x17c4`, and conditionally invokes
  `_tztv_frc_tcon_nreset_control` at `0x1760..0x176c` or `0x1948..0x1954`;
* a separate suspend branch, gated by fields at `+0x3b8` and `+0x30`, calls
  the directly recovered ACDET/ELVDD helpers with zero at `0x2cf0..0x2d08`.

These are source-derived control-flow facts only.  The values of their guards,
the ordinary-TV path that reaches PM suspend/resume, and the lower
`set_power_mode` / nreset semantics are not established by these copied
objects.  Therefore there is no static basis to rank PM against Mode 2 as a
safer or more complete reset, or to claim either one clears RT Protect.

## Live-binding and access boundary

The retained read-only kernel-access metadata records all capability bits
0–37 in `CapEff` (`0000003fffffffff`) and `modules_disabled=0`, but also shows
that `/sys/module/qdf_tcon/sections/.text`,
`/sys/module/qdf_tcon/sections/.bss`, `/dev/mem`, `/dev/kmem`, and
`/proc/kcore` were absent.  This report did not use any live pointer read or
module load.  It consequently cannot say whether either resolver returned a
non-null provider on the observed boot.

The later reported one-shot Mode-2 observation is deliberately outside this
static report’s proof: a reported status/pin change does not identify which
branch/callback executed or demonstrate a physical-panel outcome.

## Reproduction

`python3 tcon-research/qd-full-reset-versus-mode2-reproduce.py` checks the
four source hashes, resolves the two literal names, verifies the key resolver
stores and calls, and prints bounded supporting disassembly.  The PM guard
interpretation and the API-object limitation remain manual CFG review; the
script is not an emulator or a live binding check.
