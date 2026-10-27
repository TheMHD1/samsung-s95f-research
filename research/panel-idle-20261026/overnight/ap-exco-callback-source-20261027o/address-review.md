# Corrected AP_EXCO callback-source read address review

Recorded 2026-10-27 UTC. This is an independent, offline qualification of
three proposed fixed target-`0x101` read windows. It read retained host files
and the original selected package only. It made no TV, network, root, USB,
controller, device-node, helper, UI, write, reset, or configuration request.
Frozen earlier reports and captures were not modified.

## Decision

The following fixed geometry is positively qualified for a finite read-only
helper:

| purpose | address | length | exact target-`0x101` header |
| --- | ---: | ---: | --- |
| fixed pointer neighborhood | `0x470002c0` | `0x20` | `01010000c002004720000000` |
| corrected callback object base | `0x450158a8` | `0x10` | `01010000a858014510000000` |
| corrected callback object tail | `0x45015c70` | `0x20` | `01010000705c014520000000` |

The pointer binding is little-endian word
`response_pointer[0x0c:0x10] == 0x450158a8`. The tail begins at object offset
`+0x3c8`, so callback source byte `+0x3d8` is at tail response offset
**`0x10` (decimal 16)**. It is not at `0x0c`; that was the offset in the old
tail window for a different AP_EXCO object.

The helper must preserve source bytes `+0`, `+1`, and `+0x3d8` as three
distinct unnamed values. No value `20/0`, packaged default, field name,
physical unit, or equivalence among those offsets is qualified for this
corrected object.

## Pinned selected package and exact original bytes

The reviewed original is:

```text
selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin
size       0x500000
SHA-256    bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0
image-1 FILE = 0x40200 + linked VA
```

The separate registry record at FILE `0x3c5b8..0x3c5d3` is 28 original
bytes, SHA-256
`41dfa8809a435830065f05cbcf22bc20ee9b0f4b4f773e3d49f02f3b04403f66`.
Decoded as seven little-endian words, it is:

```text
0x0003dd84  string -> "MULTI"
0x0003d44b  unnamed
0x00000002  unnamed
0x0003dd8c  string -> "AP_EXCO"
0x200158a8  returned destination field
0x000003ec  object-record extent
0x00000018  unnamed
```

Only the two strings, returned destination, extent, and their use by the
qualified lookup path are used for address geometry. The words at positions
1, 2, and 6 are not assigned a schema or physical meaning. This record does
not supply a package payload whose values may be assumed to populate the
live object.

## Mapper and object extent

The complete selected image-1 mapper at linked VA
`0x1bb74..0x1bbc3` is stored at FILE `0x5bd74..0x5bdc3` and has SHA-256
`94da5bec3c7fd05448a66d3828ec420e5cb08e03cb4474a54d07570732d1fe5c`.
For selector zero, a nonzero CPU address below `0x20020000` in the
`0x20000000` RAM domain is mapped by adding `0x25000000`. The alternate
registry lookup wrapper at VA `0x1bc24` selects root `0x1000c`, takes the
record's destination word, and uses this selector-zero mapping. Therefore:

```text
CPU object base   0x200158a8
object extent     0x000003ec bytes
CPU inclusive     0x200158a8..0x20015c93
mapped bus base   0x450158a8
bus inclusive     0x450158a8..0x45015c93
```

The whole CPU extent is within the mapper's bounded RAM domain. Both proposed
source reads are wholly inside it:

```text
base window  0x450158a8..0x450158b7  object +0x000..+0x00f
tail window  0x45015c70..0x45015c8f  object +0x3c8..+0x3e7
object end   0x45015c93             object +0x3eb
```

The tail leaves the final four object bytes unread but crosses no boundary.
Its `+0x3d8` byte is exactly:

```text
0x450158a8 + 0x3d8 = 0x45015c80
0x45015c80 - 0x45015c70 = 0x10
```

## Pointer slot and callback provenance

The selected image-1 reset scatter positively allocates CPU
`0x20000000..0x200004f7`, which includes slot `0x200002cc`. Startup VA
`0x1bcc4..0x1bd47`, SHA-256
`344accecffd7cff7fb1e7e56ec85778bfa99a9b12646223f34a84e43fb49288b`,
calls the distinct root-`0x1000c` AP_EXCO lookup and stores its mapped result
at that slot.

Getter VA `0x38e8` is the exact 12-byte sequence:

```text
ldr r0, =0x200002cc
ldr r0, [r0]
bx  lr
```

The complete getter neighborhood VA `0x38e8..0x3907` has SHA-256
`6cecc2e176e4eebe73302ec1a1644613b705fe843044ee0aa279f547b5c82c4c`.
Callback VA `0x3934` calls this getter and then performs three separate byte
reads through the returned pointer:

```text
source +0x001 -> r8
source +0x3d8 -> fixed context +0x6c7
source +0x000 -> fixed context +0x6c8
```

The callback prefix VA `0x3934..0x395f` has SHA-256
`3eb32bd2a2930a045ee01a9c605e81d7ef9e2f8ca07615ebae8837efad9f8a72`.
These instructions prove three different source offsets. The destinations or
later consumers do not make `+0`, `+1`, and `+0x3d8` aliases, and they do not
provide field-level semantics.

## Why the pointer window is qualified

The fixed pointer window `0x470002c0/0x20` was already acquired successfully
on the retained boot. Its raw SHA-256 is
`7634f63e1eace3b6da5f287655f1b1ef3ebdb81b22909605a467c2472af43cd3`,
and its eight little-endian words were:

```text
00000001 4500ff14 4501024e 450158a8
450130b6 450130f0 4500f0e0 0001b691
```

Thus the proposed offset `+0x0c` previously returned exactly
`0x450158a8`, while the neighboring words independently match the corrected
selected startup layout. This is an observation from the same retained boot,
not a permanent alias assertion. A future helper must still require the exact
word before interpreting its two source windows as bound to this pointer.
A mismatch remains valid raw transport evidence but rejects the binding; it
must not trigger pointer dereference, address substitution, or retry.

## Correlation from the completed code-view capture

The later fixed code-fingerprint acquisition returned exact selected-package
bytes for all three nonadjacent mapped windows:

```text
0x46001e60/0x200  SHA-256 8be303fddfa4aefd0f2d307f05c7522213f8017ae15b374a4fd7178aeca2bb49
0x460038c0/0x040  SHA-256 0483a632a5e65f8eba8bd623411d6f955705d012c831eac9347e7f9564d944cb
0x4601bb60/0x240  SHA-256 035d13a7c17ac9b303ee5739a421a84d0ceec46167d6efce13f4723fc701d9b8
```

The second window contains the exact getter at VA `0x38e8`; the third
contains the exact mapper, lookup wrappers, root literals, and startup
initializer used in the address proof. This is positive cross-correlation
between retained original bytes and the mapped code view. The callback body
at VA `0x3934` was not inside those fingerprint windows, and no program
counter was sampled. Therefore this evidence strengthens the local
layout/address qualification but does not prove physical core identity,
current execution, or that the callback ran during a panel event.

## Exact future-reader acceptance boundary

A fixed helper may send only the three headers listed above, each followed by
one exact-length IN transfer: exactly six USB bulk transfers total. Every
negative, zero, short, long, or exceptional result must stop before any later
header. Raw bytes from each completed window should be retained immediately.
There must be no write, reset, dynamic-pointer dereference, alternate address,
or retry.

Transport completion and interpretation are separate:

- exact three-window transport, release, close, and ReadyForHeader may be
  accepted even if the pointer word differs;
- the corrected source binding is accepted only if pointer offset `0x0c`
  equals `0x450158a8`;
- source base bytes `+0` and `+1` are response offsets 0 and 1 of the base
  window;
- source byte `+0x3d8` is response offset `0x10` of the tail window; and
- no expected numeric values are imposed on any of those three source bytes.

## Limits

This review qualifies fixed read addresses and offset arithmetic. It does not
prove an atomic three-window tuple, a live field name, a physical unit, an
event-time value, an active fault predicate mode, whole-image identity, or an
executing core/PC. It provides no basis for a write, patch, threshold change,
protection bypass, persistence action, high-bank operation, POFLG operation,
or return-guard change.
