# Independent runtime review: fault-context read after V6

Date: 2026-10-27 UTC  
Scope: offline replay and byte-level review only; no TV, root, USB, network,
UI, reset, or storage action

## Findings

### No runtime acceptance defect found

The retained run is a complete accepted execution of the reviewed helper
manifest
`c64d77d8356fde3867490155095e1ef240151634f1c72a529a43970055f5aa7e`.
The runtime artifacts have these independent hashes:

| artifact | bytes | SHA-256 |
| --- | ---: | --- |
| `record.json` | 310586 | `017e4b0a749b95a7df3dcc35a7a60fb4a2bed060ddebcb9d97718a7e952acac5` |
| `execute-envelope.txt` | 2568 | `093c94de788ebd4c3a4a7877fa4ae1b9a67a7c423bd317f29319f965d87a41bb` |
| `native.stdout.txt` | 1669 | `2710fe30ebab011cb9b70bf73e6e50bc42e0dc849634090e9d2bf31f780d8ab7` |
| `native.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `context.bin` | 64 | `0683bb72c1bb998774ba4747987ec82ac938ce892ede62d877b9a1da641f2439` |
| `rt.bin` | 256 | `91055b0ce0f0b798a78313bd90520506f63261fa1c35d78a0de85b2d332379f9` |
| `result.json` | 651 | `8c03aa8af4155f77adca558dcbbb8f37ee6fe0f03e1efa9c4450634c28dacdec` |

All 19 retained root calls independently pass the pinned authenticated
response validator against their exact command text. Every call has exit
zero, empty transport stderr, no host timeout, the expected 45-second remote
and 75-second host bounds, and a command length below 8192 bytes. The raw
base64 transport records reconstruct the saved authenticated response
objects exactly.

The call sequence is one private-stage creation, exact chunked upload and
verification of three artifacts, one zero-I/O self-test, one and only one
`--execute` invocation, and one cleanup. The self-test reports 34 tests and
zero target operations. The active envelope is strictly framed, boot-bound
to `00000000-0000-4000-8000-000000000000`, exits zero, has empty stderr, and
hashes to the saved native stdout.

The native transcript is exactly:

| step | direction | exact count | errno |
| --- | --- | ---: | ---: |
| open | local | fd 25 | 0 |
| claim | local | 0 | 0 |
| context header | OUT | 12 | 0 |
| context data | IN | 64 | 0 |
| RT header | OUT | 12 | 0 |
| RT data | IN | 256 | 0 |
| release | local | 0 | 0 |
| close | local | 0 | 0 |

Its final stage is `complete`, protocol phase is `ReadyForHeader`, and all
opened/claimed/released/closed/accepted booleans are true. The two returned
base64 fields reproduce `context.bin` and `rt.bin` byte-for-byte and reproduce
their embedded hashes. The staged DLL hash is the reviewed
`cd80eafa03fdcf9f3cc514434aef78ccd25228bb3b5cbe058d93dcb788e32127`,
which fixes the headers to target `0x101`, `0x47010f00/64` and
`0x47012400/256`.

Cleanup first revalidated the exact five-file inventory, ownership, modes,
sizes, and hashes, removed only those five files and the exact private
directory, and returned `STAGE_ABSENT`. The final record says two exact
accepted target operations and `cleanup_required=false`.

### The sampled numeric state is exact, but late and sequential

Little-endian decoding gives:

| returned window field | value |
| --- | ---: |
| `+0x0f04` shared latest `T` latch | 0 |
| `+0x0f06` mode-6 `r7` latch | 54 |
| `+0x0f08` shared non-mode-6 `r7` latch | 44 |
| `+0x2430` candidate `fp` | 200 |
| `+0x2432` candidate `fp` | 0 |
| `+0x2440` candidate `fp` | 0 |
| `+0x249e` predicate gate | 1 |
| `+0x24a0` source threshold | 160 |
| `+0x24a2` mirrored `q` | 0 |
| `+0x24c0` candidate `fp` | 200 |
| `+0x24c4` alternate candidate `fp` | 40 |
| `+0x24d2` T-calculator selector | 1 |
| `+0x24d6` T-calculator field | 10 |

The RT prefix also has `+0x2400=1`, logger gate `+0x2406=0`, fault
`+0x240a=0x1001`, `+0x240e=0`, and raw field `+0x2410=4`. Its first 64 bytes
are byte-identical to V6 `restored-rt.bin`, SHA-256
`2175e6ce7455123b8071e9edb3b3ada855107d182650c47a307f31bdd39a6ab8`.
That establishes stability of this window prefix across the retained
samples, not event-time identity for the newly read latches and thresholds.

The active result is around uptime `117834`; V6 observation ended at
`115907.45`, approximately 1926.6 seconds earlier. The context read and RT
read are sequential and have no per-step timestamps. Scans could update a
latch before, between, or after them.

### Predicate-compatible numeric pairings, without selecting a mode

Under the separately documented CPU/bus alias hypothesis, the late values
permit these numeric comparisons:

| predicate branch | sampled `r7` source | sampled `fp` | late inequality |
| --- | ---: | ---: | --- |
| mode 1, selector byte zero | shared `+0x0f08` = 44 | `+0x2430` = 200 | `44 > 200` false |
| mode 1, selector byte nonzero | shared `+0x0f08` = 44 | `+0x24c4` = 40 | `44 > 40` true |
| mode 4 | shared `+0x0f08` = 44 | `+0x2440` = 0 | `44 > 0` true |
| mode 6, selector byte zero | `+0x0f06` = 54 | `+0x24c0` = 200 | `54 > 200` false |
| mode 6, selector byte nonzero | `+0x0f06` = 54 | `+0x24c4` = 40 | `54 > 40` true |
| mode 2 code branch | shared `+0x0f08` = 44 | `+0x2432` = 0 | `44 > 0` true |
| fallback/other, selector zero | shared `+0x0f08` = 44 | `+0x2430` = 200 | false |
| fallback/other, selector nonzero | shared `+0x0f08` = 44 | `+0x24c4` = 40 | true |

The selected image has direct callers for modes 1, 4, and 6; mode 2 has a
predicate branch but no recovered direct caller, and indirect calls were not
excluded. The CPU selector byte `0x20000bc7` and the direct-caller mode flags
were not sampled, so both selector outcomes must remain listed. More
importantly, `+0x0f08` is one shared latch for every non-mode-6 invocation,
not a separate retained value for each possible mode. It cannot be paired
with all of those thresholds as simultaneous state or used to choose which
mode ran.

These comparisons show only which branches are numerically compatible with
the late samples. They do not prove that 44 or 54 was the V6 event's `r7`,
that the selected threshold was 0, 40, or 200 at that instant, or that any
particular mode caused the physical blackout. The bus-to-CPU interpretation
also remains conditional because the live core tag was not read.

## Decision

The runtime capture and cleanup are accepted as exact bounded evidence. No
transport, framing, hash, step-order, protocol-phase, or cleanup discrepancy
was found. The useful new result is a late, read-only set of latch and
threshold values with several compatible predicate branches; it is not an
event-time reconstruction, a selected fault mode, a physical cause, or a
repair.
