# Image1 selector origin, consumers and refresh scheduling

**C+7 is a byte copied from the remote AP_EXCO context, with a separately
scheduled local refresh and more than one local consumer/mirror.** The direct
copy and upstream boolean were already established by DF. This audit adds a
concrete callback-registration/dispatch bridge, a bounded direct-access census,
a separate byte mirror and hash-qualified configured-delay observations. It
performs no target, root, network, UI, reset, mask, code or memory operation.
No helper or operation packet is created. Existing frozen files are unchanged.

All linked instruction addresses below belong to selected **image1**, file
`VA+0x40200`, in package SHA256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
`audit.py` decodes original bytes with Capstone and verifies93 exact instruction
anchors,16 literal values,16 source-range hashes and bounded syntactic scans.
`source-audit.json` pins the results. Later bodies discussed here were not among
DX's four16-byte live fingerprints; sampled identity does not attest their live
execution. Image0 and image1 numeric CPU addresses are distinct domains.

## Direct producer and upstream boundary

Getter0x38f4 loads literal0x38f8=CPU0x20000500. At0x393e the refresh function
gets `*(CPU0x200002cc)` through getter0x38e8 into r6. It then performs:

```text
0x394e: r0 = u8[r6 + 0x3d8]
0x3952: u8[CPU0x20000500 + 0x6c7] = r0       // CPU0x20000bc7, C+7
0x3956..3958: C+8 = u8[r6 + 0]              // separate field
0x39fc..3a02: u16[RTP_root + 0x24ca] = C+7   // zero-extended copy
```

This copies a full byte; the image1 instruction does not normalize it to0/1.
The preceding load from provider+1 is also a separate value, not the selector.
Getter/root/operand identities are checked directly, rather than inferred from
an isolated textual offset.

DF's frozen cross-core bridge identifies the provider as image0 AP_EXCO context
CPU0x200158a8, visible to image1 through0x450158a8; provider+3d8 therefore refers
to image0 CPU0x20015c80. DF/source-upstream already recovers its image0 producer
at0x2fb44..2fb76:

```text
context[3d8] = bool((AP_EXCO_data[e6] & 1) | u16(AP_EXCO_data + 2fc))
```

The first input comes from debounced comparisons of table-tail sums; the second
has independently masked/debounced comparisons and stale-bit behavior. These
are existing source results, not newly recovered UI controls. The physical table
writer, units, contemporaneous input values and complete configuration-writer
history remain unresolved. A matching cached Apps/Live label is an observation,
not a direct UI→selector store. No persisted/high-bank/POFLG operation route was
followed, invoked or packaged for this work; this investigation stops at the
already reviewed context/value providers and their low-context consumers.

## Newly closed callback path

The only syntactic direct BL to refresh0x3934 in the bounded image interval is
0x18c96, in wrapper0x18c94. Its Thumb pointer0x18c95 is installed indirectly:

| Source | Exact effect |
|---|---|
|0x195f8..19614|Get RTP root; clear byteCPU0x20000460; store literal0x18c95 toCPU0x2000046c; load u16[root+0x240c] and store its zero-extended value toCPU0x20000468.|
|0xaef6|Direct call to this initializer. The surrounding general initializer is not expanded here.|
|0x19520..1955e|Reset byteCPU0x20000470 to0, load callback-table word0 atCPU468 into the selected timer register+0x24, enable the local timer path and set byteCPU460=1.|
|0x43e6|Direct call to the arming function. In the same inspected caller,0x4446 later calls selector-edge handler0xc250 only when provider context byte+0x48 is nonzero.|
|0xe060..e072|Read selected timer status at+0x1c and, when bit2 is set, call0x19574. This source inspection proposes no timer/MMIO read.|
|0x19574..195e4|If byteCPU470<1 and table slot callback is nonzero, load it and BLX at0x195a8. After callback, sample active byteCPU460; if active, increment byteCPU470 and program the next table word; if index is already≥1, clear index/active.|

The selected timer base literal is0x40124000. That is a **source constant**, not
a proposed live observation address. No timer clock, prescaler, physical IRQ
number, elapsed unit or callback period is qualified here. In particular root240c
value200 must not be renamed200ms,200Hz or a fixed callback frequency.

This is a finite, rearmed callback sequence, not a self-contained periodic loop.
The dispatch bound is index<1. After an active first callback it increments to1
and reads a word starting atCPU0x20000470, the same address as its byte index.
That overlapping next-slot word and its adjacent bytes must not be invented as
a second initialized callback or a known delay. The model deliberately reports
only the next-slot offset, not its value. The callback can affect active and index
state; the model therefore accepts **post-callback** active and index inputs.
Its default index assumption is explicitly stable. The index is also reloaded
while selecting a callback; the supplied callback argument represents the
actually loaded value under stable pre-dispatch table/index inputs. No atomic
access or complete concurrent-writer exclusion is established.

The arming call precedes the mirror/refresh-seed handler in one caller, while
the selector value copy occurs through a separate indirect callback path.
Their relative runtime order, interruptions, rearming cadence and occurrence
around a particular Apps→Live transition are unobserved. If the copy occurs
after one mirror check, that check can have used the previous byte; this is a
conditional ordering possibility, not proof of a race or a stale-reference fault.
EG's seed1→two qualifying boundary events remains the reference-copy model;
these sources do not require one top and one bottom event.

## Consumers and separate mirrors

The overlapping halfword scan over image1 `[0,0x1d6a4)` finds21 instructions
with explicit memory displacement0x6c7: one byte store at0x3952 and20 byte
loads. The matching fixed-displacement strb/strh/str/strd overlap scan finds only
that store; aligned literal0x20000bc7 is absent. These are **syntactic bounded
censuses**, not a reachable CFG, exclusion of computed addresses/copies, other
core/DMA stores or a whole-image writer proof. Startup also clears the enclosing
image1 BSS interval0x200004f8..0x2000e19c; this is a separate known initializer,
not evidence that any particular MODE2 executed that startup or cleared C+7.

| Reads | Selected effect / certainty |
|---|---|
|0x39fc|Publish full byte to RTP root24ca halfword. Already inside the refresh function.|
|0xc27c/0xc288|Compare against u16CPU4c2; changed nonzero value seeds u16CPU4c4=1, changed zero clears it; unchanged value does not rearm. EG already proves this path.|
|0xb83a/0xb862 and0x1c13a|Permit fixed-reference row branches and boundary-copy path, conditional on actual B header/counter/geometry. C+7 alone does not prove selected final A.|
|0x1e98/0x1ec4/0x1edc and0xbdc2/0xbdf4|Select alternate root24c4 threshold for nonzero C+7 in the inspected category branches. Other explicit categories retain their separate thresholds.|
|0x197a2/0x197ae|Separate **byte** mirror atCPU0x2000045d (literal0x198f0), notCPU4c2. Changed-to-nonzero sets local r7; either nonzero-to-different-nonzero also qualifies at byte level. This combines with other flags before call0x19730.|
|0x19792/0x19834/0x198b0|Further control branches inside0x1976c; these do not write C+7. The inspected body may set context+6ce; its role is not assigned a physical name.|
|0x18c3a|Diagnostic argument read; logging is not a producer.|
|0x1992c|Select another resource's+c2 versus+122 halfword. Distinct from the RTP root; do not call it the same threshold from matching offsets alone.|
|0x1b7e0/0x1bf70|Additional conditional consumers; source excerpts identify their byte reads but no physical/UI meaning is assigned here.|

The separate45d and4c2 mirrors can update in different bodies, while root24ca
updates in the copy itself. None is a timestamp or a proof of atomic ordering.
Zero/one agreement at a later read does not reconstruct the intermediate edges.

## Saved configured delay and selector observations

`audit.py` verifies26 retained R windows against both the original result hash
index and native receipt bytes, plus available same-capture C windows. It reads
no moving EH/EI result. Inputs are:

| Completed capture | R windows | u16[root240c] |
|---|---:|---:|
|ED/table-read-01|2|200 throughout|
|DK/score-baseline-01|6|200 throughout|
|DK/reference-onset-01|6|200 throughout|
|DK/dv-observation-01|4|200 throughout|
|DK/dv-rechallenge-01|4|200 throughout|
|EE/onset-01|4|200 throughout|

Of these,12 have same-capture C7/root24ca=0/0 and12 have1/1. Two R-only
transition captures have root24ca=1 but no same-capture C window; their C7 is
left **null**, not borrowed from post-fault samples. The Apps trigger baselines
are0/0 and later Live boundaries1/1 in both faulting and nonfaulting runs.
Thus this selector transition and configured delay do not distinguish the
outcomes. The source permits content-dependent antecedents through AP_EXCO,
but no contemporaneous AP_EXCO/table capture here predicts particular shows,
sparse menus, full Apps or screen savers. The packed-difference path and its
history remain necessary, separately observed inputs.

## Bounded next observations, without a helper

Existing full R already contains root240c at+0x0c and root24ca at+0xca. Existing
C+7 and M+34/+36 contain selector/reference mirror/counter. Decode these before
adding any read; EH's frozen54-byte records are unchanged by this work.

`future-low-sram-observations.json` records one minimal optional future window:
image1 CPU0x20000468/8 through the source-qualified SRAM alias0x47000468/8,
containing configured u32 delay and callback pointer. Both words are within
initialized static SRAM below0x200004f8. Separately useful bytes are active460,
index470 and mirror45d. These are ordinary low-SRAM source identities; no MMIO,
remote provider dereference or generic scan is proposed. They have not been
read live and need their own fixed-reader review/readiness before any use.
A sampled registered pointer or nonzero flag would still not prove a call,
frequency, historical edge, final A identity, physical effect or safe write.

## Reproduction and scope

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/tcon-capstone python3 audit.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/tcon-capstone python3 -O audit.py
PYTHONDONTWRITEBYTECODE=1 python3 test_model.py
PYTHONDONTWRITEBYTECODE=1 python3 -O test_model.py
```

The pure models assume stable pre-dispatch table/index inputs and cover
byte/halfword widths, nonzero values other than1,
unchanged/changed mirrors, finite callback dispatch and invalid inputs. They
do not invoke callbacks, reproduce timer units, schedule interrupts or prove
actual content behavior. `input-provenance.json` records source/capture hashes
without copying OEM payloads or original raw windows. The small reviewed
instruction excerpts are original analysis, not a whole-binary disassembly.
No persisted/high-bank/POFLG route, operation recipe or protection write is
included. `source-inventory.json` freezes authored outputs; original captures
and all predecessor reports remain intact.
