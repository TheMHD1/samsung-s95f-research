# Independent EH implementation review

**PASS for the frozen bounded reader/checkpoint implementation, parser and wrapper; no blocking finding.** All37 inventory files and the regenerated deployment manifest match the final pins below. This is host qualification for the centrally coordinated finite observation; it does not claim successful ARM32 target execution, physical picture observation, a root cause, a fix, a safe hook/write, or active pointer/header identity. Only new `reviews/` artifacts were written. No TV, root-transport or network operations were performed.

| Frozen artifact | SHA-256 |
| --- | --- |
| Source inventory | `38ae37ba3e64c516d0e9aa5d2e811d7c6d85e0164f6a155e3bb93ff0990991fd` |
| Deployment manifest | `d0059b32e4e3d99a398a3763934e8927cd2967126c6d1ad9e76d8bf069f3059e` |
| Native managed DLL | `7ea168e30685a75e474774b0893f631d30fd28fea944f7360f62de25a461af19` |
| Wrapper | `4870a6a0c089a739e6bc8af4f3b9076dc73bc5cf21123a2a0b8305ef206dfc15` |
| Strict decoder | `1de2a8f769f4a801b85f2dff74bb840221e0394db8ec7acb9cffdd7a763d5229` |

## Native source and transport

The entire Program.cs equals frozen DP with only schema/default-budget/dry-metadata substitutions:20s→15s and80→60cycles. NativeBinding.cs and OnsetKey.cs are byte-identical. The Controller/window specifications and full Run/ReadPair/ReadSet remain unchanged, as independently checked both through whole-file comparison and the source verifier's bounded sections. The selected source reads remain R,M,C,P,N,H,L,R in the same order; no new header, arbitrary address, data write, key call, reset or retry was introduced.

Preallocated buffers precede IOps. Preflight/FD identity/revalidation/own usbfs binding checks precede the observation clock. The inherited ARM32 little-endian/native-layout ABI refusal and owned-FD release/close behavior remain intact. An exact accepted OUT header still obligates one exact matching IN even if a subsequent clock/deadline read fails. A short/throwing OUT or ambiguous/short IN leaves no permission for another header; subsequent cleanup does not retry or reset the protocol. A complete cycle alone adds a checkpoint. Partial transition/post-fault H/N context is preserved through the existing raw retention policy, not fabricated as a complete compact row.

The native production Config defaults are60maximum cycles,15,000,000us duration,250,000us nominal cadence and2s per bulk. Maximum accepted complete-loop/postfault totals are487headers and974bulks. Binding qualification is outside the observation interval. Neither implementation has a native process alarm; the15s observation is cooperative and the wrapper's root45s/host75s bounds do not prove termination of an uninterruptible target process or exactly60completed cycles. EH is a distinct shorter observation and must not be labeled DP's80cycle/20s experiment.

## Packed source bytes and decoder

ScoreCheckpointBuffer uses a preallocated60×54byte array. The original34byte construction is source-identical and each of the first60prefixes matches the frozen DP host golden fixture. The appended20bytes have the correct source/index/width:

| Compact offset | Exact source |
| --- | --- |
|34/36|M+2/M+4, two u16|
|38/40|M+0x22/M+0x24, two u16|
|42/44|**end-R**+0x60/+0x6e, two u16|
|46/50|P+4/P+8, two u32|

M is window1, P window3, end-R window7. CPU mirror/counter and pointer coordinates agree with reviewed EG. The builder retains little-endian raw bytes, not an inferred boolean, pointer dereference or historical branch. Host marker tests distinguish end-R from start-R and preserve upper pointer bytes. Independent tests additionally accept all-ones full-width values when the retained source and compact bytes agree, reject compact/source disagreement for every appended field, and verify changing start-R does not change the end-R-derived values. An unretained pointer word may legitimately be any u32; accepting it does not qualify an address, alias, header, epoch or active buffer.

The strict decoder requires the exact new schema,54byte records,count≤60,canonical Base64 and SHA-256, exact count×size extent and ordered H full-pair brackets within the accepted native interval. It projects only the additional schema/checkpoint/device/binding fields into the inherited synchronized parser. The underlying transport parser was narrowed from80/20s to60/15s and corresponding global-counter bounds; the synchronized key parser changes only its derived transport pin. The80cycle/20s projection is refused. Global counts and trigger-baseline duplicate semantics are preserved.

Each retained complete cycle is independently reassembled byte for byte, including all appended taps and H time offsets; duplicate retained references are not extra cycles. Discarded intermediate cycles remain compact native source samples without later full raw recomputation. Fields from earlier M/P and later end-R are sequential observations, with no common timestamp or compact per-field/R brackets. The interpretation explicitly rejects atomicity, every-call coverage, pointer/header/active-branch proof and physical observation.

The one-Left down/up action remains armed only after a full first clean cycle. The inherited parser requires valid dispatch/reap/exit/timing structure and USB-window overlap for trial qualification. Key calls still do not establish UI receipt, consumption or physical screen change. A captured zero refresh counter can miss the entire sequence at250ms cadence. EG's seed1 permits two qualifying boundary events without guaranteeing distinct top/bottom buffers; EH does not strengthen that source result into a historical observation.

## Receipt and orchestration bounds

The fixed exclusive0600 semantic receipt is opened inside a fresh owned0700 nonce stage before managed selftests or production Run. ARM O_NOFOLLOW spelling and receipt helpers are unchanged except the EH prefix and exact checkpoint-test count. Semantic JSON is separated from opaque diagnostic stdout; GC stdout is never line-filtered or repaired into JSON. Full binding audit is retained only on preheader refusal, with a compact success flag on long traces.

The native checkpoint selftest independently reports46checks and maximum serialized output24,249bytes; adding the publication newline gives **24,250**, leaving **326bytes** below24,576. The exercised adverse cases include the60thfull fault with retained baseline/last-clean/transition/postfault context, maximum19digit clocks, escaped/duplicated key errors and all14late postfault bulk exceptions. Partial first-cycle failures add no checkpoint. The bound relies on the fixed schemas/caps, bounded error strings, null omission and unchanged compact binding policy; any future native field/record-count change requires remeasurement before use. Host interpretation metadata is outside the native receipt.

The wrapper preserves dry default, exact local checkpoint/manifest validation, three payload names (94,874bytes), fresh private staging, chunk hashes, pinned boot/dotnet/root-adapter identities, exact stage inventories and immediate cached identity checks. Readiness schema is `eh-refresh-checkpoint-readiness-decision-v1`. It requires an explicit closed-world vendor-OUT lineage decision and bounded cached holder/binding metadata. Reference syntax/digests are checked locally; the coordinator must validate the referenced actual evidence before use. Cached absence is not continuous holder/queue proof.

The wrapper invokes production once, records inflight status before the call, saves the full envelope before semantic parsing, and only cleans the exact stage after accepted native parsing, post-census and final integrity. Malformed/ambiguous invocation, identity refusal or cleanup failure does not retry/recover and retains evidence. It performs no wrapper UI action. Native stdout≤16KiB,stderr≤2KiB,receipt≤24KiB and root response≤64KiB remain unchanged; the tested401shells per wrapper suite fit the8KiB command cap with maximum7806bytes. Oversized diagnostic selftest output would refuse before production rather than justify another invocation.

## Independent verification

Normal and optimized Python each pass43source checks,457decoder checks and1268wrapper checks. Decoder fixtures cover clean, complete transition and partial transition; independently cycle-coded fields and original34byte golden comparison pass. Wrapper cases cover readiness/identity races, one-shot invocation, timeout/partial/malformed/wrong-device/exit/stderr refusal, save-before-parse, stage cleanup failure and actual host-only exclusive selftest receipt creation/no overwrite. The exclusive fake selftest runs93observer,22key and46checkpoint checks with zero target operations.

`reviews/independent-checks.py` adds82checks in both modes: all37frozen files, exact manifest regeneration, full Program delta and byte-identical bindings/key source, full-width retained-field acceptance/mismatch rejection, distinct end-R source selection, intermediate pointer-word scope, exclusive-JSON refusal of diagnostic prefixes, and old80/20s/global-counter refusal. `reviews/independent-validation.json` records counts and exact pins. No further functional test expansion is required without a source change or unresolved finding.
