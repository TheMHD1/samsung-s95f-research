# Independent review: corrected AP_EXCO caller provenance

Reviewed 2026-10-27 UTC. This review is additive and is intentionally excluded
from Q's original two-file evidence set. Neither original Q file was changed.
The review used only retained local firmware bytes and standard-library tooling;
it made no TV, network, USB, root-agent, helper, configuration, UI, reset, or
write request.

## Reviewed pins

| artifact | SHA-256 |
| --- | --- |
| `ap-exco-caller-provenance.md` | `9bfacc87f231cfd78d9240870febe0180d0e62183b3b9b521db1f6cf1703851c` |
| `verify-caller-provenance.py` | `df504fe6e19e711bb0ba620e711bf7f1b9658f5db43ac71c2d78a3bca54873db` |
| selected package | `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0` |

The verifier completed normally and under `python3 -O`; the compact JSON from
both runs was byte-identical and reported `target_operations:0`. It uses
explicit exceptions rather than Python assertions.

## Result

**Clear for the stated finite scope; no P0/P1/P2 finding.** The instructions,
direct-call census, immediate arguments, branch targets, and negative semantic
claims support Q's conclusions. This is a syntactic direct-BL census over the
selected image-0 bytes, not a proof that indirect or computed callers do not
exist.

### Derived byte `+0`

Setter VA `0x3286c` has exactly these direct BL sites in the finite image:

| callsite | immediately preceding instruction | `r0` value |
| ---: | ---: | ---: |
| `0x329f8` | `movs r0,#4` | `4` |
| `0x32a0c` | `movs r0,#1` | `1` |
| `0x32a2e` | `movs r0,#2` | `2` |
| `0x32ab6` | `movs r0,#3` | `3` |

The parent slice VA `0x329ce..0x32ac7` matches SHA-256
`85b842155f9881c6d0bf8e25a71ca51bd442ce5e28b3b6f3bb0681e80e716cd3`.
The bounded ADR/literal-pointer scan finds no direct printable reference in
that slice. Values `1..4` are therefore exact arguments, but they are not
qualified as a mode, unit, state, panel identifier, or physical measurement.

### Derived byte `+1`

Setter VA `0x35b56` has nine direct BL sites. Eight have an immediately
preceding constant:

```text
0x35c8c -> 11     0x35cda -> 3      0x35ce4 -> 2
0x35d14 -> 6      0x35d1e -> 4      0x35d2a -> 5
0x35d44 -> 7      0x35e4e -> 9
```

At VA `0x35d58..0x35d69`, the ninth site loads derived byte `+0x3d8`, selects
`r1=10` when nonzero and `r1=8` when zero, copies it to `r0`, and calls the
setter at `0x35d66`. That proves an unnamed `+0x3d8`-to-`+1` control edge; it
does not name either byte or either selected value.

The parent slice VA `0x35bba..0x35e89` matches SHA-256
`d5b296850cb370ddcafff35386db425a0355411b5835281fd364db79dfbb83ac`.
Its direct printable references are exactly:

```text
Write-panelID
vcal_sw_ctrl_one
cooling                  (two reference sites)
ELVDD_EN
```

These strings locate other blocks in the same parent switch and do not name
the setter or its values. The strongest concrete counterexample to adjacency
as meaning is the `Write-panelID` block:

```text
0x35c7a: conditional branch -> 0x35c88
0x35c88: unconditional branch -> common tail 0x35e6a
0x35c8a: movs r0,#11
0x35c8c: BL setter 0x35b56
```

Thus the `Write-panelID` control path bypasses rather than falls through to
the adjacent value-11 setter. No semantic relation may be inferred from that
adjacency, and the same caution applies to the other strings.

### Derived byte `+0x3d8`

The complete direct-BL scan finds exactly one call to derivation VA `0x2fb44`:
VA `0x13710`. Its bounded parent prefix VA `0x13464..0x13713` matches SHA-256
`fb02019acc42be182aa0b7b0f2843e709f2b0d5bb8df232496bbb10f426d7a8b`.
The bounded direct printable-reference scan finds none, so the caller remains
unnamed.

Within the derivation, the order visible in the pinned bytes is:

1. call `0x2f5d8` unconditionally at `0x2fb52`;
2. test the `+0xca` halfword and, when nonzero, call `0x2f980` at `0x2fb5c`;
3. only afterward read byte `+0xe6` and halfword `+0x2fc`; and
4. reduce those final values to the byte stored at derived `+0x3d8`.

This supports Q's “post-helper values” qualification. It does not establish
what the values physically mean or when the routine ran.

### Helper VA `0x2f980`

The helper slice VA `0x2f980..0x2f9b9` matches SHA-256
`84fb989b1945c419f9291ec374ba59c57fb71807227f7892d5be2cc9ad2dfc12`
and has exactly one direct caller, `0x2fb5c`. Its immediate control flow is:

```text
ordinary halfword +0x2cc == 0 -> clear halfword +0x2fc -> return
ordinary halfword +0x2ce == 0 -> clear halfword +0x2fc -> return
ordinary byte +0x2ce bit 0 set -> call 0x2f9ba
ordinary byte +0x2ce bit 1 set -> call 0x2fa38
return
```

The four CBZ targets independently resolve as follows:

| branch VA | target | effect |
| ---: | ---: | --- |
| `0x2f98c` | `0x2f9b2` | zero `+0x2cc` reaches direct clear |
| `0x2f992` | `0x2f9b2` | zero `+0x2ce` reaches direct clear |
| `0x2f99c` | `0x2f9a2` | bit 0 clear skips call `0x2f9ba` |
| `0x2f9aa` | `0x2f9b8` | bit 1 clear skips call `0x2fa38` |

The bytes at `0x2f9b2..0x2f9b7` are the direct `movs r0,#0` and halfword
store to ordinary `+0x2fc`. The two nested call targets and the unconditional
`0x2f5d8` callee are correctly retained as the first unresolved edges.

## Review boundary

The evidence establishes direct calls and exact register arguments only. It
does not establish field names, units, mode numbers, event-time state, indirect
caller completeness, or a current live tuple. Adjacent text is not used as a
field label. No nested callee was followed, and no protection, bypass,
persistence, high-bank, POFLG, return-guard, or write path was inspected.
