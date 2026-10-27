# Active QDDimming-base duty path — bounded static audit

The runtime path is now resolved as **QDDimming → DimmingBackendRoseMQD**.
The final combined read directly verifies its relocated output slot and finds
cache207 equal to working duty207. The exact retry weakness is a cache write
before I/O with no rollback; no failed transaction or physical blackout was
observed in that read. See [the combined runtime report](../overnight/runtime-control-state.md).

Offline input: `binaries/libave.so.0.1`, SHA-256 `a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777`. The live vptr reported by root is `AVE bias + 0x59f2e8`, the QDDimming address point, not QDDimmingMNT `+0x5a094c`. This audit therefore traces base QDDimming only. No live action occurred.

The Itanium vtable address point is symbol+8. Base QDDimming slot `+0xc4` is relocation address `0x59f3ac` and resolves to `QDDimming::t_vSyncCallBack()` (`0x17b35c`). MNT's corresponding `0x5a0a10` resolves to `QDDimmingMNT::t_vSyncCallBack()` (`0x19b1c8`). The live sample selects the base routine.

## Vsync to final-duty path

Base vsync checks inner `+0x39`, `+0x5c`, and `+0x1b4`, then dispatches on control word `+0x18c`. Its explicit final-duty edge is:

```
17b55e  lsls r1, r3, #0x14
17b560  bpl.w 17b3e4
17b564  mov r0, r4
17b566  blx #0x8e304  ; QDDimming::m_SetFinalDuty2D
```

Thus it is mode/bit-gated per-vsync work, not a timer or proof it ran live.

`QDDimming::m_SetFinalDuty2D()` code `0x174260` calls the base auto routine:

```
1742fa  str.w r2, [r3, #0xa8]
1742fe  blx #0x8f75c  ; QDDimming::m_AutoPowerOff
```

`m_AutoPowerOff` code `0x1740f0` reads raw AutoDim at inner `+0x2a8`, reads/writes inner `+0xa8`, and reads inner `+0xfc`. At `0x174118`, `cmp r6,#1` selects the exact-1 request path; its local counter is clamped at `0x12c` and the calculated value is stored at `+0xa8` (`0x17415c`). This is a call count, not a duration.

Known dataflow labels only: `+0x2a8` raw AutoDim request; `+0xa8` ramp/working-duty field; `+0xfc` source/target-side input; `+0xac` final-duty working field written by `m_SetFinalDuty2D`; `+0x18c` vsync control word. They are not calibrated physical units, PWM, voltage, luminance, or proof of current hardware state.

## Backend boundary

After auto processing, base final-duty builds argument blocks, but the two interface calls are gated. `this+0x10` is the constructor's passed backend pointer and is explicitly nullable: `0x17433c` loads it, `0x174340` `cbz` skips the vptr `+0xd8` call at `0x174382..0x174388` when it is null. The second call occurs only if inner `+0x0` equals `1` (`0x17438e..0x174392`): it loads `this+0x0c` and calls vptr `+0x48` at `0x1743a0..0x1743b2`.

The constructor obtains `this+0x0c` from `DimmingVendor::GetInstance()` (PLT `0x8e3dc`). Its intended singleton vptr is `0x59fa7c`; slot `+0x48`, relocation `0x59fac4`, resolves to inherited `DimmingVendorInterface::t_SetFinalDuty2D_NonFRC(...)` at `0x188501`, a no-op stub. This static constructor evidence alone does not identify the nullable `this+0x10` runtime backend vptr; the later runtime reads below resolve it separately.

The static base route is `vsync → m_SetFinalDuty2D → m_AutoPowerOff`, followed only by conditional interface calls. The base routine alone does not identify the concrete output setter; that requires the runtime backend and its own body below. The MNT body must not be substituted for it. Curated excerpts above are bounded; the companion reproducer makes exact operand/relocation assertions.

## Runtime-resolved non-MNT backend and transport boundary

The read-only paired runtime captures `overnight/runtime-dimming-backend-pointers-20261026T114540Z.json` (SHA-256 `f6802e9bf922c695d7b396638291e2088d8c02883c2c4c1c50e52922fa75cbea`) and `runtime-dimming-backend-vptrs-20261026T114613Z.json` (SHA-256 `6c01c3efbe773430b3c367820c9080a3a4e96c4abfda698d3ab8dfc548c4c931`) are non-atomic before/after-equal samples against the matching libave hash. They resolve the formerly unknown nullable backend pointer `this+0x10` to `0xf7203630`, vptr `0xf711852c = AVE bias + 0x5a152c`: `DimmingBackendRoseMQD` vtable address point, not MQDMNT. The vendor pointer remains `0xf7135618`, vptr `bias+0x59fa7c`.

For RoseMQD, vtable slot `+0xd8` is relocation `0x5a1604`, resolving to `DimmingBackendRoseMQD::t_Set2DFinalDuty(BackendGd2DFinalDuty_t*)`, code `0x1c6274`. Its real caller parameter is the block constructed by base final-duty: the backend routine receives it in `r1` and takes the candidate scalar from `[r1,#8]` at `0x1c6288`.

The cache is not an unnamed proximity inference. Literal `0x1c6354 = 0x3e56be` plus Thumb PC base `0x1c628a` yields state base `0x5ab948`; the cached scalar is `state+0x10 = 0x5ab958` (`siDimLvl`). `0x1c629a..0x1c62a0` compares it with candidate `r8`; on a mismatch `0x1c62ac` stores `r8` to that cache **before** either I/O call. There is no rollback in this bounded function. The API result and FRC result are ORed at `0x1c62c8`, but its vsync caller branches on without consuming `r0` (`0x17b56a`), so a returned status is not a retry, success, or applied-state proof.

For a mismatch, `0x1c62a4..0x1c62b4` passes command `0xf300`, subcommand `0x128`, and a mutable local buffer to `ave_tcon_api_send_onecommand`. The second call at `0x1c62c4`, `ave_frc_write_i2c`, loads its value from that local buffer after the first API call; it is therefore not necessarily the original candidate scalar. This proves a conditional software command/transport request route, not a physical result.

At the captured instant, inner `+0x0=0x59`, `+0xa8=+0xac=0xcf`, `+0xfc=0x11`, `+0x18c=0xffffffff`, and `+0x2a8=0`. These are a single non-atomic cached-memory observation: they neither prove vsync execution, cache inequality, transport emission, command acceptance, nor physical panel state. The backend-vptr capture reused matching maps/hash from an earlier fresh capture roughly 32 seconds before; it was stable before/after its own reads but is not an independently fresh map assertion for this later snapshot.

The subsequent [combined108-byte capture](../overnight/runtime-qd-duty-cache-20261026T115305Z.json)
freshly matches source-file hash and maps on both sides, reads the actual
relocated `vptr+0xd8` target, and pairs identity/cache/duty reads. It observes
`siDimLvl=207`, inner`+0xa8=+0xac=207`, and the same RoseMQD slot target.
The cached-equal branch would skip both transports for an unchanged candidate.
This is steady-state suppression, not an observed failed retry. It does not
prove callback invocation, transport failure, physical picture state or recovery.
