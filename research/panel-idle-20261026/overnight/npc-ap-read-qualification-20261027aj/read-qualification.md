# NPC_AP low-field passive-read qualification

Recorded 2026-10-27 UTC. This is an offline, source-only feasibility review.
It made no TV, network, root-agent, USB, device-node, MMIO, controller,
playback, UI, helper, or deployment call. It does not authorize a write,
reset, retry, protection change, bypass, or storage operation.

## Result

The existing fixed target-`0x101` read transport can carry a bounded raw read
of the candidate selector-zero `NPC_AP` view **without a new register or MMIO
primitive**. The address is source-derived rather than inferred from a
`CPU -> 0x4500...` pattern:

```text
named CPU allocation       0x2000d71c..0x2000dc5b  (0x540 bytes)
exact selector-zero rule   address + 0x25000000
candidate mapped extent    0x4500d71c..0x4500dc5b
requested object bytes     +0x16..+0x1b
minimal aligned envelope   0x4500d730 / 8 bytes
target-0x101 header         0101000030d7004508000000
```

That eight-byte response represents object offsets `+0x14..+0x1b`; the three
requested little-endian halfwords begin at response offsets `+2`, `+4`, and
`+6`. The extra halfword at object `+0x14` must be retained but not assigned a
new meaning.

The qualification has one important limit. There is no retained dynamic
`NPC_AP` pointer slot analogous to W's AP_EXCO anchors, and no prior live read
at `0x4500d71c`. Therefore the fixed raw read is feasible and the bus candidate
is positively derived, but an outcome must still be described as a
**conditional selector-zero NPC_AP sample**, not an unconditionally proven
live-object identity. Stored initializer bytes must not be used as an
acceptance gate because ordinary code writes the requested fields.

## Positive source chain

The selected package is
`overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin`,
size `0x500000`, SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
The recovered stored backup is size `0x500000`, SHA-256
`f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562`.

### Named allocation and fixed CPU identity

The ordinary 21-row registry at FILE `0x3ccbc..0x3cf07`, SHA-256
`669adda911a2e5bf5b053ab486f11c2611e115b284eeaec79c58e5876fbad287`,
contains row 2:

```text
name VA   0x3de84 -> "NPC_AP"
CPU base  0x2000d71c
extent    0x540
```

Selected image-0 getter VA `0xef9c` is the exact eight-byte body
`004870471cd70020`, SHA-256
`84f93c6639be7fc7a21229eead9d80b31746059a46741f4973167e2b14ff0b47`.
It returns fixed root `0x2000d71c`. In the bounded nominal image-0
byte-granular census, that exact word occurs only in the getter literal at VA
`0xefa0` and registry word at VA `0x3caf8`. AF already binds the consumer at
VA `0x2f5d8` and both direct writers to this getter. This is positive object
identity at the CPU-address level, not a guessed neighboring allocation.

The requested last byte is CPU `0x2000d737`, only `0x1b` bytes into the
allocation; the whole proposed envelope remains inside it.

### Exact selector-zero mapper

Selected image-1 mapper VA `0x1bb74..0x1bbc3`, SHA-256
`94da5bec3c7fd05448a66d3828ec420e5cb08e03cb4474a54d07570732d1fe5c`,
has the following exact relevant RAM branches:

```text
address == 0                                      -> 0
selector == 0 and 0x20000000 <= address < 0x20020000
                                                   -> address + 0x25000000
selector != 0 and 0x20000000 <= address < 0x20020000
                                                   -> address + 0x27000000
otherwise                                          -> 0
```

`NPC_AP` is wholly inside the selector-zero domain, including its inclusive
last byte:

```text
map(0, 0x2000d71c) = 0x4500d71c
map(0, 0x2000dc5b) = 0x4500dc5b
```

This is the positive alias arithmetic required here. It is not extrapolated
from the separate `0x4700...` local-window mapper or from numeric symmetry.
The mapper's ordinary startup callers supply selector zero. The same startup
lookup family maps first-destination words from the ordinary registry, and W
later captured the resulting mapped pointers for AP_EXCO, AP_TED, and AP.
Thus `0x4500...` is an exercised selector-zero configuration-object domain,
not merely an unused arithmetic branch.

## Existing transport and W comparison

W's pinned helper source
`overnight/ap-exco-input-snapshot-20261027w/source-checkpoint/Program.cs`
has SHA-256
`ef5dd6f33a9daece5fbcaca8decf1328128a0b648268d21a1dc97d28da9136b9`.
Its fixed read-only target-`0x101` headers include reads at `0x4500ff14` and
`0x450158a8`. The accepted retained result has SHA-256
`83cd349d84ef397074f36c5b80e2cc72ad8b00bbeebae5dae978a21f11935171`,
records `transport_accepted=true`, `bus_contents_altered=false`, and terminal
`STAGE_ABSENT`, and retains the 32-byte pointer window with SHA-256
`7634f63e1eace3b6da5f287655f1b1ef3ebdb81b22909605a467c2472af43cd3`.

That pointer window contains:

```text
00000001 4500ff14 4501024e 450158a8
450130b6 450130f0 4500f0e0 0001b691
```

These are positive live examples of the same selector-zero mapped domain.
They do not contain `0x4500d71c`, and W did not read `NPC_AP`. Consequently W
qualifies the transport/domain mechanism, not the requested live values.

The proposed minimum operation is exactly one fixed 12-byte OUT header and
one exact eight-byte IN response. It requires no caller-selected address, no
dynamic pointer dereference, no retry, and no additional bus-access class.
Any implementation would still need the already established fail-closed
transport lifecycle: preserve short/error bytes, send no later header after
an unknown phase, release and close, and retain raw output before semantic
interpretation. This task does not build that implementation.

## Existing object-slot identity

The complete known image-1 startup initializer at VA
`0x1bcc4..0x1bd47`, SHA-256
`344accecffd7cff7fb1e7e56ec85778bfa99a9b12646223f34a84e43fb49288b`,
has exactly seven decoded name/call/store triplets:

| name | destination slot |
| --- | ---: |
| AP_EXCO | `0x200002c4` |
| AP_EXCO | `0x200002c8` |
| AP_EXCO | `0x200002cc` |
| AP_TED | `0x200002d0` |
| AP_TED | `0x200002d4` |
| AP | `0x200002d8` |
| MULTI | `0x200002bc` |

There is no `NPC_AP` entry in that complete seven-store initializer, and the
retained W pointer window has no candidate NPC pointer. This is a bounded
negative only; it does not prove that no indirect or external slot exists
anywhere. A dynamic slot is also not required by the selected image-0
consumer, because its getter returns the fixed CPU root directly.

This is why the proposed read cannot copy W's pointer-gate design literally.
W had several AP_EXCO allocations and used a live slot to choose one. Here the
selected consumer has one fixed root, but no equivalent live pointer is
available to re-bind that root immediately before the read.

## Envelope and stored source proof

The selected and recovered backup both contain the named `NPC_AP` directory
block at FILE `0x84e00..0x84fff`, SHA-256
`04a151171ff9a3774578ff4ad328f2a0016f2ab4c60c9afa7dd30501c307b414`.
Its first payload coordinate selects FILE `0x172600`. Metadata declares type4,
logical base `0x140000`, destination offset0 and copy length `0x53e`, while
the registry allocation extent is `0x540`. The declared `0x53e`-byte payload
is identical between both artifacts, SHA-256
`3e9f4747fa26eeca6818944a6dae2fbba54f6ccc79d1ed6a4dc05434b5ad21b7`.
The separate allocation-sized `0x540`-byte stored slice has SHA-256
`37bb4edfb3d24fc8fe0887f59815cbfb10e3ecf87bfbdf40e481b0852de56518`;
its last two bytes are outside the declared copy. These are stored metadata
associations, not proof of type4 loader execution or live initialization.

For the minimal aligned read, the selected stored bytes are:

```text
object offsets +14..+1b: 64 00 00 04 00 04 00 04
SHA-256: 20cae6279c2a3816896854fb7e76f6d8366bd14520d6c0fd81764369fc2ff2c0
```

The stored requested halfwords are therefore `1024,1024,1024`. AF proves
ordinary writers can change all three, so equality with those bytes is not a
runtime identity condition and a mismatch is not a transport failure.

An optional larger diagnostic envelope is:

```text
address/length  0x4500d71c / 32
header          010100001cd7004520000000
coverage        NPC_AP +0x00..+0x1f
```

It supplies more neighboring raw context for comparison but still does not
create a dynamic pointer binding or prove live identity. The eight-byte
envelope is the minimal four-byte-aligned measurement of the requested
fields.

## Precise remaining qualification

There is no blocker in the existing read transport, allocation extent, or
selector-zero address arithmetic. What is missing is **NPC-specific live
binding**, not another USB primitive:

- no retained ordinary startup slot contains the mapped NPC pointer;
- no accepted prior read covers `0x4500d71c` or its requested fields;
- no pre-event value exists for comparison; and
- the stored default is mutable and cannot substitute for a live anchor.

A stronger W-grade interpretation would require either a positively decoded
ordinary slot/call that contains the current mapped NPC pointer and can be
read first, or an independently accepted live mapped-view identity anchor for
this exact allocation. Until then, a future result may report the fixed
address, raw bytes, same-boot provenance, and conditional selector-zero
lineage; it must not report an exact event tuple, physical panel state, field
unit, or unconditional current-object identity.

`verify-read-qualification.py` reproduces the registry/getter identity,
stored provenance, exact mapper boundaries, startup-slot census, retained W
transport anchors, and both proposed headers using only local files and the
Python standard library.
