# Independent review: RTP score-input provenance

Date: 2026-10-27 UTC  
Scope: offline selected-package and retained-artifact review only; no TV,
root, USB, network, UI, reset, write, or modification of frozen evidence

Reviewed inputs:

- `rtp-score-input-provenance.md`, SHA-256
  `8c4b66ccc2a9933176f3bc9651b8cafd56815da2cc71243691950649b31d7e75`
- `rtp-score-input-provenance.py`, SHA-256
  `4a96fbe99c0d9ecc5f317cc264e49055227953ce129ecb4a0bff05f5668307aa`

The verifier passed with identical JSON under normal Python and `python3 -O`.

## P1 — The record-ID flow is not mandatory before every `s[]` increment

The core conclusion that `s[i]` is a count rather than a sum of lane
differences is correct. However, the report's top-level pseudocode and
quantity table currently imply this unconditional sequence for every
accepted formatter path:

```text
record_id[i] += 1
publish root record-ID latch
s[i] += 1
```

There is an explicit packaged bypass. After reading the current u32 record ID
at VA `0xc5f6..0xc5fa`, VA `0xc604` executes `bhi 0xc6de` when that ID exceeds
the loaded halfword bound. VA `0xc6de` is an unconditional branch directly to
`0xc708`. It therefore skips all of:

```text
0xc6aa..0xc6b8  u32 record-ID increment/store
0xc6ca..0xc6d8  category-1 root +0x2490 publication
0xc6e0..0xc6ee  category-4 root +0x2492 publication
0xc6f2..0xc700  category-6 root +0x2492 publication
```

but still executes:

```text
0xc708..0xc718  uint16 s[category-1] += 1
```

Other earlier formatter checks can reject the call before either counter is
updated, so this is not a claim that every call increments `s[]`. The exact
supported relation is:

- a path that reaches `0xc6aa` increments/publishes its record ID and then
  increments `s[]`;
- the bound-exceeded path `0xc604 -> 0xc6de -> 0xc708` increments `s[]`
  without incrementing or publishing a record ID; and
- early rejected paths do neither.

Consequently, the detailed-row record IDs and root `+0x2490/+0x2492` latches
are not one-for-one proxies for `s[]`, even within one selector invocation.
They also have different reset scope: selector VA `0xb7f8..0xb80a` resets
only `s[]`, while the record-ID table is cleared by the separate broad
initializer at `0xca84`, whose direct callers are `0xb964` and `0xcb50`.
Record IDs can therefore span selector invocations in which `s[]` restarts
from zero.
This strengthens, rather than weakens, the report's warning that the 31
retained V6 rows are not the complete score input, but the bypass needs to be
stated explicitly before the report is used as the authoritative count-flow
description.

## P2 — The claimed whole-image pointer-literal census is broader than the verifier

The local pointer correction is exact, but the report's statement that it
has a complete census of the direct encoded pointer words and their 16-bit
literal loads is not supported by the current verifier.

Independent raw occurrence checks give:

```text
0x20000494 at VAs 0x0b894 and 0x1c064
0x20000498 at VAs 0x0b7ac, 0x0b898, 0x0c5ac, and 0x1c1a4
```

The verifier checks the words at `0xb894/0xb898` and checks 16-bit literal
references to those two literal locations, but it does not assert the full
occurrence lists above or classify the additional occurrences. Its actual
complete occurrence assertion applies to `0x2000ba40`, not to both dynamic
pointer words.

This coverage gap does not affect the local fallback call: exact PC-relative
resolution already proves its operands. The report should narrow the census
claim to the selector literal pool/path or add and classify the missing raw
occurrences before calling it a complete selected-image census.

## Verified correction — `0xb884` loads `0x20000494`, not `0x2000ba40`

The relevant 16-bit Thumb literal arithmetic is unambiguous:

| instruction | encoding | aligned PC | displacement | literal | word |
| ---: | --- | ---: | ---: | ---: | ---: |
| `0xb7fe` | `24 4a` | `0xb800` | `0x90` | `0xb890` | `0x2000ba40` |
| `0xb87e` | `06 48` | `0xb880` | `0x18` | `0xb898` | `0x20000498` |
| `0xb884` | `03 48` | `0xb888` | `0x0c` | `0xb894` | `0x20000494` |

Thus the fallback unpacker call at `0xb88a` receives:

```text
A = *(u32 *)0x20000494 + 8
B = *(u32 *)0x20000498 + 8
```

The nearby `0x2000ba40` literal at `0xb890` belongs to the six-halfword reset
loop at `0xb7fe`; it is not the `ldr` target at `0xb884`. The frozen format
trace's fallback `A=*(u32*)0x2000ba40+8` statement is therefore a concrete
address-resolution error.

## Verified distinction — count, record ID, and root latches are separate

The selected bytes independently establish:

1. VA `0xb7f8..0xb80a` zeros six halfwords at
   `0x2000ba40..0x2000ba4b` before the selector calls unpacker `0xbd58`.
2. Comparison helper `0xbbbc` computes `uint16 abs(A-B)` and calls formatter
   `0xc5d0` only on the documented qualifying category-1, category-4, or
   category-6 routes.
3. VA `0xc708..0xc718` indexes `0x2000ba40` by
   `2*(category-1)`, adds the literal value one, truncates to 16 bits, and
   stores it back. No `diff` operand participates in this update.
4. VA `0xc6aa..0xc6b8` separately increments a u32 table at
   `0x2000ba28 + 4*(category-1)` when that path is not bypassed.
5. The post-increment low half of category 1 is written to root `+0x2490`.
   Categories 4 and 6 read different u32 slots but both publish to the shared
   root `+0x2492` latch. It therefore records whichever of those two paths
   published most recently, not a combined count or a mode identity.

The retained equality `R+0x2492 == 54` and mode-6 `R+0x0f06 == 54` has no
assignment edge in this path. The first is a post-increment low-half record-ID
latch; the second is the low 16 bits of the separate mode-6 aggregate. Numeric
equality is not evidence that one supplied the other.

## Verified aggregate semantics

Predicate VA `0x1e68` does not receive a lane `diff`. For selected category
`i=mode-1`, it:

- shifts the category's four-halfword history and inserts current `s[i]` at
  `H[i].h3`;
- conditionally increments `q[i]` when `s[i] > R+0x24a0`;
- suppresses the aggregate update for q states `{8,9,10,12,24,25}`;
- otherwise adds the post-shift `H[i].h0` (an older count) to u32 `A[i]`;
- conditionally subtracts `T` at most once; and
- compares `low16(A[i])` with `fp`.

The supported description is therefore a stateful, delayed aggregate of
qualifying-lane counts. It is neither the current number of printed rows nor
a sum of the printed difference amplitudes. No physical panel-coordinate map
is established by this chain.

## Decision

The fallback pointer correction and the principal count-versus-amplitude
result are supported. The source report needs the P1 record-ID bypass
correction before its pseudocode/table can be authoritative, and its
whole-image pointer-census claim must be narrowed or completed. Neither issue
requires changing the frozen evidence; both can be carried by an additive
erratum.

## Follow-up closure of P1 and P2

The revised source artifacts are:

- `rtp-score-input-provenance.md`, SHA-256
  `ac06e131d4a062d1d7b8179f3f721bb9337b043913c44f3ccce5941c0672a122`
- `rtp-score-input-provenance.py`, SHA-256
  `6d1b82bb4fc2d8c1acc0fa5ff262d6409f0b22e6fff5376c2f462615abf8d0b6`

Both findings above are resolved in that revision:

- the pseudocode, quantity table, explanatory text, and JSON now explicitly
  distinguish the `0xc604 -> 0xc6de -> 0xc708` record-ID bypass and the
  different reset scopes; and
- the verifier now pins the complete raw occurrence lists for
  `0x20000494/0x20000498`, while the report correctly limits semantic
  interpretation to the selector-local literal loads.

The revised verifier again produced identical accepted JSON under normal
Python and `python3 -O`. No remaining defect was found in the bounded
pointer/count/aggregate claims. This closes P1 and P2 for the revised hashes;
it does not change any frozen artifact or promote the conditional CPU/bus
alias to a proved universal mapping.

