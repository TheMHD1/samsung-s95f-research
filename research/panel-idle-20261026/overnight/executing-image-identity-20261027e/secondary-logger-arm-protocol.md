# Secondary logger volatile-arm protocol

Recorded 2026-10-27 UTC. This is an offline reconstruction only. No writer was
built, no USB request was serialized or sent, and no TV, USB node, driver,
network endpoint, controller, RAM location, register, storage object, or
external service was accessed.

## Result

The selected package contains a locally complete ordinary-header path for a
raw direct-memory write using **target `0x102`**, not target `0x201`.
`0x102` is family 1, normalized operation 2, transfer mode 0. `0x201` belongs
to family 2 and is part of the separate storage family; the values are not
interchangeable.

For the single candidate discussed here, the offline bytes would be:

```text
header OUT:  020100000624014702000000
             target=0x102 address=0x47012406 length=2
payload OUT: 0100
```

The first exact 12-byte OUT is a header. It does not itself write the target
halfword. After validation it arms another OUT receive whose destination is
the header address, passed unchanged. The second exact two-byte OUT is the
payload. There is **no IN acknowledgement or returned status**. When the
payload completion count is exactly two, the firmware advances the address to
`0x47012408`, reduces remaining length to zero, stores operation 6, and rearms
the next 12-byte header receive.

This resolves the local mode and completion control flow for target `0x102`
operation 2. It does not prove physical write success, current executable
identity, absence of a concurrent writer, or the semantics of every other
write operation. In particular, family-2 operation 4 is a distinct eMMC write
path and is outside this candidate.

## Positive header-to-payload edges

Image 0 uses exactly **FILE = linked VA + `0x200`**.

1. OUT callback VA `0x28cf0` / FILE `0x28ef0` sees remaining length zero and
   calls parser VA `0x28f24` at VA `0x28d30`.
2. The parser copies header target, address, and length into state at
   `0x28f50..0x28f60` and calls validator VA `0x29258` at `0x28f68`.
3. The validator requires at least 12 received header bytes and nonzero length.
   It explicitly accepts target `0x102` at `0x292e8..0x292ee`.
4. The target high halfword is family 1. The validator stores the separate
   remap flag `0x20000570 = 0`; only family 0 sets that flag to one.
5. The parser takes the low target byte, removes optional bit 4, and therefore
   normalizes `0x102` to operation 2 at `0x28fb4..0x28fc4`.
6. Operations 1 and 2 store transfer mode 0 at `0x29046..0x29060`.
7. Because the family-1 remap flag is zero, `0x290c8..0x290d4` skips address
   mapper VA `0xefa4`. The supplied `0x47012406` remains unchanged.
8. `0x290e0..0x290f4` stores
   `min(remaining, configured_cap)` as the current chunk. The configured cap is
   either `0x200` or `0x6000`; both produce a two-byte chunk here.
9. The operation-2 branch `0x2912a..0x2914c` loads that chunk as a halfword and
   calls OUT receive scheduler VA `0x7fce` with the unchanged address and
   length two. It does not call IN scheduler VA `0x8054`.
10. VA `0x7fce` stores the caller's address unchanged at endpoint-context
    `+0x10` and `+0x14`, stores length at `+0x18`, marks the direction OUT, and
    calls VA `0x2ac10`.
11. The OUT scheduler rounds nonzero receive capacity to an endpoint-packet
    multiple. Endpoint `0x02` has max packet `0x200`, so requested length two
    arms a **512-byte-capacity** DMA descriptor. VA `0x280c` ultimately writes
    `caller_address + descriptor_offset` into the DMA address register at
    `0x296e..0x2970`; the sole descriptor has offset zero.
12. When the payload completes, callback VA `0x28d66..0x28d84` obtains the
    actual completed byte count from VA `0x260c`, subtracts it from remaining,
    and advances the state address by the same count.
13. Exact completion takes `0x28d88..0x28da0`, stores operation 6, and calls
    VA `0x29500`. That rearm body requires operation 6 and remaining zero, then
    schedules an exact 12-byte OUT header at `0x29522..0x2952a`.

The device therefore expects **two OUT transfers and no IN transfer** for this
write. A successful host payload count of two is the transport completion
condition; it is not an independent memory-content acknowledgement. A
subsequent readback is required to establish the observed value.

## Address and length boundaries

The family-2 validator applies its 16 MiB bounds only when `family == 2`.
Family 1 has no recovered address-range, address-alignment, length-alignment,
or address-plus-length overflow check in this path. The common validator only
requires nonzero length. Current chunks are limited by the configured cap and
passed through a 16-bit length load; two bytes fit both caps and the 16-bit
field.

The firmware therefore does not reject unaligned address `0x47012406` or
two-byte length. That is not a general hardware-alignment proof. It shows only
that the firmware passes this candidate into the USB DMA descriptor without an
alignment guard. The device controller's physical behavior must be verified by
readback, never assumed from header acceptance.

For OUT, the lower scheduler rounds two bytes to a 512-byte descriptor
capacity. An exact two-byte host request ends in a short USB packet and should
report actual count two. The larger device-side capacity materially increases
the consequence of malformed, concurrent, or accidentally oversized host
traffic even though a correctly bounded host buffer contains only two bytes.

## Bus alias and secondary context

The current acquired image's mapper shows CPU range
`[0x20000000,0x20200000)` receives addend `0x25000000` for core tag `0xa` and
`0x27000000` otherwise. The write protocol does not call this mapper for
family 1: it programs the already-translated header address into the USB DMA
descriptor.

Separate retained evidence binds the relevant addresses:

- image-1 root accessor VA `0x38fc` / FILE `0x43afc` loads pointer slot
  CPU `0x200004e0`;
- decoded image-1 row 0 initializes that slot to `0x20010000`;
- root `0x20010000 + 0x2406 = 0x20012406`;
- non-A-core bus alias `0x20012406 + 0x27000000 = 0x47012406`; and
- the retained D3 read of `0x47012400..0x470124ff` returned a coherent RT block
  and observed halfword offset 6 as zero.

Together with the descriptor dataflow, this supports the specific conclusion
that `0x47012406` is passed as a DMA bus destination for the image-1 SRAM
object. No write was performed. D3's zero is a past observation, not proof the
halfword will still be zero at a future write instant.

## What `+0x2406` controls

Image 1 uses exactly **FILE = linked VA + `0x40200`**. Formatter VA
`0x1b8c8` / FILE `0x5bac8` reads the low byte at context `+0x2406`, masks bit
0, and skips all formatting/ring writes when that bit is zero. Common event
setter VA `0xc1e0` / FILE `0x4c3e0` updates fields `+0x2400`, `+0x240a`, and
`+0x240e`, then calls the formatter twice. Enabling bit 0 therefore exposes
those event strings to the secondary `0x20200000` ring path.

An exact halfword write of `0x0001` is more invasive than the firmware's own
direct writers. The complete direct `MOVW #0x2406` census found:

- no direct-immediate reference in stored image 0;
- the formatter gate at VA `0x1b8d6`; and
- two image-1 save/set/restore sequences at
  `0x183d8..0x18556` and `0x1ba54..0x1bab8`.

Both sequences save bit 0, read the halfword, set bit 0 with a
read-modify-write preserving the other 15 bits, perform initialization/logging
work, and restore only the saved bit while again preserving the other bits.
Thus the recovered direct uses treat bit 0 as a logging gate, but they also
show that the remaining halfword bits are deliberately preserved. A raw
payload `01 00` overwrites all 16 bits. It is acceptable as a candidate only
if an immediate same-boot pre-snapshot proves the exact halfword is `0x0000`.
This census cannot exclude computed offsets, aliases, DMA, or an external core.

The save/restore sequences also create a race: if firmware saves zero before
an external arm and restores afterward, it can silently clear the external
bit. Conversely, an external full-halfword write during a firmware sequence
could clobber concurrently changed upper bits. A post-read is mandatory.

## Partial-transfer and retry hazards

This protocol is not retry-idempotent.

- If the 12-byte header is accepted, the device stops waiting for a header and
  waits for payload at `0x47012406`. Sending a new header at that point would
  be treated as payload and could overwrite the target window.
- A one-byte payload completion writes one byte, leaves remaining length one,
  advances the address to `0x47012407`, and arms another OUT receive.
- A zero-byte completion leaves the same address and remaining length pending.
- A payload count larger than remaining length causes unsigned subtraction.
  For example, count 12 against remaining 2 yields `0xfffffff6`, advances the
  address by 12, and leaves the protocol in a corrupted continuation state.
- A host timeout cannot distinguish no transfer, accepted header awaiting
  payload, partial payload, exact payload awaiting callback/rearm, or completed
  rearm. Neither header nor payload may be retried blindly.
- Closing or releasing the interface is cleanup, not proof that the firmware
  state machine returned to header phase.

After any short count, timeout, transport error, boot change, interface
identity change, or ambiguous cleanup, the only safe disposition is to retain
the record, issue no new SSB header on that session, and require a separately
reviewed controller reset/requalification path before another attempt.

## Review gates before any volatile experiment

No writer exists from this work. A future fixed writer should not be approved
unless all of the following are independently reviewed:

1. Same-boot pre-read of the containing RT block, with exact transport counts,
   proves bytes `0x47012406..07` are `00 00` immediately before the write.
2. The writer contains only the fixed 12-byte header and fixed two-byte
   payload, one attempt each, exact counts, no retry, no reset, and no
   caller-selected target, address, length, or payload.
3. The writer treats header success followed by any payload result other than
   exact count two as indeterminate and permanently stops that session.
4. Exact completion is followed by a fresh fixed readback proving `01 00`;
   absence of an IN acknowledgement is never presented as memory success.
5. The original exact two bytes are retained before mutation. Rollback uses a
   separately reviewed fixed two-OUT operation with those bytes, then a fixed
   readback proves restoration. Rollback is not attempted blindly after an
   ambiguous partial transaction.
6. Observation is bounded in time because the ring can grow rapidly and the
   firmware's own save/restore sequences can race or undo the arm.

These are protocol requirements, not authorization to perform the write.

## Inputs, slices, and reproduction

- Selected package: 5,242,880 bytes, SHA-256
  `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
- Current acquired 5 MiB image: SHA-256
  `f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562`.
- Prior device-read report: SHA-256
  `6bafcfb45e95b18a3646b71e5da37a43df4a863e6368e57dfb808e139da7021c`.
- Mode-gate correction: SHA-256
  `1d0539352a82a6c51a5b084de5d42fc8c272f1a3ca6b821b217bb75add680c9c`.
- D3 RT block: 256 bytes, SHA-256
  `7044ed744404edf22eff6d90a7cc9cdcd5704cbbad5e0e2f85de03acfa23217d`.
- Verifier: `verify-secondary-logger-arm-protocol.py`, SHA-256
  `4858efeaaa6fbf3185b9eed9c7741e3e2ab5f9cd656b18b4c7a87d5075fd87e7`.

Pinned source slices include:

| role | linked VA / FILE | length | SHA-256 |
| --- | --- | ---: | --- |
| OUT callback | `28cf0` / `28ef0` | `0x1d6` | `7c165cbf88ebd117d929ee9c1dd8594c442b4c73b78b0fc12ad0273ba1c952b7` |
| parser/dispatch | `28f24` / `29124` | `0x2cc` | `101fe3f099e3d9b75ed873206120a8753486edeefe3019b55648e3758a8c2bc4` |
| target validator | `29258` / `29458` | `0x15c` | `febec20e4653208a48681cf6f82f1f9e13a7b03149e53f6baf5ddf149827c234` |
| header rearm | `29500` / `29700` | `0x34` | `19b640cf59ed8e61dbefe6e4d59ce3188f4d20be75e9d8d432bd483ada39561f` |
| OUT receive wrapper | `07fce` / `081ce` | `0x3c` | `fec5159ee7f5e38ae07f64d070d783af0a98bd2599905c6c8d1d8b0c243a9ebc` |
| OUT scheduler | `2ac10` / `2ae10` | `0xc4` | `ca6d2a5c81c82c37ae523712eee79e1549fb801e2e60ddf4574edfed1166ef48` |
| DMA descriptor writer | `0280c` / `02a0c` | `0x17c` | `42c9a28b25bc9dddca9436fdf64172897c4a381584a5f4a48d8b7753d65fe4f2` |
| completion counter | `0260c` / `0280c` | `0x48` | `dadfb1866a5ce16b1b8ef60a85814d34e13d287ccf21277cc10479dbd29f5225` |
| image-1 formatter | `1b8c8` / `5bac8` | `0x78` | `47abdf7963385a87473920daae5212943303054ceb9ba3df92c3c31928fb545e` |
| image-1 save/restore A | `183b8` / `585b8` | `0x1a4` | `42158128055eed35af26373855871473a0bfbcc94159d5046c83fde1010d4778` |
| image-1 save/restore B | `1ba24` / `5bc24` | `0x98` | `23daaceae0a229c5ac76796f50b8200ba0635b8da533ee09ca170a822f2128da` |
| image-1 event setter | `0c1e0` / `4c3e0` | `0x32` | `f8a6285dd94b3338eff37ded006a2ebff6ecfe7409bef9044f34fd25cdb27102` |

Run both modes; all checks use explicit `need` calls and remain active under
optimized Python:

```sh
PYTHONPATH=/tmp/tcon-capstone python3 verify-secondary-logger-arm-protocol.py
PYTHONPATH=/tmp/tcon-capstone python3 -O verify-secondary-logger-arm-protocol.py
```

Both runs are offline and perform zero target operations.
