# Independent runtime review: selector/context read after V6

Date: 2026-10-27 UTC  
Scope: offline replay and byte-level interpretation only; no TV, root, USB,
network, UI, reset, write, or cleanup action

## Runtime acceptance

No runtime acceptance defect was found. The retained run used reviewed
manifest
`4d3e0ac655aff8eac8d1d2f3835d96597f74d5c45c751e67323ea36805663446`
and completed exactly one native invocation. The host-side poll interruption
did not cause a second invocation: the retained record contains one execute
call, one native outcome, and one terminal cleanup call.

The artifact identities are:

| artifact | bytes | SHA-256 |
| --- | ---: | --- |
| `record.json` | 310385 | `374d2e56348cfbe02d1b78a0904b1fe245fef4605048cc522c2f8883c27e4e31` |
| `execute-envelope.txt` | 2394 | `0f6cac34c45adba9e4f76c737a1965d64a04b6fe1346eaf4d0083543afd064a9` |
| `native.stdout.txt` | 1540 | `2cf88c5c86968648541d3020dd461a5e83224023af70726357aac76525d04f3b` |
| `native.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `mode-window.bin` | 68 | `c58a20a4147d7b09bfe560456cb65bfce1462fdc5aefcfc50b80e3f5927765c9` |
| `alternate-window.bin` | 16 | `2efca8a0f734277a3df0351751a2ec11d33d20423983381f5068299289fc308a` |
| `result.json` | 1141 | `d2c3a49f2bd721eb6a33eed70776689386cf32bacab036459fcff2f16795c703` |

All 19 retained root calls independently pass the pinned authenticated
response validator against their exact command text. Every call has a
45-second remote bound, 75-second host bound, no timeout, transport exit zero,
empty transport stderr, and command length below 8192 bytes. The sequence is
one private-stage creation, exact upload/final verification of three staged
artifacts, one zero-I/O self-test, one execute call, and one cleanup call.

The self-test reports 35 tests and zero target operations. The active
envelope is strictly framed, boot-bound to
`00000000-0000-4000-8000-000000000000`, exits zero, has empty native stderr,
and reconstructs the saved native stdout byte-for-byte. Its two GC rows are
classified and do not alter the single JSON outcome.

The native transcript is exact:

| step | direction | expected | returned | errno |
| --- | --- | ---: | ---: | ---: |
| open | local | 0 | fd 25 | 0 |
| claim | local | 0 | 0 | 0 |
| mode header | OUT | 12 | 12 | 0 |
| mode data | IN | 68 | 68 | 0 |
| alternate header | OUT | 12 | 12 | 0 |
| alternate data | IN | 16 | 16 | 0 |
| release | local | 0 | 0 | 0 |
| close | local | 0 | 0 | 0 |

The final native stage is `complete`, protocol phase is `ReadyForHeader`,
and opened/claimed/released/closed/accepted are all true. The native base64
fields reproduce both saved binaries and their embedded hashes. Final record
accounting is two exact accepted read operations, one native invocation, and
`no_retry=true`.

Cleanup revalidated the exact five-file stage inventory and hashes, removed
only those files and the private directory, and returned `STAGE_ABSENT`.
The final record has `cleanup_required=false`.

## First window: rooted conditional image-1 sample

The 68 bytes returned from bus `0x470004a0` are:

```text
8c0100000000400b8007000002000000
000026000000f4010000f40100000000
000001000000590cf401280000010000
00002600000000010001000000000000
00000120
```

Little-endian decoding gives:

| proposed CPU field | returned offset | value |
| --- | ---: | ---: |
| `0x200004a0` scan/status counter | `+0x00` | 396 |
| mode halfword `0x200004aa` | `+0x0a` | 0 |
| mode halfword `0x200004ac` | `+0x0c` | 2 |
| alternate numeric mirror `0x200004c2` | `+0x22` | 1 |
| associated enable/state `0x200004c4` | `+0x24` | 0 |
| ordinary gate byte `0x200004d8` | `+0x38` | 0 |
| root slot `0x200004e0` | `+0x40` | `0x20010000` |

The same-response root matches the reset-derived root and the prior live
root observation, satisfying the reviewed gate for a **conditional** image-1
interpretation of this first window. It remains a small-window structural
anchor, not a live core-tag measurement or whole-image identity proof.

Under the selected predicate body, `aa==1` selects mode 4 and
`aa!=1 && ac==1` selects mode 6. The late pair `aa=0, ac=2` therefore selects
neither special direct mode; a newly reached predicate with unchanged values
would take the mode-1 fallback. The value 2 is also a valid ordinary
post-scan selector state, so it must not be projected backward to the V6
predicate tail.

The zero at `0x200004d8` is consistent with the separately traced ordinary
post-fault gate: retained fault state can make the next ordinary caller skip
the packed scan. It is not proof that every scan path or interrupt source is
disabled.

## Second window: positive local-layout corroboration, not a whole-bank alias proof

The 16 raw candidate bus bytes are:

```text
70 08 80 07 40 0b 5c 01 03 00 00 00 00 00 00 00
```

The first six bytes exactly match the independently decoded image-1 startup
stores:

```text
u16 +0 = 0x0870
u16 +2 = 0x0780
u16 +4 = 0x0b40
```

This three-halfword match is positive local-layout corroboration for the
candidate `0x47000bc0` response. It is materially stronger than a lone zero
or a match at byte `+7`. In addition, candidate byte `+7` is 1 and the first
window's separately returned numeric mirror is also 1. That sequential
cross-window agreement further supports the intended local relation.

The evidence must retain its boundary. The actual secondary core tag was not
read; the two USB reads are sequential; the complete running body is not
identified; and a local structural match does not prove a universal
`0x4700...` alias. The wrapper correctly leaves this artifact labelled
`candidate-bus-bytes-only` and fixes
`consistency_promotes_alternate_cpu_alias=false`.

The live candidate callback bytes differ from the selected packaged AP_EXCO
defaults:

| byte | observed | selected packaged source |
| ---: | ---: | ---: |
| `+7` / proposed `0x20000bc7` | 1 | 20 |
| `+8` / proposed `0x20000bc8` | 3 | 0 |

Thus the packaged `20/0` pair must not be assumed live. The result is
compatible with a different or changed runtime source, later local writes,
or another unbounded producer; it does not select one explanation.

## Mirror/state mismatch corrects the ordinary model

The first window reports numeric mirror 1 and associated enable/state 0,
while the second reports candidate source byte 1. The selected VA `0xc250`
body compares the source byte with the numeric mirror and updates the mirror
and boolean state only when the numeric value changes. When source and mirror
are already equal it skips both writes.

Therefore `enable/state == (mirror != 0)` is not a valid continuously
maintained invariant. The observed `1/0` pair must be preserved rather than
normalized to `1/1`. It can arise from stale state, another writer, or
execution ordering not captured here; this review does not assign a cause.
The mirror update occurs before the later ordinary packed-scan gate, so the
current mirror can also be newer than the last retained score latch.

## Timing and bounded predicate compatibility

The active terminal uptime is `119358.55`. V6 observation ended at
`115907.45`, exactly **3451.10 seconds earlier**. The prior score/context
sample was at terminal uptime `117834.25`, approximately 1524.30 seconds
before this selector capture. These are not one predicate-time tuple.

If one applies the static predicate to the late values only, the observed
mode-1 fallback and nonzero alternate selector would choose `fp=R+0x24c4`,
whose earlier late sample was 40; the earlier non-mode-6 score latch was 44.
The numeric relation `44 > 40` is compatible with a taken predicate. It is
not causal or incident-time evidence because the mode/selector and score/fp
values were sampled sequentially about 25 minutes apart, and the ordinary
post-fault gate may have prevented score refresh.

## Limits

- No physical picture observation accompanies this read.
- No UI transition, blackout, repair, or named Samsung setting is proved.
- The read does not prove live core tag, immutable code body, or universal
  CPU/bus aliasing.
- The current selector and older score must not be relabelled as V6
  event-time state.
- The helper issued read operations only; it did not change the sampled
  memory, reset the controller, or retry the transaction.

