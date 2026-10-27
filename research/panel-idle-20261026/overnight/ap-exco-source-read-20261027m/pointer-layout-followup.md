# AP_EXCO pointer-layout follow-up

Recorded 2026-10-27 UTC. This is an additive offline correction to the earlier
pointer interpretation. It reads retained files only and made no TV, network,
USB, device-node, UI, configuration, or storage request. The frozen reader and
earlier evidence were not modified.

## Result

The capture does **not** support a global `-8` relocation. Bus window
`0x470002c0..0x470002df` lines up exactly with packaged image-1 CPU slots
`0x200002c0..0x200002df`. The error was in the earlier static interpretation
of which AP_EXCO lookup populates each slot:

| CPU slot | captured bus word | exact packaged origin |
| --- | ---: | --- |
| `0x200002c0` | `0x00000001` | startup readiness byte/word area, not a configuration pointer |
| `0x200002c4` | `0x4500ff14` | ordinary AP_EXCO first destination |
| `0x200002c8` | `0x4501024e` | ordinary AP_EXCO second destination |
| `0x200002cc` | `0x450158a8` | AP_EXCO entry from the distinct `0x1000c` registry root |
| `0x200002d0` | `0x450130b6` | ordinary AP_TED first destination |
| `0x200002d4` | `0x450130f0` | ordinary AP_TED second destination |
| `0x200002d8` | `0x4500f0e0` | ordinary AP first destination |
| `0x200002dc` | `0x0001b691` | reset-initialized odd linked-code address; not a configuration allocation |

Most importantly, getter VA `0x38e8` reads slot `0x200002cc`. The ordinary
callback at VA `0x3934` calls that getter and performs three distinct reads
through the returned pointer: source `+1` into `r8`, source `+0x3d8` into
context `+0x6c7`, and source `+0` into context `+0x6c8`. Its source object is
therefore `0x450158a8`, not either ordinary AP_EXCO allocation at
`0x4500ff14` or `0x4501024e`. The further role of the `+1` value is not named
here.

The prior assertion that slot `0x200002cc` should contain `0x4500ff14` is
mistaken and is superseded by this note. The actual capture itself handled the
mismatch safely: transport was accepted, interpretation was rejected, and the
three raw windows were retained.

## Retained capture

The accepted capture has these immutable raw artifacts:

```text
pointer-window.bin     32 bytes
SHA-256 7634f63e1eace3b6da5f287655f1b1ef3ebdb81b22909605a467c2472af43cd3

source-base-window.bin 16 bytes
SHA-256 374708fff7719dd5979ec875d56cd2286f6d3cf7ec317a3b25632aab28ec37bb

source-tail-window.bin 32 bytes
SHA-256 f4eec86c76db591f12c003fc318c76418e9455c10f10ad2c40acf0b21010814b

result.json
SHA-256 ffba3a63943e30fe689a1251237dfe18dcadff0c6eb5aec1022c3ac1eb20e901
```

`result.json` records accepted transport, `pointer-anchor-mismatch`, no bus
alteration, and successful stage cleanup. The pointer bytes decode to:

```text
00000001 4500ff14 4501024e 450158a8
450130b6 450130f0 4500f0e0 0001b691
```

The selected package is
`F_RSM1_BN9659934B_COMMON.bin`, size `0x500000`, SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
Image-1 linked VA maps to package FILE `0x40200 + VA`.

## Exact startup stores

Image-1 startup VA `0x1bcc4..0x1bd47` has SHA-256
`344accecffd7cff7fb1e7e56ec85778bfa99a9b12646223f34a84e43fb49288b`.
Decoding every name/call/store triplet gives:

| name | call | destination slot |
| --- | ---: | ---: |
| AP_EXCO | `0x1bbfc` | `0x200002c4` |
| AP_EXCO | `0x1bbd4` | `0x200002c8` |
| AP_EXCO | `0x1bc24` | `0x200002cc` |
| AP_TED | `0x1bbfc` | `0x200002d0` |
| AP_TED | `0x1bbd4` | `0x200002d4` |
| AP | `0x1bbfc` | `0x200002d8` |
| MULTI | `0x1bc24` | `0x200002bc` |

The earlier analysis inspected the third AP_EXCO store but implicitly assigned
it the first wrapper's result. The three calls have different roles:

- VA `0x1bbfc` passes logical registry-root address `0x00010000` to common
  lookup VA `0x1bc4c`, takes row word `+4`, and maps that destination.
- VA `0x1bbd4` passes the same root `0x00010000`, takes row word `+12`, and
  maps that destination.
- VA `0x1bc24` passes a different root, `0x0001000c`, takes its row word `+4`,
  and maps that destination.

The exact wrapper hashes are respectively:

```text
0x1bbfc..0x1bc23  0c718c8af720ca992a613b0a9cc6091f76ce58ec7160d229af12af03d40c5b53
0x1bbd4..0x1bbfb  c1da8944bfcffd4f8cfcfe01737c040e21f4dd8c1c1c76ab960e5de8bac25922
0x1bc24..0x1bc4b  5a79a33e09ba696ab0ff9eb60bdcec8c1a1aabd20b7f4a3cd02f93f5942c0960
```

Common lookup VA `0x1bc4c..0x1bcc3`, SHA-256
`de75682718d9e334652ad449ae8ccc62445ee631d5b670c10dbb145be1eda83e`,
maps the supplied registry root, follows its descriptor and entry-array
words, walks fixed-stride entries, maps each entry name, and calls the ordinary
string comparator at VA `0x89c`. Thus `0x10000` and `0x1000c` select distinct
registry roots; they are not interchangeable constants.

## Exact table matches

The ordinary 21-row configuration table at FILE `0x3ccbc..0x3cf07` has
SHA-256
`669adda911a2e5bf5b053ab486f11c2611e115b284eeaec79c58e5876fbad287`.
Its relevant rows are:

```text
AP_EXCO first  0x2000ff14  len 0x033a
        second 0x2001024e  len 0x1200

AP_TED  first  0x200130b6  len 0x003a
        second 0x200130f0  len 0x0f42

AP      first  0x2000f0e0  len 0x040c
```

The explicit selector-zero mapping adds `0x25000000`, producing five of the
captured words exactly.

The separate record at FILE `0x3c5b8..0x3c5d3`, SHA-256
`41dfa8809a435830065f05cbcf22bc20ee9b0f4b4f773e3d49f02f3b04403f66`,
is:

```text
word 0 -> "MULTI"        0x0003dd84
word 1, raw unnamed value 0x0003d44b
word 2, unnamed          0x00000002
word 3 -> "AP_EXCO"      0x0003dd8c
word 4, returned field   0x200158a8
word 5, unnamed          0x000003ec
word 6, unnamed          0x00000018
```

Mapping that destination with selector zero gives exactly `0x450158a8`, the
captured value at slot `0x200002cc`. Only the string pointers, the wrapper's
selection of entry word `+4`, and the mapped destination are used here; the
other record words and their physical or semantic meanings were not proved.

Reset scatter row 0 independently explains the last word: dynamic slots
`0x200002c0..0x200002d8` reset to zero, while `0x200002dc` resets to
`0x0001b691`. This further contradicts a blanket `-8` shift.

## Callback and the two source reads

Getter VA `0x38e8` is exactly:

```text
ldr r0, =0x200002cc
ldr r0, [r0]
bx  lr
```

At callback VA `0x393e`, its return is placed in `r6`; the callback then has
these exact operations:

```text
394a  byte [r6 + 1]     -> r8
394e  byte [r6 + 0x3d8] -> context byte +0x6c7
3956  byte [r6 + 0]     -> context byte +0x6c8
```

The last two copies preserve the earlier observed mirror lineage:
context `+0x6c7/+0x6c8` reflects source `+0x3d8/+0`, respectively. The
additional `+1` read is kept separate and its downstream meaning is not
claimed. All three operations bind the callback source to the distinct
`0x450158a8` object.

The two already captured source windows remain valid raw observations of the
ordinary AP_EXCO blocks:

- `0x4500ff14/16` returned all zero. It does **not** match the complete
  selected packaged 16-byte prefix, which contains `1` at offset `+8`.
- `0x450102e0/32` matches the selected packaged window exactly, including
  byte `0x14` at returned offset `+0x0c` (ordinary AP_EXCO object offset
  `+0x3d8`).

The old result's `sequential_values_match_packaged_defaults: true` compared
only byte `+0` from the first window and byte `+0x3d8` from the second. It is
not a whole-window match and, more importantly, neither window sampled the
callback's `0x450158a8` object.

## Boundary

This trace corrects pointer lineage only. It does not establish the current
bytes at `0x450158a8`, a physical unit, an active fault-time value, an active
configuration bank, or a reason to alter any configuration. No additional
read, retry, helper, write, reset, protection, persistence, high-bank, POFLG,
or return-guard action was performed or authorized here.

`verify-pointer-layout-followup.py` reproduces the package coordinates,
startup call/store sequence, distinct registry roots, table rows, reset
initializer, callback getter/use, and captured-window comparisons using only
the Python standard library.
