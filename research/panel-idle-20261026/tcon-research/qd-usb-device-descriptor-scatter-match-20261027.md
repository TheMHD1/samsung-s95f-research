# USB device identity recovered from reset scatter

Recorded 2026-10-27 UTC. Offline reconstruction of retained package bytes and cached USB metadata; no target operation.

## New result

The packaged image's **complete 18-byte USB device descriptor** matches the previously captured Samsung USB `7-1` device byte for byte. The descriptor was hidden inside the reset scatter compression, so searching for its plain bytes in the 5 MiB package did not find it.

```text
12 01 00 02 ef 02 01 40 e8 04 01 20 50 02 01 02 03 01
```

This binds USB version 2.00, composite class/subclass/protocol `ef/02/01`, endpoint-zero packet size 64, VID/PID `04e8:2001`, revision `0250`, string indices `1/2/3` and one configuration. It is stronger than matching the vendor/product strings alone. It does not establish equality of the currently executing program with the packaged executable, or prove that a particular USB read targets the RT controller's storage.

## Byte and callback provenance

Canonical image-0 mapping: **FILE = linked VA + `0x200`**. Absolute RAM addresses are unchanged.

Image-0 scatter row6 at FILE `0x3e3a0` contains:

| Field | Value |
| --- | --- |
| linked compressed source | `0x3e89c` |
| stored compressed source | `0x3ea9c` |
| destination | `0x20261000` |
| output length | `0x4d4` (1,236 bytes) |
| decoder linked VA | `0x17c` |

The existing hash-pinned scatter decoder, first checked against the independent image-1 known answer, consumes through exclusive FILE `0x3eac6`. Its output SHA-256 is `b7017446eabb7487bd28e612aa20df018b7b5442528664ca5990d3db80397fe0`. Output offsets `0x200..0x211`, RAM `0x20261200..0x20261211`, are the exact descriptor above.

The descriptor has a concrete executable use:

```text
VA 0x2a1ec / FILE 0x2a3ec:
    mov r2, r0
    movs r0, #0x12
    strh r0, [r1]        ; output length = 18
    ldr r0, [pc, #4]     ; literal RAM 0x20261200
    bx lr
```

Reset scatter row0 expands to `0x20000000`, size `0xf4c`; its output SHA-256 is `685d8eda90bb3ce7e6210ad0dfe962f65ac3b8e1b2eb1a40962e0e5720d81eb3`. At output `+0x500` it stores Thumb pointer `0x2a1ed`, targeting this descriptor callback. The accessor at VA `0xf778` / FILE `0xf978` returns that table address `0x20000500`.

The USB initialization body VA `0x2490c..0x24962` calls the accessor at VA `0x24948`, preserves its result and passes it as `r2` into VA `0x28b36` at VA `0x2495a`. This is a positive table-to-USB-initialization edge. This bounded report does not claim to reconstruct every later request dispatch or every configuration-descriptor byte.

## Retained live comparison

`overnight/qd-usb-interface-metadata-20261027a/client.stdout`, SHA-256 `065113d8f9d133570a72a4c086e2fdbff26567c9f8c082612f794f7414430530`, contains one authenticated root command returning zero with empty stderr and no timeout, boot `00000000-0000-4000-8000-000000000000`, uptime `83382.46..83382.52`.

It read the USB core's cached sysfs descriptors. The retained binary value is 116 bytes: this 18-byte device descriptor followed by a 98-byte configuration descriptor. The 116-byte SHA-256 is `7293efb1f43f1166a3c54f193fe584a423d25beb41597b85f5d3452f211e0bc0`. The configuration records CDC control/data interfaces and a vendor bulk interface with endpoints `0x82/0x02`; the complete packaged configuration has **not** been reconstructed in this report.

The live record predates the later stock MODE2 disconnect/re-enumeration. Descriptor identity does not prove that either executable or all descriptors remained unchanged after that event. The separate reset-coupled report preserves its own chronology.

## What this changes

The full **device** descriptor identity gap is closed for the retained package versus the retained cached sample. The next useful discriminator is the vendor-bulk handler's actual storage target and read semantics. There is no need to repeat a plain-byte descriptor search or mistake the SmartThings serial dongle for this device. No flash, protection modification, USB request or new panel reset was performed.

## Reproduction

[The checker](qd-usb-device-descriptor-scatter-match-20261027.py) pins the package, decoder, retained metadata, both scatter rows/outputs, descriptor callback, table accessor and USB-init bytes. It performs no network or device operation. Run it normally or with `python3 -O`; both must report exact equality while retaining the separate `current_executable_equality_proved=false` result.
