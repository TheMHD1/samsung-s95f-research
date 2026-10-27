# Fixed secondary-controller event-log reader

This is an offline-built, read-only, fixed-request derivative of the reviewed
main-event-log helper. Its only active request is target `0x101`, address
`0x20200000`, length `0x3c0c` (15372), encoded as
`01010000000020200c3c0000`. The native path performs exactly one 12-byte OUT
followed by one 15372-byte IN with the inherited two-second per-transfer
timeout. It accepts no caller-selected address or length and sends no write,
retry, reset, or control request.

The response extent is the 12-byte index/metadata header followed by the
`0x3c00`-byte ring, or `30 * 512 + 12` bytes in total. Exact completion is
required; reported counts of 15371 or 15373 fail and are never retried.

The local evidence copies pin the corrected image-1 static analysis: the
DWORD index is at `0x20200000`, the flag is at `+8`, and the circular byte
ring occupies `0x2020000c..0x20203c0b`. A prior accepted 64-byte read from
`0x20200000` proves direct visibility for that sample only. It does not prove
freshness, stability of a longer read, running-image identity, record
boundaries, formatter activity, log validity, or fault causality.

Default mode performs no target I/O. This helper has not been deployed or
executed on the TV.
