# Independent review of derived AP_EXCO object provenance

Recorded 2026-10-27 UTC. This is an independent, offline review of
`ap-exco-derived-object-provenance.md` and
`verify-derived-object-provenance.py` against the original selected package
and retained raw captures. It made no TV, network, root, USB, controller,
device-node, helper, UI, write, reset, or configuration request. It did not
modify the original P report/verifier or any frozen evidence.

Reviewed source pins:

```text
ap-exco-derived-object-provenance.md
7a85d8f721d75edf6c366734b7f25bf3a9ed33d4c0f9e9e2174cb34af1e3a5ae

verify-derived-object-provenance.py
6142d08f45ce0a68c3014acd7acaac3d3686039ec9aa9a33bd5cd074a7b839c6
```

## Verdict

The finite object identity, extent, reset-zero coverage, startup `+0` clear,
direct `+0` and `+1` setter routes, final `+0x3d8` Boolean reduction, old-read
coverage limits, and no-`20/0`-normalization boundary are supported.

- **P1 findings:** none.
- **P2 findings:** one temporal-provenance omission.

The omission does not invalidate the final Boolean expression, but it matters
to the provenance of the values used by that expression. Function `0x2fb44`
contains an unconditional direct call to `0x2f5d8` before it reads ordinary
`+0xca`. If the post-call `+0xca` is nonzero, it then calls `0x2f980`; only
after that conditional call does it read ordinary `+0xe6` and `+0x2fc` and
compute the stored Boolean. Moreover, `0x2f980` itself contains a positive
direct path that clears ordinary halfword `+0x2fc`.

Therefore the accurate bounded statement is:

```text
call 0x2f5d8 unconditionally
read post-call ordinary u16[+0xca]
if nonzero: call 0x2f980
read post-helper ordinary byte[+0xe6] and u16[+0x2fc]
derived[+0x3d8] = bool((ordinary[+0xe6] & 1) OR ordinary_u16[+0x2fc])
```

The report correctly lists `0x2f980` before the two final reads, but omits
the preceding `0x2f5d8` call and describes `0x2f980` only in terms of possible
indirect effects. The verifier likewise pins getters and bytes beginning at
the later `+0xca` load, but does not assert the `0x2fb52 -> 0x2f5d8` call or
the complete call/read order. These are documentation and verifier coverage
gaps, not evidence that the retained late Boolean value is wrong.

## Object identity and extent

The selected package is exactly `0x500000` bytes with SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
For image 0, stored FILE is linked VA plus `0x200`.

The 28-byte record at FILE `0x3c5b8` independently reproduces SHA-256
`41dfa8809a435830065f05cbcf22bc20ee9b0f4b4f773e3d49f02f3b04403f66`
and these seven words:

```text
0x0003dd84  0x0003d44b  0x00000002  0x0003dd8c
0x200158a8  0x000003ec  0x00000018
```

The two string pointers resolve to `MULTI` and `AP_EXCO`. The destination and
extent positively establish CPU object
`0x200158a8..0x20015c93`. No semantics are assigned to the remaining record
words. Getter VA `0xe76c` has the pinned eight bytes
`00487047a8580120`, returning literal `0x200158a8`; ordinary AP_EXCO getter
`0xe678` is distinct.

## Reset and startup initialization

The complete image-0 scatter table hash and final row reproduce as reported:

```text
source       0x0003e764
destination  0x20000f4c
length       0x00016438
handler      0x000001d8
```

The destination extent is `0x20000f4c..0x20017383`, wholly containing the
derived object. The pinned handler body zeros registers, emits repeated
16-byte zero stores, handles its bounded tail, and returns. Thus reset-zero
coverage for `+0`, `+1`, and `+0x3d8` is positive.

The ordinary sub-initializer VA `0x333a8` has the reported SHA-256. Its call
at `0x333c4` targets getter `0xe76c`, the result is moved into `r4`, and
instructions `0x333e8..0x333eb` are `movs r0,#0; strb r0,[r4,#0]`.
The image-wide direct-BL scan returns only caller `0x39b22`, inside the
reported startup function. This supports an ordinary explicit `+0` clear in
addition to reset scatter. It does not add corresponding startup clears for
`+1` or `+0x3d8`.

## Direct byte setters

The `+0` setter slice VA `0x3286c..0x328a3` matches SHA-256
`ccaae391eab8d2cda5b01f181a99308fb799ba9e93923251f3fb29a841616a9d`.
The local sequence is caller `r0 -> r5`, getter `0xe76c -> r4`, then
`strb r5,[r4,#0]`. The direct-BL caller census reproduces:

```text
0x329f8  0x32a0c  0x32a2e  0x32ab6
```

The `+1` setter slice VA `0x35b56..0x35b69` matches SHA-256
`50d464ed7f82d179e974c298739548ca77b0fc698dcc6a57e79c48397d8174ce`.
Its local sequence is caller `r0 -> r4`, getter `0xe76c -> r5`, then
`strb r4,[r5,#1]`. The direct-BL caller census reproduces:

```text
0x35c8c  0x35cda  0x35ce4  0x35d14  0x35d1e
0x35d2a  0x35d44  0x35d66  0x35e4e
```

These are positive unnamed input-byte setters. The finite review does not
resolve caller value selection and does not promote either byte to a named
Samsung setting.

## Exact `+0x3d8` control and data order

The complete VA `0x2fb44..0x2fb7b` slice matches SHA-256
`f9b94ce545ffc142ac8cbff9d0c4f2c6bcf7146316a59dd32d49814ffb8443a7`.
Independent BL decoding and instruction ordering give:

| callsite | target | position/effect |
| ---: | ---: | --- |
| `0x2fb46` | `0xe76c` | get derived object; save to `r5` |
| `0x2fb4c` | `0xe678` | get ordinary AP_EXCO; save to `r4` |
| `0x2fb52` | `0x2f5d8` | unconditional call before any of the three reported input reads |
| `0x2fb5c` | `0x2f980` | conditional call when post-`0x2f5d8` ordinary `u16[+0xca] != 0` |

The remaining sequence is exactly:

```text
0x2fb56  ldrh ordinary[+0xca]
0x2fb5a  cbz  -> skip 0x2f980
0x2fb60  ldrb ordinary[+0xe6]
0x2fb64  and  bit 0
0x2fb68  ldrh ordinary[+0x2fc]
0x2fb6c  orr
0x2fb6e  cbz  -> store 0; otherwise store 1
0x2fb76  strb derived[+0x3d8]
```

Thus `+0xca` gates `0x2f980` but is not directly ORed into the result. The
final expression stated in P is correct for the values observed after the
preceding calls. It must not be described as necessarily using entry-time
ordinary values.

The ordering caveat is concrete rather than hypothetical for `0x2f980`:
that function gets the ordinary object and has instructions
`0x2f9b2..0x2f9b7`:

```text
movs r0,#0
strh r0,[r4,#0x2fc]
```

on one branch. Therefore the gated helper can directly change an operand
subsequently consumed by the Boolean. This review does not broaden into a
full semantic trace of `0x2f5d8`, `0x2f980`, their subcalls, or excluded
branches. It simply preserves their proven place in the ordinary order and
the one direct relevant store already visible in the gated helper.

The direct-BL scan returns `0x13710` as the only direct caller of `0x2fb44`.
That is a finite direct-call fact, not an invocation record or a complete
indirect-caller census.

## Old captures and late corrected sample

The older ordinary raw windows retain their reported hashes and cover object
offsets:

```text
+0x000..+0x00f
+0x3cc..+0x3eb
```

The transform inputs `+0xca`, `+0xe6`, and `+0x2fc` lie in neither range.
Consequently the old captures cannot evaluate the transform, and their
selected bytes `20/0` cannot be normalized, copied, or treated as defaults
for the distinct derived object.

The corrected late raw capture independently reproduces expected pointer
`0x450158a8` and derived values `+0=3`, `+1=10`, `+0x3d8=1` with the pinned
raw hashes. Value `1` is compatible with the Boolean store; `3` and `10` are
compatible with byte-valued setters. None proves which routine ran, which
source operand selected the Boolean, when a value changed, or what any field
means. The three-window capture is late and sequential, not the V6 event
instant or an atomic tuple.

## Verifier reproduction and bounded limits

Normal and optimized verifier runs emitted byte-identical JSON, SHA-256
`c9c35ef347b74c68a267fa4a8766c7b3d2323221c08be970956f7b26ddc59b42`,
with `target_operations:0`. The verifier meaningfully pins the package,
record/getter, scatter coverage, initialization, setters, caller sets, final
reduction bytes, capture hashes, and interpretation limits.

Its missing assertion for callsite `0x2fb52` and complete transform order is
the P2 coverage gap above. Subject to that additive correction, the report is
bounded and useful. It does not provide a global writer census, an invocation
trace, field names/units, physical cause, active bank, event-time state, or a
safe write. No protection, bypass/return, persistence, high-bank, POFLG, or
guard branch was reviewed.
