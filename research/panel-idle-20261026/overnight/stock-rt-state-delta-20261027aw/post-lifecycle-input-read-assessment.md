# Independent assessment and runtime audit of the late W input snapshot

Recorded 2026-10-27 UTC. This review was read-only with respect to the TV. It
made no TV, network, USB, UI, power, reset, or firmware call. The only file
created by this reviewer is this report.

## Result

**PASS, with no P0/P1 finding, for the one completed late snapshot.** Reusing
the unchanged W helper was a bounded way to collect a later ordinary/derived
object state after the stock lifecycle. The result is transport-complete,
pointer-gated, read-only, terminal in `ReadyForHeader`, and cleaned up. It is
not a combined or onset collector and does not recreate the rejected AL
design.

The new sample materially narrows the compatible ordinary state:

| field | earlier W and AK reuse | late post-lifecycle W |
| --- | ---: | ---: |
| ordinary `+0xca` | 1 | 1 |
| ordinary `+0x116` | 1 | 1 |
| ordinary `+0x10a` | 62590 | 31868 |
| ordinary `+0x10c` | 125 | 0 |
| ordinary `+0xe6` | 1 | 0 |
| ordinary `+0x2fc` | 0 | 0 |
| ordinary `+0x300/+0x302` | 0 / 0 | 0 / 0 |
| derived `+0/+1/+0x3d8` | 3 / 10 / 1 | 3 / 8 / 0 |

The late values satisfy the selected-source relationship
`derived[+0x3d8] = bool((ordinary[+0xe6] & 1) OR ordinary_u16[+0x2fc])`:
both operands and the derived byte are zero. The accompanying derived `+1`
change from 10 to 8 is also numerically compatible with the separately
recovered selected-image callsite that chooses 10/8 from nonzero/zero
`+0x3d8`.

This supports a genuine difference between the two **late sequential object
snapshots**, conditional on the same selected image-0 layout and CPU/bus
interpretation. It does not establish when the values changed, that MODE2
caused the change, that the callback copied the value during the observed
lifecycle, or that the physical panel emitted light.

## Pre-execution qualification

The exact unchanged helper pins are:

| artifact | SHA-256 |
| --- | --- |
| build manifest | `5d760fbdabf7b23b6e57f13fc40914a8ede43bf1b488738dc7c42f203321ca69` |
| wrapper | `92b6b36e9001fed8817d3b34420fd5b85cb5cf25c20f5a957c6d8deeb3f9b37e` |
| native source | `ef5dd6f33a9daece5fbcaca8decf1328128a0b648268d21a1dc97d28da9136b9` |
| native DLL | `6ee73254087fcf34e19159b25b16d3cd3afd8e63ee033fcc19db5f7b3473e0b0` |
| root adapter | `bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a` |

The manifest records 48 native fake-operation tests, 26 wrapper tests in
normal mode and 26 under `-O`, host-ABI refusal, unknown-CLI refusal, and zero
build-time target operations. The live self-test reproduced exactly 48 passes
and zero target operations, followed only by two classified `GC_INFO` rows.

The helper has exactly three fixed target-`0x101` reads, in this order:

1. `0x470002c0`, 32 bytes (pointer anchors);
2. `0x4500ff14`, 824 bytes (ordinary AP_EXCO prefix); and
3. `0x450158a8`, 1004 bytes (complete derived object).

It therefore makes six bulk transfers total. It has no write, retry, reset,
UI action, caller-selected address, dynamic pointer dereference, or storage
operation. The first response must contain the two exact dependent-window
pointers before either dependent request is admitted. A transport ambiguity
would stop all later headers; a pointer mismatch would retain the pointer raw
bytes and stop in a known Ready phase.

The separate host preflight is pinned by
`input-host-preflight.json` (SHA-256
`de2778beefe7a5736fcaf7439bb4b24dbb087177e1afef4d7787f461c343f7f7`).
Its one authenticated root call observed the same boot ID
`00000000-0000-4000-8000-000000000000`, USB device 46 with
`04e8:2001`, revision `0250`, configuration 1, all three interfaces unbound,
and zero usbfs file-descriptor holders. It ended at uptime `137665.37`; the
private W stage was created at `137703.31`, 37.94 seconds later. This is a
reasonable bounded collision check, not a proof that no firmware task or
unrecorded actor could race after the scan. The execution additionally relied
on the recorded lineage that post-X ended in `ReadyForHeader` and no
intervening vendor OUT was issued.

## Independent runtime reconstruction

The completed capture is under `post-lifecycle-inputs/`. Its principal pins
are:

| artifact | SHA-256 |
| --- | --- |
| `record.json` | `f4722be28e23b953c1befbd60482f592741b90b231bc43dd415f66ae04946cd9` |
| `result.json` | `778cb7e9ab4f3950c6a466f799e41b13115e0b9e4cef8f8ac412466041d90e57` |
| `execute-envelope.txt` | `1a28b4f13c1e5d7f755f182308e2852e9676b9b8e5e88ba96b37469279162c49` |
| `native.stdout.txt` | `a41b11bcf5cfba7af9691292f0bdb7fe4efdff130bb909b8ff138ba9351e10b4` |
| `native.stderr.txt` | empty SHA-256 `e3b0c442...b855` |
| pointer window | `7634f63e1eace3b6da5f287655f1b1ef3ebdb81b22909605a467c2472af43cd3` |
| ordinary window | `94839af14f71937d0defd81b380d277f092d8a9add3f782731da835a66dee2cf` |
| derived window | `eb15688aac78bcaf6ca12d34249898b355df5d4f7332b97e9d9b325852be4694` |

I independently replayed the retained parser contract against the saved
envelope and native stdout, then reconstructed each binary from the native
base64. The reconstructed bytes, lengths, and SHA-256 values exactly equal the
three saved binary files. The 32-byte pointer response is unchanged from both
earlier accepted W captures and contains `0x4500ff14` at `+4` and
`0x450158a8` at `+0xc`.

All 20 saved root calls pass the retained transport/authentication checks:

- transport exit 0, no host timeout, empty transport stderr, and response
  within the 64-KiB cap;
- authenticated model `QN77S95FAFXZC`, UID/EUID 0, host-assisted root, and
  the acquisition system-file invariant true;
- exactly one echoed target command per response, target exit 0, no remote
  timeout, and empty target stderr;
- every command is within 8192 bytes and records the 45-second remote and
  75-second host limits; and
- base64-decoding each retained transport stdout reproduces its parsed JSON
  response exactly.

There was one native invocation. Its strict envelope reports boot ID match,
target uptime `137706.50`, native exit 0, 4446 stdout bytes with the saved
hash, empty stderr, and exact terminal inventory. The native result has the
ten expected ordered steps: open, claim, three exact 12-byte OUT headers,
exact IN counts 32/824/1004, release, and close. All six bulk counts are exact
with errno 0. The terminal phase is `ReadyForHeader`; open, claim, release,
close, acceptance, pointer match, and bounded interpretation are all true.
The record consequently accounts for three exact read requests, one native
invocation, no retry, and no altered bus contents. The final authenticated
cleanup returns `STAGE_ABSENT`; `cleanup_required` is false.

## Relationship to AV and remaining limits

The AV retained bytes independently show candidate C byte `+7` changing from
1 before the lifecycle to 0 in the delayed post-X cycle, while M byte `+0x2a`
changed from 40 to 200. The new W capture occurred at terminal uptime
`137706.50`, about 784.26 seconds after post-X ended at `136922.242531`.

Under the selected-image callback trace, derived object `+0x3d8` is a source
for context byte `+0x6c7`, which is numerically compatible with the saved C
`+7` value. The new W `+0x3d8=0`, together with ordinary `+0xe6=0` and
`+0x2fc=0`, therefore supplies useful later corroboration for the zero state.
It is not an atomic equality proof: AV C and W derived/ordinary were captured
about 13 minutes apart, and callback execution or intervening writers were
not observed.

W has no direct read or qualified semantic equation for M `+0x2a`. It cannot
explain that byte's 40-to-200 transition. At most, the new ordinary/derived
state is another late state associated with the same post-lifecycle boot.

The ordinary 824-byte and derived 1004-byte raw windows changed in 32 and 16
byte positions, respectively, relative to both earlier identical W samples.
That establishes changed retained bytes, not the time, order, units, or
physical meaning of every changed field. In particular:

- the three USB reads are sequential, not atomic;
- the active image-0 generation, executing core, and global CPU/bus alias are
  not proved by the two local pointer matches;
- image-1 equality between the two retained generations does not prove the
  image-0 code body was executing during this read;
- no current RT tuple was sampled with W, so the prior post-X clean tuple is
  not assumed current at uptime `137706.50`;
- there was no physical picture observation; and
- the result narrows compatible ordinary/derived diagnostic state, but does
  not by itself identify why a selector changed, prove MODE2 causality, or
  establish a repair.

No repeat W execution is indicated by this audit. The single accepted result
already answers the bounded late-state question and should be retained as the
comparison point.
