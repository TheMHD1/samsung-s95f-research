# Pre-PD exact cross-image reference census

Recorded 2026-10-27 UTC. This is a bounded offline census of the selected
package's image-1 nominal linked window. It made no TV, network, root, USB,
device-node, MMIO, controller, firmware, UI, playback, or configuration call
and performed no write outside this new report/checker directory.

## Result

No direct image-1 reference to the qualified `Pre-PD` source range was found
in the exact-reference forms checked.

The scan found none of the following anywhere in nominal linked image-1 VA
`[0, 0x20000)`:

- a four-byte little-endian value in `[0x58410000, 0x58410ab0)`, even at an
  unaligned byte offset;
- a Thumb-1 or Thumb-2 PC-relative literal load whose resolved word is in that
  range;
- a Thumb `MOVT` candidate with high half `0x5841`;
- a Thumb `MOVW` candidate with any of the four requested target low halves;
  or
- a Capstone-decoded `mov*` immediate equal to an address in that range.

Consequently this finite pass adds no image-1 producer or consumer edge for:

```text
0x584109a4  four-lane source base
0x58410a64  fourth-lane source
0x58410178  companion source
0x58410000  enclosing Pre-PD base
```

This is a precisely bounded negative result. It does not upgrade the earlier
image-0-only producer census into a whole-firmware absence claim. Image 1
could still receive a pointer from a caller, compute the address through a
different base/arithmetic sequence, access an unqualified alias, or rely on a
peripheral, DMA engine, boot component, or code outside this nominal window.

## Pinned package and image bounds

The only firmware input was:

| item | value |
|---|---|
| selected package | `overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin` |
| size | `0x500000` bytes |
| SHA-256 | `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0` |

Two retained descriptions use different but compatible scopes that need to
remain explicit:

- the earlier image-1 report calls FILE `[0x40000,0x60000)` the stored
  component range; those `0x20000` bytes have SHA-256
  `c97865a60fcf0112b0547d41dca99bcad79d5411f90d26f4048cab926a9c4a5f`;
- the later validated N mapping pins the full stored image-1 slot as FILE
  `[0x40000,0x80000)`, SHA-256
  `56bfea112d161a22f5bee8630c81306bf04fa9d8d3d901c6d8e7cdd89c09dfbf`,
  and corrects the coordinate to `FILE = 0x40200 + linked VA`.

Following the task's nominal `0x20000` linked span and the corrected N
coordinate, the census scans:

```text
linked VA  [0x00000, 0x20000)
stored FILE [0x40200, 0x60200)
SHA-256 d16d0a293fc889b891b15904edc22cbba1f8173012ea07eac691041a649fb675
```

This deliberately includes linked VA `0x1fe00..0x1ffff`, whose FILE bytes are
the `0x200`-byte suffix immediately beyond the older component interval. It
does not reinterpret that suffix as executable code. It only prevents the
requested nominal linked extent from being silently shortened. All scans are
raw code/data candidate scans.

The nominal extent is the only instruction-start and byte-granular raw-word
census. PC-relative literal loads starting there are allowed to resolve into
the remaining positive-VA bytes of N's pinned full slot:

```text
literal backing linked VA  [0x00000, 0x3fe00)
literal backing stored FILE [0x40200, 0x80000)
SHA-256 6fb6c9ae101fbe7c6c1fd7f46df6ef2fd9f2fbb8bc28ce23ddc38795b68c1288
```

Those backing bytes are read only when a nominal-window instruction candidate
resolves a literal there. They are not added as instruction starts or to the
raw source-word census.

Pinned reference reports are:

- `overnight/code-map-qualified-followup-20261027n/code-map-qualified-followup.md`,
  SHA-256
  `d14282ce16dac0b6a594bfdcce078170d28264c54c515f3b02ad670477901c2a`;
- `tcon-research/qd-profile-rtp-image1.md`, SHA-256
  `90230a772b149d3f56c5beecf9ebfd3546a5e488d684d6ebcd3fa97e2b502c87`;
- `overnight/ap-table-source-20261027y/table-source-trace.md`, SHA-256
  `52774f5a67d1f927a05c71dd7788da2b4601091472ac9e3230b53692c89aacdb`;
- `overnight/pre-pd-stored-values-20261027ab/stored-values.md`, SHA-256
  `31312fd987633bba78f4d9edc87c149d766181a50a5c99c01ba6be1632c7ac3f`.

## Exact census

### Raw words and literal loads

The checker interprets every consecutive four-byte slice, not merely aligned
words. Zero slices decode to a value in `[0x58410000, 0x58410ab0)`. Thus the
four requested exact values are absent as byte strings, and so are all other
complete address words in the enclosing source range.

It then tests every halfword instruction start from VA `0` through the final
start at `0x1fffe` for these literal forms:

- Thumb-1 `LDR Rt, [PC, #imm]`;
- Thumb-2 positive `LDR.W Rt, [PC, #imm]`; and
- Thumb-2 negative `LDR.W Rt, [PC, #-imm]`.

The 32-bit forms are considered only when both instruction halfwords remain
inside the nominal instruction window. Resolved literal words may lie anywhere
in the separately pinned positive-VA backing above. The census has 5,101 raw
literal-load candidates; exactly one reaches beyond the nominal window:

```text
LDR16 candidate VA 0x1ff3e -> literal VA 0x20000 / FILE 0x60200
resolved word 0x00000000
```

The final nominal halfword at VA `0x1fffe` is also examined as an instruction
start; its value is `0x0000`, so it is not a literal load. No resolved literal
word, inside or outside the nominal window, falls in the Pre-PD source range.
The byte-granular source-word absence remains a statement about the nominal
window only; the larger backing is qualified separately as literal-pool data.

### `MOVW` / `MOVT` and other exact moves

The raw halfword scan decodes every candidate Thumb `MOVW` and `MOVT` encoding.
It finds:

- zero `MOVT #0x5841` candidates;
- zero `MOVW` candidates for low halves `0x09a4`, `0x0a64`, `0x0178`, and
  `0x0000`; and
- 38 unrelated `MOVW` candidates whose immediate happens to lie in
  `0x0000..0x0aaf`.

Those 38 low values cannot construct a source-range address through the
checked `MOVW`/`MOVT` form because the required high-half candidate is absent.
They are not classified as references.

As an independent instruction-decoder check, Capstone 5.0.7 decodes one
candidate instruction at every halfword offset and searches all `mov*`
immediate operands for the full address range. It also returns zero. Because
this deliberately decodes data as possible instructions, any positive would
still require code-flow qualification; the zero result is only a raw encoding
absence within the stated forms.

## Mapper and alias boundary

The positive image-1 mapper at VA `0x1bb74` does not qualify an alias for this
source. Its recovered domains cover low linked addresses and
`0x20000000..0x2001ffff`, mapping them into `0x44/0x46...` code views and
`0x45/0x47...` RAM views. Input `0x58410000..0x58410aaf` is outside those
domains, and none of the mapper's qualified output ranges is this `0x5841...`
range.

Accordingly no mapped alias was added to the census. Numeric symmetry or an
unreviewed address translation would not be positive alias evidence. This does
not exclude another mapper or hardware alias that is absent from the reviewed
ordinary path.

## Relationship to the image-0 census

The earlier Y trace positively identifies image-0 readers of the four-lane
source and companion, plus two outward lane copies. Its exact literal pass did
not find a direct image-0 writer. AB further shows that the packaged table
bytes are zero while later mirrored values are nonzero, leaving a runtime
refresh/source gap.

The present image-1 pass does not close that gap: no exact source reference
exists to follow into an ordinary image-1 producer or consumer. It only rules
out the most direct cross-image edge in this selected nominal range. It does
not inspect or enter protection, return-guard, high-bank, bootloader, storage,
or persistence branches, and it makes no bypass, patch, threshold, or physical
causality claim.

## Reproduction

`verify-cross-image-census.py` uses Python's standard library plus the retained
Capstone environment. It pins the package and four source reports, verifies
the two stored-range hashes, nominal scan hash, and literal-backing hash. Its
fixtures cover byte-granular words, 16-bit literal loads, positive and negative
32-bit literal loads, a final 16-bit instruction whose pool lies outside the
instruction window, a truncated final 32-bit first halfword, and
`MOVW`/`MOVT` decoding. It then emits one compact JSON object.

```sh
PYTHONPATH=/tmp/tcon-re-capstone python3 \
  overnight/pre-pd-cross-image-20261027ad/verify-cross-image-census.py
PYTHONPATH=/tmp/tcon-re-capstone python3 -O \
  overnight/pre-pd-cross-image-20261027ad/verify-cross-image-census.py
```

Normal and optimized executions pass and emit byte-identical JSON with
`target_operations:0`.
