# Controller memory ownership and reset rollback audit

**No logger scratch allocation or guaranteed code rollback is qualified.** This
audit adds concrete startup and allocator evidence: the selected image0 has a
stock heap that can grow into the apparent space below its stack; image1's
startup scatter writes data, without copying its low instruction bank. The
stock MODE2 evidence reaches a reset mailbox and USB re-enumeration, but does
not establish restoration of modified instructions. This is a host-only source
audit, with no device operations, executable payload, patch or installer.

The selected package is 5,242,880 bytes, SHA256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
All code addresses below are linked virtual addresses in the named CPU domain.
Image0 bytes are at file `VA+0x200`; image1 bytes are at `VA+0x40200`.
The same numeric `0x200...` address in the two CPU domains does **not** imply
shared storage or transferable allocation ownership. The separately qualified
DW mapper exposes image0 local SRAM through `0x450...` and image1 local SRAM
through `0x470...`; the `0x460...` window selects the image1 low code bank.

## What the startup actually writes

`source-audit.json` enumerates every startup scatter row, destination, exclusive
end, handler, compressed-source consumption and output SHA256. It replays the
existing hash-pinned decoder; no decompressed OEM data is copied into this
directory. The relevant local SRAM coverage is:

| CPU domain | Range, exclusive end | Source-backed owner |
|---|---|---|
| image0 | `0x20000000..0x20000f4c` | decompressed startup data |
| image0 | `0x20000f4c..0x20017384` | zero-initialized static data |
| image0 | `0x20017384..0x20018000` | unclassified 3,196-byte gap; smaller than the proposed data pool, no ownership grant |
| image0 | `0x20018000..0x20019000` initially | stock allocator pool; runtime can extend it |
| image0 | toward `0x20020000` from below | downward stack; growth ceiling is computed from current SP |
| image1 | `0x20000000..0x200004f8` | decompressed startup data, including root pointer at `0x200004e0` |
| image1 | `0x200004f8..0x2000e19c` | zero-initialized static data |
| image1 | `0x2000e19c..0x20010000` | unclassified 7,780-byte numerical gap, no positive reservation or complete runtime writer exclusion |
| image1 | `0x20010000..0x200147bc` | owned RTP context: image0 scatter row9 writes its `0x47010000` alias, including later live state/record/eligibility fields |
| image1 | `0x20015000..0x20015b50` and `0x20015f10..0x20016a60` | initialized fixed-reference buffers |
| image1 | top `0x20020000` | explicit initial stack top; lower bound and worst-case depth unproved |

Other initialized `0x202...` processing buffers appear in the complete JSON
map. A startup write establishes an existing owner; a missing scatter row
does not establish free memory. Parent's separately ongoing per-lane eligibility
analysis under the RTP root is consistent with excluding that entire context
from scratch use; it is not treated as a new allocator reservation here.

The DS logger data footprint is exactly 92 slots ×64 bytes plus64 control
bytes = **5,952 bytes** (`0x1740`). Stub code, saved context, alignment and
interrupt/stack budget are additional. Neither a run of zero package bytes,
a currently zero runtime field nor a zero-initialized BSS range grants space
to that logger.

## Image0 has a real, expandable stock allocator

At image0 startup `0x28a..0x28e`, literal inputs `0x20018000` and
`0x20019000` are passed to `0xcb4`. The initializer obtains the initial end
through `0x1ae4`, initializes metadata and supplies the remaining pool to the
free list. The initial extent is 4 KiB, already smaller than the logger's
5,952 data bytes.

The stock allocator entry `0x378` rounds the requested allocation including
its header to eight bytes, walks/splits a free list and can call the extension
route `0xc8c -> 0x1afa`. Entry `0x3d6` reinserts/coalesces released blocks.
The free-list root slot is `0x2001732c`; extension frontier is at
`0x20000f48`. A concrete caller at `0x2f14e..0x2f180` requests24 bytes,
checks the returned pointer and stores fields plus a link into another
object. This is positive use, beyond resemblance to a library routine.

At `0x1afa`, the extension computes the current `SP-0x1000`, checks that the
required end fits, chooses extra capacity bounded by that ceiling and advances
the frontier. Thus `0x20019000` is **not** a fixed upper reservation. Space
above it may belong to future stock allocations. `audit.py:growth` models
this aligned, non-overflowing argument domain and tests the stack-dependent
success/refusal boundary. It does not predict live free space, allocations,
fragmentation, total stack depth or allocator thread safety.

This allocator is in the **image0** CPU domain. No image1 allocator pool or
alloc/free API was established on its examined startup path: its runtime
entry calls `0x1c2d0` (FPSCR setup), `0x904` (runtime state getter), and the
string-selection helpers `0x1c268`/`0x1c294`, then application `0x1ba0c`.
This is a bounded startup result, not proof that no image1 allocator exists
anywhere. A future proven allocation API would still need actual lifetime,
concurrency, cross-core visibility and invocation qualification. This audit
provides no remote function-call capability and invokes no allocator.

## Stack and misleading literal checks

Startup sets each CPU's SP to `0x20020000` (image0 `0x2bc`; image1 `0x2ac`).
It does not publish a linker-reserved stack floor. The image1 unpacker at
`0xbd58` pushes52 bytes and subtracts`0xf1c`, consuming **3,920 bytes before
callees**, callers or interrupt frames. An apparently idle high SRAM range
therefore cannot be assigned to a logger without a stack ownership/depth proof.

A raw aligned-word census finds image1 value `0x2001e000` at `0x96c`.
Decoding the containing path shows it is `b 0x970` followed by `movs r0,#1`,
**not a referenced stack-limit constant**. Similarly, image0's AIRCR literal
`0xe000ed0c` at `0x2c5f0` is read by priority-comparison code at `0x2c5ae`;
the examined function does not write SYSRESETREQ. Neither raw match supplies
a stack boundary or reset mechanism.

## Reset entry is not a recovered instruction reload

Both selected reset vectors enter code already in the low instruction bank:

| CPU | Reset entry | First call | Next stage |
|---|---|---|---|
| image0 | `0x344` | `0x26758`, enables FPU access through CPACR | scatter `0x140`, then stack/runtime/application |
| image1 | `0x368` | `0xdc00`, enables FPU access through CPACR | scatter `0x140`, then stack/runtime/application |

Image0 has12 scatter rows; image1 has9. **None targets its low code range.**
The selected reset/scatter sequence therefore does not itself restore those
instructions from a separate backing image. This does not exclude boot ROM,
an external loader, flash mapping or another earlier reset stage. Conversely,
the low linked addresses and successful `0x460...` byte reads do not identify
the bank as writable instruction RAM or mapped flash.

The earlier secondary-component loader audit records a host update-capable
whole-file SSB transport, but does not recover a component-specific boot/load
command or destination. That transport is not treated as MODE2 or proposed
for rollback. Its older unresolved alias statement is superseded by DW's
positive mapper proof; its unclosed boot-loader boundary remains relevant.

The exact retained MODE2 chain is stronger than a helper return code:

1. QDF mode2 calls stock off then on. The platform4/nonmonitor path reaches
   `tztv_set_sdp_jp_tcon_power_reset(1)` at QDF `.text+0x11b14`, then `(0)`
   at `.text+0x119ec`, with ACDET ordering/waits.
2. `tztv_frc_tcon` resolves `sdp_ocl_reset_tcon_power` and stores that callback
   at `.text+0x57e4..0x57f8`.
3. Retained `sdp_ocl_jp` `.text+0x2b38` sends mailbox operation1, command
   `0x3f`, length1, payloadvalue; its helper reaches `i2c_transfer`.
4. The frozen stock-MODE2 transport audit observes off/on GPIO and mailbox
   requests, USB disappearance/re-enumeration, and346 complete I2C on-tail
   transactions including113 cached-setting writes.

These anchors establish the software/transport lifecycle. They do **not**
provide the OCL mailbox receiver's reset-domain semantics, a boot-memory
mapping or a code reload. Cached setting replay is not evidence of rewriting
either embedded instruction image. Ordinary FRC PM's separately resolved
`set_power_mode` is a distinct, unresolved callback, not a substitute proof.

The parent's completed DX/DY probe was reported to match all four16-byte
code samples through the qualified aliases, with4 headers/8 bulks and clean
release/close. This source audit did not consume its moving analysis and does
not add its artifacts to the frozen input set. That result closes sampled
byte identity/read reachability only; it does not change the scratch,
instruction-write, active-fetch or rollback conclusions above.

## Smallest concrete remaining proof

There is **no positively qualified address** for the requested logger yet.
This is not a proof that no suitable memory exists. The source now narrows
the required evidence:

- For image1 scratch, obtain a positive link/map/reservation or actual
  allocator ownership/lifetime proof covering at least`0x1740` data bytes
  plus the separately sized stub/context, with stack and other runtime
  writers excluded. Do not choose the 7,780-byte gap merely because it fits.
- For rollback, recover the receiver of OCL mailbox command`0x3f` and the
  corresponding boot/remap/storage implementation that determines whether
  the selected code bank is restored, retained or executed in place. A
  before/after unchanged fingerprint across an ordinary reset would show
  stability, not restoration of a modified bank.
- Executable writes, fetch visibility/barriers, install/removal atomicity,
  exception nesting and recovery after ambiguous USB completion remain
  separate obligations. No arbitrary debug/MMIO probe is specified here.

The useful current alternative remains fixed source-qualified read-only
observations or independently qualified data-only experiments. This audit
does not authorize or implement an instruction hook.

## Reproduction and evidence boundary

Run from any directory (Capstone is the existing host dependency):

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/tcon-capstone python3 audit.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/tcon-capstone python3 -O audit.py
```

The checker pins the whole selected package and existing decoder, replays all
21 scatter rows, checks startup/allocator literals, tests the bounded heap
model, and compares exact derived JSON/disassembly. Checks use explicit
exceptions and remain active under`-O`. `input-provenance.json` pins the
prior authored analyses, DS/DW evidence and retained kernel binaries.
`validation.json` records both runs and the independent rerun of the existing
hash-gated MODE2 callback checker. `source-inventory.json` seals this task's
authored artifacts. Tests validate the stated static/model claims, not
target runtime ownership or safe patch execution. No OEM binary or raw
decompressed image is duplicated here.
