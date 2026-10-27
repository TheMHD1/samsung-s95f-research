# Independent review: base QDDimming final-duty analysis

## Reviewed inputs and method

This is an independent, offline review of the corrected frozen worker inputs:

| Input | SHA-256 |
|---|---|
| `tcon-research/qd-final-duty-branch-analysis.md` | `85bac5ebfcf28816cd7317ebb611c0f57d4969ffdaf684e7b21b7dc43db15551` |
| `tcon-research/qd-final-duty-reproduce.py` | `5287b7caf0ff4c9d1c52abf0f67783c36b2052e12de126f8a4d2ac206512d4f0` |
| `binaries/libave.so.0.1` | `a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777` |
| `overnight/pqe-policy-baseline-20261026T174544Z.json` | `5c36124d0d510fff8ac5ff282cfc43c1a70854d065b76da68ad760ceb56482a4` |

The review independently decoded the bounded Thumb bodies beginning at
`QDDimming::m_AutoPowerOff` `0x1740f0` and
`QDDimming::m_SetFinalDuty2D` `0x174260`, and compared their instruction order
with the report's arithmetic and branch claims.  It also ran the supplied
hash-gated checker locally:

```text
PYTHONPATH=/tmp/tcon-capstone python3 tcon-research/qd-final-duty-reproduce.py
PASS: pinned final-duty gates, arithmetic, clamps, static state, backend relocation/transport, and sampled-baseline anchors
LIMIT: CFG/dataflow classification is manual; indirect writers, runtime virtual mutation, transport application, and physical output are not proved
```

No TV, network, root, process-memory, device, getter, setter, IOCTL, or other
live operation was used for this review.

## Review result

No material contradiction was found in the corrected reviewed claims.

- The two weighted initial paths use low-32-bit multiplication followed by the
  signed reciprocal `/100` sequence; the ordinary Weber path uses the stated
  unsigned low-multiply and logical-shift stages.  These are integer
  expressions, not physical-light units.
- The final-duty body first computes `inner+0xac`, conditionally floors it,
  passes its address through the `this+8` virtual `+0x54` hook, copies the
  possibly mutated value into `inner+0xa8`, then calls `m_AutoPowerOff`.
- `m_AutoPowerOff` uses signed comparisons for its exact-1 AutoDim branch and
  its invocation counter; its non-exact-1 route decrements and clamps the
  counter.  The review agrees that this is an invocation count, not a proved
  wall-clock duration.
- A zero may be produced inside the AutoPowerOff arithmetic, but the caller's
  later signed clamp remains after that call: `51..1023` ordinarily, or
  `12..1023` for exact `inner+0x188 == 1`.  The two debug-log detours rejoin
  the pre-hook and backend paths; they do not remove those final clamps or
  bypass the relevant calls.
- For the sampled RoseMQD `+0xd8` backend route, the cache is written before
  the two transport calls, their results are ORed, and the examined vsync
  caller does not consume the final-duty return.  This supports the documented
  request/retry limitation, not acceptance, application, or physical-output
  claims.

## Correction history

The originally reviewed pair, report
`fb4f5b4cc5f4435673aa825bd60001e7d49d6f45eeecb45574d1b43fca0ff230` and
checker
`651373f1695c21cfceca6983d02c184fe949f0306e5acac5842c07ca6ebd7f1d`, had a
factual ordering error in its gate-writer discussion.  It said the
`ave_get_oled_model_type` call occurred only when `inner+0x450 != 1`.  Raw
constructor instructions instead call it unconditionally at
`0x17afc4..0x17afc6`, before `get_product_type(1)` at `0x17afca..0x17afcc`
writes `+0x450` at `0x17afd2`; the stored product type then decides whether the
already-returned enum is consumed or `+0x188` is forced to zero.  The corrected
pair above states that ordering and adds PLT identity checks for the final-duty
and AutoPowerOff calls.  The corrected checker was rerun successfully before
this note was updated.

## Limits retained by this review

The checker establishes hashes and selected instruction/relocation landmarks;
the full CFG/dataflow interpretation remains manual and bounded.  In
particular, the passive baseline is sequential and non-atomic, so it cannot
prove a stable contemporaneous state, a callback, a cache transition, a
transport attempt, an applied command, or any physical screen condition.
The virtual mutation hook, indirect writers, driver/transport outcome, and
physical panel effect remain unresolved.  This review found no evidence that
the analyzed duty route caused, prevented, or repaired the reported blackout.

## Related review-history note

Parent separately corrected an earlier DLSR literal interpretation to
`0x007c037c`.  That correction is noted here solely as project history; it was
not part of this independent final-duty review.
