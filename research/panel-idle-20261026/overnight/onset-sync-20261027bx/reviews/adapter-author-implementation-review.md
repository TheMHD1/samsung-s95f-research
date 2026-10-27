# Independent implementation review by SWU adapter author

Reviewed 2026-10-27T23:29:27.837881+00:00. Scope: `Program.cs`, `OnsetKey.cs`, `SynchronizedOnset.csproj`, and the supplied host-runnable assembly. No TV operation, native USB operation, normal-key utility invocation, deployment or firmware change occurred. The only write by this reviewer in this tree is this review file. Other implementation and review artifacts were not changed.

**No material defect was found in the reviewed success-path concurrency, transaction cleanup, fixed command scope or temporal evidence recording.** This is an implementation review plus host tests, not evidence that the target UI received a key or that a physical picture transition occurred.

## Exact reviewed inputs

| Input | Bytes | SHA-256 |
|---|---:|---|
| `Program.cs` | 47260 | `1c044c0fe514c823b992b00a797abd4e067df8f2dcf6b8d85c352c8f3170e86f` |
| `OnsetKey.cs` | 13199 | `af6a7d3e495f8e2422d333faa98bad899115960a0dbbb4979e456b85c6ced510` |
| `SynchronizedOnset.csproj` | 353 | `05893d224110307cdce9838c9620aba3ed1326901288ad105279cfc9eed3f187` |
| `bin/Release/net6.0/SynchronizedOnset.dll` | 67072 | `9989c9e44edb99d59cc36459c2bf5e4f4ec34c540631415f43416d4076a11eb8` |
| `bin/Release/net6.0/SynchronizedOnset.deps.json` | 421 | `0eaa049e2815d0650d76f204906209d181c9e71fd7637547693f3fa6069fe5bb` |
| `bin/Release/net6.0/SynchronizedOnset.runtimeconfig.json` | 242 | `aeb46a15366e38511c192ccf65312442c64e8753b3c16fd2ca0b4cb34a5c59f3` |

The two test entry points were executed against the supplied assembly using the existing .NET 6 host runtime, not a separately rebuilt assembly. Source and assembly hashes are recorded above; the parent's deterministic build manifest should bind the final deployed assembly to these source inputs.

Commands, both exit 0:

```text
${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet bin/Release/net6.0/SynchronizedOnset.dll --self-test
{"selfTestsPassed":75,"targetOperations":0,"maxTestOutputBytes":10541}
${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet bin/Release/net6.0/SynchronizedOnset.dll --key-self-test
{"keyTestsPassed":22,"targetOperations":0,"maxTestOutputBytes":14476}
```

## Concurrency and cleanup findings

- `OneLeft.Start` marks its one-shot attempt before thread scheduling, and runs down/hold/up on a dedicated background thread. The sampling loop starts that worker only after the first complete R/M/C/H/L/R cycle is clean at both R endpoints, freezes that trigger baseline, and proceeds without joining the key worker. It does not move key child waiting onto the USB loop.
- The two `BlockingKeyOps` tests use actual thread synchronization: the down call stays blocked until later USB transfers release it. At least ten following USB transfers occur while it remains pending, including a fault scenario whose onset data is retained. These are meaningful scheduling tests beyond an immediately returning fake key.
- `OneLeft.Work` always attempts up in a finally after entering the down/hold operation. Down-call errors, hold errors and timestamp errors do not suppress that release attempt. A failed scheduling attempt cannot be retried by the main loop. The recorded call pair is fixed to Left down/up; child output drains with fixed buffers and count caps rather than growing retained strings.
- On the success path, `Finish` joins the worker before the intervention state is serialized. A successful `Thread.Join` reconciles worker writes before the caller reads the state. USB release/close happen before that join, so a key worker cannot hold a claimed USB interface merely by finishing late.
- `ReadPair` marks phase unknown around transfers. Once a complete OUT header is accepted, it attempts exactly the corresponding IN even if a timestamp/deadline check fails in between. A short/failed header or input stops subsequent traffic; pending/unknown phase cannot be classified accepted. Fixed response storage and DTO prefix clamping prevent over-read while preserving abnormal returned counts.
- Cleanup attempts release after a successful claim and close after a successful open on ordinary failure paths, preserving failures in the acceptance decision. The intervention's final reconciliation is attempted after USB cleanup. Acceptance requires successful observation cleanup plus, in Main, a completed intervention without intervention errors.
- The largest tested intervention transition serializes to 14,476 bytes under the 24,576-byte output limit. The program rejects an oversized result before printing it. The current retention design keeps a trigger baseline, last-clean, transition and one post-fault set as applicable, with current partial data retained on failure.

## Temporal qualification and limits

`OnsetObserved` identifies a sampled RT clean-to-fault observation. It is not a causal statement about the Left action. A background worker can begin its actual key child call after it was armed; a fault can occur before that call begins. Compare each retained transfer's before/after interval with the key call intervals. The action's armed time alone is insufficient. `UiReceiptObserved` and `PhysicalPictureObserved` correctly remain false; successful utility exit is not evidence of either event.

R bracketing and sequential windows supply interval evidence, not one atomic snapshot of all windows or proof that RT remained continuously clean between samples. A no-transition result is bounded by the 20-second/80-cycle observation and its gaps. Child completion, exact 150 ms hold scheduling, UI receipt and physical onset remain target observations to measure, not host-test conclusions.

A 7-second join timeout rejects the run. In that failure case the worker may still exist, its diagnostic fields can still change, and key release cannot be guaranteed; those fields must not be treated as a reconciled successful action. Likewise a blocked native USB/process operation, forced termination or target crash can defeat ordinary finally cleanup. These are limits of the rejected/indeterminate outcome, not a successful cleanup guarantee. Keep the parent's finite outer process/transport timeout and do not automatically repeat a failed intervention.

The fixed native USB ABI, descriptors/interface identity, runtime/utility hashes and source/binary pins still need the parent's existing deployment preflight. This review introduces no new TV action or permission request and does not authorize broad memory commands, power changes or firmware operations.
