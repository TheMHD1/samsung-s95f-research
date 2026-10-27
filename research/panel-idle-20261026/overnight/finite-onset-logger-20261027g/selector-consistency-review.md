# Independent selector-consistency review

Reviewed offline on 2026-10-27. No TV, network, root, USB, controller, UI,
firmware, or other target operation was made. This review used the retained
captures and selected package only.

Pinned inputs:

- `rtp-selector-consistency-after-v6.md`:
  `4d11034d497dfa3b19f1c7dbf4517e69d6ea613193361dc0eeddd5fa616e34d9`
- `rtp-selector-consistency-after-v6.py`:
  `3c9e65fdf72094f5040a569329728d9a3157e480f2c9a0862367ba66cae9ec1b`

## P2 — the verifier does not actually census positive-immediate `STRH`

`direct_stores_covering()` uses first-halfword mask `0xf820` for `STRH`.
That mask selects Thumb-2 register/post-index halfword-store forms; the
positive `imm12` `STRH.W Rt,[Rn,#imm12]` form used by the claimed census has
mask `0xf8a0`. Consequently the pinned verifier does not, by itself, prove
the report's statement that no direct positive-immediate halfword store
covers fixed-context offset `+0x6c6`.

I independently repeated the finite selected-image scan with the corrected
`0xf8a0` mask. It also found no store whose two-byte destination span covers
`+0x6c6`; the existing `STRB` and word-`STR` scans likewise return none.
Thus this is a reproducibility/evidence-checker defect, not a contrary writer
or a change to the bounded interpretation. The report already correctly
leaves computed-address, indirect, interrupt, bulk/DMA, other-processor, and
external producers unresolved.

## Bounded conclusion

No P0/P1 issue was found in the numeric or lifecycle interpretation. Direct
instruction review confirms:

- `0xc27c..0xc2a2` updates the selector mirror and sets the companion only
  when the selector changes; the equality branch skips both stores;
- `0x1c12c` returns on companion zero, otherwise increments it on either
  qualified path and clears the small progress value after it becomes three,
  so the documented `1 -> 2 -> 3 -> 0` path can leave mirror `1` with
  companion `0`;
- direct calls at `0xb682` and `0xb828` target `0x1c12c`;
- startup writes `0x5c` to `AP_EXCO+0x36` and polls fixed-context `+0x6c6`
  for `0x5c`, but these instructions do not identify the producer of the
  observed context byte; and
- late mode `1`, selector `1`, score `44`, and candidate threshold `40` are
  numerically compatible. The separated late samples, zero scan gate, and
  conditional bus/CPU interpretation do not establish V6 event-time mode,
  predicate inputs, causality, or a general bus alias.

The verifier produced identical JSON under normal Python and `python3 -O`.
The P2 mask gap should be corrected or carried as an explicit erratum before
the script is described as mechanically proving the complete three-width
direct-immediate store census.

## Closure

The P2 finding was corrected before publication. The superseding inputs are:

- `rtp-selector-consistency-after-v6.md`:
  `670c1177931628957d5121f8562f86b4a3624ece3547e2f40e855178b2fd5c11`
- `rtp-selector-consistency-after-v6.py`:
  `c092d4ac3ce7830959d441ddc7e45f1005429490d6ad77fe10c114de1186ee1c`

The scanner now uses the correct `0xf8a0` Thumb-2 positive-`imm12` `STRH`
mask. Its new positive control requires exactly the instruction at VA
`0x17984`; independent decoding gives `a4 f8 c0 06`,
`strh.w r0,[r4,#0x6c0]`. The corrected scan then returns no direct store
covering `+0x6c6`. Normal and optimized verifier runs again produced
identical JSON. The P2 finding is closed, with no remaining P0/P1/P2 finding
in this bounded review.
