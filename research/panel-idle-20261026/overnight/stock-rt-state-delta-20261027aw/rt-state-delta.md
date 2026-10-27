# AV pre/post RT-state delta

Recorded 2026-10-27 UTC. This is a bounded offline comparison of already
retained AV raw windows and selected-package source. It made no TV, root,
network, USB, controller, reset, firmware, or native-helper call. It does not
modify the frozen AV evidence.

## Result

The accepted pre-lifecycle faulted `R` window and delayed post-lifecycle clean
`R` window differ at exactly **12 of 256 bytes**, forming 11 aligned
halfword changes. The changed state is selective:

- the source-bound fault tuple changed from `1 / 0x1001 / 0` to `0 / 0 / 1`;
- the source-bound mode-1 action bucket `+0x86` changed from `7` to `0`;
- the mode-1 record-ID latch `+0x90` changed from `41` to `0`, while the
  shared mode-4/mode-6 record-ID latch `+0x92` changed from `54` to the
  still-nonzero value `48`;
- two source-bound mode-selected scan/setup halfwords at `+0x20/+0xbc`
  changed but did not clear; and
- five source-bound threshold candidates and the mode halfword were
  byte-identical before and after.

This is evidence for clearing/evolution of dynamic RTP state without a
sampled threshold change. It is **not** evidence for a wholesale object reset:
one record-ID latch remains nonzero, several other dynamic halfwords remain
nonzero, and the clean post window is not equal to the packaged AP_RTP
initialization payload. Image 1's own reset scatter still does not initialize
this pointed-to object.

## Exact retained inputs

Both pre-X `R` brackets are byte-identical, SHA-256
`91055b0ce0f0b798a78313bd90520506f63261fa1c35d78a0de85b2d332379f9`.
Both retained post-X cycle-80 `R` brackets are byte-identical, SHA-256
`a15bcc5f51c78ccdea8283d0839533c2e5f12c243a8e351032747b729b66b477`.
Each is exactly 256 bytes.

The selected package is SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`;
the recovered stored package is SHA-256
`f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562`.
Their complete FILE `0x40000..0x7ffff` image-1 slots are byte-identical,
SHA-256
`56bfea112d161a22f5bee8630c81306bf04fa9d8d3d901c6d8e7cdd89c09dfbf`.
The field/source conclusions below therefore do not differ between those two
retained image-1 slots. This remains stored-byte compatibility, not proof of
active whole-code identity or root continuity across MODE2.

## Complete 256-byte delta

No byte outside this table changed:

| response offset | aligned interpretation | pre-X | post-X | source-bounded classification |
| ---: | --- | ---: | ---: | --- |
| `+0x00` | `u16` | `1` | `0` | common stop/event flag; common setter writes 1 |
| `+0x0a` | `u16` | `0x1001` | `0` | common fault halfword; setter writes `0x1001` |
| `+0x0e` | `u16` | `0` | `1` | ordinary gate; setter writes 0 |
| `+0x20` | `u16` | `3161` | `3138` | mode-selected scan/setup source halfword; unit unresolved |
| `+0x86` | `u16` | `7` | `0` | mode-1 action bucket |
| `+0x90` | `u16` | `41` | `0` | mode-1 record-ID publication latch |
| `+0x92` | `u16` | `54` | `48` | shared mode-4/mode-6 record-ID publication latch |
| `+0x98` | `u16` | `24` | `23` | unresolved in the bounded source slices |
| `+0xac` | `u16` | `243` | `244` | unresolved; numeric `+1` is not enough to call it a counter |
| `+0xbc` | `u16` | `3138` | `3092` | alternate mode-selected scan/setup source halfword; unit unresolved |
| `+0xca` | `u16` | `1` | `0` | unresolved; zero is not enough to call it a scan flag |

The fault halfword accounts for two changed bytes (`+0x0a/+0x0b`); every
other changed halfword differs only in its low byte. Hence the byte offsets
are exactly:

```text
00 0a 0b 0e 20 86 90 92 98 ac bc ca
```

No semantic name is assigned to `+0x98/+0xac/+0xca`. The prior bounded count
producer explicitly left `+0x2498/+0x24c8/+0x24ca` without a direct store in
that slice. A decrement, increment, or transition to zero does not supply a
field identity.

## Source bindings for the classified changes

Image-1 VA `0xc1e0..0xc211`, SHA-256
`f8a6285dd94b3338eff37ded006a2ebff6ecfe7409bef9044f34fd25cdb27102`,
stores root `+0x2400=1`, `+0x240e=0`, and `+0x240a=0x1001`. Those become
response offsets `+0x00/+0x0e/+0x0a` in the `R=bus 0x47012400` window.
This is the exact source of the faulted tuple labels.

The ordinary pre-scan body at VA `0xbad8..0xbaef` clears root
`+0x2486/+0x2488/+0x248c` before clearing two later fields. Thus
`+0x86: 7 -> 0` is compatible with ordinary pre-scan clearing and is not, by
itself, a reset signature. The separate action helper can OR bits into these
three per-mode buckets; the late faulted value `7` carried bits 0, 1, and 2.

The formatter/count producer publishes the low 16 bits of separate record
IDs at:

```text
category/mode 1       -> root +0x2490
category/mode 4 or 6  -> root +0x2492
```

The shared `+0x92` value remaining `48` after MODE2 is direct evidence against
describing all recorded latches as cleared. The source also proves that these
record-ID latches are distinct from the qualifying-count array, the delayed
history, and the accumulator. The `R` window alone therefore does not show
whether the separate `s[]`, `H[][]`, `q[]`, or `A[]` areas were cleared.

The ordinary unpacker setup at VA `0xbda2..0xbe0d` selects one of several
root pairs. One branch reads `+0x24bc/+0x24be`; the fallback reads
`+0x2420/+0x2422`. Each branch separately chooses from the source-bound
threshold halfwords. This classifies changed `+0x20/+0xbc` as mode-selected
setup/source values, but does not recover their units or their writers. Their
nonzero-to-nonzero changes are compatible with ordinary runtime refresh and
do not resemble a uniform clear.

## Threshold/configuration comparison

The known mode and threshold candidates are unchanged:

| response offset | pre-X | post-X | packaged AP_RTP payload |
| ---: | ---: | ---: | ---: |
| mode `+0x10` | `4` | `4` | `4` |
| candidate `+0x30` | `200` | `200` | `200` |
| candidate `+0x32` | `0` | `0` | `0` |
| candidate `+0x40` | `0` | `0` | `0` |
| candidate `+0xc0` | `200` | `200` | `200` |
| candidate `+0xc4` | `40` | `40` | `40` |

These exact samples rule out a retained before/after change in those five
threshold candidates. They do not rule out an unobserved transient or a
different threshold outside this source-bound set.

Image 0's packaged AP_RTP first payload for bus `0x47012400..0x470124ff`
has SHA-256
`3a16ea440b59a8e778c01ddfc429b110fbdd03e55c953954ce99337ebf5b3937`.
The pre-X window differs from it at 20 byte positions; the clean post-X window
still differs at 15. In particular, post-X has ordinary gate `+0x0e=1`, the
shared record-ID latch `+0x92=48`, and multiple other live values absent from
the payload. Some fields moving to zero happen to equal packaged zeros, but
the complete mismatch prevents calling the post window a replayed
initialization template.

Image 1 supplies an even firmer reset boundary: its reset scatter establishes
the pointer to this object but does not populate the object. Therefore no
known image-1 reset byte template exists for this 256-byte comparison.

## What this changes in the diagnosis

The new paired raw evidence is more specific than “faulted became clean”:

1. The fault tuple and mode-1 action bucket no longer remain latched in the
   delayed post state.
2. At least one record-ID latch did **not** clear; it evolved to another
   nonzero value. Other dynamic scan/setup values also evolved.
3. The five recovered threshold candidates and mode field did not change.
4. The post window is neither the selected AP_RTP payload nor proof of an
   image-1 reset initialization.

The strongest bounded interpretation is therefore **selective dynamic-state
clearing plus later ordinary evolution, with stable sampled thresholds**.
MODE2 is associated with this delayed difference, but the nine-minute gap,
missing reset-domain receiver, possible ordinary writers, and absence of a
physical picture observation prevent assigning the exact transition to a
reset or declaring recovery.

## Reproduction

Run locally only:

```text
python3 rt-state-delta-reproduce.py
python3 -O rt-state-delta-reproduce.py
```

The standard-library checker pins both pre/post bracket pairs, both complete
firmware files, full image-1 slot equality, exact source slices for the common
setter/action clear/record-ID publishers/unpacker setup, the AP_RTP payload,
all changed bytes and aligned halfwords, unchanged thresholds, and five
negative mutation fixtures. It emits one compact JSON object with
`target_operations=0` and performs no external operation.

