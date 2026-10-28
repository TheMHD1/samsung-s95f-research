# FE stock recovery: independent offline replay

The saved sequence establishes one accepted stock operation 41 / mode 2 request, a positive USB 64 disconnect followed by USB 65 enumeration on the same Linux boot with identical descriptors, and a later clean limit-40 readback. Both EB captures and the stock helper completed their documented cleanup. This analysis made no target, root-adapter, or network calls.

The scope is FE `fault-readiness-01`, `fault-capture-01`, both parent checks, `recovery-apps-preparation-01`, `recovery-01`, `after-recovery-identity`, `validation-readiness-01`, `recovery-validation-01`, `final-ui`, and their saved logs/phases. The 220 individually pinned inputs also bind referenced readiness evidence, source inventories, manifests, payloads, predecessor identity, and ordinary helpers. The onset trial itself is a separately analyzed capture; this report does not replace its admission.

## What was replayed

`verify.py` rechecks all 30 frozen EB source-inventory entries, regenerates its manifest, loads the actual readiness decisions, and runs the frozen strict parser on both original native receipts. It checks all 16 raw files per capture, exclusive selftest/native receipt framing and separate diagnostic stdout, authenticated root records, census snapshots, binding/identity, native completion and phase, and cleanup. With fake root responses only, it regenerates every EB wrapper command and all wrapper artifacts byte for byte: 28 saved calls per capture. It preserves the original accepted receipts and never substitutes acceptance fields.

The stock helper's fixed contract and original receipt parser are reused. Its 12 source-generated staging/invocation/cleanup calls and all helper output files replay byte exactly. Successful framing, exit zero, empty native stderr, one request, and stage cleanup are required. The receipt reports `kernel_return_zero_only` for ioctl operation 41 / mode 2 with a 12-second native deadline. It does not acknowledge a physical power action. The helper's initial `root.json` acceptance placeholder remains false in the original file; the separate final accepted result and strict receipt establish success. This distinction is retained explicitly in `decoded.json`.

The public reject-state snapshot is replayed, as are the two cached identity/census commands and three UI snapshots. The ordinary preparation records show one VOLUP pair, Right, Up, Up, with successful child statuses and no retries. These are UI operations, not threshold writes. The eight parent log phases are ordered by their saved host monotonic times; their helpers, stdout, completion statuses, and input files are pinned. No threshold-writer invocation occurs in this recorded recovery sequence.

## Actual sampled changes

| Sample | Fault USB64 | Validation USB65 |
|---|---:|---:|
| EB headers / bulks | 16 / 32 | 16 / 32 |
| R stop / fault / ordinary gate | 1 / 4097 / 0 | 0 / 0 / 1 |
| Alternate limit | 40 | 40 |
| Mode-1 record latch | 41 | 0 |
| N first ordinal | 41 | 0 |
| C7 / publication-bound mirror | 1 / 40 | 0 / 200 |
| X nonzero u16, of 48 | 41 | 48 |
| Y nonzero u16, of 48 | 41 | 48 |
| RGB nonzero u16, of 48 | 0 | 26 |
| B nonzero u16, of 48 | 15 | 22 |
| Diff nonzero u16, of 48 | 41 | 0 |

Each capture's complete 256-byte start/end R is identical. Validation's two 36-byte N windows are entirely zero: all six ordinals and all six source counts. Its scan byte is 1. Both captures have all 68 sampled primary u16 and all 68 secondary bytes zero. The validation fixed-top and fixed-bottom candidate windows are zero; the fault windows contain respectively 104 and 98 nonzero bytes. X/Y/RGB/B remain nonzero after recovery, so the data does not support universal RAM clearing. Record epochs and candidate-reference identity at the historical comparator remain unproved.

Both contexts retain AA=0, AC=2, x-base 0, 1920 lanes, packed width 2880, and operating mode 4. Operating mode is distinct from comparator category. A normal publication-bound mirror of 200 alongside alternate limit 40 is not a threshold-200 write. FE had no threshold-200 write; this is not evidence of a 200-to-40 reset.

The saved kernel log positively records device 64 disconnect at 194135.252364 seconds, device 65 enumeration at 194136.758918, matching VID/PID/revision at 194136.907194, and configuration 1 at 194136.907567. Boot and descriptor hashes match the predecessor. This proves the recorded instance boundary; it does not prove continuous identity, queue emptiness, code reload, or a cold reset of every controller domain. No cross-clock synchronization is inferred.

The stock recovery parent step spans host UTC 07:28:37.514150–07:28:42.544957. Validation ran later, 07:30:09.495107–07:30:16.958785. These are sequential captures with host gaps, not an atomic before/after observation. Final cached UI at 07:30:55 shows Apps, CSFS, and a screensaver window. There is no optical measurement or physical-picture observation.

## Verification and limits

Run from the host:

```sh
python3 -B verify.py
python3 -B -O verify.py
```

Both modes pass 1,197 checks, verify 220 pinned inputs, and reproduce the same decoded bytes. Eleven malformed cases reject: altered MODE2 exit/framing, operation/mode/classification, wrong predecessor disconnect, and EB acceptance/phase/release/close/transfer-count mutations. `validation.json` records the identical normal/optimized result; `source-inventory.json` freezes this report, analyzer, derived output, input pins, and validation.

Cleanup and USB protocol qualification apply to the recorded operations. Census snapshots do not prove continuous absence of other clients. The sampled windows are sequential; matching brackets do not make all fields atomic. No permanent fix, actual decision-time FP/selected-A branch, historical gate execution, physical lane mapping, optical recovery, universal memory clearing, or root cause is established.
