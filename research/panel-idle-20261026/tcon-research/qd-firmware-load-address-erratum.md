# QD firmware load-address correction, 2026-10-27

This corrects the address convention used in earlier analyses of the selected
5 MiB factory asset. It records offline analysis only. No TV, firmware update,
debug session, USB open, controller command or protection change was performed.

## Correct mapping and direct evidence

Input: `overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin`,
5,242,880 bytes, SHA256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.

Each embedded executable has a 512-byte container prefix preceding its vector
table. For addresses in its initial flash/code load region:

| Component | Stored vector offset | Initial SP | Thumb reset vector | Reset instruction file offset | Translation |
| --- | ---: | ---: | ---: | ---: | --- |
| image 0 | `0x200` | `0x20020000` | `0x345` | `0x544` | linked = file − `0x200` |
| image 1 | `0x40200` | `0x20020000` | `0x369` | `0x40568` | linked = file − `0x40200` |

The Thumb bit is removed before mapping an instruction. At the corrected reset
locations, both images decode to a coherent `LDR; BLX; LDR; BX` startup
trampoline. Interpreting the same reset vectors using the old convention lands
in other bytes. The corrected startup also resolves valid scatter-loading
tables, giving independent evidence beyond a plausible short instruction run.

This formula is not a mapping for arbitrary runtime RAM or MMIO. Those absolute
addresses retain their values. Scatter-loaded RAM needs its own load/runtime
translation. The images are independently linked; equal linked addresses in
the two images do not identify the same executable or physical storage.

## Scope of the correction

Earlier reports often labelled container file offsets as linked addresses and
said the images were linked at their component starts. Those address-equality
statements are superseded. Preserve the old reports and their evidence hashes;
use explicit stored/file and linked coordinates in subsequent work.

Relative `BL`, `B`, PC-relative literal-location and relative `TBB` walks can
remain structurally valid in file coordinates because the constant displacement
cancels. Absolute flash pointers, vector destinations, function pointers,
scatter-load sources and cross-image references require translation before
following them. A plausible function at an unadjusted destination is not
evidence that a stored pointer targets it.

## Rechecked RT-to-status path

The independent [RT wire load-map audit](qd-rt-wire-load-map-audit.md) rechecks
the important relative path under this convention:

| Role | Stored image-0 offset | Corrected linked address |
| --- | ---: | ---: |
| EEPROM RT check | `0x99e8` | `0x97e8` |
| common error entry | `0xb860` | `0xb660` |
| common error-selector store | `0x2b964` | `0x2b764` |
| I²C state machine | `0x12ac4` | `0x128c4` |
| F3:80 dispatcher | `0x21824` | `0x21624` |
| selector getter/table | `0x21ff8` | `0x21df8` |

The packaged relative path and its shared RAM error halfword remain supported.
The absolute RAM object `0x2000f0e0` and halfword offset `+0x10` do not shift.
This remains a packaged-firmware result, not proof that the executing
controller image has identical bytes or that this path caused a particular
physical blackout.

## Positive startup result for image 1

The [image-1 initialization analysis](qd-image1-context-initialization.md)
follows the corrected reset/scatter loader and decompresses its initialized
data. It proves startup stores pointer `0x20010000` at RAM `0x200004e0` before
application entry. The context getter therefore uses that base initially.

Image-1 field `+0x240a` consequently has initial runtime address `0x2001240a`.
Image 0's live RT checker uses fixed address `0x4701240a`. These are numerically
different in independently linked address spaces. That does not prove physical
storage is separate: an interconnect window, copy or secondary-core interface
could bridge them. No bridge is yet established, so neither physical aliasing
nor its absence is claimed. Establishing that edge is the next relevant step.

## Concrete USB callback error identified

The constructor at stored offset `0x22324` loads the literal Thumb code pointer
`0x2b071` from stored offset `0x223a0` into USBSerial state `+0x5c`.
The actual target is linked address `0x2b070`, stored offset **`0x2b270`**.
The earlier USB report decoded stored offset `0x2b070` instead.

The actual callback checks request code `0x20`. If the function pointer at RAM
`0x2000063c` is nonzero and the registration's state pointer exists, it invokes
that function using the line-coding state's first word. The old claim that
this callback directly rewrites register bits 0..1 came from the wrong target
and is superseded. The notifier's installed target and effects still need
tracing; no serial open or USB handshake has been performed.

This does not by itself invalidate the separate relative CDC transfer-service
or RT RAM-to-UART traces. It does require rechecking indirect bindings before
using those reports to choose a live USB experiment.

## Runtime evidence remains separate

The accepted working-Apps status/pin `0/0`, subsequent reported For You
blackout and accepted status/pin `0x10/1`, raw kernel log bindings, Linux boot
identities and retained bus bytes do not depend on this load-address mapping.
Their [runtime audit](../overnight/paired-fault-status-runtime-audit-20261027.md)
and physical-timing limits remain unchanged.

No permanent repair, safe protection override, physical SRAM alias, current
controller-image equality or recovered panel output follows from this erratum.
