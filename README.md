# Samsung S95F reverse-engineering workbench

An experimental research corpus for the Samsung S95F / Tizen platform: access and host-assisted persistence, UI and application control, firmware formats, kernel and display architecture, external controller protocols, hardware attribution, and bounded instrumentation.

This repository preserves the substantive work performed during the investigation, including failed experiments, rejected collectors, independent reviews, superseded interpretations, instruction traces, source reproducers, helpers, and host tests. A content-dependent physical blackout is one case study within the broader platform research. There is no demonstrated permanent blackout fix.

**Post-snapshot correction:** the first SWU adapter target invocation failed file preflight before reaching the TEE. A later audit found an incorrect ARM32 `O_NOFOLLOW` constant in that adapter; earlier broad readiness claims are superseded on this point. Read the [trial and guard-defect report](docs/post-cutoff-swu-trial.md) alongside the frozen source. No automatic retry or validated metadata resulted.

The investigated software model identifies as **QN77S95FAFXZC**, with panel **CY-AF077FLLV2H** and Linux **5.4.261**. A separate board marking identifies a regional QN77S95FAFXZA assembly. Those observations do not make other firmware or hardware revisions equivalent.

## Start here

| Topic | Entry point |
| --- | --- |
| Research map and searchable catalog | [Topic navigation](docs/research-map.md), [full document catalog](docs/catalog.md) |
| Evidence rules and experimental limitations | [Evidence and methods](docs/evidence-and-methods.md) |
| Platform, kernel, controller and firmware architecture | [Architecture map](docs/architecture.md) |
| Access, persistence, UI, application and debloat work | [Topic navigation](docs/research-map.md#access-ui-and-applications) |
| Controller reverse engineering | [Detailed RE index](research/panel-idle-20261026/overnight/RE-INDEX.md), [TCON findings](research/panel-idle-20261026/tcon-research/findings.md) |
| Firmware / SWU / TEE research | [External research](research/research-20261027-external/README.md), [SWU applicability](research/research-20261027-external/reports/swu-target-applicability.md) |
| Recovery case study | [Recovery boundaries](docs/recovery.md), [retained recovery runbook](research/RECOVER-PANEL.md) |
| Snapshot status and unresolved work | [Status and gaps](docs/status-and-gaps.md), [historical checkpoint](research/CURRENT-INVESTIGATION.md) |
| Provenance, coverage, omissions and licensing | [Publication policy](docs/publication.md), [source lineage](docs/source-lineage.md), [licenses](LICENSE.md), [manifest summary](manifests/export-summary.json) |

## Repository layout

`research/` preserves the original workstream hierarchy, so neighboring reports, tests and analysis scripts remain together. Personal names in filenames and references were normalized consistently. This is a research archive: historical scripts may depend on private retained inputs, original deployment layout or device-specific preconditions. Redacted addresses, boot identities and paths are placeholders, and exported source hashes differ from the originals where redaction changed bytes. Read the associated review before adapting a tool.

`tools/` and `tests/` contain the public export and verification tools. They operate offline. There is no automatic TV connection, deployment, controller reset or TEE call in the publication checks.

```sh
python3 -m unittest discover -s tests -v
python3 tools/verify_public.py
```

The minimal SWU prototype also has a host mock test that can be compiled without a TV; see [reproduction instructions](docs/reproduce.md). Many other retained tests intentionally require private fixtures and are not claimed to pass on a fresh clone.

## What the findings establish

The research distinguishes stored-image disassembly from executing-code identity, software state from emitted light, and source-derived possibilities from observed target behavior. It establishes substantial normal-world ABI and protocol detail, including controller request/response framing and a target-specific TEE operation layout. It does not establish all runtime event operands, the PrePD producer and units, the electrical suppression mechanism, or universal portability of recovery behavior.

New `20261027bx` onset synchronization and SWU adapter work was being developed concurrently with this export. These files are retained as **work in progress**; their presence is not evidence of an accepted live experiment. The additive [first-attempt report](docs/post-cutoff-swu-trial.md) records the known preflight failure and guard defect. Later messages and outcome reports must be read together, including explicit rejections.
