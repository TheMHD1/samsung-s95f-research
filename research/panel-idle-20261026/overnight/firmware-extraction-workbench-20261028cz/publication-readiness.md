# Additive publication preparation

Historical preparation status: this document records the first isolated candidate, before any push or public-tree replacement. Final published status is determined by the release manifests and commit history. The first candidate accounting below is historical and was produced while platform output was provisional. The phase report and section-status now record all nine accepted sections, with the platform original-driver rejection and explicit offline receipt reconciliation preserved. A final coherent export must synchronize this completed checkpoint and the final exporter revision before promotion.

## Policy correction

Read-only inspection of the existing workflow identified a concrete gap: the earlier path rule excluded only a top-level `private/` directory. New nested private metadata plans and TLS configs would otherwise have been classified as ordinary JSON. Binary extension and generic credential-pattern rules do not reliably protect these values.

The owned exporter, its tests, and publication policy documentation were updated before creating the isolated candidate. The correction:

- Rejects `private/` components at any depth and known sensitive plan/configuration basenames even when moved elsewhere.
- Rejects raw decrypted firmware, unpacked filesystem/partition/source acquisition trees and binary `.records` chunks regardless of filename extension.
- Omits denied contents, content hashes, original names and individual sizes from disposition rows. Aggregate omission counts/bytes remain available.
- Replaces private-reference rows inside mixed authored JSON inventories with omission markers.
- Defensively redacts the known nonce/salt/signature-value keys while retaining algorithm/scope descriptions and numeric parameters.
- Preserves original authored source/tests/reports outside raw private/OEM trees and existing upstream/license boundaries.

Thirteen publication/onset unit tests pass normally and with Python assertions optimized away. The new cases specifically exercise nested/moved private records without reading or hashing them, extensionless OEM inputs, extracted filesystem text, acquired source/chunk trees, retained authored tools, upstream license boundaries, and mixed inventory metadata. A final extra regression covers the actual CF byte-field key names. No target or network operation is part of those tests.

## First candidate accounting and audit

| Measure | Count |
|---|---:|
| Enumerated source entries | 21884 |
| Regular inputs | 21880 |
| Undereferenced symlinks | 4 |
| Direct/redacted exports | 5648 |
| Derived scientific extractions | 511 |
| Selected research files | 6159 |
| Omitted inputs | 15725 |
| Selected research bytes | 90821284 |
| Path-denied private/acquisition records with no individual metadata | 935 |
| Explicitly deferred active DB/DC inputs | 7 |

The isolated candidate used the existing private redaction configuration without printing or copying its contents. All 6159 selected files passed the public verifier: zero privacy-pattern/hash/manifest findings and zero historical Python syntax findings. All thirteen candidate publication tests and the onset fixture verifier passed. A separate host-only scan of 39 known actual CF salt/signature hex representations and retained TLS nonce values found zero matching public files; no tested values were printed or recorded in the audit output. This is bounded corroboration, not proof that arbitrary secrets under unknown names cannot exist.

The candidate remains in restricted local staging. No private/OEM binary or actual secret fixture is proposed as a publication exception. Actual-result summaries copy only allowlisted counts, names, lengths and validation booleans. Source-derived cryptographic fields and exact scopes remain scientifically useful without republishing the private plan/tree.

## Final selection and promotion requirements

Include authored CC/CE/CF schema/authentication source and reviews; CG engine/mock tests; CJ transport/local tests; fixed CI/CK/CN/CQ integrations and sanitized actual outcomes; the negative CR/CX launch evidence as concise derived classifications; CM/CV/CW lifecycle source/tests/reviews; CS offline kernel/DTB parser and derived findings; and this CZ phase index. Keep the official encrypted acquisition provenance already present. Preserve chronological failure and qualification boundaries.

Exclude nested private plans/configs/outputs, raw authentication and command envelopes, salts/signatures/nonces/key material, OEM archive/MSD/section/kernel/DTB/module/image/partition/filesystem copies, complete decoded OEM trees, acquired upstream snapshots outside the existing license scope, compiled helpers and build caches. Mixed manifests must not reintroduce private file metadata. Tests requiring withheld actual inputs remain explicitly private-input tests; fresh-clone claims should use the original synthetic parser/mock/local-transport suites.

Before a publication candidate is promoted, regenerate it with the final exporter source and final CZ result status, keep unfinished DB/DC work deferred until frozen, repeat manifest/privacy/known-value checks, and update top-level release navigation/history/accounting to match that exact snapshot. The earlier published release and its failure/outcome audit remain commit-pinned. This document author performed no export replacement, commit, push or target operation.
