# Independent BZ library binding review

Verdict: PASS for the bounded BZ binding correction and inherited one-shot, wipe-only metadata sequence. No blocking correctness or scope regression was found. This is a read-only source/artifact and host-mock review, not a real TEEC success claim, header-authentication result, physical-picture measurement or blackout remedy. User authorization already exists; any target attempt remains centrally coordinated using the exact reviewed deployment manifest and ordinary identity gates.

Reviewer did not author BZ. Only this review file was created. No root transport, TV, network, target ELF execution, real TEEC invocation, display/power operation or firmware operation occurred during this review. Retained target ELF bytes were read by existing host tests solely for hash/ELF validation. The tests loaded the two explicitly host-built mock libraries; neither is a retained target object.

## Exact comparison and target mechanism

`Core.cs` compares byte-for-byte equal to BY, SHA256 `6d55fbbac9a7fd0d426f28458809b0d43ddd4f4a8a1fdb937eac2d0d90ddba11`. The `LiveTeec` class in Native.cs also compares exactly equal to BY. Program.cs changes only the fixed envelope path from BY to BZ and adds bounded binding-stage/reason reporting. The runner is exactly BY with the single fixed STAGE literal changed to `/tmp/swu-metadata-20261027bz`; no retry, extra operation or new command argument was introduced.

The parent-retained diagnostic `/home/researcher/.local/state/s95f-vconf-loader-diagnostic/target-run-01/diagnostic.txt` was read and its SHA256 verified as `f6db2a1a4426517a5b8f256bb25a0611b94eaba9149eba934f0f9a2887c61b0a`. Both LINK_MAP and SYMBOL_OWNER report `/lib/libvconf.so.0`, with fd_spelling_match=0, canonical_match=1, stat_identity_match=1, pinned_size_hash_buildid=1. Before/after maps name `/usr/lib/libvconf.so.0.3.1`. The exact versioned symbol resolves; resolved_pointer_called/getter_calls/teec_calls/plaintext_bytes are all0. This is direct evidence for the legitimate alias/coalescence mechanism that the old exact-name test refused. It proves this observed vconf spelling, not arbitrary loader aliases or all future target TEEC bindings.

## Ownership and content checks

The new `OwnerBinding` implementation is shared by constructor link-map validation and every versioned symbol's dladdr owner validation. It bounds name reads to4096 bytes, requires a nonempty terminated printable ASCII name, and allows only the exact held fd path, requested path, canonical path, or the exact requested/canonical basenames under `/lib` and `/usr/lib` for fixed `/usr/lib` pins. Relative SONAMEs, arbitrary directories, unrelated basenames and alternate fd spellings are rejected.

Allowlist membership alone does not accept an owner. `Verify` rechecks the held file, resolves the candidate alias and requires exact canonical equality with the original. It then constructs a fresh PinnedFile carrying the complete original pin (only Path is changed to that already-proved canonical path), reapplies file mode/stat mask/size/read/EOF/SHA256/ELF/Build-ID checks, requires complete consumed stat identity equality with the original held descriptor, and rechecks both files and canonical paths again. The hostTest=true path bypass in that fresh constructor is therefore scoped to a canonical path independently proved equal to the original; it does not bypass content/ELF/identity checks. Errors become fixed labels/enums, not exception text, loader strings, paths or buffer contents.

The architecture-correct ARM NOFOLLOW/LARGEFILE/CLOEXEC flags and required statx mask0x3df are unchanged from corrected BY. This review does not rely on the superseded BX approval that missed the ARM flag defect. Library content and Build-ID pins remain unchanged. Loaded fixture descriptors are retained together during the tests, matching live Main's simultaneous four-file lifetime and avoiding the discovered host-test fd-name reuse problem.

Residual scope: this proves current canonical owner-file identity and pinned on-disk content. It does not independently hash already mapped executable pages, authenticate loader internals, or eliminate all concurrent mutation races. The design assumes its held `/proc/self/fd/N` spelling has not previously been cached for a different object in the same short-lived process. These limitations are explicitly documented in BZ readiness; no stronger mapped-code claim is necessary for the stated bounded diagnostic. No dlclose rollback is claimed. Dependency loading and library constructors retain their existing effects and run inside the native deadline.

## TEEC frames, cleanup and target scope

The byte-identical Core retains Operation60 including the zeroed cancellation tail at+56, the exact golden command0/1/2 frames, one-call-per-command budgets, fixed shared capacities, returned count bounds and selector drift checks. LiveTeec ABI delegates and wrapper calls are unchanged. There is no new TA command, arbitrary input, firmware-writing function, installation step, selector mutation, retry or output parser. Main still rejects non-ARM32/little-endian live entry before platform calls and checks root identity, exact boot, all fixed file pins and selector0.

The accepted native success still requires quarantined/code0/session closed/three shared releases/context finalized. Plaintext remains confined to allocated buffers and is wiped through the inherited normal/failure cleanup. SIGALRM25sec and the independent root45sec/host75sec containment are unchanged; abrupt process termination is not advertised as TA-state rollback or guaranteed completion of normal cleanup. The runner accepts only the one quarantine diagnostic plus exactly five selector0 observations, preserves the authenticated diagnostic before parsing, and performs fixed-stage cleanup only after that terminal contract. Ambiguous/failed runs retain the stage and have no automatic retry. A failed cleanup may leave partial remote files rather than a complete retained stage.

No physical-damage mechanism was added by this binding correction: it introduces no panel power, display, pixel, controller, reset or firmware-writing operation. That statement does not turn this metadata diagnostic into a treatment for the damaged panel. Any target binding refusal must remain evidence rather than trigger an automatic alternative operation.

## Independent host validation

The existing BZ DLL was run locally with the existing host runtime `${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet` and `--self-test`, exit0. Initial PATH-only `dotnet` lookup failed without executing the DLL; the explicit known host path was then used. No rebuild or frozen log rewrite was performed.

Observed passing output includes three golden frames, eight TEEC failure stages, three count-overflow cases, twelve allocation fault cases, three selector drift cases, SHA256 known answers, file guards/statx masks/architecture flags/real NOFOLLOW refusal, and four retained target ELF pins. Seven host-only dynamic TEEC ABI exports are invoked against the synthetic mock. Separately, canonical preload is explicitly required to coalesce to its canonical spelling, and eight versioned aborting getter/TEEC exports are resolved without any invocation. Seven owner rejection cases cover relative/unknown/fd aliases, wrong symbol version, retargeted symlink, equal-content inode replacement and modified contents; nine pure alias cases include the observed `/lib` spelling. This is meaningful ownership and failure-path coverage rather than merely testing that strings compare equal.

All nine deployment-manifest file entries were independently checked for exact length/hash, including the expected DLL below. The fake orchestration suite passed all six cases in normal and optimized Python. To preserve frozen files, its deterministic `m.save(manifest,m.manifest())` line was replaced in-memory only with an equality check against the existing manifest; all test assertions, fake requests, upload failure, native failure, framing failure, selector failure, digest refusal and generated shell syntax checks remained unchanged. Root transport was replaced by the fake throughout. The inherited25sec deadline test was inspected in retained evidence rather than rerun, since this revision does not change deadline code.

## Reviewed artifact identity

| Artifact | SHA256 |
|---|---|
| Core.cs | `6d55fbbac9a7fd0d426f28458809b0d43ddd4f4a8a1fdb937eac2d0d90ddba11` |
| Native.cs | `eb614f82bda385d52f1194eb78a3135e1350c0a4fb92e9545c2f6f5a271b08dc` |
| Program.cs | `b259728bd45c0cd7f486cfc8a6724c27974d6c1bb06396b9c1ffb6cfa32271e6` |
| SwuMetadataAdapter.dll (46592 bytes) | `cbacf03db8f50cbc8728e4869bca2360f995ef8c39f7ee4c2c15dfe55e1df974` |
| run-once.py | `4a69be38f81d24faa889a6f87b255995de239bd764b6171554e884b3b06fc43e` |
| deployment-manifest.json | `de81b2303dd50667c4a37908dee65796e92725361691a07e24c53b56c08491a7` |
| source-inventory.json | `c985fead44b4631e7472b2be3e4469f95927eb6e08d72000a0375893ed64eddb` |

The exact current BZ envelope path and deployment digest must be used by central coordination. No target result is inferred from this review. Full decrypted-header structure/signature validation remains separate offline work; a completed sequence would establish successful bounded quarantine and cleanup, not authenticated metadata publication.
