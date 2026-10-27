# Selected-profile CDC RX completion and consumer boundary

This is a static, offline trace of the selected profile's USB CDC receive
completion and re-prime path. No TV, USB, UART, network, or controller action
was performed.

## Result

The recovered CDC bulk-OUT path maintains an internal `USBSerial` circular
receive buffer and re-primes a 64-byte transfer. No direct call or literal
establishes a forwarding edge from its completion/worker machinery to the
controller-local UART command parser, its dispatcher, or its input ring.
The one generic-reader call in the surrounding CDC implementation interval is
the separately decoded TCDATA sampler, not a call from RX completion or worker
code.

This is not a whole-program absence claim. It does not exclude an unreviewed
computed callback, DMA path, or another firmware component. It does close the
obvious completion/worker and fixed-object route: no supported CLI or logical
memory-reader consumer is reached by the recovered CDC RX code.

## Pinned input and address map

Input: `overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin`,
5,242,880 bytes, SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.

For image 0, `linked VA = stored file offset - 0x200`; RAM values do not
shift. Thus RX completion VA `0x2960a` is file `0x2980a`, while RX worker VA
`0x29afc` is file `0x29cfc`.

## Object initialization and entry points

USBSerial initialization at file `0x22324..0x22390` is SHA-256
`ac0cbbee3f3088afe88c4541c0136a60778cfcfa4d8461c4720247ecb117a8b6`.
It allocates the `0x101`-byte (257-byte) RX buffer at state `+0x14`, records its capacity at
`+0x18`, and maintains TX state separately at `+0x28/+0x2c` (127-byte TX
buffer/capacity). The registration handle is stored through the sole retained
literal for RAM `0x20000638`, at file `0x223a4`.

The fixed USBSerial state literal `0x2026142c` occurs only at files
`0x22390`, `0x2b26c`, and `0x2b2f4` in image 0. These are initialization and
USB-side references; they are not a bridge to the UART parser or config
reader.

## Completion and re-prime dataflow

The first completion body is exactly VA `0x2960a..0x2966e` (file
`0x2980a..0x2986e`); the next function begins with `push` at VA `0x2966e`.
Its SHA-256 is
`f623ba9cd7ca4cd9906b0b2f199c65cebff282f83be7c36eb1eff93d8f7fe4a6`.
It updates the RX producer position at state `+0x1c`, handles empty/count
conditions, then performs circular/modulo handling before re-entering the RX
worker. The recovered direct branch at VA `0x29666` targets worker VA
`0x29afc`; no parser call occurs in that completion body.

RX worker VA `0x29afc..0x29ba1` (file `0x29cfc..0x29da1`) is SHA-256
`95f2b8b66c1a603d4d7b0d7868e5c387f0788086efc88be823b516408c725959`.
It uses the RX producer (`+0x1c`), consumer (`+0x20`), and limit (`+0x24`)
fields plus active flag `+0x48`, and submits at most `0x40` bytes to the bulk
OUT receive helper. Its complete direct-BL caller census is VA `0x29666`
(the first completion body), VA `0x2984e` (a distinct later callback), and
VA `0x29a02` (the receive wrapper). The latter two are not attributed to the
first completion function merely because they share nearby file space.

The receive state therefore proves buffer management and transfer scheduling,
not command decoding.

## Bounded consumer census

The static census covered the CDC mixed-code interval stored file
`0x28000..0x2c000` (SHA-256
`b547be2ba8996708bea037a519a7df368589a74669eb4ffa174b6638a20762f3`).
Within that interval there is no direct Thumb `BL` to:

| target | role | result |
| ---: | --- | --- |
| VA `0x16fc0` | line parser | absent |
| VA `0x17084` | parsed-command dispatcher | absent |
| VA `0x21084` | UART input-ring writer | absent |
| VA `0x637c` | configuration logical reader | one caller, VA `0x2a2f8`, the separate TCDATA sampler; not a completion/worker caller |

This is specifically a direct-edge census. It neither assumes that a global
like `0x20000638` is a parser nor treats lack of a direct BL as proof against
computed dispatch outside the reviewed range. The TCDATA sampler's existence
does not create a CDC-RX dataflow edge merely by residing in the same broad
file interval.

## Consequence

The retained code provides no basis to send a USB CDC command, to open a USB
serial endpoint, or to use the CDC RX buffer as a route to the AP_RTP/logical
reader. Existing control-line and receive-prime code can change transfer
state, so absence of a discovered consumer is not an authorization to probe
the interface.

Run `qd-usb-cdc-rx-consumer-20261027-checker.py` offline to verify the profile
hash, coordinate mapping, slice hashes, literal censuses, RX-worker callers,
and bounded direct-edge results.
