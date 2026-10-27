# Fixed main-controller event-log reader

This helper is a mechanical, length-adjusted derivative of the reviewed fixed
read engine. Its only active request is target `0x101`, address `0x20205000`,
length `0xc00` (3072), encoded as
`0101000000502020000c0000`. The native path performs exactly one 12-byte OUT
followed by one 3072-byte IN with the inherited two-second per-transfer
timeout. It accepts no caller-selected address or length and sends no write,
retry, reset, or control request.

The retained evidence snapshot identifies package image-0 logger VA
`0x39394..0x393ec`, an index pointer literal at VA `0x393ec` for CPU
`0x20000e5c`, and a byte-buffer literal at VA `0x393f0` for `0x20205000`.
The logger reduces its index modulo `0xc00` for each byte and contains no
enable-gate test in the retained slice. Because `0x20205000` is above the
exclusive mapper limit `0x20200000`, the recovered mapper returns it unchanged.

The requested response is exactly six 512-byte USB packets when full. Exact
3072-byte completion is required; short or oversized reported counts fail and
are never retried. A successful opaque read does not prove that the region is
directly visible, that it contains valid log data, that the logger ran, that a
fault occurred, or that the packaged image is the running image.

Default mode performs no target I/O. This helper has not been deployed or
executed on the TV.
