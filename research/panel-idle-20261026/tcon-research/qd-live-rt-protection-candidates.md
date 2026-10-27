# QD packaged-image live RT-protection candidates

Recorded 2026-10-27 UTC. This is a bounded offline trace of already retained
bytes. It made no TV, root, network, I2C, EEPROM, eMMC, GPIO, controller,
firmware-update, or display call and changed no prior evidence.

## Result

The packaged image contains two materially different ways to enter the common
error path with selector `0x10`:

* `0x99e8` is a pre-loop EEPROM-history check. Its two `0x10` entries consume
  four bytes previously stored at EEPROM-labelled address `0xe0`.
* `0x216d4` is a recurring runtime check. The main loop calls it on every
  pass; it tests bit 0 of common-object byte `+0x240a`, prints the exact
  literal `RT-P activate!`, and enters the same common path with selector
  `0x10` if the bit is set.

This is the first bounded source distinction between a stored-history
backstop and a live-polled selector source. The initiating writer of
`+0x240a` was **not recovered**. The bytes therefore establish a live polling
site, not the physical condition, detector, units, or electrical meaning that
sets its input bit.

The EEPROM path is also a consequence of a selector-`0x10` event, not merely
an independent detector. The selector action increments object counter
`+0x24ac`, mirrors it into EEPROM bytes 2 and 3, writes four bytes at address
`0xe0`, and verifies them. A later initialization pass reads those bytes and
can re-enter selector `0x10`. This is a persistent history/feedback path; it
does not show that EEPROM history initiated the original runtime event.

## Input and bounded method

```text
overnight/selected-qd-profile-copy-20261027b/
  F_RSM1_BN9659934B_COMMON.bin
size   5242880
SHA256 bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0
```

The first embedded Thumb image is linked at address zero. The audit:

1. decoded every halfword position in image 0 only to census direct `BL`/`BLX`
   encodings targeting `0xb860`, `0x14b10`, `0x2b964`, `0x99e8`, and the
   EEPROM helpers;
2. manually checked the surrounding basic blocks of every `0xb860` hit and
   recovered the constant selector reaching `r0`;
3. enumerated explicit fixed-offset references to `+0x240a`, `+0x2466`,
   `+0x2484`, `+0x24aa`, and `+0x24ac`;
4. followed direct callers and the backward loop at `0x39e4c`; and
5. checked the exact `0xe0` read, write, and readback-verify sites.

The direct-call census is not a whole-program CFG. Computed calls, addresses
synthesized at runtime, bulk structure copies, and separately linked image-1
code remain possible. A full-byte search found no stored 32-bit even or Thumb
function pointer for the relevant image-0 routines, but that does not exclude
such dynamic edges.

The independently reviewed internal-field-to-host-wire mapping is recorded in
`qd-profile-rt-wire-independent-review.md`, SHA256
`71972c04e8004a59307e08b261aac39774ce167e334aeeb93c254ad91d1eaf1e`.
This report does not duplicate the host serializer trace.

## Complete direct selector-`0x10` census

Image 0 contains 35 direct calls to common entry `0xb860`. All 35 decode in
coherent instruction blocks. Their immediately established selectors are:

| Selector | Direct call sites |
| ---: | --- |
| `0x10` | `0x9a34`, `0x9a62`, `0x216f2` |
| `0x00` | `0x131bc`, `0x132ea`, `0x13426`, `0x1cb70` |
| `0x01` | `0x22686` |
| `0x02` | `0x98b2`, `0x22620` |
| `0x04` | `0x2256e` |
| `0x08` | `0x1dfca`, `0x1e138`, `0x1e186`, `0x1e1d4` |
| `0x20` | `0x95f0` |
| `0x40` | `0x3b1c` |
| `0x80` | `0xd8e2`, `0x2e80a` |
| `0x400` | `0x5e52`, `0x609e`, `0x62d2`, `0x6488`, `0x6558`, `0x7148`, `0x7650` |
| `0x800` | `0xdde2` |
| `0x900` | `0x39c54` |
| `0xa00` | `0x70b8`, `0x70c4`, `0x70d0` |
| `0xb00` | `0x1c940`, `0x1cca0` |
| `0xc00` | `0x3e2a` |
| `0x2000` | `0x24eee` |

The only direct caller of action dispatcher `0x14b10` is `0xb8a0` inside
`0xb860`; the only direct caller of common-field setter `0x2b964` is `0xb8a6`
inside the same function. `0xb860` retains its original selector in `r5` and
passes that same value to both. Thus the three rows above are the complete
bounded set of direct selector-`0x10` entries into both downstream functions.

The relevant hashes match the retained image:

```text
0xb860..0xb8f9   40e434612828833aa7b433798a352a99c766cbb47351d2cb42ba364a868d2c6a
0x14b10..0x14bbb 5fcc7bea9301c9aa6b815a92fff05ac97769daf64e9eccbe1bac23f5667e3d18
0x2b964..0x2b979 3d538c104bca6958c66173c7d56a095ded57e9453134e78933ee6d0e26fffb03
```

## Pre-loop EEPROM-history producer

Function `0x99e8..0x9a69` (SHA256
`2846fcc6978d6bbcb1184a54c3334ace79a387275d5ca30e1bde14c7234a9ddc`)
reads four bytes at address `0xe0` through helper `0x9948`. Only after helper
success and equality of bytes 0/1 with RAM `0x20000c50[0:2]` does it:

* store halfword `1` at common object `+0x2466`;
* load byte `+0x24aa` and nonzero gate halfword `+0x2484`;
* enter `b860(0x10)` if the gate is nonzero and `+0x24aa < 2`;
* if EEPROM bytes 2 and 3 match, copy byte 2 to halfword `+0x24ac`; and
* enter `b860(0x10)` if that byte is at least `+0x24aa` and the gate is
  nonzero.

Its sole direct caller is `0x39d26`, in the pre-loop sequence. The immediately
following call at `0x39d2a` reaches `0x21738`, whose only two calls are
`0x594c` and `0x59dc`. Function `0x59dc` reads `+0x2466`; when it equals one,
it stores one at `+0x2442` and uses the exact literal
`[RTP] Correct RTP Fast Mode!! : RTP history + ONSEN Skip`. The `0x59dc`
function bytes (`0x59dc..0x5a03`) hash to
`49cc135c1a3cb278071705fce97e00115fc6261bcaf3175cc860ba10faf947c1`.

These direct edges place the four-byte EEPROM check and its success/history
flag before the recurring main loop. They do not establish the undocumented
units of either EEPROM byte or the configuration fields.

## Live-polled producer candidate

Function `0x216d4..0x21711` (62 bytes, SHA256
`6636bd288c51f566df590a89e48aabb761377a5da4a64d01e868a8fdee371049`)
does the following:

```text
get common object through 0xf194
load byte common+0x240a
test bit 0
if set: print literal `RT-P activate!` and call b860(selector=0x10)
```

Its sole direct caller is `0x39de8`. That call lies in block
`0x39dda..0x39e4b` (SHA256
`2b42697a77a696f72d4bf63cca89cd4a66333d0eb06231c7bd28fde5f16cce54`).
At `0x39e4c`, control branches back to `0x39dda`. Therefore the byte test is
on the recurring loop path, unlike `0x99e8` at `0x39d26`, which is before the
loop.

This proves a live-polled software input, with two limits:

* no other explicit fixed-offset reference to `+0x240a` exists in image 0,
  so the writer/source of the bit is not recovered; and
* after `b860` processes the selector, it returns only if two separate
  halfwords equal literal guards `0x1234` and `0xabcd`; otherwise it enters
  its generic emergency loop. Thus the source shows repeated *polling before
  a trigger*, not repeated returning detections after a trigger.

The literal `RTP_RDY` is used later in the same small function for a separate
condition reached after the selector test. That proximity does not identify
the `+0x240a` writer or justify expanding either stored acronym.

## EEPROM update is downstream history

The dedicated selector-`0x10` arm of `0x14b10` calls `0x9b68` before the
common selector field is stored. Function `0x9b68..0x9bfd` (SHA256
`72248d0305a3138c222077fd941bb1d0cad525ba6ccb1928e58998048c4252fc`):

1. reads the low byte of common object `+0x24ac`;
2. increments it and wraps a value above `0xfe` to zero;
3. stores the result into bytes 2 and 3 of the four-byte buffer at
   `0x20000c50`;
4. calls write helper `0x9990(address=0xe0, length=4, buffer=0x20000c50)`;
5. waits via `0x1de90(0x2710)`;
6. reads four bytes through `0x9948(address=0xe0, length=4)`; and
7. compares all four bytes, retrying up to ten times before the exact failure
   literal `RT-P EERPOM Write Verify Fail`.

The bounded explicit-field census is:

| Field | Explicit image-0 uses recovered | Bounded role |
| ---: | --- | --- |
| `+0x240a` | one byte load/test at `0x216dc`; no fixed-offset writer | live-loop trigger input; writer unknown |
| `+0x2466` | write `1` at `0x9a18`; read at `0x59ea` | successful EEPROM signature/history flag consumed pre-loop |
| `+0x2484` | reads at `0x9a24`, `0x9a56`; no fixed-offset writer | nonzero gate for both history checks |
| `+0x24aa` | byte read at `0x9a1e`; no fixed-offset writer | comparison value used by both history checks |
| `+0x24ac` | write from EEPROM byte 2 at `0x9a48`; byte read/increment at `0x9b78` | retained counter value mirrored back to EEPROM |

The absence of a fixed-offset writer is not a global absence claim: these
fields can be initialized by a bulk copy or computed address. It does prevent
labelling `+0x2484`, `+0x24aa`, or `+0x240a` as a specific physical threshold
or detector from the current evidence.

## Bounded conclusion

For the exact packaged image, the best live RT-protection discriminator is
not the EEPROM boot check. It is the recurring `+0x240a` bit-0 check at
`0x216d4`, which enters the exact common selector and host-wire status path.
The EEPROM bytes are demonstrably read during initialization and updated as a
downstream consequence of selector `0x10`, so they can preserve and reassert
history without identifying the initial live detector.

The separately linked second embedded image contains substantial `RTP`
scan-oriented code, but this audit recovered no direct cross-image call or
shared-field bridge from that code to image-0 `+0x240a`. Numeric address reuse
between separately linked images is not a cross-image edge. No claim is made
that image 1 sets this bit, that the bit represents an electrical quantity,
that either embedded image was running unchanged, or that this path caused
the owner's sparse-menu blackout.
