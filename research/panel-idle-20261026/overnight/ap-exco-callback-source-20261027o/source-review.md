# Managed AP_EXCO callback-source reader: independent source review

Recorded 2026-10-27 UTC. This is a read-only, offline review of the final
repinned candidate in `managed-usb-ap-exco-callback-read`. It made no TV,
network, root, USB, controller, device-node, helper-execution, UI, write, or
reset request. It did not modify the implementation, frozen evidence, or any
prior review.

## Verdict

**Clear for one separately authorized root-controlled invocation**, provided
the caller independently preserves the established pinned-boot and
ReadyForHeader lineage and supplies the exact reviewed manifest SHA-256.

- **P1 findings:** none.
- **P2 findings after final repin:** none.

During review, one P2 output-gating defect was found in the first candidate:
the saved-context correlation Boolean could become true from raw `3/1`
values even when the pointer binding failed. The builder corrected it before
this clearance. The final wrapper requires `pointer_matches is True` as well
as the two numeric values, and its focused regression covers the mismatched
pointer. This report applies only to the final pins below.

The helper is a fixed three-read diagnostic. It does not dynamically
dereference the returned pointer, write controller memory, reset anything,
retry, alter UI/configuration, or claim a physical/executing-core identity.

## Final pins

| item | SHA-256 |
| --- | --- |
| build manifest | `48b202a87cd714dab866a32cb36cb716a65cdec6745519463a346bab9d35f00a` |
| `Program.cs` | `cc90506197ba2784d0918b5cc9567d7fd78c5bcb10973c6b7bb90870080842be` |
| `run-once.py` | `a7d50ab656c727c2aab080410a1360db27f64051c0b488398eb9836651d0feae` |
| `test-wrapper.py` | `9633402f47cb209d3acf0302bf5bd3dbf26c8c551e252aa07165ed613703c6be` |
| native DLL | `dc33c7abb8010ec5b9ad36bdece053298370f1e8183ba7c2b83f80dfcccdb8e7` |
| pinned root adapter | `bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a` |

The final manifest contains exactly 12 expected source/runtime members. An
independent check reproduced every size/SHA row, all seven evidence pins, the
fixed protocol rows, and object arithmetic. The manifest records zero target
executions and pins the reviewed parent manifest
`3222c56b1b80749123a2b360ebae9ffbf44779cf748061737774c93fc153fa51`.

## Fixed protocol geometry

The native program hardcodes exactly these byte arrays:

| order | target | address/length | exact header |
| ---: | ---: | --- | --- |
| 1 | `0x101` | `0x470002c0 / 0x20` | `01010000c002004720000000` |
| 2 | `0x101` | `0x450158a8 / 0x10` | `01010000a858014510000000` |
| 3 | `0x101` | `0x45015c70 / 0x20` | `01010000705c014520000000` |

Each request is one exact 12-byte OUT followed by one exact-length IN, giving
exactly six bulk transfers. The native `Bulk` method accepts only an input
buffer of one of the three fixed sizes or an output buffer equal to one of
the three fixed headers. It uses only usbfs bulk, claim, and release ioctls;
there is no reset or memory-write request.

The corrected object arithmetic is consistent in source, tests, README, and
manifest:

```text
object bus extent       0x450158a8..0x45015c93  (0x3ec bytes)
base read               object +0x000..+0x00f
tail read               object +0x3c8..+0x3e7
source +0x3d8           tail response +0x10
pointer binding word    pointer response +0x0c
```

Native output independently records source bytes `+0`, `+1`, and `+0x3d8`.
It does not compare this corrected object against the ordinary AP_EXCO
`20/0` package values. Those older values belong to other objects and are not
used as defaults here.

## Fail-closed native state machine

Before every OUT and IN transfer, `Run` changes the protocol phase to
`Unknown`. It promotes the phase only after an exact transfer count:

```text
ReadyForHeader -> ExpectingPointerIn -> ReadyForHeader
               -> ExpectingBaseIn    -> ReadyForHeader
               -> ExpectingTailIn    -> ReadyForHeader
```

A negative, zero, short, long, or exceptional transfer remains `Unknown` and
cannot issue the next header. Failures before claim issue no header. An
identity change between FD validation and claim also stops before traffic.
Release and close are attempted only as lifecycle cleanup; neither is used to
recover an unknown parser phase. Acceptance requires complete stage,
ReadyForHeader, all three raw payloads, successful release, and successful
close.

Native FakeOps tests cover all four nonexact result classes and an exception
at each of the six transfers, with an explicit forbidden-next-call check for
every nonterminal failure. They also cover open/claim/identity and injected
preflight/FD failures, release/close failures, pointer mismatch, base/tail
short-read retention, exact headers, and descriptor-stream boundaries.

## Raw retention and interpretation gate

After each exact IN, the native program immediately computes and stores that
window's Base64 and SHA-256 before issuing the next header. It additionally
extracts only fixed offsets:

```text
pointer word       pointer[0x0c:0x10], little-endian
source byte +0     base[0]
source byte +1     base[1]
source byte +3d8   tail[0x10]
```

If a later window fails, previously completed windows remain in native
stdout. The wrapper retains the entire authenticated execute envelope before
parsing, so an exit-one/partial outcome leaves the private target stage and
host-side envelope/record for review rather than sending cleanup traffic.

A fully completed pointer mismatch is deliberately accepted as valid raw
transport evidence, while `InterpretationAccepted` is false and the label is
`pointer-anchor-mismatch`. All three raw windows are still saved locally. The
final saved-context correlation is correctly gated by:

```python
pointer_matches is True and byte_zero == 3 and byte_3d8 == 1
```

Thus matching numeric values cannot create a callback-source correlation
when the pointer anchor differs. Source `+1` remains a distinct raw field and
is not folded into the `+0/+0x3d8` comparison.

The result also fixes the interpretation bounds to sequential, non-atomic,
late-state evidence and explicitly sets current executing body, whole-core
identity, live-tuple inference, bus alteration, and physical-picture
observation false.

## Wrapper, authenticated envelope, and one-execution rule

The host wrapper is dry by default and execution requires:

- `--execute`;
- an absolute, nonexistent output directory; and
- the exact reviewed manifest SHA-256.

It verifies the complete local manifest, loads only the pinned root adapter,
creates a unique private `0700` stage, and uploads only three pinned runtime
files as root-owned `0600` regular non-symlinks. Every call rechecks the boot
and exact stage/file inventory as applicable.

The wrapper executes a complete target-side self-test first. There is exactly
one production `--execute` command and one `envelope = call(command)` site;
there is no retry loop or alternate address. Immediately before that call,
the durable record changes the target-operation count to unknown/in-flight.
It changes to the exact three-request count only after strict envelope and
native-outcome validation.

The execute command redirects stdout/stderr to private `0600` files, bounds
their sizes, verifies the exact five-file inventory, and returns boot,
uptime, exit code, byte counts, hashes, and framed Base64. On the host, the
complete authenticated call response is already in `record.json`; the
wrapper then writes `execute-envelope.txt`, validates its exact framing and
hashes, and writes `native.stdout.txt`/`native.stderr.txt` before interpreting
the native JSON.

Cleanup is permitted only for exit zero, empty stderr, one valid complete
native result, ReadyForHeader, exact ten-step sequence, exact raw hashes and
fixed-offset fields, and successful release/close. The cleanup command first
revalidates the exact five-file inventory and every mode/size/hash, removes
only those files and the unique stage, and requires `STAGE_ABSENT`. Rejected,
ambiguous, malformed, oversized, partial, or unknown outcomes retain the
stage and do not issue cleanup.

## Offline verification reproduced

The following were rerun locally without target access:

```text
native FakeOps self-tests       47 passed, targetOperations=0
wrapper tests                   24 passed, targetOperations=0
wrapper tests under python -O   24 passed, targetOperations=0
native dry geometry             exact three requests, writes=0, retries=0
host x64 --execute              REFUSED_ARM32_ABI, exit 64 before device access
mechanical derivative check     fixed requests=3, bulk steps=6, targetOperations=0
manifest/evidence audit         12 exact members, 7 exact evidence pins
```

The wrapper tests exercise accepted and pointer-mismatch parsing, the final
pointer-gated saved-context correlation, malformed terminal phase and step
counts, hash/offset/interpretation lies, framed-envelope prefix/suffix/noise
and hash failures, self-test count, dry geometry, fixed source tokens,
in-flight accounting, and adapter pinning under normal and optimized Python.

The tests do not run the production wrapper end-to-end with a fake root
transport. That is a bounded coverage limitation, not an observed source
defect: the orchestration is inherited from the separately reviewed pinned M
wrapper, while the derivative checker and direct review cover the modified
fixed geometry, parsing, output fields, one-execution site, and cleanup gate.

## Interpretation limits

An accepted future result would establish three sequential raw bus windows
and, only if the pointer equals `0x450158a8`, a conditional local association
with the corrected callback source object. It would not establish event-time
atomicity, a field name or physical unit, a writer, causality, current
instruction execution, a physical core or PC, whole-image identity, or panel
recovery. It provides no basis for a write, patch, threshold change,
protection bypass, persistence action, high-bank operation, POFLG operation,
or return-guard change.
