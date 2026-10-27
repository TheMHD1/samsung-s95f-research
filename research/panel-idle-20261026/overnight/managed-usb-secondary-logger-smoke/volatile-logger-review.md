# Volatile image-1 event-logger instrumentation review

Recorded 2026-10-27 UTC. This is an offline architecture and protocol review.
It made no TV, network, USB, controller, UART, factory, flash, or firmware
call. The proposed experiment changes one volatile RAM halfword for a finite
interval; it does not change a protection threshold, fault latch, EEPROM,
eMMC, firmware image, or factory setting.

## Decision

A single, finite `0 -> 1 -> 0` experiment at image-1 object field `+0x2406`
is technically supportable **only after** a fresh read proves the complete
halfword is exactly zero. Bit zero is the recovered enable for the image-1
formatted-event sink. The common RTP event setter runs and updates its event
fields independently of this bit; enabling the bit adds formatting/ring
writes, not an RTP protection enable.

The write transport has a positive selected-image path: vendor target
`0x102` is family 1, operation 2, and schedules a bulk-OUT payload directly
to the header address. The exact fixed header for two bytes at the observed
alias is:

```text
target  0x00000102
address 0x47012406
length  0x00000002
header  020100000624014702000000
arm payload      0100
restore payload  0000
```

Target `0x201` is not interchangeable with this request. It selects family 2,
not the recovered family-1 direct-address operation.

There has not yet been a live target-`0x102` write. USB completion alone is
not a memory-success acknowledgement, so a first attempt must be treated as a
write-direction qualification. Two finite variants are supportable:

* **preferred, arm-verified:** after an exact arm write, use one exact
  target-`0x101` read to prove the halfword became `0x0001`, then retain the
  known header-ready boundary through the quiet interval and restore;
* **rollback-priority:** perform no read while armed, restore directly from
  the exact arm-write boundary, and verify only the final zero. This reduces
  traffic while the gate is set but cannot claim a verified `0 -> 1 -> 0`
  transition.

The protocol has a critical partial-transfer rule: a short header, payload,
or IN transfer can leave the device waiting for missing bytes, and a new
header would then be consumed in the wrong phase. Restoration is mandatory
whenever the preceding transaction is positively known complete/header-ready.
It is forbidden to send a blind restore header from an unknown phase. The
preferred variant deliberately accepts the bounded risk that a failed armed
read can make protocol phase unknown and therefore leave the volatile gate
changed; that tradeoff is necessary to prove the arm actually took effect.

## Corrected meaning of the retained runtime state

The retained 256-byte target-`0x101` read at bus address `0x47012400`
observed bytes `+6..+7 = 00 00` at uptime `100842.22..100842.70`. That is a
real old observation of the candidate gate, not a current precondition.

The later direct read of `0x20200000` at uptime
`107512.54..107513.05` observed:

```text
write cursor +0x00 = 5
read cursor  +0x04 = 5
valid flag   +0x08 = 0
ring bytes   +0x0c = "[C1]\n" followed by older contents
```

Those observations are separated by about 6,670 seconds and cannot be
combined into a current atomic state. In particular, `5/5/0` means that the
consumer had caught the producer and cleared the availability flag at that
snapshot. It does not prove that no event had occurred, and it does not prove
the `+0x2406` gate was still zero. A new write experiment therefore requires
a fresh gate read immediately before arm and must abort without writing if
the halfword is anything other than `0x0000`.

The fresh host status getter at uptime `107708.45` returned a kernel-written
word of zero, and the retained nonclearing dmesg read contains the matching
line `ERR DET Status:0x0`. This is not atomic with the controller RAM reads,
does not exclude read-to-clear or a debug override, and does not alter the
logger-gate conclusion.

## Complete exact-immediate census for `+0x2406`

The selected image-1 stored region `0x40000..0x80000` is byte-for-byte equal
between the selected package and the full current eMMC backup (SHA-256
`56bfea112d161a22f5bee8630c81306bf04fa9d8d3d901c6d8e7cdd89c09dfbf`).
This is storage identity, not by itself proof of every executing instruction.
The live callback tuple and actual target-`0x101`/`0x203` transactions provide
additional runtime binding for the USB side.

A halfword-aligned Thumb census over image 1 finds eleven exact
`movw ..., #0x2406` instructions, in four coherent bodies:

| linked VA | exact use |
| --- | --- |
| `0x183d8` | read byte, mask bit zero, save it in `r8` |
| `0x183e2`, `0x183ee` | read halfword, force bit zero to one while preserving bits 1..15, store halfword |
| `0x18548`, `0x18552` | read halfword, restore saved bit zero with `BFI`, store halfword |
| `0x1b8d6` | read byte and require bit zero before the formatter/ring body |
| `0x1ba54` | read byte, mask bit zero, save it to a RAM byte during startup |
| `0x1ba62`, `0x1ba6e` | read halfword, force bit zero to one while preserving bits 1..15, store halfword |
| `0x1baaa`, `0x1bab4` | read halfword, restore saved bit zero with `BFI`, store halfword |

The body at `0x183b8..0x18558` uses the firmware's own save-set-run-restore
idiom around a bounded diagnostic sequence. Startup at
`0x1ba0c..0x1bad8` uses the same idiom around initialization. The formatter
at `0x1b8c8..0x1b940` exits before formatting when bit zero is clear.

No exact direct use in this census interprets bits 1..15; every recovered
firmware writer preserves them. That is not a whole-program proof against a
computed pointer, DMA writer, or external core. It is why fixed payload
`0x0001` is acceptable only when a fresh read returns the complete original
halfword `0x0000`. If the original is nonzero, the fixed helper must not be
used; a later design would need to arm with `original | 1` and restore the
exact saved original.

The instrumentation can race the firmware's own temporary togglers. A
firmware sequence that began before the external arm could later restore its
saved zero and end the logging interval early. Conversely, a sequence begun
after arm should save and restore one. The preferred design performs exactly
one immediate armed readback, then no more controller traffic until restore.
That sample proves only its instant; it cannot exclude a later firmware race.
The rollback-priority variant performs no armed read and therefore preserves
the post-arm write boundary at the cost of never directly proving the one.

Pinned selected-image slices:

| role | linked VA / stored range | SHA-256 |
| --- | --- | --- |
| diagnostic save/set/restore | `183b8..18558` / `585b8..58758` | `c409043151e281f285bc0275c151287bb3d4df25d701b54429cdf4568e479d79` |
| gated sink | `1b8c8..1b940` / `5bac8..5bb40` | `47abdf7963385a87473920daae5212943303054ceb9ba3df92c3c31928fb545e` |
| startup save/set/restore | `1ba0c..1bad8` / `5bc0c..5bcd8` | `e7806b27e0db5ca8a8f8b25b1ff58cf5fad18865f177c4a8368715b675f1b1b6` |

## Event path exposed by the gate

The common setter at linked VA `0xc1e0..0xc212` obtains root
`0x20010000`, then writes these event fields regardless of the logger bit:

```text
root + 0x2400 = 1       (halfword)
root + 0x240e = 0       (halfword)
root + 0x240a = 0x1001  (halfword)
```

Only afterward does it call the gated sink twice with the same exact format
literal `rtp_act_%d\n`. Its four direct callers supply events:

| call VA | event | decimal text expected when logging is enabled |
| ---: | ---: | --- |
| `0x203a` | `0x2e0` | `rtp_act_736` |
| `0xc792` | `0x338` | `rtp_act_824` |
| `0xc7e0` | `0x344` | `rtp_act_836` |
| `0xc836` | `0x351` | `rtp_act_849` |

Each common-setter event should therefore produce two identical formatted
lines if bit zero remains enabled for both calls. The `0x338` path is the
already recovered packed-sample/count/helper predicate; the gate neither
creates that predicate nor suppresses its event-field stores.

The sink has 30 direct `BL` call sites in image 1, not only the two calls from
the common setter. Enabling it can record unrelated diagnostic messages and
can add formatter/ring/UART work. This is an observational perturbation: the
extra work may change real-time timing even though it does not directly
change a protection threshold. The arm interval must therefore be short and
finite.

The common-setter slice SHA-256 is
`f8a6285dd94b3338eff37ded006a2ebff6ecfe7409bef9044f34fd25cdb27102`
over stored bytes `0x4c3e0..0x4c412`.

## Producer, consumer, and what restoration preserves

The image-1 sink maintains this object:

```text
0x20200000  uint32 write cursor
0x20200004  uint32 read cursor
0x20200008  uint32 availability flag
0x2020000c  byte ring, length 0x3c00
```

For every formatted byte it reduces the write cursor modulo `0x3c00`, stores
the byte, advances the cursor, and finally writes one to the flag.

Image-0 linked VA `0x39404..0x394a2` is an independent drain. It has seven
direct call sites. For the secondary object it:

1. skips or finishes when `read cursor == write cursor`;
2. reduces the read cursor modulo `0x3c00`;
3. sends the selected byte through the UART-shaped writer at MMIO base
   `0x40150000`;
4. advances the read cursor; and
5. clears the flag when the cursors meet.

The drain does **not** zero the write cursor or erase ring bytes. Therefore
restoring the logger gate to zero before the final full-ring read does not
delete the produced text. It can, however, allow the drain to advance the
read cursor and clear the flag before collection. A collector must not treat
flag zero as “no event” and must not rely only on the unread interval between
the cursors. It needs a complete pre-arm ring snapshot and a complete
post-restore ring snapshot so byte differences and the two cursor endpoint
states survive consumption.

If more than `0x3c00` bytes are produced during the arm interval, older text
can be overwritten and the cursor alone has no persistent wrap count. This
is another reason for a short deadline and complete baseline/post-restore
snapshots. Apart from the preferred variant's one immediate verification
read, the corrected state machine permits no controller sampling while armed.

The drain slice SHA-256 is
`417e7c69a8422b140e7e59f680fdbb3b89e685de7716a9b2e7b38defd0ad2752`
over selected stored bytes `0x39604..0x396a2`. The current eMMC image-0 slot
differs from the selected package, so this byte identity is not inferred from
storage alone; the live `5/5/0` header and preserved `[C1]\n` contents are
runtime behavior consistent with the decoded producer/consumer contract.

## Target-`0x102` direct-address write path

The selected USB callback table observed live points to the packaged vendor
callbacks, including OUT completion VA `0x28cf0`. The same vendor transport
has already completed actual target-`0x101` memory reads and target-`0x203`
eMMC reads. Operation 2 has not itself been exercised.

The static target-`0x102` path is:

1. Validator VA `0x29258` accepts exact target `0x102` and, because the
   family is nonzero, stores the separate remap flag as zero.
2. Parser VA `0x28f24` copies the header words into state, normalizes the low
   target byte to operation `2`, and selects backend mode zero for operations
   1 and 2.
3. The zero remap flag skips mapper VA `0xefa4`; the supplied bus address is
   retained unchanged.
4. The current transfer size is `min(remaining, configured cap)`. Length two
   is nonzero and far below both recovered caps.
5. At VA `0x2912a..0x29148`, operation 2 loads that size as an unsigned
   halfword and calls bulk-OUT scheduler VA `0x7fce` with the header address
   as its destination.
6. OUT completion VA `0x28cf0` obtains the completed count, subtracts it from
   remaining, advances the address, and rearms the next 12-byte header when
   the remainder reaches zero. Its continuation schedules another direct
   OUT chunk if a remainder exists.

There is no family-1 allowed-address whitelist in this validator. That is not
permission to scan or write arbitrary addresses; it makes pinning the one
reviewed address in the helper essential.

Pinned selected-image slices:

| role | linked VA / stored range | SHA-256 |
| --- | --- | --- |
| vendor OUT completion | `28cf0..28ec6` / `28ef0..290c6` | `7c165cbf88ebd117d929ee9c1dd8594c442b4c73b78b0fc12ad0273ba1c952b7` |
| header parser and operation dispatch | `28f24..291f0` / `29124..293f0` | `101fe3f099e3d9b75ed873206120a8753486edeefe3019b55648e3758a8c2bc4` |
| target validator | `29258..293b4` / `29458..295b4` | `febec20e4653208a48681cf6f82f1f9e13a7b03149e53f6baf5ddf149827c234` |

What remains unproved is bounded and concrete:

* operation-2 writeability of the `0x47012406` bus address has not been
  qualified live;
* a successful host bulk-OUT count does not prove the destination changed;
* two-byte DMA visibility/atomicity relative to image-1 halfword accesses is
  not established; and
* there is no recovered device response carrying a write status or checksum.

These gaps require target-`0x101` readback. In the preferred variant it occurs
both immediately after arm and after restore; in the rollback-priority variant
it occurs only after restore. They do not erase the positive target-`0x102`
parser/scheduler path.

## Address and bus-range rationale

Image-1 code obtains root `0x20010000`; the logger gate is therefore CPU
address `0x20012406`. The recovered mapper translates the
`0x20000000..0x201fffff` CPU range by `+0x27000000` for the non-`0xA` tag,
giving `0x47012406`. The upper bound is exclusive, and this address is safely
inside the translated range.

This is corroborated by actual reads, not arithmetic alone:

* target `0x101`, bus `0x47012400`, length 256 returned a structured live RT
  block, including zero at `+6` in the old snapshot; and
* target `0x101`, bus `0x470004c0`, length 64 returned the live root pointer
  `0x20010000` at `+0x20` and the expected nearby configuration values.

The direct secondary-ring address `0x20200000` is different: it is at the
mapper's exclusive upper bound and passes through unchanged. Its successful
64-byte live read proves visibility for that snapshot. A full object read is
`0x3c0c` bytes, within the recovered `0x6000` transfer cap, but that exact
length should still be reviewed and qualified as a read-only helper before
the write experiment.

## Required finite experiment state machine

The experiment should be a single controller that owns arm, the timed quiet
window, restoration, and post-restore collection. Separate manually invoked
commands create an avoidable window in which phase state or restoration can
be lost.

The controller must model protocol phase explicitly:

* `READY_FOR_HEADER`: a new 12-byte header is allowed; this is also the state
  reached after an exact write payload or exact read IN completion;
* `EXPECTING_WRITE_PAYLOAD`: an exact target-`0x102` header completed and the
  device expects exactly two payload bytes;
* `EXPECTING_READ_IN`: an exact target-`0x101` header completed and the device
  owes exactly the requested IN bytes; and
* `PHASE_UNKNOWN`: any short transfer, timeout, disconnect, or malformed
  result occurred after a transaction began.

Only `READY_FOR_HEADER` permits a new header. Exact two-byte write-payload
completion and exact-count read-IN completion each establish a positive
transaction boundary and return to `READY_FOR_HEADER`. In `PHASE_UNKNOWN`,
halt all further controller traffic and preserve the record.
Releasing/closing the host interface is local cleanup; it is not a
device-protocol reset and does not restore the missing byte count.

### 1. Preflight and baseline

* Pin boot ID, device identity, configuration, unbound interface, helper
  hashes, and absence of another USB helper.
* Take and retain one complete `0x3c0c`-byte snapshot at `0x20200000`, plus
  its hash. Require write/read cursors each in `0..0x3c00` inclusive and flag
  in `{0,1}`; otherwise abort without writing.
* Last, take a fresh target-`0x101` read covering `0x47012406`. Require exact
  original halfword `0x0000`. Store the raw read and its monotonic/UTC/boot
  anchors. Any other value aborts without writing.

Do not clear the cursors, flag, or ring. The baseline snapshot is sufficient
to distinguish new bytes without destroying retained evidence. Every
baseline target-`0x101` transaction must transition
`READY_FOR_HEADER -> EXPECTING_READ_IN -> READY_FOR_HEADER` using exact
OUT-header and IN-payload counts. A short/timeout baseline read enters
`PHASE_UNKNOWN` and aborts the experiment without any subsequent controller
request.

### 2. Arm and establish a known boundary

* Send exactly one target-`0x102` header. Exact count 12 moves the controller
  to `EXPECTING_WRITE_PAYLOAD`; any other result enters `PHASE_UNKNOWN`.
* Only after exact header count 12, send exactly one two-byte payload
  `01 00`. Exact count 2 returns to `READY_FOR_HEADER`; any other result enters
  `PHASE_UNKNOWN`. In particular, a one-byte completion can write the low
  byte at `0x47012406` while leaving byte `0x47012407` pending. A restore
  header sent then would corrupt memory because its first byte would satisfy
  that pending payload.

If either arm transfer is anomalous, record
`restore_unverified=true` and `log_flag_may_remain_changed=true`, release and
close for local cleanup, and halt. Do not send a new header, do not retry, and
do not continue to a read or restore operation.

For the **preferred arm-verified variant**, immediately issue one fixed
target-`0x101` read (prefer a fixed 64-byte window beginning at `0x47012400`,
a bounded prefix of the previously exercised 256-byte read, and extract bytes
`+6..+7`). Exact header count 12 moves to
`EXPECTING_READ_IN`; exact IN count 64 returns to `READY_FOR_HEADER`. Require
the halfword to be `0x0001` for arm acceptance. If the exact read instead
returns another value, arm verification fails, but protocol state is known:
perform the mandatory restore from `READY_FOR_HEADER`, then verify final zero.
If its header or IN transfer is short, times out, disconnects, or is malformed,
enter `PHASE_UNKNOWN`, set `restore_unverified=true` and
`log_flag_may_remain_changed=true`, and halt without restore or retry.

For the **rollback-priority variant**, omit this armed readback. The exact arm
payload leaves the protocol `READY_FOR_HEADER`, so restore remains safe, but
the result must never be described as a verified arm or verified
`0 -> 1 -> 0` transition.

### 3. Collect under a hard deadline

Have the owner ready to trigger the physical transition before arm. Use a
monotonic deadline of at most ten seconds; do not wait indefinitely for user
input while armed. In the preferred variant, start this interval only after
the exact armed readback has returned `0x0001`; in the rollback-priority
variant, start it after the exact arm payload.

Issue **no controller USB transaction** during this interval. In particular,
do not sample the gate, cursors, flag, or ring while armed. Host-side
monotonic/UTC timing and an owner annotation can continue, but the device
must remain `READY_FOR_HEADER` until the restore header is sent. Apart from the
preferred variant's single immediate arm-verification read, this sacrifices an
armed cursor trajectory in order to avoid another failed read stranding the
protocol with the logger enabled.

### 4. Restore at the known boundary, then preserve the ring

* At the fixed deadline, require that protocol phase is still recorded as
  `READY_FOR_HEADER`. Whenever that condition holds, restoration is mandatory,
  including after an exact armed read returned an unexpected value.
* Send exactly one target-`0x102` restore header. Exact count 12 moves to
  `EXPECTING_WRITE_PAYLOAD`; any other result enters `PHASE_UNKNOWN`.
* Only after exact restore-header count 12, send exactly one payload
  `00 00`. Exact count 2 returns to `READY_FOR_HEADER`; any other
  result enters `PHASE_UNKNOWN`.
* Only after that exact restore boundary, perform one target-`0x101` readback.
  Exact OUT-header and IN-payload counts return to `READY_FOR_HEADER`; value
  `0x0000` verifies restoration.
* Only after verified zero, read the full `0x3c0c`-byte object and compare it
  byte-for-byte with baseline. Clearing the producer first does not erase
  ring bytes, while it prevents further gated writes during the final read.

A short restore header or payload sets `restore_unverified=true` and
`log_flag_may_remain_changed=true`; halt without any new header. If the
restore transfer completed exactly but its subsequent readback is short or
times out, the restore transaction remains recorded as complete but the new
read has left protocol phase unknown: mark readback unverified and halt
without fetching the ring. If an exact, boundary-completing readback returns
a nonzero value, mark restoration failed and halt. There is no automatic
retry or loop in any of these cases. Release/close does not repair the device
phase. A controller reset may change volatile RAM, but this review does not
claim reset necessarily restores this field to zero.

### 5. Acceptance and interpretation

Transport acceptance requires exact header/payload counts, one write per
phase, no hidden retry, release/close success, and stage cleanup.

The **preferred arm-verified variant** may claim a verified finite
`0 -> 1 -> 0` transition only when all of these are retained:

* fresh pre-arm halfword `0x0000`;
* exact arm header and payload counts returning to `READY_FOR_HEADER`;
* exact armed-read header/IN counts returning to `READY_FOR_HEADER`, with
  halfword `0x0001`;
* a finite, fully timestamped no-controller-traffic interval;
* exact restore header and payload counts returning to `READY_FOR_HEADER`;
* exact final-read header/IN counts returning to `READY_FOR_HEADER`, with
  halfword `0x0000`; and
* complete, retained baseline/post ring snapshots and cleanup evidence.

The **rollback-priority variant** omits the armed-read requirement and may
claim only `pre-arm zero + exact arm transport + exact restore transport +
verified final zero`. Even if new logger text appears, that is evidence
consistent with the gate taking effect, not direct verification that the
halfword was one. Any anomaly that enters `PHASE_UNKNOWN` rejects both
variants and forbids a restore or any other new controller request.

Parse newly changed ring bytes using the baseline/post snapshots and their
two endpoint cursor states. Search for the four decimal `rtp_act_*` records,
but preserve all other text. Duplicate RTP lines are expected from the two
sink calls and are not two independent protection events. Absence of a line
does not exclude an event if the gate raced low, the ring wrapped, formatting
failed, or the target write was not actually visible.

This experiment can establish that the gated image-1 logger recorded a
specific event near an owner-observed transition. It cannot by itself prove
that the event caused the OLED panel blackout, that a status getter is
non-clearing, that every selected-package byte is executing, or that a
repair has been found.

