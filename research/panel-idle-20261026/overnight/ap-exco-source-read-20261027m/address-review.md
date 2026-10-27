# AP_EXCO fixed-source read address review

Recorded 2026-10-27 UTC. This is an independent, offline review of three
proposed target-`0x101` read windows. It read only retained host files. It made
no TV, root, USB, controller, network, UI, firmware, configuration, or storage
request and changed no prior evidence.

## Decision

The two fixed `0x4500....` source windows are positively qualified from the
selected package's AP_EXCO table row, selected type-4 metadata, copy geometry,
and selector-zero mapper:

- **qualify** `0x4500ff14`, length `0x10`;
- **qualify** `0x450102e0`, length `0x20`.

The `0x470002c0`, length `0x20` window is qualified for a **raw conditional
pointer observation**, rather than as an unconditional CPU alias. Selected
image 1 positively allocates CPU slot `0x200002cc`; its RAM mapper maps that
slot to `0x470002cc` on the non-`0x0a` core-tag branch; and retained reads from
the same boot positively correlate two other `0x4700....` windows with the
same image-1 RAM layout. The live core tag itself was not captured. Therefore:

- the fixed read is not blocked;
- returned bytes remain raw unless the little-endian word at returned offset
  `0x0c` is exactly `0x4500ff14`;
- a zero, different word, short result, or transport failure rejects the
  pointer binding and must not be explained as a different AP_EXCO address;
- even an exact match supports this pointer instance and the proposed source
  correlation, not a universal identity between all `0x4700....` bus space
  and CPU `0x2000....` RAM.

This is the narrow positive proof required for the pointer read. It combines
an exact packaged allocation and mapper with multi-field, same-boot bus
anchors; it does not promote a conditional mapper branch into an
architecture-wide fact.

## Pinned package and original-byte checks

The reviewed package is:

```text
selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin
size      0x500000
SHA-256   bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0
```

All values below were re-read from that original file, rather than accepted
from an earlier report. Image-1 linked VA maps to package FILE
`0x40200 + VA`.

### Pointer-slot scatter coverage

The exact image-1 scatter table at FILE `0x5d8a4..0x5d933` has SHA-256
`73eaacb3784da627c734f46dceeca569c403209c3e3e969d813f2bf13d09caef`.
Its first record is:

```text
source linked VA  0x0001d860
destination CPU   0x20000000
output length      0x000004f8
operation          0x0000017c
```

Thus CPU word `0x200002cc..0x200002cf` lies wholly inside the positively
allocated/decompressed range `0x20000000..0x200004f7`. Independently decoding
the source stream at FILE `0x5da60` produced exactly `0x4f8` bytes with
SHA-256
`76bebfc83f8e286d8ae152749a1aa376d0bc8d3f415f2433d9ca6944506e7ef8`;
its reset word at offset `0x2cc` is `00000000`. This proves allocation and the
reset value. It does not prove the slot's later live value.

Selected image-1 startup obtains the named AP_EXCO first destination and
stores the mapped result into this slot:

```text
1bcde  ADR   r1, "AP_EXCO"
1bce0  MOVS  r0, #0
1bce2  BL    1bc24
1bce6  LDR   r1, =0x200002cc
1bce8  STR   r0, [r1]
```

Getter VA `0x38e8` loads the same slot and returns its word. These bytes prove
the ordinary packaged writer/getter chain, but not that startup completed on
the currently running secondary image or that no later writer/corruption
changed the word.

### AP_EXCO table row and allocations

Configuration table row 10 at FILE `0x3cdd4` is seven little-endian words:

```text
name pointer        0x0003dd8c  -> FILE 0x3df8c, "AP_EXCO"
first destination   0x2000ff14
first length        0x0000033a
second destination  0x2001024e
second length       0x00001200
first logical base  0x001b0000
second logical base 0x001b0400
```

The exact row SHA-256 is
`e3d967a7b74ce674f6c10d2b5c1f945913b1381baa5ac50ad5aec6e4c370713d`.
The allocations are contiguous because:

```text
0x2000ff14 + 0x033a = 0x2001024e
```

The selected 512-byte metadata row at FILE `0x85e00` is named `AP_EXCO`, is
type 4, and has SHA-256
`dad4caf149769f0b363a11231267d73752802a3bd7484bd720562bbaa7be1cd8`.
Its two enabled copy records give:

| record | package source | CPU destination | length | payload SHA-256 |
| --- | ---: | ---: | ---: | --- |
| first | `0x182200` | `0x2000ff14` | `0x033a` | `c50e438b4882c04e62542fa718cda662b56c3ea0930e20d54944a949e2e3afbf` |
| second | `0x182600` | `0x2001024e` | `0x1200` | `5000ce2a135b4b463505a32cf5b525916605b32c21a20de4bd91607d4b839761` |

Consequently the selected-package successful-copy layout is:

```text
FILE 0x182200..0x182539 -> CPU 0x2000ff14..0x2001024d
FILE 0x182600..0x1837ff -> CPU 0x2001024e..0x2001144d
```

This establishes source/allocation arithmetic. It does not prove that this
payload was the one successfully copied into live RAM on this boot.

## Mapper qualification for the two address spaces

There are two distinct mappings; conflating them would overstate the result.

### CPU slot candidate: `0x200002cc` to `0x470002cc`

The exact image-1 RAM mapper at VA `0x3084` (FILE
`0x43284..0x432a7`) has SHA-256
`64ef2153ee7053a16b6741c455535147ddb1d247aaf216482b5e46fba7c0f471`.
For CPU inputs in `[0x20000000,0x20200000)`, it reads the word at
`0xe00fdfdc` and applies:

```text
core tag == 0x0a  -> address + 0x25000000
core tag != 0x0a  -> address + 0x27000000
```

Thus the proposed pointer location is exactly the non-`0x0a` result:

```text
0x200002cc + 0x27000000 = 0x470002cc
```

The live core-tag word was not retained, so the branch is not proved by a tag
sample. There is, however, positive same-boot corroboration for this local bus
mapping:

- an older accepted 64-byte read at `0x470004c0` returned the expected fixed
  root pointer `0x20010000` at bus `0x470004e0`; its raw SHA-256 is
  `2543a59edfbd16832cfddd460c3dae28017309669d35eabc6eedcdfd95b7675d`;
- a later accepted 68-byte read at `0x470004a0` again returned
  `0x20010000` at `0x470004e0`; its raw SHA-256 is
  `c58a20a4147d7b09bfe560456cb65bfce1462fdc5aefcfc50b80e3f5927765c9`;
- that capture's separate 16-byte `0x47000bc0` window matched three
  independent image-1 startup halfwords and runtime-local fields; its raw
  SHA-256 is
  `2efca8a0f734277a3df0351751a2ec11d33d20423983381f5068299289fc308a`.

The retained records bind these acquisitions to boot ID
`00000000-0000-4000-8000-000000000000`. These are strong local anchors for
reading the fixed slot through `0x470002cc`, while still falling short of an
unconditional whole-bank alias proof.

### AP_EXCO source: CPU destinations to `0x4500....`

The AP_EXCO lookup uses mapper VA `0x1bb74` with selector zero. For a nonzero
input in `[0x20000000,0x20020000)`, this exact branch adds
`0x25000000`; the selector-nonzero branch would add `0x27000000` instead.
Lookup VA `0x1bc24` loads row word `+4`, the first destination
`0x2000ff14`, and calls that mapper with the startup-supplied selector zero.
Therefore the ordinary stored pointer is code-defined as:

```text
0x2000ff14 + 0x25000000 = 0x4500ff14
```

Both AP_EXCO CPU allocations fall inside the selector-zero mapper's bounded
range. Their mapped extents are exactly:

```text
first   0x4500ff14..0x4501024d
second  0x4501024e..0x4501144d
```

Unlike the CPU-slot `0x4700....` candidate, this `0x4500....` result does not
depend on the unobserved word at `0xe00fdfdc`; it is selected by the explicit
zero passed into the configuration lookup.

## Window arithmetic and static fingerprints

### `0x470002c0`, length `0x20`

The inclusive bus span is `0x470002c0..0x470002df`. Candidate CPU slot
`0x200002cc` appears at returned offset `0x0c`; four bytes remain entirely
inside the 32-byte response. The binding check is:

```text
LE32(response[0x0c:0x10]) == 0x4500ff14
```

There is no useful package-default fingerprint for the full live bus window.
The scatter reset value at that word is zero, while normal startup is expected
to replace it. Preserve and hash all 32 raw bytes regardless of whether the
binding check passes.

### `0x4500ff14`, length `0x10`

The inclusive span `0x4500ff14..0x4500ff23` is AP_EXCO object offsets
`+0x00..+0x0f`, wholly inside the first allocation. It corresponds to selected
package FILE `0x182200..0x18220f`. The selected-package bytes are:

```text
00000000000000000100000000000000
SHA-256 9d34149fbd1fe777eb238799054c8cbfbce372255f219f8740838def9bfd02db
```

These are comparison data only; a mismatch is a live observation, not a
license to force the bytes to the packaged defaults.

### `0x450102e0`, length `0x20`

This starts at AP_EXCO object offset `+0x3cc`, which is second-allocation
offset `0x3cc - 0x33a = 0x92`. Its inclusive span
`0x450102e0..0x450102ff` is wholly inside the second allocation and maps to
selected package FILE `0x182692..0x1826b1`.

The unnamed AP_EXCO byte at object `+0x3d8` is at bus `0x450102ec`, returned
offset `0x0c`. Selected package FILE `0x18269e` contains `0x14` there. The
complete selected-package comparison window is:

```text
1300130013001300140014001400140015001500150016001600160016001700
SHA-256 f4eec86c76db591f12c003fc318c76418e9455c10f10ad2c40acf0b21010814b
```

The values are unnamed numeric configuration data. Neither `0x14` nor any
neighbor is assigned a physical unit here.

## Exact target-`0x101` read geometry

Each request header is exactly three little-endian 32-bit words:
`target`, `address`, `length`. The fixed headers are:

| purpose | address | length | exact 12-byte header |
| --- | ---: | ---: | --- |
| pointer-slot window | `0x470002c0` | `0x20` | `01010000c002004720000000` |
| AP_EXCO start | `0x4500ff14` | `0x10` | `0101000014ff004510000000` |
| AP_EXCO `+0x3d8` neighborhood | `0x450102e0` | `0x20` | `01010000e002014520000000` |

The fixed sequence is six bulk transfers: for each row, one exact 12-byte OUT
header followed by one exact-length IN. The target receives bus addresses; no
raw `0x2000....` CPU address belongs in these headers. Any negative, zero,
short, over-count, exception, or phase uncertainty must fail closed without a
retry or a new header. On three exact pairs, the terminal parser phase is
`ReadyForHeader`. This review qualifies geometry only; it does not authorize
execution or replace the helper's transport/state-machine review.

## Remaining uncertainties and interpretation boundary

- The selected stored image-1 slot has been shown elsewhere to match the
  retained current fixed-data slot byte-for-byte. That is stored-image
  identity, not proof that every executing RAM byte still matches it.
- The AP_EXCO type-4 metadata and generic successful copy path prove what a
  successful load would copy. They do not establish which configuration bank
  was active, whether this load succeeded on this boot, or whether AP_EXCO was
  later modified.
- The CPU-slot reset, ordinary writer, and getter are exact packaged facts.
  Their current execution and lack of indirect/external writers are not
  proved.
- The `0x4700....` pointer window remains conditional on a mapper branch. The
  retained same-boot anchors justify the narrow observation, not the entire
  bus bank or future boots.
- A returned pointer equal to `0x4500ff14` strongly binds the three responses,
  but still does not prove the entire executing image, a physical panel state,
  event-time state, or immutability between sequential reads.
- The three reads are sequential, not atomic. Record acquisition order and
  preserve each raw response even when semantic validation fails.

Accordingly, the proposed capture can answer a narrow question: whether the
ordinary pointer slot currently names the expected fixed AP_EXCO object and
what bytes the two fixed AP_EXCO source windows return at that acquisition.
It cannot by itself prove why the panel fault occurred or justify modifying
any configuration, threshold, protection, persistence, high-bank, POFLG, or
return-guard state.
