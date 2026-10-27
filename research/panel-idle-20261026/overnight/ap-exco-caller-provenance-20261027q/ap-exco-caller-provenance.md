# Corrected AP_EXCO direct-caller provenance

Recorded 2026-10-27 UTC. This is a finite offline caller/argument trace over
the selected image-0 bytes. It made no TV, network, USB, root, controller,
device-node, helper, write, reset, UI, or configuration request. It does not
inspect protection or return/bypass paths, persistent storage, high-bank
state, POFLG, or guards. It builds on P's corrected call ordering without
changing or expanding into the unresolved callees.

## Result

One direct caller layer recovers exact control values but no field-level name
or physical unit for derived-object bytes `+0`, `+1`, or `+0x3d8`.

- The `+0` setter receives only immediate values `1`, `2`, `3`, or `4` from
  its four direct callsites. Its parent decision routine has no direct
  printable string reference. The first unnamed edge is the parent routine's
  conditions selecting those four values.
- The `+1` setter receives immediate values `2`, `3`, `4`, `5`, `6`, `7`,
  `9`, or `11`. A ninth call chooses `8` or `10` from derived byte `+0x3d8`.
  Its parent switch directly references several human-readable control
  strings, but control flow does not bind those strings to the setter values.
- The `+0x3d8` derivation has one direct caller at VA `0x13710`, inside a
  large routine with no direct printable string reference in the bounded
  prefix. It calls `0x2f5d8` unconditionally, then conditionally calls private
  helper `0x2f980`, before it reads the final `+0xe6` and `+0x2fc` inputs.
  The internals of `0x2f5d8` and nested targets `0x2f9ba` and `0x2fa38` are
  the first unresolved edges.

Thus the strongest supported labels remain the object-level registry names
`MULTI` and `AP_EXCO` from P. The current bytes `3/10/1` are not used to infer
units, modes, names, or defaults.

## `+0`: four exact constant callers

Setter VA `0x3286c` has exactly four direct BL callsites in selected image 0:

| callsite | immediate `r0` passed to setter |
| ---: | ---: |
| `0x329f8` | `4` |
| `0x32a0c` | `1` |
| `0x32a2e` | `2` |
| `0x32ab6` | `3` |

Each immediate `movs r0,#value` is directly adjacent to its call. The bounded
parent routine VA `0x329ce..0x32ac7`, 250 bytes, has SHA-256
`85b842155f9881c6d0bf8e25a71ca51bd442ce5e28b3b6f3bb0681e80e716cd3`.
It selects among these values using fields from other objects, but the finite
routine contains no direct ADR or literal-pointer reference to a printable
name. Following those other fields would open new branches, so the precise
boundary is: **unnamed selector values 1–4 chosen by VA `0x329ce`**.

This is not evidence that `+0` is a mode number, state number, temperature,
panel identifier, or fault level.

## `+1`: fixed codes and one dependency on `+0x3d8`

Setter VA `0x35b56` has exactly nine direct callers:

| callsite | value source |
| ---: | --- |
| `0x35c8c` | immediate `11` |
| `0x35cda` | immediate `3` |
| `0x35ce4` | immediate `2` |
| `0x35d14` | immediate `6` |
| `0x35d1e` | immediate `4` |
| `0x35d2a` | immediate `5` |
| `0x35d44` | immediate `7` |
| `0x35d66` | `10` if derived `+0x3d8` is nonzero, otherwise `8` |
| `0x35e4e` | immediate `9` |

The `0x35d58..0x35d69` block directly loads byte `+0x3d8`, selects `10/8`,
moves that selection into `r0`, and calls the `+1` setter. This is a positive
derived-to-derived control edge. It does not name either byte.

The bounded parent VA `0x35bba..0x35e89`, 720 bytes, has SHA-256
`d5b296850cb370ddcafff35386db425a0355411b5835281fd364db79dfbb83ac`.
It has direct ADR references to:

```text
Write-panelID
vcal_sw_ctrl_one
cooling
ELVDD_EN
```

Those are positive control strings for other blocks in the same switch, not
names for `+1` or its numeric codes. In particular, the block referring to
`Write-panelID` does **not** fall through to the adjacent value-11 setter:

```text
conditional branch at 0x35c7a -> 0x35c88
unconditional branch at 0x35c88 -> common tail 0x35e6a
value-11 setter block begins at 0x35c8a
```

This explicit control-flow separation prevents assigning
`Write-panelID = 11`. The other direct strings likewise occur in distinct
switch blocks and are retained only as unbound parent-routine context.

The precise unresolved edge is the switch/jump-table condition selecting each
unnamed code. No unit or semantic label is inferred from the numeric set.

## `+0x3d8`: caller and helper boundary

The ordinary-to-derived update VA `0x2fb44` has one direct caller,
VA `0x13710`. Its containing bounded prefix VA `0x13464..0x13713`, 688 bytes,
has SHA-256
`fb02019acc42be182aa0b7b0f2843e709f2b0d5bb8df232496bbb10f426d7a8b`.
The prefix performs many initialization/update calls but has no direct ADR or
literal-pointer reference to a printable string. It is therefore retained as
an unnamed ordinary entry rather than assigned a function name.

Helper VA `0x2f980..0x2f9b9`, SHA-256
`84fb989b1945c419f9291ec374ba59c57fb71807227f7892d5be2cc9ad2dfc12`,
has exactly one direct caller, `0x2fb5c` inside the derivation. It obtains the
ordinary AP_EXCO root and executes this finite control:

```text
if ordinary halfword +0x2cc is zero: clear +0x2fc, then return
if ordinary halfword +0x2ce is zero: clear +0x2fc, then return
if ordinary byte +0x2ce bit 0: call 0x2f9ba
if ordinary byte +0x2ce bit 1: call 0x2fa38
return
```

Immediately before the `+0xca` gate, the derivation also calls `0x2f5d8`
unconditionally at `0x2fb52`. The final `+0xe6` and `+0x2fc` reads occur only
after these call stages; the formula from P is therefore a post-helper-value
formula. The direct clear is a positive helper effect, not merely a possible
indirect one. Neither helper nor the bounded caller has a direct printable
field/control name. The trace stops at `0x2f5d8`, `0x2f9ba`, and `0x2fa38`
rather than expanding into new branches merely to seek a label.

## Boundary

This report proves exact direct callsites, fixed arguments, one `+0x3d8` to
`+1` selection edge, direct parent strings, and the helper's immediate branch
structure. It does not claim:

- that parent-switch strings name any of the setter fields or numeric codes;
- a complete indirect/computed caller census;
- an invocation time, event-time tuple, or physical cause;
- a current code identity beyond the separately retained fingerprint work;
- a safe write, patch, threshold, bypass, or persistence action.

`verify-caller-provenance.py` pins the package, direct caller censuses,
immediate arguments, branch targets, direct string coordinates, parent/helper
slices, and explicit negative claims using only Python's standard library.
Normal and optimized runs must emit byte-identical JSON with
`target_operations:0`.
