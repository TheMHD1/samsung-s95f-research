# Device-side SSB target `0x203` read protocol

Recorded 2026-10-27 UTC. This is an offline reconstruction of the selected
5 MiB QD package. No USB interface, target device, TV, controller, UART,
network endpoint, flash path, or kernel driver was opened or invoked.

## Result

The storage-side leaf is recovered, but the execution-phase edge is **not**.
In the selected package, the
vendor interface with bulk OUT `0x02` and bulk IN `0x82` receives a 12-byte
little-endian header `(target, address, length)`. Target `0x203` is the read
member of the accepted `0x201..0x204` family. Its read branch calls a storage
routine which:

* requires both byte address and byte length to be multiples of 512;
* converts the byte address to a sector number with `address >> 9`; and
* invokes a controller leaf with MMIO base `0x58000000` in read mode.

This positively binds `0x203` to this firmware's **eMMC-sector read path**.
It is not the QD SPI-flash space established elsewhere. The host log string
“EMMC OTP read” was therefore directionally useful, but this CFG does not
prove that the selected range is an OTP partition: it only proves an eMMC
controller address space, bounded here to the accepted family-2 range below
16 MiB.

That local branch is not sufficient to construct a working one-header
transaction. The header parser unconditionally stores mode byte RAM
`0x20000571 = 2`; the common transfer body then tests the same byte and
branches around **all** operation dispatch while it remains `2`. The bounded
literal/writer census recovered no later `0` or `1` producer or alternate
re-entry which makes target `0x203` reachable. Therefore this report does
**not** clear even a one-sector USBDEVFS request. The exact missing edge is a
phase/mode transition or alternate entry between header parsing and operation
dispatch. This corrects the earlier candidate conclusion that one aligned
header was protocol-ready. See [the parent lead](ssb-family1-memory-in-route-lead-20261027.md),
SHA-256 `fe3bf0721efca33f720087ebad1dc4b4d5e6ecf407b57f6fb348aa6d58a702c1`.

If that gate is later resolved, the firmware ignores the eMMC read routine's
return before scheduling its IN response. A failed read could therefore
leave response-buffer contents ambiguous. No CRC, generation, storage
identity, or transfer-status field was recovered in this branch.

The initial review's response-capacity gap is also closed for **one 512-byte
sector**, not for an arbitrary host-selected chunk. The configuration callback
sets the cap to `0x200` when its internal halfword is zero and to `0x6000`
when it is nonzero. The transfer path uses `min(remaining, configured_cap)` and writes
that current size at RAM `0x2000054c` before reading into fixed buffer
`0x20001bc0`. Reset scatter row 11 zero-fills RAM `0x20000f4c..0x20017383`,
which contains the response buffer through the entire larger `0x6000` cap.
Thus `0x200` is both the eMMC minimum alignment unit and no larger than either
configured chunk. This closes the static buffer-size question only; it does
not close the mode-2 execution gate.

## Inputs and address convention

* Selected profile:
  `overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin`,
  5,242,880 bytes, SHA-256
  `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
* Image 0 uses canonical mapping **FILE = linked VA + `0x200`**.
* [Prior Linux-side boundary](qd-ssb-readback-acquisition-boundary.md),
  SHA-256
  `911c230c3509752f318af6e8ca7aa846547510c41c28a4fcdcbb02f6c72c7607`,
  established the host 12-byte header and the driver-side `0x203` choice but
  did not bind the device storage space.
* [Independent prior review](ssb-acquisition-independent-review.md), SHA-256
  `c7a1f1232f6765f67a72f97da74ec007351c1062710ce640118107c55b252e5a`,
  preserved that open/close participates in USB runtime PM.
* [Packaged/live USB descriptor match](qd-usb-device-descriptor-scatter-match-20261027.md),
  SHA-256
  `ec6d1c4edf55b4d7738422ecfbf2f141ac2ae6f35dcb3a00e2c861dec527ff64`,
  shows that the packaged 18-byte `04e8:2001` device descriptor exactly
  equals the retained cached descriptor. It does not prove current executable
  equality.

## Vendor endpoint and callback binding

The USB initializer at linked VA `0x2490c` / FILE `0x24b0c` writes endpoint
numbers `0x82` and `0x02` at VA `0x24920..0x24928`, then registers a callback
table. Reset scatter row 0 expands to RAM `0x20000000`, length `0xf4c`, with
output SHA-256
`685d8eda90bb3ce7e6210ad0dfe962f65ac3b8e1b2eb1a40962e0e5720d81eb3`.
The eight words at RAM `0x2000058c` are:

```text
2945d 293d1 294fb 00000000 00000000 28b85 28cf1 294f5
```

The Thumb pointer in slot `+0x18` binds the OUT completion callback to linked
VA `0x28cf0` / FILE `0x28ef0`. The rearm body at linked VA `0x29500` / FILE
`0x29700` passes exact length `0x0c` into the receive scheduler at VA
`0x2952a`.

This is reached through the normal packaged startup/configuration path, not
only through a previously active application transfer:

1. startup VA `0x39a16` directly calls the USB initializer VA `0x2490c`;
2. initializer VA `0x2493a` calls VA `0x284a0`, which returns the reset-scatter
   USB-core callback table at RAM `0x200004b8`; the initializer supplies it to
   VA `0x28b36` at VA `0x2495a`;
3. that core table's first Thumb pointer is VA `0x28448`, which walks the
   registered class list and invokes slot `+0` of each class table; and
4. the vendor class table at RAM `0x2000058c` has VA `0x2945c` in slot `+0`.
   VA `0x2945c` installs the 12-byte-header buffer, chooses the chunk cap, and
   calls the exact rearm body VA `0x29500` at VA `0x294dc`.

Fresh retained host state also shows that this device was configured, active,
and unclaimed by a kernel interface driver at the sampled instant:
`overnight/rt-telemetry-followup-20261027b/usb-one-chunk-preflight-metadata.txt`,
SHA-256
`ac45ca58422861555639eac65dd2fd1b26aba71ffb389753da96292d0cab948c`,
records the expected boot, uptime `98176.31..98176.36`, configuration `1`,
runtime status `active`, all three interfaces `UNBOUND`, and usbfs node
`/dev/bus/usb/007/045`. This is a timestamped endpoint-state fact, not proof
of current firmware bytes or future exclusivity.

The callback reads the three words through its header pointer:

| header offset | destination state | meaning established by use |
| ---: | ---: | --- |
| `+0x00` | state `+0x0c` | target/family/operation |
| `+0x04` | state `+0x04` | byte address |
| `+0x08` | state `+0x08` | remaining byte length |

It invokes validator linked VA `0x29258` at VA `0x28f68`. The validator has
explicit comparisons for `0x201`, `0x202`, `0x203`, and `0x204` at
`0x29322..0x2933e`. For this family it rejects address/length ranges reaching
16 MiB. The completion callback separates the high family and low operation;
the low byte of `0x203` is operation `3`. At VA `0x2914e..0x29176`, operation
`3` calls linked VA `0x9bd4`. Operation `4` follows a different write branch
to linked VA `0x9fe8`; nothing in this report treats those directions as
interchangeable.

## Header-phase mode gate

The preceding destination is a local CFG branch, not a proven ordinary-header
execution path:

```text
VA 0x28f44  movs  r0,#2
VA 0x28f46  ldr   r1,[pc,...]       ; literal RAM 0x20000571
VA 0x28f48  strb  r0,[r1]
...
VA 0x290d6  ldr   r0,[pc,...]       ; same RAM byte
VA 0x290da  ldrb  r0,[r0]
VA 0x290dc  cmp   r0,#2
VA 0x290de  beq   0x28f70           ; bypass chunk/op dispatch
```

The same byte is the mode selector in helper VA `0xefa4`: zero selects its
first address map, one its second, and other values return without a useful
mapped source; invalid selections also store two. Exact raw `0x20000571`
literals in image 0 occur at FILE `0xf348`, `0x28edc`, `0x290ec`, and
`0x293f0`. This finite literal census cannot exclude an alias/computed writer,
but it did not recover the required later transition. Calling this merely a
deferred main-loop operation would be speculation.

The adjacent remap byte is distinct: validator VA `0x29270..0x29282` stores
RAM `0x20000570 = 0` for nonzero families, and the callback reads that same
byte. Target `0x203` therefore does not take the family-0 remap in this header
path absent a concurrent writer. Resolving that remap does not resolve the
separate `0x20000571 == 2` dispatch bypass.

## eMMC read leaf and integrity boundary

The linked VA `0x9bd4` / FILE `0x9dd4` read leaf is concrete:

```text
VA 0x09c44  ubfx  r0,r4,#0,#9       ; length low 9 bits
VA 0x09c54  ubfx  r0,r5,#0,#9       ; address low 9 bits
VA 0x09c90  lsr.w sl,r5,#9           ; byte address -> sector
VA 0x09c9a  mov.w r0,#0x58000000    ; controller MMIO base
VA 0x09ca2  bl    0x16b70            ; storage-controller leaf
```

The caller supplies response buffer RAM `0x20001bc0`, the decoded byte
address, bounded current chunk length, read mode `0`, and stack constant
`0xabcd`. Immediately after the `BL 0x9bd4` at VA `0x29176`, execution starts
response-buffer setup at VA `0x2917a`; there is no compare or branch on the
read routine's return. Consequently, receipt of the requested number of USB
bytes does **not** by itself prove that the eMMC controller populated them.

Before that call, VA `0x290e0..0x290f4` takes the smaller of the remaining
length and configured cap at RAM `0x20000548`, then stores the current chunk at
RAM `0x2000054c`. The configuration callback writes either `0x200` or
`0x6000` to the cap. The fixed response-buffer
literal is RAM `0x20001bc0`; both limits are inside the reset zero-fill span
described above. This closes capacity for a one-sector request but does not
justify enlarging it to the host driver's historical 8 KiB chunk merely
because that driver used 8 KiB.

The bounded code slices are:

| role | linked VA / FILE | bytes | SHA-256 |
| --- | --- | ---: | --- |
| vendor init | `2490c` / `24b0c` | `0x58` | `fe0614e38e5ba9a93ea7b9e7f6713407c9f2abdc4fcce28d11448c8baee41ae2` |
| OUT completion | `28cf0` / `28ef0` | `0x234` | `08ac2b1b519d532452e92428777d04d935f4bbe883d42e06a5456b4a6d5ddb17` |
| target validator | `29258` / `29458` | `0x15c` | `febec20e4653208a48681cf6f82f1f9e13a7b03149e53f6baf5ddf149827c234` |
| next-header arm | `29500` / `29700` | `0x34` | `19b640cf59ed8e61dbefe6e4d59ce3188f4d20be75e9d8d432bd483ada39561f` |
| eMMC read | `09bd4` / `09dd4` | `0xe4` | `7eb2e0e5029fb8ac2c64fe88c207c7922dafbfcc651928dcae21b1a2cef2343b` |
| adjacent eMMC write | `09fe8` / `0a1e8` | `0x46` | `3303ecbaa6a74cc7a25c6420aa9a33aa44ff077807e70c27443bfeb132bf7466` |
| core class broadcaster | `28448` / `28648` | `0x4a` | `c4f064a989b3b50c08d280832b60792021494ac45e7b1ec65691a7981c46ff3b` |
| core table accessor | `284a0` / `286a0` | `0x14` | `0b2ed95da6399a86d48c019a1b21ddfc546dc5c49933f91866f417ce12d619f5` |
| vendor configuration | `2945c` / `2965c` | `0x88` | `7d0acce7e777be885ce0e87c205580f21a204dc38800d1d58a633405dda25748` |
| startup call window | `39a00` / `39c00` | `0x1a` | `1be8eb4f97bb2028d3ffe93a61dc0566e5021eeaae5044dd55af294752dbe722` |

## One-chunk userland feasibility

A strict USBDEVFS implementation is **not ready** from the recovered code.
Although endpoint identity, header grammar, target validation, one-sector
capacity, and the target-`0x203` eMMC leaf are source-bound, ordinary header
parsing demonstrably leaves mode `2` and bypasses the operation. A proven
phase transition/re-entry is required before even a descriptor-RAM control
read or one-sector storage read can be specified faithfully.

If that missing gate were recovered, a request would still be active USB bulk
OUT and could participate in runtime resume/interface state. It would also
remain an untrustworthy installed-prefix validator for three independent
reasons:

1. The retained package descriptor matches cached live USB identity, but the
   currently executing firmware has not been byte-bound to this package.
2. The firmware ignores storage-read failure before IN scheduling, and the
   response has no recovered status, CRC, or freshness marker.
3. The eMMC address region is proven, but the partition/object represented by
   a particular offset—including whether a prefix is firmware, metadata,
   spare/stale data, or an OTP-like area—is not proven by this CFG.

A known-prefix match would corroborate package/storage identity; it would not
alone prove current executable equality. A mismatch would be ambiguous among
different storage content, wrong offset/object, stale response data, current
firmware mismatch, and read failure. Those are technical integrity and
binding gaps, not an assertion that an authorized operator lacks permission.

## Reproduction and limits

[The checker](ssb-device-read-protocol-20261027.py) pins the package and
validated scatter decoder, reconstructs the callback table, decodes exact
Thumb/M-class instructions, pins all bounded slices, and models the grammar
with local bytes only. Run it with the retained Capstone environment:

```sh
PYTHONPATH=/tmp/tcon-capstone python3 tcon-research/ssb-device-read-protocol-20261027.py
PYTHONPATH=/tmp/tcon-capstone python3 -O tcon-research/ssb-device-read-protocol-20261027.py
```

This report does not reconstruct eMMC partition tables, prove the current
interface binding, prove live package equality, identify a firmware prefix,
or prove a reachable header-to-read execution path. No USB packet was built
or sent. A future read would not be passive: bulk OUT, interface claiming,
USB runtime PM, and firmware/controller access are active effects even when
the storage direction is read.
