# Managed USB AP_EXCO input snapshot

Offline-built, dry-by-default ARM32 helper for one bounded read-only snapshot of the pointer anchors, the first 824 bytes of the 826-byte ordinary AP_EXCO allocation, and the complete 1004-byte derived AP_EXCO allocation.

The fixed geometry is documented in `../ap-exco-input-snapshot-20261027w/read-plan.md`. The native path permits exactly three target-`0x101` read requests (six bulk transfers), with no write, reset, retry, UI action, persistent operation, or caller-selected address. It validates both pointer anchors before either dependent read. Prior exact response bytes remain in the outcome if a later operation fails.

`run-once.py` is dry unless passed `--execute`, an absolute fresh output directory, and the exact reviewed manifest SHA. Execution stages only the three pinned runtime files in a private directory, runs a separate self-test, performs exactly one native invocation, retains the authenticated envelope/raw files, and removes the target stage only after a fully accepted known-Ready result.

This build does not claim atomic sampling, event-time reconstruction, current executing-body identity, physical panel causality, or runtime semantics for the captured numeric fields. In particular, ordinary `+0x10a/+0x10c` can be changed by a helper when ordinary `+0x116` is nonzero, so packaged initializer values do not determine their later state.

Offline verification:

```sh
python3 build-offline.py
```

No TV was contacted during derivation, build, or tests.
