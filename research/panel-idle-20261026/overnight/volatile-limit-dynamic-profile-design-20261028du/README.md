# Dynamic profile guard design and pure source model

This is a host-only design, not a writer revision or an execution clearance. The frozen DQ writer remains unchanged. Its exact profile correctly refuses newly observed legitimate runtime variation. The proposed admission policy replaces four exact halfwords with narrowly modeled checks; it retains the fixed two-byte action and every other guard. No target, USB, network, subprocess, OEM execution, or native-code binding is present in the model/tests.

The model passes **135452 explicit checks** in ordinary and optimized Python, with identical validation output. Thirteen retained R snapshots match both modeled endpoints. Two later recovered snapshots are an important negative case: mode6 has alternate3161 and shared temperature24, while ordinary3200 was not refreshed. Therefore neither endpoint is universally equal to the shared diagnostic prediction. The proposed mode1 admission policy deliberately rejects this state.

## Source and arithmetic

The selected package is `selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin`, 5242880 bytes, SHA256 `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`. Image0 file offsets are VA+0x200; image1 offsets are VA+0x40200. Package identity is not a new attestation of the entire running image. Source ranges and retained input identities are in `validation.json`; no OEM input bytes are duplicated here.

Image0 function0x389d0 receives cap/coefficient/scale/selector in r0/r1/r2/r3. At0x389f6..38a12 it loads an unsigned halfword from object+0x3a6, converts to float32, multiplies by literal0x3d800000 (0.0625 at0x38aec), converts to unsigned integer with truncation, and zero-extends16bits. Values above4000 are replaced with25 at0x38a3c..38a42. Getter0x27670(1) supplies unsigned CPU0x20000c1e; the adjacent label is TEMP. The same exact conversion gives the runtime mirror at R+0x98. For all65536 possible unsigned inputs, conversion equals integer division by16: raw getter input maps to0..4095. Calibrated physical temperature units are not established.

At0x38a4a..38a62 three unsigned halfwords from object+0x31c are summed, divided unsigned by48, then truncated to16bits. This base, the reference, and the scaled runtime input are later stored at R+0x94/+0x96/+0x98. The underlying three samples are outside the fixed capture, so the proposed guard pins their diagnostic base to2075 and reference to24; it does not pretend to reconstruct unobserved raw samples.

The arithmetic at0x38a64..38a72 is:

```text
delta     = (temperature - reference) mod 2^32
mla       = (base + coefficient * delta) mod 2^32
product   = (mla * scale) mod 2^32
candidate = bits 7..22 of product
endpoint  = cap, if candidate > cap
            otherwise max(floor, candidate)
```

This preserves ARM SUB/MLA/MUL overflow and UBFX width. It is not unrestricted integer division by128. Signed comparison instructions receive zero-extended halfwords here, so their ordering is ordinary nonnegative ordering. The cap branch runs before the floor branch; the model preserves that order. Under the pinned coefficient15, scale195, floor3000 and cap3800, exhaustive temperatures0..4095 produce endpoints within3000..3800 and strictly above the fixed lower endpoint500. This establishes numeric admission bounds, not monotonicity over the complete temperature domain or electrical safety.

Caller0x21576..215ac selects ordinary R+b2/ae/b0 with selector0 when its object+0x1e is1; otherwise it selects alternate R+ba/b6/b8 with selector1. Caller0x3af16..3af42 also selects the alternate parameters. The callee stores only the selected ordinary R+0x20 or alternate R+0xbc, then updates the shared diagnostics at0x38ad4..38ae2. It does not refresh both endpoints atomically. Image1 copies ordinary root2420 to CPU4c6 at0xbddc..bde4, and alternate root24bc at0xbdaa..bdb2. Observed M+0x26 is that sampled endpoint mirror.

With the retained pinned parameters, temperature25 predicts3183; temperature24 predicts3161. This accounts exactly for the baseline-to-recovered variation that blocked DQ. The later mode6 recovery is also consistent with the selective-update source: alternate3161 matches the shared diagnostics and M mirror, while ordinary3200 remains unchanged. No initialization-writer census is claimed for that3200 value.

## Volatile echo

Image0 0x9978..9986 reads the low byte of R+0xac, increments it and wraps255 to0. At0x9988..998c it duplicates the value into request bytes2/3. The bounded endpoint-e0 exchange checks the response. Receive path0x9844..984c writes a matching duplicated received byte using STRH to root24ac. This is an echo/sequence field, not immutable configuration.

The conservative admission domain is a zero high byte and low byte0..254. It permits changes and wrap between reads without assuming exactly one exchange occurred. The bounded receive path can accept a duplicated255 if externally supplied, but the identified own sender does not generate it; this design rejects255. These are bounded source facts, not a claim that every possible writer was enumerated.

## Proposed admission policy

Only these additional halfwords change treatment from the frozen profile:

| Field | Proposed invariant |
|---|---|
| R+0x20 ordinary upper endpoint | Exact modeled value, within3000..3800 and above500. |
| R+0x98 shared scaled runtime mirror | Unsigned0..4095; participates in the exact model. |
| R+0xbc alternate upper endpoint | Same exact modeled-value restriction. Both-fresh equality is a conservative admission restriction, not a general live-state invariant. |
| R+0xac echo | High byte0, low byte0..254; may change independently. |

The static base/reference, both coefficient/scale/cap/floor sets, lower endpoint500, alternative gates and latches, callbacks, root, mode, scan, geometry, clean stop/fault/gate state, logger state, ordinary thresholds200 and remaining exact profile bytes retain their prior requirements. Existing historical-field exclusions and selector0/1 handling are preserved. No new endpoint wildcard, temperature calibration, automatic mode selection, or arbitrary write is introduced.

M flags must remain aa0/ac2, which is the source-qualified ordinary mode1 path. Geometry remains2160/1920/2880, root20010000, scan1, directional thresholds500/0/500/0, lower500, C6=92, C8=3, and C7 remains in the original0/1 domain. Only M's previous exact upper3183 comparison changes to equality with validated ordinary R+0x20. Mode6 aa0/ac1 rejects, even if its selected alternate endpoint is mathematically valid.

For each separate set or restore invocation, validate the initial R, initial M/C context, fresh R and readback R. Require the thermal tuple R+0x20/+0x98/+0xbc to remain equal initial→fresh and fresh→readback. Require selector stability and all other previously exact pairwise bytes, allowing only the fixed c4 change and independently bounded echo variation. A later restore may start with a different valid temperature tuple from the earlier set. This supports legitimate drift between invocations without accepting a thermal update inside the short write transaction.

The design can conservatively refuse transient or selectively refreshed states, and it can refuse after a write if an update races readback. Sequential equal samples do not prove atomic firmware execution. Such a refusal must retain the writeAttempted/limitMayHaveChanged, matched-transfer phase, native ownership and readback evidence; it must not trigger an automatic retry or reverse write. An unclosed phase or child/ownership ambiguity still prohibits new headers.

The write contract stays exactly one action40→200 (`c800`) or a separate200→40 (`2800`), address0x470124c4, length2, target0x102. All fixed callback/R/M/C/fresh-R/write/readback ordering, native same-FD GETDRIVER/statx ownership, exact readiness instance, full matching payload obligation, Unknown-stop rule, cleanup, exclusive receipt, deadlines, no UI/reset/retry, and central serialization remain required. This document does not implement that composition in native code.

## What the model permits and leaves unresolved

The pure model demonstrates a bounded alternative to pinning temporary3183/25/251 values forever. It also demonstrates that permissive endpoints or unconditional both-endpoint freshness would be unjustified. A new native derivative would need independent source/host review, fresh normal Apps mode1 evidence, and all original deployment/readiness checks before a finite comparison.

Threshold c4 also bounds publication:200 permits indices0..200, below the independently observed512-entry guard. That is an index-capacity statement, not electrical safety evidence. Forty-eight-record readers would not cover all201 possible publications. Neither this model nor a finite clean result proves a permanent fix, physical picture state, actual final-A selection, a hardware packed-data producer, or complete source/runtime equivalence.

Reproduce host qualification with `python3 test_model.py` and `python3 -O test_model.py` from this directory. The script reads pinned retained inputs in the sibling research tree and rewrites only its own deterministic `validation.json`. It checks all raw-input conversions, all allowed modeled temperatures, modular-overflow cases, changed static bytes, endpoint/echo bounds, full proposed R/M/C policy, set/restore pair rules, fault refusal and the later mode6 counterexample. It does not execute the firmware or perform a target operation.
