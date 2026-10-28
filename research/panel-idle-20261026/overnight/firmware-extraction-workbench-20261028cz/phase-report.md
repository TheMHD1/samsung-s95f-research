# Firmware extraction phase report

Checkpoint: 2026-10-28 01:25:31 UTC, after all nine main-package sections passed extraction validation, including explicit offline receipt reconciliation for platform.img. This report was prepared through offline reads only. It adds no target operation, firmware write, device control, helper invocation, retry, publication, or changes to frozen work.

## Observed results

The complete official Canadian package was acquired with HTTPS verification, exact length checks, local full-file identity records and complete ZIP-member CRC verification. The retained main MSD prefix and directory match the complete package. These checks establish acquisition consistency; OEM authenticity is handled separately below. The companion MSD was acquired but is outside this main-package extraction result.

CE produced a 4032-byte raw header aggregate. Both target and independent host verification accepted its canonical PKCS7 representation: five bytes removed, 4027 selected bytes, RSA signed span at offset 262 with length 3765, and twelve present roots. Authentication is relative to the pinned installed 2048-bit public key. An independently established OEM certificate chain and full semantic firmware applicability are not claimed.

CF's independent host analysis parsed 68 descriptors with no unknown actual tags and reconciled all nine item IDs with the clear numeric section intervals. It verified all nine section ciphertext RSA signatures before extraction. The per-item tree records and salts remain private.

| ID | Section | Cipher bytes | Original bytes | Actual result | Trial family |
|---:|---|---:|---:|---|---|
| 1001 | platform.img | 1455423504 | 1455423488 | Accepted payload after explicit offline receipt reconciliation; original driver rejected | CW + DA / CX02 |
| 1002 | uImage | 11892544 | 11892528 | Accepted | CN |
| 1003 | factory_peq.img | 9306128 | 9306112 | Accepted | CQ |
| 1004 | secos.bin | 8380432 | 8380416 | Accepted | CQ |
| 1005 | seret.bin | 3661840 | 3661824 | Accepted | CQ |
| 1006 | secos_drv.bin | 3137552 | 3137536 | Accepted | CQ |
| 1007 | dtb.bin | 1564688 | 1564672 | Accepted | CQ |
| 1008 | ddr.init | 166416 | 166400 | Accepted | CK |
| 1009 | sign.bin | 1040 | 1024 | Accepted | CI |

For every accepted section, including platform.img, the retained result records ciphertext RSA verification, exact output size, strict sixteen-byte PKCS7 removal, authenticated original-size and original-byte CRC validation, and zero retries. The relevant runners also require native count/cleanup/wipe evidence and exact stage removal. CQ's authored actual report explicitly records all five cleanups and removals. Accepted outputs remain private. Neither accepted extraction nor signature verification means firmware was installed.

The smallest whole-section trials established sign.bin and ddr.init behavior; CN separately established streaming uImage behavior. The subsequent five CQ sections were separately fixed and validated. Platform.img then separately completed the larger fixed-section stream. This is measured coverage of these nine sections, not qualification of arbitrary future inputs or general updater behavior.

## Source-backed cryptographic and tree model

The exact retained installed SWUCoreTV is the static authority for the mapping; no downloaded OEM code is executed by the host parser. CF retains decisive instruction anchors and explicit field layouts in its [call map](../swu-item-schema-20261028cf/schema-call-map.md).

The header's successful hardcoded CryptoInfo candidate is `(mode=1, keySize=2, derive=1, RSA-hash=2)`. The alternative candidate has different AES parameters. A successful candidate is copied to the graph, then pipeline; section AES inherits these words. AES descriptor tag 14 carries the section's own salt and processed size. It does not serialize a plaintext passphrase or independently select AES mode/key size/derivation.

The source-backed command-0 mapping is p2 `(0,1)`, p3 `(1,0x201)`: decrypt with the selected encrypted item-master input and the authenticated section salt. The master remains bound to the reviewed selector/content identity. No plaintext master key is exported. Command 1 consumes the exact bounded ciphertext stream; command 2 finalizes once. Helpers expose no arbitrary commands, caller-selected addresses, algorithms, paths or retries.

The three relevant integrity/authentication scopes are distinct:

| Gate | Exact scope and meaning |
|---|---|
| Header wrapper CRC | Selected unpadded header envelope; consistency check, separate from signature |
| Header signature | RSA PKCS1 with SHA512 over the exact OUIT remainder after key identifier and signature prefix |
| Section signature | RSA PKCS1 with SHA512 over the complete exact ciphertext interval; public-key ID comes from tag 16, digest selector from inherited CryptoInfo |
| Section tag-18 CRC | CRC-32/ISO-HDLC over `[0, original_size)` of the original item; excludes AES padding |
| Strict extraction padding | All nine authenticated processed sizes exceed original sizes by sixteen; extraction requires a complete canonical sixteen-byte padding block |

Each actual processing list is CRC tag 18, AES tag 14, RSA tag 16; there is no compression or patch descriptor in these nine items. Consequently the decrypted section after padding removal is the original-byte stage for these items. That conclusion must not be generalized to a different package with XZ or patch processors.

The CF parser recognizes all 21 descriptor factory layouts, enforces bounded lengths/depth/counts, consumes exact descriptor bodies and tree EOF, and distinguishes unknown optional from mandatory tags. Wire completeness is true for the actual tree. Full semantic/policy validation remains false. Parsing alone confers no authenticity, applicability, target safety or execution permission.

## Launch failures and corrected lifecycle work

CR used the original CM long-lived job route. The target positively reported Samsung UEP refusal of the unsigned `worker.sh` file. Reconciliation found no supervisor/child identity receipt or native stdout, no known fixed process, and zero TLS connections/cipher/raw bytes. This is a launch-layer failure before the native sequence. Its retained stage and records are separate from subsequent work.

CX supplied a fresh fixed native stage/config to the CV inline-shell route. Its stored-script hash guard rejected the preparation before supervisor dispatch. Retained child/worker lengths differed from the intended text: the pinned root agent's argument quoting doubled backslashes, changing embedded printf escapes. No supervisor/child marker, native stream or TLS connection was observed. The guard detected a real content change; the crypto or native engine did not fail.

CM/CV host tests and source reviews covered local setsid/PID/session binding, deadlines, pipe detachment, lock lifetime, output bounds, and refusal without retries. They did not qualify Samsung's unsigned-script policy or the target root agent's string transformation. Those target-specific failures are observations that constrain the next implementation; an earlier source PASS must not be presented as target success.

CW is an additive correction: fixed script bytes are prepared through separately bounded base64 commands, verified by exact stored identity, then dispatched by a short inline `sh -c` command. No UEP policy disable is part of that design. Preparation, launch, and native acceptance remain separate gates. The DA-controlled CX02 attempt passed preparation/launch and completed native streaming in 555190 ms. The final counts were 22209 updates and 22215 guards, with full ciphertext/output counts, EOF/hash, session close, three releases, context finalization and wipe confirmed. Parent-controlled reconciliation/cleanup of a known failed job is separate from native execution and must not be described as an automatic retry.

CX's native source remains the reviewed fixed platform helper: native alarm 1700 seconds, TLS total 1600 and per-I/O 10; outer supervisor/host bounds are 1750/1800. It uses the same fixed CF plan and unmodified core/native/CG/CJ behavior as CR apart from the fresh stage/config seal. Observed platform sequence counts match the source-derived 22209 updates and 22215 full guards. The parent carried forward the fixed unused CX payload/config only through its new explicit controller manifest and positive prior-job reconciliation, with zero earlier connections; no native execution was retried automatically.

The native result was not originally accepted by the DA controller: runtime `[GC_INFO]` bytes interleaved with the final status. A separate explicit offline reconciliation examined the retained 345471-byte stdout and found exactly one actual 385-byte status span at `[344064,344449)`. Removing only that unique span restored 3020 exact GC start/end pairs with matching timing/IDs. The reconciliation accepted that native receipt while retaining `original_driver_accepted=false` and `reconciled_native_receipt=true`. No native sequence, root/firmware mutation for reconciliation, or TEEC invocation was repeated. Independent host validation then accepted all 1455423488 original bytes, strict sixteen-byte padding and authenticated tag-18 CRC; exact job and stage cleanup passed. This is a validated payload plus a reconciled receipt, not an originally accepted driver run.

## Offline kernel and board findings

[CS's report](../firmware-kernel-analysis-20261028cs/report.md) independently validates the extracted uImage header/data CRCs and establishes byte equality of the declared kernel payload with the previously acquired kernel image. The raw image is ARM64 Linux 5.4.261. This confirms the existing export analysis against those bytes; it does not hash executing kernel text, recover full vmlinux/debug information, or establish module/observer deployment readiness.

The extracted DTB section contains ten bounded FDTs. Tree 1 matches the retained runtime dtsversion and is the strongest source-backed board candidate. Its bootargs differ in root slot, console and serial configuration from runtime, positively showing that boot configuration is patched. Thus it is not a complete live-tree identity proof.

The candidate tree resolves TCON PMIC/ERR_DET/VDD/sync inputs to GPIO controllers/lines, and several power/AC signals to micom GPIO banks. CS also separates TCON mailbox resources from the distinct micom control/messagebox blocks. These are useful static endpoints for future source tracing; they establish neither present electrical levels nor safe live MMIO/GPIO access. Raw GPIO flags are not automatically electrical assertion polarity. Names such as micom version getter do not imply passive cached reads: CS finds an active message/completion path. Existing logger routing setters are mutating, not passive discovery.

Opaque appended kernel and DTB material remains unidentified. The dummy panel node is not evidence of the physical panel timing. No content-triggered root cause or prevention setting has been established by firmware extraction.

## Reproduction and remaining work

The reproducible chain is encoded in the authored modules and retained evidence references rather than a one-command target script. A reviewer can reproduce bounded parser/fixture checks in a disposable host copy, with private actual inputs supplied only where expressly required:

1. Acquisition's bounded directory validator establishes exact main MSD section extents; its report separately records HTTPS/ZIP checks.
2. CC's authentication model distinguishes CRC representation selection from RSA acceptance. CE's independent host verifier repeats authentication of the retained raw header.
3. CF's `item_schema.py` parses only the signed OUIT span. Its `test_item_schema.py` runs normally and with `python3 -O`; `apply_authenticated_header.py` is a private-input host analysis that reauthenticates before writing private plans.
4. CG's host mock engine tests establish operation layout, capacity accounting, count/failure handling and cleanup. CJ's local TLS tests establish pinned transport/quarantine behavior. Native target bindings are separately fixed, reviewed and measured by the central trials.
5. Each accepted trial's private result is checked against the matching fixed section plan. Final padding/length/CRC acceptance occurs on the host after transport/native acceptance, before downstream offline analysis.
6. CS's `fdt_bundle.py` and eight-test suite reproduce bounded FDT parsing and candidate selector/property evidence from the private accepted DTB; its kernel audit revalidates exact-image export records.

This index ran no reproductions that contact the target. Frozen source directories should stay unchanged; use a disposable copy for builds/tests that create outputs. The index deliberately omits live runner invocation instructions and private configuration.

Next analysis priorities, in dependency order:

1. Preserve the completed platform trial and its original rejected-driver / later offline-reconciled-receipt distinction. Future helpers should emit a dedicated bounded final receipt through a channel that runtime GC output cannot interleave; do not assume each Console.WriteLine arrives as one indivisible stdout record. A logging/parser fix requires its own source review, not a claim that the rejected driver originally passed.
2. Identify accepted platform.img's container/filesystem from its bytes, then inventory offline with bounded read-only tooling. Locate TCON/provider modules, board data, update assets and log/config definitions by source anchors and identity. Do not assume that a filename identifies OLED-controller firmware or a persistent protection setting.
3. Reconcile candidate DTB properties with retained runtime evidence and exact provider registration/code. Preserve the distinctions between static board choice, boot patching, active GPIO getters and electrical fault causes.
4. Recover stronger symbol/owner relationships for TCON fault/log routing and kernel/module interfaces. Keep image offsets, DT physical resource addresses and runtime virtual addresses separate.
5. Compare any firmware configuration/limits to the already captured synchronized blackout operands and the exact producer/comparison path. Extraction supports this investigation but does not itself justify a RAM/protection change.
6. Treat the companion MSD, full metadata policy/applicability rules, opaque appended data and any signature chain beyond the pinned installed key as separate open work with their own input and scope records.
