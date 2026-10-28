# Bounded limit200 fault recovery review and additive guard

EW qualifies a recovery route for a future fixed40→200→40 experiment. It does not perform that experiment, recover a target, send a controller request or change the public repository. The additive `recover-eb200-fault.py` is ready for independent review. All original EI/EB/DV/DH and retained capture files remain unchanged.

The frozen EB reader already captures and interprets alternate limit200 without a source or target-read change. Its admission is packing/root/ordinary-mode context, not a fixed alternate-limit or clean-state requirement. The existing EI recovery coordinator instead requires byte-identical start/end256-byte R and exact `[stop=1,fault=0x1001,ordinaryGate=0,c4=40]`; it therefore cannot be reused unchanged for a200 fault. EW narrows a separate coordinator to the corresponding fixed200 tuple. It does not weaken the old40 path.

## Implemented boundary

The helper is dry by default. Explicit execution requires a retained absolute EB capture directory, separate caller-sealed SHA256 pins for the actual accepted `result.json` and original `record.json`, and a fresh absolute output directory. Those pins must be taken from the independently accepted actual200 capture, not from host fixtures. There is no arbitrary address, threshold, mode, USB device or restore option.

Before loading any operational recovery module, the validator checks:

- Frozen EB wrapper/parser and regenerated source/payload manifest, exact result schema/booleans/integer counts, one native invocation,16 headers/32 bulks and `STAGE_ABSENT`.
- Strict native parser acceptance, complete exact-pair phase history, ReadyForHeader, successful release/close, fixed16-window raw byte/hash inventories and saved-file equality.
- Readiness hash, same native/readiness device and pinned evidence; both original selftest/native envelopes, receipt/stdout/stderr bytes and original terminal records. Diagnostic stdout is not a semantic receipt.
- The sealed original28-call record's completed authenticated response envelopes, command/count bounds, exact saved native envelopes, final cleanup response and pre/before/post cached census receipts. This is envelope/byte/record binding; EW does not claim to regenerate every original shell command or prove continuous queue ownership.
- Exact equality of the full start/end R blocks and the stable fixed200 fault tuple. Thermal/echo drift can cause this deliberately strict guard to refuse even if the four fault fields agree; no automatic relaxation or recapture follows.

The execution body retains EI's same cached snapshot, optional one Right from cached Live, ordinary `apps_gate`, public reject gates and one unchanged DH MODE2 helper. Their exact source hashes are enforced. Public gates require upgrade idle, lcdon, screen-state1 and burn-in activity0; these are reject signals, not optical or global maintenance proofs. Navigation failure or a failed public gate yields zero MODE2 attempts. There is no hidden owner-confirmation gate in these functions; old prose requesting a later physical observation is not a prerequisite to automatic software classification.

The stock helper retains operation41/mode2, `/dev/tztv_tcon`, ARM32/root/ABI and stock lifecycle checks, a process-only12s SIGALRM, root45s/host75s bounds, one request and strict exclusive receipt/framing/cleanup. Return0 is **kernel_return_zero_only**, not power-action acknowledgement. Signal delivery can be deferred in uninterruptible kernel sleep. A wrapper attempt is recorded separately from a verified one-request success: failure after entering the helper leaves invocation count unknown and cannot authorize retry. There is no threshold write, automatic DV restore, EB read or USB discovery inside EW after MODE2.

## Concrete coordinator route

1. Admit the write/observation only from a fresh fully guarded DV context and closed-world protocol lineage. The last retained USB63 clean validation is not sufficient: it has AA0/AC1, R20=3200, Rbc=3138 and temperature23; frozen DV's restrictive modeled endpoint and AA0/AC2 guards independently refuse it. Operating-mode4 is not the category field. Ordinary Apps/header preparation followed by fresh guards may produce an admissible context; it must be observed, not assumed.
2. If the fixed200 observation faults, preserve its original result. Only a positively classified ReadyForHeader terminal state, completed pending obligations, released/closed ownership and centrally established no-intervening-vendor lineage permit the separate unchanged EB read. Bind the accepted EB200 capture and cleanup to the same current instance. A refused initial-fault ER result is not itself promoted to an accepted onset.
3. Run the EW stable200 guard against that exact accepted EB capture. Independently qualify current same-boot/instance metadata, no holders/unbound interface and the coordinator phase ledger immediately before operational recovery. Captured hashes and cached metadata are snapshots; EW cannot prove an external client remained absent. If saver/navigation prevents Apps qualification, stop with zero MODE2; separate reviewed ordinary preparation may establish a new positive cached Apps state. Do not loop or blindly replay a key.
4. With cached Apps and public gates accepted, attempt exactly one unchanged stock MODE2. Retain its original final result, native/frame/cleanup receipt and any refusal. Do not promote the stock `root.json accepted=false` initial placeholder into a final rejection or rewrite it as success; inspect the separately validated final receipt/result.
5. After successful return, establish positive old/new USB identity and same-Linux-boot proof using new ordinary metadata. A positive disconnect/enumeration and new instance are required; no assumption of code reload, c4 reset, all-RAM clearing or repaired parser follows. Form fresh EB readiness and retain a separate read/cleanup.
6. Branch only on that fresh observation and full writer admission:

| Fresh result | Allowed next bounded step |
|---|---|
| Clean0/0/1 and c4=40 | Report observed40; no restoration write is needed or attributed. |
| Clean0/0/1 and c4=200, full DV callbacks/root/geometry/AA0/AC2/scan1/model/thermal/selector guards pass | A separate parent-reviewed DV restore200→40 may run once; require complete write transport, full guarded readback40 and cleanup. EW never launches it. |
| Clean200 but any DV context/profile/scan/model guard fails | Do not write. Retain200 as observed; ordinary reviewed preparation plus a newly qualified read may be considered separately. No automatic retry, mode substitution or guard weakening. |
| Faulted, Quiescent, unexpected c4, missing identity or any semantic refusal | Stop; no blind restore or second MODE2. Preserve the exact outcome for central reconciliation. |
| Unknown/ambiguous USB phase or unresolved pending transfer | No further OUT/header of any kind and no automatic reset/MODE2; release/close does not repair phase. No independent tool may silently issue a read or restore. |

MODE2 at a classified known phase is a different action from trying to repair an ambiguous parser phase. The documented risk is runtime diagnostic/restoration uncertainty, not an established boot/network/code corruption mechanism. Existing finite DV writes address one low-SRAM halfword and do not expose persistent/high-bank/POFLG routes. This distinction does not waive protocol ambiguity, guarantee electrical behavior or establish a general safe protection bypass.

## Host qualification and limits

`test-recovery.py` constructs a clearly labeled **synthetic200** fixture by adapting retained EB validation bytes in task-private temporary storage. It is not an actual200 result. It checks fixed200 admission, wrong40 rejection, full-R drift, native Unknown/release/close/count failures, duplicate/nonfinite JSON, result/raw/envelope/record/digest/symlink corruption, gate/contract/adapter failures with zero MODE2, exact one injected helper success and ambiguous helper failure without retry. Injected modules have no target binding. Normal and optimized Python produce37 checks/28 malformed refusals each. The dry CLI performs zero target/root/network operations.

Reproduce host tests with `PYTHONDONTWRITEBYTECODE=1 python3 -B test-recovery.py` and `python3 -B -O test-recovery.py`. Actual EB source/payload files and retained private qualification inputs are required in the original sibling layout; this is not a standalone arbitrary-device tool. No native code or OEM firmware is executed by this test. `source-inventory.json` seals source, this plan and validation records; `input-pins.json` binds original sources and the retained63 baseline privately. Independent review and parent-only target coordination remain required before any invocation. No prevention, physical-output or completed200 recovery claim is made.
