# Independent review: SSB target-`0x203` device read protocol

Reviewed 2026-10-27 UTC using the saved selected profile only. I ran the
provided checker with the retained Capstone path in both normal and `-O`
modes; both passed. I also independently decoded the receive callback,
validator, rearm helper, operation-3 dispatch, and the selected eMMC-read
leaf. No USB, TV, root, network, or firmware operation was made.

## CFG verdict

The bounded direction claim is correct for a received, validated header:

* the scatter-resident callback-table slot is Thumb `0x28cf1`, giving OUT
  completion VA `0x28cf0` / file `0x28ef0`;
* that completion copies header words from its header pointer to state
  `+0x0c` (target), `+0x04` (address), and `+0x08` (length) at
  `0x28f50..0x28f60`, before calling the validator at `0x28f68`;
* for accepted family-2 target `0x203`, the low operation is `3`, and the
  operation-3 branch at `0x2914e..0x29176` calls the read leaf `0x9bd4`;
  the distinct operation-4 branch begins at `0x291a8` and calls `0x9fe8`.
  The review found no fall-through from the `0x203` operation-3 branch into
  that write call;
* the selected leaf checks the low nine bits of both length and address,
  converts address with `>> 9`, places `0x58000000` in `r0`, and calls
  `0x16b70`. Its return is not tested before the next response-scheduling
  path at `0x2917a`.

Thus the report correctly separates target `0x203` from the adjacent write
operation and correctly preserves the integrity limitation: an IN payload is
not a proof that the leaf succeeded or that it came from a particular eMMC
object.

## Phase/rearm review: material limitation for a live one-chunk plan

The report establishes that the rearm helper `0x29500` posts a 12-byte receive
only when its state argument has `+0x0c == 6` and `+0x08 == 0`
(`0x29518..0x2952a`). The direct call census in the selected image found five
calls to this helper: `0x28bf0`, `0x28d44`, `0x28da0`, `0x28eb2`, and
`0x294dc`. Each visible nearby path sets state `+0x0c` to `6`; the callback
error/retry paths also explicitly clear `+0x08` before rearming.

This proves no prior **application command header** is needed by the rearm
helper itself: it consumes the existing state object and posts a fixed
12-byte OUT receive. It does **not** prove, from the package alone, that the
currently attached device has executed one of those arming paths, that its
vendor interface is configured/claimable now, or that no separate host has a
pending transfer. Those are live binding/phase prerequisites, not evidence
that a well-formed operation-3 header routes to write code.

There is a second bounded issue for the proposed 8,192-byte request: the
validator proves alignment and the `<16 MiB` family-2 range, but its recovered
body does not prove a maximum equal to the response-buffer capacity. The
separate Linux SSB backup path uses 8,192-byte chunks, which is useful stock
provenance, but this report does not prove that the current vendor callback's
response buffer is exactly 8,192 bytes. A proposal that treats the 8,192-byte
length as firmware-validated capacity overstates the present evidence.

Accordingly, this review is **clear on the selected protocol direction**, but
**HOLD on calling a direct 8,192-byte USBDEVFS one-chunk action ready solely
from this report**. A live plan needs an explicit preflight for current
interface/configuration/ownership and an evidence-backed response-size limit
or bounded transport behavior. This is a technical completeness hold, not a
claim that authorization is missing.

## No-erasure/reset claim scope

The reviewed selected operation-3 slice has no call to the adjacent operation
4 / `0x9fe8` write leaf, erase helper, reset helper, or USB CDC handler. That
is a statement about this exact received-header dispatch path. It is not a
global claim about all firmware, host interface-claim effects, controller
side effects, or live executable equality.

## Reviewed source identities

* `ssb-device-read-protocol-20261027.md`:
  `fb07c40ce744d964133aad1f361400f28e81d5c3bb9f938d580e873acab689c9`
* `ssb-device-read-protocol-20261027.py`:
  `995d1edf6cb3048345babf9029fae7d6ec1532de434caa8198cff21bfe75efbe`
