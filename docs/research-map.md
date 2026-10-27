# Research navigation

The preserved tree follows the work's original chronology and dependency layout. The [full document catalog](catalog.md) lists every retained Markdown report; `manifests/source-dispositions.json` includes source code, JSON, logs and instruction traces too. Search from the repository root, for example:

```sh
rg -n 'TEEC_Operation|paramTypes|offset 56' research
rg -n 'PrePD|0x584109a4|736|0x2e0' research
rg -n 'rejected|superseded|not accepted|erratum' research
rg --files research | rg '(reproduce|test|review|findings|disasm)'
```

## Access, UI and applications

* [Local archive-root source and documentation](../research/root-access/source/README.md), [quickstart](../research/root-access/source/QUICKSTART.md), access wrapper `research/root-access/s95f-access.py`, host-assisted persistence `persistent-root.py`, and their tests.
* Stock remote/UI wrapper `research/s95f-remote.py` and `test_s95f_remote.py`. Redacted endpoints and credential paths must be replaced with a verified configuration before any adaptation.
* Application/debloat/rollback source and observed results under `research/debloat-20261025/`, `research/apps-only-20261026/`, `research/live-cast/`, `research/streaming-20261026/` and `research/screen-power-20261026/`.
* Managed component patcher sources, IL instruction excerpts and API maps are retained with their original workstreams. OEM DLLs and whole-library mechanical IL dumps are withheld.
* Root-source lineage and local working-tree differences: [source delta](../research/research-20261027-external/sources/root-sources/local-source-delta.json), [root-source audit](../research/research-20261027-external/reports/root-sources.md) where available, and [source lineage](source-lineage.md).

## Firmware, SWU and trusted execution

* [External research index](../research/research-20261027-external/README.md), [target acquisition boundary](../research/research-20261027-external/TARGET-ACQUISITION.md), [gaps and experiments](../research/research-20261027-external/GAPS-AND-EXPERIMENTS.md).
* [SWU target applicability](../research/research-20261027-external/reports/swu-target-applicability.md), [independent ABI and helper audit](../research/research-20261027-external/reviews/swu-independent-review.md).
* `research/research-20261027-external/sources/swu-target-applicability/`: authored ABI inspection, offline plans and input manifests. Vendor library bytes are omitted.
* `research/research-20261027-external/sources/minimal-swu-helper/`: isolated commands 0/1/2 prototype, mock backend and tests. [Host reproduction](reproduce.md) describes what is runnable without private inputs.
* `research/panel-idle-20261026/overnight/swu-metadata-adapter-20261027bx/`: source-only publication snapshot of ongoing adapter/runner work. Read the additive [first target-attempt and ARM flag defect report](post-cutoff-swu-trial.md); it supersedes broad earlier readiness claims.

## Kernel, platform and hardware

* [Detailed reverse-engineering index](../research/panel-idle-20261026/overnight/RE-INDEX.md).
* `research/panel-idle-20261026/tcon-research/`: kernel power/PM, HDMI, FRC/QDF, GPIO, pinctrl, USB/SSB, firmware address-domain and controller analyses. Includes annotated instruction excerpts and their reproducers.
* `research/panel-idle-20261026/overnight/`: executing-image qualification, kernel-observability audits, callback lifecycle, code/source fingerprints, MMIO attribution, controller arithmetic and telemetry gaps.
* [Controller findings](../research/panel-idle-20261026/tcon-research/findings.md), [ordinary fault model](../research/panel-idle-20261026/overnight/ordinary-fault-model-20261027.md), [runtime producer gap](../research/panel-idle-20261026/overnight/rt-input-producer-gap-20261027bq/source-review.md).
* Board and hardware conclusions remain in authored reports. Personal photos and complete repair-guide copies are omitted; their absence does not turn inferred topology into directly observed electrical behavior.

## Instrumentation, protocol qualification and case studies

* `research/panel-idle-20261026/overnight/managed-*`: bounded managed helpers with exact phase, length, error and cleanup rules; source, tests, reviews and result qualification remain together.
* [Original passive RT observer source](../research/panel-idle-20261026/overnight/managed-usb-rt-passive-observer/Program.cs), and `onset-sync-20261027bx/`: ongoing synchronized one-key onset work and independent design review.
* `owner-paired-recovery-20261027bh/`, `owner-repeat-recovery-20261027bi/`, `recovered-replay-phase-audit-20261027bs/`, `apps-selected-panel-recovery-20261027bu/` and `full-confirmation-20261027bw/`: outcome reports, rejected observations and qualified recovery cases. Read their lifecycle reviews, not just headline findings.
* Earlier `.onset/`, rejected source checkpoints, finite-logger and replay directories preserve failed collectors, timing mistakes, capacity bounds, corrective tests and reasons for non-acceptance.
* [Recovery boundaries](recovery.md), [evidence rules](evidence-and-methods.md), [open gaps](status-and-gaps.md).
