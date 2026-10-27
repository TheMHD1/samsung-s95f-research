# External source research: Samsung S95F blackout investigation

Started 2026-10-27 UTC. This phase reviews the owner's seven supplied GitHub
links and additional primary sources against gaps in the existing target
investigation. It does not assume a repository's claims are correct or that
shared Samsung branding means shared firmware, pinouts or ABI.

The original objective and current target evidence are in the
[project entry point](../README.md) and
[current investigation](../CURRENT-INVESTIGATION.md). The demonstrated
[recovery](../RECOVER-PANEL.md) is a control for later experiments, not the
completion criterion.

## Research workstreams

Ten GPT-6.1 Sol researchers were assigned in successive waves, with at most
three running alongside the parent. They own separate report/artifact paths;
the parent coordinates target reads and integrates the result. No researcher
was assigned a TV command or live helper execution in this phase.

| Workstream | Deliverable |
| --- | --- |
| Supplied remote-control projects and topic discovery (parent) | [Controls/discovery](reports/controls-discovery.md) |
| Root/persistence claims and upstream changes | [Root sources](reports/root-sources.md) |
| Kernel tracing, quiet-tizen and exact ABI dispatch | [Kernel tools](reports/kernel-tools.md) |
| Hardware identity and firmware acquisition | [Hardware/firmware](reports/hardware-firmware.md) |
| Video measurement APIs and native buffer extents | [Video measurement](reports/video-measurement.md) |
| Downstream RGB dispatcher and local sampler | [RGB controller dispatch](reports/rgb-controller-dispatch.md) |
| Installed SWU client and TEE ABI | [SWU target applicability](reports/swu-target-applicability.md) |
| Controlled content intervention | [Content-control experiment](reports/content-control-experiment.md) |
| Independent kernel/firmware/root-source review | [Independent audit](reviews/independent-audit.md) |
| Independent installed SWU/TEE review | [SWU audit](reviews/swu-independent-review.md) |
| Minimal SWU source prototype and host mock tests | [Prototype design](reports/minimal-swu-helper-design.md); deployment remains unfinished |

Use the [gap register](GAPS-AND-EXPERIMENTS.md) to choose the next experiment.
The [source registry](source-registry.json) indexes original researcher
inventories; shared commits are grouped so forks are not counted as independent
hardware replications. The [target acquisition record](TARGET-ACQUISITION.md)
separates ordinary file/configuration reads from the unperformed TEE calls.

[Prior BW document snapshots](document-snapshots/bw-prior/snapshot-provenance.json)
preserve the exact report bodies matching that older checkpoint, even as the
current project entry point changes. New phase checkpoints should snapshot
mutable documents as files, not only retain their old hashes.

## Supplied sources to account for

1. <https://github.com/JoergZ2/ovos-skill-my-samsungctl>
2. <https://github.com/jakubpas/samsungctl>
3. <https://github.com/topics/samsung-smart-tv>
4. <https://github.com/jss8649/quiet-tizen>
5. <https://github.com/DemonKingSwarn/samsung-tv-tizen-root>
6. <https://github.com/levkropp/samsung-tv-root-untethered>
7. <https://github.com/chris-ritsen/samsung-tv-root>

A GitHub topic page is discovery material, not a technical implementation.
Record the selected underlying project and inspect it before relying on it.

## Required content of a finding

Each report records source URL, immutable commit where available, license,
reviewed files, acquisition date, actual implementation, compatibility limits,
what was already known locally, new evidence, contradictions, and a concrete
next action. An upstream assertion stays attributed until independently checked.
No external finding silently changes a target fact or makes a failed capture
valid. A negative search result means the bounded search found nothing;
it does not prove that documentation does not exist.

## Initial open questions

| ID | Gap | Evidence needed |
| --- | --- | --- |
| G01 | Exact event that enters the persistent-black fault | Last-clean/first-fault mode, selected limit and operands tied to navigation and physical feedback |
| G02 | Producer and physical meaning of the controller input table | Actual writer/DMA path or documented peripheral binding; stored constants alone are insufficient |
| G03 | MCU fault to loss of physical output | Matched error/output state and hardware sequence; Linux composition is insufficient |
| G04 | Trustworthy instrumentation without an invalid combined collector | Verified trace facilities or bounded instrumentation with proven ABI and cleanup |
| G05 | Installed/controller firmware identity and acquisition | Format/section validation, executing-image binding and transport provenance |
| G06 | Reversible modification and recovery route | Target-correct loading/signature/storage knowledge and recoverable rollback |
| G07 | Untethered access across cold boot | Actual target boot hook and privilege proof, independent of another model's demonstration |

The owner's permission for testing and modification is already given. The
remaining technical constraints concern correctness, reversibility and keeping
the TV usable; they are not requests for renewed permission.
