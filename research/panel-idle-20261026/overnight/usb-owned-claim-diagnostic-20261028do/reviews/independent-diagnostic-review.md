# Independent owned-claim diagnostic review

Checkpoint: 2026-10-28 UTC. Host-only independent review; no target/root/USB request was made by the reviewer. The reviewer owns only this reviews directory and has not changed diagnostic sources. The native source, wrapper, strict parser and final frozen manifest were reviewed.

Final integrated verdict: **PASS — no blocking defect found for the bounded zero-vendor diagnostic scope.** This is not a production driver-policy qualification or authorization for a vendor transaction.

`Program.cs` SHA256: `66e69e1e09e8045bdd8b65019c1e2f9560ad0ebaaa8fd6df3c86d294f46fc0d4`.

The production path is fixed to the recorded boot, USB bus7/device58/interface2, node `/dev/bus/usb/007/058`, active authorized configuration1, vendor/product04e8:2001, interface2 alternative0/classff/subclass00/protocol00, and the exact116-byte cached descriptor sequence. The opened no-follow/CLOEXEC FD is checked as character189:825, followed by an exact18-byte cached device-descriptor read. These metadata checks are repeated after claiming; they are sequential observations, not atomic continuity proof. Initial cached driver absence is required; a failed claim never permits the diagnostic to borrow another owner's claim.

Only three USB ioctl request constants and their fixed sites exist: CLAIMINTERFACE0x8004550f once, GETDRIVER0x41045508 before/after claim, and RELEASEINTERFACE0x80045510 once in finally after successful claim. Interface number2 is fixed. There is no bulk/control transfer structure, vendor header, endpoint request, reset, detach, configuration change, UI operation, limit write or retry path. Opening/claiming affects kernel FD/interface ownership; the source claim is zero explicit controller/vendor protocol transfers, not a claim that kernel power-management internals cannot run.

The retained same-version upstream Linux UAPI defines GETDRIVER as an inline260-byte object (u32 interface plus256-byte driver name), matching the code's zeroed byte buffer and request-size encoding. `devio.c:proc_getdriver` reads the cached `intf->dev.driver->name`, returns ENODATA when absent, and copies the result to userspace; its handler does not submit a device transfer. Same-version upstream source is not attestation of the executing vendor kernel. Post-claim metadata/query failures are retained as observations rather than treated as an already-established driver acceptance rule; `driverPolicyEstablished` and `physicalPictureObserved` remain false. A lifecycle acceptance alone cannot establish endpoint queue phase.

Resource cleanup is structurally sound: opened/claimed flags are set after successful acquisition, release is attempted only for the acquired claim, and close is attempted independently even after release failure. Post-claim snapshot/identity/deadline exceptions still enter finally. Any release/close error rejects acceptance. Receipt publication occurs after cleanup; publication failure cannot skip that finally block. File receipts use fixed names, exclusive no-follow/CLOEXEC creation, mode0600, a fixed nonce-shaped private directory with mode0700 and matching UID/EUID, and a24576-byte serialization bound. ARM32/little-endian ABI refusal precedes production receipt/native work; root UID/EUID is checked before USB open. Managed receipt content is separated from unmanaged stdout.

The native15-second deadline is cooperative checks, not a hard syscall interrupter. The final wrapper enforces pinned remote45/host75 foreground bounds and retains rejected or ambiguous stages. A blocked uninterruptible kernel operation is not proved terminable by a host timeout.

Independent host checks: existing built DLL `--self-test` passed10 checks/zero target operations; `--execute` on x64 returned64 with REFUSED_ARM32_ABI. The10 self-tests cover layout/driver-absence policy and size, not injected resource-creation/cleanup failures; cleanup claims above are source review, not fault-injection results.

The wrapper remains dry by default and loads no root adapter until manifest and fresh fixed-device readiness contracts pass. Readiness binds boot/bus7/device58/interface2, exact descriptors, node/sysfs identities, zero-holder census and the explicit closed-world lineage premise; endpointQueueProof remains false. The target self-test uses only the exclusive private managed file. Exactly one production invocation follows its strict10-check receipt and repeated metadata/census checks. Every remote command is bounded8192 bytes; the three individually sized/hashed/canonical-base64 blobs fit the65536-byte root response cap. Native24576-byte receipt,16384-byte diagnostic stdout and2048-byte stderr remain separate. Diagnostic stdout cannot become a semantic receipt. The parser independently requires zero vendor headers/bulk/control counts, fixed58/interface2/FD189:825, successful claim/release/close, snapshot ordering, exact raw260-byte GETDRIVER buffers/hashes and unsupported-policy/physical flags false. Postclaim driver observations are deliberately not a newly guessed acceptance policy.

Accepted cleanup requires postmetadata/census, the exact nine-file inventory and all received hashes, then removal of only those fixed names and the exact private directory. Submission ambiguity, malformed framing, failed semantic receipts, nonzero exit/stderr or failed cleanup produce no accepted result and no retry. Source/dependency pins are validated before device access. Root45/host75 budgets do not establish guaranteed termination of an uninterruptible syscall.

Independent final host verification passed **742 checks normally and742 under python -O**, each covering214 generated shell syntax checks; maximum actual generated command was7728 bytes. Cases include malformed/missing native fields, nonzero vendor counters, wrong fixed device/interface, raw-driver hash/ABI corruption, observation errors, pre/invocation/post metadata refusal, ambiguous submission, partial framing, native failure, stderr, cleanup failure, size/hash bounds, actual host exclusive0600 receipt/no-overwrite, and ARM32 ABI refusal. Test responses are synthetic; no target/root transport was loaded or contacted. Native exceptional cleanup remains source-reviewed rather than syscall-fault-injection tested.

Final frozen pins:

| Input | SHA256 |
|---|---|
| deployment-manifest.json | `22b22f8b788115ed64772eea01dc3725e3e93f2582fdc4387aefe8246c0b099b` |
| run-once.py | `c54824702fca8548e03cf98eaa85437cafeca48bdaa34e24f94a43b85afe0119` |
| parse-result.py | `83ba12c13eac9bfa7a0424ce41275208e71b7f0e1f2274964781642a30019a32` |
| test-runner.py | `23cfea0f38c5a60ea327a618921059bed6a69d1eb19a90ee809ba3d254fde153` |
| ClaimDiagnostic.dll | `18ebe3359e3897321534705eeec961b4475a95bf32cfa96346f9d1c5e4c8e4a7` |
| host-build-checkpoint.json | `672a283d5eaa55960f7ff9fd8c3f9129f741e88bebe34344a1d22fb4d8b6f024` |
| source-inventory.json | `a61b65b590bffd753c3f8d9590667778753ceb91973d09131c92c14f64d2e4a2` |

This PASS qualifies this fixed diagnostic's reviewed source and host checks. A future vendor-operation policy still requires interpretation of the actual retained diagnostic observations; this diagnostic itself establishes neither queue freshness, root cause, threshold change, nor physical panel recovery.
