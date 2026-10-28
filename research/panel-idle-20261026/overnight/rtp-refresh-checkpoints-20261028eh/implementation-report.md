# EH source freeze — 2026-10-28

EH is ready for independent host review. This is a host-built managed .NET6 candidate, with no TV, root client, network, firmware/OEM execution, new instrumentation write or target deployment performed by its author. The parent remains the sole target coordinator. Frozen DP and all other workstreams were left unchanged.

The accepted shape is54 bytes per row, at most60 rows,15s cooperative observation,250ms nominal polling. This intentionally differs from DP's34×80/20s. All eight reads remain R,M,C,P,N,H,L,R. NativeBinding.cs and OnsetKey.cs are byte-identical DP; exact source comparison verifies that full Run, ReadPair, ReadSet, fixed window definitions, pending-IN behavior, claim/release/close and one-Left timing code are unchanged. Native caps are2s per bulk, wrapper45s/root and75s/host. Frozen DP has no native40-second alarm; EH does not add one or claim guaranteed process termination.

Each original34-byte prefix is retained byte-for-byte. The20-byte suffix contains M+2/+4/+0x22/+0x24 u16s, end-R+0x60/+0x6e u16s and P+4/+8 u32 pointer words. Source coordinates and EG pins are in source-lineage.json and README-wrapper.md. Pointers do not establish any header, alias, epoch, buffer selection or active comparator. M/P/end-R taps are sequential reads, with only the original H pair bracket compactly retained. The source permits two qualifying refresh boundary events from the same side; no distinct top/bottom requirement is assumed.250ms polling can miss an entire refresh sequence.

The original80-row proposals did not fit the unchanged24KiB receipt cap:46×80 would exceed it by261 bytes including newline,54×80 by1113. Work stopped, and parent explicitly authorized60 rows/15s. Actual adversarial serialization of the accepted shape gives24249 bytes,24250 including newline,326 bytes margin below24576. The proof includes19-digit times, maximum retained transition/postfault context, all14 late throw points, duplicated escaped key errors and the inherited128-serialized-JSON-byte error cap. No new native outcome metadata or per-row JSON was added. Adding fields requires repeating the bound proof.

Host validation completed with zero target operations:

| Suite | Result |
|---|---|
|Offline SDK build|0 warnings,0 errors, .NET6.0.428 retained SDK; cleared NuGet sources|
|Native fake lifecycle/protocol|93 checks|
|One-Left fake workflow|22 checks|
|Compact row/failure/capacity|46 checks, worst24250 including newline|
|Exact source delta|43 checks normal/-O, byte-identical results|
|Strict decoder|457 checks normal/-O, byte-identical results|
|Wrapper mocks/exclusive host receipt|1268 checks normal/-O,401 shell commands, maximum7806 bytes|

Decoder tests independently mark all60 M/P/end-R source values with cycle-specific patterns, distinguish start/end R values, check full u32 pointer decoding, compare every34-byte prefix to frozen DP's host golden fixture and mutate every appended retained field. They enforce15s/60 rather than accepting an old20s/80 receipt. Partial cycles produce no full checkpoint; all16 first-cycle transfer failures remain bounded and unretried. The wrapper includes ambiguous launch/partial receipt/bad exit/identity/cleanup rejection tests, preserves evidence and performs no automatic recovery/retry. The actual host exclusive-file test runs only fake native selftests, verifies0600 mode and refusal to overwrite, then deletes its own fresh test stage.

The frozen deployment manifest is `deployment-manifest.json`. Functional source, parser, wrapper and DLL pins were sent to parent for readiness preparation before this documentation-only inventory step. Readiness schema is `eh-refresh-checkpoint-readiness-decision-v1`; native schema is `managed-usb-rt-synchronized-key-eh-v1`; packed schema is `eh-refresh-checkpoints-v1`. `build-host.sh` reproduces the offline build and mock tests using task-owned DOTNET_CLI_HOME/TMPDIR without changing HOME/CODEX_HOME or copying an SDK. It depends on retained DP provenance/host golden fixtures and EG source audit; it is not an independent fresh-clone target qualification tool.

Remaining gate: independent review of the frozen source/manifest and parent-controlled readiness/target decisions. Host compilation/mocks establish neither target execution nor optical output. No root cause or prevention result is claimed. All host-environment, obj/cache and review scratch paths are excluded from the source inventory; only three explicit managed payload files under bin are retained.
