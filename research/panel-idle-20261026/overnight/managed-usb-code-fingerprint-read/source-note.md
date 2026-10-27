# Fixed selector-1 code-window reader

Recorded 2026-10-27 UTC. This directory is an offline-only, mechanically
bounded derivative of the reviewed `managed-usb-ap-exco-source-read` helper.
It has not been run against the TV. It does not write, reset, retry, launch a
UI action, patch code, or accept runtime addresses from the command line.

## Fixed geometry

The native helper performs exactly three target-`0x101` memory-IN requests,
in this order, with one exact 12-byte OUT header and one exact-length IN for
each request:

| mapped bus address | bytes | header |
| --- | ---: | --- |
| `0x46001e60` | `512` | `01010000601e004600020000` |
| `0x460038c0` | `64` | `01010000c038004640000000` |
| `0x4601bb60` | `576` | `0101000060bb014640020000` |

Each exact response is serialized and hashed before the next request. Any
uncertain or non-exact transfer stops all later requests. There are no
retries. Release/close still occur when reached; cleanup is allowed only
after the retained result proves all six bulk transfers completed and the
protocol returned to `ReadyForHeader`.

## Content comparison is not transport acceptance

The exact selected-package expectations are:

| window | expected SHA-256 |
| --- | --- |
| A | `8be303fddfa4aefd0f2d307f05c7522213f8017ae15b374a4fd7178aeca2bb49` |
| B | `0483a632a5e65f8eba8bd623411d6f955705d012c831eac9347e7f9564d944cb` |
| C | `035d13a7c17ac9b303ee5739a421a84d0ceec46167d6efce13f4723fc701d9b8` |

Every returned window is retained whether it matches or differs. A mismatch
does not reject an otherwise complete transport result and does not trigger
a different-address guess. The host independently recomputes each hash and
byte comparison before cleanup.

## Source qualification and hard limits

The independent offline mapping report
`code-map-qualified-followup-20261027n/code-map-qualified-followup.md`
(SHA-256
`d14282ce16dac0b6a594bfdcce078170d28264c54c515f3b02ad670477901c2a`)
pins mapper VA `0x1bb74`: for a nonzero selector and a nonzero linked address
below `0x20000`, it returns `0x46000000 + address`. All three windows stay
inside that domain. The corresponding verifier SHA-256 is
`6f645c0bc6fc90f92c4f3180a053a1be6d47734fcaf7eb234a9906f5322ca11c`.

That positive mapping does **not** prove selector 1 identifies the currently
executing stored image-1 component. The bounded stored startup census instead
uses selector 0. Even three exact matches prove only the bytes returned by
the selector-1 mapped view at three non-atomic acquisition points. They do
not prove a core executed those bytes, whole-image identity, writable-code
qualification, fault-time execution, a physical blackout, or a repair.

No target execution is cleared by this directory alone. Independent review
of the final implementation, manifest, and address/source report is required
before any live read is considered.
