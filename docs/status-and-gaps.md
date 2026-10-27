# Snapshot status and open questions

This is a publication snapshot of an active 2026-10-27 investigation. Original timestamps are retained for scientific ordering. Personal viewing titles/history, local network identities, boot identities and account data are removed or generalized. The full retained [checkpoint](../research/CURRENT-INVESTIGATION.md) supplies historical detail; later workstream records can supersede it.

The general platform work includes root/access lifecycle, local UI input, application and home-provider patching, settings/debloat rollbacks, firmware selection and SWU layout, target-specific TEE ABI analysis, kernel observability, controller and hardware mapping, and bounded collectors. The blackout case remains unresolved at the causal level.

Material gaps remain:

* The ordinary RT event's actual mode, selected threshold and aggregate values at the decisive comparison are not all contemporaneously captured.
* The runtime producer, scaling and units of the PrePD-related table remain unproven.
* The link from MCU RT fault state to electrical suppression and emitted light is incomplete.
* Stored firmware image identity is qualified by selected functions; some current stored image-0 functions differ. Whole executing-image equivalence is not established.
* Callback and daemon policy may constrain an isolated live SWU caller. Host ABI and mock success alone do not prove trusted-application acceptance.
* A target-side kernel interface can fail independently of a source-proven kernel capability; the retained ENOSYS results must retain their identity qualification.
* The onset synchronization and SWU adapter directories carrying `20261027bx` are work in progress. Source, drafts and host checks are preserved; only separately accepted outcome reports establish completed live work.

The [external gaps register](../research/research-20261027-external/GAPS-AND-EXPERIMENTS.md) and original reports contain proposed discriminators and reasons for rejected experiments. No publication check here contacts the TV.

The source copy completed at **2026-10-27 23:34:25 UTC**. The original research snapshot remains frozen. An additive [first SWU target-attempt report](post-cutoff-swu-trial.md) now accompanies it: exit 65 at file preflight, before selector/TEE construction. A subsequent audit found `O_NOFOLLOW` was given the x86-64 value `0x20000` rather than the ARM32 value `0x8000`. This is a real guard defect, but is not established as the refusal cause. Earlier broad no-defect/readiness statements are superseded on this point. There was no automatic retry, TEE sequence or validated metadata. The additive source/public hashes are recorded in `manifests/post-cutoff-provenance.json`.
