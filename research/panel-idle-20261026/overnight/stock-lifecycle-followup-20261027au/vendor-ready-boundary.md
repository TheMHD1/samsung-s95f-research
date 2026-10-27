# Vendor-header readiness after a stock lifecycle

Recorded 2026-10-27 UTC. This is a bounded offline follow-up to
`readiness-review.md`. It used retained package, backup, module, and trace
files only. It made no TV, root, network, USB, I2C, GPIO, reset, command,
firmware, or target operation.

## Result

The firmware source positively closes the **normal initialization-to-header
submission control-flow edge**. In both the selected `241230A` image and the
recovered stored `241205A` image, the vendor configuration callback:

1. initializes the vendor state to operation `6` and remaining length `0`;
2. installs the header-buffer pointer;
3. chooses the transfer cap; and
4. calls a rearm helper which submits an exact 12-byte receive on bulk OUT
   endpoint `0x02`.

That is the firmware's initial idle/header state plus `ReadyForHeader`
*submission intent*. It does not prove the live post-MODE2 endpoint is armed.
The rearm helper's receive-submission return is not tested, and the
configuration callback returns zero regardless. Consequently USB
re-enumeration, configuration value 1, same-image source provenance, an
unbound host interface, and no known competing bulk client do not positively
establish that the controller accepted the receive descriptor.

The missing fact is narrow: a live, fresh-instance indication that vendor OUT
endpoint `0x02` has an active 12-byte receive for the header buffer, or an
already completed exact vendor request on that same post-reset instance. A
host descriptor/open/claim check observes host state, not that firmware queue.
The first attempted header is not a non-consuming liveness check. There is,
however, an important safety distinction: under the positive premises that
this same-image configuration callback executed and no vendor OUT occurred
afterward, initialized `operation=6 / remaining=0` and the installed header
pointer rule out a pre-existing write-payload phase. A failed OUT can still
leave liveness or completion ambiguous, but it cannot be reclassified as a
prior operation-2 payload without violating those premises.

Thus blocker 3 in `readiness-review.md` is **narrowed but not closed**.

## Selected-image initialization path

Image 0 uses `FILE = VA + 0x200`. The selected package is 5,242,880 bytes,
SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.

The ordinary startup body calls vendor initializer VA `0x2490c` at VA
`0x39a16`. The initializer writes endpoint numbers `0x82` and `0x02` at
`0x24920..0x24928`, obtains the USB-core and descriptor tables, and registers
them through VA `0x28b36` at `0x2495a`. Its reset-scatter vendor class table
at RAM `0x2000058c` begins with Thumb configuration callback `0x2945d` and
contains OUT completion callback `0x28cf1`.

The USB-core broadcaster VA `0x28448` walks registered classes and invokes
slot `+0` of each active class table. Vendor callback VA `0x2945c` then makes
the readiness state explicit:

| VA | store/action |
| ---: | --- |
| `0x29492..0x294a0` | install header-buffer pointer plus 12-byte offset bookkeeping |
| `0x294b6` | state `+0x04 = 0` |
| `0x294b8` | state `+0x08 = 0` (remaining) |
| `0x294ba..0x294bc` | state `+0x0c = 6` (completed/idle operation) |
| `0x294be..0x294c0` | state `+0x1c = 1` |
| `0x294c2..0x294d6` | choose cap `0x200` or `0x6000` |
| `0x294dc` | call rearm VA `0x29500` |

Rearm VA `0x29518..0x29520` requires operation `6` and remaining `0`.
VA `0x29522..0x2952a` then passes endpoint, header pointer, and exact length
`0x0c` to OUT receive scheduler VA `0x7fce`. It does not inspect that call's
return; it immediately returns. The configuration callback likewise returns
zero at `0x294e0`.

This is stronger than merely finding endpoint constants: a successful path
through the callback reaches the exact 12-byte submission. It is weaker than
proving that the endpoint controller retained an active descriptor.

## Parser-phase safety versus endpoint liveness

The selected OUT completion callback makes the phase discriminator explicit:

- VA `0x28d22..0x28d30` loads state `+0x08` (remaining). If it is zero, the
  callback enters header parser VA `0x28f24`.
- Only a **nonzero** remaining value branches to payload accounting at VA
  `0x28d66`, where completed bytes are subtracted and state `+0x04` advances.
- The parser reads the three header words through installed state pointer
  `+0x10` at VA `0x28f50..0x28f60`.
- A valid fixed target-`0x101` header normalizes to operation 1. VA
  `0x290f6..0x29106` schedules USB IN directly from the requested address.
  It does not enter the separate operation-2 OUT-payload branch beginning at
  VA `0x2912a`.
- A rejected header returns parser result 2; VA `0x28d34..0x28d44` restores
  operation 6, remaining 0, and attempts the 12-byte rearm again.

Therefore, under all three source premises below, a first fixed read header
has no ordinary path to a target-memory write:

1. the selected-image vendor configuration callback actually executed on the
   fresh instance;
2. its state stores completed before the first host OUT; and
3. no other vendor OUT transaction intervened.

The bounded failure envelope is then:

| outcome | firmware interpretation supported by the source | host disposition |
| --- | --- | --- |
| initial rearm did not create a live receive | no header callback; OUT can stall, time out, or fail | stop; endpoint liveness remains unproved |
| header receive is live and exactly 12 bytes complete | parse target `0x101`, schedule IN; no write-payload phase | perform only the fixed matching IN; exact completion can re-establish the host model |
| fewer than 12 bytes reach header completion | validator rejection and idle/rearm attempt; no operation-2 target write | stop anyway because host/callback completion is not positively bound |
| transfer reports an error or timeout after ambiguous lower progress | header-buffer progress or callback timing is unknown, but the initialized state supplies no prior write destination | stop with no retry or later header |
| any premise above is not proved | current parser phase is genuinely unknown; a pre-existing operation-2 payload cannot be excluded | this source argument does not permit the attempt |

This is a source-level wrong-phase bound, not a live-state observation. In
particular, it does not claim that a timed-out transfer accepted no bytes, that
release cancels firmware state, or that the configuration callback executed
merely because a host descriptor is visible.

The terminology must remain separate:

- **firmware idle/header state** means state `+0x0c = 6`, `+0x08 = 0`, and
  the header pointer installed;
- **firmware header posted** additionally means the endpoint controller
  accepted the exact 12-byte OUT receive; and
- native **`ReadyForHeader`** is host state-machine bookkeeping: initially a
  reviewed precondition, and after an exact read pair a conclusion of that
  invocation. It is not a register read or direct observation of either
  firmware condition.

Thus guaranteed endpoint liveness is not logically required to bound one
fixed read attempt against wrong-phase writes. Positive execution of the
configuration stores and absence of intervening bulk traffic are required.
Those premises still need runtime evidence; the package source alone does not
turn them into facts about a future MODE2 instance.

Relevant selected-image slice hashes are:

| role | VA / bytes | SHA-256 |
| --- | --- | --- |
| startup window | `0x39a00 / 0x1a` | `1be8eb4f97bb2028d3ffe93a61dc0566e5021eeaae5044dd55af294752dbe722` |
| vendor initializer | `0x2490c / 0x58` | `fe0614e38e5ba9a93ea7b9e7f6713407c9f2abdc4fcce28d11448c8baee41ae2` |
| class broadcaster | `0x28448 / 0x4a` | `c4f064a989b3b50c08d280832b60792021494ac45e7b1ec65691a7981c46ff3b` |
| vendor configuration | `0x2945c / 0x88` | `7d0acce7e777be885ce0e87c205580f21a204dc38800d1d58a633405dda25748` |
| rearm helper | `0x29500 / 0x34` | `19b640cf59ed8e61dbefe6e4d59ce3188f4d20be75e9d8d432bd483ada39561f` |

## Recovered-backup corroboration and runtime boundary

The full recovered backup is 5,242,880 bytes, SHA-256
`f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562`.
Its image-0 code is an older generation, so selected-image absolute VAs must
not be applied to it. Independently decoded equivalent edges are:

| role | stored-generation VA | decisive edge |
| --- | ---: | --- |
| startup | `0x3977e` | calls initializer `0x2468c` |
| vendor initializer | `0x246a0..0x246a8` | stores endpoints `0x82/0x02` |
| class broadcaster | `0x281ac` | invokes active class slot `+0` |
| vendor configuration | `0x291c0` | configures the vendor state |
| state idle/remaining | `0x2921a..0x29220` | stores `+4=0`, `+8=0`, `+0xc=6` |
| rearm call | `0x29240` | calls `0x29264` |
| exact receive | `0x2927c..0x2928e` | checks `6/0`, submits length `0x0c` |

The current-generation callback initializer differs from this older stored
one. A retained live RAM read instead matched all six nonzero selected-image
vendor callback pointers, including configuration `0x2945d` and OUT completion
`0x28cf1`. This is positive active callback-generation evidence, but not a
whole-code or immediate post-reset endpoint-queue measurement. Later exact
vendor transactions after the historical MODE2 show that the interface
eventually reached a usable header boundary; they do not prove the boundary
existed before the first post-enumeration request.

## Stock MODE2 traffic boundary

The copied `qdf_tcon.ko` is SHA-256
`97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63`.
Its bounded undefined-symbol census contains four QDF I2C entry points
(`tztv_i2c_read_common`, `tztv_i2c_read_raw`, `tztv_i2c_write_common`, and
`tztv_i2c_write_raw`) and no undefined name containing `usb`, `ssb`, or
`bulk`. Its MODE2 body calls the reset callback, which causes the observed USB
disconnect/re-enumeration, while its normal-on status/frame/replay tail reaches
the QDF I2C command transport.

The historical retained action agrees: after enumeration it recorded 346
complete PID-9931 transfers, all on I2C bus 5/address `0x76`, covering checks
and cached-setting replay. No retained row positively identifies a vendor
bulk consumer or SSB bind in that normal tail. The separate Linux SSB module
can be an active vendor-bulk client if it binds, but the retained interface
samples were unbound and the MODE2 window contains no identified SSB
probe/bind row.

This supports “no **known stock MODE2 vendor-bulk consumer**,” not a
whole-system absence theorem. The trace did not prove every possible URB,
another process could be unrecorded, and a silent or computed client is not
excluded merely by the QDF symbol census.

## Exact remaining readiness boundary

A source-backed same-image fresh initialization plus positive configuration
callback execution proves the safe idle/header state and an attempted initial
12-byte receive. Adding a bounded no-competing-client fact protects the
no-prior-payload premise. It still does not turn that attempt into a completed
queue-state observation because the submission result is discarded.

Any future execution review therefore still needs one of these positive
bindings on the newly enumerated instance:

- a source-supported, read-only endpoint/descriptor state showing endpoint
  `0x02` owns an active 12-byte receive at the vendor header buffer; or
- an exact completed vendor transaction whose terminal callback rearmed the
  next 12-byte header, with exclusive-session lineage carried forward.

The second option proves liveness/readiness only *after* that completed
transaction. It is not required for the narrower conditional conclusion that
one fixed read header cannot become a prior write payload. That narrower
conclusion instead requires positive same-image configuration execution and
no intervening vendor OUT. If either premise is only inferred from USB
enumeration or source bytes, parser phase remains a live evidence gap and the
argument does not clear an attempt.

## Retained evidence pins

- `readiness-review.md`: `37ef1bb63643ead88549e8f6ce101a1ab037db5e3f2d64c0ffcc9e5c9113e2fb`
- `ssb-device-read-protocol-20261027.md`: `6bafcfb45e95b18a3646b71e5da37a43df4a863e6368e57dfb808e139da7021c`
- `ssb-mode-gate-followup-20261027.md`: `1d0539352a82a6c51a5b084de5d42fc8c272f1a3ca6b821b217bb75add680c9c`
- `qd-power-control-hardware-sequence.md`: `01cb7aa76093d74b4ccd8124a667f0d0e58c68fdde6270a010445e57606f319d`
- `stock-mode2-transport-audit.md`: `70b0d0f2f7a8301d2b598d45a3510a4304bd493c2e7507e0bb1c8f270baf8847`
- callback initializer record: `6dc11008595816ed87252bbea0378caa9a76b496b0787746d7e5066b322f6322`

No new request, reader, collector, probe, or patch is proposed by this report.
