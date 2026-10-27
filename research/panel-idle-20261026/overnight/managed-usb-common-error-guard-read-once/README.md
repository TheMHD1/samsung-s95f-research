# Fixed common error-guard and selector reader

This helper is an independent mechanical derivative of the fixed 64-byte
DMA-alias reader. Its only active request is target `0x101`, address
`0x4500f0c0`, length 64, encoded as `01010000c0f0004540000000`.
It accepts no caller-selected address or length and sends no write, retry,
reset or control request.

Under the separately recovered tag-0xA mapping, the candidate CPU range is
`0x2000f0c0..0x2000f0ff`. The common-object root begins at CPU
`0x2000f0e0`, 32 bytes into this snapshot. Its return-guard halfword is at
snapshot offset 32, and the selector halfword at common-object `+0x10` is at
snapshot offset 48. The fixed read samples these values; it does not change or
bypass them.

Packaged reset analysis predicts zeros throughout this window, while later
runtime/configuration writers may change it. Transport acceptance cannot by
itself establish emergency-loop entry, panel causality, whole-image identity,
or the live core-tag branch. Default mode performs no target I/O, and this
build has not been deployed or executed on the TV.
