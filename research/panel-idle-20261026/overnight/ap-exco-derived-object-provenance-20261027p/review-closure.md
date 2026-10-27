# Closure of independent P ordering finding

Recorded 2026-10-27 UTC. This is an offline closure review of the corrected P
sources. It made no TV, network, root, USB, controller, helper, UI, write, or
reset request and did not modify the original report, verifier, or prior
independent review.

Corrected source pins:

```text
ap-exco-derived-object-provenance.md
50b17b0f93ecf8982e158193b5b1637f91d74b84c941cf5cc6f5fb744d2d9f40

verify-derived-object-provenance.py
9e67570f7f022f8c1ae069dbc458522e2e5d2f8bbe9a589f22f32900198f006f
```

## Result

The P2 temporal-provenance finding in `independent-review.md` is **closed**.
No P1 or P2 finding remains against these corrected pins.

The revised report now states the complete bounded order:

```text
get derived object through 0xe76c
get ordinary AP_EXCO through 0xe678
call 0x2f5d8 unconditionally at 0x2fb52
read post-call ordinary u16[+0xca]
if nonzero, call 0x2f980 at 0x2fb5c
read post-helper ordinary byte[+0xe6] and u16[+0x2fc]
store bool((+0xe6 & 1) OR +0x2fc) to derived +0x3d8
```

It explicitly records that `0x2f980` has a directly visible path at
`0x2f9b2..0x2f9b7` which clears ordinary halfword `+0x2fc`, and therefore
describes the final formula as operating on post-helper values rather than
entry-time values. It keeps the internal effects of `0x2f5d8` and nested
targets below `0x2f980` unresolved, which is the correct finite boundary.

The corrected verifier independently pins:

- `BL 0x2f5d8` at `0x2fb52`;
- gated `BL 0x2f980` at `0x2fb5c`;
- the following `+0xca`, `+0xe6`, `+0x2fc`, normalization, and `+0x3d8`
  instruction sequence; and
- direct helper bytes `0020a4f8fc02` for the `+0x2fc` clear.

Normal and optimized verifier runs completed successfully and emitted
byte-identical JSON with SHA-256
`f8af7c7a88513932ed98a3ed0f8a403359df0491207473d6a06c34005ae90c13`
and `target_operations:0`.

All other conclusions retain the prior bounded acceptance: the corrected
object identity/extent, reset zeroing, startup `+0` clear, direct `+0/+1`
setters, old-window coverage gaps, and refusal to normalize ordinary `20/0`
values remain supported. This closure adds no invocation record, global
writer census, field meaning, event-time tuple, physical cause, active-bank
claim, or safe-write conclusion.
