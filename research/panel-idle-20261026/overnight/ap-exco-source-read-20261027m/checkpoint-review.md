# Independent H–M checkpoint review

Recorded 2026-10-27 UTC. This is a read-only byte, inventory, containment and
publication-policy audit of the already published H–M checkpoint. The only
new file is this review, which the checkpoint explicitly excludes. No TV,
network, root, USB, controller, device-node, UI, firmware, configuration or
storage operation was made. No copied verifier, source builder, native binary
or wrapper under `source-checkpoint/` was imported or executed.

## Verdict

**PASS.** No byte, inventory, parent-checkpoint, symlink-containment or
publish-once discrepancy was found.

The reviewed manifest is:

```text
ap-exco-source-read-20261027m/ordinary-provenance-evidence-manifest.json
SHA-256 26b5cc4faa8a3c03917b92ac48254ba359362bd201830cdf29fb229154b3dd0b
schema ordinary-provenance-evidence-checkpoint-v1
files 49
bytes 615642
```

The manifest has no duplicate JSON keys. Every listed path is normalized and
relative, contains no `..` component, resolves beneath the evidence base, is
a regular non-symlink file, and matches its recorded size and SHA-256. The
sum of the 49 independently read sizes is exactly 615,642 bytes.

## Exact H–M scope

The manifest inventory and a separately reconstructed filesystem inventory
are identical:

| scope | files | bytes |
| --- | ---: | ---: |
| `executing-code-diagnostic-route-20261027h/` | 3 | 28,618 |
| `rtp-scan-input-origin-20261027i/` | 4 | 26,724 |
| `rtp-alternate-runtime-origin-20261027j/` | 2 | 18,446 |
| `rtp-baseline-live-comparison-20261027k/` | 3 | 6,909 |
| `rtp-packed-buffer-origin-20261027l/` | 4 | 21,779 |
| `ap-exco-source-read-20261027m/` | 31 | 509,958 |
| `public-architecture-context-20261027.md` | 1 | 1,963 |
| `finite-onset-logger-20261027g/external-code-map-search-followup.md` | 1 | 1,245 |

All six scope roots are real directories rather than symlinks. Recursive
inspection found no symlink anywhere in those roots. There are no unlisted
ordinary files inside the declared roots after applying only the published
exclusions:

- this `checkpoint-review.md`;
- the checkpoint manifest itself;
- `__pycache__/` directories; and
- `*.pyc` files.

The two extra files are regular non-symlink files within the evidence base
and match their recorded rows. The manifest records the mutable investigation
navigation files and the future N/code-fingerprint work as outside scope;
this review makes no claim about their bytes.

## D7 parent preservation

All three parent manifests are regular files with their expected immutable
hashes. For each parent, I reconstructed its declared individual-file and
recursive-root inventory, found no missing or extra scoped path, then checked
every listed file's size, SHA-256 and non-symlink containment:

| parent | manifest SHA-256 | files | bytes |
| --- | --- | ---: | ---: |
| `runtime-evidence-manifest.json` | `2d1d1427ea37c70e5b6ee37e301488027f6b2a0ff64f7d591884ca6faa252534` | 84 | 4,515,096 |
| `fault-capture-evidence-manifest.json` | `3bda86db80ddc3a0d5d6b0127e2dbc0ce6c1dcc19b15af3ad7b919bd29d12fb6` | 194 | 6,083,645 |
| `diagnostic-followup-evidence-manifest.json` | `4b93587a1062f2611fa0c2cdaeb6b0f7f0ef1fac637693d0003e0e0ed0bd33da` | 75 | 1,111,428 |

The H–M manifest's `parent_manifests` rows exactly match those hashes, counts
and byte totals. “Unchanged” here means byte-for-byte equality to the three
published parent inventories; it does not convert a retained failed,
ambiguous or conditional parent result into an accepted one.

## Publisher audit

The reviewed publisher is
`ap-exco-source-read-20261027m/publish-provenance-checkpoint.py`, SHA-256
`9fcab595c3fd63a2316b1db8e877af416114b9a1136225fb46353520d5595a86`.

Its inventory construction:

- rejects a symlink at a scope root or anywhere recursively beneath a scope
  root;
- requires every inventoried object and extra to be a regular, non-symlink
  file resolving under the evidence base;
- excludes only the two named checkpoint outputs and generated Python cache
  artifacts;
- verifies all listed files in each pinned parent manifest; and
- derives file counts and byte totals from the actual rows.

Both of these completed successfully and returned the published 49-file,
615,642-byte manifest hash:

```text
python3 -B publish-provenance-checkpoint.py --verify
python3 -B -O publish-provenance-checkpoint.py --verify
```

Optimized mode is meaningful because the publisher uses explicit `need()`
checks rather than Python `assert` statements.

I then invoked publication mode once against the already existing manifest,
with bytecode generation disabled. It returned exit status 1, emitted no
stdout, and ended with the expected `ValueError: refuse second publication`.
The manifest SHA-256, inode, size, modification time and change time were
identical before and after. A complete post-refusal `--verify` also passed.
The publisher computes and validates current and parent inventories before
the existence refusal, but performs no mutation during those reads; the write
path was never reached. For a first publication, the preliminary existence
check is reinforced by exclusive `xb` creation.

## Scope and interpretation caveats

This checkpoint proves preservation and provenance, not the truth of every
historical interpretation within the frozen files. In particular, the
corrected callback-source lineage remains deliberately additive:

- older frozen material that associated callback getter slot
  `0x200002cc` with ordinary AP_EXCO block `0x4500ff14` remains present as
  historical evidence;
- `source-lineage-erratum.md` and `pointer-layout-followup.md` supersede that
  interpretation without rewriting those bytes;
- the corrected lineage distinguishes ordinary AP_EXCO pointers at
  `0x200002c4/0x200002c8` from the separate `0x1000c`-registry AP_EXCO object
  at `0x200002cc`, whose captured value is `0x450158a8`; and
- the two retained fixed source windows remain authentic raw observations of
  ordinary AP_EXCO storage, but not observations of the callback's third
  object.

The source checkpoint and native DLL are frozen reproductions of what was
reviewed and run; their inclusion is not authorization to execute them again.
Likewise, the manifest does not prove a physical panel observation, repair,
executing-code identity, field semantics, active configuration bank, global
bus alias, or causal fault mechanism.

Two narrow publisher limitations do not invalidate this published object:

1. `--verify` validates the file map, parent map, count and total directly;
   it does not independently compare every descriptive metadata field. This
   review separately checked the current schema, roots, extras and exclusions
   under the manifest's pinned SHA-256.
2. Initial publication writes directly to an exclusively created manifest
   rather than a temporary-file rename, so an interruption during a future
   first publication could leave a partial new file. The present manifest is
   complete, valid JSON and fully verified, and second publication is refused
   without mutation.

No content-analysis verifier was rerun for this review; the outcome is limited
to the byte/inventory and publication guarantees stated above.
