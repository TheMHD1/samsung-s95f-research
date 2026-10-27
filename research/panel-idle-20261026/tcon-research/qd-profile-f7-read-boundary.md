# Selected-profile `F7` read boundary

Recorded 2026-10-27 UTC. This is a bounded offline analysis of the remaining
`F7` protocol family in the retained selected QD profile. It made no TV,
root, network, controller, I2C, EEPROM, MMIO, getter, or display call and
changed no prior evidence.

## Result

The packaged controller's `F7` transmit dispatcher is finite and small. It
recognizes exactly three read commands:

| command | valid byte indices | returned source |
| ---: | ---: | --- |
| `f700` | `0..1` | protocol checksum byte at RAM `0x20000cb9`; low byte of common-object halfword `+0x152` |
| `f720` | `0..1` | the same two sources as `f700` |
| `f740` | `0..30` | 31 bytes from response RAM `0x20015180` |

Unknown commands and out-of-range indices return zero. The transmit function
does not read MMIO and does not expose an arbitrary address, firmware window,
or the fixed image-0 object.

The `F7` family as a whole is **not a passive read family**. Its receive path
dispatches `f700` and a finite set of `f701..f716` commands into state-changing
handlers; it also has an explicit `f730` no-op case. Those handlers update the
common object, response buffer, and in some cases MMIO or other internal
state. `f740` reads the transient result buffer that these operations build.

No immediate writer of that result buffer copies the saved RT fields at
image-0 object offsets `+0x2466`, `+0x2484`, `+0x24aa`, or `+0x24ac`, nor the
live RT-related `+0x240a` field. The apparent checksum bytes are byte sums of
the current protocol command/value or response, not a firmware-image
checksum. No firmware identity string or full-image digest is exposed.

Therefore `F7` does not supply an additional source-backed, read-only RT
history or firmware-identity diagnostic. No command or invocation is
proposed.

## Exact input and address convention

| Input | SHA-256 |
| --- | --- |
| `overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin` (5,242,880 bytes) | `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0` |
| `qd-profile-rt-status-wire.md` | `6c532e2ad8a48041cf83ebddfa42af1282019d14169902b47e621f6a1c237f6e` |
| `qd-profile-readonly-rt-state-selectors.md` | `cde271e73dc03bafb950862df9ec3fe1a0323463c770b236cb5aa087bf5a4de8` |
| `qd-profile-open-register-read-route.md` | `c50aee500fd8ff69000e0ae7c59dec72b4097062d350b2b93fdb19e8643ef27c` |

The first embedded Thumb image is linked at zero, so the code addresses below
are also file offsets. Packaged-image identity does not prove current
controller-flash identity.

## Parser routing

The already reviewed I2C state machine is `0x12ac4..0x12dbd`, 762 bytes,
SHA-256
`5b2cbcbac9d03ba3a1dd175568a5cbc8cb7e74a75264a17fd354833d1f4e9c85`.
Classifier `0x12a9a` assigns first byte `0xf7` to parser mode 1. The first two
received bytes form the 16-bit command halfword at RAM `0x200008c8`.

On receive, the mode-1 branch at `0x12c2a..0x12c44` waits for its exact
receive-counter state, then passes the command and assembled halfword value
to action dispatcher `0x1eee4`. On transmit, the mode-1 branch at
`0x12d24..0x12d40` passes the command and successive byte index to read
dispatcher `0x1f608`; each returned low byte is placed directly in the I2C
data register. This is a byte-stream response, not the four-byte word
serialization used by `F3:80`.

The parser updates command/value/index/count RAM as part of either direction.
Those bookkeeping stores alone prevent describing the transport as having
literally no controller-state effects.

## Complete transmit dispatcher

Function `0x1f608..0x1f65b` is 84 bytes, SHA-256
`2ae7a0bb909b54b67268f938d7456961ceb7a60a908794ffe15bc767241f1d51`.
Its complete command logic is:

```text
f700 or f720:
    index 0 -> byte [0x20000cb9]
    index 1 -> low byte of halfword [common_object + 0x152]
    other   -> 0

f740:
    index 0..30 -> byte [0x20015180 + index]
    other       -> 0

all other commands -> 0
```

The function calls only the common-object accessor `0xe870`; it contains no
store and no MMIO load. This local fact does not make preceding `F7` actions
non-destructive.

### `0x20000cb9` is a protocol sum, not image identity

Immediate writer `0x1fc9c..0x1fcab` is 16 bytes, SHA-256
`2d6b0d806ef0165abd6351365aac55fe431b29af460247531139701e768ea0f2`.
It computes, modulo the stored byte width:

```text
command_low + command_high + value_low + value_high
```

and stores that result at `0x20000cb9`. The `f700` receive case separately
stores the high byte of its supplied value at `0x20000cb8`. Thus read index
zero is protocol bookkeeping for the current command/value exchange. It is
not a CRC or checksum over either embedded firmware image, the 5-MiB profile,
EEPROM, or RT history.

### Common-object `+0x152` is action status

The receive/action code repeatedly writes small status values to the
halfword at common-object `+0x152`: values observed in the bounded dispatcher
and its immediate actions include 1, 2, and 4. For example, an unrecognized
or rejected action sets 4, while several accepted action paths set 2 during
processing and later 4. The transmit dispatcher returns only the low byte.

This is a state-machine status field. No decoded path aliases it to the RT
EEPROM record or current error-selector halfword `common_object+0x10`.

## The 31-byte `F7:40` result buffer

Response RAM begins at `0x20015180`. Immediate reset helper
`0x1eed4..0x1eee3` is 16 bytes, SHA-256
`7276da33f6172e31b583e5e11610dcb89473997ab0cb5bc3722b1abfdde188dc`.
It calls the firmware's memory-fill helper with length `0x23`, clearing 35
bytes before the action dispatcher builds a response.

Response checksum helper `0x1efd4..0x1eff1` is 30 bytes, SHA-256
`0f9c85389f2b5e0bed86756031ba6286b232bfac3e5c756d8971985557ca3e0d`.
For an action-supplied response length, it sums response bytes beginning at
offset 1 and stores the low byte of the sum at offset 0. This again is a
packet-local additive checksum, not a firmware digest.

The transmit dispatcher exposes only offsets `0..30`, even though the reset
clears 35 bytes. Literal-reference and immediate-writer review of this buffer
shows the following bounded roles:

* byte 0: packet-local additive checksum;
* byte 1: low command/subcommand identifier written by the dispatcher or a
  response builder;
* byte 2: response length/type/status used by individual action handlers;
* later bytes: action-specific status, measurement, or fixed response bytes;
* unwritten bytes remain zero after the 35-byte reset.

Examples include a six-byte measurement response built by `0x1fcb0`, small
boolean/error responses built by `0x1ee84`, `0x1fc74`, `0x1fddc`, and
`0x2018c`, and a bounded multi-byte status response near `0x20420`. These
examples establish that the buffer is a transient command/result envelope;
they do not assign meanings to every action-specific byte.

No immediate buffer writer loads from fixed object offsets `+0x240a`,
`+0x2466`, `+0x2484`, `+0x24aa`, or `+0x24ac`. One action obtains the fixed
image-0 object and **writes** literal one to `+0x2400`; it does not copy that
region into the response. No buffer writer walks executable memory, computes
a whole-image digest, or copies a firmware version string.

## Receive side is an action/control dispatcher

Function `0x1eee4..0x1efc5` is 226 bytes, SHA-256
`bdf186399bea803b7ec43d700238ad147607d89e43f56233ba1bc3a9edb2917e`.
Its bounded command behavior is:

* `f730`: immediate return with no action in this function;
* `f700`: updates protocol bookkeeping through `0x1fc9c`, clears the result
  buffer, records the command, and stores part of the supplied value;
* `f701..f716`: after bookkeeping/handshake checks, a 22-entry table invokes
  handlers for `f701`, `f702`, `f703`, `f708`, `f709`, `f70b`, `f70c`,
  `f70e`, `f70f`, `f714`, `f715`, and `f716`;
* the remaining entries in that range and commands outside it set action
  status 4 rather than exposing a read address.

The dispatched handlers are materially active. Within the immediate bounded
set they write common-object state, build/clear response RAM, snapshot and
restore hardware-related values, and include explicit stores to addresses in
the `0x58xxxxxx` range. This is enough to classify the receive family as
control/action capable without assigning undocumented hardware meanings to
those addresses.

Because the action path precedes the result-buffer read in the protocol's
intended exchange, `f740` must not be treated as a freestanding harmless
memory-dump primitive. Static code does not establish that reading a stale
buffer is useful, fresh, or free of surrounding protocol effects.

## RT and firmware-identity exclusion

The prior reports source-bound the packaged RT fields as:

| fixed image-0 object offset | established role |
| ---: | --- |
| `+0x240a` | live RT-related producer input retained for separate analysis |
| `+0x2466` | EEPROM signature/check-complete flag |
| `+0x2484` | RT gate |
| `+0x24aa` | threshold/history byte |
| `+0x24ac` | saved EEPROM count/value |

The complete transmit dispatcher reads only `0x20000cb9`, common-object
`+0x152`, and response RAM `0x20015180..0x2001519e`. Its immediate response
producers do not copy any of the five fixed-object fields into those sources.

Likewise, neither checksum helper reads the selected profile or executable
images. One adds four command/value bytes; the other adds a bounded response
packet. Calling either a firmware checksum would be incorrect.

## Conclusion and limits

`F7` supplies a finite byte-oriented action/result protocol, not an
additional read-only diagnostic namespace. It does not expose saved RT
history, the live RT field, a full controller firmware image, or a firmware
identity checksum in the recovered paths.

This conclusion is bounded to the exact packaged image, the complete
`0x1f608` transmit dispatcher, and immediate sources/writers of its three
returned regions. Deeper semantics of every action handler, undocumented
MMIO meanings, current-flash equality, and any alternate firmware image
remain unresolved. No arbitrary register guess, controller command, status
read, or control action is constructed or recommended.
