# Independent N checkpoint review

Recorded 2026-10-27 UTC. This is an independent read-only byte, inventory,
containment and parent-preservation audit of the published N code-view
checkpoint. The only new file is this review, which the manifest explicitly
excludes. No TV, network, root, USB, controller, device-node, UI, firmware,
configuration or storage operation was made. No copied source builder,
verifier, wrapper or native binary was imported or executed.

## Verdict

**PASS.** No byte, size, scope-inventory, parent-checkpoint, symlink or path
containment discrepancy was found.

The reviewed manifest is:

```text
code-map-qualified-followup-20261027n/code-view-evidence-manifest.json
SHA-256 a365b51fe014af70d50697bdeefd0b5eac2d6abb342fda1c6d21ab6ec2b145d7
schema candidate-code-view-evidence-manifest-v1
files 28
bytes 543563
```

The manifest parses as complete JSON with no duplicate keys. Every listed
path is normalized and relative, contains no `..` component, resolves within
the N checkpoint, is a regular non-symlink file, and matches its recorded
size and SHA-256. Independently summing the listed sizes produces exactly
543,563 bytes.

## Exact N inventory

I reconstructed the inventory from the two declared frozen roots and five
standalone scope files rather than trusting the manifest's path list. The
reconstructed map equals the manifest exactly:

| scope | files | bytes |
| --- | ---: | ---: |
| `capture-once/` | 9 | 360,798 |
| `source-checkpoint/` | 14 | 139,340 |
| `capture-findings.md` | 1 | 2,448 |
| `code-map-qualified-followup.md` | 1 | 11,224 |
| `code-map-qualified-followup.py` | 1 | 9,867 |
| `reader-source-review.md` | 1 | 12,523 |
| `runtime-review.md` | 1 | 7,363 |

Both frozen roots are real directories rather than symlinks. Recursive
inspection found no symlink anywhere in N. Apart from the manifest itself and
this explicitly excluded future review, there is no unlisted ordinary file in
the checkpoint. No symlink can redirect a listed path outside N.

The manifest accurately leaves these outside its byte guarantee:

- mutable investigation navigation and the ordinary fault model;
- the O callback-source evidence/helper work; and
- future P derived-object provenance work.

## M parent preservation

The parent is:

```text
ap-exco-source-read-20261027m/ordinary-provenance-evidence-manifest.json
SHA-256 26b5cc4faa8a3c03917b92ac48254ba359362bd201830cdf29fb229154b3dd0b
files 49
bytes 615642
```

The N manifest's parent row exactly records that path base, path, hash, count
and byte total. I independently read all 49 parent rows, verified every file's
size and SHA-256, required regular non-symlink containment beneath the shared
evidence base, and reconstructed M's six scope-root plus two-extra-file
inventory. The reconstructed M map equals its manifest exactly. M's excluded
checkpoint review and generated Python caches remain outside that 49-file
parent identity as declared.

This establishes that N was reviewed against the same frozen M provenance
checkpoint, including its additive callback-source lineage correction. It
does not cause N to absorb later excluded M review prose or future O/P work.

## Captured code-view boundary

This review did not rerun content-analysis code. It verifies the preservation
of the retained finding: the three N raw windows have the exact bytes, sizes
and hashes recorded by the frozen checkpoint, and the retained result says
all three sequential windows matched the selected stored-package ranges.

That match is strong evidence about the returned selector-1 mapped code view
at these three ranges. It does **not** prove:

- that a core's current program counter was executing any matched byte;
- that selector 1 names the stored component ordinal or a particular physical
  core;
- whole-image or whole-core memory identity outside the three windows;
- that the predicate executed during the physical V6 event;
- event-time state, UI causality, physical panel recovery, or a repair; or
- permission or safety for a patch, write, reset, bypass, protection change,
  persistence operation, high-bank access, POFLG action or return-guard
  change.

The capture windows are sequential rather than atomic. Their exact match is
not a core-PC trace or execution proof.

## Scope caveats

- “Frozen” means the listed bytes and inventory are preserved. It does not
  promote failed, conditional or explicitly limited claims into accepted
  conclusions.
- The source checkpoint and native DLL are historical reviewed artifacts;
  their inclusion is not authorization to execute them again.
- The manifest itself and this review are outside its `files` map. The
  manifest is bound here by its independently checked SHA-256.
- This audit covers bytes, inventory and containment only. It did not import
  or execute copied builders/verifiers and does not substitute for the source
  and runtime reviews already frozen in N.

Within those boundaries, the N checkpoint and its complete M parent are
internally consistent and byte-for-byte intact.
