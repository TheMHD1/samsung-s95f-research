# Reviewed pre-roll observer: first accepted passive TV smoke

The new pre-roll observer has now completed one independently accepted five-second passive capture on the TV. This removes a technical preparation obstacle; it does not diagnose or repair the physical blackout. There were zero human annotations, so physical picture state remains unobserved/incomplete and diagnostic eligibility is false.

## Reviewed implementation and corrections

The [new source](observed-preroll-onset-capture.py) and [tests](observed-preroll-onset-capture-tests.py) implement the separately [reviewed design](observed-preroll-onset-design.md). The physical/annotation window remains exactly START..END. Trace arming, a bounded read-only per-thread syscall sweep, and a declared pre-roll precede it. Complete calls crossing START can be reported separately; missing entries, unresolved physical overlaps, ring loss, lifecycle ambiguity and unstable relevant file descriptors reject. `running` is an indeterminate `/proc/.../syscall` result and never qualifies by itself.

Independent review caught defects in the first implementation before a live run:

- Nested module dispatch still reached older validators. Both layers are now explicitly installed/restored, and a complete mocked lower capture tests the real validation route.
- Earlier/prelude FD attribution could use a later mapping. Unstable earlier mappings now produce unknown attribution.
- Physical-window FD instability was not included in the aggregate check. All boundary/window/tail pairs now require the relevant stability contract.

These were fixed in new files only. Historical rejected captures and earlier source archives remain unchanged. The corrected implementation passed 78 offline tests, Python compilation, four generated-shell syntax checks, emitted-quiescence-shell fixtures, a no-transport completed lower-run test, and independent exact-byte review. Parent reran all 78 tests before the one live smoke.

| Final offline artifact | SHA-256 |
|---|---|
| `observed-preroll-onset-capture.py`, 38,679 bytes | `355d98bc04ab26b962fb3e92dc0953dd2aa6ccc837456efd49fbdd5b4329e697` |
| `observed-preroll-onset-capture-tests.py`, 35,127 bytes | `144f0a4dc188542180c4a66f4853ba31d61e5909073a9480756527caf6c22de1` |
| Design, 18,395 bytes | `1e0935d8ad62161d3ee00c194265f0a771f97ef84379b5470f8c7fd2710565cc` |

Read-only reference copies and parent test output are in [the reviewed archive](observed-preroll-onset-reviewed-355d98b/archive.json). Copies are reference evidence, not standalone executable tools; their dependencies live in the original directory.

## Actual smoke and scope

The unique run [preroll-smoke-20261026t1942.onset](preroll-smoke-20261026t1942.onset/record.json) started at host UTC `2026-10-26T19:39:16.009280+00:00` and finished at `19:39:51.582482`. The label is a unique identifier, not a precise timestamp. Command exited zero. Result:

```text
accepted = true
technical_capture_complete = true
cleanup_verified = true
diagnostic_eligible = false
physical_state = unobserved-or-incomplete
absence_claim_supported = false
human annotations = 0
```

The actual staged shell is 30,596 bytes, SHA-256 `f466a3234d5d7a47188c3fd2c54d790a45965f81aaa20c919e08173249b66c77`. It differs from the shorter offline fixture label's shell size/hash because private paths contain the run label. Independent review rebuilt this exact labeled shell and matched the staged/saved bytes.

The collector had PID/process group `3679`, start ticks `16292074`, target uptime `65180.13`. Process/source/mapping/pointer checks passed. No remote display setter, key, getter invocation, service restart, module load, hardware write or recovery action was added by the observer.

## What the raw data validates

All five markers were owned by the validated collector and used the same trace marker source:

| Marker | Trace clock |
|---|---:|
| TRACE_ARMED | `65178.894161` |
| PREROLL_START | `65179.115040` |
| START | `65180.149922` |
| END | `65185.155380` |
| DRAIN_END | `65185.261025` |

The enable bracket was `65178.88..65178.89`. The prelude was `0.220879` seconds, declared pre-roll `1.034882` seconds, physical-eligibility window `5.005458` seconds and return drain `0.105645` seconds. All satisfied the predeclared bounds.

The exact same 23 AVOC TIDs passed the initial/pre/arm/quiescent/end inventories. Every first quiescence attempt yielded a numeric non-54 syscall state; no `running` qualification or retry exhaustion occurred. The sweep took about 0.15 seconds. This validates feasibility on this run, not guaranteed scheduling behavior on every run.

Trace ring retained/wrote/decoded **10,488/10,488/10,488** events, with zero reported loss and no I2C syntax error. Region event inventories were enable-slop 15, prelude 699, pre-roll 968, window 8,693, drain 108, post-drain zero. No tracked fork/exit or relevant FD change, unmatched row, pending call or post-drain syscall row was present.

Completed syscall-54 pairs were outside-context 105, pre-roll 428, physical-window-originated 2,128, window-tail zero, start-boundary zero, drain-only 43. **This actual smoke did not exercise a live start-boundary pair.** Boundary classification is supported by offline fixtures and a separately labeled synthetic marker-only replay of a byte-pinned historical trace, not by inventing an overlap in this run. The original historical 1901 capture remains rejected.

Sampling retained 22 monitor rows and five sequential QD branch rows. Measured monitor/branch rates were about 4.468/1.005 Hz; QD row spans were 0.42..0.48 seconds, within the declared two-second maximum. Endpoints passed. All 191 expected DD operations had complete successful summary pairs; `sample-errors.txt` contains those expected DD summaries, while collector/launch stderr are empty. These reads are sequential, not an atomic snapshot or an active-branch/output measurement.

Vlog retained 29,739 ordered records over about ten seconds, met endpoint coverage, had a maximum observed inter-record gap of 0.01 seconds, and terminated naturally. This is bounded coverage evidence, not proof that an unlogged event did not occur.

## Cleanup and independent audit

The saved authenticated root cleanup response has exit zero, no timeout, empty stderr and stdout `0\nCLEAN\n`. Cleanup verified the stated global trace baseline and absence of the named collector/instance/staging/expiry resources under the owned-process identity rules. It does not assert global absence of unrelated TV processes. No observer experiment is left running from this smoke.

Independent offline review rehashed all seven transferred sidecars, reconstructed the exact shell, reran the source-pinned metadata/FD/trace/sample/DD/vlog/annotation validators and reproduced the record's results. Both the code and the actual result were cleared within this passive smoke scope.

| Retained artifact | SHA-256 |
|---|---|
| `record.json` | `2d881b86485426da63acbeff38eac3eb94d3edc1c977490f511b95f526bfcc2c` |
| `trace` | `cb31443829a4e3ac13ce8dcec3ffa7fd01876bea85da6be6a692986e8c3b5655` |
| `meta.txt` | `e2a9bdd94ee4415322d6bc4e7728b30650fd3b33638ae91065f7b79f95873542` |
| `samples.txt` | `3709671508d60f6f69e7793bdb0d75b32f1c61dbf8377965729166205463d964` |
| `sample-errors.txt` | `73fb41b150534e589959427fe2badc602aa32776a38c32f61e3f7891e2ea6d52` |
| `vlog-after.txt` | `5e3cb4686d823f12010317d156211cad913e5f4e914363b2a7b652fffafb2a98` |
| `fds.txt` | `8be297a31648671ee017828f3fc274423f23cca3f2bf35f3bbd06570603efed1` |
| `cleanup.json` | `31095c2a9e11274ca05166be2cd095423cf9a950c33dc9f9a0be12290429cb2a` |

## Next observed use

The remaining diagnostic capture requires an available physical observer, visible populated Apps as the initial control, and one deliberate transition to the owner's known sparse-page trigger. Keep settings, composition mode and firmware fixed; record optimization warnings separately. Human visible/black annotations need conservative reaction and clock uncertainty and must fall wholly inside START..END. The pre-roll cannot supply a physical label. This report authorizes no unattended recovery or repeated triggering.

An 85..90-second full capture still needs its own observed validation and resource/coverage review. This smoke proves only that the new finite mechanism can acquire and clean up successfully on the current TV. It does not justify claiming a permanent root, repaired panel, identified fault, prevention across reboot or physical recovery.
