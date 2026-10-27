# Mechanical derivation boundary

Parent: `managed-usb-current-callbacks-alias-read-once`

Pinned parent source SHA256:
`795bc39dd478146d6c947ecb4b0d604f18851d2655b9500182af1baf02e6b8c5`

Pinned parent wrapper SHA256:
`b80c5a4553e351b23a842a96c5dc6bdf5275e811543cf19be8f0c53ca6ca43e8`

Native changes are limited to the fixed length, both fixed-header literals,
the dry-run address and label, and a self-test-only assertion for the
3072-byte/six-packet geometry. The wrapper changes are limited to the planned
header and length, manifest schema, and recorded address and length. The
project file is byte-identical. Native discovery, descriptor checks, ABI
checks, claim/detach behavior, one OUT plus one IN sequence, exact-count
checks, timeouts, failure handling, and cleanup are unchanged.

The fixed request is target `0x101`, address `0x20205000`, length 3072. Its
little-endian header is `0101000000502020000c0000`. Default mode is zero-I/O;
host `--execute` must be refused. No target deployment or execution is part of
this derivative build.
