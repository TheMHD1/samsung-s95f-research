# DT actual clean reference baseline: independent offline replay

Both saved fixed-reference candidate windows in `DK/reference-baseline-01` are **exactly104 zero bytes**. The frozen strict DT parser accepts the receipt, and all14 saved raw files match their native and wrapper hashes. The capture reports14 headers/28 bulk transfers, ReadyForHeader, release/close, one native invocation, zero writes/retries/UI operations and stage removal. This replay makes no TV/root/network calls and changes no original capture or frozen source.

| Requested candidate | Bus address | Full OUT-start/IN-end bracket, µs | Raw SHA256 |
|---|---|---|---|
| Top | `0x47015354` | 179212120586–179212120655 | `39f37f8d1931b3bdf767e7510dd69509fbf23af1f7654933d0a4d291cbdd4418` |
| Bottom | `0x47016264` | 179212120669–179212120737 | same |

Each104-byte response contains102 bytes of complete12-bit packing:68 lanes568..635 plus2 ignored tail bytes. An independent contiguous-bitstream decoder agrees with the frozen parser's requested lanes570/571,622/623,624/625,632/633, allzero. This is a statement about these exact returned windows at this clean-baseline collection. It does not establish that whole fixed-reference buffers are zero or identify what the earlier fault compared.

Start/end R bytes match and decode stop/fault/gate `0/0/1`, alternate40 and mode1 record latch0. Start/end N bytes match with six zero ordinals and six zero current source counts. Context is aa0/ac2, C7=0, publication mirror200, xbase0, packed length2880, lanes1920 and root20010000. Sampled X/Y/RGB/Diff columns are allzero, while B contains nonzero data. Zero ordinals and cleared columns do not turn residual B into valid current records. The full paired-read span is **179212115342–179212120901 µs**, width5559µs. Sequential equality is not atomicity or a proof that no reset occurred between reads. No timed physical-light observation is present.

The initially suspected review-reference race was examined and **is not present in the retained readiness chain**:

- Actual saved readiness SHA256 is `a8761a8dbe6d80d79a7ee86675859ab89f5eb3bfdb461134bb86c6e6d3a073bd`; both saved record and result bind that digest.
- That readiness explicitly references **final** `reviews/independent-validation.json`, SHA256 `a09c5c3f913a263a326bc62d66309a63d2faf0ea3fbd06085a544ad7e8cbe4c4`. The file matches. All10 readiness evidence references match their current pinned bytes.
- Earlier review content is preserved separately as `reviews/independent-validation-initial.json`, SHA256 `2f095687a0ceff1c6df5970d53029d8a569434c5e656a6251c47b813fa8435d3`. Removing only final fields `sourceRangesVerified` and `sourceRangeEvidence`, then serializing sorted/indented JSON with a trailing newline, reproduces those earlier bytes exactly. All shared fields are unchanged. This reconstructs content, not a historical filesystem timestamp.
- The actual readiness bound the final version; the older hash was from a separate earlier metadata observation. There is no basis to label this capture provenance-rejected or to rehabilitate/rewrite its readiness. The present audit establishes consistency of retained artifacts rather than inventing a launch-time filesystem snapshot.

Frozen deployment manifest SHA256 is `ed1e1594f3dc23528c69894c21a19c214593a0ae12c0dd20ec5ceebc9fda4d80`. The captured reviewed manifest matches byte-for-byte. Every native/wrapper source and payload pin, the build checkpoint and frozen parser pin match. The parser is `85e6d0783dc0455d4002e6e0332e23eed15d7d8b21c5ece3b3443c5529428b47`; DLL is `746bccf900e4608af2606c0096a342948b320ff248b6cf8d01f5c5d535a69f6c`. The final review's seven selected-package source ranges are independently rehashed and match. This does not attest the complete live controller instruction image.

`analyze.py` verifies `input-pins.json`, replays the exact frozen parser without invoking any runner, compares14 raw outputs and the saved interpretation, independently decodes68 complete lanes per reference, checks original counters/context and validates the complete retained readiness/review/source chain. `decoded.json` contains exact brackets, all decoded values and the evidence-digest comparisons. No OEM binary is copied here.

Reproduce with `PYTHONDONTWRITEBYTECODE=1 python3 analyze.py --check` and `PYTHONDONTWRITEBYTECODE=1 python3 -O analyze.py --check`. Both modes pass148 explicit checks, including the exact decoded-artifact comparison; frozen parser validation also runs. `validation.json` records both runs, and `source-inventory.json` pins this additive analysis only. Original readiness, record, result and raw captures remain unchanged.
