# Independent S–X checkpoint audit

Recorded 2026-10-27 UTC. The independent reviewer made no file writes, target/network calls, or verifier/source executions. Root records its returned findings here, outside the frozen inventory as declared in the manifest.

Result: PASS, no material issues. Manifest SHA-256 `4a68594f94a3ad5138c144cee17b4c86251efc1554ab7954df0ffa5ffbbba235`; all 98 regular files match exact size and hash, totaling 1,719,391 bytes. Schema, path base, scopes and exclusions are correct. No symlinks or path escapes were found.

| scope | files | bytes |
| --- | ---: | ---: |
| S | 2 | 26,238 |
| T | 2 | 21,693 |
| U | 1 | 11,410 |
| V | 21 | 416,302 |
| W | 30 | 527,608 |
| X | 42 | 716,140 |

Parent preservation passed byte-for-byte: M49/615642, N28/543563 and O36/552155, all 113 prior file entries unchanged. Parent manifest hashes and totals match the new manifest. The excluded generated Python cache is correctly declared. The checkpoint includes runtime/source reviews, retained raw capture/record/envelope, source checkpoint, and both superseded and accepted decoder outputs. The closure clearly identifies alias-qualified JSON as current.

Root also ran normal and optimized `checkpoint.py --verify`; both returned the same successful count, byte total, parent count and manifest hash. No additional TV operation occurred during publication or audit. All listed artifacts remain frozen; future work uses additive directories outside S–X.
