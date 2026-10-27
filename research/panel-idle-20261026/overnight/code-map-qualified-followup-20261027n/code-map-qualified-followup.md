# Image-1 low-linked-address code-map qualification follow-up

Recorded 2026-10-27 UTC. This is a finite offline follow-up based on original
selected-package bytes and the retained recovered-current storage backup. It
made no TV, root, network, USB, controller, device-node, helper, memory-read,
write, reset, UI, or process-control operation. It does not modify the frozen
prior code-bus report.

## Result

The prior qualification gap is now narrowed by a positive ordinary mapping
mechanism that the frozen report did not include. Image-1 mapper VA `0x1bb74`
explicitly covers low linked addresses, before its RAM cases:

```text
address == 0                         -> 0
selector == 0, address < 0x40000    -> address + 0x44000000
selector != 0, address < 0x20000    -> address + 0x46000000
```

The selector-nonzero branch positively maps the known predicate linked range
`0x1e68..0x203f` to bus range **`0x46001e68..0x4600203f`**. This is not an
extension from a `0x4700....` RAM alias or numeric symmetry. It is the exact
decoded low-address branch of a mapper that ordinary configuration lookup
code calls and whose returned pointers it dereferences.

Three fixed selector-1 code-fingerprint windows are therefore qualified as
source-grounded potential target-`0x101` reads:

```text
0x46001e60 / 0x200  predicate neighborhood
0x460038c0 / 0x040  neighboring getters, including complete VA 0x38e8
0x4601bb60 / 0x240  mapper, lookup wrappers, roots, and startup initializer
```

The essential identity limit remains: **the mapper's selector value 1 is not
proved to mean “the currently executing stored image-1 component.”** In fact,
the finite direct ordinary startup path in stored image 1 invokes these lookup
wrappers with selector 0. No direct selector-1 invocation is present in the
bounded call census. Thus the `0x4600....` mapped-code domain is positive,
while selector-1/current-image-1 core identity and actual execution remain
unproved.

## Pinned stored images

| retained file | size | SHA-256 |
| --- | ---: | --- |
| selected `F_RSM1_BN9659934B_COMMON.bin` | `0x500000` | `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0` |
| recovered-current `fixeddata.bin` | `0x500000` | `f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562` |

Their complete stored image-1 slot, FILE `0x40000..0x7ffff`, is
byte-identical and has SHA-256
`56bfea112d161a22f5bee8630c81306bf04fa9d8d3d901c6d8e7cdd89c09dfbf`.
For this component:

```text
stored FILE = 0x40200 + linked VA
```

This proves stored-slot identity for the retained backup. It does not prove
that live executable memory equals storage or that the component is running.

## Exact low-address mapper

Mapper VA `0x1bb74..0x1bbc3`, stored at FILE `0x5bd74..0x5bdc3`, has SHA-256
`94da5bec3c7fd05448a66d3828ec420e5cb08e03cb4474a54d07570732d1fe5c`.
Its complete behavior for the relevant domains is:

| selector | input domain | returned address |
| ---: | --- | --- |
| any | `0` | `0` |
| `0` | `0x1..0x3ffff` | input `+0x44000000` |
| `0` | `0x20000000..0x2001ffff` | input `+0x25000000` |
| nonzero | `0x1..0x1ffff` | input `+0x46000000` |
| nonzero | `0x20000000..0x2001ffff` | input `+0x27000000` |
| corresponding gaps/out of range | otherwise | `0` |

The verifier exercises both ends and the first rejected value of each low
domain, plus both ends of each RAM domain. “Selector 1” below is the concrete
nonzero instance proposed for fingerprinting; the instruction branch itself
tests nonzero, not equality to one.

This is distinct from mapper VA `0x3084`, which only covers RAM
`0x20000000..0x201fffff` and consults a core-tag word. The frozen prior report
correctly refused to extend that RAM-only mapper to linked code. The positive
result here comes from a separate mapper with explicit low-address cases.

## Ordinary use makes this a code-domain mapping, not guessed arithmetic

The mapper is not an isolated constant-adder. Wrapper VA `0x1bbc4` preserves
its selector and address arguments and directly calls `0x1bb74`. Lookup VA
`0x1bc4c` uses that wrapper to map a table-root linked address, dereferences
the returned pointer, then maps table-held linked pointers before comparing
names and returning rows.

The three lookup wrappers have exact linked table-root literals:

```text
VA 0x1bbd4 -> root literal 0x00010000
VA 0x1bbfc -> root literal 0x00010000
VA 0x1bc24 -> root literal 0x0001000c
```

Those values are inside both low linked-address domains. The mapper therefore
defines:

| root | selector 0 | selector 1 |
| ---: | ---: | ---: |
| `0x10000` | `0x44010000` | `0x46010000` |
| `0x1000c` | `0x4401000c` | `0x4601000c` |

Lookup code subsequently performs loads through the mapped results. That
ordinary pointer consumption is the positive address-semantics edge missing
from the prior reset/scatter-only audit.

The complete mapper/wrapper/startup span VA `0x1bb74..0x1bd49` has SHA-256
`9297113c033fee2008a35f991c436e798cb1315114f09272fc37e097b7cebb54`.
The verifier separately pins mapper and wrapper subranges so a changed branch
or table root cannot be hidden by arithmetic fixtures.

## What ordinary startup says—and does not say—about selector identity

Stored image 1 has a coherent launch chain:

```text
vector FILE 0x40200: SP=0x20020000, reset Thumb=0x369
reset linked VA 0x368 -> scatter/runtime entry
runtime VA 0x2b4 directly calls application entry VA 0x1ba0c
application VA 0x1ba12 directly calls context initializer VA 0x1bcc4
```

The reset body VA `0x368..0x38b` has SHA-256
`77428a5791705e4b966092c95715a84b617dfd7f414902ff35ae2089d92c93d6`.
The runtime application-launch slice VA `0x2ac..0x2bb` has SHA-256
`b08d19cb6f498725935e2cf4acbf9b0ab11c2339d7448430cee09fdab9077cd0`.
The application/context-call slice VA `0x1ba0c..0x1ba2b` has SHA-256
`c282e390f7fd971029b3b62ef4cc00c5c0d6e6fa4b4dddcaac8cddace4d57827`.

The complete direct-call census finds:

- application entry `0x1ba0c` has direct caller `0x2b4`;
- context initializer `0x1bcc4` has direct caller `0x1ba12`;
- all seven direct lookup calls inside `0x1bcc4` immediately load
  `r0 = 0` before calling their wrapper;
- the mapper's only direct calls are inside the mapper/lookup family; and
- the lookup wrappers' direct calls are confined to this selector-zero
  initializer path.

This strongly ties the mapper and table lookups to ordinary stored-image-1
startup. It does **not** tie selector 1 to that launched component. The direct
evidence actually shows selector 0 for this packaged path. Possible indirect
or external selector-1 callers, another processor's use of these mapped
windows, boot-ROM behavior, and later-loaded code are not excluded.

Component ordinal “image 1,” mapper selector “1,” and a physical core number
must therefore remain separate labels. A matching `0x4600....` fingerprint
would establish the contents of that mapped view; it would not alone prove
which core's PC is executing there.

## Qualified fixed fingerprint geometry

Every byte of all three windows has a nonzero linked VA below `0x20000`, so
the selector-1 branch maps each entire inclusive extent without crossing its
domain boundary. Each expected window is identical in selected and
recovered-current stored image 1.

| bus read | linked VA / FILE source | content included | exact target-`0x101` header | selected expected SHA-256 |
| --- | --- | --- | --- | --- |
| `0x46001e60`, `0x200` bytes | VA `0x1e60`, FILE `0x42060` | predicate VA `0x1e68..0x203f` at response offsets `0x08..0x1df` | `01010000601e004600020000` | `8be303fddfa4aefd0f2d307f05c7522213f8017ae15b374a4fd7178aeca2bb49` |
| `0x460038c0`, `0x40` bytes | VA `0x38c0`, FILE `0x43ac0` | complete getter VA `0x38e8`, adjacent fixed-base getter `0x38f4`, and prefix of `0x38fc` | `01010000c038004640000000` | `0483a632a5e65f8eba8bd623411d6f955705d012c831eac9347e7f9564d944cb` |
| `0x4601bb60`, `0x240` bytes | VA `0x1bb60`, FILE `0x5bd60` | mapper, wrappers, table roots, startup context initializer through VA `0x1bd9f` | `0101000060bb014640020000` | `035d13a7c17ac9b303ee5739a421a84d0ceec46167d6efce13f4723fc701d9b8` |

The inclusive bus ends are `0x4600205f`, `0x460038ff`, and
`0x4601bd9f`. Each header is exactly `struct.pack('<III', 0x101, address,
length)`. If combined in one future fixed helper, the geometry is exactly six
bulk transfers: one exact 12-byte OUT header and one exact-length IN for each
row. No helper was built or executed in this task.

The known predicate itself remains the 472-byte body at selected/current
stored FILE `0x42068..0x4223f`, SHA-256
`c3afd8863cf7f6d098fe7459ef91da9fd8827662041e77cd29497dccb2aae57a`.
It is fully contained in the first proposed window.

## Interpretation of a future read

The positive mapper qualifies these addresses as selector-1 linked-code
fingerprint candidates. Interpretation must remain conditional:

- an exact hash match at one window proves that the returned mapped-view bytes
  equal the retained stored bytes for that range at acquisition;
- exact matches at all three nonadjacent windows would strongly bind the
  selector-1 mapped view to this stored image-1 build, including both fault
  predicate and mapping/initialization code;
- such matches still would not prove that a core was currently executing
  those instructions, that selector 1 names the stored component ordinal, or
  that the predicate ran during V6;
- any mismatch, short read, or transport error must be preserved as raw
  evidence and must not be converted into a different address guess; and
- no result from these windows identifies a safe write, patch, bypass,
  threshold, protection, persistence, high-bank, POFLG, or return-guard
  action.

This result does not use or strengthen a `0x4700....`-to-code symmetry claim.
The `0x4600....` addresses arise only from the exact selector-nonzero
low-linked-address branch.

## Remaining gap

The code-domain mapping gap is closed for selector 1 and linked VAs
`0x1..0x1ffff`. The core-identity/execution gap remains:

```text
positive: selector 1 + linked VA -> 0x46000000 + VA
positive: ordinary code dereferences mapper results for linked lookup roots
positive: retained selected/current storage has exact expected code bytes
unknown:  selector 1 == currently executing stored image-1 component
unknown:  live 0x4600.... bytes equal retained storage until read
unknown:  any core PC executed the predicate during the physical fault
```

No broader loader, persistence, bank, protection, or return-guard analysis is
needed to state this finite result.

## Reproduction

`code-map-qualified-followup.py` uses only Python's standard library. It pins
both whole retained files and stored-slot equality, exact mapper and wrapper
bytes, mapping boundary fixtures, table roots, direct callers, selector-zero
startup sites, reset/application launch slices, predicate bytes, all three
window hashes, and exact target-`0x101` headers:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 code-map-qualified-followup.py
PYTHONDONTWRITEBYTECODE=1 python3 -O code-map-qualified-followup.py
```

Both modes must emit byte-identical JSON with
`status=selector1-linked-code-domain-qualified`,
`selector1_is_proven_image1_core=false`, and `target_operations=0`.
