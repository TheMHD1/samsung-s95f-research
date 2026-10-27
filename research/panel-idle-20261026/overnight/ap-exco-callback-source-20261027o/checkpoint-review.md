# Independent checkpoint review: O–R callback provenance block

Reviewed 2026-10-27 UTC. This file is the explicitly excluded future review
named by the checkpoint manifest. No manifest-listed O, P, Q, or R artifact was
rewritten. The audit was metadata-only: it did not import or execute copied
builders, rerun content verifiers, contact the TV or network, or perform any
target operation.

## Verdict

**PASS.** Manifest
`callback-provenance-evidence-manifest.json` has SHA-256
`c8876fcb5c6d2f5e41e21d2e202f35c4304629524c2f7cdc7bea94ed44c2d404`.
Its path base `..` resolves to the `overnight` directory. All 36 listed files
exist at safe relative paths beneath that base, are regular files rather than
symlinks, and reproduce their declared sizes and SHA-256 values. Their exact
aggregate is 552,155 bytes.

The reconstructed inventory is exact:

| frozen scope root | files | bytes |
| --- | ---: | ---: |
| `ap-exco-callback-source-20261027o` | 26 | 476,484 |
| `ap-exco-derived-object-provenance-20261027p` | 4 | 28,491 |
| `ap-exco-caller-provenance-20261027q` | 3 | 22,884 |
| `code-write-readiness-20261027r` | 3 | 24,296 |
| **total** | **36** | **552,155** |

The reconstruction recursively enumerated all four declared scope roots and
then applied only the manifest's declared exclusions:

- `ap-exco-callback-source-20261027o/callback-provenance-evidence-manifest.json`;
- this `ap-exco-callback-source-20261027o/checkpoint-review.md`; and
- generated `__pycache__` directories and `*.pyc` files.

The generated P bytecode-cache file presently on disk is therefore correctly
outside the evidence set. After those exclusions, the actual and declared
path sets are identical: no listed path is missing and no other ordinary file
under O–R is unaccounted for. No file or directory symlink occurs in the four
scope roots, every manifest key is normalized and relative, and every resolved
listed path remains below the declared path base.

## Complete parent checkpoints

The O manifest's two parent declarations match both the current manifest
bytes and the complete independently reconstructed parent inventories:

| parent checkpoint | files | bytes | manifest SHA-256 |
| --- | ---: | ---: | --- |
| M, `ordinary-provenance-evidence-manifest.json` | 49 | 615,642 | `26b5cc4faa8a3c03917b92ac48254ba359362bd201830cdf29fb229154b3dd0b` |
| N, `code-view-evidence-manifest.json` | 28 | 543,563 | `a365b51fe014af70d50697bdeefd0b5eac2d6abb342fda1c6d21ab6ec2b145d7` |

For M, every one of the 49 entries reproduces its size and hash. The actual
inventory across its six declared roots plus its two explicit extra files is
exact after applying its declared manifest/review and generated-cache
exclusions. There are no symlinks or path escapes in that scope.

For N, every one of the 28 entries reproduces its size and hash. Its five
explicit scope files and the recursive contents of `capture-once` and
`source-checkpoint` reproduce the exact declared set. There are no symlinks or
path escapes in that scope.

N's parent declaration still binds the exact M manifest/count/byte tuple
above. M's three retained D7 parent-manifest declarations were also compared
with the current manifest bytes and each parent's embedded count/total:

```text
runtime-evidence-manifest.json
  84 files / 4,515,096 bytes
  2d1d1427ea37c70e5b6ee37e301488027f6b2a0ff64f7d591884ca6faa252534

fault-capture-evidence-manifest.json
  194 files / 6,083,645 bytes
  3bda86db80ddc3a0d5d6b0127e2dbc0ce6c1dcc19b15af3ad7b919bd29d12fb6

diagnostic-followup-evidence-manifest.json
  75 files / 1,111,428 bytes
  4b93587a1062f2611fa0c2cdaeb6b0f7f0ef1fac637693d0003e0e0ed0bd33da
```

This last comparison binds the M parent metadata; it is not a new recursive
content audit of those three older D7 checkpoints.

## Historical P review status

P's `independent-review.md` remains preserved as historical review evidence.
Its former ordering finding is not an open finding against the frozen P source
pins: the separately listed `review-closure.md` records that the corrected
report and verifier include the unconditional `0x2f5d8` call, conditional
`0x2f980` call, direct `+0x2fc` clear, and post-helper ordering, and closes the
P2 finding. The checkpoint correctly preserves both the historical review and
its closure rather than rewriting either document.

## Scope boundary

This audit establishes checkpoint integrity, inventory closure, safe path
resolution, and parent-manifest continuity only. It does not independently
re-adjudicate firmware semantics, execute a helper, make a live-state claim,
or expand any protection, persistence, bank, POFLG, return-guard, or write
branch.
