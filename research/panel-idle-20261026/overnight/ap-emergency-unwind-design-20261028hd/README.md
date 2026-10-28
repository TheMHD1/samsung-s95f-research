# AP emergency effects and the stock initialization boundary

**The selected firmware contains complementary output operations, but no complete post-emergency stock unwind or externally callable full image0 reset has been established.** `25b24(0)` is not the inverse of `25b24(1)`. Full image0 startup positively initializes the AP witnesses, shared RTP root, output configuration and callback ownership in separate stages. The currently qualified MODE2 ABI does not prove that this path runs. A synthetic three-scalar fault clear would leave these other obligations unresolved.

This is a bounded host-only source checkpoint. No TV, root adapter, USB, network, UI, field write, hardware access, new executable, deployment or reset was performed or implemented. The synthetic replay runs retained instructions inside Unicorn with private emulated memory and explicitly stubbed unrelated callees. All OEM source stays in the retained package; this directory contains hashes, selected textual disassembly and analysis only. It is an author audit, not an independent approval of a recovery operation.

## Source coordinates and actual boundary

The selected package is `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`, 5,242,880 bytes. All instruction addresses below are **image0 VA**; package file offset is VA+`0x200`. The image1 mapping is VA+`0x40200`. Some older source notes use package offsets; e.g. their `b860` is the image0 VA `b660` used here. `source-spans.json` pins exact extents and file offsets; `selected-disassembly.txt` deliberately excludes literal pools from decoding as code.

The retained actual `GP/ha-capture-01` passes the frozen HA strict parser. All five retained raw files exactly match its receipt hashes and lengths: 5 complete headers,10 bulks,548 IN bytes, USB70, released/closed, wrapper `STAGE_ABSENT`, one production invocation and zero writes/UI/retries. Both complete R256 windows are byte-identical and decode stop1/fault`0x1001`/ordinary0/limit40/logger0. AP magic=0; AP reason+`0x10`=16; AP_EXCO-data magic=0 and+8=0; AP_EXCO-context+`0x7c`=`0x3000` (bit12 set). The parent readiness evidence is separately pinned. The three exact low-SRAM intervals have now completed once; the frozen prospective HA wording remains untouched.

These are non-atomic source-compatible markers. They do not prove current PC, historical bypass choice, a unique writer, completion of every emergency side effect, or that image0 never reset and re-entered. The parent separately reported the physical panel off. No optical observation or onset timestamp is derived from these memory reads.

## What the emergency path changes

`b660` calls `2fed4` at`b66e`, teardown`96d8` at`b678`, reason dispatch`14910` at`b6a0`, and reason setter`2b764` at`b6a6`. GY/HB supply the already pinned root-fault→reason16/status bridge; this checkpoint adds the complementary output/init closure.

| Exact source edge | Positive effect and boundary |
|---|---|
|`2fed4..2fef4`|Writes1 to`0x58601404`; calls ordinary-off`215bc`; changes AP_EXCO-context+7c bit12 to1 while preserving the other bits. The physical/global flag role remains unnamed.|
|`96d8..9746`|Obtains descriptor indices`1c,1e,1b,7,8,10`, reads their signed IRQ byte+4 and calls`1b0e8`, whose literal is NVIC ICER-class`0xe000e180`. It first also calls resource operation`d834(8,0)`. Live descriptor contents/IRQ numbers were not sampled.|
|`b694..b69a`|Sets IRQ27 priority byte to`0x20`. A complete matching restoration of this and all disabled owners is not established here.|
|reason16 arm`14970..14988`|Clears AP_EXCO-data+8; calls`25b24(1)`; writes mask`0x10` to`0x4013400c`; then calls history/handshake`9968` and eMMC-path`a030`. Their complete receiver/storage outcomes are not closed by this audit.|
|`25b24` regardless of argument|Calls`3dfc`: RAM byte`20000cb0=0`, word`40130010=8`. If AP halfword+36 is0 or1, calls`3e14`: RAM byte`20000cb1=0`, word`40132010=0x200`. Calls`10de0(AP+92)` through a separately bounded timer-like sequence.|
|`25b24` only when argument nonzero|Adds word`40132010=0x80` and word`40131010=4`. Argument0 skips only these final two stores; it still performs the preceding operations.|
|`2b764..2b778`|Stores the supplied reason halfword to AP+`0x10`.|

The initial return at`b6d6` requires AP magic`0x1234` and data magic`0xabcd`. Otherwise`b6f8→b6dc` repeats service calls`3ab34(1),16fc0,39404(0),276ec,20510,1f3e4`. The backedge does not recheck the magic pair. Later setting those words would not itself supply a new tested exit. This does not exclude reset/nonlocal behavior inside unresolved service callees or an external core reset.

## Code-backed bank convention and complementary stock paths

Generic writer`441c..447e` selects six bank bases`40130000..40135000` in increments`0x1000` from an index0..95. For argument value1 it ORs the selected bit into bank+`0x0c`; otherwise it ORs it into bank+`0x10`. Generic configuration`40f4` updates per-index nibbles at+0/+4; reader`41d0` reads a selected bit from+`0x18`; wrappers`d810`/`d822` bind them. This is positive evidence for the firmware's paired output convention. It does **not** establish board net names, active electrical polarities, measured voltage, rail timing or a register specification. Direct emergency helpers write a full mask rather than the generic helper's read/OR form; this audit does not model real hardware reads or write-one behavior.

| Emergency-side effect | Positive complementary source operation | Reachability limitation |
|---|---|---|
|`cb0=0;40130010=8`|`228bc..228c8`: `cb0=1;4013000c=8`|Called at`1dd20`, and guarded `1dd70`/`1dd8e`. `1dd54` chooses enable when AP+170==1, disable when==2, otherwise follows sampled resource1. It is not unconditional enable.|
|`cb1=0;40132010=0x200`|`228fc..22908`: `cb1=1;4013200c=0x200`|Called by guarded transition`1dcd2` at`1dcf8`, and conditionally by`26b6c` at`26b86`. The latter depends on its separate register status.|
|`40131010=4`|`1de64`: reads AP+8e, calls delay helper`1de0c`, then`1de78` writes`4013100c=4`|Positive main startup call`39b60`; no emergency-loop call to it established.|
|`40132010=0x80`|`1ddac..1ddee` writes`4013200c=0x80` at`1dde0`|When AP+170==0 and sampled resource1==0, the alternate branch instead enters`b660(reason8)`. Otherwise it performs the complementary store and separate status/log calls.|
|reason16 `4013400c=0x10`|Initialization`1e2fe..1e302` writes`40134010=0x10`|Part of broad init`1e02c`, not an exposed standalone recovery operation.|

`1dcd2` is itself guarded by`38e24`: initial nonzero returns without the transition; a nonzero final check calls both off helpers again. Argument1 performs off/off, separate control call and delay before`228fc`; other arguments perform off/off, AP-dependent delays and`228bc`. Its stock wrappers`1dcba`/`1dcc6` pass0/1, but no admitted external command or complete post-fault entry through them is recovered. These routines are not a safe host call list.

## Full startup is staged, not “write the opposite masks”

The reset entry`344` calls literal`360=26759` then branches through literal`364=141` into the scatter dispatcher. The dispatcher reaches`2bc`; `2c4` calls main`39998`. This is a positive static reset/startup linkage, conditional on that reset path actually executing.

- Image0 scatter row11 zeros CPU`20000f4c..20017384`, including **all complete AP witness intervals**. The real zero handler`1d8..1f2` is checked. This initializes AP reason, both magic words and AP context+7c to0. It does not preserve the observed`0x3000` context as a full-reset postcondition.
- Row9 decodes the full`0x47bc`-byte shared root initializer at bus`47010000`; stop/control/fault/ordinary are0/0/0/0. Root initialization therefore does not by itself produce operational Clean0/0/1. GX's ordinary-on path remains a separate prerequisite.
- Main calls broad bank initialization`1e02c` twice, at`39a3e` and`39b3a`. It configures many resources, calls both off helpers, writes the same emergency-low masks to`40131010`/`40132010`, and separately clears bit`0x10` through`40134010`. Initialization intentionally begins with several outputs in the same software-low state as emergency handling.
- The later startup stages call`1de64` at`39b60`, registration`1e47c` at`39b8e`, and guarded`1dd54` at`39b96`, then enter recurring loop`39bda..39c4c`. This order is positive source reachability, not a claim every branch completes or this path ran in GP.
- BC's pinned registration/reenable closure supplies a concrete interrupt dependency: ordinary descriptor8 reenable occurs in descriptor1c's callback, after bit3, two state-byte checks and saved-pointer checks. Emergency teardown disables descriptor1c as well as descriptor8. Existence of the ordinary handoff therefore does not establish self-reenable after fault. Registration and full IRQ ownership matter independently of the RAM fault tuple.

HA's reason16/context`0x3000` and faulted R are not the lasting full-startup initializer values. They remain compatible with no full image0 reset, incomplete initialization, or full reset followed by re-entry. GX separately proves local image1 counter clearing can produce N0 without clearing root fault; USB70 and N0 do not resolve those alternatives.

## Qualified unwind/reset design and exact remaining gap

No direct MMIO, arbitrary function call, magic rewrite, RAM tuple clear or extra MODE2 invocation is proposed. A qualified stock recovery would need a single source-bound route that either (a) runs the full image0 reset/scatter/startup domain, or (b) positively restores all required output sequencing, interrupt/resource ownership, ordinary service execution and fault-latch semantics. The selected source presently supplies the components, not that complete route.

GZ's existing MODE2 sender operation41/mode2 and platform4 OCL operation1/command`0x3f`/length1 are positively recovered. The receiver's reset/rail/core-domain semantics remain the exact message gap. Its off/on error/null-provider paths and ignored recovery-tail outcomes prevent treating helper terminal success as full image0 reset. The actual GP accepted MODE2 followed by faulted EB/HA is a concrete reason to retain this distinction.

The smallest useful continuation is to identify that exact stock receiver/domain or an already existing ordinary cold-start lifecycle whose execution is tied to image0 reset entry. A normal UI preparation may change the triggering conditions, but it is not source proof of output/IRQ restoration or escape from the emergency service loop. This checkpoint does not qualify a new UI or power command. Any separately chosen stock lifecycle must retain its native/helper outcome independently, then observe fresh same-device-lineage R and AP markers plus a separately timed owner picture report. A transient zero reason or new USB number alone is insufficient; source re-entry and retained fault must remain distinguishable. Operational clean R0/0/1 and restored service are separate from physical picture recovery.

Unresolved boundaries are exact: OCL`0x3f` receiver/reset domain; complete behavior of emergency service callees and indirect/nonlocal paths; all runtime/computed/DMA aliases to root/AP; actual descriptor IRQ contents and ownership; external signal names/polarities/timing and persistent/history side effects. This is not a whole-firmware writer census or proof that no other stock recovery exists.

## Limit canary boundary

The decoded row9 halfword **root+24c4 is0**, not40 or200. Its neighboring c0/c2/c6 halfwords are also0. Row11 makes APcontext+7c exactly32-bit0, APreason+10 exactly16-bit0, and the two magic halfwords0. Thus operational40 already requires configuration after the raw initializer. A complete initial zero is not the same as the eventual configured post-startup value.

The positively pinned writer routes here are the full row9 initialization and the reviewed FA fixed USB2-byte set/restore transaction. In the bounded selected image1 immediate24c4 uses, `1e9e/1eca/1ee2` feed comparison loads and`bdc8/bdfa` feed publication-bound loads, not stores. No additional runtime c4 setter was positively recovered by this bounded examination. This does not close computed/indexed stores, bulk parameter copies, configuration reloads, image0 generic resource handlers, other cores or DMA. The source path that establishes ordinary operational40 after row9 zero remains unresolved here.

A future pre-reset200 canary would therefore measure **the value after the whole lifecycle**, not uniquely which initialization ran:200 could be retained or restored after initialization;40 could be reloaded without full context initialization;0 could be an intermediate/configuration failure as well as row9 initialization. Neither200 survival nor40 readback alone proves a reset domain. It would also retain the coupled publication/comparison and admission/recovery limitations documented in GK/GH; the existing clean-only FA contract cannot be transplanted into the current fault/AA0AC3 context. This is a design interpretation only, with no new writer or trial admitted.

## Reproduce

```sh
python3 -B audit.py > validation.normal.json
python3 -B -O audit.py > validation.optimized.json
cmp validation.normal.json validation.optimized.json
```

The script uses retained Capstone and Unicorn only, with no installation. It validates every `input-pins.json` entry and24 exact source spans, real instructions/literals, startup decode known answers,21 finite real-body synthetic cases and the actual frozen HA strict parser/raw binding, plus4 malformed receipt cases. Unrelated calls are explicit stubs; their results are not claimed. Normal/optimized output is byte-identical and checks are explicit under`-O`. `source-inventory.json` freezes this authored checkpoint; no predecessor artifacts were changed.
