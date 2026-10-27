# PQE event query: recurring -11 is queue-empty, not a panel-off error

## Actual capture

The physically unobserved ninety-second capacity trace contains 4,186 completed AVOC ioctl calls on captured fd 27, `/dev/sdp_pqe_dp`, request `0xc004510a`, argument pointer `0xf44f94b8`, all from `AVEMonDLSR` TID 1016. Returns alternate exactly between 0 and -11 (2,093 each). The earlier technically accepted five-second smoke has the same argument and alternating pattern (117 each). No transition into a physical black state was annotated in either interval.

The captured FD map is stable at its two endpoints; it does not exclude arbitrary mid-interval close/reuse. The 90-second trace's separate missing final return belongs to fd 33 `/dev/dri/card0`, `DRM_IOCTL_WAIT_VBLANK`, not this PQE query. Its enter is 4.038 ms before the END marker and no return was recorded before tracing stopped. This is not evidence of a hung call.

## Exact kernel implementation

Source is `binaries/sdp_pqe_dp.ko`, 319,518 bytes, SHA-256 `2f23cf9256f2cc2b39a2e0afea7a7fc6007bffd3d5efb536aacd695ee4f3967e`. It is the acquired matching AArch64 module. Addresses below are ELF `.text` offsets, not relocated live addresses. Reconstructible instructions and RELA annotations are saved in [pqe-query-event-disassembly.txt](pqe-query-event-disassembly.txt).

1. `sdp_pqe_dp_compat_ioctl` at 0x1788 handles ARM32 clients. The compare at 0x1820..0x182c selects exactly `0xc004510a`, forwards the argument pointer at 0x1830, and calls `_query_event` at 0x1834 (named relocation). It returns that result without the unconditional zeroing used by some other compat commands. The native ioctl independently selects `0xc008510a` at 0x113c..0x1150.
2. `_query_event` at 0x0fa0 passes a stack output buffer to `_queue_pop` at 0x0fbc, sign-extends its return into x20 at 0x0fc0, and eventually returns x20 at 0x0ffc or 0x105c. Its userspace copy length is 0x34 bytes (52); the query does not interpret an event as a panel failure.
3. `_queue_pop` at 0x1cc8 checks the first index for -1, returning -2 at 0x1d60 for that sentinel. If the index at offset 0 equals the index at offset 4 (0x1ce8..0x1cf0), it returns exactly -11 at 0x1d58. Otherwise it takes the spinlock, copies a 0xa0-byte queue record into its caller's local buffer, advances/wraps the second index at 999, unlocks, and returns 0 at 0x1d48. Thus -11 is structurally the empty-queue outcome; it does not need a guessed vendor error interpretation. The equality check precedes the spinlock, so queue state can change around that check; it is not an atomic long-term state observation.
4. `_dlsr_queue_event` at 0x95b8 is one producer. It obtains PQE data, stores a leading zero word and one data word in a local record, then calls `_queue_push`. Other producers exist; a returned query cannot be assigned to this producer without its output record or another matching trace.

The query's copy-to-user return is not used to replace the saved queue result. Consequently return 0 proves successful dequeuing along this route, not successful delivery of every byte, correct event interpretation, output light, or panel health. On an empty queue the caller must not interpret the copied buffer as a fresh successful event; the captured trace does not include that buffer or the userspace branch.

## Diagnostic consequence

The repeated -11 values now have an exact code-grounded explanation: draining a kernel event queue until it is empty. Their repetition is not an independently detected panel error, and no patch to suppress them is justified. This eliminates a misleading negative-return lead; it does not eliminate PQE algorithms or internal controller behavior as possible contributors to the owner's content-dependent fault. The next useful PQE evidence would be the actual userspace event record and its consumer across a physically timed onset, rather than treating ioctl return codes as panel-state sensors.

No ioctl, register, factory function, live getter, or TV command was invoked for this analysis. No driver was patched.
