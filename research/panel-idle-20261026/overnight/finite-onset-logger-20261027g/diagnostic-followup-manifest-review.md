# Independent diagnostic-followup manifest review

Reviewed read-only on 2026-10-27. I did not import or execute any listed
source, builder, helper, or verifier and made no TV, network, root, USB,
controller, UI, or firmware operation.

Published manifest:

- `diagnostic-followup-evidence-manifest.json`
- SHA-256:
  `4b93587a1062f2611fa0c2cdaeb6b0f7f0ef1fac637693d0003e0e0ed0bd33da`

## P3 — one mutable-exclusion path is metadata-only and incorrect

The `excluded_mutable` entry `../../CURRENT-INVESTIGATION.md` resolves from
this D7 directory to:

```text
${S95F_EVIDENCE_ROOT}/panel-idle-20261026/CURRENT-INVESTIGATION.md
```

That path is absent. The actual root investigation file is one level higher:

```text
../../../CURRENT-INVESTIGATION.md
${S95F_EVIDENCE_ROOT}/CURRENT-INVESTIGATION.md
```

This does not change the frozen inventory: neither path is a listed row, the
actual file is outside the D7 tree, and the explicit 4-root plus 34-file scope
reconciles exactly. Because the published manifest is immutable, this review
is the bounded erratum rather than a manifest rewrite.

## Verification result

No other finding was identified.

- The manifest has exactly 75 unique rows totaling 1,111,428 bytes. Every
  current file size and SHA-256 matches its row.
- Every listed path is relative, canonical, contained under this D7
  directory, a regular non-symlink file, and belongs to either an exact scope
  root inventory or the explicit standalone list.
- Exact root inventories are 8 files in `fault-context-after-v6`, 8 in
  `selector-context-after-v6`, 12 in `source-checkpoint-fault-context`, and
  13 in `source-checkpoint-mode-selector`. Those 41 files plus the 34
  standalone files equal all 75 rows; there is no unlisted regular file in a
  scoped root and no listed row outside that union.
- The frozen selector closure and its corrected inputs match their manifest
  rows: review `b5c553b6...`, report `670c1177...`, and verifier
  `c092d4ac...`.
- The parent pins are unchanged. Independent row replay of
  `runtime-evidence-manifest.json` at
  `2d1d1427ea37c70e5b6ee37e301488027f6b2a0ff64f7d591884ca6faa252534`
  verifies 84 files and 4,515,096 bytes with its exact 10-root plus
  15-standalone inventory. Independent replay of
  `fault-capture-evidence-manifest.json` at
  `3bda86db80ddc3a0d5d6b0127e2dbc0ce6c1dcc19b15af3ad7b919bd29d12fb6`
  verifies 194 files and 6,083,645 bytes with its exact 14-root plus
  46-standalone inventory; its prior-manifest pin equals the runtime-manifest
  digest.
- `../executing-code-diagnostic-route-20261027h` resolves outside this frozen
  D7 scope as declared.

The publication is byte-consistent and inventory-complete subject only to
the P3 mutable-exclusion path erratum above.
