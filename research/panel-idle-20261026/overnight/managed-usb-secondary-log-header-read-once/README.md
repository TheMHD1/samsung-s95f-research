# Fixed secondary event-log header reader

This helper is a mechanical derivative of the reviewed fixed 64-byte
DMA-alias reader. Its only active request is target `0x101`, address
`0x20200000`, length 64, encoded as
`010100000000202040000000`. It accepts no caller-selected address or length
and sends no write, retry, reset, or control request.

The pinned image-1 analysis identifies formatter/sink VA `0x1b8c8` (FILE
`0x5bac8`) and a candidate circular history rooted directly at `0x20200000`:
a DWORD write index at `+0`, an availability flag at `+8`, and a `0x3c00`-byte
ring beginning at `+0xc`. The image-1 mapper range is
`[0x20000000,0x20200000)`, upper bound exclusive, so it returns this boundary
address unchanged rather than adding either recovered DMA-alias offset.

This qualifying read only tests whether the fixed header window is directly
visible through the existing read primitive. A successful transfer does not
prove that the bytes are the log object, that the formatter ran, that the log
is valid, or that the selected packaged image is the running image. Default
mode performs no target I/O. This helper has not been deployed or executed on
the TV.
