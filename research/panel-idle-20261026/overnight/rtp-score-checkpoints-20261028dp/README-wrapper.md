# Bounded intermediate score checkpoints

Host-built additive candidate, using frozen DQ native GETDRIVER/statx ownership guards and the private exclusive receipt path. Deployment remains centrally coordinated after the final independent artifact review. No target/root/network/OEM execution occurred here. This additive directory preserves frozen DF. It retains the exact R,M,C,P,N,H,L,R cycle, existing20s/80cycle/250ms bounds and oneLeft workflow after the first complete clean cycle; it adds no USB request, key call, memory write, producer flag, breakpoint or firmware patch.

A preallocated80×34-byte buffer receives one checkpoint only after all eight windows/sixteen transfers of a cycle complete. The first R has already classified clean. It is sampled RAM, not instrumentation at every comparator call. Incomplete cycles and the seven-window postfault set never invent a full checkpoint; their original retained raw context remains available. A missing sampled score above40 cannot exclude a crossing between polls. Source counts reset per dispatch and may be zero even after prior contributions.

The native scoreCheckpoints object contains schema, recordBytes34, count0..80, canonical rawBase64 and SHA256 over exactly count×34 used bytes. Records are implicitly cycle1..count in order; no duplicate trigger baseline increments count. Every integer is little-endian. Times are u32 microseconds relative to native StartUs; full timestamps remain reconstructed host-side. No epoch stamp or device physical timestamp is added.

| Packed offset | Bytes | Exact source bytes / meaning |
|---|---:|---|
|0|1|highnibble=startR classification, lownibble=endR; exact ClassifyRt:0=stop0/fault0/gate1,1=stop1/fault1001/gate0,2=Unexpected (no invented raw triple) |
|1|1|C raw+7 selector mirror |
|2|2|firstR raw+0xc4 alternate threshold |
|4|2|endR raw+0xc4 alternate threshold |
|6|4|H raw+4 A0u32 |
|10|2|H raw+28 q0u16 |
|12|8|H raw+40 fouru16 history0 |
|20|4|N raw+0 ordinal0u32 |
|24|4|H request-header BeforeUs minus StartUs |
|28|4|H reply-data AfterUs minus StartUs |
|32|2|M raw+0x2a publication-bound mirror (earlier sequential read, not proof of actual predicate FP) |

The explicit code/layout source is selected package SHA256bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0, image1 FILE=VA+0x40200. The existing CB predicate analysis/source checks establish CPU0x2000d0e4 A0, CPU0x2000d0fc qbase and CPU0x2000d108 historybase; H startsCPU0x2000d0e0. The exact decoder offsets are independently checked against retained full H/N raw windows and unchanged DF cycle order. Predicate0x1e68..0x203e processes the mode−1 slot and publishes low16(A), so fullu32 A0 and low16 score must remain distinct. Ordinal0 is not source count or a timestamp. Source/layout/running-mode identity remains conditional; the compact record omits aa/ac and normal threshold, so C7 alone cannot establish the complete actual selected threshold/mode at a predicate call.

The strict offline parser validates DP fields, packed extent/hash/types/times/state/count; removes only scoreCheckpoints; projects the old DF schema and delegates unchanged transport/key/baseline validation to pinned parent-synchronized-parser.py and transport-parser.py. Global counters remain untouched. Every retained complete cycle's checkpoint is recomputed byte-for-byte from its raw H/N/C/R and transfer times, including duplicate baseline/last-clean references. Earlier discarded cycles are retained only as compact source bytes; the parser cannot independently recapture those samples. Raw score-checkpoints.bin is saved alongside the old retained raw files.

The initial52-byte layout fit short fake timestamps but failed the24KB bound under large timestamps. The40-byte format omits optional per-checkpoint Ncount/Npair times. Nordinal was read earlier within the same completed cycle, while the H fields retain their exact full request/reply bracket. Native fake tests cover80 clean samples,80th-cycle full transition, partial-cycle failures and unchanged transaction/key counts. The output bound test uses19-digit times,80checkpoints,four retained captures and maximum successful key metadata:23556bytes<=24576,1020bytes margin (including late escaped transport/key failures; newline consumes one additional byte). Adding native outcome fields requires repeating that bound check. Host interpretation objects are outside the native receipt cap.

Production uses the DM/DL exclusive0600fixed JSON receipt in a fresh0700nonce stage with diagnostic stdout separately bounded and opaque. No console-JSON or GC row repair is an accepted receipt route. The host wrapper must retain the envelope before parse, accept one production invocation only and preserve ambiguous stages without retry. The wrapper accepts one synchronized workflow, with a fresh digest-pinned readiness decision and exact device binding; it performs no UI operation itself. Native is the sole one-Left workflow producer. DQ binding checks execute before the20s observation clock starts, preserving DF loop timing; actual cycle counts and overruns are reported without promising80 successful cycles.

Full native binding audits are retained only if qualification refuses before any header; successful and late-failing traces carry compact bindingQualified instead, preserving the raw-fault/checkpoint budget. The three actual DQ guards execute unchanged, with full cached kernel-name and native link/follow/canonical device+inode checks; only the USB read-header/input-length adapter differs. Accepted traces do not retain full per-stage binding metadata. DO/DQ retain the private native binding evidence, and source verification pins the guards. This is not a claim that every individual target function was dynamically traced.

Private JSON serialization uses UnsafeRelaxedJsonEscaping to avoid expanding Base64'+' into HTML escapes; the receipt is parsed as JSON data and never embedded in HTML. Control/quote escaping remains valid JSON. ShortError preserves the first error's type/prefix with a128serialized-JSON-byte cap, replacing the old240-character bound that could expand sixfold. Stage/phase, actual counts and cleanup results remain explicit. Late errors never append large binding audits.
