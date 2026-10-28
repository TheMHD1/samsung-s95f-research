# Selected RTP predicate: executable host oracle

This is a host-only execution model of the selected controller's actual Thumb instructions, rather than another translation of the predicate. It adds a reusable way to test accumulation/threshold semantics before a target change. It installs no TV instruction hook, logger, code patch or firmware change. It does not identify the live operands of a past blackout or establish a permanent fix.

The selected package is SHA256 `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`, with image1 bytes at package offset VA+0x40200. The script verifies the whole package before its test run and maps the selected bytes only into a host Unicorn 2.1.4 Cortex-M4/Thumb instance. No OEM bytes are redistributed in this directory's authored analysis. The private tools directory contains the separately acquired emulator distribution, not a TV executable payload.

## Real instructions and explicit substitutions

The main entry is image1 VA0x1e68, started in Thumb state at0x1e69. VA0x1e46 is the called q-filter helper, not the main entry. The strict executed-address allowlist covers the q filter and predicate through the full four-byte return instruction at0x203e (exclusive end0x2042), the actual context/root getters, and the common setter at0xc1e0 through its return at0xc212. Any attempted execution outside those ranges or the five explicit substitutions fails. The register/stack return is checked; each run is limited to1,000 instructions and a one-second emulator timeout. No cycle-accurate timing, exceptions, DMA, other core or panel model is claimed.

Five functions are deliberately substituted with bounded host callbacks:

- 0x35a4: reports ordinary-gate availability0. All supplied cases start with ordinary gate1; this is not a model of a stalled/live wait.
- 0xc8a0 and0xca10: return a caller-supplied T. Their lane-array processing and counter side effects are not executed.
- 0x1c0c8: records mode/action4 and returns without any hardware action.
- 0x1b8c8: records formatter arguments and returns without ring writes, stack formatting cost or stock gate behavior.

The common setter's actual instructions perform the stop=1, ordinary gate=0 and fault=0x1001 stores. Its two actual BL instructions reach the formatter substitute with event736. Thus the run distinguishes one setter entry from its two logging calls without representing those callbacks as actual produced ring text.

## Qualified cases

The initial corpus has1,000 controlled cases: modes1..6, selector values0/1/2/255, threshold equal/below/above boundaries, low16 truncation,32-bit accumulator wrap, q values0..31, all six q-skip values, source-count event boundaries, non-admitted aggregate gates, history shifts and both T-call choices. It compares the executed instructions against an independent small arithmetic model and checks preserved callee-saved registers/SP. The corpus does not cover every integer combination or all hardware/race behavior.

A further four **counterfactual** cases use the accepted GC baseline's hash-verified current R/C controls. The actual sampled fields were C7=0, mode1 fallback root2430=200, alternate root24c4=40, and clean0/0/1/logger0. Aggregate41/76, selector changes, T0, q0 and zero history/current count are supplied hypothetical inputs. They are not a claim that the TV executed such an invocation at the read time.

| Supplied score | Supplied C7 | Supplied alternate limit | Executed selected threshold | Executed setter |
| --- | --- | --- | --- | --- |
|41|0|40|200|No|
|41|1|40|40|Yes, event736|
|41|1|200|200|No|
|76|1|200|200|No|

This explains a concrete mitigation hypothesis: matching alternate200 to the already sampled fallback200 can avoid this modeled selector-dependent threshold reduction. Earlier EX contains actual finite200/40 target evidence, including sampled clean values above40, but history/workflow and c4's publication-cap coupling remain confounders. These emulations neither eliminate those confounders nor establish that200 is safe, persistent or sufficient on the damaged panel. No new threshold write occurs here.

The actual decision uses the low16 score, so a later32-bit H snapshot is not automatically the exact comparison operand. The model retains that distinction. Live decision FP, actual selected-A branch, electrical producer and physical output still require separate evidence. This work does not qualify DS's executable storage, installation/cache visibility, scratch ownership, real-time overhead or independent rollback requirements.

## Reproduce and provenance

Run `python3 -B oracle.py` and `python3 -B -O oracle.py` from any directory. Explicit checks remain active with optimization. The local tools directory is imported only by this project script; no system Python environment or TV tooling was changed. Tool acquisition records the exact official PyPI2.1.4 wheel and its SHA256, with installed-byte equivalence checked separately. Relevant primary references are [Unicorn API mode definitions](https://github.com/unicorn-engine/unicorn/blob/2.1.4/include/unicorn/unicorn.h), [upstream FAQ](https://github.com/unicorn-engine/unicorn/blob/2.1.4/docs/FAQ.md), and [the pinned distribution](https://pypi.org/project/unicorn/2.1.4/).

`validation-initial.stderr` preserves the initial host-only range guard failure: the first implementation ended the allowed predicate span at0x2040, truncating its four-byte POP at0x203e. The range was corrected to0x2042; it was not a firmware defect or target failure. The original selected package remains unchanged.
