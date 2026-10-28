# Snapshot status and open questions

This is a research snapshot of an active investigation, updated on 2026-10-28. It covers access/root lifecycle, UI control and debloat, firmware formats and acquisition, target-specific SWU/TEE ABI, kernel/platform and controller/hardware mapping, logging and bounded instrumentation. The blackout case remains unresolved at the causal level. Personal viewing history, network identities, boot identities and account data are removed or generalized.

The [earlier CA/CB/BZ evidence update](update-20261028.md) and [later firmware extraction update](firmware-extraction-20261028.md) separate the completed milestones:

* CA preparation and the accepted CB software-onset capture, including one synchronized Left down/up pair, 18 retained scientific windows and a 250.294 ms conservative clean/fault USB bracket. A separate owner blackout report has no instantaneous physical timestamp. Key causation is not established.
* The rejected subsequent recovery harness, despite native helper exit/ioctl/close zero, confirmed cleanup and the owner's reported picture return. No retry rehabilitated the rejection.
* Failed BX/BY adapter attempts and diagnostics, followed by one successful bounded BZ installed-service command sequence 0/1/2. Its 4032-byte output was quarantined and wiped; no validated metadata or payload names were published.
* Complete official encrypted firmware acquisition with archive/member CRC and reread/hash checks. These establish transport/storage consistency, not OEM signature authenticity or decrypted metadata validity.

* Later CE header authentication and CF source-backed tree/parameter mapping, then nine accepted main-section outputs with strict padding/original-size/CRC validation. The platform original driver rejected interleaved stdout; an explicit unique-receipt/GC-framing reconciliation accepted the native result without another TEEC call.
* Offline CS analysis confirms the extracted stored kernel and identifies a candidate board DTB wiring map, while positively retaining live-tree/boot-patching limitations.

Material gaps remain:

* The ordinary RT event's actual mode, selected threshold and aggregate values at the decisive comparison are not all contemporaneously captured.
* The runtime producer, scaling and units of the PrePD-related table remain unproven.
* The link from MCU RT fault state to electrical suppression and emitted light is incomplete. The accepted software capture does not supply an exact physical-light timestamp.
* Stored firmware image identity is qualified by selected functions; some stored image-0 functions differ. Whole executing-image equivalence is not established.
* CE/CF and the nine extraction results close the specific main-package authentication/tree/section-validation gaps, independently of the earlier BZ service return. Full metadata semantic/policy/applicability validation, an independently established OEM certificate chain, the companion package and arbitrary-input portability remain open.
* A target-side kernel interface can fail independently of a source-proven kernel capability; retained ENOSYS results keep their identity qualification.
* The CA phase premise is conditional and its FD/sysfs checks are snapshots, not continuous queue ownership proof.
* Ongoing DB/DC filesystem investigations are explicitly deferred from this snapshot. Header/tree/engine/transport source, tests, reviews and the completed nine-section result are included; private OEM outputs and actual metadata/configuration fixtures are excluded.

The [external gaps register](../research/research-20261027-external/GAPS-AND-EXPERIMENTS.md), [current retained checkpoint](../research/CURRENT-INVESTIGATION.md) and neighboring workstream reports contain proposed discriminators and reasons for rejected experiments. No publication check contacts the television.

The initial release's source cutoff was **2026-10-27 23:34:25 UTC**. It remains immutable at its [original commit](https://github.com/TheMHD1/samsung-s95f-research/tree/e8a8b1170b712ab3114e3235318b32b4b3817679), including its separately added [BX preflight/ARM-flag report](post-cutoff-swu-trial.md). The new snapshot does not rewrite that release's audit or earlier failed outcomes. Current enumeration/export timestamps and explicitly deferred scope are recorded in `manifests/export-summary.json`; [release history](../manifests/release-history.json) preserves both releases' accounting.
