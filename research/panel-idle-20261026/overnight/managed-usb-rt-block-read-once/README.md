# Fixed 256-byte RT block read

This separately built derivative of the preserved32-byte reader requests only
target0x101, address0x47012400, length0x100. Header:
`010100000024014700010000`. The request exactly covers the loader-proved
AP_RTP field block and fits one firmware chunk and one USB packet.

All earlier ARM32 ABI, boot/device/full cached descriptor, unbound-interface,
opened-FD validation and cleanup guards remain. Default invocation accesses no
device. Twenty-six injected I/O/stream checks pass. Explicit --execute performs
one request, with no retry/reset/protection or storage payload write. The
controller's ordinary protocol state changes while processing the request.

Actual target execution completed OUT12/IN256, release/close0 and Accepted=true
on the expected boot; stage removal was verified. The read-only independent
reviewer reassembled all uploaded payloads and reconciled all16 root responses.
Raw records and the audit are in `../rt-onset-memory-20261027c`.

Accepted describes exact transfer and cleanup. A256-byte DMA read can overlap
firmware updates and is not guaranteed to be atomic. Physical light output,
causality, image1 aliasing and current whole-program identity are unproved.
