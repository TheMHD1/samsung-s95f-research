# Fault-state initialization and independent counter clearing

**A stock USB lifecycle does not establish that the RTP fault-state initializer ran.** The selected source separates the cross-core RTP context from image1's local counters. Image0's startup scatter row9 positively initializes the fault fields to zero. Image1's startup and application counter-clear paths can clear N while preserving a faulted RTP tuple. This supplies a concrete source-compatible explanation for the parent's reported GP69→70 observation; it does not identify which initializer, CPU or reset domain actually ran in that trial.

This is a host-only source follow-up to GV. No target, network, root transport, command dispatch, reset, memory write, helper or experiment was invoked or implemented. Firmware instructions run only in isolated Unicorn against synthetic memory. No OEM byte copies are retained here, including decoded startup data. The completed GP capture remains owned by the parent/other analyst; this report does not independently replay it.

## Source domains and exact initializer values

The selected package has SHA256 `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`. Image0 VA maps to file+0x200; image1 VA maps to file+0x40200.

Image0 getter`0xef94` loads literal`0xef98=0x47010000`, the cross-core RTP context alias. Image1 getter`0x38fc` instead loads the pointer stored at CPU`0x200004e0`; its packaged startup seed is CPU`0x20010000`. These source identities link the contexts through the qualified alias, rather than equating two cores' arbitrary numeric CPU addresses.

The pinned existing decoder independently verifies its image1 known answer and then decodes image0 scatter row9: source VA`0x3ea34`, destination`0x47010000`, size`0x47bc`, full output SHA256 `aee8a64ff7ccfaa95aa4def885fcf7d79c8f4f982d63c5efdb1686eec2cd2b6d`. The initial halfwords are:

| RTP-root offset | Packaged value |
|---|---:|
|`+0x2400` stop field|0|
|`+0x2408` separate control|0|
|`+0x240a` fault field|0|
|`+0x240e` ordinary gate|0|

Thus even this full startup initialization produces tuple **0/0/0**, not the operational clean tuple0/0/1. A separate ordinary-gate-on path is needed for the latter. A transient0/0/0 observation alone remains insufficient to identify initialization or a fault; stock gate-off can also produce it from a clean tuple.

Image1's scatter table has no destination covering its RTP root at CPU`0x20010000`. Its zero-initialized BSS is CPU`0x200004f8..0x2000e19c`, which includes N ordinals/counts CPU`0x2000ba28..0x2000ba4c`. The RTP root is initialized through image0 row9, not this local BSS clear. DZ already established the startup/domain split; this follow-up adds the exact fault-field initial values and executes the distinct application clear paths.

## Positive runtime stores and conditions

| Source body | Exact fault-state effect |
|---|---|
|image1`0xc1e0` setter|`0xc1f0` stores stop1; `0xc1f8` ordinary0; `0xc200` fault0x1001. It then calls the generic logger twice. This is the already qualified setter, not a reset path.|
|image0`0x21544` ordinary-on body|`0x2155a..0x21560` reads ordinary; only when it is zero does`0x21568` store1. This store does not clear stop or fault. Later temperature/endpoint work is separate.|
|image0`0x215bc` ordinary-off body|Only when ordinary equals1 does`0x215fc` store0; it also increments a different object's counter. Stop and fault are untouched by this branch.|
|image0`0x1163c` argument-conditioned body|After the sixth comparison matches,`0x116d8..0x116de` stores stop0. Other branches store stop1 or ordinary0/1. No fault240a clear is recovered in this body. External entry/command availability and invocation are not qualified or packaged here.|
|image0`0x1f45c` backup / subsequent restore slice|Stop is saved into CPU`0x20000ce4`; the restore slice loads that value and`0x1f642` writes it to root2400. This can restore a previously saved zero or one, rather than unconditionally clearing. No fault240a clear or MODE2 invocation of this path is established.|

The checker records a bounded halfword candidate index for immediate2400/240a/240e in both selected instruction ranges. It is a syntactic aid, not reachable-code coverage. The positive zero-store to fault240a recovered here is the **full image0 row9 initializer**; no separate runtime240a zero-store has been established by the bounded fixed-offset examination. Computed addresses, broader copies, generic resource update paths, asynchronous stores, other CPUs and DMA remain unresolved. This is not a whole-image absence claim or a reason to synthesize a new clear operation.

## Real local clear paths preserve the fault tuple

The audit executes image1`0xca84`, `0xcb2c`, and `0xc220` against seeded N and a root fault tuple1/0x1001/0, using the actual helper bodies/getter:

- `0xca84` clears N and related local counters/history; it does not change R256.
- `0xcb2c` calls`0xca84`, derives geometry from root2402, and clears X/Y/RGB arrays. It preserves B/Diff and R256, including the fault tuple.
- `0xc220` calls`0xcb2c`, then stores root2408=1 and clears three separate local halfwords. Its only R256 change in the test is that control halfword; stop/fault/ordinary are preserved.

All three cases return normally with N36 zero while the fault tuple remains1/4097/0. Six additional partial-body cases execute the actual ordinary on/off branches for incoming ordinary0/1/2 and verify stop/fault remain unchanged. These partial cases stop before unrelated later work; they do not claim full gate-function execution. No helper calls, control messages or live operations are exposed.

These positive source paths show why zero N or a fresh USB device number cannot be substituted for full R validation. A later clean0/0/1 must be observed, and a claimed fault clear must be tied to an actual clearing path or actual field readback. Conversely, N0 plus retained fault is compatible with several source paths and does not prove image1 startup, an internal core reset, retention of every memory bank or execution of image0 row9.

## Continuation boundary

The unresolved stock-recovery task is to identify which reset/init domains and call paths the actual MODE2 receiver executes, and whether image0's cross-core context initialization or another qualified fault240a clear is included. DZ's reset-mailbox/USB evidence does not answer that question. Ordinary-gate toggles and stop-only restores are not complete fault clears. No repeat reset, guard weakening, arbitrary write, persisted/high-bank/POFLG route or fault-state writer is proposed here.

`audit.py` pins the package, existing pure decoder and predecessor source reports; independently derives both scatter tables; checks exact instruction anchors; and runs the finite synthetic cases. Run it with retained Capstone/Unicorn available, with bytecode disabled:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B audit.py > validation.normal.json
PYTHONDONTWRITEBYTECODE=1 python3 -B -O audit.py > validation.optimized.json
```

Normal/optimized outputs match exactly. Explicit checks remain enabled under`-O`. The instruction-closure checks account for many assertions but only the stated three full local-initializer and six partial gate cases. `source-inventory.json` seals authored files; existing captures, sources and analyses were not changed.
