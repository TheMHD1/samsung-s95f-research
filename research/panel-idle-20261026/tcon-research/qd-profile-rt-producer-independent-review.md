# Independent review: selected QD profile RT-protection producer lead

Recorded 2026-10-27 UTC. This review is bounded to
`qd-selected-profile-content.md` (17,350 bytes, SHA256
`e2dcdd78576032d2a250d388cbc55f40950f961238ce426bd5c9b961a4a40beb`)
and the already retained regular file
`overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin`
(5,242,880 bytes, SHA256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`).
It made no TV, root, network, controller, I2C, updater, firmware or display
call and modified no prior evidence.

## Review outcome

The report's main byte-level conclusion is supported: the selected QDF-matched
asset contains executable Cortex-M/Thumb content and a real, referenced
RT-protection error path whose selector is exactly `0x10`. This is materially
closer to the accepted host `0x10` than the separate RHEA/internal-TCON 2 MiB
startup identity.

It is not yet an end-to-end producer proof. No reviewed instruction maps the
firmware's internal selector field to the four bytes returned by the host's
`F3 80 00 00 00 08` query, and no retained evidence proves that these packaged
image bytes are the bytes currently executing. The content report preserves
both limits. There is no material blocker in its current conclusion.

## Independently checked facts

### File identity and executable classification

The full-file size and SHA256 reproduce exactly. Repeating the report's
conservative aligned vector scan over all bytes found exactly two candidates:

| Stored offset | initial SP | reset vector | plausible following vectors |
| ---: | ---: | ---: | ---: |
| `0x200` | `0x20020000` | `0x00000345` | 15/15 |
| `0x40200` | `0x20020000` | `0x00000369` | 15/15 |

Both odd reset vectors decode into coherent Thumb startup code. The first
image's exact banner/build/QD-display strings and the second image's fault and
RTP strings corroborate, rather than independently establish, that executable
classification.

The retained acquisition provenance is internally consistent: manifest
SHA256 `39ad1db84bfa64d2bad8928b80da5b9bb1b92b12398a0dc2c6ad756a3905a706`
and runtime-audit SHA256
`42b46c851fd266f4f3e673a910f840be60ab0bd5031f77036e539ddea8050d99`
bind the copied bytes to the ordinary factory-data file. They do not bind the
packaged image to a current controller flash.

### EEPROM-labelled RT path

Manual Thumb decoding reproduces the reported `0x99e8..0x9a69` body and its
SHA256 `2846fcc6978d6bbcb1184a54c3334ace79a387275d5ca30e1bde14c7234a9ddc`:

* `0x99f0..0x99f6` passes output buffer, length 4 and address `0xe0` to
  helper `0x9948`.
* A nonzero lower return or a mismatch against two signature bytes at literal
  RAM address `0x20000c50` exits without entering the error path.
* A match stores halfword 1 at object `+0x2466`.
* Gate `+0x2484 != 0` plus byte `+0x24aa < 2` calls `0xb860` with
  `r0=0x10` and exact text `EEPROM Check RT Protection`.
* Returned bytes 2 and 3 must match before byte 2 is stored as a halfword at
  `+0x24ac`; when that byte is at least `+0x24aa` and the same gate is nonzero,
  the second `r0=0x10` call carries exact text
  `EEPROM Check RT Protection Max count`.

The helper `0x9948..0x998b` also reproduces: low 16 address bits become the
two-byte address, bits 16..17 modify base device byte `0xa0`, and the caller's
buffer/length reach lower function `0x12df8`. This identifies the firmware's
EEPROM-labelled access construction, not the actual external storage device or
meaning/units of the four bytes.

### Selector handling

Manual decoding also reproduces all three important downstream bodies:

* `0xb860..0xb8f9` preserves the incoming selector, calls `0x14b10`, then
  calls `0x2b964`, and logs an `err_src` description.
* `0x2b964..0x2b979` uses `BFI` to replace the low 16 bits of object field
  `+0x10` with the selector.
* `0x14b10..0x14bbb` has an explicit `selector == 0x10` branch at
  `0x14b4a..0x14b70`; that branch clears a halfword, invokes lower handlers,
  stores literal `0x10` in another state field and calls two more routines.

For precision, the field at object `+0x10` is proved to be a retained
selector/error-source field. Calling it the exact host-visible status mask
would require the still-missing serialization/response-reader edge. The
content report already states that boundary, so this is a terminology guard,
not a correction to its conclusion.

One behavior deserves explicit retention when this path is interpreted later:
after the common entry has performed those selector operations, `0xb8c2`
checks two magic halfwords. Unless they are `0x1234` and `0xabcd`, the body
enters the loop at `0xb8dc..0xb8f8` and repeatedly invokes several handlers.
That supports treating this as substantive error/protection handling, but the
lower routines and physical effect of the loop are not recovered here.

### Reachability within the packaged image

The instruction at stored address `0x39d26` is a valid direct Thumb `BL` to
`0x99e8`. It lies among a coherent series of direct initialization calls in
`0x39cf2..0x39d3d`, whose reported SHA256
`4ed212a0286c80b4c67578224fed538bc106c77b32269fe38c4fa36e0ab4af5e`
reproduces. This establishes a packaged-image call edge. It does not prove
that the initialization sequence ran on this boot.

## Identity and causality boundary

The separately reviewed host identity path matters to interpretation:

* QDF FW/MD and the RT-status query are on the external QDF I2C route at
  adapter 5/address `0x76`.
* `Int.Tcon` FW/DATA and the `RHEA_M_TCON_FW` log are on the separate
  `sdp_tcon` shared-memory/message-box route.
* The selected 5 MiB asset uniquely matches the retained QDF FW/MD tuple and
  now contains an actual QD controller-oriented executable plus the selector
  `0x10` RT path.

That combination makes this asset the stronger layer-correct producer lead.
It still does not prove live installation or that selector `0x10` is serialized
into the `F3:08` response. Numeric equality and exact RT-protection text are
strong correlation, not permission to merge the two states.

The following remain unsupported:

* EEPROM history/count is the event that occurred during the owner's blackout;
* the EEPROM bytes identify a panel defect, temperature event or repairable
  threshold;
* the selector branch turns emission off, resets a module, or is safe to
  suppress;
* image 0 or image 1 is currently executing; or
* any recovered constant should be written, patched, cleared or replayed.

The smallest remaining static question is the firmware-side command parser or
status serializer that serves host command `F3:08`. Until that edge is
recovered, no new controller read/write, firmware apply or protection bypass
is justified by this review.
