# Independent ordinary trace reviews and corrections

Recorded2026-10-27. No target operation was made by these reviews. S and T
were new, unfrozen work; no H--R listed artifact was changed.

## S helper-input trace

Root independently decoded the three helper bodies with Capstone, checked
the signed/unsigned branch domains and stateful set/increment/clear behavior,
and inspected the stored initializer. Review caught a semantic ordering error:
the first helper can overwrite `O+10a/+10c` before the later helper consumes
that X value. Stored `+116=1` permits this path. Therefore stored X0 does not
force the later runtime condition false. The initial bit remains clear on
its first pass because counter0 is below threshold30, regardless of that
condition's outcome.

The original two S files and original verifier outputs are retained in V as
`s-before-review-correction.md`, `s-verifier-before-review-correction.py` and
`s-verifier.{normal,optimized}.json`. They record the rejected interpretation
and must not be used as the current conclusion.

Root corrected the S report/verifier. Fresh executions normally and under
Python optimization passed with byte-identical output, saved as
`s-verifier.corrected.{normal,optimized}.json`.

An additional independent read-only agent reviewed these exact corrected
files and reported CLEAR with no remaining semantic blocker:

| Corrected S file | SHA256 |
| --- | --- |
| ap-exco-helper-inputs.md | 17068bd31de065a2720ca027498da41517e5d214e0dd633272ed144c29cabdb6 |
| verify-helper-inputs.py | ae0d25c648e8b777f3829cd2e13fc563ec5f26cb0514c7a89b542b9bac1283bd |

This establishes selected-code dataflow and stored initialization. Runtime
evolution is normal for these stateful helpers; divergence from a stored zero
is not by itself a configuration defect or a physical fault diagnosis.

## T action-causality trace

The independent read-only reviewer found two causal overclaims, subsequently
corrected by the author:

1. Late action mask4 in the mode1 bucket has no pre-event freshness proof.
   Conditional clearing and four possible action4 producers allow an older
   retained mark. It is compatible with a mode1 hypothesis and cannot identify
   V6's event mode.
2. Later host status10 is not unique to the recurring RT poll. Two other
   direct selector10 sites compete with that poll; no event-aligned image0
   diagnostic establishes which path produced the status.

The revised report states these limits, and the verifier checks all35 direct
common-handler callers and the three selector10 sites. The independent agent
reran the revised verifier normally and under optimization, got identical
passing results, and reported CLEAR for these exact files:

| Corrected T file | SHA256 |
| --- | --- |
| rtp-action-causality.md | 4465ca1a50b9c4a851cf0233a4172e930987b1b1dec7f1b7d3972e264755dbb5 |
| verify-rtp-action-causality.py | 5c73870fd7698a76d35500b82f31cdcbc2d5d6ecca126e7ab7fd75c8f09218ef |

Root also read the revised full report. Exact bookkeeping stores and a
software emergency path are supported; the MMIO writes' physical output
meaning and V6-to-image0 causal join remain unproved. Neither review
establishes a panel recovery or a safe firmware modification.
