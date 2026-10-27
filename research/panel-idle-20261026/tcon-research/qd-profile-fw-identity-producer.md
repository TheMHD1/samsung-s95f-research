# QD profile FW/MD identity producer

## Result

The controller firmware does not derive the four FE identity arrays from the
first embedded image's `241230A` string.  A single Thumb helper at linked/file
address `0x255a8` constructs them from four fixed offsets in one selected
`0x500000`-byte storage bank:

| FE-visible RAM | returned field | storage bytes selected by `0x255a8` |
| ---: | --- | --- |
| `0x200153c4` | first 9-byte FW value (`FE A4`) | bank `+0x4ffe00`, 9 bytes |
| `0x200153cd` | `/F` 9-byte FW value (`FE A3`) | bank `+0x4ffe00`, 9 bytes |
| `0x200153d6` | first 16-byte MD value (`FE 64`) | bank `+0x80100` (9) + `0x60142` (2) + `0x8000a` (5) |
| `0x200153e6` | `/F` 16-byte MD value (`FE 63`) | the same 9 + 2 + 5-byte construction |

For the retained selected profile those source bytes are exactly:

```text
bank+0x4ffe00  FA024C300
bank+0x80100   F77ABUAE2
bank+0x60142   03
bank+0x8000a   12300
```

The resulting values are therefore exactly `FA024C300` and
`F77ABUAE20312300`, matching both sides of the retained runtime QDF line.  This
is an instruction-level explanation of the previously observed three-field
match; it is not merely a literal scan.

There is still an important boundary.  The producer reads the controller's
selected storage bank through an internal block-read path.  It does not read
the host pathname or the retained host copy.  The bytes above prove what the
packaged selected asset *would* produce under this layout; they do not prove
that either controller bank was byte-identical to that host file during the
incident, that this file was installed, or which bank was active then.

This was offline static analysis only.  No TV, root command, controller read,
I2C operation, flash operation, update callback, or network access was used.

## Exact inputs and scope

| artifact | size / SHA-256 |
| --- | --- |
| `overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin` | 5,242,880 bytes; `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0` |
| [`qd-profile-open-register-read-route.md`](qd-profile-open-register-read-route.md) | `c50aee500fd8ff69000e0ae7c59dec72b4097062d350b2b93fdb19e8643ef27c` |
| [`qd-runtime-profile-log-fields.md`](qd-runtime-profile-log-fields.md) | `a339e02422f6be0a6979a7030a91b34d7ba5ee0c7483e81f94cbbddf03f2c323` |
| [`qd-selected-profile-content.md`](qd-selected-profile-content.md) | `e2dcdd78576032d2a250d388cbc55f40950f961238ce426bd5c9b961a4a40beb` |
| [`qd-cad-tcon-ex-proc-provider.md`](qd-cad-tcon-ex-proc-provider.md) | `d7ab562a52f2a33d5c5446a2ceffccc5afe486f4bd7d53fc828060e580e2a575` |

The selected file's first embedded image is linked at address zero, so linked
addresses below equal file offsets.  Thumb-2 decoding was performed locally
with Capstone; the decisive instruction windows were also checked directly
against the pinned bytes.  This review is intentionally bounded to the FE
identity arrays, their common producer, its direct callers, and the selected
asset fields.  It is not a general flash/update analysis.

## Exact producer

The producer spans `0x255a8..0x2564b` (164 bytes, SHA-256
`e17f6b515492a7968d88390c1f089596a8f02eb400850cebdb175c0c698a6825`).
Its arguments are:

```text
r0 = destination for 9-byte FW field
r1 = destination for 16-byte MD field
r2 = storage-bank bias (observed direct callers pass 0 or 0x500000)
```

The dataflow is exact:

1. `0x255b4` obtains a shared `0x200`-byte scratch buffer.
2. `0x255bc..0x255c8` requests `0x200` bytes from
   `bank+0x80000`.  Before the scratch buffer is reused, instructions
   `0x255ce..0x255ea` save five bytes at scratch `+0x0a` to local bytes
   `+0x13..+0x17`, and nine bytes at scratch `+0x100` to local bytes
   `+0x08..+0x10`.
3. `0x255f6..0x25602` requests `0x200` bytes from
   `bank+0x60000`.  Instructions `0x25608..0x25612` save its two bytes at
   scratch `+0x142` to local bytes `+0x11..+0x12`.
4. `0x2561c..0x25628` requests `0x200` bytes from
   `bank+0x4ffe00` (literal `0x004ffe00` at `0x25650`).
5. `0x25632..0x25638` copies the 16 assembled local bytes to the MD
   destination.  `0x2563c..0x25646` copies scratch bytes `0..8` to the FW
   destination as two words and one byte.

Thus the 16-byte MD value is a scatter/gather result, not a stored contiguous
literal.  The full string `F77ABUAE20312300` does not occur anywhere in the
selected 5 MiB file.  The three components occur once each at the exact
offsets above.  Conversely, the `241230A` string at image file `0x40` is not
among the producer's source ranges and has no recovered dataflow into these
arrays.

The three reads call retry wrapper `0x9fc4`, which invokes the internal
`0x9dd4` block-read path up to three times while it returns `1`.  That lower
path ultimately calls code using fixed base `0x58000000`; its adjacent exact
error text is `EMMC Read Fail [USB BUSY]`.  This report does not turn that
string or numeric base into a physical flash-chip identity.  It is enough to
establish that `0x255a8` consumes storage-bank offsets, not its own linked
code bytes or a host file pointer.

There is also a qualification in the error path.  After any nonzero final
read result, `0x255cc`, `0x25606`, or `0x2562c` calls `0xcc50`, but the
producer continues and performs the destination copies.  It does not return
a separately checked validity flag to these direct callers.  Static layout
therefore proves the intended byte provenance, not that every population at
runtime followed three successful reads or contained fresh bytes.

## Initialization and later writers

The bounded direct-call census finds six calls to `0x255a8`:

```text
0x0e910  0x0e91e  (bank 0 branch)
0x0e934  0x0e944  (bank 0x500000 branch)
0x2b8f8  0x2b952  (later bank 0 / bank 0x500000 branches)
```

### Initialization

The initialization caller at `0x3e6c..0x3e99` (46 bytes, SHA-256
`3f36910a23f444c00390431992c0b8df2e17bcbd683918c48bd80c2d78216cca`)
loads a halfword from RAM `0x20000814` at `0x3e84..0x3e88` and passes it to
`0xe888`.

Function `0xe888..0xe94d` (198 bytes, SHA-256
`120596dcbceec992b354856068a5339972f119d97b5eeb3dcbf546f45b227419`)
uses that argument only as a zero/nonzero choice in this path:

* zero calls the producer twice with bank bias `0`;
* nonzero calls it twice with bank bias `0x500000`.

The first call pair writes `0x200153c4` and `0x200153d6`; the second writes
`0x200153cd` and `0x200153e6`.  Both pairs therefore start from the same
chosen bank under nominal successful reads.  The 36-byte array area is based
at literal RAM `0x200153b0` (literal at `0xe950`), with destinations formed by
adds/subtracts in the call setup rather than four address literals.  This is
why a scan for the four exact array addresses finds their FE readers but not
these writers.

The halfword at `0x20000814` is a runtime bank selector in this bounded use.
Its initialization and incident value were not recovered, so this analysis
does not select bank zero or bank `0x500000` for the captured incident.

### Later refresh of the second displayed pair

Function `0x2b88c..0x2b95b` (208 bytes, SHA-256
`eaa41c999f894d66b2d2a4f2ba51535a78cca91ce66764b35a14b1cf17ae0a20`)
contains the other two direct calls.  After a `0x200`-byte lower-storage
operation at address `0xf00000` or `0xf10000`, it calls `0x255a8` with only
the destinations `0x200153cd` and `0x200153e6`, selecting bank zero or
`0x500000` respectively.  This proves that the second FE pair can be
refreshed separately by this path.  It does not prove that the path ran in
the incident, that the lower operation succeeded, or that the `/F` label
means factory, fallback, or flash.

The direct-call census and RAM-base reference review found no other direct
producer for these four ranges.  That is a bounded static result, not a
whole-program proof against arbitrary pointer aliasing, DMA, boot-ROM writes,
or an unobserved second image.

## Byte-for-byte relationship to the selected asset

The relevant selected-file fragments are:

| file range | bytes | fragment SHA-256 |
| --- | --- | --- |
| `0x4ffe00..0x4ffe08` | `FA024C300` | `29222516927db7b8af91b5f5a70fcd6f45a8eb046c598df5a2fce24c2dfd8cc7` |
| `0x80100..0x80108` | `F77ABUAE2` | `c105e86f2c17b2742be392e43449276a58542cee9d4d2e5f4a1a7f60f0ea6c2a` |
| `0x60142..0x60143` | `03` | `0b8efa5a3bf104413a725c6ff0459a6be12b1fd33314cbb138745baf39504ae5` |
| `0x8000a..0x8000e` | `12300` | `093c066bee5f61f40a70d4834c4218b9f0e4205343d5f5833b8b2a9861e08d9c` |
| image `0x40..0x46` | `241230A` | `fb9305b8937e9244f8e8f95128b5089c5aee799a9b1d37ce4dd678f9d907a994` |

This closes the previously unknown `03`: it is copied directly from
profile offset `0x60142`, between the nine-byte VD component and five-byte
data-version component.  No transform, character conversion, or checksum is
applied to these 16 output bytes.

It also separates two superficially similar values.  `241230A` belongs to
the embedded image header and is not consumed here.  The directory-side
`2412300` spans bytes at `0x80008`, but this producer starts its five-byte
copy at `0x8000a`, yielding only `12300` after the two-byte component from
`0x60142` has already been placed ahead of it.

## Evidence boundary

What is now established:

* the exact controller-side writer and byte layout behind all four FE values;
* the runtime FW and MD strings are precisely what this selected asset's
  corresponding bank fields encode;
* the MD value is deliberately assembled from three profile regions; and
* the embedded-image version `241230A` is not the source of either FE string.

What remains unproved:

* which storage bank was selected in the incident;
* whether current controller storage equals the retained host asset, in full
  or even at these four ranges;
* whether the producer's reads succeeded and were fresh when the retained
  log was emitted;
* what `/F` expands to, or whether either displayed pair denotes active,
  fallback, factory, or currently executing firmware; and
* any relationship between these identity strings and RT Protect, physical
  light output, the black-screen symptom, or a safe repair action.

Accordingly, the packaged executable/runtime relationship is substantially
stronger than a coincidental filename match: the package contains exactly the
fields and assembly layout used by the controller's FE identity producer.
It is still a layout-and-content match, not proof of current-flash or running-
image equality.
