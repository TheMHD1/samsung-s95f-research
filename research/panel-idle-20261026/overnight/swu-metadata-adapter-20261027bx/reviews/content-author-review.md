# Independent SWU metadata adapter review

Reviewed 2026-10-27 UTC by the content-control author, separately from the adapter author and parent review. This review read the frozen source, retained exact-target ABI report and host test evidence, and ran the already-built adapter's `--self-test` on the x64 host. No target, root, TEEC, firmware, display or library-acquisition operation occurred. Adapter implementation and retained evidence were not changed.

**Finding:** no material ABI, command-budget, output-bound, library-binding or cleanup defect found in the reviewed bounded command-0/1/2 diagnostic. The source is consistent with one centrally coordinated diagnostic invocation after the parent's staging/identity checks. This is a source/host review, not evidence that this target accepts the session or that an opaque secure-world operation is universally side-effect-free. No implementation correction is requested by this review.

## ABI and operation-frame check

Compared `Core.Frame` and `LiveTeec` with the installed-client/backend facts in `research-20261027-external/reports/swu-target-applicability.md` and its retained target excerpts:

- Context/session are four-byte handle storage; each shared-memory descriptor is 36 bytes. All unmanaged blocks are initially zeroed.
- The operation is **60 bytes**, including the cancellation token at offset 56. All 60 bytes are cleared before every frame; the old 56-byte modern-operation error has not been reintroduced.
- Parameter types use byte slots and the parameters start at offset 8 with stride 12. Command 0 is `0x01010d0d`: blob parent/416 bytes at +8/+12; salt parent/8 bytes at +20/+24; p2 `(0,1)` at +32/+36; p3 `(1,0x201)` at +44/+48. This matches the installed first header candidate `(decrypt, encrypted-passphrase, derivation=1, key-size=2, mode=1)` propagation.
- Command 1 is `0x00020e0d`, with 4032-byte input/output partial memrefs and returned count at +32. Command 2 is `0x0000020e`, with the actual 65536-byte output allocation advertised and returned count at +20. The parent fields receive **descriptor addresses**, not shared-buffer addresses.
- UUID construction produces `22222221-0000-0000-0000-000000000001`; login is zero with null connection data and null open operation, matching the installed caller.
- Live delegates use C calling convention, pointer arguments and the expected return-origin out parameter. `Pointer32` preserves unsigned ARM32 addresses and rejects zero/misalignment/out-of-range host addresses.

The command allowlist is 0–2. The sequence issues command 0 once, command 1 once and command 2 once, stopping on any error; there is no command 3, retry, fallback, arbitrary request or parameter sweep. Native commands are attempted only after exact input validation and repeated master-selector/boot/file checks.

## Inputs, counts and memory lifecycle

The 4056-byte staged envelope and 416-byte selected master blob have fixed sizes and hashes. `Validate` checks the marker at envelope +8. Salt is taken from +16 for eight bytes; ciphertext is +24 for 4032 bytes. The exact staged envelope hash was independently recomputed and matches the source. No blob bytes or passphrase were exported during this review.

Each of the three allocations is 65536 bytes with flags 3. Allocation success is recorded before validating its returned descriptor, so later validation failure still releases that allocation. Input and salt descriptors are independent. Their views are cleared after command 0 and again during final cleanup; the managed blob is wiped on the success/error paths. Plaintext is quarantined in an unmanaged 4032-byte block and wiped on disposal. No plaintext publication path exists in this adapter.

After a successful command 1, the returned count must fit the advertised 4032-byte memref, actual shared allocation and remaining 4032-byte plaintext capacity before any copy. Command 2's count must fit its 65536-byte memref/allocation and the remaining cumulative plaintext capacity. Error returns do not consume returned counts. Overflow tests cover update >4032, final beyond remaining capacity and final >65536. The adapter does not trust modified offset fields to select another output pointer; it copies from the originally mapped output view.

A successfully opened session closes first, then all successful allocations are cleared/released in reverse order, then an initialized context finalizes. A failed open does not trigger a close on an unestablished session. Later cleanup is attempted after managed adapter exceptions without replacing the first result/origin diagnostics. Native process termination or an invalid native pointer can still prevent managed cleanup; those are not represented as successful cleanup in the diagnostic output.

## Binding, identity and deadline

Ordinary-file preflight holds descriptors, verifies regular-file type, non-group/other-writable mode, exact size/hash and retained ELF32 ARM EABI5/Build ID, and compares statx identity before and after reading. Recheck covers the held descriptor and the current path inode/size/time/device identity. The library allowlist and resolved-path restrictions avoid an arbitrary caller-controlled library path.

Libraries are loaded through their held `/proc/self/fd/<n>` names, in common/backend/wrapper dependency order. `dlinfo` checks the link-map object name; `dlvsym` requires the specified symbol versions; `dladdr` checks that each returned entry point belongs to the pinned wrapper descriptor. The seven TEEC bindings are verified in the host mock. This does not claim that loading native libraries is a pure read: constructors and the actual secure-world service are part of the later target action.

The ARM statx syscall number 397, argument order, AT_EMPTY_PATH flag, 256-byte buffer and Linux UAPI offsets are consistent with the code. The identity deliberately omits atime while retaining inode/size/ctime/mtime/device metadata. The live selector is a versioned `vconf_get_bool` call, checked for return zero and value zero; master-selection drift stops the sequence.

`Native.Deadline` installs SIGALRM default disposition, explicitly unblocks it in the calling thread and arms 25 seconds before identity/file/library/TEEC work. Its 128-byte sigset storage and constants are consistent with the intended glibc ARM32 ABI. The retained host deadline test for this exact assembly reports signal 14 termination after 25.036 seconds. I did not repeat that already-passing timed test.

The deadline is a **process lifetime mechanism, not secure-world rollback**. If it fires during an invocation, command completion and native cleanup can be unknown; a timeout must not trigger an automatic retry. Lower native code could theoretically change a signal disposition/mask after arming, so the host test is not a hard real-time proof for every target call. Nothing in the new adapter requests a display-controller reset, flash write, protection change or arbitrary secure-world command. No specific material brick path was found in this bounded client sequence; that conclusion does not substitute for observing the target result.

## Host evidence checked

I ran the retained `SwuMetadataAdapter.dll --self-test`, which passed. Its three emitted golden 60-byte frames match the independently checked field layout above. The run also passed eight TEEC failure stages, three count-overflow modes, twelve allocation descriptor/address faults, three selector-drift positions, SHA-256 known answers, ordinary-file guards, four acquired ELF pins and seven versioned host-mock TEEC bindings. It loaded no target library and performed no real TEEC call.

The retained `host-verification.json` assembly hash matches the assembly reread during this review. The x64 host guard and retained deadline evidence belong to that same hash. Host mocks and ELF parsing do not constitute ARM execution evidence, but no host result was misread as target success.

## Reviewed identities

| File | SHA-256 |
| --- | --- |
| `Core.cs` | `6d55fbbac9a7fd0d426f28458809b0d43ddd4f4a8a1fdb937eac2d0d90ddba11` |
| `Native.cs` | `1c6bf415de44c5dcea093228313ba8ce7a301a87be45225f30e38d219e649bb5` |
| `Program.cs` | `eadd2a671ef134d6602a5165984eaeefa9a4621a4491000437d81bc7e0160324` |
| `HostTests.cs` | `2c14ac28abc1927ec33dbc3d123b18b454218b18063e60aec1cd45e7493ca944` |
| `verify-host.py` | `afd3e7926e83675c2a63dc83dd946a6e8b6bab4341ef7a45e3e5104b572e9030` |
| `host_mock.c` | `0bb6ba72d43df9aa50df1810f0e72193c08716a34ad54e0365465ee42a60008c` |
| `host_mock.map` | `47441e73e5d2b78e99aa9e1ff1a2f3ef5124525e142d54634240bf367b2edff2` |
| `bin/Release/net6.0/SwuMetadataAdapter.dll` | `a55539aa106b542905926f5bb6761adbd542d2111bcff2a68ba2ecbc559838db` |
| `header-envelope.bin` | `6da1e2386f0f97a180984f249febaf831febfee1adb35a8cefa96f89ad069e0d` |

This review applies to these bytes. A later source, binding, input or sequence change requires a corresponding review update.

## Runner addendum

Reviewed the final `run-once.py` (`d969ac178d7761c01ac1f1091f65b81aa97bbc21cfc8bbe348cee4715b1864a5`, 8871 bytes) and `test-runner.py` (`a33505b4f924ae117e14571e953a2f052292134cd2c6250b33b4d4453670780f`, 3535 bytes). **No blocking runner issue found under the stated frozen-source/payload condition.** The parent can freeze the deployment manifest for these bytes. No target action was made by this review.

- Default execution prints a dry plan. Live execution requires the exact deployment-manifest digest and a fresh absolute host output directory. The manifest compares the full current source/payload inventory before root loading and pins the root adapter. Unknown execution inputs do not provide arbitrary commands, paths, payloads or retries.
- Target commands recheck the known boot and stock dotnet hash. The fixed stage must not exist before creation and is root-owned mode 0700. Exactly four mode-0600 payload files are created and uploaded in bounded 3072-byte chunks. Offset checks prevent implicit append retries; the exact pre-invocation guard checks names, file types, modes, lengths and hashes, including hidden-name rejection.
- The runner records `inflight_or_unknown` before the sole foreground managed invocation. Source and control flow contain exactly one invocation command and no retry path. Upload failure, root/transport ambiguity, rejected framing, nonzero native exit, stderr or incomplete diagnostics stop before cleanup and retain the stage. There is no automatic second invocation after an uncertain result.
- Native stdout/stderr are size-capped before retrieval. The authenticated root wrapper supplies the transport envelope; the runner further requires its exact run markers, one successful quarantined diagnostic, calls `1,1,1`, native close/release/finalize claims and precisely five successful selector rows. The five count matches `Program`'s initial selector check, post-binding check, `Core.Run` pre-context check, post-open check and final post-command check. Ignored GC rows do not supply selector/terminal evidence.
- Successful host output stays narrow: `metadata_validated=false`, `plaintext_saved=false`, no permanent-prevention claim. A completed crypto diagnostic is not presented as authenticated metadata or a repair.
- Cleanup is reachable only after that accepted native terminal contract. It rechecks the exact six-file stage (four payloads plus stdout/stderr), removes only those allowlisted files and then the directory. A cleanup-check failure does not retry or broadly remove an ambiguous stage; a failure partway through removal can leave a partial stage, and no successful result is written for that failure.
- The tests replace every root call with a fake, check generated shell syntax, and cover success, upload failure, native failure, framing failure, missing selector and pre-target manifest rejection. I read these six cases; I did not rerun the test script because it rewrites the deployment manifest that the parent is about to freeze. The parent's normal/optimized six-case results are consistent with the reviewed control flow. The already-checked 25-second deadline test was not rerun.

The runner rereads local payload bytes during upload and when generating remote guards; it does not retain an immutable in-memory snapshot of all payloads from its initial manifest comparison. The stated source/payload freeze must therefore remain in force through dispatch. This is not a blocker for the parent's frozen bounded invocation, but concurrent edits during deployment would violate the reviewed condition.
