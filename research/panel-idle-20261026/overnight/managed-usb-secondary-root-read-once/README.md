# Fixed secondary-root and gate reader

This helper is a mechanical derivative of the fixed 64-byte DMA-alias reader.
Its only active request is target `0x101`, address `0x470004c0`, length 64,
encoded as `01010000c004004740000000`. It accepts no caller-selected address
or length and sends no write, retry, reset or control request.

The predicted CPU-side bytes are image 1 reset-row-0 RAM
`0x200004c0..0x200004ff`. That range includes three zero-initialized halfword
gates at offsets `0x4c6`, `0x4c8`, and `0x4ca`, and the root pointer slot at
`0x200004e0`, initialized to `0x20010000`. The candidate DMA address follows
the non-A-core mapping branch recovered separately. A matching byte shape does
not by itself prove the live core-tag branch or the secondary RAM namespace.

The default mode performs no target I/O. All self-tests use injected I/O.
This build has not been deployed or executed on the TV.
