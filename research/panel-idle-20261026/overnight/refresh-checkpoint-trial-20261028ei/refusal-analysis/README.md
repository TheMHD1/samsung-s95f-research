# EI onset-01: explicit AlreadyFaulted refusal classification

**The original wrapper refused correctly.** Its native receipt reports `AlreadyFaulted`: the first R read was already faulted, so no complete clean baseline was obtained and **no Left down/up was attempted**. Native observation/transport completion is supported by eight complete read pairs, `ReadyForHeader`, released claim and closed device. This is not an accepted wrapper result or a qualified onset trial. The wrapper stopped on native exit1 before its success parser, post-census or cleanup; its original record correctly retains `cleanup_required=true` and `target_operations_status=inflight_or_unknown`.

This directory is a separate host-only classifier. It preserves the original false `accepted` value, every native byte and the original wrapper record. No receipt is rewritten/projected to manufacture success. The frozen EH decoder can also parse the original unchanged receipt as transportAccepted=true, observationAccepted=true and trialQualified=false; that limited decoder result does not override the wrapper's earlier exit gate. `decoded.json` explicitly distinguishes these states and records an exact private nine-file stage inventory for separately reviewed cleanup.

## Exact software transport boundary

The retained shape is `initial-faulted` cycle1 containing R, followed by `post-fault` cycle1 containing M,C,P,N,H,L,R. Every OUT reports12bytes/errno0 and every matching IN reports the exact fixed response size/errno0. There are eight headers,16bulk transfers and eight completed inputs, with zero writes/retries, zero completed clean cycles and zero checkpoint rows. The pending-IN obligations are all matched in the recorded sequence. The classifier validates exact schema/field sets/types, fixed addresses and sizes, canonical Base64, raw SHA-256, ordered full read-pair timestamps and raw fault-state classification.

| Window | Bus address | Bytes |
| --- | --- | ---: |
| Initial R | 0x47012400 | 256 |
| Post M | 0x470004a0 | 68 |
| Post C | 0x47000bc0 | 16 |
| Post P | 0x47000490 | 16 |
| Post N | 0x4700ba28 | 36 |
| Post H | 0x4700d0e0 | 96 |
| Post L | 0x47010f00 | 64 |
| Post R | 0x47012400 | 256 |

`raw/` contains these eight additive exports, each0600 within the owned0700 analysis directory. The source header is the frozen read-only0x101 command with exact address/length; no data-write0x102 path, key call, reset or fallback was introduced. No gate tables, fixed references or actual pointer-target header are present in this capture.

Both key call records remain unstarted/unreaped with zero stdout/stderr, no dispatch timestamps/exit codes, no armed/end timestamps, attempted=false and completed=false. The native `onsetMissed=true`, `onsetObserved=false` describes a missing initial clean baseline, not an observed transition caused by a key. The fault was present at the first recorded R; its actual start time and relation to preceding ordinary UI preparation remain unknown.

## Fault context decoded from original bytes

Initial and post R are byte-identical: stop/fault/gate = **1/4097/0**, alternate limit40, normal mode-1 limit200, mode-1 record latch41, temperature24, both ordinary/alternate B upper endpoints3161 and echo0.

The later H sample has A0 **42**, other aggregates0; all q values0; history0 **[2,0,4,0]** and other histories0. N ordinal0 is41, other ordinals0, and all source counts0. These are sequential post-fault observations, not proof of the exact score/comparator state when fault latched.

M has AA0/AC2, trainer4a2=0, aggregate4a4=0, selector mirror4c2=0, refresh counter4c4=0, publication-bound mirror40, current/saved metadata row0, x base0 and rootCPU0x20010000. C geometry is2160/1920/2880 and C7=0. End-R controls root2460/root246e are0. P retains dynamic pointer words0x20253b6a and0x202546d2.

C7=0 and publication mirror40 in this later fault sample must not be substituted for historical selected FP or fixed-A decisions. Pointer words do not expose their target headers, alias, acquisition epoch or active branch. Zero refresh/trainer fields at one later read do not establish their intermediate history or inactivity. This data does not determine a physical damage mechanism, physical light state or a fix.

## Times and refusal framing

Native start is184305055007us, deadline184320055007us and end184305068710us. The first R full pair spans [184305058224,184305063523]us; final R spans [184305065986,184305066070]us. The whole sequential read span is **7846us**. H spans [184305065822,184305065905]us. These are conservative OUT-before/IN-after software brackets conditional on source freshness, not atomic controller snapshots or optical timestamps.

The three-blob envelope is complete and hash-consistent. Selftest exit0 reports93observer/22key/46checkpoint fake checks with zero target operations; production exit is **1**, stderr empty, semantic receipt5906bytes and separate opaque diagnostic stdout109bytes. No GC stdout repair is performed. The envelope's same saved boot, native device60, immediate ordinary metadata checks and compact `bindingQualified=true` flag agree with the frozen EH code path. Full native binding syscall metadata is not retained; code/flag evidence is not a separate full binding audit.

All37 EH source-inventory entries and the regenerated manifest match. Manifest SHA-256 is `d0059b32e4e3d99a398a3763934e8927cd2967126c6d1ad9e76d8bf069f3059e`; readiness SHA-256 is `61c965a32f2dc169a0a7e954d92b684dd7cc9777b14add3b2d5cc620a1556ea4`. All seven readiness evidence references and its exact coordinator lineage statement are pinned. Cached readiness and both available wrapper censuses decode with zero matching holders/other errors, while retaining classified disappearing-FD counts. These are bounded snapshots, not endpoint-queue or continuous absence proof.

A mock transport regenerates **all36 root commands** and every saved refusal artifact byte for byte. It stops at the same `exact successful exit and empty stderr` gate after the native envelope is saved. There is no post-census, success interpretation/result, raw export or stage-removal command in that original sequence. The classifier makes no real root/network call and never imports the real root adapter.

## Cleanup and next-operation interpretation

The recorded protocol state is qualified as eight matched complete read pairs with a native ReadyForHeader/release/close result. It is not an ambiguous short/failed vendor transaction in these receipts. Original wrapper acceptance remains false and is not retroactively repaired. An exact nine-file stage inventory in `decoded.json` covers the three pinned managed payloads plus selftest/native semantic receipt/stdout/stderr. The private stage is bound by its SHA-256 and derived only from the original record; its literal path is not printed here.

This classifier performs no cleanup or recovery. `stageCleanupPerformed=false` describes the original wrapper outcome, not later independent coordinator activity. Separate cleanup must verify the exact private directory/files and their current hashes; a later EB fault snapshot or recovery still needs its own fresh identity/readiness and protocol-lineage decision. None is automatically retried or implied by this report. The inability to obtain an onset baseline is no reason to replay the one-Left trial blindly.

## Verification and freeze

`input-pins.json` lists84immutable source/capture/evidence inputs. Cloned malformed tests reject changed native acceptance/lifecycle/count/state flags, wrong window addresses, short counts, mismatched raw hashes, invalid transfer times, nonzero key activity, boolean-as-integer fields and corrupted RT type declarations. Original bytes remain unchanged. The normal and optimized `--check` runs each pass6797checks and reject76malformed cases; both reproduce the exact proof and all eight extracted raw hashes. The first export run performs extra raw-export validation, so its counter is not the `--check` count.

Run `PYTHONDONTWRITEBYTECODE=1 python3 analyze.py --check`, also with `python3 -O`. `validation.json` and `source-inventory.json` freeze this additive analysis. The source inventory pins the proof, input-pin manifest, original classifier and private raw exports; its external digest avoids a circular self-pin inside the proof. No TV/network operation or original-file mutation was performed.
