# Descriptor 8: packaged initializer and callback argument

Recorded 2026-10-27 UTC. This is offline analysis of the selected saved
controller package. No target, network, USB, firmware, interrupt, power or UI
operation was performed. Root wrote this report from the independent
reviewer's bounded findings and independently reproduced the decoder and
disassembled the wrapper/callback slices.

## Positive source identity

The selected image-0 reset-scatter row at package FILE `0x3e340` is
`(sourceVA=0x3e32c, destinationCPU=0x20000000, length=0xf4c, handler=0x17c)`.
Using the already-pinned decoder on FILE `0x3e52c` returns `0xf4c` bytes,
consuming through FILE `0x3e961`. The decoded initializer SHA-256 is
`685d8eda90bb3ce7e6210ad0dfe962f65ac3b8e1b2eb1a40962e0e5720d81eb3`.

The descriptor table's base is `0x20000948`, stride 20. Descriptor 8 is
therefore CPU `0x200009e8`. Its exact 20 initial bytes are
`2400225827000000000000000000000000000000`, SHA-256
`facb8521188d38789f83d3fcd1c21a7a3ec2410b20951e9a511e2edd6c9b7f55`.

| Offset | Packaged initial word | Source role |
| --- | --- | --- |
| `+0` | `0x58220024` | pointer later dereferenced by the callback |
| `+4` | `0x00000027` | interrupt-number field, signed byte read as 39 |
| `+8` | `0` | callback initially absent |
| `+0xc` | `0` | claim state initially clear |
| `+0x10` | `0` | no further role inferred here |

The selected standard vector slot at linked VA `0xdc`, corresponding to
external IRQ 39, contains Thumb pointer `0x26a91`. Wrapper `0x26a90..0x26aa5`
loads the callback from table-base `+0xa8`, skips it when zero, and otherwise
passes table-base `+0xa0` to the indirect callback. These are descriptor
8's `+8` and descriptor 8 itself, respectively.

The [BA registration trace](../mute-request-consumer-20261027ba/findings.md)
conditionally installs `0x132c1` there after claiming descriptor 8. The
wrapper therefore supplies a positive packaged route into `0x132c0` with
descriptor 8 as its argument. That callback loads `[descriptor+0]`, then
dereferences that pointer and extracts bit 3. Under the packaged pointer
initializer, its gate is bit 3 of the current word at `0x58220024`.
This sharpens the earlier caller-supplied-pointer description; it does not
identify the electrical signal represented by that bit.

## Implication and limits

The descriptor initializer, vector slot, wrapper and fault teardown's signed
`+4` load are internally consistent as resource 8 / IRQ 39 in the selected
package. This narrows the source identity of the callback whose later
execution could be interrupted by teardown.

It does not prove the currently active vector base, successful initialization,
unchanged live descriptor fields, actual interrupt delivery, callback
execution, teardown occurrence, later enable state, or physical-light cause.
The vector slot and decoded initializer are saved bytes, not current RAM or
CPU-register observations. No interrupt manipulation or bypass recipe follows.

## Reproduction

[descriptor-reproduce.py](descriptor-reproduce.py) pins the complete selected
package and existing decoder, checks an independent known-answer decode,
reconstructs row 0, and checks descriptor bytes, vector, wrapper and callback
instructions. Normal and optimized Python executions both pass. The
independent reviewer and root decoder/disassembly results agree. These
checks have zero target operations and do not establish a repaired panel.
