# QD fixed RT-window reset output and image-1 root gap

Recorded 2026-10-27 UTC. This is offline replay of the retained package's
shared scatter decompressor against one additional, already identified image-0
record. It performs no controller emulation, TV/root/network access, firmware
update, or write.

## Result

Image-0 reset scatter row 9 produces exactly **`0x47bc` zero bytes** at
`0x47010000`. Its SHA-256 is:

```text
aee8a64ff7ccfaa95aa4def885fcf7d79c8f4f982d63c5efdb1686eec2cd2b6d
```

Consequently its reset value at the image-0 RT offsets is zero, including
`0x47012400`, `0x4701240a`, `0x4701240e`, `0x47012410`, and the documented
RTP-related offsets through `+0x24b4`. This gives a concrete image-0 reset
baseline, not a live-state observation.

The later AP_RTP payload is different: it supplies image-0 `+0x2410 = 4` and
`+0x24aa = 100` while retaining zero at `+0x2400`, `+0x240a`, `+0x240e`, and
`+0x24ac`. That is an independent image-0 configuration-loader provenance;
matching field positions still do not bind it to image 1.

Image 1's scatter/zero-fill sequence does **not** initialize its later root
range at `0x20010000`:

```text
first decoded block      0x20000000 .. 0x200004f8
final zero fill          0x200004f8 .. 0x2000e19c  (exclusive end)
image-1 context root     0x20010000
next scatter destination 0x20015000
```

The root lies outside every image-1 scatter destination in the nine-entry
table. The reset data does establish the pointer `*(u32*)0x200004e0 =
0x20010000`, but does not supply bytes at that pointer's target. This leaves
the root's initialization provenance unresolved: it could be a later image-1
initializer, an external/boot component, or a processor/window resource. It
is **not** proof that the root aliases image-0 `0x47010000`.

## Exact replay and validation

Both images use the same decoded handler at linked VA `0x17c`. The compact
byte decoder was first validated against the already established image-1
context record:

| Record | compressed source (file) | output | consumed source end | output SHA-256 |
| --- | ---: | ---: | ---: | --- |
| image 1 row 0 | `0x5da60` | `0x4f8` bytes to `0x20000000` | exclusive `0x5db5b` | `76bebfc83f8e286d8ae152749a1aa376d0bc8d3f415f2433d9ca6944506e7ef8` |
| image 0 row 9 | `0x3ec34` | `0x47bc` bytes to `0x47010000` | exclusive `0x3ecc5` | `aee8a64ff7ccfaa95aa4def885fcf7d79c8f4f982d63c5efdb1686eec2cd2b6d` |

The known image-1 output includes its pointer at decompressed offset `0x4e0`:
`00 00 01 20`, or little-endian `0x20010000`. The image-0 output is bytewise
equal to `b'\\0' * 0x47bc`, not merely zero at selected RT fields.

The replay follows the recovered handler's tag/literal/zero-or-backreference
format and bounds every output write to the row's declared output size. The
image-1 known answer detects an incorrect decode before the image-0 result is
accepted.

## Image-1 startup distinction

The image-1 application entry gets the context root at linked VA `0x1ba0c`
and preserves it in `r4`. In its visible entry body, after calls whose full
effects are not asserted here, the first direct root operation is a
read-modify-write of `r4 + 0x2406` at linked VAs `0x1ba54..0x1ba72`.
That is use of pre-existing root data, not a visible full-root clear/copy.

This is deliberately a limited result. The calls before that direct access,
later application code, a boot ROM, or hardware window may initialize the
root. No broad writer census was performed, and the gap must not be converted
into an alias claim.

## Consequences for the proposed bridge

The newly decoded all-zero image-0 reset window makes the two initialization
stories more precise:

```text
image 0: reset scatter zeros 0x47010000..0x470147bb
         then a separate AP_RTP loader may populate part of that window

image 1: reset scatter stores a pointer to 0x20010000
         but does not write the pointed-to root range
```

This explains why both local code paths can have similarly shaped offsets
without providing a cross-core transfer. A positive bridge still requires a
mapping/register edge, a source/destination copy or mailbox descriptor
covering both address spaces, or a controlled read-only runtime observation.

## Reproduction

[qd-rt-window-reset-output-reproduce.py](qd-rt-window-reset-output-reproduce.py)
is a bounded, hash-pinned offline checker. It passed in normal and optimized
Python modes:

```sh
python3 tcon-research/qd-rt-window-reset-output-reproduce.py
python3 -O tcon-research/qd-rt-window-reset-output-reproduce.py
```

## Provenance

| Artifact | SHA-256 |
| --- | --- |
| selected package | `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0` |
| shared decompressor bytes, image 0 file `0x37c..0x3d6` | `b475c7fd3d25463bd7fefd0f1c9e2b4790762f2725d458bdc72530247f0713fb` |
| same handler bytes, image 1 file `0x4037c..0x403d6` | `b475c7fd3d25463bd7fefd0f1c9e2b4790762f2725d458bdc72530247f0713fb` |
| image-0 row-9 compressed bytes, file `0x3ec34..0x3ecc5` | `de50c18c28008f84a91949e5a73b8214d4563e71d96b47d27dc185ca1a483d99` |
| image-1 known-answer compressed bytes, file `0x5da60..0x5db5b` | `0e31a52894540406c6c1fd1d07cc1694d245ee57aecb596ff435561a648e06d1` |
| image-1 entry prefix, file `0x5bc0c..0x5bcd0` | `4fe4c6c4f044f333ee0ff8fbe7c599410c0befae4f5b7a4e32679607d2b4883d` |

This supplement preserves and refines, but does not overwrite,
`qd-rt-window-alias-evidence-20261027.md` and the earlier handoff/context
reports.
