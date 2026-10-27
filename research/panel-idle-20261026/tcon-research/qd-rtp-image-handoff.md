# QD profile image 1 → image 0 RTP/RT field handoff check

Recorded 2026-10-27 UTC. This is an offline examination of the already
retained selected profile. It made no TV, root, network, controller, firmware,
or process call, and does not identify a value to change.

## Result

The proposed cross-image handoff is **not proved**. The two routines use the
same *field displacement* (`+0x240a`), but their recovered object roots are
not statically the same:

| Image and operation | Exact root sequence | Effective target |
| --- | --- | --- |
| image 0 live RT check | `0xf194: ldr r0,[pc,#0]; bx lr`; word at `0xf198` is `0x47010000` | byte at fixed address `0x4701240a` |
| image 1 RTP event setter | `0x3afc: ldr r0,[pc,#4]; ldr r0,[r0]; bx lr`; word at linked `0x3b04` (stored `0x43b04`) is `0x200004e0` | halfword at `[*0x200004e0 + 0x240a]` |

Thus image 1 would set the byte tested by image 0 only under an unobserved
runtime condition: while the two images are executing in a shared address
space, the RAM word at `0x200004e0` would need to contain `0x47010000` (and
the relevant code would need to execute in an order that preserves the write).
The retained file does not establish that condition. Equal structure offsets
are not evidence of a common structure.

## Inputs and address convention

The sole input was the retained ordinary file:

```text
overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin
SHA-256 bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0
```

The prior container audit identifies two independently linked Thumb images:

| Component | Stored bytes | Linked addresses | vector table / reset |
| --- | --- | --- | --- |
| image 0 | `0x00000..0x3ffff` | linked base zero | stored/linked `0x200`; reset `0x345` |
| image 1 | `0x40000..0x5ffff` | stored offset minus `0x40000` | stored `0x40200`, linked `0x200`; reset `0x369` |

Both vector tables start with the same nominal initial stack pointer
`0x20020000`, but their reset and exception vectors differ. That is evidence
of two separately linked images, not evidence that they run concurrently or
share application objects.

## Exact image-0 check

The coherent image-0 main-loop block at `0x39de0..0x39df0` directly calls the
following checker at `0x39de8`:

```text
216d4  push    {r4,lr}
216d6  bl      0xf194
216da  mov     r4,r0
216dc  movw    r0,#0x240a
216e0  ldrb    r0,[r4,r0]
216e2  and     r0,r0,#1
216e6  cbz     r0,0x216f6
216f0  movs    r0,#0x10
216f2  bl      0xb860
```

Its helper is deliberately simple:

```text
0f194  ldr     r0,[pc,#0]
0f196  bx      lr
0f198  .word   0x47010000
```

So this check reads the low bit of the byte at **fixed** address
`0x4701240a`; if set, it takes the existing image-0 error path with selector
`0x10`. This report does not assign hardware semantics to the `0x47010000`
range.

## Exact image-1 setter

Image 1's root helper is materially different:

```text
03afc  ldr     r0,[pc,#4]
03afe  ldr     r0,[r0]
03b00  bx      lr
03b04  .word   0x200004e0
```

At `0xc3e0`, the local RTP event routine calls it and writes several fields:

```text
0c3e4  bl      0x3afc
0c3ea  movs    r1,#1
0c3ec  movw    r0,#0x2400
0c3f0  strh    r1,[r4,r0]
0c3f4  movw    r0,#0x240e
0c3f8  strh    r1,[r4,r0]       ; r1 was set to zero at 0xc3f2
0c3fa  movw    r1,#0x1001
0c3fe  subs    r0,r0,#4         ; r0 = 0x240a
0c400  strh    r1,[r4,r0]
```

The final store is little-endian halfword `0x1001`; if `r4` were the same
base as image 0's fixed base, it would make the image-0 low-byte bit test true.
But the instructions establish only `r4 = *(uint32_t *)0x200004e0`, not that
equality.

## Root and handoff audit

I performed bounded raw-word and adjacent Thumb `movw`/`movt` scans over each
of the two recovered image ranges:

* `0x200004e0` occurs as a little-endian word only at image-1 linked `0x3b04`.
  No adjacent `movw`/`movt` construction of that complete value was recovered
  in either image.
* `0x47010000` occurs as a little-endian word in image 0 (including the
  `0xf198` getter literal), never in image 1. No adjacent `movw`/`movt`
  construction of that complete value was recovered in either image.
* Neither image contains the literal `0xe000ed08` (the standard Cortex-M VTOR
  register) as a four-byte value. This is not proof that no bootloader or
  external component remaps vectors; it means this retained pair does not
  itself provide that simple static VTOR handoff evidence.

This bounded search is not a complete writer census. A writer could compute a
pointer from a different base and offset, receive it in a boot argument, or
arise from an ARMCC scatter-load/copy routine, an external loader, DMA, or an
opaque call. Nor does the missing raw VTOR literal exclude a computed remap or
hardware boot selection. It does establish the opposite of the proposed
*direct static* bridge: no recovered image-1 assignment of `0x200004e0` to
`0x47010000`, no image-1 literal reference to the fixed image-0 root, and no
image-0 literal reference to the image-1 RAM root.

## What remains unresolved

The current bytes cannot decide any of the following:

1. Which image, if either, is flashed or executing on this TV.
2. Whether a bootloader or another retained-unavailable component initializes
   RAM word `0x200004e0`, and to what value.
3. Whether image 0 and image 1 are time-multiplexed modes, concurrently active
   components, or alternative payloads.
4. Whether the image-1 RTP routine at `0xc3e0` runs in the incident path.
5. Whether the host-visible RT status comes from either internal image field.

Accordingly this is neither a recovery mechanism nor an incident-cause claim.
It narrows the next valid discriminator to runtime/loader evidence that binds
`[0x200004e0]`, an explicit cross-image loader/copy path, or a demonstrated
execution mode—not another inference from `+0x240a`.

