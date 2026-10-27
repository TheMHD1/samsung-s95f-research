# AP_EXCO ordinary-input snapshot plan (offline)

Date: 2026-10-27 UTC. This is a source/build plan only. No target operation was performed while producing it.

## Fixed acquisition

One native invocation performs, in this order, three fixed target-`0x101` reads:

| Purpose | Bus address | Bytes | Fixed header |
| --- | ---: | ---: | --- |
| pointer anchors | `0x470002c0` | 32 | `01010000c002004720000000` |
| ordinary AP_EXCO prefix | `0x4500ff14` | 824 (`0x338`) | `0101000014ff004538030000` |
| derived AP_EXCO object | `0x450158a8` | 1004 (`0x3ec`) | `01010000a8580145ec030000` |

The native engine sends one exact 12-byte header and receives one exact data response for each request: six bulk calls total. There is no write, reset, retry, caller-selected address, dynamic pointer dereference, UI action, or storage operation.

The first response must contain `0x4500ff14` at response offset `+4` and `0x450158a8` at `+0xc`. Either mismatch is a content rejection in a known protocol-ready state: the raw 32-byte pointer response is retained and no dependent request header is sent. An exact first anchor does not prove a global `0x47...` CPU alias or whole-core identity; it only admits the two prequalified fixed dependent windows.

The ordinary object has a positively qualified allocated extent of `0x33a` (826) bytes. The read deliberately captures the aligned prefix `+0..+0x337`, 824 of 826 bytes, and never pads past the allocation. The derived object read covers its qualified `0x3ec`-byte extent exactly.

## Decoded fields

All raw windows and their SHA-256 digests are retained. The wrapper also decodes these bounded fields:

- ordinary `u16`: `+0xca`, `+0x116`, `+0x10a`, `+0x10c`, `+0xe6`, `+0x2fc`, `+0x300`, and `+0x302`;
- derived bytes: `+0`, `+1`, and `+0x3d8`.

The ordinary helper can write the `+0x10a/+0x10c` pair when ordinary `+0x116` is nonzero; the packaged initializer has `+0x116 == 1`. Therefore an initializer value of zero for that pair is not evidence that the runtime bit-1 condition is false. The retained snapshot includes the gate, pair, two counters, and helper outputs so later analysis does not make that invalid inference.

The wrapper recomputes `bool((ordinary[+0xe6] & 1) or ordinary_u16[+0x2fc])` and reports whether it equals derived byte `+0x3d8`. This is only a comparison among sequentially acquired current-state samples. The three reads are not atomic, do not recover the V6 event-time tuple, and do not establish physical panel cause, mode semantics, or a changing value's temporal order.

## Failure and cleanup contract

- A short, over-count, timeout, transport exception, or disconnect makes the native protocol phase unknown. No later USB request or retry is issued; only best-effort interface release and descriptor close occur.
- Each exact raw response is attached to the native outcome immediately after its exact receive, before any later transfer. A later failure cannot erase earlier exact bytes from the retained native stdout.
- The host marks target-operation accounting as unknown/in-flight before the one native execution.
- Target-stage cleanup is allowed only after a strict terminal envelope, zero native exit, empty stderr, exact Ready phase, all three raw lengths/hashes, both pointer anchors, all ten lifecycle/transfer rows, release, and close have been validated.
- Any rejected, partial, ambiguous, or framing-failed outcome leaves the private stage and authenticated host record for deliberate follow-up. There is no automatic retry.

The helper remains dry by default. Only root, after independent source/build review and an exact manifest pin, may authorize a later live invocation.
