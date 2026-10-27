# Independent audit of the stock RT lifecycle trial

Recorded 2026-10-27 UTC. This report is an offline audit of retained local
artifacts. It made no TV, root, network, USB, I2C, GPIO, power, reset, UI,
firmware or controller call and did not rerun a helper.

## Pre-action baseline: PASS

The unchanged X baseline is a complete accepted read-only transaction. It is
suitable as the fresh pre-action software baseline for the proposed trial.
No stock power lifecycle had been requested at this checkpoint, so this
section makes no post-MODE2 or lifecycle claim.

### Provenance and transport envelope

The wrapper and native pins match the previously reviewed builds:

- wrapper manifest
  `915d19e20d7e5e7fc81a1962cec150ef17f2d00229277666918d199e755d2fe1`;
- native manifest
  `44f74a8a695f41ed21d68a7a36e13934eebc74050bf991c634e6015ec88043a2`;
- wrapper
  `a4146bc302a764f476e068f456398b8dc34a6e3cc480b876f6e44ed65098cc82`;
  and
- root adapter
  `e69b79a103931c4eecca6f6f505975acdd8f9de2e1e8189b8321dd77d8bc6938`.

All 24 retained root calls are authenticated, UID/EUID 0, transport exit 0,
not host-timed-out, and contain one target command with exit 0 and
`timed_out=false`. The fixed boot is
`00000000-0000-4000-8000-000000000000` throughout. Self-test output has the
expected result `75 / targetOperations 0 / maxTestOutputBytes 10541` plus two
classified GC rows; its SHA-256 is
`3750f16367896c8f351ef242de045213bc7bc541d0f2a61f2238519d6e47ab6f`.

There was exactly one native invocation. The authenticated execute envelope
is byte-identical to `pre-x/execute-envelope.txt`, SHA-256
`488fb8b5bfb2fb996b6bd0c556b58397ec740689577b538042141814d168d279`.
It reports native exit 0, stdout 4,544 bytes with SHA-256
`3075f7d927501fa4bfd0667b6c140af3638ba7d026eb36599ddb47d7c222ab43`,
and empty stderr with the standard empty SHA-256. The separately saved native
files reproduce those exact lengths and hashes. The native output contains
one terminal JSON object and two classified GC rows, as the wrapper result
records.

The terminal boot matches, terminal target uptime is `136101.98`, and native
open/claim/release/close are all true. Protocol phase is
`ReadyForHeader`. Cleanup removed the exact private stage and returned
`STAGE_ABSENT`; no retry occurred. The record and result hashes at this audit
point are respectively:

- `pre-x/record.json`:
  `b0dfb95fd9940e8b82c98b54f278b957f55659b3d530265d7156ea50bcade139`;
- `pre-x/result.json`:
  `00e978140af8ff4dadc223d420cd3018ca57577cf14229e2175d2704f8a13eec`.

### Exact read geometry and timing

The native result contains six fixed target-`0x101` read requests in the
reviewed `R,M,C,H,L,R` order and exactly 12 USB bulk transfers: six exact
12-byte OUT headers and six matching IN responses. Every transfer reports
the expected count and errno 0; timestamps are monotonic. The first transfer
began at `136101796645 us`, the final transfer ended at
`136101805694 us`, and native execution ended at `136101806791 us`, well
before its 20-second deadline with zero overshoot. `target_operations=6`
therefore means six fixed reads, not six individual bulks.

The six saved response files reproduce the native base64 bytes, declared
lengths and SHA-256 values exactly:

| window | bytes | SHA-256 |
| --- | ---: | --- |
| initial R | 256 | `91055b0ce0f0b798a78313bd90520506f63261fa1c35d78a0de85b2d332379f9` |
| M | 68 | `c58a20a4147d7b09bfe560456cb65bfce1462fdc5aefcfc50b80e3f5927765c9` |
| C | 16 | `2efca8a0f734277a3df0351751a2ec11d33d20423983381f5068299289fc308a` |
| H | 96 | `d94f16ac03ed209ece31c6e35b49d89a81755681fabf296b3bc5a37013c3fe42` |
| L | 64 | `0683bb72c1bb998774ba4747987ec82ac938ce892ede62d877b9a1da641f2439` |
| final R | 256 | `91055b0ce0f0b798a78313bd90520506f63261fa1c35d78a0de85b2d332379f9` |

The two R windows are byte-identical. Independently decoding their reviewed
little-endian fields gives:

| R field | offset | initial | final |
| --- | ---: | ---: | ---: |
| stop | `+0x00` | `1` | `1` |
| fault | `+0x0a` | `0x1001` | `0x1001` |
| ordinary gate | `+0x0e` | `0` | `0` |

That is the exact accepted `Faulted` tuple. The wrapper's
`AlreadyFaulted`, `onsetMissed=true`, `onsetObserved=false` classification is
therefore reproduced from raw bytes rather than trusted as an unsupported
label. `onsetMissed` means only that the tuple was already faulted at X's
first R; it does not date the onset. The auxiliary M/C/H/L windows are
retained raw by X and are not independently promoted to new semantic fields
here.

All six response hashes—including both R windows—also exactly match the
earlier accepted X capture that ended at uptime `126642.16`. The new sample
at uptime `136101.80` is thus a fresh byte-for-byte repeat of those retained
windows on the same Linux boot. This establishes persistence at two sampled
epochs, not continuous invariance between them.

### Preflight scope

`baseline-intent.json`, SHA-256
`be665c65dae5f8a03fdcef8ec493548a2d4008fe9e3b128e7e3066d77a599b19`,
correctly labels this as the pre-action stage. Its referenced public preflight
SHA-256 `8cc7ce0f85ebfbdefebe2d9d096b31ebfeb194a502a3c1a56617cc2198a36624`
matches `AU/preflight-for-one-shot.json`.

That authenticated read-only preflight observed, on the same boot:

- software-upgrade status `0` and burn-in-in-progress `0`;
- USB identity `04e8:2001`, revision `0250`, product
  `STL1 CDC and Bulk`, configuration 1;
- all three interfaces unbound; and
- zero matching usbfs file-descriptor links in its `/proc` snapshot.

The sample ran from uptime `136050.56` to `136076.79`; the first baseline R
started about 25.0 seconds later. These are bounded no-conflict observations,
not an atomic maintenance exclusion. The FD census is inherently racy, and
this particular preflight did not query public power/screen state or the
private QDF update word. It therefore does not by itself clear a later stock
lifecycle; the separately declared immediate action gates still apply.

## Bounded conclusion

The baseline positively proves a fresh, exact software tuple
`stop=1 / fault=0x1001 / ordinary_gate=0`, with an exact repeated post-fault R,
six complete reads, terminal `ReadyForHeader`, clean release/close and absent
stage. It does not prove a physical black screen, fault cause, continuous
state, onset time, maintenance absence, or recovery. In particular, no
comparison with a future post-lifecycle sample is valid until that stock
lifecycle and its independent kernel/I2C subchannel are separately audited.

## One-shot stock lifecycle: channel audit PASS

The retained AV bracket is sufficient to accept a **narrow lower-path
lifecycle channel** for this trial. It is not sufficient to accept the whole
AVOC collector. The collector remains rejected exactly as recorded:

- `accepted=false`, `diagnostic_eligible=false`, and
  `technical_capture_complete=false`;
- error `ValueError: orphan AVOC ioctl exit in physical window/drain`; and
- zero human observer rows, with physical state unobserved.

No AVOC absence, picture, light, panel-recovery, or physical-blackout claim is
made below. The narrower channel is accepted because its raw kernel, GPIO and
I2C evidence is independently complete and is bound to the single stock
helper by PID and time, rather than because the enclosing collector succeeded.

### Acquisition and byte provenance

The collector launch response is authenticated as UID/EUID 0 and binds PID
`11344`, start ticks `34085118`, process group `11344`, and session `11344`.
The capture record binds that same PID/start pair and records
`controller_gate_released=true`. Both readiness probes are authenticated on
boot `00000000-0000-4000-8000-000000000000`, observe tracing enabled, and
require exactly one `CAPTURE_START` and no `CAPTURE_END`; their target uptimes
are `136354.04` and `136361.93`. The raw trace itself contains
`CAPTURE_START` at `136352.329589` and `CAPTURE_END` at `136412.369844`.

The complete and `partial-*` copies are byte-identical for every channel
retained by the rejected collector. Important pairs include:

| channel | bytes | SHA-256 |
| --- | ---: | --- |
| trace | 12,118,068 | `ea9f0a57ae34faaae714c11230194d32819cf28c5debcbe8ec1e381706d686ed` |
| metadata | 494,785 | `7d8bdec8923af6dcdacd25ff4b6e2928c9b435fd3cb17fc459514cc1f9e650f3` |
| samples | 84,362 | `1470aec34254a2be547bbe019f673365ac406d285ddd5433ad6cc1d5c5caef12` |
| sample errors | 144,448 | `0bf3a999f964d93c7f70efaf8d746dffcb1d1de14cf30b9750e101b9e24d5bbb` |
| kernel artifacts | 146,358 | `a5cb2171a4faf92f7128d15d8adcda5f30449d83daff0aa31fceb4e6b539f95d` |
| FD snapshot | 5,839 | `88cf85a176cc2709b2719c01969c3838c16e6968b0012caf1c7bba130da4a72a` |
| collector stdout | 636 | `ebba9b172c5e8d27b93e13fcd342f00f7aca20e48a5dae8fedc19ead3325566b` |
| collector stderr | 0 | standard empty SHA-256 |

I independently base64-decoded and gunzipped the two sections in the original
`artifacts.txt`. They reproduce the saved files exactly:

- start kernel ring: 497,624 bytes, SHA-256
  `e5eac973ce8ca603e5bfc1e1749eea3897e87eec14f17b4943720da9bbc82e68`,
  boot as above and uptime `136341.92`;
- end kernel ring: 497,238 bytes, SHA-256
  `c00c2efd6ba743283c38113dc4513d04c9e01488e84c7a27b7536e97d2ece8e8`,
  same boot and uptime `136412.87`.

Thus the action, its I2C tail, and all three post helpers lie inside one raw
capture on one Linux boot. `trace-decoded.json`, SHA-256
`a6835690ca62fb68ca563ba132171549161876f96c4c964f1a8928ccbd59978b`,
is bound to that exact raw-trace hash. The unchanged decoder accounts for all
106,914 retained/written trace entries, reports 381 structurally complete
two-message transfers, zero partial transfers, zero parse errors, zero orphan
I2C results, `ring_accounting_complete=true`, and
`semantic_capture_complete=true` for its I2C grammar.

The decoder's `markers=[]` does not defeat this predeclared bracket. No custom
MODE2 trace marker was injected or expected. The action is instead bound by
the external one-shot dispatch record, helper PID `17157`, its ftrace
fork/exec chain, the PID-tagged QDF `Reset(2)` row, and the subsequent
PID-tagged GPIO/I2C stream. This is adequate for the lower lifecycle channel;
it must not be rewritten as a successful AVOC bracket.

### Exactly one fixed helper action

The seven helper records have these hashes:

| helper | record SHA-256 | PID | retained result |
| --- | --- | ---: | --- |
| pre status | `7a54d0524055f024e252ca4ed67d7c28152ab9823bdf1c48e7d8f94e876ba1c7` | 13707 | `0x10` |
| pre GPIO | `5f8d8b27a7e1f46b4ddec2f0fd55220f42de71232dd4b9b58a588ccc3216ebeb` | 14749 | line 5 = 1 |
| pre duty | `b186b36d31e4abd849b6bbfb19a3a1cf7b61ff032167027694cb107bffca4270` | 15984 | 256 |
| MODE2 | `a9ea023992ee7fe20692db73844cb1c0e7374dbee2bd38d02449b5b2057c2cac` | 17157 | operation 41, mode 2, return 0 |
| post status | `7bec5ac684ef9f6312f0d375de0a2e458340c58036f90478a054c72c604f4290` | 19162 | `0x00` |
| post GPIO | `113f576a017f28773a26e16115e37211c51239e1431841212a4e4a30de0eb43e` | 20396 | line 5 = 0 |
| post duty | `754ff71533964bf5ed81b0dd220ff79695b98adbbb00da92c4ffd084b94ba471` | 21381 | 256 |

Every one is `accepted=true`, `cleanup_confirmed=true`, and
`retry_permitted=false`. Every retained call is authenticated UID/EUID 0,
has host transport exit 0, is not host-timed-out, and contains only target
commands with exit 0 and `timed_out=false`. Each helper's preflight and
execution boot is the same fixed boot. `dispatch.json` records one attempted
request, `at_most_one=true`; `bracket-exit.json` records it attempted and
confirms no automatic post-X.

The MODE2 helper's return 0 alone remains only
`kernel_return_zero_only`—not a power acknowledgement. The raw channel closes
that particular no-action ambiguity at the Linux lower callbacks:

1. PID `17157` logs QDF `Reset(2)` and `Tcon Power Off` at
   `136363.892943..951`; GPIO425 is driven low in ftrace at
   `136363.890072..079`.
2. The kernel records the off mailbox `[01 3f 01 01 00]` and
   `Reset TCON power=1 ret=0` at `136363.935094..110`.
3. USB device 45, identity `04e8:2001`, product `STL1 CDC and Bulk`, Samsung,
   disconnects at `136364.069572` and completes disappearance.
4. QDF logs `Tcon Power On` at `136365.058925`, then the on mailbox
   `[01 3f 00 01 00]` and `Reset TCON power=0 ret=0` at
   `136365.079157..179`.
5. USB device 46 enumerates at `136365.554961`; the kernel records the same
   vendor/product, revision 2.50, product/manufacturer/serial and config 1 at
   `136365.703846..704361`.
6. PID `17157` drives GPIO425 high and samples GPIO125 as input/raw 0 at
   `136365.920063..088`; the named ACDET-high callback follows at
   `136365.922973`.
7. QDF records init check OK, `TCON Access Success`, display check OK and
   normal state replay. These are software/log interpretations, not electrical
   measurements.

This is positive evidence that the one requested stock off/on path reached
its reset, GPIO and re-enumeration boundaries. It does not prove rail voltage,
MCU reset internals, emitted light, or panel recovery.

### I2C and pre/post channel results

PID `17157` owns exactly 346 decoded bus-5/address-`0x76` transfers from
`136365.920098` through `136366.222190`. All are structurally complete,
two-message, `ret=2`, and classified
`all-messages-reported-transferred`: 233 write6/read4 and 113 write6/write4,
including 226 status-handshake reads. This is a complete observed Linux I2C
replay, but `ret=2` is not MCU semantic acceptance.

The request sequence is not byte-for-byte identical to the earlier stock
MODE2 trial: 345 of 346 requests match; the retained dimming write at sequence
index 326 is now selector `0x128` value 256 rather than 207, and its two raw
handshake replies consequently differ. Calling the two trials an "exact
byte-identical replay" would therefore be wrong. The current replay is exact
and complete within this capture, and its value 256 agrees with both current
pre/post duty reads.

The separately accepted helper values are also independently present in the
shared raw trace/ring with exact PIDs:

- PID `13707`: `f38000000008 -> 00000010`, `ret=2`, at
  `136356.139443`; kernel log at `136356.142708` says ERR DET `0x10`.
- PID `15984`: `f30000000128 -> 00000100`, `ret=2`, at
  `136361.141522`; kernel log at `136361.144788` says value 256.
- PID `19162`: `f38000000008 -> 00000000`, `ret=2`, at
  `136368.748469`; kernel log at `136368.751743` says ERR DET `0x0`.
- PID `21381`: `f30000000128 -> 00000100`, `ret=2`, at
  `136373.627682`; kernel log at `136373.630957` says value 256.

This closes the standalone helpers' stated "controller transaction not
proved" limitation for these four observed wire transactions. It does not
exclude read-to-clear semantics, prove MCU meaning, or make the values
physical luminance measurements. The GPIO helper results are likewise in
ftrace: PID `14749` samples GPIO125 raw 1 at `136358.746215`, while PID
`20396` samples raw 0 at `136371.122827`. The bounded observed transition is
therefore ERR DET reply `0x10 -> 0x00`, GPIO raw `1 -> 0`, and retained duty
`256 -> 256` across this lifecycle.

### Cleanup and post-reset USB ownership

The collector itself was quiesced and cleaned despite its semantic rejection.
Authenticated quiesce returns `QUIESCED`; authenticated cleanup returns
global tracing `0` and `CLEAN`, with the trace instance, output directory,
stage directory and expiry residue absent. The collector record records both
`quiesce_verified=true` and `cleanup_verified=true`.

The later read-only host snapshot `post-usb-host-preflight.json`, SHA-256
`831ce51a71c10d3a1046b2e5419eb890ec7094e28e05bc57028b1e9f98dfccdc`,
is authenticated UID/EUID 0 and succeeds on the same boot from uptime
`136651.28` to `136677.25`. It observes the reset-era device number 46 with
identity `04e8:2001`, revision `0250`, product `STL1 CDC and Bulk`, serial
`0x12345678`, bus 7 and configuration 1; all three interfaces are unbound and
the `/proc` usbfs FD census reports zero holders. This is a bounded ownership
snapshot, not proof that no unrecorded actor touched the device at every
instant.

## Post-lifecycle X decision: eligible once

No material blocker remains for **one** invocation of the unchanged,
previously reviewed X passive observer, under the recorded closed-world
lineage that no vendor bulk OUT occurred after the pre-X read or MODE2. The
positive disconnect/re-enumeration, complete current I2C tail, clean helper
and collector teardown, same boot, unbound interfaces, and zero usbfs holders
provide a concrete fresh-session boundary rather than relying on the stock
ioctl return alone.

Acceptance must remain narrow and fail closed:

- invoke the unchanged pinned X wrapper only once; never retry an ambiguous
  transport or phase;
- require its existing exact fixed-address/read-only contract, authenticated
  envelope, terminal `ReadyForHeader`, release/close, and stage-absence gates;
- treat X's first R as a **delayed post-lifecycle software sample**, not an
  event-time sample and not proof that the first R began clean;
- compare only retained raw RT/software fields with the accepted pre-action
  baseline; and
- preserve any `AlreadyFaulted`, unchanged, malformed, timeout, or unknown
  result without sending a compensating MODE2, reset, or second X.

The enclosing AVOC collector remains rejected, `markers=[]` remains honestly
recorded, and physical state remains unobserved. A post-X change may establish
a software RT transition following one positively observed stock lifecycle;
it cannot by itself establish picture recovery, a working panel, causality of
the original blackout, or a permanent repair.
