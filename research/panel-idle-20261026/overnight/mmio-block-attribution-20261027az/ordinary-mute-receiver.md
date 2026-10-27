# Selected-image ordinary mute receiver and fixed register blocks

Recorded 2026-10-27 UTC. This is a bounded offline trace over the retained
selected QD profile and copied QDF host module. It made no TV, root, network,
USB, I2C, controller, MMIO, UI, power, reset, helper, firmware, or protection
request.

## Result

The host's ordinary named panel-mute command **does** have a positive mapping
through the retained selected image-0 `F3:00` parser for selector `0x164`.
The mapping is not the previously discussed `F3:80` status table and is not a
single symmetric set/read register:

* the `F3:00` read case for selector `0x164` directly reads the word at fixed
  address `0x58200060`, extracts bits 22..23, and returns one only when that
  two-bit value equals two;
* the `F3:00` write case for selector `0x164` accepts scalar zero or one and
  calls an internal routine carrying the exact format literal
  `Failmode:%d\n`;
* that routine changes bits in the distinct derived `MULTI/AP_EXCO` RAM object
  at CPU `0x200158a8 + 0x80`; on scalar zero it first copies two saved RAM
  words to fixed addresses `0x58300018` and `0x58300000`.

This provides a source-backed association between the host's named mute
readback and an unnamed fixed `0x58200000` register block, and between the
zero/unmute setter path and a separate unnamed `0x58300000` block. It does
not prove that either block directly drives OLED light, that the read
predicate is the electrical mute bit itself, or that the selected package was
the code executing during any owner-observed blackout.

## Exact inputs and coordinate correction

| input | SHA-256 |
| --- | --- |
| selected 5 MiB profile `../selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin` | `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0` |
| copied host module `../../binaries/qdf_tcon.ko` | `97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63` |
| prior RT-status report | `6c532e2ad8a48041cf83ebddfa42af1282019d14169902b47e621f6a1c237f6e` |
| corrected image load-map audit | `f69c2b74859d1015ec37ddb2cf9f316b22b5c44eb8fd8a5722c5757a3faa810b` |
| host mute-readback correction | `b8e489feff3c34de0036841ac1de36d4eac85f84c5046a8b69499b9236d158a1` |
| receive/write framing report | `2fd6029d587022c839a2655108c977ed0108e2835a7069d590b2ac7ac4da7664` |
| derived-object provenance | `50b17b0f93ecf8982e158193b5b1637f91d74b84c941cf5cc6f5fb744d2d9f40` |

The corrected image-0 coordinate rule is `stored FILE = linked VA + 0x200`.
All linked addresses below use that correction. Fixed RAM/register literals
are not shifted.

## Host command identity

In the hash-pinned QDF module, exported `QDFTcon_t_Tcon_SetMute` constructs
packed command `0xf30000000164` for its sends. Its zero/unmute path also
constructs the same command at `.text+0xcfa0..0xcfac` and calls the four-byte
read helper. The lower helper serializes it as:

```text
F3 00 00 00 01 64
```

The actual `.text+0xcfa8` instruction is `movk x0,#0xf300,lsl#32`; the older
panel-mute report's `F3 80 ... 01 64` read description is superseded by the
dedicated host-wire correction. The vendor function name and its zero/one
arguments establish the host-side panel-mute semantic. They do not by
themselves establish the controller implementation.

## Read receive/decode path

The low-level state machine is linked `0x128c4..0x12bbe`, stored FILE
`0x12ac4..0x12dbe`. For mode zero it assembles the first two bytes into
command halfword `0xf300` and the next four bytes into selector word
`0x00000164`. On the read phase, the transmit route calls linked dispatcher
`0x21624(command, selector)`.

The dispatcher compares the command with `0xf300` and calls linked getter
`0x2174c` with the selector. Selector `0x164` is aligned and falls in the
getter's first bounded range. Its index and signed table entry are:

```text
index = (0x164 >> 2) - 9 = 0x50
table entry FILE 0x21af0 = +0x57c
table PC linked 0x217b0 + 0x57c = linked target 0x21d2c
```

The target at linked `0x21d2c`, stored FILE `0x21f2c`, is exactly:

```text
ldr   r0, =0x58200000
ldr   r0, [r0, #0x60]
ubfx  r0, r0, #22, #2
cmp   r0, #2
bne   zero
movs  r0, #1
b     common_return
zero:
movs  r0, #0
b     common_return
```

Thus the selected package's reply word is the normalized predicate:

```text
1 iff ((*(u32 *)0x58200060 >> 22) & 3) == 2
0 otherwise
```

A returned zero collapses raw states zero, one, and three. It therefore does
not prove that the two source bits are clear, nor does it by itself prove that
the panel is physically emitting light.

## Write receive/decode path

When four data bytes follow the six-byte header, the same state machine
assembles the big-endian scalar and calls linked write ingress `0x2c5f4` with
`(command=0xf300, selector=0x164, scalar)`. The `f300` branch passes selector
and scalar to linked writer `0x2c71c`.

The writer has real entry gates: gate byte `0x200008e8 == 1` returns before
the table; value two enters its separately constrained special gate. A
successful Linux transfer does not prove this selector-specific case ran.
On the normal table route:

```text
index = (0x164 >> 2) - 9 = 0x50
table entry FILE 0x2caf4 = +0x656
table PC linked 0x2c7b4 + 0x656 = linked target 0x2ce0a
```

The target performs:

```text
if scalar == 1: call 0x3a078(1)
else if scalar == 0: call 0x3a078(0)
else: no call
return through the common writer tail
```

Linked function `0x3a078` passes the exact literal `Failmode:%d\n` and the
incoming scalar to the internal event-log formatter. It gets the derived
object at CPU `0x200158a8`; its hash-pinned registry row names the pair
`MULTI` / `AP_EXCO` and gives extent `0x3ec`.

For scalar one, the routine forces bits 3 and 2 in the word at derived object
`+0x80`. For scalar zero, it first calls linked `0x20770`, clears bit 3,
clears word `0x20000ed8`, and forces bit 2 in the same staged word.
`0x20770` performs the two direct copies:

```text
*(u32 *)0x58300018 = *(u32 *)0x20000d40
*(u32 *)0x58300000 = *(u32 *)0x20000d4c
```

No direct store to `0x58200060` occurs in this bounded setter chain.
Conversely, the getter does not read the staged `MULTI/AP_EXCO +0x80` word.
The trace therefore supports an associated command/status mechanism, not a
claim that one register is simply written and read back.

## Existing late snapshots do not retain the setter's immediate bit pattern

The derived-object reads already retained in W, AK, and AW each cover all
`0x3ec` bytes and passed their recorded transport and pointer-match gates.
Their exact derived-object results are:

| retained capture | raw SHA-256 | little-endian word at `+0x80` |
| --- | --- | ---: |
| `ap-exco-input-snapshot-20261027w/capture-once` | `de263b1ebda47b3d1c306f87017b4961e1f25473d43b7ee7964345002b3a90f0` | `0` |
| `npc-ap-divisor-snapshot-20261027ak/capture-ordinary-after` | `de263b1ebda47b3d1c306f87017b4961e1f25473d43b7ee7964345002b3a90f0` | `0` |
| `stock-rt-state-delta-20261027aw/post-lifecycle-inputs` | `eb15688aac78bcaf6ca12d34249898b355df5d4f7332b97e9d9b325852be4694` | `0` |

Therefore bits 3 and 2 were both clear in all three late samples, including
the post-stock-lifecycle sample. That is useful only as a retained-state
negative: the exact immediate post-call pattern of `0x3a078` (bit 2 forced
one in both branches) was not present when these later reads occurred.

It is not evidence that no mute request ran. The word may be transient or
consumed/cleared, the conditional CPU-to-bus object interpretation may not
bind the executing core, and selected-package execution remains unproved.
All three capture records explicitly say event time was not inferred, the
samples were sequential rather than atomic, and no physical picture was
observed. Accordingly this word is not a measured light state or a reliable
persistent mute-intent mirror.

## `F3:80` is a separate family

The earlier RT-status work established an `F3:80` selector table with 35
valid entries and a bound `selector < 0x23`. Feeding `0x164` to that table
would be rejected. That does not contradict the result here: the exact host
mute readback is `F3 00 00 00 01 64`, and dispatches through the larger
`F3:00` table. Treating it as `F3 80 ... 01 64` was the earlier host-wire
error corrected by the dedicated mute-readback report. No controller-side
`F3:80`-to-`F3:00` normalization is inferred; the prefix change is a
source-backed correction to the older host description.

## Limits

This finite trace proves selected-package control/data flow, not current
execution or physical causality. It does not prove:

* whole running-controller equality with the selected package;
* the vendor name or electrical purpose of either fixed register block;
* that the `Failmode` staged word was consumed after a particular request;
* that host transport success passed the controller writer's internal gates;
* that readback zero means unmuted output rather than one of three collapsed
  raw states; or
* that this command caused or repaired any recorded blackout.

It does positively exclude the proposed `F3:80` interpretation for the exact
host mute transaction and supplies the missing ordinary `F3:00` mapping.

## Reproduction

Run locally only:

```text
python3 ordinary-mute-receiver-reproduce.py
python3 -O ordinary-mute-receiver-reproduce.py
```

The standard-library checker verifies both retained file identities, the
corrected-coordinate slices, both selector-table entries and targets, the
read predicate literal/leaf, the write leaf, the `Failmode` literal, the
derived-object registry, and the scalar-zero fixed-address copies. It performs
zero target operations and constructs no transport request.
