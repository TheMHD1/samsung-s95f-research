# Stock fault-event logging option, 2026-10-28

The smallest source-backed way to add an actual setter-event record to a future ER-style sequence is the **existing image1 gated stock formatter**, owned by the same finite native process that performs observation and the one Left. This needs a new combined, independently reviewed helper. Neither the historical gate helper nor ER can be composed unchanged to achieve that ownership. No helper is implemented here and no target operation was performed.

The route is concrete: historical G/V6 recorded two `rtp_act_736` lines together with the ordinary fault field changing from0 to0x1001, then restored the volatile logging flag to0. F's earlier control recorded only `t[10]` during its three-second interval; that control was outside a retained fault transition. The new audit pins both receipts and their raw snapshots. It makes no claim that a new ES incident has already been logged or that event736 caused physical darkness.

## What this adds to ER

ER's fixed samples identify a software state transition and retain sampled H/count/reference/control fields. They do not record the event argument passed to the common setter. A newly appended, correctly delimited event736 pair would distinguish the stock setter's event code from an unexplained fault-field observation and place its text after any earlier retained detailed rows. It would also capture the stock formatted B/difference tuples that pass the formatter's own additional gates.

It still would not give the live r7/fp comparison operands, final selected A pointer, executing PC/LR, electrical producer, historical packed-record epoch, instruction timestamp, key consumption, or emitted light. Two lines are the expected result of **one setter calling the sink twice**, not evidence of two faults. The common setter accepts an argument; a different `rtp_act_N` must be reported honestly. Event736 alone does not prove which upstream caller ran.

Source chains use selected package SHA256 `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`, image1 FILE=linked VA+0x40200. All addresses below are explicit domains, not guessed aliases.

| Source anchor | Positive result | Limit |
| --- | --- | --- |
| image1 VA202a..203e | `r7 > fp` tail calls1c0c8, loads736 and calls c1e0 | live operands/caller execution unknown |
| c1e0..c214 | sets root2400=1,240e=0,240a=1001; c206 and c20e call1b8c8 with same event and literal c214 | no timestamp or PC stored |
| 1b8d6..1b8e2 | reads low byte of root2406 and tests bit0; zero skips formatting and ring writes | gate is separate from ordinary comparison gate root240e |
| 1b8c8..1b948 | formatter uses a0x1040-byte stack frame, scratch sp+40; appends bytes to ring | formatter maximum/cost and interrupt safety not newly proved |
| c638;19aa6 | detailed RTP rows and `t[]` call the same sink | no event-only filtering control is qualified |
| 183d8..183f4 /18548..18558 | stock code saves bit0, sets it, then restores saved bit while preserving upper15 bits | can race an external owner |
| 1ba54..1ba74 /1baa6..1baba | second stock save/set/restore sequence | no complete computed/DMA/cross-core writer exclusion |

Exact range hashes, input hashes and positive BL targets are in source-audit.json. The wider documented sink slice1b8c8..1b940 hashes47abdf79...; this audit additionally pins the128-byte range through its ring literal. The setter range here includes its final POP; historical52/50-byte conventions are explicitly separate slice boundaries, not conflicting package identities.

## Fixed gate, ring and wire contract

The root getter38fc uses CPU pointer slot200004e0. Retained initialization and prior coherent captures bind root20010000; root2406 is CPU20012406, DMA bus47012406. The gate halfword is **not** root240e (ordinary gate), root24c4 (limit), or any persistent/high-bank object.

| Operation | Exact historical header/payload | Meaning |
| --- | --- | --- |
| containing RT64 read | `010100000024014740000000` | family1 read target101, bus47012400,64bytes |
| logger arm | `020100000624014702000000`, then `0100` | target102, bus47012406,2-byte OUT payload |
| logger restore | same header, then `0000` | exact original-zero halfword, only with proven ownership/context/phase |
| ring read | `01010000000020200C3C0000` | target101, direct20200000,15372bytes |

Every read is one12-byte OUT and its exact IN. Each write is one12-byte OUT plus exactly2-byte OUT, **no IN acknowledgement**. Only a subsequent containing read establishes the observed flag value. The payload must complete once its exact header is accepted; no clock/deadline check may abandon a pending IN or payload. Short/error/exception/ambiguous counts make the protocol Unknown; no new header, retry, restore packet, UI/reset or fallback then follows automatically. Release/close does not repair parser phase.

The protocol's device-side OUT DMA capacity rounds a2-byte payload to512bytes. The future owner must have fixed2-byte buffers, one claim/FD, exact counts and no other USB client. Historical transport success is evidence for this exact2-byte gate address, not a general write primitive.

The ring is **direct20200000**, not47200000: header DWORDs at0/4/8 and15360-byte data at+12. CPU mapper3084 excludes addresses>=20200000, and the family1 header supplies the DMA address unchanged. Prior F/G captured this exact15372-byte read successfully. The sink writes the first DWORD and sets+8; this audit does not assign sole ownership of the second DWORD or flag clearing to a newly inferred consumer. F/G observed equal cursors and flag0 despite the sink's set-to1 path, so asynchronous stock activity must remain possible.

Each appended byte reduces write index modulo15360, writes one byte, then advances it;15360 is a valid transient/persisted end index before the next reduction. A whole-lap count is not retained. Equal or increasing endpoint cursors do not prove that the ring did not wrap one or several times. Do not clear ring data, indices, consumer cursor or flags to simplify interpretation. A read snapshot can race a producer/consumer and is not atomic.

## Historical proof and why existing helpers cannot span ER

F's accepted source used Hold3000ms, arm-deadline10000ms, whole-deadline20000ms. Its16 exact bulks observed gate0→1→0, identical pre/restored RT, ring5→11 and six bytes `t[10]\n`. G/V6 used Hold20000ms, arm-deadline30000ms, whole-deadline45000ms. Its16 exact bulks observed0→1→0 and ring143→1899,1756retained span bytes,31detailed rows plus the paired event736. The native G/V6 outcome was accepted, released and closed; host orchestration qualification and earlier rejected attempts are separate history.

Both helpers **claim interface2, arm, hold without USB, restore/read back, fetch ring, release and close**. Thus:

- F/G then ER: the gate is already restored when ER begins.
- ER then F/G: any new arm occurs after the incident and cannot retrospectively record the setter.
- F/G concurrently with ER: violates the single USB owner/claim and phase-lineage contract. A READY marker means the logger is armed; it does not release ownership.
- Altering F/G to exit while armed: removes its finite restoration guarantee and needs a new ownership protocol; not the minimal proposed route.

G's fixed historical boot/device handling and old CLR/stdout output path are not a current deployment candidate. Its JSON was printed to Console with a55000-byte cap. Do not copy that framing into modern ER; the exclusive-receipt GC fix and modern cached descriptor/GETDRIVER/native inode checks must remain.

A separately qualified **read-only postfault ring snapshot** is a smaller preliminary observation if the coordinator wants existing text without changing the gate. Historical F/G qualifies this fixed address/length class, not a new current helper. Without a fresh preincident baseline and gate history, any matching event could be old or stock-temporarily-enabled output; that snapshot cannot retrospectively establish ES event provenance. It does not replace a prospectively armed trial.

## Minimal combined-owner plan to qualify next

This is a finite design, not approval of an unbuilt helper. Derive from frozen ER's actual binding, read-pair completion, exclusive receipts and one-key workflow; reuse only the old fixed gate/ring contract.

1. Keep the centrally supplied same-boot/device/descriptor/config/phase-lineage readiness and modern single FD/claim validation. Preallocate ring buffers and exclusive output files before any arm. Revalidate current selected-code premise; historical V6 proves old execution behavior, and sampled code fingerprints prove only their sampled bytes. If new source attestation is required, propose bounded fingerprints of c1e0/52 and1b8c8/128 via the source-backed46000000 code bank, separately qualified; do not claim those have already been captured in full.
2. Read the baseline ring while the logging gate is observed off. Immediately read the containing current R block and require **exact gate halfword0**, a full Clean initial triplet, limit40, correct root/source context and modern ready phase. Preserve original bytes. Any nonzero upper bit refuses this fixed0→1 contract; no ad-hoc mask or erase.
3. Send the exact arm pair once, then a complete R read proving halfword1. Do not emit Left if that fails. Begin the bounded ER observation only after an armed **full Clean** initial read-set. Keep exact Clean/Quiescent/Faulted classifications; logger1 is not ordinary-gate1. Each already-read R can retain the logging flag, distinguishing observed1/off/drift without adding reads. A sampled1 does not prove continuous enable between samples.
4. Execute the existing one Left and58-byte checkpoint schedule for at most2s/56cycles, ending on the existing fault/postcontext policy. Added stock formatting changes timing/workload; compare to the prior unlogged trial as a measurement intervention, not an identical replicate. No extra code hooks, event injection or protection changes.
5. At a positively HeaderReady boundary, take one fresh R read **before restoration**. Require observed current full gate1 with original upper bits0 and same device/root context. Ordinary fault1/1001/gate0 or Quiescent0/0/0 must not forbid logger cleanup: those are intended observation outcomes. Legitimate selector, publication count, row, temperature and RT-fault changes are not an excuse to overwrite unrelated state. If the logging halfword has upper-bit drift, new unexpected context, or Unknown transfer phase, refuse a blind0000 write and retain a may-remain-changed outcome for central reconciliation. Gate already0 is a separately reported observed-off condition, not evidence that our restore write occurred.
6. When admitted, send fixed restore pair and read fresh R proving complete logger halfword0. Then read post ring, release/close, save all raw artifacts; stage cleanup only after strict accepted restoration/terminal proof and all output retention. A fault does not justify rewriting the whole R block or restoring historical fault bytes. No stockMODE2/reset while ownership or protocol state remains unresolved.

Normal completion must reserve restoration and final-read capacity **before arm and before every new optional observation cycle**. Per-bulk timeout remains2s. The conservative fixed addition is **eight pairs/16bulks**: baseline ring; pre-arm R; arm write; dedicated armed R; fresh pre-restore R; restore write; restored R; post ring. Existing ER headers/bulks remain separately counted. Using ER's initial R as the armed readback could remove one pair only after proving the gate/fullClean checks run before the rest of that set/key; the default here does not borrow it. Final ER R cannot serve fresh pre-restore R when postfault context reads intervene.

The conservative addition alone can consume32s at2s per bulk. Do not append it and assume ER's existing root45s timeout suffices in every late case: the pending ER cycle/postfault tail also has a bounded cost. A new implementation must prove a whole-operation budget, stop starting optional cycles while restoration reserve remains, and preserve the no-header-after-ambiguity rule. A service-time measurement is not a worst-case timeout proof. There is no guarantee of rollback after process death, device loss or hung runtime. A hard kill while armed is not a safe substitute for bounded restoration; watchdog/process-timeout policy needs explicit separate review. No larger deadline is silently authorized as a qualified implementation by this source design.

## Output, timing and acceptance constraints

Two ring snapshots are30744raw bytes/40992base64 bytes. ER's largest receipt24302bytes needs32404base64 bytes. Their sum73396 already exceeds the65536root response cap, before framing/stdout/stderr. ER's current24KiB structured receipt has274bytes margin; adding ring data, step metadata or error paths without a new size proof is invalid.

Use two fixed exclusive0600 binary sidecars in the0700 stage, maximum15372bytes each, with no arbitrary output paths. Keep native GC stdout opaque/separate. Fetch each ring through a separately bounded ordinary-file envelope only after native terminal status; retain size/hash and exact manifest inventory. This fetch is ordinary target file I/O, not another controller transaction, but must be included in the new runner and cleanup contract. A new compact receipt should hash-bind the ring sidecars and include full gate-write/readback timestamps/phase/status; if56checkpoint capacity no longer fits all late failures, preregister a smaller finite cap rather than silently truncate evidence or raise the cap. This report does not assert a size bound for unbuilt code.

Keep host monotonic before/after brackets around every header/data pair and arm/restore payload. There are no timestamps in event text. A new event pair is bounded by the observed armed interval/postring capture, conditional on ring provenance/freshness and no overwritten/lapped history; it cannot be assigned to a particular25ms checkpoint from text order alone. An absent pair does not prove setter absence: gate races, wrap, incomplete terminal capture, formatted-record gates and source-identity uncertainty remain. A partial/overwritten text record must not be promoted to an exact event.

Acceptance fields must separate transport/pending-phase, arm readback, observed gate continuity samples, restore transport, exact restore readback, ring retention, native cleanup, UI dispatch return, event text match and physical observation. Missing restoration or ambiguous phase leaves stage/evidence retained and no automatic subsequent controller request. The proposed observer cannot prove physical light or repair.

## Reproduction and freeze scope

`python3 -B audit.py` and `python3 -B -O audit.py` are standard-library, read-only checks of29pinned inputs, eight exact selected-source ranges, BL targets, old fixed packets/deadlines,16exact historical bulks per run and ring/event deltas.124checks pass with identical output. source-audit.json is that output; source-inventory.json freezes this workstream only. No OEM code bytes are copied here.

The existing G `verify-rtp-act-736-trace.py` passed normal/-O. The F frozen reviewed-helper copy of `verify-secondary-event-log-buffer.py` has a snapshot-relative path that does not locate the package when invoked there. It was left unchanged; the byte-identical canonical `managed-usb-secondary-logger-smoke/verify-secondary-event-log-buffer.py` passed normal/-O with the retained local Capstone. This is a reproduction-location limitation, not a source or target change. validation.json records those checks.

No current live gate value, continuous writer exclusion, event-only filter, new combined helper, new output/deadline qualification or deployment is claimed. Persisted/high-bank/POFLG routes remain excluded.
