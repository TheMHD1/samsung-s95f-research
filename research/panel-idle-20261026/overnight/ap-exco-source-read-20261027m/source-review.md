# Managed AP_EXCO source reader: independent offline source review

Recorded 2026-10-27 UTC. This review began only after the implementation
owner declared the final build frozen. It inspected the final source,
wrapper, tests, native artifacts, and manifest entirely offline. It made no
TV, root, USB, controller, network, UI, or target request and did not modify
the implementation or frozen evidence.

## Verdict

**Clear for one separately authorized, controlled invocation, subject to the
external known-`ReadyForHeader` precondition and the pinned boot identity.**

- **P1 findings:** none.
- **P2 findings:** none.

The native implementation has exactly three fixed target-`0x101` reads and
six bulk transfers. Every non-exact count or exception stops before any later
header. It retains every prior exact window, always attempts release/close
when applicable, makes no memory-write/reset request, and gates semantic
interpretation on the conditional pointer word. The wrapper performs one
native invocation, retains the authenticated raw response before parsing,
does not retry, and cleans the private target stage only after a strictly
validated complete result.

One non-blocking test-coverage note remains: `test-wrapper.py` exercises the
parsers, dry contract, pins, and important rejection cases, but does not run
the wrapper's complete `main()` orchestration against a fake authenticated
root transport. The one-execute/no-retry and retain-before-parse properties
are clear from direct source review and the pinned inherited root adapter;
future hardening could turn them into an end-to-end fake-transport test. This
is not a P2 defect in the reviewed implementation.

## Final identities

| artifact | SHA-256 |
| --- | --- |
| `build-manifest.json` | `3222c56b1b80749123a2b360ebae9ffbf44779cf748061737774c93fc153fa51` |
| `Program.cs` | `99fe549a5b4c408e6c83a44675cdd7c5f975231f2495e07b1bc9481939d6dc60` |
| `run-once.py` | `79341a52a0c69031a2d489d35c80997997b80b75661814637f6de27836221106` |
| native DLL | `9e38d3f2f4cf7664894cbfc8b209aef476d1580b77e8d0100793e606e6702871` |
| pinned root adapter | `bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a` |

The manifest contains exactly the 12 files required by `load_contract`:
nine source/configuration files and the DLL, deps file, and runtimeconfig.
Every recorded size and digest matched the file on disk. The wrapper requires
the externally supplied exact manifest SHA-256 before staging and re-hashes
every local manifest member. It also re-checks every staged file's size,
SHA-256, ownership/mode, non-symlink status, and exact directory inventory.

The final manifest explicitly fixes:

```text
interpretation scope  conditional-local-pointer-binding-sequential-only
samples_atomic        false
live_tuple_inferred   false
```

Those qualifications are reflected in both native/wrapper output and avoid
promoting three sequential reads into an atomic live tuple.

## Native fixed-transfer review

The only accepted execution CLI is exactly `--execute`; zero arguments are
dry-run, exactly `--self-test` is fake-only, and every other CLI returns 63.
Actual execution refuses unless the process is 32-bit, the packed usbfs bulk
structure is 16 bytes, and the host is little-endian. On this review host,
`--execute` refused before any device access with exit 64 and
`REFUSED_ARM32_ABI`.

The headers and read buffers are compile-time fixed:

| order | OUT header | subsequent IN |
| ---: | --- | ---: |
| 1 | `01010000C002004720000000` | 32 bytes |
| 2 | `0101000014FF004510000000` | 16 bytes |
| 3 | `01010000E002014520000000` | 32 bytes |

Decoded as three little-endian words, these are exactly:

```text
(0x101, 0x470002c0, 0x20)
(0x101, 0x4500ff14, 0x10)
(0x101, 0x450102e0, 0x20)
```

`RealOps.Bulk` accepts an OUT buffer only when it equals one of those three
headers and accepts an IN buffer only at one of the three fixed lengths. The
stateful `Run` sequence narrows that set to the exact order above. Endpoints
are fixed to `0x02` OUT and `0x82` IN, with a 2,000 ms timeout per transfer.
There is no target memory-write header, caller-selected address/length,
control reset, device reset, detach, or retry path.

### Exact six-transfer state machine

Each `Read` starts only in `ReadyForHeader` and performs:

1. set phase to `Unknown` before sending the header;
2. promote to the read-specific expected phase only if OUT count is exactly
   12;
3. reject any negative, zero, short, or long OUT count;
4. set phase to `Unknown` before receiving data;
5. promote back to `ReadyForHeader` only if IN count equals the exact fixed
   buffer length;
6. reject any negative, zero, short, or long IN count.

An exception unwinds from `Read`; the catch block preserves `Unknown` unless
the last transfer had already returned exactly to `ReadyForHeader`. There is
no loop, retry, recovery header, or later call after the failure. Release and
close occur only in `finally` and are local usbfs lifecycle operations, not
protocol recovery.

The 47 native FakeOps cases cover successful completion, pointer mismatch,
base/tail late failure retention, open/claim/identity failure, exceptions in
all preflight phases, and for each of the six transfers: negative, zero,
short, long, and exception outcomes. For steps 0 through 4 the test also
asserts the immediately later transfer/header is absent. Release failure and
close failure both reject acceptance. No C# `assert` is used, so optimized
execution does not remove checks.

## Raw retention and interpretation gate

After each exact IN completes, `Run` immediately serializes that full window
and its SHA-256 before issuing the next header:

```text
PointerBase64 / PointerSha256  after exact pointer IN
BaseBase64    / BaseSha256     after exact source-base IN
TailBase64    / TailSha256     after exact source-tail IN
```

Therefore a later base or tail failure preserves all prior exact windows in
the final native JSON. A non-exact current IN is not represented as a falsely
complete window. This matches the manifest's precise claim that a late or
partial failure preserves **prior exact** windows.

The pointer word is decoded only at pointer-window offset `0x0c`. Transport
completion does not depend on its value: a mismatch still collects and
retains the two statically qualified fixed source windows. Semantic
interpretation is accepted only when:

```text
LE32(pointer[0x0c:0x10]) == 0x4500ff14
```

On equality, the label is
`conditional-local-pointer-binding-sequential-source-samples`; on mismatch,
it is `pointer-anchor-mismatch`. The wrapper recomputes the pointer word,
both selected source bytes, every window SHA-256, and the interpretation gate
from decoded raw bytes; it does not trust the native summary fields alone.
The result also carries `samples_atomic=false` and
`live_tuple_inferred=false`.

This is consistent with `address-review.md`: equality is a narrow local
binding, not proof of the whole `0x4700....` alias, active configuration bank,
executing-image identity, event-time state, or physical panel meaning.

## USB lifecycle and identity checks

Before claiming interface 2, `RealOps` requires:

- exact boot ID `00000000-0000-4000-8000-000000000000`;
- USB runtime state already `active`;
- exact Samsung VID/PID, configuration, authorization, and cached descriptor
  bytes;
- exact vendor interface number/class/subclass/protocol and no bound driver;
- bus 7 and a bounded device address;
- an `O_RDWR|O_CLOEXEC|O_NOFOLLOW` device-node open;
- `statx` proof that the opened FD is the expected USB character device;
- exact 18-byte descriptor identity from that already-open FD; and
- a second preflight returning the same bus/device identity before claim.

Claim must return exactly zero before any bulk traffic. Once claimed, release
is attempted even after protocol failure; once opened, close is attempted.
Acceptance requires successful release and close in addition to complete
fixed traffic and terminal `ReadyForHeader`. A cleanup failure changes native
exit to rejection, so the wrapper retains the remote stage for review.

## Wrapper and authenticated-envelope review

The wrapper is dry by default. Execution additionally requires an absolute,
fresh output directory and the exact reviewed manifest SHA. It loads only the
hash-pinned root adapter. That adapter records raw transport stdout/stderr in
`record.json` before checking response size, transport exit, strict UTF-8
JSON, authentication, UID/EUID, and exact command echo through its inherited
`validate_response` contract.

The wrapper stages a root-owned mode-0700 directory with only three pinned
runtime artifacts, each regular, non-symlink, root-owned mode 0600, exact
length, and exact SHA-256. It runs the fixed self-test first. The production
command contains exactly one:

```text
/usr/bin/dotnet <fixed staged DLL> --execute
```

stdout and stderr are redirected to private mode-0600 files. Before that
single call, the durable record changes operation accounting to
`inflight_or_unknown`; it changes to three exact target read requests only
after validating the terminal envelope and native outcome. There is no retry
branch and exactly one production `envelope = call(command)` site.

The remote envelope binds boot ID, uptime, native exit, exact stdout/stderr
sizes and SHA-256 values, exact terminal inventory, and framed base64. The
authenticated root response is already durably present in the record when
`call` returns. The wrapper then saves `execute-envelope.txt`, decoded native
stdout, and decoded native stderr before semantic parsing. Malformed,
unauthenticated, oversized, nonzero-exit, nonempty-stderr, non-ready,
non-exact, or inconsistent results stop without cleanup; the record and
private remote artifacts remain available. Cleanup is a separate root call
permitted only after strict exit-zero, empty-stderr, exact six-transfer,
release/close, raw-hash, interpretation-gate, and `ReadyForHeader`
validation.

The wrapper's final extracted `.bin` files are written before cleanup and
their hashes/lengths are repeated in `result.json`. Pointer mismatch is not
misreported as an AP_EXCO semantic sample: transport evidence remains
accepted, while `interpretation_accepted` is false.

## Independently reproduced offline checks

The following final-pinned checks were rerun without target access:

```text
python3 test-wrapper.py
  {"wrapperTestsPassed":22,"targetOperations":0}

python3 -O test-wrapper.py
  {"wrapperTestsPassed":22,"targetOperations":0}

dotnet ManagedUsbRtBlockReadOnce.dll --self-test
  {"selfTestsPassed":47,"targetOperations":0}

dotnet ManagedUsbRtBlockReadOnce.dll
  exact dry schema, three headers/lengths, writes=0, retries=0

dotnet ManagedUsbRtBlockReadOnce.dll --execute
  REFUSED_ARM32_ABI, exit 64, before device access

manifest inventory and every one of 12 size/SHA rows
  PASS
```

Five additional one-off parser mutations were also rejected: decoded pointer
field mismatch, invalid raw base64, nonzero transfer errno, a false
`BusContentsAltered` claim, and an interpretation-gate inconsistency. These
checks performed zero target operations.

The existing wrapper suite also rejects wrong terminal stage/phase, a raw
hash mismatch, a false interpretation gate, a short recorded transfer, an
extra step, leading/trailing/interior envelope noise, and an envelope digest
mismatch. It checks the exact dry request list, root-adapter pin, and durable
inflight-accounting statement order under both normal and optimized Python.

## External conditions not supplied by this helper

The helper cannot passively discover the controller parser's preexisting
phase. A separately reviewed, closed-world lineage must establish
`ReadyForHeader` immediately before invocation; absence of old processes or
files is not sufficient. This review does not authorize a live call and does
not establish that external precondition.

The fixed boot ID is intentionally fail-closed. Any reboot makes this build
refuse and requires a new review/re-pin rather than substituting a new boot ID
at the command line. The three reads remain sequential and can observe state
changes between them. No result from this reader alone authorizes a write,
threshold change, protection bypass, reset, persistence action, high-bank or
POFLG operation, or return-guard modification.
