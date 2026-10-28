# EM dense reference-refresh checkpoint candidate

EM is ready for independent host review. It requests a 25 ms cycle-start period, a 2 s cooperative observation ceiling and at most 60 completed 54-byte checkpoints. The read map, request/reply implementation, claim binding, intervention, capture retention, output cap and cleanup policy are inherited exactly from frozen EH. This work performed zero target, root-adapter or network operations and executed no OEM code. Existing workstreams were not modified.

Program.cs differs from EH only in the default duration, default period, native schema and dry-run budget metadata. NativeBinding.cs and OnsetKey.cs are byte-identical; full Run, ReadPair and ReadSet are unchanged. ScoreCheckpoints.cs changes only its schema. ReceiptMain.cs changes only the private stage prefix. Transport parsing narrows the fixed duration to 2 s; the synchronized key parser changes only its derived transport pin. The outer decoder changes schemas, interpretation metadata and its parent pin, with identical raw-source recomputation. The wrapper changes schemas, assembly/stage names, budget metadata and derived pins. `verify_source.py` proves these exact transformations against the pinned 37-file EH inventory and manifest.

The unchanged loop computes sleep as cycleStart + period − completed-cycle time, capped by remaining observation time. A service overrun creates no additional sleep. It does not guarantee 25 ms, catch up to a global schedule or sample every comparator invocation. In the host fake fixture, H starts are exactly 25,000 us apart, the first-to-last H span is 1,475,000 us and the 60-cycle clean path ends at 1,500,000 us. Actual target timing must be read from the H request/reply brackets and retained raw-cycle transfers. The cap can end recording near 1.5 s even though the ceiling is 2 s. Slower service can instead hit the time limit with fewer rows. The key worker still starts after the first complete clean cycle and may overlap multiple dense cycles.

This is a higher-load diagnostic than EH's 250 ms polling. It may perturb timing or content/controller state. Neither absent counter transitions nor matching boundary samples prove that no refresh occurred. The 54-byte record retains only H pair timestamps compactly: M/P/end-R taps remain sequential and non-atomic. Pointer words do not prove headers, epochs, active buffers or actual comparator branches. No physical light observation, fix or prevention result is claimed.

The same seven fixed window definitions are read in eight-window order R,M,C,P,N,H,L,R. The maximum remains 487 headers / 974 bulks, including a full 60th-cycle transition plus seven post-fault reads. No vendor writes, extra read address, additional key, reset, fallback or retry was added. The prior pending-IN obligation after a complete accepted OUT remains intact, including clock-error cases. New headers stop after ambiguity. Private structured receipts are exclusive files; native diagnostic stdout is never parsed as semantic JSON. An AlreadyFaulted baseline still refuses the live wrapper and retains evidence/stage for separate classification; no automatic cleanup/recovery is added for that case.

Budgets remain 2 s per bulk, 24,576 bytes per semantic receipt, 16 KiB opaque stdout, 2 KiB stderr, 64 KiB root response, 8 KiB generated command, root 45 s and host 75 s. There is no native process alarm. Adversarial serialization gives 24,255 bytes plus newline = 24,256, leaving 320 bytes. It covers all 14 late failure positions, 19-digit timestamps, duplicated escaped key errors and maximum retained transition/post-fault context. The largest generated wrapper command is 7,916 bytes. No new native outcome property or compact field was introduced.

Offline validation:

| Check | Result |
|---|---|
| Retained .NET 6.0.428 build | 0 warnings / 0 errors; cleared NuGet sources |
| Native fake lifecycle / transport | 93 |
| Key fake workflow | 22 |
| Checkpoint / failure / receipt bound | 46 |
| Exact EH derivative / pinned source | 54, normal and `-O` |
| Strict decoder / malformed fixtures | 457, normal and `-O` |
| Wrapper mocks / exclusive host receipts | 1,268, normal and `-O`; 401 shell checks |
| Cadence / overrun arithmetic / old schema refusal | 204, normal and `-O` |
| EM cached-readiness builder mock | 17, normal and `-O`; one mocked cached request |

The old DP golden fixture supplies the original 26 non-time prefix bytes. Both original H timestamp fields are independently checked at the new cadence, rather than claiming that changed-time records are byte-identical. All appended fields retain the EH cycle-coded markers and malformed-source checks. The test suite launches only managed host FakeOps commands, never RealOps or the root adapter.

`prepare-readiness.py` is an EM-only derivative of EI's cached metadata builder. Its exact delta is the fixed wrapper/schema map and local marker/module names. It requires the caller to pin the EM wrapper, provide fresh identity and a bounded explicit phase/lineage note, then retains one ordinary cached census and validates the unique EM readiness schema. It does not create an endpoint-queue proof. This builder was only mocked here. Parent coordination must qualify current identity/phase and decide any target use after independent review.

`deployment-manifest.json` pins the three managed payloads, source checkpoint, parser, wrapper and inherited adapters. `source-inventory.json` pins the complete owned source, documentation and validation outputs; host environment, obj/cache and independent reviews are excluded. `build-host.sh` reproduces the offline build and meaningful tests. No deployment or target qualification is implied by host compilation.
