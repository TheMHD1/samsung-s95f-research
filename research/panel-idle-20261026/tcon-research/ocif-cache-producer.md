# OCIF cached-lock byte: static producers and lifecycle paths

This is an offline analysis of exact copied `sdp_ocl.ko`; it did not invoke a
getter, setter, callback, or any TV control. It resolves the byte returned by
`sdp_ocif_lock_get`, but does not establish a physical SerDes lock, a display
state, or a cause of the reported blackouts.

## Exact scope

| Input | SHA-256 |
|---|---|
| `overnight/serdes-ocif-copy-20261026/sdp_ocl.ko` | `80b9e66f4129a31207f1eee8d7636d7565193ecf9ba87e3bded6196c5e1b02e7` |
| Pinned ELF `Source` reader `sdp-hdmi-cell-gate-reproduce.py` | `8c97cb7cfed4b0e8694725e7017625b363b772f132ad3aaae32ccd699de28c67` |

All addresses below are section-relative ARM64 ELF offsets. The verifier
hash-checks both inputs before decoding.

## Getter and object identity

`sdp_ocif_lock_get`, `.text+0x90`, size 28, relocates its `adrp`/`ldr` pair at
`0x90/0x94` to module `.bss+0` (`serdesData`). A non-null pointer causes
`ldrb w0, [x0,#0xb8]` at `0x9c`; null returns `-1`.

The local `sdp_serdes_probe`, `.text+0x2f40`, size 2068, allocates its object
into `x28` at `0x2f74`, initializes `[x28+0xb8]` to zero at `0x2fb8`, and
stores that exact `x28` into `.bss+0` at `0x30c4`. The relocation at `0x30b8`
targets the same `.bss+0` as the getter. This is the static connection between
the getter and the probe-initialized object.

## Concrete writers, with base provenance

| Writer | Exact dataflow | What is and is not proved |
|---|---|---|
| `sdp_serdes_is_available_set`, `.text+0x2030`, size 36 | Masks `w0` to a byte; loads `.bss+0`; on non-null writes `strb w2,[x1,#0xb8]` at `0x2044`. | A direct writer to the getter's published object when `.bss+0` is non-null. No caller was observed. |
| Probe | `x28` allocation → `strb wzr,[x28,#0xb8]` (`0x2fb8`) → `str x28,[.bss+0]` (`0x30c4`). | Initial zero for the published object. Not a live observation. |
| `sdp_serdes_platform_suspend`, `.text+0xb8`, size 280 | Loads `x20=[input+0x70]` at `0xd0`, passes `x20` to `sdp_serdes_do_ocl_pwr_down` at `0x114`; that callee clears `[argument+0xb8]` at `0x4bbc`. | A static suspend-side clear for the object supplied by its caller. It is not proven that this argument is the live `.bss+0` object. |
| `sdp_serdes_i2c_check`, `.text+0x4ce8`, size 528 | Its argument is retained in `x22`; after the callback return is non-negative (`0x4e04`), it writes byte one to `[x22+0xb8]` at `0x4e0c`. | A conditional set for the supplied object, not proof of a physical lock measurement. |

The same numerical offset in another function/object is not treated as an
alias. In particular, the suspend clear has explicit argument provenance but
no captured live equality to `serdesData`.

## Resume and callback route

`sdp_serdes_platform_resume`, `.text+0x2d40`, size 512, has the direct
relocation call at `.text+0x2dec` to `sdp_serdes_i2c_check`. It reaches that
call only after its `x20=[input+0x70]` is non-null, `x20+0xb0` bit 0 is set,
the call at `0x2dc8` returns zero, and `x20+4 != 0xe`. Probe has a second
direct call at `.text+0x362c`.

`sdp_serdes_i2c_check` dynamically looks up
`SDP_OCL_I2C_AckPolling` (literal `.rodata.str1.8+0x1c70`) through
`__symbol_get` at `0x4de0`, caching the result in its own static table. Its
callback branches use request values `0x78` or `0x80` before a `0x54` call; the
return from the `0x54` invocation becomes `w19`. Only a non-negative `w19`
reaches the cache-one store. The callback implementation, its live binding,
and its actual lower-layer read semantics were not captured.

## Export and bounded caller census

`sdp_ocif_lock_get` has one `__ksymtab` export. In contrast,
`sdp_serdes_is_available_set` is a global symbol but has **no**
`__ksymtab_sdp_serdes_is_available_set` entry: it is not established as an
exported module ABI by this ELF.

The verifier scans every relocation section of this exact ELF both for the
setter symbol and for a `.text` section-symbol relocation with addend `0x2030`.
It separately examines every fixed four-byte word of every executable section
for the ARM64 direct `b`/`bl` encoding. A raw target of `0x2030` is considered
the setter only in logical `.text`; other sections have independent
zero-based section-relative offsets. No direct branch or code/data relocation
consumer was found; the unwind-metadata exception is described below. This
does not exclude indirect calls, constructed addresses, branches entered by
another mechanism, or a consumer in a module that was not copied; it is not a
general absence or execution claim.

One matching relocation is retained and classified explicitly: `.rela.eh_frame`
at offset `0x468` is the setter's unwind-frame metadata reference. It is not a
code or data consumer. The verifier requires that exact metadata entry while
requiring no other relocation-based setter reference.

The AckPolling literal is relocation-pinned at `.text+0x4d0c/0x4d14` to
`.rodata.str1.8+0x1c70`; `0x4ddc` moves its constructed `x24` address to `x0`
immediately before `__symbol_get` at `0x4de0`. The verifier checks that
register path as well as the resolver call. This is static argument
provenance, not proof that the lookup succeeded or that any callback ran.

## Corrections retained

An earlier manual interval assignment accidentally shortened `0x2dec` to
`0x2ec` and called it a remove-path call. The exact offset is inside
`sdp_serdes_platform_resume` (`0x2d40..0x2f40`); this report and verifier use
the corrected identity. Earlier discussion also called the generic setter an
export. The exact `__ksymtab` check shows it is global but not exported.

## Reproduction

```sh
PYTHONPATH=/tmp/tcon-capstone python3 ocif-cache-producer-reproduce.py
PYTHONPATH=/tmp/tcon-capstone python3 -O ocif-cache-producer-reproduce.py
```

The verifier defaults to comparison with the saved disassembly. Its optional
`--write-disassembly` creates that file exclusively and is only for creating a
missing artifact; it never overwrites an existing one.
