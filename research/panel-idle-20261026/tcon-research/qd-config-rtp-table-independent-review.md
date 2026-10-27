# Independent review: QD configuration `AP_RTP` load table

Date: 2026-10-27 UTC  
Scope: independent offline review of the packaged selected-profile bytes  
Target/controller actions: none

## Verdict

The selected 5 MiB package contains a positive, source-bound configuration
route from the directory record named `AP_RTP` to the image-0 fixed RT object
window. This is no longer a name-only association.

The exact route is:

1. a 21-entry firmware table gives `AP_RTP` two physical destinations,
   `0x47012400` for `0x100` bytes and `0x47010000` for `0x2400` bytes;
2. the packaged `AP_RTP` directory record supplies two present source ranges,
   relative to the configuration base, at `0x103800`/`0x100` and
   `0x103a00`/`0x2400`;
3. the loader compares the directory name against the 21-entry table and, on
   successful lower reads, copies the bounded minimum of directory and table
   lengths to those exact destinations; and
4. the reset/startup chain reaches the type-4 configuration enumerator and
   this loader.

When the packaged configuration base is the header at file `0x80000`, those
sources are file `0x183800..0x1838ff` and
`0x183a00..0x185dff`. The resulting physical destinations are contiguous:
`0x47010000..0x470124ff`. Therefore the established RT fields at object
offsets `+0x240a`, `+0x2466`, `+0x2484`, `+0x24aa`, and `+0x24ac` all lie in
the first, 256-byte source payload.

This is a static packaged-image binding. It does **not** prove that the
owner's currently running controller flash equals this package, that the
lower reads succeeded on a particular boot, that later code did not change
the fields, or that any packaged default was present during the black-screen
incident.

The adjacent generic table reader is not established as a safe I2C memory
reader. It is a RAM-copy helper with incomplete internal range checking, and
its three direct call sites do not bind it to the already reviewed F3/FE I2C
dispatchers.

## Input and address model

Input:

- [`overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin`](../overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin)
- size: 5,242,880 bytes
- SHA-256: `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`

For image 0, the vector table begins at container file `0x200`. Accordingly:

```text
linked image-0 VA = container file offset - 0x200
container file offset = linked image-0 VA + 0x200
```

RAM/MMIO constants such as `0x47010000` are not shifted. All code locations
below name the container file offset first and the linked VA where useful.

## Exact table binding

The table occupies file `0x3ccbc..0x3cf07`, exactly 21 entries of `0x1c`
bytes. Its SHA-256 is
`669adda911a2e5bf5b053ab486f11c2611e115b284eeaec79c58e5876fbad287`.

Entry 14 begins at file `0x3ce44`:

| Entry word | Value | Meaning established by loader/reader use |
|---:|---:|---|
| `+0x00` | `0x0003de8c` | linked name pointer; file `0x3e08c` is `AP_RTP\0` |
| `+0x04` | `0x47012400` | first physical destination |
| `+0x08` | `0x00000100` | first physical length |
| `+0x0c` | `0x47010000` | second physical destination |
| `+0x10` | `0x00002400` | second physical length |
| `+0x14` | `0x00210000` | first logical reader prefix |
| `+0x18` | `0x00210400` | second logical reader prefix |

The table pointer is not inferred from the string. Loader file `0x63aa` and
generic reader file `0x659e` independently load linked literal `0x0003cabc`
from file `0x6570` and `0x660c`; corrected by `+0x200`, that is the exact
table file offset `0x3ccbc`. Both functions index it as `entry = table +
index*0x1c`.

## Packaged configuration record

The configuration header is at file `0x80000`. Its first word is count
`0x39`; its word at `+0x28` is `0xcfcfcfcf`. The first `0x200`-byte directory
record is at file `0x80200`. The `AP_RTP` record is file `0x86000`, directory
index 47, and has SHA-256
`b4f7b34aedaadfbfc8d67c3f232dd7c37d1d0a1bcea704483071770f39c1f248`.

The fields actually consumed by the loader are:

| Record offset | Value | Loader use |
|---:|---:|---|
| `+0x00` | `AP_RTP\0` | exact name comparison |
| `+0x28` | `1` | first segment present |
| `+0x2c` | `0x103800` | first source relative to configuration base |
| `+0x6c` | `0` | offset added to first physical destination |
| `+0xac` | `0x100` | first requested length |
| `+0xf0` | `1` | second segment present |
| `+0xf4` | `0x103a00` | second source relative to configuration base |
| `+0x174` | `0x2400` | second requested length |

The record also contains `0x400` at `+0x134`. The loader does **not** read
that field and does not add it to the second physical destination. The
corresponding `0x400` gap belongs to the table's logical reader namespace:
`0x210400 - 0x210000 = 0x400`. Conflating that logical prefix delta with a
physical destination offset would be wrong.

With packaged configuration base file `0x80000`, the exact source payloads
are:

| Source | File range | Bytes | SHA-256 |
|---|---:|---:|---|
| first | `0x183800..0x1838ff` | 256 | `3a16ea440b59a8e778c01ddfc429b110fbdd03e55c953954ce99337ebf5b3937` |
| second | `0x183a00..0x185dff` | 9,216 | `2d07a41ae992770085117e9815300bfd0730745883e60b24aaad5e69dfc087ae` |

There is a deliberate `0x100`-byte source-file gap between the payloads.
There is no physical destination gap: the second payload fills
`0x47010000..0x470123ff`, while the first fills
`0x47012400..0x470124ff`.

## Loader dataflow

The loader is file `0x6390..0x656b` (linked VA
`0x6190..0x636b`), 476 bytes, SHA-256
`7ed64cc1e224e5d68fc66e8c99e40beb6d5d2fc2f8aa99c83853372910e9064c`.

Its relevant behavior is exact:

- `0x63a6..0x63b8`: loop across 21 table entries; compare each table name
  against the inline directory-record name and skip nonmatches.
- The large directory record is passed by value. Relative to its start, the
  loader's stack references map to the record fields listed above. The extra
  argument loaded at file `0x6398` is the configuration-base pointer.
- `0x63ba..0x648c`: if first-present is nonzero, request reads beginning at
  `base + source1`; cap each lower-read request at `0x2000`; and, after a
  zero/success return, copy from staging RAM `0x2021c000` to
  `entry.first_destination + record.first_destination_offset + progress`.
  The copy total is bounded to `min(entry.first_length,
  record.first_length)`.
- `0x6492..0x655c`: the same structure handles segment two, but its physical
  destination is exactly `entry.second_destination + progress`. No record
  destination offset is added. Its total is bounded to
  `min(entry.second_length, record.second_length)`.
- Each lower read is retried at most three times. A load conclusion is
  conditional on those lower reads returning the success value expected by
  the caller.

For this AP_RTP record, table and record lengths agree exactly, the first
destination offset is zero, and both present flags are one. Thus successful
execution copies exactly `0x100` bytes to `0x47012400` and `0x2400` bytes to
`0x47010000`.

## Static RT defaults covered by the route

Because object offsets `0x2400..0x24ff` map to source file
`0x183800..0x1838ff`, the specific bytes already associated with RT state
have the following packaged values:

| Object offset | Source-file offset | Packaged little-endian value |
|---:|---:|---:|
| `+0x240a` | `0x18380a` | byte `0` |
| `+0x2410` | `0x183810` | byte `4` |
| `+0x2466` | `0x183866` | halfword `0` |
| `+0x2484` | `0x183884` | byte `0` |
| `+0x24aa` | `0x1838aa` | byte `100` |
| `+0x24ac` | `0x1838ac` | halfword `0` |
| `+0x24b4` | `0x1838b4` | byte `1` |

These are packaged initializer bytes only. The field names and runtime
roles remain those proven in the dedicated RT-path reports; this review does
not invent new names or claim that zero means “no fault.” Later EEPROM/check
logic is known to write some of these locations.

## Reset/startup reachability

The loader is not merely an uncalled table utility in the packaged code.
The direct startup chain is:

```text
vector reset VA 0x344 (file 0x544)
  -> runtime VA 0x140 / VA 0x2bc
  -> startup VA 0x39998 (call at file 0x4c4)
  -> config wrapper VA 0x7474 (call at file 0x39c5e)
  -> type-4 enumerator VA 0x7544 (call at file 0x7692)
  -> loader VA 0x6190 (call at file 0x7780)
```

The enumerator at file `0x7744..0x77b1` obtains successive `0x1b8`-byte
directory records from `base + 0x200`, tests record field `+0x20` for type
4, places its input base as the loader's extra base argument, and calls the
loader. A sibling enumerator at file `0x77b8..0x7825` independently calls the
same loader for type-4 records at file `0x77f4` and routes type 7 elsewhere.

Relevant slice hashes:

| Slice | File range | SHA-256 |
|---|---:|---|
| reset prefix | `0x544..0x56b` | `ab26f68c73c5451c7a615f64d0e2a4241000bba3c50e6f1f21eabaacebec8162` |
| runtime-to-startup call | `0x4bc..0x4cf` | `049cd9af761e7cb4cc4823c6db0ce526cd826f778a61f417d238918d3b919bec` |
| startup config call | `0x39c4e..0x39c65` | `0adae889aecd4c542aa056ce2fb89bc619f760491a9a87657074ab1a2470d8df` |
| config wrapper | `0x7674..0x7697` | `5ea0c799a9f0af5ef320792e9b07b208d3d14d1ec369129f6b47275e12369341` |
| first enumerator | `0x7744..0x77b1` | `98d89a9a9feb7f32f64a480d3ae7b1f9508d92dcb9d0672b7e609908c3a63be6` |
| second enumerator | `0x77b8..0x7825` | `e4ab91e3bed11d7a1177d35f3bbbf4cb62c36d71eceea23efb74874c7a3a1882` |

This establishes packaged startup reachability to the record enumerator and
loader. It does not supply a trace of the owner's controller executing these
instructions, prove that runtime directory count/global state included the
record on that boot, or prove successful storage reads.

## Generic reader and acquisition boundary

The generic table reader is file `0x657c..0x6609` (linked VA
`0x637c..0x6409`), 142 bytes, SHA-256
`8f332095b3df8762972d501df39f4dbcf4a4038a132aefc43b8ae6817a871dc3`.
It takes a logical address, a 16-bit-word count, and an output pointer, then
uses `memcpy` from the physical destination table.

For AP_RTP it behaves as follows:

- high 16 bits `0x0021` select the AP_RTP entry;
- low 16 bits below `0x100` read from `0x47012400 + low`;
- otherwise it computes
  `0x47010000 + low - (0x210400 - 0x210000)`; and
- copy length is `word_count * 2`.

The helper does not itself reject the logical gap `0x210100..0x2103ff`, does
not check the end of the second region, and does not prove that
`low + word_count*2` stays within either physical range. It is safe only
under caller constraints that are outside this helper.

A bounded direct-BL census found exactly three calls:

- file `0x11258`: variable word count into a local buffer in a command/debug
  formatter whose adjacent strings include `bin,ER` and `%s %08x`;
- file `0x1168c`: one word into a local buffer in a parameter/debug formatter
  whose adjacent strings include `Invaild target string.` and `param,...`;
- file `0x2a4f8`: one word for a type-2 item in an 11-entry internal `TCDATA`
  collection loop.

The call-site slice hashes are respectively
`7a8173e2593c2eb47a94719a3b4d1c9cdeef3e3771e99c35517f706052900ef5`,
`4c61cc096e6fc48288a506167316a76a959f47aa2a848abfb5c7a41381cdc62a`,
and `7eea12741b0f330653f651321bbdd1338c164dc4ab43c99f5cb9fc1654f44014`.
No literal Thumb function pointer to the reader was found in the package.
Computed indirect calls cannot be excluded by that negative census.

Most importantly, the separately decoded I2C/open-register dispatchers do
not call this helper. Their finite F3/FE selector routes remain distinct.
These three callers therefore do not establish an ordinary host-accessible,
side-effect-free route for reading `0x210000` or the RT history fields. This
review neither constructs nor recommends a controller command.

## Supersession and remaining limits

The earlier [`qd-rt-parameter-load-provenance.md`](qd-rt-parameter-load-provenance.md),
SHA-256 `9837f05195f96bf4577ea463fe5c357ae11dfaa49e4a811c388acda033c99e76`,
correctly bounded its then-available search but said no loader bound the
`AP_RTP` record to the fixed RT window. The newly recovered 21-entry table,
metadata offsets, and loader supersede that narrow missing-load conclusion.
Its cautions remain valid: the name alone was insufficient, current-flash
identity was not proved, runtime values were not observed, and no threshold,
fault cause, recovery action, or safe write follows from packaged defaults.

The positive result is limited to the selected package and this code/data
route. It does not prove:

- that the live controller used this exact selected package or load base;
- that the configuration reads succeeded during the relevant boot;
- that EEPROM/check logic left the initializer values unchanged;
- that image 0 and image 1 address spaces are physically identical;
- that the logical table reader is exposed through a normal host protocol;
- that any field value caused or prevented light emission; or
- that modifying any payload or runtime location would be safe.
