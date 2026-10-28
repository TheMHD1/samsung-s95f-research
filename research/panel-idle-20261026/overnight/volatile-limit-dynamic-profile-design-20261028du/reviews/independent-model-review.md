# Independent DU source-model review

**PASS for the frozen pure model and its deliberately restrictive mode1 admission policy. No blocking model defect found. This is not native-writer deployment clearance.** I did not author DU and changed none of its frozen sources, validation or inventory. Review was local/read-only apart from this additive report; no TV/root/network/OEM execution occurred.

Reviewed inventory SHA256: `d09e0f7486ec7c4d3f8a3095b9374198d33504124592e01858ba140c0e9ef22c`. Model SHA256: `7a1c2d9b9f5cc5d9136166b79be7ba16d639d18c7d92450b546db8476b3f937a`. README `ae8fec4f78954c8b615fbbff6a21a4a23e2afa35ae8a1fb16bef543c452c8ee2`; tests `54da19200ef11fb5eb420a775cff482225df4438a9b004da8ecc683a533f357e`; validation `6217d916c31373361e871b7663542959dec9434135b1190431630deca5d0b086`. All inventory files, retained input references, selected-package identity and six declared image0 source ranges matched. Source conclusions are conditional on the selected-code/runtime-layout binding, not whole executing-image attestation.

## Source math and widths

I independently disassembled the selected image0 function0x389d0, both documented callers, the getter, and the echo sender/receiver. At389f6 the reference is LDRH, converted unsigned to float32, multiplied by the exact1/16 literal and converted unsigned with truncation, then UXTH. Runtime input from getter27670(1) follows the same unsigned conversion; the getter uses LDRH. Unsigned inputs0..65535 are exactly representable in float32 and multiplication by this binary power of two is exact here. Integer division by16 therefore reproduces the0..4095 scaled result. Only the reference is replaced with25 when above4000. The runtime mirror is not given that fallback. No calibrated physical-temperature units are established.

Three LDRH samples are summed, unsigned-divided by48 and truncated to16bits to form the base. DU pins the observed base2075/reference24, rather than guessing the unobserved three samples. Image0 VA38a64/38a6a/38a70 implement SUB/MLA/MUL at32bits. UBFX38a72 extracts bits7..22 into a zero-extended16-bit candidate. The subsequent signed CMP/branches receive nonnegative zero-extended candidate/cap/floor values, so DU's ordinary integer comparisons are correct for this domain. It preserves cap-before-floor order, including the source's behavior for a generic floor greater than cap.

The independent reference calculation used an arbitrary-precision signed polynomial followed by floor division and modulo:

`candidate = (((base + coefficient*(T-reference))*scale) //128) %65536`.

This selects the same bits7..22 without repeating DU's intermediate wrap implementation. I checked all4096 admitted temperatures and10000 deterministic generic u16 operand tuples, including negative subtraction and wide products. Outputs24→3161 and25→3183 agree. These results validate the arithmetic model, not endpoint monotonicity over the whole domain or protection safety.

## Selective refresh and M mirror

Image0 caller21576..215ac chooses ordinary parameters with selector0 or alternate parameters with selector1. Caller3af16..3af42 chooses alternate. The callee stores only ordinary R+0x20 or alternate R+0xbc, then stores shared diagnostic base/reference/runtime into94/96/98. **It does not atomically refresh both endpoints.** The retained mode6 counterexample (ordinary3200, alternate3161, diagnostic24) is therefore material and correctly rejected by the restrictive admission rule. It must not be called corrupt merely because both endpoints fail one shared prediction.

For the required aa0/ac2 ordinary mode1 path, image1 bddc..bde4 loads root+0x2420 and stores it through literalCPU0x200004c6. That is **M+0x26, decimal38**, not the directional-threshold field at decimal26. Alternate bdaa..bdb2 loads root+0x24bc to that same mirror. DU requires aa0/ac2 and M+0x26 equal the validated ordinary R+0x20. This replaces only DQ's old exact3183 comparison. It correctly keeps the remaining context restrictions. It is a sequential agreement test, not proof that M and R were sampled atomically or that no mode transition occurred between them.

DU's requirement that *both* endpoints match the same diagnostic model is conservative admission. It can reject legitimate selectively refreshed or initialization states. Equal initial/fresh/readback thermal tuples establish sampled stability only; they cannot exclude an unobserved change-and-return or an update after the fresh check. The native derivative must retain that distinction and may not relax the model to a wildcard when it refuses.

## Echo and preservation of other guards

The sender9978..9986 loads the low byte, increments, zero-extends8bits, and maps255 to0; the duplicated request bytes are stored at998a/998c. Receiver9838..984c verifies duplicate bytes and STRH-writes the zero-extended byte. DU's high-byte-zero, low-byte0..254 domain admits the own sender's wrap without assuming a particular number of exchanges. A matching duplicated255 could enter through another accepted receive input, but the identified own sender does not generate it; rejecting255 is conservative.

The only newly modeled halfwords are20/98/bc and bounded echoac. Every other nonhistorical DQ profile byte remains exact, including base/reference, both parameter sets, lower bound, gates/latches, normal thresholds200 and unknown high byte atcb. Existing historical exclusions remain the same. The selectorca retains its0/1 domain and stability requirement. There is no newly caller-selected address, value, geometry or mode.

`validate_candidate_r` and `validate_candidate_context` are compositional guards, not independent proof of transport or one coherent epoch. `validate_transaction_pair` permits an unchanged expected limit for baseline→fresh validation; it does not authorize an action by itself. The native caller must still select only the fixed40→200 or separate200→40 action and run all original callback/binding/phase/deadline/readback/receipt/cleanup checks. I will review that composition separately in DV.

## Independent host validation

Normal and optimized Python each passed:

- **14383 additional explicit checks**, covering pinned files/ranges, independent arithmetic, cap/floor ordering, reference fallback boundaries, fresh actual mode1 admission, mutation refusal for every remaining exact profile byte, bounded echo wrap and255/high-byte rejection, valid synthetic endpoint tuples across representative temperatures, thermal changes within a pair, each individually stale endpoint, the actual mode6 counterexample, and exact ordinary/alternate mirror load/literal anchors.
- DU's **135452 original checks**, executed with only its deterministic validation-file write intercepted and compared byte-for-byte against the frozen file. The requested bytes were identical; no frozen validation file was rewritten. Both runs reproduced validation SHA256 `6217d916c31373361e871b7663542959dec9434135b1190431630deca5d0b086`.

Fresh actual `DK/admission-clean-01` start/end R bytes are equal and independently pass DU's full R/context composition: mode1 aa0/ac2, scan1, C7=0, ordinary/alternate3161, diagnostic24, echo0 and M upper3161. Pins: R `ed7b953417afc9932e1b270c9c12d2aace2be18b9a3c7cffc1f05975309338aa`; M `32e547d3329930357f47f9312fba936335bddf3c6e07bd9c6e916a6c9856bc27`; C `c9bc21efabc33dc5c687f230ecf321722552c99518957cc37b833c7aaaf9c2b0`. This demonstrates an available admitted state, not future target clearance or a native write.

## Refusal, restoration and finite-plan obligations

Thermal or echo activity can race a write/readback. If a model or stability guard refuses **after** a matched write, it must not erase writeAttempted, writeTransportComplete, limitMayHaveChanged, raw readback or native phase/ownership evidence. Positive header-ready state can permit a separately reviewed later action; an ambiguous phase prohibits further headers. No automatic reverse write or retry follows a refusal. A separate restore may legitimately begin at a different valid temperature tuple from the set invocation.

I also read `DK/experiment-plan-v6.md`. Its set→qualified DP observer→separate restore sequence preserves the necessary distinctions: no observation before accepted set; known-phase/lifecycle completion before further operations; fault records before recovery; no assumption that reinitialization restores40; explicit reconciliation after a clean prewrite restore refusal; and no blind reset/new header after phase or ownership ambiguity. The native writer must not implement the plan's separately reviewed operational fallback implicitly. A finite200 exposure also changes publication capacity; even a clean result would not isolate a pure comparator change or establish a physical repair.

No model-level revision is required before reviewing the frozen DV implementation. Native writer, strict parser, receipt and wrapper integration remain separate review obligations.
