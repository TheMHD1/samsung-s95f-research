# Authenticated firmware extraction — final main-package result

All nine sections of the exact Canadian 0090-1301.0 main MSD have been extracted and validated. The final platform result completed on 2026-10-28 at 01:25:31 UTC. No firmware was installed, no OEM or decrypted payload is included, and the blackout's causal mechanism remains unresolved.

The [CZ phase index](../research/panel-idle-20261026/overnight/firmware-extraction-workbench-20261028cz/README.md) provides the architecture and source/report navigation. Its [phase report](../research/panel-idle-20261026/overnight/firmware-extraction-workbench-20261028cz/phase-report.md) and [safe section status](../research/panel-idle-20261026/overnight/firmware-extraction-workbench-20261028cz/section-status.json) preserve individual validation boundaries.

## What completed

CE acquired the 4032-byte raw header through a fixed bounded native sequence. Target and independent host checks accepted canonical padding, selected-envelope CRC and RSA PKCS1/SHA512 authentication relative to the pinned installed public key. CF parsed the bounded signed OUIT span, resolved all 68 actual descriptors and reconciled nine numeric items with the clear directory. Its static call map establishes the inherited CryptoInfo record, per-item salt/length, command mapping, ciphertext-signature scope and original-byte CRC scope. All nine ciphertext signatures were independently checked before extraction.

CI validated sign.bin, CK ddr.init, CN uImage, and CQ five separately fixed sections: dtb.bin, secos.bin, seret.bin, secos_drv.bin and factory_peq.img. Every accepted output passed strict sixteen-byte PKCS7 removal, authenticated original length and tag-18 CRC. [CQ's report](../research/panel-idle-20261026/overnight/swu-section-batch-20261028cq/actual-batch-report.md) retains its five measured outcomes.

Platform.img separately produced 1455423488 original bytes. Native execution took 555190 ms, with 22209 updates and 22215 guards. Exact input/output counts, EOF/input digest, session close, three releases, context finalization and buffer wiping passed, followed by host padding/original-byte CRC and exact job/stage cleanup.

## Original driver rejection and offline reconciliation

The final DA controller did **not** originally accept its native stdout. GC logging interleaved with the final status and caused the parser to reject the receipt. An explicit offline reconciliation of the retained output found one unique 385-byte native status span. Removing exactly that span restored 3020 exact GC start/end pairs with matching timing/IDs. It accepted the native receipt without another TEE invocation; the result retains `original_driver_accepted=false` and `reconciled_native_receipt=true`. [DA's completed report](../research/panel-idle-20261026/overnight/swu-platform-controller-20261028da/phase-report.md) preserves the proof and qualification.

Earlier failures remain separate: CR's unsigned script-file launch was refused by Samsung UEP; CX's script hash guard detected a root-argument quoting mutation before dispatch. Neither produced a native section stream or TLS connection. The additive CW route prepared fixed script bytes using bounded base64 commands and dispatched a short inline shell command, without disabling UEP. Source reviews and host tests did not establish target utility/policy behavior; these measured failures must remain visible beside later success.

A future receipt should use a dedicated bounded channel immune to runtime log interleaving. This is a logging/parser lesson, not grounds to rerun TEEC, erase rejection history or treat provisional streamed bytes as accepted plaintext.

## What the extracted kernel and DTBs add

[CS's offline report](../research/panel-idle-20261026/overnight/firmware-kernel-analysis-20261028cs/report.md) validates uImage header/data CRCs and establishes equality of its declared kernel payload with the earlier stored kernel acquisition. The image is ARM64 Linux 5.4.261. Existing export analysis therefore remains attached to those bytes; executing kernel text was not hashed, and full vmlinux/debug/module qualification is still incomplete.

The ten-tree DTB bundle supplies a source-backed candidate board selection matching the retained runtime dtsversion. Bootargs differ, positively showing boot patching. Its GPIO bindings narrow static fault/control wiring, and its MMIO descriptions separate TCON resources from distinct micom blocks. These findings do not prove the live tree, current GPIO levels, passive getter behavior, safe register access, external-controller protocol identity or blackout cause.

## Reusable work and publication boundary

This snapshot adds original authentication/schema/parser source, mock streaming and local TLS tests, fixed native integration source, independent reviews, sanitized result classifications, lifecycle fixes and kernel/DTB analysis. Read the [reproduction guide](reproduce.md) before running historical tools. Actual private metadata/configuration fixtures, salts/signatures/nonces, keys, OEM images/filesystems/modules, raw authentication/transport records and compiled payloads remain excluded.

The exporter now denies nested `private/` trees and moved sensitive plan/config basenames before reads/hashes, omits private-reference metadata from mixed inventories, and excludes raw extraction/acquisition trees independently of extension. [Publication policy](publication.md) explains the tests and accounting. An unchanged source ABI or a passing host mock is distinct from measured target compatibility.

Full semantic metadata policy/applicability, an independent OEM certificate chain, the companion MSD, live-tree/runtime-image equivalence, the PrePD producer and blackout prevention remain open. Ongoing DB/DC filesystem work is outside this frozen snapshot.
