# Published sleep-evidence manifest: independent post-snapshot audit

Audit time (UTC): 2026-10-27.  This file was written after publication and is
deliberately outside the frozen snapshot; it is not an additional manifest
entry.

## Verdict

The published manifest is internally consistent.  Its own SHA-256 is
`956d690aae4dad5309db6af6324c329d4e67bf29f8bd9e7601f8c26ae4157296`, matching
the published value.  It anchors 260 unique listed files totalling 98,276,246
bytes.  An independent byte-for-byte SHA-256 check of every listed file found
no missing files, duplicate paths, size mismatches, or digest mismatches.

The manifest is an integrity snapshot, not an acceptance decision.  Its
explicit classifications remain `physical_recovery_confirmed: false` and
`whole_mode2_capture_accepted: false`.

## Reproducible verification

Both of the following completed successfully against the published bytes:

```text
PYTHONDONTWRITEBYTECODE=1 python3 sleep-evidence-index.py --verify
PYTHONDONTWRITEBYTECODE=1 python3 -O sleep-evidence-index.py --verify
```

Each reported:

```json
{"verified_files":260,"bytes":98276246,"manifest_sha256":"956d690aae4dad5309db6af6324c329d4e67bf29f8bd9e7601f8c26ae4157296"}
```

Independently of the index program, this audit read each manifest entry under
the declared root, recomputed SHA-256, checked its byte count, and checked
path uniqueness.  Result: `independent_hash_rows=260`, `unique_paths=260`,
`actual_bytes=98276246`, and zero errors.

The declared scope is an explicit retained-file list.  The manifest excludes
`__pycache__`, `obj`, mutable documentation named in the manifest, and the
manifest file itself; later additions, including this audit, are outside its
scope.

## Explicit rejected / non-accepted evidence states

| Evidence record | Manifest-pinned SHA-256 | Status independently read from the record |
| --- | --- | --- |
| `overnight/sleep-mode2-20261027a.onset/record.json` | `357e7f517ff019c1f185de4233a87f1a8ccd44e9716f5ccdf9e82e003eb86df0` | `accepted: false`, `diagnostic_eligible: false`, `technical_capture_complete: false`; rejection is `ValueError: duplicate AVOC ioctl enter`; salvage is explicitly `incomplete-unclassified`. |
| `overnight/sleep-investigation-20261027a/stock-mode2-trial/outcome.json` | `647723f1950603a1423f5ded97e1d5e74bfc06fc7d65ce0b29573bc43ee505e2` | `capture_technically_accepted: false`, `accepted_sequence: false`, `diagnostic_eligible: false`, `physical_state: unobserved`, and `recovery_inferred: false`. |
| `overnight/sleep-investigation-20261027a/avemon-all-syscalls-20261027a/record.json` (V1) | `29a2f76e738e8f9444a8755937d6f2ef6bd72e2225930dfb53d626d2888b9531` | `accepted: false`, `technical_capture_complete: false`, `physical_state: unobserved`; error is `ContractError: Root client failed`. |
| `overnight/sleep-investigation-20261027a/avemon-all-syscalls-20261027b/record.json` (V2) | `4f2dc7510b528fa5162b7ee11f9628831c6df22e4fa70b479e552e57a576b52c` | `accepted: false`, `technical_capture_complete: false`, `physical_state: unobserved`; error is `ContractError: Root client failed`. |
| `overnight/sleep-investigation-20261027a/avemon-all-syscalls-20261027c/record.json` plus its eligibility audit (V3) | record SHA-256 `20f31ce338c78d9a3c65c7bcbcfaa3cd33583df407289fc5d831d2f88ad48404` | The source record deliberately remains `accepted: false`, while the separate eligibility decision accepts the defined two-second AVEMonMain syscall-pairing question: gzip CRC valid, 190,711 decoded bytes, 1,922 retained trace entries, 959 complete interior pairs, and leading/trailing boundary half-pairs.  It does **not** establish physical state, full-window pairing, controller state, or fault causality. |

V3 therefore did run and provides qualified runtime evidence for that narrow
pairing question.  It is not a replacement for the V1/V2 rejected attempts,
nor an accepted panel-fault or whole-window capture.

The individual MODE2 control helper record (`stock-mode2-trial/mode2.json`)
is retained with `accepted: true` for that helper's bounded operation and
`physical_state: unobserved-by-helper`.  This does not override the separate
encompassing observer/orchestration outcome above, which remains rejected and
not diagnostically eligible.

## Boundaries

This audit verifies frozen-file integrity and the recorded classifications
only.  It does not establish panel recovery, identify a hardware fault,
reinterpret the duplicate-enter condition, or convert any rejected capture
into a valid diagnostic result.  No TV, network, media-server, or target
operation was performed for this audit.
