# Selectively refreshed endpoint admission

This source-qualified policy retains DV's ordinary-current admission and replaces only the alternate endpoint's equality-to-current requirement with membership in the **exact finite source image**. Parent approved this policy for the additive FA writer. This directory contains a pure model and audit, not a controller writer. Frozen DU/DV remain unchanged.

Selected package SHA256 is `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`; image0 FILE=VA+0x200. Pinned source ranges come from DV/model-source-proof.json and are checked against the actual package. No OEM bytes are copied here.

## Positive selective-update source

Image0 function389d0 stores **only one** endpoint: selector0 writes root2420 at38a90 or38ad2; nonzero selector writes root24bc at38a86 or38ab4. Both branches converge at38ad4, which stores the shared base/reference/current diagnostics at2494/2496/2498. Caller21576..215ac chooses ordinary parameters/selector0 when its object byte+1e is1, otherwise alternate parameters/selector1. Caller3af16..3af42 explicitly uses selector1. The same shared diagnostics can therefore describe a more recent update of one endpoint while the other endpoint retains a previous calculation.

A precise domain correction matters:38a3c compares **r8** to4000 and38a42 replaces **r8** with25. r8 came from the scaled reference at context+3a6. The current diagnostic comes from getter27670(1) into **sl**, then UXTH. **The >4000→25 fallback does not restrict current diagnostic T to4000**. All65536getter halfwords scaled by1/16 produce current T0..4095; reference is independently guarded to the pinned value24. test_model.py checks the exact CMP/MOV opcodes as well as their enclosing source hash.

The inherited arithmetic remains unsigned32 SUB/MLA/MUL wrapping, UBFX bits7..22, then cap-first/floor. Fixed base2075/reference24/coefficient15/scale195/floor3000/cap3800 give:

- T23→3138;3138 has unique preimage23.
- T24→3161;3161 has unique preimage24.
- T25→3183.
- Full T0..4095 has **72 distinct output values**, SHA256 `a61417913462d9b4c45d39431dbf6b662c84238e4f3b6585ac24c75654eabc53` over sorted little-endian u16 values.

This is not admission of any number between3000and3800. In-range3200 and3139 have no preimage and refuse. The complete72-value list is in validation.json; every allowed value has an enumerated source preimage, and every one of65536u16 candidates is checked for exact membership.

## Minimal revised admission

R20 ordinary endpoint must still equal Endpoint(currentR98), with currentR98 in0..4095. This is deliberately restrictive: mode1 does not universally prove that ordinary was the latest refreshed endpoint, and this policy does not claim otherwise. Rbc alternate must belong to the exact72-value image computed from the same **pinned** coefficients/base/reference/cap/floor. No historical diagnostic is invented; a matching preimage proves source compatibility, not when a value was written or which writer last ran.

All former DV static bytes remain exact. Echo remains zero-high-byte0..254; alternative limits/latches, normal limits200, callbacks, root20010000, aa0/ac2, scan1, geometry/profile/C7domain and M upper-mirror agreement retain their guards. Mode6, dirty/faulted/Quiescent state, arbitrary coefficient/reference changes and values in finite-image gaps still refuse. This changes admission of a modeled read-only endpoint; the action still writes only limitc4.

Each baseline→fresh→readback transaction retains **equal R20/R98/Rbc** and all other unchanged nonhistorical bytes, except the fixed c4 action byte and bounded echo. An alternate refresh from3138to3161 during the invocation refuses even though both endpoints individually belong to the image. A postwrite refusal preserves writeAttempted/limitMayHaveChanged and never auto-retries/reverses. Separate set and restore can start with different individually valid thermal tuples; no fixed historical T23 requirement prevents later legitimate drift.

The actual completed EX/preparation-01/baseline on USB63 is the positive new case: aa0/ac2/scan1, ordinary3161/current24, alternate3138, echo3, clean40, full M/C guards pass. Frozen DV's exact parser still refuses the alternate equality. The new pure policy admits the raw unchanged EX R/M/C and stable R pair. A separate synthetic pair changes only c4 to200 to test the fixed action composition; no target write is performed by these tests.

The source does not prove all historical coefficients were unchanged, enumerate every computed/DMA/cross-core writer, guarantee concurrent inactivity or establish electrical safety. Exact static profile admission and stable sequential transaction observations are the bounds of this policy. No waiting for temperature coincidence, endpoint rewriting, general numerical range, mode exception, extra USB read or new action is introduced.

## Reproduction and integration boundary

`python3 -B test_model.py` and `python3 -B -O test_model.py` read only the pinned source/EX inputs and emit identical validation JSON. They verify source ranges, exact reference-only fallback opcodes, all4096preimages/all65536candidate memberships, old DV refusal, actual EX admission, wrong-static/mode/fault/gap cases and thermal drift. No root/network/native/OEM execution occurs.

FA separately copies this pure model into its strict parser, uses the same verified72-value table in C#, and keeps fixedDV transport/binding/read-map/receipt/cleanup/timeouts. Its independent review and actual central execution are separate from this model's host validation.
