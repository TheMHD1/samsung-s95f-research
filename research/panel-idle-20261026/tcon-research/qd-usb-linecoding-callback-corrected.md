# Corrected QD image-0 USB line-coding callback

Recorded 2026-10-27 UTC. This is bounded offline analysis of retained bytes.
It made no TV, root, network, USB, UART, controller, GPIO, or firmware call.

## Result

The absolute Thumb pointer installed in the image-0 `USBSerial` object is
`0x0002b071`. With the proved `0x200` image-0 container displacement, its body
is linked VA `0x2b070` at stored file offset **`0x2b270`**. The prior USB log
report decoded stored file `0x2b070`, a different function; its claim that the
class callback rewrites register bits is superseded.

The corrected callback is narrower:

* it acts only for CDC `SET_LINE_CODING` (`bRequest=0x20`);
* if RAM word `0x2000063c` is nonzero and the registered USB state exists, it
  calls that word as a function pointer with the little-endian baud dword at
  USB state `+0x4`; and
* it returns zero. It ignores state `+0x8..+0xa` and DTR request `0x22`.

Reset scatter initializes `0x2000063c` to **zero**. Its only exact address
literal in image 0 is the corrected callback's read, and no direct packaged
setter or nonzero target was recovered. A runtime producer, target function,
and UART bridge therefore remain unproved. The code is compatible with an
optional baud-change hook, but does not prove that the hook is populated.

DTR remains state-changing for a separate reason. A zero-to-one control-line
transition clears USBSerial transfer/ring bookkeeping and can prime a 64-byte
receive on bulk-OUT endpoint `0x01`. That is a local USB data-path reset and
submit, not a proved MCU reset, panel reset, rail action, or UART baud change.

## Inputs and corrected coordinates

| retained input | size | SHA-256 |
| --- | ---: | --- |
| `overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin` | 5,242,880 | `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0` |
| `qd-image1-context-initialization.md` | 12,386 | `e885c17d2d1092fd82d761ed4c7b1cd1627bcfa921bfba8027b515918da39c66` |
| historical `qd-usb-log-output-route.md` | 14,474 | `a14f5280bd15244ac702d5f1fb9131b42be74504722be3a7bdf3d81f80e5ba50` |
| historical `qd-usb-cdc-control-requests.md` | 5,005 | `909a30915e2bf7ffa6ec5aeac02a1b65efc8fde636f0db333ef99e16a9d4a99b` |

Image 0's vector is stored at file `0x200`, but linked addresses begin at
zero: `stored file offset = linked VA + 0x200`. RAM/MMIO values are not
shifted.

## Pointer installation and exact callback

The USBSerial initializer is stored at file `0x22324`, linked VA `0x22124`:

```text
VA 22158  ldr  r0,[pc,#0x44]   ; word 0x0002b071
VA 2215a  str  r0,[r1,#0x5c]  ; USBSerial callback slot
```

Clearing the Thumb bit gives target VA `0x2b070`; adding the payload base
locates file `0x2b270`. Raw word `0x0002b071` occurs once, at file `0x223a0`.
The same initializer stores a registration handle at RAM `0x20000638`; it
does not write the neighboring optional hook at `0x2000063c`.

The corrected body at VA `0x2b070..0x2b097` is:

```text
2b070  push.w {r4,r5,r6,r7,r8,lr}
2b074  mov    r4,r0                 ; registration/context
2b076  mov    r5,r1                 ; bRequest
2b07c  cmp    r5,#0x20
2b07e  bne    2b094
2b080  ldr    r0,[pc,#0x18]         ; &0x2000063c
2b082  ldr    r0,[r0]
2b084  cbz    r0,2b094
2b086  ldr    r6,[r4,#0x18]         ; USBSerial state
2b088  cbz    r6,2b092
2b08a  ldr    r1,[pc,#0x10]         ; &0x2000063c
2b08c  ldr    r0,[r6,#4]            ; baud dword
2b08e  ldr    r1,[r1]
2b090  blx    r1                     ; hook(baud)
2b094  movs   r0,#0
2b096  pop.w  {r4,r5,r6,r7,r8,pc}
2b09c  .word  0x2000063c
```

Upstream, request `0x20` copies seven bytes into the USBSerial state: bytes
zero through three become `+0x4`, and bytes four through six become `+0x8`,
`+0x9`, and `+0xa`. The common tail invokes the callback with the registration
object and request code. This binds `[r4+0x18]` to the registered USBSerial
state rather than arbitrary caller RAM.

The exact comparison proves a SET_LINE_CODING post-hook, not a generic DTR
or reset callback. The body contains no direct MMIO, endpoint, UART, reset,
panel, rail, EEPROM, or controller-command access. Only a nonzero indirect
target could add such an effect, and that target is not established.

## Reset initialization and producer census

Image-0 reset enters scatter VA `0x140`. The first record is:

```text
compressed source VA  0x0003e32c  (stored file 0x3e52c)
destination RAM       0x20000000
output size           0x00000f4c
handler VA            0x0000017c  (decompressor)
```

Replaying the exact decompressor produces 3,916 bytes with SHA-256
`685d8eda90bb3ce7e6210ad0dfe962f65ac3b8e1b2eb1a40962e0e5720d81eb3`.
The relevant output is:

```text
RAM 0x20000634  00 00 00 00
RAM 0x20000638  00 00 00 00
RAM 0x2000063c  00 00 00 00
RAM 0x20000640  00 00 00 00
```

The final scatter record zero-fills from `0x20000f4c`, so it does not
overwrite this earlier decompressed region. Zero is therefore a positive
reset-time initialization result, not an assumption from writer absence.

A bounded producer census found one aligned raw word `0x2000063c`, at file
`0x2b29c` in the callback; no second exact-address literal; and no
halfword-aligned Thumb `movw`/`movt` construction of that absolute address in
image 0. The direct `0x20000638` reference is the distinct handle store above.
This does not exclude computed-address code, bootloader/debugger mutation, or
another component. It does establish that no nonzero producer or live target
is present in retained evidence.

## DTR path after correction

Corrected labels for the previously recovered relative path are:

```text
class handler       linked VA 0x29858  (stored file 0x29a58)
DTR transition      linked VA 0x29534  (stored file 0x29734)
receive wrapper     linked VA 0x299f2  (stored file 0x29bf2)
receive worker      linked VA 0x29afc  (stored file 0x29cfc)
```

For request `0x22`, the handler stores low `wValue` at state `+0x58`, masks
bit zero, and calls the transition. On a zero-to-one edge, the transition:

1. zeros words `+0x38`, `+0x3c`, `+0x34`, and `+0x30` and byte `+0x49`;
2. calls the receive wrapper; and
3. stores the new bit at state `+0x4a`.

For the fixed USBSerial object, `+0x30/+0x34` are formatter-ring indexes, so
a rising edge discards queued formatter bytes. The wrapper calls the receive
worker when byte `+0x48` is zero. That worker uses the buffer at `+0x14`,
capacity/index fields `+0x18..+0x24`, and endpoint byte `+0x0d` (initialized
to `0x01`). With enough free space it marks byte `+0x48` active and calls the
endpoint receive helper for `0x40` bytes. Other branches can alter that active
state and call another endpoint helper. These are USB transfer effects.

The class common tail also invokes the shared callback for request `0x22`,
but the corrected comparison at VA `0x2b07c` returns immediately. DTR does
**not** read or call `0x2000063c`. No direct UART baud setter, MCU reset, panel
reset, power cycle, rail, or protection-state change is present in these
bounded bodies.

## Historical supersession

The frozen historical reports remain unchanged.

* This report supersedes `qd-usb-log-output-route.md` only where it treated
  linked pointer `0x2b071` as stored file `0x2b070` and attributed that
  unrelated body's register rewrite to the callback. Its statement that DTR
  invokes that rewrite is also superseded.
* It resolves the shared callback left unknown in
  `qd-usb-cdc-control-requests.md`. That report's relative class-request copy
  and DTR-state trace remain structurally intact under corrected
  `VA = file - 0x200` labels.
* The formatter-ring/endpoint-`0x81` route followed relative branches and
  object fields and is not invalidated by this callback correction. Its
  no-guaranteed-backlog and no-current-live-binding limits remain.
* The separately recovered common-error UART ring is not connected here to
  the optional baud hook. Co-location is not a dataflow edge.

No USB procedure follows from the correction. SET_LINE_CODING and DTR are
host-to-device control writes; the former could invoke an unresolved indirect
hook if runtime code populated it, while the latter has the concrete transfer
state effects above.

## Exact stored-byte hashes

| interval | bytes | SHA-256 |
| --- | ---: | --- |
| scatter table file `0x3e340..0x3e3ff` | 192 | `3f09781583f48d9b429fe8438b06bbd26196b3f673c79e6a2cf7adde356b612d` |
| USBSerial init file `0x22324..0x2238f` | 108 | `ac0cbbee3f3088afe88c4541c0136a60778cfcfa4d8461c4720247ecb117a8b6` |
| corrected callback file `0x2b270..0x2b297` | 40 | `5389e0b7ec7ee954988cad706524ebe79584d60553f84b5a995a63405d34acb9` |
| class handler file `0x29a58..0x29b33` | 220 | `e15cf87757aca28af68b7ecbb44b3fca5166682eea1b225a17e61c436dee4c3f` |
| DTR transition file `0x29734..0x29769` | 54 | `5cd48ca0bee9bf9a4c72e3fbdfd31d274a3cd7a9f79044e99d26809a2f7fc273` |
| receive worker file `0x29cfc..0x29da1` | 166 | `95f2b8b66c1a603d4d7b0d7868e5c387f0788086efc88be823b516408c725959` |

## Limits

This is a packaged-image static trace. It does not prove that these bytes are
currently executing, that running RAM hook `0x2000063c` is zero, that a USB
interface is bound, which class requests a host sends, that an endpoint
transfer succeeds, or that UART-like MMIO is bridged to CDC. It provides no
RT-fault, panel-light, Apps, recovery, cause, or repair conclusion.

