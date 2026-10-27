# Independent review of the delayed post-lifecycle X observation

Recorded 2026-10-27 UTC. This was a read-only audit of finalized local
artifacts. It made no TV, root, network, USB, power, reset, firmware, native
helper, or collector call and did not modify the evidence under review.

## Result

**PASS for a narrow, delayed software-state comparison.** The finalized
post-X record is an accepted, read-only `TimeLimit` observation: 80 cycles,
480 fixed read requests, 960 bulk transfers, terminal protocol phase
`ReadyForHeader`, successful release and close, and an absent private stage.
Its one retained cycle has clean R brackets. Compared with the accepted
pre-action X baseline, the retained R tuple changed from
`1 / 0x1001 / 0` to `0 / 0 / 1`.

This proves a sampled software-state difference after the one observed stock
lifecycle. It does **not** prove when the change occurred, that MODE2 reset
the RT object's processor or storage, that the state remained clean through
the unobserved interval, or that the physical panel displayed a picture.

## Record, transport, and cleanup

The post-X record/result pins are:

| artifact | SHA-256 |
| --- | --- |
| `post-x/record.json` | `a2cff56b3bc17e9a7f1621ca40bcc800d1419d8476fc2485c0f23ed20de7a6cf` |
| `post-x/result.json` | `122ae75f84e69ee94aac3e2878db36d2fef8eca19c805ed7c7e568439c179485` |
| `post-x/native.stdout.bin` | `dcf694a97796d9afe306669fdc9c4b62717f7f68de98fb51cfae7160f0d03fb7` |
| `post-x/native.stderr.bin` | standard empty SHA-256 `e3b0c442...b855` |
| `post-x/execute-envelope.txt` | `a56a7ff8c620fe87ffbc72388c3ae23520f34283a986d65f82ef718d204d5908` |
| `post-x/selftest.stdout.txt` | `f8e8587172006870326a1859c9342b017549a2408d785bdf4f57c129c5d0419c` |

The record pins the previously reviewed wrapper manifest
`915d19e20d7e5e7fc81a1962cec150ef17f2d00229277666918d199e755d2fe1`
and native manifest
`44f74a8a695f41ed21d68a7a36e13934eebc74050bf991c634e6015ec88043a2`.
It has `terminal_validated=true`, one native invocation,
`target_operations_status=accepted_exact_read_requests`, and no required
cleanup remaining.

I independently checked all 24 saved root calls. Every call has transport
exit 0, no host timeout, an authenticated UID/EUID-0 response, exactly one
identical target command, target exit 0, `timed_out=false`, and empty target
and transport stderr. Base64-decoding each saved transport stdout reproduces
its parsed authenticated response. The fixed boot ID is
`00000000-0000-4000-8000-000000000000`.

Self-test reports 75 passes and zero target operations. The execute envelope
binds native exit 0, 4,583 stdout bytes with the saved hash, and empty stderr.
The output contains exactly one terminal JSON object and four classified GC
rows. The terminal object reports open, claim, release, close, and acceptance
all true; writes 0, retries 0, and `busContentsAltered=false`. The final
authenticated cleanup call returns `STAGE_ABSENT`.

## Counters, timing, and retention

The terminal counter equations reproduce exactly:

- 80 cycles started and 80 clean cycles completed;
- 79 older clean cycles discarded by the declared rolling-retention policy;
- six fixed reads per cycle = 480 headers and 480 completed inputs;
- two bulk transfers per read = 960 bulk transfers; and
- one retained `last-clean` set at cycle 80, in exact `R,M,C,H,L,R` order.

Native execution ran from `136902237744 us` to `136922242531 us`, with
deadline `136922237744 us`; its 4,787-us overshoot equals `end-deadline`.
The retained cycle ran from `136922041962 us` through `136922042549 us`.
All 12 retained transfer records are monotonic, exact-count, and errno 0.

The observed lower-path lifecycle's final retained I2C transaction ended at
uptime `136366.222190`. Thus the observer began about `536.015554` seconds
later, and the retained cycle-80 raw set ended about `555.820359` seconds
later. These are delayed samples. The public host context immediately before
X observed `lcdon` and screen-state integer 1 at uptime
`136897.93..136897.96`; those are public software results, not a human or
instrument observation of emitted light or picture.

Only cycle 80's raw bytes are retained. The terminal summary says all 80
completed cycles were classified clean, but the 79 older cycles cannot be
independently byte-replayed from this rolling artifact. Nothing here proves
the state was clean before X began, throughout the approximately nine-minute
post-lifecycle delay, or continuously between X's discrete sequential reads.

## Raw-byte reproduction and baseline comparison

Each of the six saved cycle-80 binary files exactly reproduces the terminal
JSON base64, declared length, and SHA-256:

| window | bytes | post-X SHA-256 |
| --- | ---: | --- |
| initial R | 256 | `a15bcc5f51c78ccdea8283d0839533c2e5f12c243a8e351032747b729b66b477` |
| M | 68 | `cdc6fc83a62defbb54a37a7004f6c1a4c6b9de01912785c248c1fb256b31c2e3` |
| C | 16 | `c9bc21efabc33dc5c687f230ecf321722552c99518957cc37b833c7aaaf9c2b0` |
| H | 96 | `2ea9ab9198d1638007400cd2c3bef1cc745b864b76011a0e1bc52180ac6452d4` |
| L | 64 | `07a165885767f11c0687509812d30e7a493185f02e03296e70ee1188f3ccb827` |
| final R | 256 | `a15bcc5f51c78ccdea8283d0839533c2e5f12c243a8e351032747b729b66b477` |

The two post-X R windows are byte-identical. Direct little-endian decoding of
the three reviewed R fields reproduces the wrapper's classification:

| retained R field | offset | pre-action X | delayed post-X |
| --- | ---: | ---: | ---: |
| stop/event flag | `+0x00` | `1` | `0` |
| fault field | `+0x0a` | `0x1001` | `0` |
| ordinary gate | `+0x0e` | `0` | `1` |

The pre-action baseline record/result remain pinned as
`b0dfb95fd9940e8b82c98b54f278b957f55659b3d530265d7156ea50bcade139`
and
`00e978140af8ff4dadc223d420cd3018ca57577cf14229e2175d2704f8a13eec`.
That baseline was `AlreadyFaulted`; both of its R brackets contained the
faulted tuple above. The post-X terminal is `TimeLimit`, not an observed onset
transition.

For completeness, bytewise comparison of the pre-X post-fault set with the
retained post-X clean set finds 12 changed bytes in R, 15 in M, one in C,
three in H, and two in L. Those auxiliary differences are retained evidence,
but this review does not assign new meanings or physical units to them. The
R windows themselves are sequential, and the M/C/H/L samples between them
are not an atomic tuple.

## Generation and reset-domain limits

`reset-domain-provenance.md`, SHA-256
`a362da5eb3cc48278bec1eba2282a966d317be21f83b0f859f4ebb286986312a`,
supports a bounded layout comparison: the complete image-1 256-KiB slot is
byte-identical across the two retained package generations, and the common
setter stores the reviewed R fields at `+0x00`, `+0x0a`, and `+0x0e`.
Accordingly, the raw three-field before/after comparison is layout-compatible
with either retained slot, conditional on the same rooted bus view.

That report also establishes the missing causal edge: no recovered source
proves that stock MODE2 resets image 1 or clears/retains its `0x20010000` RT
object. Even a core restart would not imply an object clear from the recovered
image-1 scatter path. The active generation, root continuity across MODE2,
and OCL command receiver/reset domain remain unproved. Therefore this review
supports **faulted before, clean in a delayed post-lifecycle sample**, not
“MODE2 reset the fault,” “the panel recovered,” or a permanent repair.

