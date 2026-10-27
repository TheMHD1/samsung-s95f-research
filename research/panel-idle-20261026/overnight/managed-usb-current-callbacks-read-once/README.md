# Fixed current-callback-table reader

This helper is a mechanical derivative of the frozen 256-byte RT-block
reader. It keeps the same USB identity checks, ARM32 ABI, FD validation,
interface claim, exact-count requirements, failure handling and cleanup.

Its only active request is target `0x101`, address `0x20000580`, length 64,
encoded as header `010100008005002040000000`. The range includes the
loaded scatter RAM callback table at `0x2000058c`. It accepts no caller-supplied
address or length and sends no write, retry, reset or control request.

The default mode performs no target I/O. The self-test uses injected I/O only.
This build has not been deployed or executed on the TV. Returned pointers need
static comparison with the acquired stored image before they can identify the
running controller build.
