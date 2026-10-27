# Mechanical derivation boundary

Parent: `managed-usb-current-callbacks-alias-read-once`

Pinned parent source SHA256:
`795bc39dd478146d6c947ecb4b0d604f18851d2655b9500182af1baf02e6b8c5`

Pinned parent wrapper SHA256:
`b80c5a4553e351b23a842a96c5dc6bdf5275e811543cf19be8f0c53ca6ca43e8`

The native source differs only in both fixed-header literals, the dry-run
address, and the dry-run operation label. The deployment wrapper differs only
in its fixed planned header, manifest schema, and recorded address. The project
file is byte-identical. Native discovery, descriptor checks, ABI checks,
claim/detach behavior, one OUT plus one IN sequence, exact-count checks,
timeouts, failure handling, and cleanup are unchanged.

The fixed request is target `0x101`, address `0x4500f0c0`, length 64. The
little-endian header is `01010000c0f0004540000000`. Host self-test reports 26
passing zero-I/O cases. Default mode is zero-I/O; host `--execute` is refused.

This reader only samples an opaque window. Snapshot offset 32 corresponds to
the candidate common-object guard halfword and offset 48 to its selector
halfword under the separately recovered A-core mapping. Reading those bytes
does not assign semantics, establish a fault, or prove running-image identity.
