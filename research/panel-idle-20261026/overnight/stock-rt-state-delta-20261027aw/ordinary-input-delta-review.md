# Independent review of the ordinary-input delta reproducer

Recorded 2026-10-27 UTC. This review was limited to the host-only
`ordinary-input-delta-reproduce.py`, its pinned raw inputs, and the selected
source bodies it cites. It made no TV, root, network, USB, native-helper,
controller, power, reset, firmware, or physical observation and changed no
existing report, verifier, capture, or frozen AV artifact.

## Verdict

**CLEAR, with no material correctness finding.** The reproducer correctly
implements the selected-source `ca=1, cc=1, ce=0` branch, binds the relevant
source bodies and raw windows, and restricts its result to delayed sequential
numeric consistency. It does not claim that the selected image-0 body was
executing, that either snapshot is event-time state, that MODE2 exclusively
caused the differences, that the post-X RT tuple was still current, or that a
physical picture was present.

Reviewed reproducer SHA-256:

```text
5bab5089562542dc4d054b72603257dd9d89213af908745ca3169b0db24018d3
```

## Independent source and arithmetic check

The script pins the complete selected 5-MiB package at SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`
and hashes the relevant image-0 ranges:

| source range | pinned SHA-256 | reviewed role |
| --- | --- | --- |
| VA `0x2f5d8..0x2f96f` | `428c93783eeb93bec0a363d29043bca4c8aecdbf5e7339542ccd5c70ba537b45` | complete first helper |
| VA `0x2f804..0x2f963` | `1edc35ef9c97b5836cbf6be9c671d948f247b31375c70d1fe9cff1f57941566a` | decisive branch/output region |
| VA `0x2fb44..0x2fb7b` | `f9b94ce545ffc142ac8cbff9d0c4f2c6bcf7146316a59dd32d49814ffb8443a7` | ordinary-to-derived transform |

I independently decoded the selected bytes. The relevant control flow is:

- VA `0x2f804` loads ordinary `+0xca`; zero takes the output-clear path.
- VA `0x2f80c` loads `+0xcc`; zero bypasses the first candidate.
- VA `0x2f812` loads `+0xce`. Zero branches to the restricted first
  condition at `0x2f840..0x2f858`, which is exactly
  `(P0<X0) OR (P1<X1) OR (P2<X2)`.
- A false condition reaches `0x2f87c..0x2f880` and clears halfword `+0xe2`.
  A true condition compares `+0xe2` with threshold `+0xe0`; the mature
  `e2>=e0` case supplies `F0=1`, while the immature case increments the
  counter and leaves `F0=0` for that invocation.
- With `+0xce=0`, the second candidate/F1 path is bypassed. The store at
  `0x2f958` therefore makes `+0xe6` exactly F0 in this bounded case.
- VA `0x2fb60..0x2fb76` reads `(+0xe6 & 1)`, ORs it with ordinary halfword
  `+0x2fc`, normalizes the result to 0/1, and stores derived byte `+0x3d8`.

That is exactly the formula implemented by the reproducer. Calling it a
fixed-point consistency check, rather than replaying one invocation, is also
correct: the raw snapshots contain later stored inputs/counters/outputs, not
an instruction trace through the helper.

## Independent raw-value check

The two 824-byte ordinary and 1004-byte derived files are hash-pinned. Direct
little-endian decoding reproduces the verifier's values:

| field | older post-fault AK snapshot | later post-lifecycle AW snapshot |
| --- | ---: | ---: |
| gates `+ca/+cc/+ce/+116` | `1/1/0/1` | `1/1/0/1` |
| `P0/P1/P2` | `7,464,960` each | unchanged |
| `P3` | `8,128,512` | unchanged |
| initial indexes | `3/3/3` | unchanged |
| recomputed indexes / caps | `6/6/6` / `6/6/6` | unchanged |
| multiplier / upper flag | `900 / 0` | unchanged |
| recomputed `X0/X1/X2` | `8,254,590 / 8,251,261 / 8,250,967` | `31,868 / 21,738 / 35,229` |
| strict `P<X` terms | `true/true/true` | `false/false/false` |
| debounce threshold/counter `+e0/+e2` | `30/30` | `30/0` |
| first-helper output `+e6` | 1 | 0 |
| other final operand `+2fc` | 0 | 0 |
| derived `+0/+1/+3d8` | `3/10/1` | `3/8/0` |

For the older values, the selected condition is true and the sampled counter
is mature, so sampled `+e6=1` is consistent. For the later values, every
strict term is false, and sampled `+e2=0`, `+e6=0` is consistent with the
source clear path. In each snapshot, `+2fc=0`, so derived `+0x3d8` correctly
tracks bit 0 of `+e6`: `1 -> 0`.

The change at derived `+1` from 10 to 8 is preserved numerically. This
reproducer does not use that byte to prove the helper condition or assign it
a meaning, which is the correct boundary for this narrow comparison.

## Timing and interpretation limits

The later W terminal uptime is `137706.50`; post-X ended at native monotonic
`136922.242531`, a numeric difference of about `784.257469` seconds. That is
only a delayed ordering comparison. Cross-capture clock equivalence beyond
the retained same-boot context is not promoted into a sub-second event bound.

The W read consists of three sequential fixed reads. Ordinary and derived
values are not a controller-wide atomic tuple, and the reproducer correctly
labels its scope `late sequential numeric consistency only`. It also records:

- `table_words_observed=false`: only stored sum mirrors were sampled;
- `image0_interpretation` is conditional, not executing-code proof;
- no physical units or physical picture were identified;
- no exclusive reset cause was proved; and
- target operations by the reproducer are zero.

No current RT window was part of W. The clean RT tuple retained by post-X
roughly 13 minutes earlier must not be projected forward to this ordinary
input snapshot. Conversely, the W state cannot date the AV selector change or
be substituted for the missing fault-onset tuple.

## Non-blocking reproducibility notes

The script hash-pins both raw ordinary/derived inputs and requires each
capture result to be accepted, pointer-interpretable, cleaned to
`STAGE_ABSENT`, and bound to those raw hashes. It does not separately pin the
two `result.json` file bytes, and its emitted `stable_fields` list omits the
four gates that `decode()` nevertheless hard-requires to equal
`1/1/0/1`. Neither omission changes the reproduced arithmetic or conclusion;
they are presentation/provenance hardening opportunities, not blockers for
this host-only comparison.

Focused verification ran:

```text
python3 ordinary-input-delta-reproduce.py
python3 -O ordinary-input-delta-reproduce.py
```

Both modes emitted byte-identical JSON with SHA-256
`3c1c99dc05c7513e8cc885e7a4c0103f618a8392017f4fd496e346e1ace027aa`.

