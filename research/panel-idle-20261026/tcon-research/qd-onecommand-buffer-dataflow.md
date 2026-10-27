# One-command send buffer: caller value is copied in, not copied back

This new offline audit closes a deliberately unresolved edge in the frozen [final-duty report](qd-final-duty-branch-analysis.md). Its exact source is `binaries/libave.so.0.1`, SHA256 `a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777`. No TV, device, network, target function, getter, setter, root command or process-memory access occurred in this audit. Addresses are ELF VAs, not reusable runtime addresses.

## Exact send wrapper

`ave_tcon_api_send_onecommand(unsigned long long,unsigned*)` has Thumb symbol `0x2519d9`, size 224. Under the ARM32 calling convention the 64-bit command arrives in `r0/r1` and the caller's scalar pointer in `r2`. Its nonnull route reads the pointed value once at `0x2519f4` (`ldr r2,[r2]`), replacing that pointer register with the scalar. It does not save the original pointer in another register or a local slot.

The wrapper constructs its own 16-byte local envelope at `r7+4`:

| Offset | 32-bit word |
| --- | --- |
| `+0` | operation 18 (`0x12`) |
| `+4` | copied caller scalar |
| `+8` | low 16 bits of the command's high 32-bit half |
| `+12` | command low 32-bit half |

For the final-duty command `0x0000f30000000128`, those command words are `0xf300` and `0x128`. The wrapper passes `0xc010749f` and the local envelope pointer to `tcon_ioctl(unsigned long,void*)` through PLT `0x8df5c` at `0x251a0c`. It retains the ioctl result for return and logging. It does not copy an envelope word back to the original caller buffer on success or failure. A null input pointer takes its log-and-return-zero branch without an ioctl.

The ioctl request's read/write encoding does not override this positive wrapper dataflow: any ordinary copyback into the wrapper's envelope remains in its own local frame. The sender has not supplied the kernel with the original scalar pointer.

## Read wrapper is different

The adjacent `ave_tcon_api_read_onecommand` (`0x251ab9`, size 232) preserves the caller pointer in `r4` at `0x251ac8`, uses operation 19 (`0x13`), and, only after a nonnegative ioctl result, copies envelope word1 to `[r4]` at `0x251af6..0x251af8`. This is a distinct method with an explicit output store; it must not be substituted for the send method.

## Consequence for the final-duty backend

The base RoseMQD backend calls the exact send PLT `0x8db9c` with a local copy of its requested scalar, then reloads that local before `ave_frc_write_i2c` through PLT `0x9023c`. The previous bounded backend-only analysis correctly left possible pointer mutation open. The now-recovered stock send wrapper closes that edge: on defined normal execution, it does not modify that caller local, so the second FRC write receives the original requested scalar.

This conclusion assumes the copied stock implementation, normal ABI/stack behavior, and no concurrent external memory write or corruption. It is not a claim that arbitrary injected code or memory corruption cannot change the local. The live contents of the send PLT/GOT were not read for this audit, and no call or transmitted value was observed during a blackout.

The separate pre-I/O cache/error behavior remains: the backend advances its requested-value cache before transport and has no rollback. Identical later requests can skip both calls. This audit removes one buffer-semantics uncertainty; it does not establish a send, lower hardware acceptance, physical brightness, reset, fault or recovery.

## Reproduction

`PYTHONPATH=/tmp/tcon-capstone python3 tcon-research/qd-onecommand-buffer-reproduce.py` reads only local files and prints exact disassembly plus a result record. It hash-gates the ELF, checks three symbol spans, three PLT names and 23 instruction landmarks, and prints literal pools separately from code. The retained output is `qd-onecommand-buffer-reproduced.disasm`. Pointer lifetime, all-path absence of caller copyback and interprocedural consequence above remain manual CFG/dataflow interpretations anchored by the complete wrapper bodies, not automatic taint proof or live execution evidence.
