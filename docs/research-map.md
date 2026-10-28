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

* [Completed nine-section extraction and failure/reconciliation chronology](firmware-extraction-20261028.md), [CZ phase architecture/index](../research/panel-idle-20261026/overnight/firmware-extraction-workbench-20261028cz/README.md).

* [External research index](../research/research-20261027-external/README.md), [target acquisition boundary](../research/research-20261027-external/TARGET-ACQUISITION.md), [gaps and experiments](../research/research-20261027-external/GAPS-AND-EXPERIMENTS.md).
* [SWU target applicability](../research/research-20261027-external/reports/swu-target-applicability.md), [independent ABI and helper audit](../research/research-20261027-external/reviews/swu-independent-review.md).
* `research/research-20261027-external/sources/swu-target-applicability/`: authored ABI inspection, offline plans and input manifests. Vendor library bytes are omitted.
* `research/research-20261027-external/sources/minimal-swu-helper/`: isolated commands 0/1/2 prototype, mock backend and tests. [Host reproduction](reproduce.md) describes what is runnable without private inputs.
* Adapter/runner source, host tests and actual outcome reports under `swu-metadata-adapter-20261027bx/`, `swu-metadata-adapter-20261027by/` and `swu-metadata-adapter-20261027bz/`. [The evidence update](update-20261028.md) connects the failed preflight/loader diagnostics to the bounded BZ service sequence without inferring validated metadata.
* [Complete official encrypted firmware acquisition](../research/firmware-acquisition-20261028/acquisition-report.md): reusable acquisition/clear-directory inspection source, provenance, archive/member/section hashes and malformed-input tests. OEM ZIP/MSD bytes are omitted.
* Authored SWU header-validation function traces, byte anchors and framing models under `swu-header-validation-20261027bx/`. CC/CE/CF authentication/integration/schema source is now included as a separate completed phase. The completed [DB partition analysis](../research/panel-idle-20261026/overnight/firmware-platform-analysis-20261028db/accepted-report.md) and [DC contained reader/patch](../research/panel-idle-20261026/overnight/vdfs-reader-research-20261028dc/README.md) are included with their upstream notices; OEM trees remain private.

## Kernel, platform and hardware

* [Decrypted kernel and candidate-board DTB analysis](../research/panel-idle-20261026/overnight/firmware-kernel-analysis-20261028cs/report.md): exact stored-kernel equality, bounded ten-tree parsing, candidate wiring and boot-patching limits.

* [Detailed reverse-engineering index](../research/panel-idle-20261026/overnight/RE-INDEX.md).
* `research/panel-idle-20261026/tcon-research/`: kernel power/PM, HDMI, FRC/QDF, GPIO, pinctrl, USB/SSB, firmware address-domain and controller analyses. Includes annotated instruction excerpts and their reproducers.
* `research/panel-idle-20261026/overnight/`: executing-image qualification, kernel-observability audits, callback lifecycle, code/source fingerprints, MMIO attribution, controller arithmetic and telemetry gaps.
* [Controller findings](../research/panel-idle-20261026/tcon-research/findings.md), [ordinary fault model](../research/panel-idle-20261026/overnight/ordinary-fault-model-20261027.md), [runtime producer gap](../research/panel-idle-20261026/overnight/rt-input-producer-gap-20261027bq/source-review.md).
* Board and hardware conclusions remain in authored reports. Personal photos and complete repair-guide copies are omitted; their absence does not turn inferred topology into directly observed electrical behavior.

## Instrumentation, protocol qualification and case studies

* `research/panel-idle-20261026/overnight/managed-*`: bounded managed helpers with exact phase, length, error and cleanup rules; source, tests, reviews and result qualification remain together.
* [Original passive RT observer source](../research/panel-idle-20261026/overnight/managed-usb-rt-passive-observer/Program.cs), and `onset-sync-20261027bx/`: synchronized one-key recorder/wrapper, parser, rejected-candidate diagnostics and independent reviews.
* [CA phase preparation](../research/panel-idle-20261026/overnight/onset-preparation-20261028ca/phase-decision-v2.md) and [accepted CB onset](../research/panel-idle-20261026/overnight/onset-trial-20261028cb/findings.md), with separately rejected subsequent recovery. [Public 18-window fixture](../fixtures/onset-cb.json) and [standalone offline verifier](../tools/verify_onset.py).
* `owner-paired-recovery-20261027bh/`, `owner-repeat-recovery-20261027bi/`, `recovered-replay-phase-audit-20261027bs/`, `apps-selected-panel-recovery-20261027bu/` and `full-confirmation-20261027bw/`: outcome reports, rejected observations and qualified recovery cases. Read their lifecycle reviews, not just headline findings.
* Earlier `.onset/`, rejected source checkpoints, finite-logger and replay directories preserve failed collectors, timing mistakes, capacity bounds, corrective tests and reasons for non-acceptance.
* [Recovery boundaries](recovery.md), [evidence rules](evidence-and-methods.md), [open gaps](status-and-gaps.md).

## Firmware evidence graph and autonomous experiments

See the [current integrated guide](firmware-evidence-guide-20261028.md) for DE display/AVE source, DF cross-core RTP provenance and eight-window capture, DG graph/playbook and DH layered actual outcomes. The initial graph and later actual-outcome extension are separate snapshots. Volatile-limit work remains deferred.
