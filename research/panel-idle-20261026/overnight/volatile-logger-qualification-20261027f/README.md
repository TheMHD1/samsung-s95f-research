# Volatile controller logger: verified finite test

One live three-second qualification completed and passed independent runtime
review. Logging readbacks were `0 → 1 → 0`; all 16 USB transfers were exact,
and the private target stage was removed. No helper from this test remains
running. No physical panel observation, initiating blackout, firmware flash,
protection bypass, permanent root or repair was established.

- [Actual result and remaining diagnostic gap](progress.md)
- [Authenticated runtime replay audit](runtime-audit.json)
- [Independent runtime review](independent-runtime-review.md)
- [Exact byte comparison](byte-comparison.json)
- [New message format and direct argument producer](new-log-format-trace.md)
- [Offline architecture](architecture-review.md)
- [Review decisions and rejected candidate](review-history.md)
- [Exact reviewed helper artifacts](reviewed-helper/)
- [Raw authenticated run](logger-smoke-once/)

The offline build verifier checks the canonical helper beside this directory.
The runtime auditor replays retained commands and artifacts entirely offline.
A failure or ambiguous record must never be treated as restoration proof.
Evidence is frozen: 53 files / 1,084,601 bytes.
[Manifest](logger-qualification-evidence-manifest.json) SHA-256:
`e2bd3a19dd06aab6524da2a2d4142c0e02b242f5045c37a09842b69346942d6d`.
Publication and optimized read-only verification passed. This README remains
a mutable navigation page. The parent D5/D4/D3 snapshots verified unchanged.

Independent final freeze review checked all53 manifest rows, the exact
on-disk inventory and19 reviewed-helper copies. Every size/hash matched.
D6 and D5/D4/D3 passed normal and optimized read-only verification. No
frozen file was edited during that review.
