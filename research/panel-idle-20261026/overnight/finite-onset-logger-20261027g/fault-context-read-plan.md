# Prospective fixed fault-context read at `0x47010f00`

Recorded 2026-10-27 UTC. This is an offline, read-only planning note. It did
not build a helper, contact the TV, open USB, read controller memory, alter a
threshold, or perform a write, reset, storage, UI, or recovery operation.
The exact predicate addresses from the event-736 caller are still pending;
no live operation should be scheduled from this note alone.

## Recommendation

The lowest-cost qualified design is one fixed 64-byte target-`0x101` memory
read at bus address `0x47010f00`, mechanically derived from the already built
and successfully used D5 fixed reader
`overnight/managed-usb-secondary-root-read-once`.

The prospective immutable geometry would be:

```text
target   0x00000101
address  0x47010f00
length   0x00000040
header   01010000000f014740000000
range    0x47010f00..0x47010f3f
root offsets +0x0f00..+0x0f3f
```

The header above is `struct.pack('<III', 0x101, 0x47010f00, 64)`, not a
manually shifted address. The range contains both candidate halfwords written
by the event-736 caller: root `+0x0f06` at returned bytes 6..7 and root
`+0x0f08` at returned bytes 8..9. The source selects `+0x0f06` for mode/index
6 and `+0x0f08` otherwise before it compares the selected value and raises
event `0x2e0`.

Do not freeze this geometry until the parallel predicate trace confirms that
all desired inputs fit in these 64 bytes. If a required value is outside the
window, choose one newly reviewed fixed range rather than adding a
caller-selected address or taking multiple exploratory reads.

## Why this is the lowest-cost reusable path

`managed-usb-secondary-root-read-once` is already the exact protocol shape:
fixed target `0x101`, fixed 64-byte length, one 12-byte OUT header followed by
one exact 64-byte IN, and no caller-selected geometry. Only the address,
header, dry-run label, wrapper metadata, schema, and manifests need mechanical
replacement. The native engine and assembly name can remain unchanged.

Pinned parent artifacts are:

| artifact | SHA-256 |
| --- | --- |
| parent `Program.cs` | `4a725f342237a848bd835ef090a9341ae30a80c70e9798a05236d108bbffe5e4` |
| parent `run-once.py` | `8023844c0219918544214f0a2ebaf8a6d8937ade14ea65c2b6b86027d674db9a` |
| parent `build-manifest.json` | `180acb56334ac1af0e4ccf3838e02bbefc7b7a91c2c9735848a2fba947ab2319` |
| byte-identical project file | `05893d224110307cdce9838c9620aba3ed1326901288ad105279cfc9eed3f187` |
| derivation boundary | `2a9f81085d88d6d0fc7e8522b9199c84b5292b82ebb70b64d5a2622d1b035cd5` |

The parent reports 26 zero-I/O fake-operation tests, including success;
open/claim failures; short, zero, negative, and over-count OUT/IN results;
identity change; exceptions at every phase; release/close errors; and bounded
descriptor-stream cases. Default invocation is dry-run, unknown CLI returns
63, and host execution is refused on the local non-ARM32 host.

This is preferable to deriving from the 256-byte RT-block reader: it avoids a
second independent length change and already has a successful live 64-byte
read in the same `0x470...` namespace. It is also preferable to the onset
logger helper, whose multi-read/write state machine is unnecessary for one
passive snapshot.

## Existing successful qualification

The D5 parent was executed once at target `0x101`, address `0x470004c0`,
length 64. Its retained record SHA-256 is
`d783bb6be3a01ef3dfe8ac86d1b2f1857674f8c463edd1bba09b70cc0b5c4881`;
the returned block SHA-256 is
`2543a59edfbd16832cfddd460c3dae28017309669d35eabc6eedcdfd95b7675d`.
It returned the expected live word `0x20010000` at CPU slot
`0x200004e0`/bus-window offset `+0x20`, used 16 authenticated root calls, and
finished with `STAGE_ABSENT`.

The consolidated D5 runtime audit SHA-256 is
`0eaa69868337c3bf21b9e5681488b6419a88c1fe05c4033fe2e5e467d3ab9e9b`.
That audit explicitly limits the result: the read establishes returned bytes
and the expected root pointer shape, not whole-image identity or a direct
sample of the core-tag register.

## Native boot, identity, and protocol contract

The reusable native contract is finite and fixed:

1. Refuse unless the process is little-endian ARM32 and the packed usbfs bulk
   structure is exactly 16 bytes.
2. Require the pinned boot ID, USB runtime state `active`, IDs
   `04e8:2001`, configuration 1, authorization 1, and the exact cached
   116-byte descriptor set.
3. Require interface `7-1:1.2` to be unbound and exactly interface 2,
   alternate setting 0, class `ff`, subclass/protocol `00/00`.
4. Resolve bus 7 and a bounded device number, open the corresponding usbfs
   character node with read/write, close-on-exec, and ARM-EABI no-follow
   flags.
5. Validate the opened FD through `statx`: character device, USB major 189,
   matching computed minor; then read and compare the exact cached 18-byte
   device descriptor.
6. Repeat the sysfs preflight and require the same bus/device identity before
   claiming interface 2.
7. Send exactly one 12-byte header to endpoint `0x02`, requiring return count
   12. Only then issue exactly one 64-byte IN on endpoint `0x82`, requiring
   return count 64. Each bulk operation has a 2,000-ms timeout.
8. On any short count, transport error, exception, or identity failure,
   reject. Do not send a second header, retry, reset, or continue with another
   memory request. Attempt release if claimed and close if opened.
9. Accept only after stage `complete`, exact counts, successful release, and
   successful close. Emit the 64 bytes only as bounded base64 plus SHA-256 in
   the compact result.

This is read-only at the requested memory level, but it still opens the USB
node read/write because usbfs bulk OUT is required to send the read header.
The initial OUT is protocol metadata, not a memory write request. Exact
transport counts prove framing, not freshness or that every internal leaf
status was honored.

## Host staging and cleanup boundary

The historical parent wrapper pins the build manifest, all three deployed
managed artifacts, the root runner, boot ID, and `/usr/bin/dotnet`; stages to
a random private `/tmp` directory under `umask 077`; executes self-tests and
one active invocation; records all authenticated calls and stdout; then, in a
`finally` block, removes only the three allowlisted files and their temporary
base64 files, removes the exact stage directory, and requires `STAGE_ABSENT`.
It contains no automatic active retry.

Its cleanup behavior is proven by the accepted D5 execution, but the wrapper
predates the later D7 hardening. A future build should preserve the native
engine while bringing the wrapper up to the current bounded pattern before
review: explicit directory/file type, owner, mode, and inventory guards;
separate completed target self-test from the exactly-one execute call; pinned
root adapter with an outer timeout margin; raw failed outcome retention; and
cleanup only after terminal completion. This is a wrapper repin, not a reason
to broaden the target protocol or add a retry.

The native parent hard-codes boot ID
`00000000-0000-4000-8000-000000000000`. An eventual candidate must first
confirm that boot remains current. If the TV reboots, the stale binary must
refuse; the boot binding must be deliberately rebuilt and reviewed rather
than bypassed at runtime.

## Is `0x47010f00` inside the same object?

There are two different questions, and the evidence supports them at
different strengths.

### Fixed `0x4701...` object: positive extent

The selected AP_RTP loader has two adjacent fixed destinations:

```text
0x47010000, length 0x2400  -> 0x47010000..0x470123ff
0x47012400, length 0x0100  -> 0x47012400..0x470124ff
```

Therefore the proposed 64-byte range `0x47010f00..0x47010f3f` is positively
inside the first configured AP_RTP destination, not merely adjacent to an
inferred object. It is well below the `0x47012400` boundary and does not cross
either payload extent. The selected-package configuration evidence is static;
it does not prove that every byte retains its packaged initial value live.

### Image-1 CPU root: positive code membership, conditional alias

Image-1 reset initialization puts pointer `0x20010000` in slot
`0x200004e0`, and the successful D5 live read returned that pointer. The
event-736 caller obtains that same root and directly stores halfwords at
root `+0x0f06` or `+0x0f08`; other RTP code accesses arrays at larger offsets
`+0x1000`, `+0x1400`, `+0x1800`, `+0x1c00`, and `+0x2000`, and the common
setter reaches `+0x240a`. Thus the firmware itself positively treats
`+0x0f00..+0x0f3f` as part of the same root-relative context.

What remains conditional is the address-space statement
`CPU 0x20010f00 == bus 0x47010f00`. The recovered mapper translates CPU
range `[0x20000000,0x20200000)` by `+0x27000000` on the non-A-core branch,
which gives exactly that address. Successful reads at `0x470004c0` and
`0x47012400`, plus V6's matched `0x1001`/`rtp_act_736` transition, strongly
support the continuous secondary window. They do not constitute a direct
core-tag-register observation or a prior read of this exact 64-byte range.
The prospective read would test that last address-specific assumption; it
must not be described beforehand as guaranteed image-1 RAM.

The packaged static allocation at `0x47010f00` is therefore positive. The
cross-core alias interpretation is strongly supported but still conditional.

## Optional identity reads and minimum operation count

For the present unchanged boot, the lowest operation count is the new context
read alone:

```text
1 fixed header OUT + 1 fixed 64-byte IN
```

Existing same-boot evidence already includes a successful callback-table read
at `0x45000580`, a successful root read at `0x470004c0`, repeated fixed RT
reads at `0x47012400`, and V6's exact callback and RT snapshots. Repeating
them merely for comfort would add protocol traffic without making the context
bytes more atomic.

If the boot or device identity changes before a future capture, optional
fresh qualification should be explicit and finite:

1. callback 64 bytes at `0x45000580` to compare the known eight-word active
   callback tuple; and
2. RT 64 bytes at `0x47012400` to bind the same secondary window and record
   the current event/gate/fault fields;
3. only then the context 64 bytes at `0x47010f00`.

That would be three separately fixed reads—three headers and three INs—not a
retry loop. A short/error/identity change at any phase must halt all later USB
traffic. If atomic correlation is required, the three reads need a newly
reviewed finite native sequence with ordered timestamps; three independent
host launches do not provide atomicity.

## Decision gate before any build or read

Wait for the event-736 predicate trace to supply exact addresses, widths, and
interpretations. Then require all of the following before implementation:

- every desired field is wholly contained in `+0x0f00..+0x0f3f`;
- expected byte offsets and endianness are derived from exact instructions,
  not guessed names;
- a new fixed helper differs mechanically from the pinned 64-byte parent;
- zero-I/O tests cover exact success data/hash and every short/error phase;
- a hardened wrapper and independent review clear the exact build;
- execution remains one-shot, read-only, no retry/reset, with raw retention;
- the result is treated as a sampled context, not a physical-panel sensor or
  justification to alter protection logic.

No helper should be built and no target read should occur until that predicate
address gate is resolved.
