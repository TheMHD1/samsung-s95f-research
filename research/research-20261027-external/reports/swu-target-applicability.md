# Minimal SWU metadata decryption: target applicability

2026-10-27 UTC. This work inspects retained host files and pinned source. It did not contact the television, load a target library, execute Probe/updater code, invoke TEEC, read a passphrase blob, or build a target helper. Parent-coordinated ordinary-file acquisitions are cited as capture provenance; they are not SWU execution evidence. No key, passphrase, or salt bytes are printed here.

## Result and stage completion

**The target's normal-world SWU command ABI and its metadata-decryption caller are now mapped from the installed binaries.** This closes a substantial gap beyond the earlier wrapper-only review. The installed `SWUCoreTV` first metadata candidate selects mode 1, key-size 2 and derivation 1, passes an encrypted items blob and an eight-byte salt to command 0, and uses command 1/2 output-count slots matching the reviewed modern source. The target backend independently confirms eight-bit parameter-type packing and 12-byte parameter stride. The public structures used by the installed client match context/session 4 bytes, shared-memory stride 36 and a 56-byte operation public prefix **plus a required four-byte cancellation token at offset 56: minimum operation storage is 60 bytes**. The retained Python `ModernTeecOperation` allocates only 56 bytes and must not run unchanged against this backend.

The retained firmware contains the complete metadata input: **4,032 ciphertext bytes at `[258,4290)`, with its own eight-byte salt at `[250,258)`**. The wrapper's second word is an independently reproduced CRC32 over that ciphertext, `0xefed4e54`. A host-only verifier now requires this CRC before producing a plan. There is no need to fetch gigabytes or a payload merely to attempt the metadata milestone.

A minimal direct TEEC helper can consequently be designed from target evidence, separated from the updater and broad Probe. **No helper was built or invoked.** The current selector sample is false (master), and both blob identities are recorded without copying their bytes. Remaining gaps concern actual caller authorization, transport/TA effects and bounded plaintext validation; it is no longer accurate to say that every normal-world ABI field is unknown. A matching normal-world frame does not establish successful TA acceptance or persistent-state safety.

## Retained target provenance

All five ELF files below were re-hashed locally and inspected without loading them. Parent acquisition records include bounded ordinary-file copies, hashes before/after and boot identity `00000000-0000-4000-8000-000000000000`. This identifies the capture boot; it does not claim future boots or files are immutable.

| Installed path | Bytes | SHA-256 | Capture |
|---|---:|---|---|
| `/usr/lib/libteec.so` | 10,892 | `926840c9e7b26c59d8cb9d4ab5ae274e62b11efdbf14831b0a4d81d3de720f70` | [02 manifest](../target-file-acquisition-02/acquisition-manifest.json) |
| `/usr/lib/libteec_trustware.so` | 30,352 | `0574261e6291fb3f28bf8a254c0610c9177e132a6afd0bc7418826173555db81` | [02 manifest](../target-file-acquisition-02/acquisition-manifest.json) |
| `/usr/bin/SWUCoreTV` | 4,980,824 | `b8de9e31bf6e74cf9a1f3cfd2598658d978a4edd88b36d1c2f10129ccc8a2697` | [03 manifest](../target-file-acquisition-03/acquisition-manifest.json) |
| `/usr/lib/libSWUProductionConfig.so` | 6,440 | `c6af8346f4643f2cf50e996682611ece7ad6ff8999274570023561d1a97879f0` | [03 manifest](../target-file-acquisition-03/acquisition-manifest.json) |
| `/usr/lib/libteec_trustware_common.so` | 244,580 | `353104729c40d6f1eff4f07b96f8a14466dd98efddb21a9cb7d14752351dd139` | [04 directory](../target-file-acquisition-04/) |

Each is ELF32 little-endian ARM EABI5, soft-float ABI. The wrapper Build ID is `80169c30fb9cc031d073eb88350ada39a0dfba67`; backend `60872566e5bfe19d56c7175b4071a63d845245c9`; common `272f10b47670723b6c7863ca8e331ea2140d1544`. Exact dependencies, remaining Build IDs, selected exports, initializer metadata and hashes are in [target-static-evidence.json](../sources/swu-target-applicability/target-static-evidence.json). The [reproducer](../sources/swu-target-applicability/inspect_retained_abi.py) checks all five hashes before producing [instruction excerpts](../sources/swu-target-applicability/target-static-excerpts.txt); it uses the existing host Capstone 5.0.7/pyelftools environment.

No installed `libTEE.so` or generic `libSWU.so` is established by this evidence. The actual SWU client implementation is inside `SWUCoreTV`, which imports the TEEC APIs directly. The earlier other-model source path `/usr/apps/org.tizen.tv.swu/bin/SWUMainApp` is not the target executable to transplant. Ordinary metadata also names `/usr/bin/SWUVerifierTV`, `SWUService`, `SWUStandalone` and `SWUAutoUpgrade`; none was executed.

## Target versus upstream evidence matrix

| Property | Target verified statically or from retained metadata | Remaining boundary |
|---|---|---|
| TEEC wrapper and backend | Wrapper exports the seven needed TEEC calls under `TRUSTWARE3.0`; load initializer dispatches through `libteec_trustware.so`. Backend depends on `libteec_trustware_common.so`, pthread, resource API, C++ runtime and libc. | Loading is an action: initializers execute. `NODELETE` means unloading is not an undo guarantee. |
| Structures | Installed Core places context at object+0, session+4 and three shared buffers at +8/+0x2c/+0x50: 36-byte stride. Backend reads buffer/size/flags at +0/+4/+8; common writes its memory handle at +0xc. | The old Python private shared-memory field names are not proven semantic names for this backend. Allocate the target-observed 36-byte structures and zero them. |
| Operation/enum | Common reads operation+4, shifts each type by index×8, masks `0x7f`; parameters start +8 with stride 12. Public prefix is 56 bytes; common session creation/invocation writes a token at +56, requiring **at least 60 bytes**. Backend cancellation reads that token. | Retained modern Python operation storage is undersized. Correct its tail while retaining target modern types `0x0d/0x0e`; choosing the legacy profile just for its 60-byte size changes unrelated semantics. Zero all 60 bytes. |
| UUID/login | Core UUID at `0x3fc2e8` is `22222221-0000-0000-0000-000000000001`; session call at `0x245668` uses login 0, null connection data and null open operation. | This proves the stock caller's request, not authorization of an arbitrary helper identity. |
| Commands/output slots | Command 0: `0x01010d0d`; command 1: `0x00020e0d`; command 2: `0x0000020e`. Target output counts match modern source. | No call was made; result acceptance, return origin and returned byte counts remain unobserved on this TV. |
| Header caller/settings | Target `OUHeaderDecryption.cpp` routine `0x1d614c` builds first candidate mode/key-size/derivation `(1,2,1)`; normal pipeline reaches command 0. | The routine also contains a legacy candidate. Minimal request should not inherit its automatic fallback loop. |
| Encrypted input selection | Target getter `0x244698` branches on `db/menu/support/softwareupdate/isSubmodelKeyType`; false selects master path, true submodel path, listed below. | Parent sample at uptime 163635.32–163635.40 reports false and identifies the master file by size/hash; this is a sampled state, not a promise about future calls. |
| Production configuration | Copied config SONAME is `libSWUProductionConfigRelease.so`; its only substantive export `SWU::Common::Debug::isProduction()` at `0x42df03bc` returns 1. Target cryptography helper `0x2450f4` separately returns 1 for in-engine encrypted passphrase handling. | Neither return value is a key, access grant or TA implementation audit. |
| Salt/wrapper/input | Target stream helper reads an eight-byte `Salted__` marker and eight-byte salt. Header path skips the eight-byte wrapper; ciphertext CRC matches target bytes. | Wrapper first-word/plaintext CRC and RSA trailer semantics are not yet fully qualified. |
| Transport | Common constructs an AF_UNIX connection using `tzdaemon_server`; its sockaddr uses a leading NUL, i.e. abstract `@tzdaemon_server`. It also names `libtzdev-ppi.so` and `PPI_TzdevInterface_ops` for its PPI loader. | Actual daemon executable, PPI implementation, device ioctl behavior and authorization policy are not retained here. Do not guess `/dev/tee0` or infer transport from generic TEEC documentation. |
| TA internals | None recovered or invoked. | Persistent logging/state, quotas, failure behavior, crash effects, cleanup and secure-world rollback remain unverified. |

Older [wrapper-only analysis](../../panel-idle-20261026/tcon-research/libteec-installed-abi.md) correctly identified the backend edge. The [earlier feasibility report](../../panel-idle-20261026/tcon-research/swu-decrypt-feasibility.md) predates even the wrapper copy; its statements that no relevant binaries are retained are now superseded. The ABI claims above come from the new exact installed binaries, not the target model string, GCC version, or a cross-model Tizen profile switch.

## Exact command mapping and caller context

All addresses are ELF virtual addresses before runtime relocation. The installed Core's TEEC PLT entries resolve to initialize `0x576cc`, allocate `0x58b6c`, open `0x57ae8`, invoke `0x57f24`, close `0x56b78`, release `0x589e8`, finalize-context `0x572e4`. Its normal client open routine starts `0x245594` and allocates three 64 KiB shared buffers with flags 3.

| Call | Installed Core proof | Parameters/status/count |
|---|---|---|
| Command 0 | Routine `0x24581c`; type word built at `0x245900..0x245908`; invoke `0x245946` | p0 partial input encrypted blob, p1 partial input salt; p2 `{a=encrypt,b=passphraseEncrypted}`; p3 `{a=derivation,b=mode+(keySize<<8)}`. For the first header candidate: `{0,1}`, `{1,0x201}`. Memref offsets are zero. |
| Command 1 | Routine `0x245ed8`; type word `0x245f2e..0x245f3a`; invoke `0x245f4e` | p0 input, p1 output, p2 value output. **Returned byte count is p2.value.a**, loaded at `0x245f58`. Stock client advertises p1 capacity equal to that input chunk's length, although backing allocation is 64 KiB. The Python helper advertises 64 KiB: preserve the target contract in a minimal implementation. |
| Command 2 | Routine `0x245d98`; type word `0x245dd2`; invoke `0x245dea` | p0 output with capacity 64 KiB; p1 value output. **Returned byte count is p1.value.a**, loaded at `0x245df2`. |
| Failure | Each TEEC result is checked against zero before output use | Record stage, result, origin and bounded output count independently. Do not treat result as output length or trust output after failure. |

The common backend independently enforces byte-slot interpretation at `0x15016..0x1501c`, and computes operation+8+index×12 for values at `0x14028..0x14044`. This is stronger evidence than merely importing a TEEC header. The pinned C Probe includes an external `tee_client_api.h` whose contents are not retained; the target disassembly now closes that macro/layout gap for this build.

The full storage requirement comes from the installed implementation, not a class name. Common `teecSession::invokeCommand` loads the operation pointer into `r7` at `0x208e4`; at `0x209b6` it forms `operation+0x38`, stores that address in its transport message, and at `0x209c0` writes zero to that word. Session creation similarly writes +0x38 at `0x164a8` when the operation is nonnull. Backend cancellation reads it at `0x5954` and `0x5a18`. Stock Core command 2 reserves a 0x60-byte local frame, places the operation at SP+0x20 and its canary at SP+0x5c: 60 bytes fit immediately before the canary. See [tail disassembly](../sources/swu-target-applicability/operation-tail-disassembly.txt) and the regenerated static excerpts. Context/session remain four-byte handles and shared-memory structures have the observed 36-byte stride; those are separate layout facts.

| Operation offset | Installed ARM32 storage |
|---|---|
| +0 | Four-byte started/cancellation state word. |
| +4 | Four-byte parameter-type word, eight-bit slots. |
| +8, +20, +32, +44 | Four 12-byte parameter unions. A value uses words a/b; a partial memref uses parent pointer, size, offset. |
| +56 | Four-byte implementation token touched by session/invocation/cancellation. |
| Total | Minimum 60 bytes; four-byte word layout. A 56-byte allocation omits the token. |

Stock command 0 uses an SP+0x2c operation in a 0x10c-byte local frame; command 1 uses SP+0x1c in a 0xfc-byte frame; command 2 uses SP+0x20 in its 0x60-byte frame. Each has space for the token. The reviewed call-site excerpts initialize the used type/parameter fields, rather than showing a complete 60-byte `memset`; the common layer separately zeros the token. This is evidence of sufficient stock storage, not permission to leave a new helper's unused words uninitialized. The common argument wrapper retains the operation pointer and handles fields by selected type; no public 56-byte size should be inferred from the parameter prefix. These bounded excerpts do not claim to audit every private transport copy or asynchronous cancellation race.

The first header candidate is constructed at `0x1d6180..0x1d618a`. Its record `(mode=1,keySize=2,derivation=1,2)` reaches `0x1d6548 → 0x1d503c → createCryptEngine 0x243030 → createPlatformCryptEngine 0x244e7c → TrustZoneAESEngine constructor 0x246d20 → command-0 routine 0x24581c`. The first three numeric settings match the modern upstream interpretation CBC/AES-256/SHA-256; target settings are recovered directly rather than copied from the EU manifest. The fourth record field remains unnamed here. The next record `(1,0,0,0)` is a separate fallback, not part of the bounded proposal.

The first-record settings are traced across callers rather than inferred from upstream defaults. At `0x1d5088` record[0] becomes factory stack argument 0 (mode); `0x1d50a8` loads record[1] into `r3` (key size) and record[2] into `r2` (derivation). The factory receives crypt-type 1 as its stack argument 1, then converts it to encrypt=false using `clz`/shift at `0x243182..0x24318a`. The encrypted-passphrase helper returns 1. Platform factory/constructor propagation reaches command 0 with `r2=0`, `r3=1` and key-size/mode/derivation stack arguments `(2,1,1)`; command 0 then writes p2 `(0,1)` and p3 `(1,0x201)`. The fourth record field does not supply derivation. These arguments are included in the static excerpts and [caller disassembly](../sources/swu-target-applicability/core-caller-disassembly.txt).

The target getter `0x244698` uses these exact paths:

- False selector: `/usr/share/org.tizen.tv.swu/itemsAESPassphraseEncrypted.txt`.
- True selector: `/usr/share/org.tizen.tv.swu/itemsSubModelAESPassphraseEncrypted.txt`.

The true branch at `0x2446ec` resolves global string object `0x4d329c`; false at `0x2447e2` resolves `0x4d32b4`. Startup `0x6ded2` establishes global base `0x4d326c`; constructors `0x6dede` and `0x6df02` associate master at base+0x48 and submodel at base+0x30 with the exact path literals. The parent's [current selector and ordinary-file metadata](../target-swu-selector-05/metadata.txt), sampled on boot `00000000-0000-4000-8000-000000000000` at uptime 163635.32–163635.40 seconds, reports **False (Boolean)**. Thus that sample selects the master input. Both files are regular, 416 bytes; master SHA-256 is `d8af420d63b9cb2643783c56ce7396a5fd4d809e48df0bd321781cfd025e8220`, submodel is `bb1ab330400743923bd06c3e8479da13ae61e699e2c39fe21227b176ac096e2f`. No blob bytes were copied. A later helper must recheck selection and input identity at its own start; the captured value is time bounded.

## Exact header input and validation

| Region | Target byte interval | Role |
|---|---|---|
| Clear directory | `[0,234)` | Nine IDs 1001..1009 and the target label/descriptor. |
| Encrypted envelope | `[234,4290)` | 4,056 bytes, complete in the retained prefix. |
| Wrapper | `[234,242)` | Two 32-bit words. First `0xcbcf1d91` has not been assigned fully qualified plaintext semantics here. Second `0xefed4e54` matches ciphertext CRC. |
| Marker | `[242,250)` | `Salted__`, excluded from ciphertext. |
| Salt | `[250,258)` | Exactly eight bytes; value omitted. |
| Ciphertext | `[258,4290)` | 4,032 bytes, 252 AES blocks. CRC32 `0xefed4e54`; SHA-256 `b7252dbea64d63a7ee9c3b038597dd99ae94a5e531246d53c15e97d274ed9eca`. |
| Payloads | First begins 4290 | Excluded from metadata operation. Their contiguous intervals end at prior ZIP member length 1,493,538,434. |

Target header code reads the wrapper words, computes encrypted-stream CRC and compares the second word at `0x1d63cc..0x1d63f8`, then skips eight wrapper bytes at `0x1d63fe..0x1d6408` before selecting the AES candidate. Common stream helper `0x32be44` validates the marker and reads the salt. Its installed constants are marker length 8 at `0x431fa0`, salt length 8 at `0x431f9c`, marker at `0x431fa4`. These target byte positions independently agree with the pinned [modern inspector](https://github.com/hTobi02/TizenWLED/blob/e6b4acea23bd4fd53a779ac23f371db70a55eda1/tools/firmware/inspect_msd.py#L91).

The source prefix is `panel-idle-20261026/overnight/samsung-official-T-RSMFAKUC-0090-msd-prefix.bin`, SHA-256 `01821f40cf70841649c856090e23b35be6173659fb54be11f3b661a3e37bf92d`. The [host-only verifier](../sources/swu-target-applicability/offline_header_plan.py) pins that hash and reconstructs the bounded directory/header. Normal and optimized Python produce identical [normal](../sources/swu-target-applicability/header-plan.normal.json)/[optimized](../sources/swu-target-applicability/header-plan.optimized.json) plans and reject ten malformed variants, including ciphertext corruption. Explicit exceptions enforce the checks under optimization. This establishes structural and ciphertext-CRC integrity, not cryptographic authenticity.

The target also contains `OUHeaderDecryption::readSignatureAndVerifyAesAlgorithm`, post-decryption CRC and RSA verification paths; the exact plaintext CRC coverage, signature length/trailer and decoded OUIT schema need further static mapping from this already retained Core. A first decode must remain unpublished/untrusted until strict padding, bounded parsing, item reconciliation and the appropriate target checks pass. No EU names, salts, CRCs, offsets, RSA assumptions or legacy key are imported.

## Minimal helper design and side effects

The concrete bounded design is a direct TEEC subset: one fixed request containing only this target salt and 4,032 ciphertext bytes; target structures with zeroed 60-byte operations and modern byte-slot types; the selected encrypted blob read in-process; one context, three shared allocations, one session, command 0 once, command 1 once, command 2 once, then session close/releases/context finalization and exit. No command 3, parameter search, fallback or retry is required. Check every result; reject counts exceeding the advertised memref capacity, actual allocation, caller buffer or the 4,032-byte cumulative plaintext maximum; clear sensitive buffers and never log blob/key bytes.

Use a parent-controlled finite transport and exclusive, mode-restricted output. Report stage/result/origin/count; publish plaintext only after strict PKCS#7 and metadata validation. A 4,032-byte request is already small enough to avoid a stream listener or large-payload transfer. Process cleanup is mandatory on every failure; it is not proof that secure-world state rolled back.

The stock updater process and full `TrustZoneAESEngine` constructor should not be executed to obtain this subset. The normal updater contains installer/verification and broader service behavior, while the engine constructor initializes extra streams and diagnostics. The reviewed direct call sites contain no flash writer; that only bounds their normal-world call graph. Library initialization, socket/PPI setup, shared-memory allocation, session creation and cipher state updates remain actual side effects. TA persistent state, logging, quotas, crash behavior and recovery are still unknown.

The broad [Probe program](https://github.com/hTobi02/TizenWLED/blob/e6b4acea23bd4fd53a779ac23f371db70a55eda1/Probe/Program.cs) is also unsuitable unchanged: startup launches `BuildReport`, which calls `ProbeSwu` and tries command 3 in four modes; its listener binds all interfaces on port 45679 and exposes file/capture routes. The [native source](https://github.com/hTobi02/TizenWLED/blob/e6b4acea23bd4fd53a779ac23f371db70a55eda1/Probe/probe_native.c) provides useful command 0/1/2 source evidence, not a reason to accept those extra actions. Its stream output check uses caller capacity; a new helper must also check actual shared allocation capacity.

The local `teec.py` and `swu_firmware_decrypt.py` match their pinned [levkropp commit 2b062938](https://github.com/levkropp/samsung-tv-root-untethered/tree/2b0629381b3eaf5a78f84332d630d6d4b10681e7/swu) bytes. That Python client rejects invalid PKCS#7; the pinned [upstream host streamer](https://github.com/hTobi02/TizenWLED/blob/e6b4acea23bd4fd53a779ac23f371db70a55eda1/tools/firmware/decrypt_via_tv.py) leaves invalidly padded input unchanged and relies on expected payload CRC. Do not reuse that permissive behavior for a metadata-only result.

No firmware application, signing, downgrade, partition write, TCON update or electrical repair is qualified by this design. Deleting the helper/output and closing its session are the available process/filesystem cleanup actions; no secure-world rollback mechanism was demonstrated.

## Exact next evidence

1. The selector/input inventory milestone is complete for the captured sample. Before any later helper invocation, recheck that selector and ordinary-file input identity without copying blob bytes. This bounds configuration drift; it does not require another acquisition for the present offline design.
2. Continue offline mapping in the already retained Core: first wrapper-word CRC coverage, RSA trailer and plaintext OUIT record schema. This is analysis work, not a new TV read. Link candidate IDs/names/offsets/sizes/salts/CRCs back to this target's nine clear records before selecting a payload.
3. For transport effects, retain exact ordinary `/usr/lib/libtzdev-ppi.so` only after metadata resolves its installed path and hash. Common's loader names `PPI_TzdevInterface_ops`; inspect that implementation offline rather than guessing device/ioctl behavior. Identify the daemon executable and existing service/access-policy metadata for abstract `@tzdaemon_server` from ordinary process/service metadata; do not open the socket or a TA to fill the gap.
4. TA registration/authorization and persistent-state evidence, if available as ordinary installed metadata. If the SWU TA is resident and cannot be identified without invocation, record that limit. Successful stock-caller frames do not establish an arbitrary helper's permission or complete failure recovery.

The artifact hashes, pinned primary links, local-source comparisons and provenance are in [source-inventory.json](../sources/swu-target-applicability/source-inventory.json). This agent's writes are confined to this report and its source directory.
