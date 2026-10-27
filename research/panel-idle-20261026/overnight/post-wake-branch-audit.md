# Independent audit: post-wake branch snapshots

This is an offline audit of the two finite passive `/proc/706/mem` snapshot
attempts.  I made no target, network, device, getter, setter, ioctl, key, or
display-control call.  The first attempt remains rejected; only the corrected
second attempt satisfies the frozen reader's complete acceptance contract.

## Evidence identity

The frozen validator is `pqe-branch-baseline.py`, SHA-256
`84ff5138a7c4551b932b10360eb6b98d806dc2ef385497b4ec2f7123d6c27acb`.
The root client pinned by both wrappers is `s95f-access.py`, SHA-256
`3a92e02003ce51d2faeace231191f6f0c73731f2bfca9caa196e05b195b439a5`.

The failed wrapper is retained as
`post-wake-branch-20261026a/source.py`, SHA-256
`3b047fa6bb05972927b08be5c5ca24d032b87e8b239b8db4135fbecc027da854`.
Its command is 4,884 bytes, SHA-256
`7bf3924bc8eefc5b00a4c0590f035f9a5b593ca48f4a52d584445a5b3c3479ae`.
The corrected wrapper reviewed for the second attempt is
`post-wake-branch-snapshot.py`, SHA-256
`5a83f4701b06543825d0d93d287b2ab8b423a1df3fd68dbac5418ce844cd1162`.
Its generated command is 4,876 bytes, SHA-256
`8dae85983c09bae928f60e381bff8ff87065d509f8ab0100b9382792c49108d5`;
offline `bash -n` passed.  The command embedded in the successful root
response is byte-identical and has that hash.

### Retained attempt `a`

| file | bytes | SHA-256 |
| --- | ---: | --- |
| `client.stdout` | 54,577 | `4b0a30ad4f860c1bd3156b546406b85166de8f97e7b2d84f8e34d69c9d0e4ee0` |
| `client.stderr` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `intent.json` | 5,485 | `c6447c53c7f77501b3cfc66beaf17efd9bdf543ab4375772ccf8d597e8b967d8` |
| `result.json` | 5,588 | `ac401703952c588c18e01c3e390871559ab64ab3753c547cd82a6151449aa051` |
| `source.py` | 3,251 | `3b047fa6bb05972927b08be5c5ca24d032b87e8b239b8db4135fbecc027da854` |

### Corrected attempt `b`

| file | bytes | SHA-256 |
| --- | ---: | --- |
| `client.stdout` | 55,229 | `71a8b6ab023ec3ae258963ed621ec43757a3777695a1f19af7031f97a6ab0dc8` |
| `client.stderr` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `intent.json` | 5,461 | `d6fcee078d9a65dd9aec09cb009e41d59194d8f107eded824125d4d31c85b953` |
| `result.json` | 10,968 | `3d42ade67be9334a7af18dc7bf84da36134a2e209ef69f054dd8e4ac6fdadfe0` |

## Attempt `a`: retained but rejected

The root envelope authenticated model `QN77S95FAFXZC`, UID/EUID zero,
host-assisted persistence, and the controller's unchanged-global-files
invariant.  Its sole command returned zero without timeout, outer client
stderr is empty, and its raw stdout/stderr were retained.  The endpoint
identity blocks both say boot
`00000000-0000-4000-8000-000000000000`, AVOC PID 706/start ticks 603, and the
pinned AVOC/libave hashes.  Endpoint pointer text is also equal.

That is not enough to accept the attempt.  The target `tr` expression had the
runtime effect of deleting literal `n` (and backslash), rather than merely
removing base64 line breaks.  Both captured map payloads contain zero literal
`n` characters, decode to the same 15,853-byte corrupted byte sequence
(SHA-256
`49a73094b014741804b0a0e636143200509a51c5999f0c2ed92a6f53fcc71832`),
and fail gzip validation with `invalid code -- missing end-of-block`.  The
record correctly remains `accepted: false` with the base64/decompression path
failing before the frozen validator.  These bytes cannot prove source-map,
read-range, load-bias, or endpoint-map identity and cannot be repaired by
whitespace normalization.  Consequently the otherwise framed memory blocks
in attempt `a` are only retained provisional bytes, not an accepted snapshot.

## Attempt `b`: independently accepted

The corrected command leaves the target `base64` wrapping intact.  Offline replay of
the raw response performed strict base64 decoding after joining captured
lines, gzip validation, bounded expansion, substitution into a deep copy of
the response, and then invoked the unchanged frozen validator.  Both gzip
streams are 16,105 bytes with SHA-256
`521eba6720dfd84065b4bbe581ba818295ef5f25cafdf77cff740e501f1ddce6`.
Both expand to 139,243 bytes with SHA-256
`e1c212b73312716846c5cc324500ef79d1a7a28c936f9fb10e9d7626f290ab6f`.
The expanded start and end maps are byte-identical.

The replay also confirms:

- authenticated root, UID/EUID zero, host-assisted persistence, and the
  controller's unchanged-global-files invariant;
- exactly one byte-bound command, exit zero, no timeout, empty outer client
  stderr, and the exact expected `dd` inventory;
- identical endpoint boot/PID/executable/start ticks/source hashes, identical
  complete process maps, and identical endpoint pointer chains;
- the unique executable offset-zero libave load at bias `0xf6b77000` and all
  source/read ranges backed by the expected mappings;
- exact `RoseMVideoEnhancer`, base `QDDimming`, and typed
  `DimmingBackendRoseMQD` object/vptr/slot relationships, including Q header
  agreement with the guarded pointer chain;
- all 292 requested memory bytes present; and
- monotonic uptime 74541.43 through 74542.35 (0.92 seconds).

My independently regenerated validator summary is structurally equal to the
summary retained in `result.json`.  Therefore attempt `b`
is accepted for the reader's narrow technical scope.

## Accepted values and comparison

The accepted snapshot records working duty `207 / 207` and typed backend
cache `207`; the Weber policy word at `inner+0x458`, static gain, and target are each `1023`,
with target count `0`.  The exact-base-QD AutoPowerOff count and raw AutoDim
argument are both `0`.  The guarded branch fields are:

| field | value |
| --- | --- |
| `inner+0x000` | 89 |
| aligned `inner+0x038` / low byte | 256 / 0 |
| weights `inner+0x088`, `inner+0x098` | 102 / 43 |
| floor `inner+0x0a4` | 0 |
| sources `inner+0x0f8/+0x0fc` | 100 / 17 |
| model/control `inner+0x188/+0x18c` | 0 / `0xffffffff` |
| gain/AutoDim `inner+0x2a4/+0x2a8` | 1024 / 0 |
| product `inner+0x450` | 0 |

Against the start-qualified rescued owner-power-on sampler interval
(uptime 73052.26--73136.66), all overlapping stable QD/backend/branch fields
remain equal: initialized low byte one, duty/cache 207, Weber/gain/target
1023, target count zero, gain/AutoDim 1024/0, and AutoPowerOff count zero.
The rescued interval's one changing QD subfield, raw `inner+0x45c`, ended at
52; it is 39 in accepted attempt `b`.  The rejected attempt `a` provisionally
contained 108 at the same offset.  This is consistent only with the prior
bounded observation that this unmapped raw field changes; it supplies no
timer, brightness, fault, or physical-panel meaning.  The accepted snapshot
does not include the rescued deviced `OP+0x24` or power-state-index fields, so
it cannot compare those transitions.

## Limits

This was sequential, non-atomic process-memory sampling.  Equal endpoint
pointers and maps do not exclude a value changing away and back.  Concurrent
daemon activity is not excluded.  The owner-last-reported-black annotation is
not time-calibrated to the 0.92-second read and the validator deliberately
reports physical state as unobserved.  No software value here proves panel
light, lower transport success, current branch selection, fault onset, or
causality.  Attempt `b` is a valid software-state baseline only; attempt `a`
remains a preserved acquisition failure.
