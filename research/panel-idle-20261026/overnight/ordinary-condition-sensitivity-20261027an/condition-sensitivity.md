# Ordinary-condition sensitivity: what the divisor finding changes

2026-10-27 UTC. This is offline arithmetic on accepted W/AK bytes and
selected-code semantics. No TV command, new collector, debugger, configuration
change, protection change, write, flash or live intervention was performed.

## Result

The new divisor118 observation resolves an index-calculation consistency gap,
but the mismatch against stored1024 does not itself identify a repair target.
With the retained numerator2700 and cap6,118 predicts index6;1024 predicts3.
The retained sum mirrors for **both** corresponding source tails already
exceed the first-helper thresholds:

| Lane | Initial tail12..14 | Recomputed tail9..14 | Threshold | Initial margin |
| --- | ---: | ---: | ---: | ---: |
| 0 | 8,252,833 | 8,254,590 | 7,464,960 | 787,873 |
| 1 | 8,248,159 | 8,251,261 | 7,464,960 | 783,199 |
| 2 | 8,248,218 | 8,250,967 | 7,464,960 | 783,258 |

For a held source table whose tails equal these retained mirrors, changing
only the divisor from118 to1024 selects tail12..14 and leaves the captured
`P<X` condition true. Under the retained cc1/ce0/ca1 and mature counter30,
the modeled F0 output remains1. This is a conditional counterfactual, not an
actual intervention or a claim about the panel response. The source words
were never captured; the initial and recomputed loops can observe different
source generations, and the USB prefix is not an atomic controller snapshot.

## Finite positive writer domain

Both ordinary writers upper-cap their selected floating components at1 and
multiply by1024 before unsigned conversion. For finite nonnegative selected
components, positive count where applicable and a nonzero converted divisor,
the resulting domain is1..1024. Zero-output gates, count0, negative/NaN or
exceptional conversion are outside this domain. This is a code-domain bound,
not a statement of every runtime path or a permitted tuning range.

The reviewed binary32 quotient calculation, including STRH truncation before
the cap, gives these exact bands with numerator2700 and cap6:

| Divisor | Final index | Inclusive source tail with upper14 |
| --- | ---: | --- |
| 1..490 | 6 | 9..14 |
| 491..600 | 5 | 10..14 |
| 601..771 | 4 | 11..14 |
| 772..1024 | 3 | 12..14 |

For a fixed table with no u32 addition overflow across the six-word tail,
all four tails are at least the initial three-word tail. In that restricted
model every divisor in this domain preserves the true condition. This
explains why simply restoring stored divisors has no demonstrated prevention
mechanism in the retained arithmetic.

The no-overflow qualification is essential. Source entries are u32 and actual
adds wrap; a distribution/count unit and its total bound are unproved.
The verifier constructs a valid u32 table per lane with the same two retained
endpoint sums but a wrapped zero at index4. Consequently the existing
aggregate mirrors do not prove monotonicity for the unobserved intermediate
tails. No proposed change follows from that counterexample.

## What remains unidentified

The verifier constructs two different non-wrapping tables with the same
captured endpoint sums and different index1 sums, plus the wrapping witness
above. These are mathematical witnesses, not reconstructed live data. They
demonstrate that the retained aggregate values cannot uniquely recover the
individual bins or general content response.

The useful diagnostic conclusion is narrower:118 is not evidence of a bad
default or a uniquely causal input. Source generation, live control choices,
counter history and the controller-to-panel action remain unresolved. The
direct host-control-to-divisor edge is established in AI, but its active
runtime factors and branches are not captured. Physical picture onset is
still needed to attribute a particular controller transition to darkness.

`verify-condition-sensitivity.py` pins the selected helper, retained ordinary
prefix, reviewed AF quotient model and W aggregate verifier. It enumerates
the finite positive domain, checks both endpoint margins and exercises the
non-identifiability/overflow witnesses. It performs no target operation and
uses explicit checks under normal and optimized Python.
