# Rosem NewHome TCON frame-rate backend

Offline reconstruction from the matching `rosem_frc.ko`, `qdf_tcon.ko`, and `tztv_frc_tcon_api.ko` copies. No TV request, ioctl, I2C transaction, GPIO operation, setting, or process operation was made. Addresses are module section-relative link addresses, not live kernel addresses.

## The Rosem handle is supplied at initialization

`RosemFrc_InitVariable` is the exported Rosem function at `rosem_frc.ko:.text+0x8`. Its first argument is retained verbatim:

```asm
RosemFrc_InitVariable +0x1e8:  bl   memset        ; clear Rosem state blocks
                         +0x1ec:  str  x20,[x19,#0x338]
```

`x20` is the function's incoming `x0`; `x19` is Rosem's BSS base. Thus `tcon_drv_handle` at BSS `+0x338` is not allocated or synthesized by Rosem. It is an externally provided operation-table pointer. The matching central `tztv_frc_tcon_api` module has separate pointers `p_frc_drv_obj` (BSS `+0x618`) and `p_tcon_drv_obj` (BSS `+0x620`). Its exported `map_frc_functions` (`.text+0x7c48`) and `map_tcon_functions` (`+0x7c58`) are each a direct one-pointer store; they establish the two tables used by the FRC/TCON API layer.

The copied API does contain the central handoff. Rosem module initialization builds `rosemfrc_ops` at BSS `+0x380`: the `RosemFrc_InitVariable` relocation pair at init `+0xbc/+0xc4` is placed in its first slot by `str x0,[x20,#0x380]` at `+0x1d0`. It then calls `map_frc_functions(rosemfrc_ops)` at init `+0x3c8`. During the ordinary central initialization, `init_frc_tcon_driver` (`tztv_frc_tcon_api:.text+0x7c78`) uses those tables in this order:

```asm
+0x7cd0: ldr x1,[x20]          ; p_frc_drv_obj
+0x7cdc: ldr x2,[x1]          ; FRC table slot 0 = RosemFrc_InitVariable
+0x7ce0: ldr x0,[x19,#8]      ; p_tcon_drv_obj (BSS +0x620)
+0x7ce4: blr x2               ; RosemFrc_InitVariable(p_tcon_drv_obj)
```

This statically proves that the registered TCON table is passed into Rosem. It does not itself inspect the live pointer value or prove that this initialization completed successfully in a particular incident. The next two facts fix the registered QD backend table and its relevant ABI slot:

1. QDF initialization creates `QDFTcon_ops` at `qdf_tcon.ko` BSS `+0x428` and passes that table to `map_tcon_functions` at init `+0x5c0`.
2. The QDF initialization stores `QDFTcon_SetVRRFrameRate` into `QDFTcon_ops +0x208`: relocations at init `+0x268/+0x270` materialize that function address, followed by `str x18,[x19,#0x208]` at init `+0x2f0` (`x19 = QDFTcon_ops`).

This is the same offset that Rosem calls. Together with the statically reconstructed central handoff, it proves the registered QDF path: `RosemFrc_InitVariable(p_tcon_drv_obj)` receives the QDF operation table and slot `+0x208` resolves to `QDFTcon_SetVRRFrameRate`. It remains not a claim that the pointer was inspected live, that initialization completed during a specific incident, or that the panel accepted a particular request.

## Exact call edge and QD frame-mode sequence

When its selected value differs from cached `m_tcon_frame_rate`, `m_rosem_set_tcon_frame_rate` (`rosem_frc.ko:.text+0x290`) does:

```asm
+0x3e4: ldr x0,[x19,#0x338]    ; supplied TCON operation table
+0x3e8: cbz x0, ...
+0x3ec: ldr x1,[x0,#0x208]    ; operation slot 520 decimal
+0x3f0: cbz x1, ...
+0x3f4: mov w0,w20            ; selected rate, hundredths of Hz
+0x3f8: blr x1
+0x404: str w20,[x19,#0x340]  ; cache happens even after callback error
```

With the QDF table, the target is `QDFTcon_SetVRRFrameRate` (`qdf_tcon.ko:.text+0x112c0`). It first de-duplicates and stores the raw requested rate in QDF BSS `+0x134`, then calls `m_tcon_set_frame_control` (`+0x11058`). That routine maps the raw hundredths-of-Hz value and panel/VRR state to a small **frame mode** (`w21`, observed values 0/1/2), compares that with QDF BSS `+0x13c`, and invokes `m_tcon_set_frame_mode(mode)` only when the mode changed.

The bounded disassembly shows this actual sequence in `m_tcon_set_frame_mode` (`+0x10508`):

```asm
+0x10578: x0 = 0xf30000000164; w1 = 1;  w2 = 1;   bl m_send_cmd_with_lock
+0x10594: w0 = 0x32;                               bl <delay helper>
+0x105d8: x0 = 0xf30000000160;                    bl <read command>
+0x10600: x0 = 0xf30000000160; w1 = mode; w2 = 0; bl m_send_cmd_with_lock ; only if changed
+0x10618: x0 = 0xf30000000160;                    bl <read command>       ; verify
+0x10664: w0 = 0x1f4;                              bl <delay helper> ; only mode-programming branch
+0x1073c: x0 = 0xf30000000164; w1 = 0;  w2 = 1;   bl m_send_cmd_with_lock
```

`m_tcon_set_frame_control` calls `m_tcon_set_vrr_dia_en(BSS+0x130)` and `m_tcon_set_vrr_control(BSS+0x130)` only after that changed-mode sequence. Those helpers send `F3:0x150` and `F3:0x15c`, respectively, with the separate cached VRR-control value (0/1), **not** the raw requested centi-Hz rate. The raw rate therefore selects a mode; it is not the payload of `F3:0x15c`.

Here the vendor semantic can be established: the separately named `QDFTcon_t_Tcon_SetMute` (`+0xce00`) uses the same `F3:0x164` command with payload1 to mute and payload0 to unmute, and maintains `m_mute_state` at QDF BSS `+0x140`. `m_tcon_set_frame_mode` reads that same named state at `+0x1052c`:

- If `m_mute_state != 1`, it sends temporary mute (`F3:0x164=1`), waits 50 ms, reads/writes/verifies `F3:0x160` for the selected mode, and then reaches `+0x1073c` to send unmute (`F3:0x164=0`). The 500 ms delay at `+0x10664` is only on the path where actual mode programming was needed; an already-matching `F3:0x160` read bypasses it.
- If `m_mute_state == 1`, branch `+0x10550 → +0x106b8` sets the local cleanup flag to zero. It performs the frame-mode operation without issuing the temporary mute/unmute pair, preserving the already-muted state.

The temporary pair does not update `m_mute_state`; it is only a local cleanup bracket. Thus the cached state can remain zero even if the physical mute command or its unmute counterpart was not accepted. The normal changed-mode return paths reconverge on the cleanup branch when the local flag is one, including the readback-mismatch retry path. That proves an attempted unmute in normal control flow; it does **not** prove hardware acceptance. This is therefore an actual temporary mute around a frame-mode update, not merely a benign timing request.

Failure handling is significant. `m_tcon_set_frame_control` stores the selected `m_tcon_frame_mode` at BSS `+0x13c` **before** calling `m_tcon_set_frame_mode` and does not propagate that function's result: it continues to the VRR calls and returns zero at `+0x11170`. `QDFTcon_SetVRRFrameRate` likewise stores the raw `m_tcon_frame_freq` at BSS `+0x134` before calling frame control and returns zero unconditionally at `+0x112e0`. Within the helper, the return from the initial temporary-mute send is held in `w21` at `+0x10590`, but a real mode-write return replaces it at `+0x10614`; the final unmute return is only ORed with that later state. Consequently, an initial-mute, mode, or final-unmute failure can be logged/attempted yet be hidden from Rosem, while both caches can suppress an identical later request. This identifies a retry-observability risk; it is not evidence that such a failure occurred in the reported black-screen event.

The code has no direct call to the separately named QDF TCON-power, fault-clear, or PMIC APIs on this edge. The rate argument supplied by Rosem remains hundredths of Hz (for example 12000, 6000, 5000); static analysis cannot establish panel acceptance or physical light output for any request.

## Scope relative to the blackout

`RosemFrc_SetNewhomeMode(1)` can reach this rate path; the NewHome policy report documents its conditions and the `12000` selection branch. A NewHome request can therefore alter frame-mode policy and drive a temporary `F3:0x164` mute/unmute sequence as well as the VRR-control commands, without proving that it caused any observed physical blackout.

Conversely, this edge is a real QD backend write once initialized, so it is not appropriate for speculative recovery tests or to force a fixed rate. The retained incident evidence does not correlate a `new tcon_frame_rate`/callback error with a black transition. A future **passive** matched capture may use those existing logs together with QD command traces to establish or rule out temporal correlation; no command should be issued merely to test this hypothesis.
