# Fixed aggregate-table source trace

Recorded 2026-10-27 UTC. This is a finite offline trace in the selected
package only. It made no TV, network, root, USB, device-node, firmware, UI,
or configuration operation. Image-0 coordinates use `FILE = VA + 0x200`.
The selected 5 MiB package has SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.

## Result

The fixed source rooted at `0x584109a4` is positively used as four adjacent
lanes of sixteen 32-bit words each:

```text
lane 0  0x584109a4 .. 0x584109e3
lane 1  0x584109e4 .. 0x58410a23
lane 2  0x58410a24 .. 0x58410a63
lane 3  0x58410a64 .. 0x58410aa3
```

Thus the minimum positively used span is `0x100` bytes, with a `0x40`-byte
lane stride. This extends W's three-lane aggregate view: several routines use
the first three lanes, while two additional paths explicitly copy the fourth
lane from the separate literal `0x58410a64`.

Every direct selected-image consumer found through the exact base literals
reads the source. The two package copy operations also use the source as the
copy input, not its destination. No direct firmware writer to this table was
found in the bounded literal/immediate census. The selected package does not
name the individual lanes or fields, but it does provide a positive enclosing
package-record association: both the table and companion lie inside the
address range of metadata record `Pre-PD`. This association does not identify
the table's producer or units and is not evidence that the table is immutable
or hardware-generated.

## Positive enclosing package record: `Pre-PD`

The complete 512-byte selected-package record at FILE `0x80600..0x807ff`
has SHA-256
`11696518d668a8c2ac409a0cf2d7a7e462f2e410bba6e5a0747007618e2ec87f`.
Its first 32 bytes are `Pre-PD` followed by zeros. At the metadata offsets
already used by the independently reviewed `EXCO_PAR2_S0` association, it
contains:

| record offset | exact value | bounded description |
| ---: | ---: | --- |
| `+0x20` | `7` | metadata type word |
| `+0x24` | `0x58410000` | metadata address word |
| `+0x28` | `1` | metadata count word |
| `+0x2c` | `0x8000` | first-group source offset relative to package configuration base FILE `0x80000` |
| `+0x6c` | `0` | first-group destination offset added to the metadata address base |
| `+0xac` | `0xab0` | first-group copy length / metadata address-range size |

The corresponding half-open package-record address range is therefore
`[0x58410000, 0x58410ab0)`. The containment arithmetic is exact:

```text
companion  [0x58410178, 0x584101b8)  is inside Pre-PD
table      [0x584109a4, 0x58410aa4)  is inside Pre-PD
```

The table ends twelve bytes before the metadata range ends. The neighboring
FILE `0x80400` record is named `OSD`, with address `0x58400000` and size
`0x40`; it does not contain either source.

The selected ordinary type-7 loader semantics use `+0x28` as count,
`+0x2c` as the source-offset array entry added to the configuration base,
`+0x24` as the destination base, `+0x6c` as its added destination offset, and
`+0xac` as length. These meanings were decoded manually from the selected
type-7 dispatch and loader and confirmed by independent disassembly; they are
not a dynamic loader execution. The checker binds the exact reviewed slices
at VA `0x7586..0x75a1` and `0x5c74..0x5e23`. For this first group,
the described package copy is therefore:

```text
FILE [0x88000, 0x88ab0) -> CPU [0x58410000, 0x58410ab0)
```

The complete 2,736-byte packaged source payload has SHA-256
`af62caa7f38a9a6a3702901ca84aa09a9ae895f1b498cabc846e51469872ddd8`.
This is package/load-path semantics only. It does not prove that this copy
succeeded for the observed boot, that these bytes remained current, or that
software rather than a later peripheral/DMA producer updates the table.

This is the same narrow association logic used for the selected package's
`EXCO_PAR2_S0` record at FILE `0x83c00`: a named 512-byte metadata record,
its exact address word and size, and an address proven to lie within that
range. It does not name individual `Pre-PD` fields, prove the record was
loaded for the observed boot, prove a live address alias/allocation, or
identify a firmware, peripheral, or DMA producer.

## Exact literal and immediate census

The exact 32-bit value `0x584109a4` occurs five times at aligned image-0 VAs.
Each occurrence has exactly one direct Thumb literal-load reference:

| literal VA | load VA | loaded register | complete consumer |
| ---: | ---: | --- | --- |
| `0xf3a8` | `0xf20a` | `r6` | `0xf1f4..0xf3a7` |
| `0x10424` | `0x10340` | `r7` | `0x10334..0x10423` |
| `0x19330` | `0x190ae` | `r9` | `0x19064..0x1932f` |
| `0x2f970` | `0x2f612` | `r9` | `0x2f5d8..0x2f96f` |
| `0x2fb40` | `0x2fa42` | `r5` | `0x2fa38..0x2fb3f` |

The exact fourth-lane address `0x58410a64` occurs at VAs `0x5540` and
`0x2c230`. Its direct references are `0x536c` and
`0x2c0ea/0x2c104/0x2c10a/0x2c110`. The last three subtract `0xc0`, `0x80`,
and `0x40` before loading, which reaches the first word of lanes 0, 1, and 2.

The related fixed value `0x58410178` occurs at VAs `0x10428` and `0x19334`,
loaded at `0x10342` and `0x190b2`. It supplies a distinct 16-word companion
source in those two routines. It is not within the `0x584109a4` four-lane
span. It shares the positive enclosing `Pre-PD` association, but has no
positive individual field name in this trace.

No Thumb `MOVW`/`MOVT` instruction in image 0 contains the exact target low
halves `0x09a4` or `0x0a64`, or the high half `0x5841`. The broader literal
`0x58400000` occurs twice; its direct sites `0x70a2` and `0x1f3ca` store only
at offset zero and do not derive `+0x109a4`. These are useful bounded negative
facts. They do not exclude a pointer supplied by an unexamined caller,
multi-step arithmetic from another base, or a producer outside this image.

## Consumer dataflow

### VA `0xf1f4`: three-lane maximum/sum ratio

This complete routine has SHA-256
`ede08927ce58e699ad253a0efd29be471d673259035344a7d83b64d60d4a91e0`.
Its nested loops select lanes `0..2` and words `0..15`; the only access
through the loaded source base is the `LDR.W` at `0xf238`. It accumulates a
64-bit sum and a maximum for each lane, derives three ratios, chooses among
them, and stores results in the named `NPC_AP` record at offsets `+0x1de` and
`+0x1e0`. That names the consumer record, not the table.

### VA `0x10334`: three-lane cumulative thresholds

This complete routine has SHA-256
`12d4d300b3402aab6bb23d31744b4bc9a1babb12698075c45fdd399c872c0dc2`.
It reads the fixed source at `0x1037c/0x10392` and the distinct companion
`0x58410178`, builds cumulative values for three 16-word lanes, and writes
three halfwords at named record `AP_SPC+0x5a..+0x5e`. It does not store
through the fixed source pointer.

### VA `0x19064`: all four lanes

This complete routine has SHA-256
`d6e9d5f5d129583ba1b248b790c947558e6759bd49371ec3ebe7f9832bff842a`.
It reads the first three lanes at `0x190e2`. It separately reads words
`0x30..0x3f` relative to the source at `0x1912a`, which is exactly lane 3.
It also uses the companion `0x58410178`. The routine has a positive `NPC_AP`
consumer edge. It separately obtains the selected-package literal root
`0x47010000`; its lane-3 stores resolve to `0x47013adc..0x47013b18`. That is
not a positive `AP_RTP` edge: the registry's `AP_RTP` row starts at
`0x47012400` with extent `0x100`, and no runtime alias or containing
allocation is proved here. The `0x47010000` context therefore remains
unnamed in this report.

### VA `0x2f5d8`: W's three aggregate lanes

This complete body has SHA-256
`428c93783eeb93bec0a363d29043bca4c8aecdbf5e7339542ccd5c70ba537b45`.
Its table reads are `0x2f662` and `0x2f7a6`. This is the W helper that sums
selected high-index tails of the first three lanes and mirrors the results
into named record `AP_EXCO`. W proved the summation bounds and captured
mirrors; it did not capture these fixed source words themselves.

### VA `0x2fa38`: terminal words of three lanes

This complete body has SHA-256
`0275a3f5b85be051f4b4a48a2759b9cf8005ffdc96e6b7f26e1c5735274cfb56`.
It loads fixed-source offsets `+0x3c`, `+0x7c`, and `+0xbc`, the last 32-bit
word in each of lanes 0 through 2, and copies their halves into named record
`AP_EXCO+0x2d8..+0x2e2` before evaluating its already documented condition.
All three operations are loads.

## Explicit copies of lane 3

The selected image's copy routine at VA `0x0afc..0x0b5f` has SHA-256
`dcedcf9312a0399a79b51da6a240a74c79a4ccfd6f2a6c429f279769db6229ba`.
Its calling convention in both relevant paths is `r0=destination`,
`r1=source`, `r2=length`.

| call preparation | source | destination | length | named consumer context |
| ---: | ---: | ---: | ---: | --- |
| `0x536a` | `0x58410a64` | selected-package CPU literal `0x2000b4e0` | `0x40` | `AP_AG` routine `0x5324..0x553f` |
| `0x2c0e8` | `0x58410a64` | stack `sp+0x0c` | `0x40` | `AP_AG` routine `0x2c080..0x2c22f` |

The first path's instruction bytes make `0x2000b4e0` the copy destination.
That is a selected-package CPU literal, not proof of a live alias, allocation
extent, or current contents. The second copies lane 3 to a local stack array
and then sorts/uses it. Neither is a writer to the fixed source. The first
three lanes are also read by the second routine through the
subtract-from-`base+0xc0` loads noted above.

## Named provenance and the remaining gap

The selected package's ordinary registry and tiny getters positively tie the
RAM records `NPC_AP`, `AP_SPC`, `AP_EXCO`, and `AP_AG` to consumers above.
This is useful consumer provenance. The separately checked `AP_RTP` registry
row does not cover the `0x47013adc..0x47013b18` stores, so it is deliberately
not listed as a named consumer.

Separately, the package metadata supplies positive **enclosing source
provenance** through `Pre-PD`. Across the seven complete pinned consumer
bodies there is still no direct printable string reference, and the fixed
addresses do not appear as named rows in the ordinary RAM-record registry.
The `Pre-PD` association does not positively call the individual table a
histogram, RGB table, pixel table, DMA buffer, or named field/register bank.
Its record name and address containment are the supported naming boundary.

The strongest supported statement is therefore:

- four 16-dword lanes at `0x584109a4` are consumed by several ordinary
  calculations;
- the table and `0x58410178` companion lie within the selected package's
  named `Pre-PD` metadata address range;
- the fourth lane is explicitly copied outward twice;
- all fixed-base consumers in the exact literal census are readers;
- no direct writer, individual field meaning, or runtime producer is
  identified in this bounded pass.

This leaves hardware/firmware producer, update cadence, units, and relation
to displayed content unresolved. A peripheral, DMA engine, interrupt path,
computed/passed pointer, or code outside the selected image is not excluded.
The separate ordinary `0x13464 -> 0x2fb44` invocation/cadence branch is
outside this source-provenance trace. Nothing here changes W's
“histogram-like/content-dependent” label from a testable hypothesis into an
identity or physical-cause conclusion.

## Reproduction

`trace-table-source.py` uses only Python's standard library. It pins the
selected package, W starting evidence, and the earlier analogous
`EXCO_PAR2_S0` analysis; checks the full `Pre-PD`, `OSD`, and
`EXCO_PAR2_S0` records, metadata fields, address containment, literal
inventories, Thumb literal references, absence of exact `MOVW/MOVT` halves,
broader-base sites, complete consumer hashes, exact read instructions, two
copy edges, copy implementation, named registry rows/getters, and direct printable
references through 16-bit `ADR` plus positive/negative 16- and 32-bit
PC-relative literal loads. The automated checker does not decode `ADR.W`.
Independent complete-body disassembly found no `ADR.W` in the seven bodies;
their only 32-bit PC-relative source-base loads are `0x190ae` and `0x2f612`,
both resolving to the fixed non-printable constant. This states the manual
and automated coverage separately rather than treating the narrower checker
as a whole-instruction-set proof. Normal and optimized executions are
required to emit byte-identical JSON with `target_operations:0`.
