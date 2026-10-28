# Independent finite limit-comparison pre-execution checklist

**Current disposition: HOLD the frozen DQ writer.** Clean state alone does not satisfy its full profile. No DQ production invocation was performed for this review. Parent confirmed its fresh readiness and Apps/header preparation, but recovered-clean-01 is incompatible with the frozen native guard before any write. This file is host-only; frozen sources/manifests and original captures are unchanged.

## Concrete current incompatibility

Recovered DK/recovered-clean-01/start-R.bin SHA256 `2348bb88e5536e59526d876478699956d13e31c19b9881142393e82a1c91cb31` is clean stop0/fault0/gate1,c4=40. Its M flags0/2,scan1,root,geometry and other numeric guards match, except the upper endpoint below. Native GuardR first refuses atbyte0x20; GuardContext would also refuse M+0x26.

| Field, little-endian u16 | Frozen DQ expected | Recovered actual | Source-grounded significance |
|---|---:|---:|---|
| R+0x20 |3183|3161|Ordinary B-exclusion upper endpoint, copied root2420→CPU4c6 at image1bddc..bde4; a real comparator qualification input. |
| R+0x98 |25|24|Mirror of a scaled runtime temperature-like input used by image0 upper-endpoint computation. |
| R+0xac |251|254|Volatile message echo/sequence value, not immutable configuration. |
| R+0xbc |3183|3161|Alternate/mode6 B-exclusion upper endpoint, copied root24bc→CPU4c6 at image1bdaa..bdb2. |
| M+0x26 |3183|3161|Sampled CPU4c6 endpoint mirror; the native numeric gate explicitly requires3183. |

R+0x92 also differs48→54, but it is inside the already allowed historical-dynamic range and is not the new blocker. M SHA256 is `7bccc1ff04b22f03b0c31ac74c99ef0d488dfdbc58e6a421c1e0d201b008b96d`; C SHA256 is `c9bc21efabc33dc5c687f230ecf321722552c99518957cc37b833c7aaaf9c2b0`.

The selected-package source is SHA256 `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`. Image0file=VA+0x200; image1file=VA+0x40200. A bounded host disassembly of image0 function0x389d0 shows runtime getter0x27670(1) scaled by0.0625 (literal0x38aec=0x3d800000) into sl, then stored into root+2498 at0x38ae2. Getter0x27670 loads u16CPU0x20000c1e; the adjacent diagnostic label is TEMP. The same function uses `(sl−r8)` with its arguments and an object-derived average, then clamps/stores the computed upper endpoint at root2420 or24bc and stores r7/r8/sl into2494/2496/2498. This supports a temperature-like runtime-derived endpoint, not an assertion of calibrated units or complete updater/caller provenance. Source range image0VA389d0,len280,file38bd0 SHA256 `7ee4431c71b9b6c9d1bb9a55b39ebea635bc4d7e6af0299d94712c37077ba33f`; getter27670,len80,file27870 SHA256 `90e19a079e3f81d9c0dd7bb5f192df4c9b8ab90478100568fad1a2c868e9bec1`.

Image0VA9978..9986 reads the low byte of24ac, increments it, and wraps255 to0;9988..998c places the value twice in request bytes2/3. The bounded endpoint-e0 exchange checks an echoed four-byte response. Receive path9844..984c stores the duplicated matching received byte into24ac with strh. Thus exact24ac can change during an otherwise clean20s comparison and prevent a subsequent exact-profile restore. Source range97e0,len138,file99e0 SHA256 `80341a73b0933c68e6f07badb862003fa007f095ada2138dcc4095990ff2a002`; range9968,len152,file9b68 SHA256 `f7b8b3247d870b8348df29a6688f295e417b6ee281c95e299c49b2f899edfa38`. These bounded source facts do not establish every possible writer.

Do not wildcard the changed endpoint or call these differences harmless padding. An exact additive rebase could pin3161/24/254 at a second independently stable clean snapshot while retaining every other guard, but it would not guarantee the same profile after20s: the sequence and runtime-derived endpoint can change again. A dependable revised set/restore policy needs explicit separately reviewed treatment of those dynamic values, their real input role, and fresh/postwrite equality; no such revision is implemented or approved by this checklist. Parent is proceeding with read-only reference capture instead.

## Compatibility already verified offline

Frozen DQ manifest is `a7a985c9c257f8e939e440bcfe0c48266e1856406790f67f731106406536537f`, wrapper `a084f948f40965a281e6f65fb1a1dcfeb8b650c399614f27d6d7f353ff104af6`. Its readiness schema is `dq-fixed-limit-readiness-decision-v1`. The helper binds `--device N` to that fresh identity; current USB59 cannot reuse old58 readiness. Bus7/interface2/full descriptors, boot, no-holder census and centrally maintained closed-world phase lineage remain required. Same-FD native kernel GETDRIVER/statx ownership validation is unchanged.

**DP supports200 without modification.** I ran the frozen host-only `--checkpoint-fixture-clean` path and strict parser:80clean cycles/80checkpoints,all start/end alternate thresholds200,trialQualified=true,and the sampled above40 witness atcycle20 were accepted. There were zero target operations. DP DLL SHA256 `9322284894869d95efecbadbfcc359d070106504d1fbf6ab0c561dc17507afc0`; parser `9b5e476a50e73439e11a6e5ed78bae0079a1d802c054212a8974e079f77d6b3a`; manifest `ba02517d7f8bb5cae6aa4257c426b7cc50780bfdfd5e0a73a7838e2386dff9ee`. DP observes the threshold values but does not itself enforce that every live value stays200; parent analysis must check actual checkpoint/raw readback values. A20s clean run is a finite observation, not a permanent fix. A clean A0Low16>40 sample with the relevant mode/C+7 context is a source-conditional counterfactual witness; no such sample is an inconclusive sampling result, not proof that crossing never occurred.

## Execution sequence if a compatible reviewed writer is later available

1. Hold the central access lock; require fresh exact readiness, settled populated Apps/header focus and no pending child/native job. Hash the exact approved manifest/payload/parser and use a fresh output directory. A prior clean snapshot does not substitute for the helper's own live callback/R/M/C/fresh-R checks.
2. Execute one fixed `set`40→200 only. Acceptance requires7headers/14bulks, exact target0x102/address470124c4/length2/valuec800, private native receipt, readback200, all non-status bytes unchanged, ReadyForHeader, successful release/close and exact stage cleanup. Never interpret nonzero exit, missing receipt or ambiguous transport as either success or permission to replay.
3. Only after accepted set and renewed readiness/lineage, run the unchanged DP one-Left workflow once from the same prepared Apps/header baseline. Require the first complete clean cycle before its single down/up; retain all checkpoint thresholds, mode/C+7 context, A/history/q/ordinal and full raw endpoint cycles. Separate software onset, key dispatch and physical picture. DP performs no200write or automatic restore.
4. Preserve a post-test read-only DM capture before any reset when its phase/readiness premise permits. Publication capacity changes with the limit: bound200 can publish0..200,within the independent512guard, but a first48reader no longer covers the complete potential publication set. Capacity is not an electrical safety proof.
5. Restore via a separate fresh reviewed action only after assessing actual clean/fault/phase state below. Every restore needs its own fresh readiness and exact profile; no stale readiness, automatic reverse write or retry.

## Restoration and refusal decision table

| Outcome after accepted set | Next bounded step |
|---|---|
| DP accepted and clean, key child reaped, native closed/released, phase known | Separately return to Apps using the reviewed normal UI action, obtain fresh readiness/clean context, then use the separately reviewed200→40 restore **only if its full guard passes**. Restore must read back40 and clean up. Frozen DQ currently cannot promise that profile. |
| DP captures fault/scan0 | Retain the postfault DM evidence first if safe. DQ restore intentionally refuses stopped/faulted or scan-disabled context. Use the separate reviewed Apps/MODE2 operational recovery, then qualify the newly enumerated device and read back actual c4. If already40, no reverse write is needed; if clean200, restoration still requires a compatible exact guard. Do not assume reset restored the limit. |
| DP refuses before production invocation |200may remain from the accepted set. Keep the rejected record; no automatic DP retry. With positive closed/known-phase proof and fresh clean context, restoration can be considered under the full restore guard. |
| DP key/trial qualification or parser refuses, but retained native evidence is complete | Preserve the refusal; classify native lifecycle/phase and pending child independently. Offline reconciliation is not a replay or a waiver. Only positive phase/ownership/child-completion proof plus fresh readiness can permit another fixed transaction. |
| Any vendor transfer or launch is ambiguous, Unknown phase, missing receipt, pending child or cleanup/ownership unresolved | Stop new headers, including restore. Retain stage/evidence and centrally reconcile the exact attempt. No guessed restoration, phase-clearing read, automatic retry or blind reset command from this wrapper. |
| Restore itself rejects before write or after a potentially sent write | Preserve its exact native/transport evidence and writeAttempted/limitMayHaveChanged/phase. A rejected top-level result is not proof of40or200. Do not retry; reconcile and read only after a newly justified phase premise. |

The native restore is deliberately200→40 and clean-only. It cannot repair a latched stop/fault; it also requires scan1,root/mode/geometry,callback tuple,alternative gates/latches,full R profile and stable selector. Full matched OUT/IN obligations and Unknown-stop semantics apply equally to set and restore. There is no persistent firmware/boot/network change, no flash operation and no claim of a root-cause repair in this experiment.
