# Fixed current-callback-table DMA-alias reader

This helper is a mechanical derivative of the preserved 64-byte callback
reader. It changes only the fixed address/header and dry-run label, plus the
wrapper request metadata and schema. The USB engine, identity and FD checks,
ARM32 ABI, exact-count requirements, fake-I/O tests, cleanup and failure paths
remain those of the pinned parent.

Its only active request is target `0x101`, address `0x45000580`, length 64,
encoded as `010100008005004540000000`. It accepts no caller-selected address or
length and sends no write, retry, reset or control request.

The address is the DMA-alias candidate for CPU RAM `0x20000580` under the
current mapping evidence. This helper does not establish the core-tag branch,
callback semantics, another RAM alias, or the running image identity. The
default mode performs no target I/O, and this build has not been deployed or
executed on the TV.
