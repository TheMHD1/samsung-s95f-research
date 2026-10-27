# QD image-0 CDC class-control request trace

Recorded 2026-10-27 UTC. This is offline disassembly of the retained selected
QD profile. No USB device, serial node, control transfer, bulk endpoint, TV,
root, or network operation was performed.

## Result

Image 0 contains a real CDC class-request handler for the four standard CDC
ACM request numbers:

| bRequest | derived operation | exact local effect |
| ---: | --- | --- |
| `0x20` | `SET_LINE_CODING` | copies seven supplied bytes into state `+0x4..+0xa` |
| `0x21` | `GET_LINE_CODING` | copies those seven state bytes into the reply buffer |
| `0x22` | `SET_CONTROL_LINE_STATE` | records the low `wValue` byte at state `+0x58`; bit 0 is passed to a DTR-like transition routine |
| `0x23` | `SEND_BREAK` | no request-specific local field operation recovered before the shared optional callback |

The names are warranted here because the image first proves class request type
`0x20` from `bmRequestType`, then switches on the documented CDC request
values. This does not make a host open or DTR change safe: a shared indirect
callback remains unresolved, and the `0x22` transition changes local transfer
state.

## Input and object boundary

```text
overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin
SHA-256 bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0
```

All addresses are image-0 linked Thumb addresses. The surrounding USB
constructor path remains separately documented in `qd-usb-console-binding.md`:
`0x24b1c` calls `0x22324`, which stores the exact `USBSerial` pointer at
`0x22394` and registers configuration helpers. This report traces the
concrete control handler but does **not** claim a recovered direct assignment
from that constructor to the handler's `state` object.

## Class dispatch proves the request-field interpretation

At `0x29c08`, `r4` is the incoming setup packet. The dispatcher does:

```text
29c1a  ldrb r0,[r4]            ; bmRequestType
29c1c  and  r0,r0,#0x60        ; type bits
29c20  cbz  r0,0x29c7e
29c22  cmp  r0,#0x20
29c24  bne  0x29cea
...
29c36  ldrb r2,[r4,#1]         ; bRequest
29c3a  add  r3,r5,#0x40        ; class data buffer
29c40  bl   0x29a58
```

The alternate zero-data path at `0x29c68..0x29c74` passes `r4+2`, the low
`wValue` byte, to the same handler. Thus the values are not inferred merely
from nearby constants: they are class (`0x20`) request codes from setup byte
one, with data or control-value source selected by the dispatcher.

The handler receives its state as `r5 = [r6,#0x18]` at `0x29a68` and switches
on `r7` at `0x29a80..0x29a90`.

## Exact four-request behavior

### `0x20`: line coding input

`0x29a9c..0x29abe` packs `r4[0..3]` into the little-endian word at
`state+4`, then writes `r4[4]`, `r4[5]`, and `r4[6]` to `state+8`, `+9`, and
`+a`. The body makes no direct call to a rail, reset, panel, EEPROM, or output
control routine.

### `0x21`: line coding reply

`0x29ac0..0x29ae2` reverses that layout into seven reply bytes at `r4[0..6]`.
It is a state read/copy in this bounded body, not a physical baud-rate proof.

### `0x22`: control-line/DTR transition

`0x29ae4..0x29af2` copies `r4[0]` to `state+0x58` and masks bit zero. The
caller for the no-data case passes setup `wValue` low byte (`setup+2`) at
`0x29c68..0x29c74`; therefore bit zero is specifically a control-line-state
bit, conventionally DTR in CDC ACM.

Both outcomes invoke `0x29734(r8, state, bit0)`:

```text
2973e  ldrb r0,[r4,#0x4a]
29742  cmp  r0,r5
29744  beq  0x29766
29748  cbz  r5,0x29760
2974a..29754  clear state +0x38,+0x3c,+0x34,+0x30 and byte +0x49
29758..2975c  bl 0x29bf2
29760  strb r5,[r4,#0x4a]
```

So a rising bit-zero transition resets local transfer bookkeeping and enters
the lower helper `0x29bf2`; it is not a passive observation. The bounded
transition body contains no direct panel power, reset, sensing, or external
rail call. That does not exclude a lower or indirect side effect.

### `0x23`: break request

The `0x23` branch at `0x29a8c..0x29a90` reaches the common tail without a
request-specific local field store or helper call. This is not a claim that
the request is globally inert, because the common callback below is still
reachable.

## Shared callback and remaining safety boundary

All four paths converge at `0x29b1a`. If `[state+0x5c]` is nonzero, the code
calls it at `0x29b1c..0x29b2c` with the class context, request code, payload
pointer, and a stack-supplied argument. No table initialization tying this
slot to a concrete function was recovered in this bounded trace.

Accordingly the static evidence proves local CDC storage and a DTR-like state
transition, but does not prove whether a host serial open sends `0x22`, whether
the callback affects endpoint `0x81`, whether it controls logging, or whether
it has further hardware effects. It also does not establish that this package
is running or that the observed USB interfaces are currently bound to it.

No console/open procedure follows from this report.
