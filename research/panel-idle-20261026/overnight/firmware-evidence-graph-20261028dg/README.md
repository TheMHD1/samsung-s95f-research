# Firmware-to-fault evidence workbench — DG

This workbench connects the authenticated firmware extraction to the content-dependent blackout investigation. It contains an authored [investigation guide](investigation-guide.md), a typed [machine graph](graph.json), the [graph builder](build_graph.py), a [validator](validate_graph.py), and malformed/provenance tests. It performs no TV, root, USB, GPIO, playback, reset, TEEC, firmware or network operation.

The initial integrated snapshot contains98 nodes and119 edges, with17 distinct authored evidence references. Use the [evidence index](evidence-index.md) to choose a starting question and the [schema/provenance guide](schema.md) to interpret the fields. Frozen DE34-node/26-edge and DF14-node/11-edge contributions are pinned and normalized without changing their originals. DF's separate cross-core SLG addendum and later eight-window capture are explicitly distinguished from its initial host-only prototype.

Read the guide for the actual case phenotypes, source boundaries, logging placements, automatic software acceptance/rejection, next discriminators and fix/rollback criteria. No current finding establishes a permanent blackout fix. The parent remains the sole device coordinator. Autonomous software classification does not wait for owner feedback and does not invent physical visibility.

The graph distinguishes `observed`, `static`, `inferred` and `unknown` edges. Observations separately identify `native_capture`, `owner_report`, `cached_ui` and `host_validation`. Negative cases and missing bridges are explicit. A report SHA pins original retained report bytes; public redaction may change those bytes. An OEM identity pin identifies a distributed/stored asset and does not prove executing-image identity. Actual OEM inputs, decoded trees, media history, secret configuration and raw transport remain withheld.

A graph path is an evidence-navigation path, not proof that all edges happened in one incident. In particular, `0x1001`, kernel status `0x10`, ERR_DET input `1`, cached Live, a nonblack screenshot and emitted light are different facts. The guide records their timing and source limits.

Host-only reproduction:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 validate_graph.py graph.json
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_graph
PYTHONDONTWRITEBYTECODE=1 python3 -O -m unittest -v test_graph
```

Rebuilding the graph or verifying original report hashes requires the retained evidence root and frozen contribution reports; a fresh public clone can perform structural validation and synthetic tests without those inputs. Tests do not load vendor code or run deployment tools. Contribution integration preserves independently frozen DE/DF reports and pins their exact authored bytes.

Normal and optimized Python runs each passed6 test cases, including malformed provenance, secret/path refusals and contribution hash drift. Original report containment/hash validation passed. [Host validation](host-validation.json) records the counts; [source inventory](source-inventory.json) pins this snapshot's authored files. Independent [DH deadline-helper review](reviews/dh-deadline-review.md) and [DF eight-window review](reviews/df-eight-window-review.md) are source/host evidence, not device outcomes. Later observations should be separate additive records rather than retroactively changing an unobserved result into a physical claim.
