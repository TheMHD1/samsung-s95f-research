# Independent DV fixed-writer integration review

**PASS: no blocking defect found in the frozen native/model/parser/wrapper integration for the planned finite comparison.** This is a source and host-validation result; no DV target invocation or physical protection-safety result is asserted. I did not author DV. Only this additive review was written; frozen files were checked unchanged after the independent suites. No TV/root/network/OEM execution occurred.

Reviewed exact pins:

| Artifact | SHA256 |
|---|---|
| deployment-manifest.json | `ef6a62a10b2bba004c405e14ac75fc927b4e20803448732b2b111177d6e4aab0` |
| Program.cs | `523f6df61e78e6a2e12f666f8dac9dec8236fc345554021a9e98a0947c92f08e` |
| FixedLimit.dll | `21b597ec864b0d2e556905bd9b0c5b116203acba610155e3d25ba37c3675f4df` |
| parse-result.py | `9a1fd4db858212e06afdb18bb6de0a23bd4abd01cf74a41876e422cd26f93bb5` |
| run-once.py | `702f7a819dd1a73ea7220da9fc6bc139de14420e8eb9d593d9165102195560e8` |
| host-build-checkpoint.json | `d83a7f30931a4acd7a7bb1061b56d1d7685661b4762af6dc8964b9d2f6836fff` |
| source-inventory.json | `254b3ac64dba3cfa0e80d7715344eebaac2d9e746989cff95092ffcb7353817f` |

DU's independently reviewed model remains `7a1c2d9b9f5cc5d9136166b79be7ba16d639d18c7d92450b546db8476b3f937a`, inventory `d09e0f7486ec7c4d3f8a3095b9374198d33504124592e01858ba140c0e9ef22c`. Its separate review is `DU/reviews/independent-model-review.md`, SHA256 `e634ff18d56f160525a79f5dc32e1e8b95da7d53b30e44ec203f483a9534b574`.

## Native change and unchanged transport

The fixed action remains exactly set40→200 or separate restore200→40, at bus0x470124c4, target0x102, length2. The fixed header is `02010000c424014702000000`; payload is `c800` or `2800`. There is no caller-selected address/value, general write API in Main, retry, automatic restore, UI/power/reset action or persistent modification path. Accepted runs still have7headers/14bulk calls and six raw read windows.

Independent source-delta checks confirm byte-identical frozen-DQ Controller, real clock/native binding bodies, private receipt machinery and action surface after the fixed schema/stage-prefix substitution. Callback/read addresses, write header and full matched-payload behavior remain unchanged. The same-FD cached GETDRIVER and native statx ownership proof is retained; the previously wrong managed symlink-resolution premise is not reintroduced. Cached descriptors are consumed once and subsequent revalidation checks identity rather than advancing the FD descriptor stream.

The pending matching transfer obligation is preserved when the clock fails after a complete header. A short or thrown transfer leaves Unknown and stops subsequent headers. No new cleanup path sends a compensating transfer from Unknown. Native release/close failure remains an error rather than an accepted operation. The40s cooperative transaction budget,2s bulk limits and root45s/host75s limits are unchanged; they are not guarantees against uninterruptible kernel I/O.

## Model, context and transaction guards

C# Endpoint uses explicit unchecked unsigned32 arithmetic for the polynomial, then extracts bits7..22, caps before applying the floor, and matches DU. GuardR first pins all static parameters and unchanged profile bytes, then applies the source-derived bounded endpoint test. Thus the arithmetic function's generic parameters do not become caller-controlled target inputs. Only R20/R98/Rbc and zero-high-byte echoRac receive the new modeled treatment. Echo0..254 may change or wrap;255/high-byte values refuse.

The root, aa0/ac2 mode1 flags, scan1, directional/lower thresholds, C geometry/profile/selector, clean stop/fault/gate, logger, callbacks, alternative gates/latches, normal thresholds200 and all other previously exact bytes remain guarded. M upper at decimal38 (M+0x26/CPU4c6) must equal validated ordinary baselineR20. No alternate3200-mode6 exception or endpoint wildcard has been added.

Both baseline and fresh R must independently qualify at the old limit. GuardPair then requires equal thermal tuple20/98/bc and all remaining nonhistorical bytes except bounded echo and the fixedc4 action byte. After the write, readback must qualify at the new limit and another GuardPair repeats that stability check. Selectorca is consequently stable throughout. Both endpoints matching one diagnostic model remains a restrictive admission policy; DU's selective-refresh counterexample is correctly refused, not labeled invalid firmware.

Postwrite drift is not reported as a prewrite refusal or silently undone. The tests and code preserve writeAttempted=true, writeTransportComplete=true when applicable, limitMayHaveChanged=true, protocol state and raw readback when the new semantic guards fail. ReadbackVerified is set and change ambiguity cleared only after the full readback/model/pair checks. There is no reverse write in catch/finally.

## Parser and wrapper

The strict parser embeds the exact frozen DU model, retains independent binding validation, checks each raw window extent/hash and all accepted transport/phase/time/cleanup claims, validates both baseline→fresh and fresh→readback pairs, and independently verifies the M mirror against baselineR20. It accepts only the two fixed actions. Failure flags, a changed thermal tuple, stale endpoint, mode6, bounded-echo violation, dirty state or altered fixed profile cannot be represented as an accepted receipt merely by updating its raw hashes.

The wrapper delta from frozen DQ is limited to pinned source/checkpoint/parser values, fixed DV schemas/stage prefix, and the native selftest count. The reviewed inherited readiness/staging/framing/collection/cleanup logic is retained. It defaults to zero-I/O dry operation. Execution requires the exact manifest, a fresh digest-pinned `dv-fixed-limit-readiness-decision-v1`, fixed USB identity and explicit closed-world phase lineage; metadata is not endpoint-queue proof.

A fresh nonce0700 stage contains the three pinned managed payload files; receipts are exclusive0600 files. Native GC stdout is a separate bounded diagnostic blob, never repaired into semantic JSON. Selftest135901 must pass before production invocation. One production invocation is made; saved envelope/receipt precede strict parse, and failure/ambiguity retains the stage instead of retrying. Accepted cleanup requires the exact inventory/integrity and positive Ready/released/closed state. No fallback recovery or automatic restore was added.

## Independent host results

- **6366 checks in normal Python and6366 under `-O`**, independently rerun from the final frozen files. Each suite checked462 generated shell commands; maximum7992bytes. The suite uses fake root transport/local command fixtures, not the TV.
- The native fake-operations selftest executed through each suite and produced the exclusive receipt with **135901 passed assertions and targetOperations0**. Receipt creation/mode/exclusivity/symlink refusal, parser framing, staged cleanup failures and modeled semantic mutations were covered.
- **23 independent source-delta checks**, normal and optimized, passed. The4096-temperature cross-language vector SHA is `923784f6db98e7d188d283dd9adcd3282c92fb57597595fe1e09d268b71c834c`.
- **36 additional checks** accepted two synthetic receipts composed from the actual admitted mode1 R/M/C data, one for each fixed action, then rejected altered accepted/write/readback/cleanup flags, limitMayHaveChanged, mode/selector/high-byte/echo mutations and individually stale endpoints after updating the raw window hashes.
- All20 source-inventory entries matched after the suites. Host-only `build_manifest()` regenerated the reviewed manifest byte-for-byte. Its three managed payload files total61058bytes. No rebuild or source regeneration was required or performed by this reviewer.

The actual admitted R/M/C source pins are recorded in the DU independent review; those data establish a source-compatible starting profile, not the state of a later target invocation. Fresh central readiness and native guards still decide whether an operation can proceed.

## Finite sequence and remaining interpretation limits

I also reviewed `DK/experiment-plan-v6.md`: accepted set precedes a separately qualified DP run; postfault DT evidence precedes recovery; clean restoration is a separate fresh guarded invocation; reinitialization does not imply value40 without readback; and an unresolved phase/ownership/child state prohibits further headers or blind resets. A known-phase clean prewrite restore refusal remains a separately coordinated operational decision, never an implicit native action.

DP's20s is an **observation budget**, not a hard20s wall-clock exposure of threshold200. Staging, selftest/census, key join, collection, Apps navigation and restoration add operation time, and refusal/Unknown can require explicit reconciliation. The plan must retain the recorded resolution rather than claim automatic timed rollback. Equality at sampled thermal endpoints does not prove continuous stability; a later legitimate update can conservatively refuse readback or restoration.

The same field also bounds record publication:200 permits indices0..200, below the known512-entry guard, but changes instrumentation behavior and is not a pure comparator-only intervention. Host review and index capacity do not prove electrical safety, physical picture state, permanent prevention, selected-A history, packed-data producer identity or whole live-code equivalence. Those claims remain outside receipt acceptance.
