# Managed selector-1 code-fingerprint reader: independent source review

Recorded 2026-10-27 UTC. This review began only after the builder declared
the final candidate stable and supplied its final pins. It inspected the
implementation, wrapper, manifest, expected-source bytes, and focused tests
offline and read-only. It made no TV, root, network, USB, controller,
device-node, helper-execute, memory-read, write, reset, UI, or cleanup call.

## Verdict

**Clear for one separately authorized root-run fingerprint invocation,
subject to an externally established `ReadyForHeader` lineage and the pinned
boot identity.**

- **P1 findings:** none.
- **P2 findings:** none.

The native implementation hardcodes exactly the three qualified candidate
code windows and performs exactly six ordered bulk transfers. Every
non-exact count or exception stops before any later header. Every prior exact
window is serialized and hashed before the next request. Content mismatch is
accepted as valid transport evidence, retained without address substitution,
and never promoted to current executing-core or whole-image identity. The
host wrapper retains the authenticated raw envelope before parsing, performs
no retry, and removes its private stage only after strict terminal validation.

A non-blocking coverage note remains: `test-wrapper.py` tests native/envelope
parsers, dry geometry, pins, mismatch handling, and rejection cases, but does
not exercise the wrapper's complete `main()` orchestration with a fake root
transport. The one-execute/no-retry, durable inflight accounting, and
retain-before-parse properties are nevertheless direct in the reviewed source
and inherited pinned root adapter. This is not a P2 implementation defect.

## Final reviewed identities

| artifact | SHA-256 |
| --- | --- |
| `build-manifest.json` | `550be573257e5d8e726fbf5b4d223a4eeb82e03376edde5dd8062a0eeb37662c` |
| `Program.cs` | `11fc7fd599c502a0f75c38d1c216a0de844dbd9f47e4169e8f57a627b13a081e` |
| `run-once.py` | `d58abdebd1e81f17465e7d0654295e371f01ff750d619e0dbba89344cb84fbf8` |
| native DLL | `dd7b57b2be34c6a08066d9b9b6b7c53219345853ce74135719189b45577e1c70` |
| pinned root adapter | `bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a` |

The manifest has exactly the 13 members required by `load_contract`: ten
source/configuration/documentation files and the three staged .NET runtime
artifacts. Every recorded size and SHA-256 matched its final file. Execution
requires the caller to supply the exact reviewed manifest SHA; the wrapper
then re-hashes all local members and every staged file, verifies exact
inventory, ownership/mode, regular-file status, and non-symlink status.

The manifest also pins the independent address qualification:

```text
report   d14282ce16dac0b6a594bfdcce078170d28264c54c515f3b02ad670477901c2a
verifier 6f645c0bc6fc90f92c4f3180a053a1be6d47734fcaf7eb234a9906f5322ca11c
selector 1 proven current executing core: false
```

## Exact fixed geometry

The only accepted production CLI is exactly `--execute`. With no arguments,
the program is dry; `--self-test` uses FakeOps; every unknown CLI exits 63.
Production execution refuses before device access unless the process has the
reviewed ARM32 little-endian usbfs ABI.

The fixed read sequence is:

| order | candidate bus address | IN length | exact 12-byte OUT header | selected expected SHA-256 |
| ---: | ---: | ---: | --- | --- |
| 1 | `0x46001e60` | 512 | `01010000601E004600020000` | `8be303fddfa4aefd0f2d307f05c7522213f8017ae15b374a4fd7178aeca2bb49` |
| 2 | `0x460038c0` | 64 | `01010000C038004640000000` | `0483a632a5e65f8eba8bd623411d6f955705d012c831eac9347e7f9564d944cb` |
| 3 | `0x4601bb60` | 576 | `0101000060BB014640020000` | `035d13a7c17ac9b303ee5739a421a84d0ceec46167d6efce13f4723fc701d9b8` |

Each header decodes exactly as `struct.pack('<III', 0x101, address,
length)`. `RealOps.Bulk` permits an OUT buffer only when it equals one of
these three headers and permits an IN buffer only at one of these exact
lengths. The stateful caller fixes their order, so the native path cannot
select another address or permute requests. Endpoints are fixed at `0x02`
OUT and `0x82` IN with 2,000 ms per transfer.

The three base64 expectations embedded in both native source and wrapper
were independently decoded. They are respectively 512, 64, and 576 bytes,
are byte-for-byte equal to the selected package slices at linked VAs
`0x1e60`, `0x38c0`, and `0x1bb60` using FILE bias `0x40200`, and have exactly
the three hashes above. The build manifest pins the selected package SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.

## Exact six-transfer fail-closed behavior

For each window, local `Read` requires `ReadyForHeader`, then:

1. sets phase to `Unknown` before the 12-byte OUT;
2. promotes to that window's expected-IN phase only after exact count 12;
3. rejects negative, zero, short, or long OUT counts;
4. sets phase to `Unknown` before IN;
5. promotes to `ReadyForHeader` only after the exact window count; and
6. rejects negative, zero, short, or long IN counts.

A rejected count or exception unwinds immediately. Release and close are the
only subsequent operations; no later header, recovery packet, reset, or retry
exists. If the error occurs while a packet phase is pending, the reported
phase remains `Unknown`. Acceptance requires completion of all three pairs,
terminal `ReadyForHeader`, all three raw fields, successful release, and
successful close.

The 50 native FakeOps tests include successful exact completion; one
independent content corruption in each window; late short-read retention;
open, claim, and identity failure; exceptions in every preflight phase; and,
for each of all six bulk transfers, negative, zero, short, long, and exception
outcomes. Each nonterminal fault asserts absence of the immediately later
transfer/header. Release and close failures reject acceptance.

## Immediate raw retention and bounded comparison

After each exact IN returns, the native code immediately assigns that
window's base64, SHA-256, and byte comparison before issuing the next header.
Consequently:

- a later B or C failure leaves every earlier exact window in native stdout;
- a partial current window is not mislabeled as a complete raw artifact;
- a mismatch never triggers a retry or alternative address; and
- all three exact raw windows are retained on complete transport regardless
  of content equality.

`Accepted` depends on protocol/lifecycle completion, not expected-content
match. A complete mismatch returns exit zero with
`ContentComparison=one-or-more-window-mismatch`. The host independently
decodes all raw windows, verifies their lengths and hashes, recomputes each
byte comparison against its own pinned expectation, recomputes the aggregate,
and requires the native labels to agree.

Both native and wrapper require these claims to remain false even when all
three windows match:

```text
ExecutingCodeIdentityProved / executing_code_identity_proved = false
WholeImageIdentityInferred / whole_image_identity_inferred   = false
```

The result additionally states that windows are sequential, not atomic, and
that content mismatch is not a transport failure. Thus exact matching proves
only the bytes returned from these three selector-1 mapped candidate windows
at acquisition. It does not prove a core executed them, selector 1 names the
currently executing stored image-1 component, the rest of an image matches,
or the predicate ran during a physical fault.

## No write, reset, or retry path

The only vendor endpoint traffic is the three fixed target-`0x101` read
headers and their IN responses. There is no memory-write target/header,
payload OUT after a header, caller-supplied address/length, control transfer,
device/interface reset, detach, patch, UI action, or retry loop. Claim and
release are fixed interface-2 usbfs lifecycle ioctls; release is not treated
as parser recovery.

Before claim, the native code pins boot ID, USB runtime-active state, VID/PID,
configuration/authorization, all cached descriptors, vendor-interface
identity, unbound-driver state, bus/device range, opened-FD character-device
identity, and the opened FD's exact descriptor. It then repeats preflight and
requires the same bus/device identity. Open uses `O_RDWR|O_CLOEXEC|O_NOFOLLOW`.
Claim must return zero before the first header. Release and close are attempted
whenever applicable even after failure; either failure rejects acceptance.

## Wrapper envelope, persistence, and cleanup

The wrapper is dry by default and requires an absolute fresh output directory
plus exact manifest SHA for execution. It loads only the hash-pinned root
adapter. That adapter durably writes each command and raw transport
stdout/stderr into `record.json` before checking response bounds, transport
exit, strict UTF-8 JSON, authentication, UID/EUID, and exact command echo.

The target stage is a fresh UUID-named mode-0700 directory. Only the three
hash-pinned runtime artifacts are staged, each root-owned mode 0600, regular,
non-symlink, exact size and hash. A fixed zero-target-operation self-test is
validated before production execution.

There is exactly one production `dotnet ... --execute` command and one
`envelope = call(command)` site. Before that call, the durable record changes
`target_operations` from zero to `None` and status to
`inflight_or_unknown`. It records three accepted requests only after strict
terminal parsing. There is no execute retry branch.

Native stdout/stderr are redirected to private files and returned in an
authenticated envelope that binds boot ID, uptime, native exit, exact sizes
and hashes, and exact terminal inventory. The wrapper saves the complete
envelope and decoded native stdout/stderr before parsing the native outcome.
Malformed, oversized, unauthenticated, nonzero-exit, nonempty-stderr,
non-ready, non-exact, or internally inconsistent outcomes leave the complete
record and private target stage for review.

For a fully validated exact transport result—including a consistent content
mismatch—the wrapper writes all three local `.bin` artifacts and durable
record fields before cleanup. Cleanup is a separate guarded root call that
requires exact hashes and exact five-file inventory, deletes only those fixed
files and their private directory, and requires `STAGE_ABSENT`. This ordering
preserves raw evidence while correctly treating mismatch as data rather than
an ambiguous protocol failure.

## Independently reproduced offline checks

The final pinned artifacts produced:

```text
python3 test-wrapper.py
  {"wrapperTestsPassed":28,"targetOperations":0}

python3 -O test-wrapper.py
  {"wrapperTestsPassed":28,"targetOperations":0}

dotnet ManagedUsbRtBlockReadOnce.dll --self-test
  {"selfTestsPassed":50,"targetOperations":0}

dotnet ManagedUsbRtBlockReadOnce.dll
  exact three-window dry geometry, writes=0, retries=0

dotnet ManagedUsbRtBlockReadOnce.dll --execute on this non-ARM32 host
  REFUSED_ARM32_ABI, exit 64 before device access

manifest inventory, all 13 size/SHA rows, and all 3 embedded source windows
  PASS
```

Normal and optimized wrapper tests were identical. Four additional one-off
negative mutations—whole-image inference true, bus-contents-altered true,
nonzero transfer errno, and invalid raw base64—were rejected. A fifth check
confirmed that a consistent window-C content mismatch remains accepted
transport evidence. All review checks performed zero target operations.

The existing 28 wrapper tests cover exact match plus each single-window
mismatch, terminal stage/phase failures, raw-hash and comparison-field lies,
short recorded traffic, extra steps, an executing-code overclaim, envelope
noise/digest failures, exact dry geometry, inflight accounting order, bounded
interpretation strings, and root-adapter identity.

## External conditions and remaining limits

This helper cannot passively establish the controller parser's current phase.
A separate closed-world lineage must establish `ReadyForHeader` immediately
before the one invocation; process/file absence alone is insufficient. The
fixed boot ID is fail-closed, so a reboot requires a new build/review rather
than runtime substitution.

Clearance here concerns one read-only candidate fingerprint acquisition. It
does not authorize a second attempt, a different address, a write, patch,
reset, threshold change, protection bypass, persistence action, high-bank or
POFLG operation, or return-guard modification.
