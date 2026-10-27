# AP_EXCO callback-source capture runtime review

Recorded 2026-10-27 UTC. This is an independent, offline audit of the retained
`capture-once` result. It read retained host files only. It made no TV,
network, root, USB, controller, device-node, helper, UI, write, reset, or
configuration request and did not import or execute the source builder. No
prior evidence or implementation file was modified.

## Verdict

The retained capture is internally complete and consistent with final build
manifest
`48b202a87cd714dab866a32cb36cb716a65cdec6745519463a346bab9d35f00a`.
It records one native execution, exactly three fixed reads/six exact bulk
transfers, expected pointer binding, correct fixed-offset extraction,
ReadyForHeader terminal phase, successful release/close, durable raw host
artifacts, and confirmed target-stage removal. There is no retry or
alternate-address attempt.

- **P1 findings:** none.
- **P2 findings:** none.

The positive result is narrow: at this late sequential acquisition, the
pointer window contained `0x450158a8`, source `+0` was `3`, source `+1` was
`10`, and source `+0x3d8` was `1`. This is not an atomic tuple, not the V6
event instant, not a physical-unit interpretation, and not proof of a writer,
causality, executing body/core, or panel state.

## Retained files and hashes

| artifact | size | SHA-256 |
| --- | ---: | --- |
| `record.json` | 324,975 | `808fde3bc9d655f4fc9551bb4924425db66e2298e232b64864378c9022439239` |
| `result.json` | 1,545 | `349139642d7e6b2f829a262ba5a26f15ecbe9067d28ee18facb41d8013f684d0` |
| `execute-envelope.txt` | 2,843 | `cb936b857f3c34b1a40077924c3916b48ee42f3f2652e4ec5792e1c1545b78b2` |
| `native.stdout.txt` | 1,875 | `f46515ad08eccbdb54acd4cb73c3e9d3b45c807d776ed94226142071dacda47e` |
| `native.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `selftest.stdout.txt` | 153 | `9ef06896e5c7134cbb18b18260c34456044ad2a4c498d0eb17be34c42fdc0254` |
| `pointer-window.bin` | 32 | `7634f63e1eace3b6da5f287655f1b1ef3ebdb81b22909605a467c2472af43cd3` |
| `callback-base-window.bin` | 16 | `21f2234ff842c398b65210295a7a5e15220503bc73240a0eb68e4b897929db47` |
| `callback-tail-window.bin` | 32 | `eb1b55a1e4f19a403134f7ddc3a4f7f3853f50ef06cb9b9e74a5659f6183323f` |

The record pins wrapper SHA-256
`a7d50ab656c727c2aab080410a1360db27f64051c0b488398eb9836651d0feae`
and root-adapter SHA-256
`bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a`.
It identifies boot `00000000-0000-4000-8000-000000000000`, terminal uptime
`123267.81 459854.02`, native exit zero, one native invocation,
`no_retry=true`, and `target_operations_status=accepted_exact`.

## Authenticated call chain and one execution

`record.json` contains 19 root-adapter calls. Independently decoding every
stored transport response found, for all 19:

```text
authenticated = true
uid = 0
euid = 0
one command
transport exit = 0
command exit = 0
```

The commands contain exactly one `--self-test` call and exactly one
`--execute` call. The self-test is preflight-only and reports:

```json
{"selfTestsPassed":47,"targetOperations":0}
```

The record progresses from private-stage creation and fixed-file staging to
self-test, one execute-envelope response, then one cleanup response. There is
no second execution, retry loop, dynamic address, or post-cleanup target
call in this capture.

## Exact native transport

The record's complete request list is:

| order | target | address | length |
| ---: | ---: | ---: | ---: |
| 1 | `0x101` | `0x470002c0` | 32 |
| 2 | `0x101` | `0x450158a8` | 16 |
| 3 | `0x101` | `0x45015c70` | 32 |

Native stdout contains exactly ten ordered steps:

```text
open, claim,
pointer-header OUT 12, pointer-data IN 32,
source-base-header OUT 12, source-base-data IN 16,
source-tail-header OUT 12, source-tail-data IN 32,
release, close
```

Every bulk count equals its expected count and every errno is zero. Claim,
release, and close all return zero. The result reports opened, claimed,
released, closed, and accepted true, with `Stage=complete` and
`ProtocolPhase=ReadyForHeader`. Thus the three reads account for exactly six
successful bulk transfers and leave the reviewed parser state ready for a
new header.

No native step is a write, reset, retry, alternate read, UI request, or
storage/configuration operation. `BusContentsAltered=false` is consistent
with the recorded fixed-read sequence.

## Raw-byte and offset verification

The raw windows are:

```text
pointer  0100000014ff00454e020145a8580145b6300145f0300145e0f0004591b60100
base     030a1100000000000000010000010000
tail     f00093239223fe000a00fa000700000001010001000000000200000000000000
```

The Base64 fields in native stdout decode byte-for-byte to the correspondingly
named `.bin` files. The native SHA fields, result SHA fields, independently
computed hashes, and file lengths all agree.

The fixed extractions independently reproduce:

```text
LE32(pointer[0x0c:0x10]) = 0x450158a8
base[0x00]                = 3
base[0x01]                = 10
tail[0x10]                = 1
```

In particular, `tail[0x0c]` is `7`, while `tail[0x10]` is `1`. This directly
confirms that the runtime result used the corrected callback-object geometry:
tail bus `0x45015c70` begins at object `+0x3c8`, so object `+0x3d8` is response
offset `0x10`, not the inherited old-object offset `0x0c`.

The native and wrapper consequently agree on:

```text
PointerMatches / pointer_matches_expected = true
InterpretationAccepted                    = true
Interpretation = conditional-local-pointer-binding-sequential-callback-source-samples
```

The 32-byte pointer window is byte-identical to the prior M capture and has
the same SHA-256
`7634f63e1eace3b6da5f287655f1b1ef3ebdb81b22909605a467c2472af43cd3`.
That repeatability supports the local pointer binding on this boot. It does
not promote the bus mapping into a universal alias or prove which core was
executing.

## Envelope, local evidence, and cleanup

The execute envelope has one exact set of markers and records:

```text
boot             00000000-0000-4000-8000-000000000000
uptime           123267.81 459854.02
native exit      0
stdout           1875 bytes / f46515ad...a47e
stderr           0 bytes / e3b0c442...b855
inventory        INVENTORY_OK
```

Independently decoding its framed stdout and stderr reproduced the retained
native files exactly. The native stdout hash also equals the record's
`native_outcome_sha256`. The self-test file hash equals the record's
`selftest_sha256` and its structured line reports 47 passing tests and zero
target operations.

Only after the complete terminal envelope and native result were validated
did the wrapper save all three local raw files and issue cleanup. The final
authenticated call revalidated the exact target inventory, file modes,
sizes, and hashes, removed exactly that private stage, and returned
`STAGE_ABSENT`. The record therefore correctly has
`cleanup_required=false` and `cleanup_stdout="STAGE_ABSENT\n"`. Host raw
artifacts, envelope, result, and authenticated record remain intact.

## Interpretation boundary

The result correctly records:

```text
transport_accepted                                  true
interpretation_accepted                             true
sequential_source0_and_3d8_match_saved_context_candidate true
samples_atomic                                      false
live_tuple_inferred                                 false
late_state_not_v6_event_time                        true
ordinary_object_default_comparison_performed        false
current_executing_body_proved                       false
whole_core_identity_proved                          false
physical_picture_observed                           false
```

The saved-context candidate Boolean is valid only as a pointer-gated numeric
comparison: late sequential source `+0=3` and source `+0x3d8=1` equal the
separately retained late context candidate. It does not show that the source
and context were sampled together, stayed unchanged between reads, or held
these values during V6. Source `+1=10` is a distinct unnamed byte and has no
saved-context/default comparison here.

No ordinary AP_EXCO `20/0` comparison was performed. Those values belong to
different objects and are neither expected values nor defaults for this
corrected callback source. None of the three observed values has a qualified
field name, unit, physical coordinate, or causal meaning.

This capture does not establish an event-time tuple, writer, mutation,
threshold, active predicate mode, executing program counter, physical core,
whole-image identity, panel recovery, or physical screen state. It provides
no basis for a write, patch, threshold change, protection bypass,
persistence action, high-bank operation, POFLG operation, or return-guard
change.
