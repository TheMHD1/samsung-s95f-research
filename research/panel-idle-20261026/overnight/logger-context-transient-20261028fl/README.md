# C8 zero is a stock runtime state; logger restoration has a separate dependency

**CPU image1 `0x20000bc8 == 0` is positively reachable through an ordinary image0 runtime clear and image1's normal callback. It does not require reset or a changed root.** The fixed C8==3 condition in FG's shared `Context` check is consequently a readiness/profile restriction, not an immutable device-identity property. A separately reviewed restore-only action can admit this source-qualified zero while preserving the existing binding, transfer-phase, root, mode, geometry, profile and exact logger checks. This result does not widen arming or observation readiness.

The recovered paths produce values0,1,2,3,4. They do **not** establish a complete global0/3-only value domain. A zero may persist until a later setter/callback; no return-to3 deadline or current live invocation is proved. FL is source-only, contains no executable/helper patch and made no TV, root, network, USB or MMIO call. The parent owns reconciliation of the failed live transaction sequence.

## Exact corrected cross-core lineage

The selected5MiB package SHA256 is `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`. Image1 uses FILE=VA+0x40200; image0 uses FILE=VA+0x200. All VAs below are selected source coordinates, not current-PC observations.

Image1 getter VA0x38e8 loads pointer slot CPU0x200002cc. Startup VA0x1bce2 invokes the alternate registry lookup0x1bc24, using root0x1000c, and VA0x1bce8 stores its mapped result at that slot. The matching image0 registry record at FILE0x3c5b8 names **MULTI/AP_EXCO**, destination CPU0x200158a8 and extent0x3ec. Image0 getter0xe76c returns that destination. The selected image1 selector-zero mapper0x1bb74 maps its image0 CPU address to0x450158a8.

This is the corrected derived object from P/O/Q. It is distinct from ordinary AP_EXCO at CPU0x2000ff14. The earlier layout document's packaged ordinary AP_EXCO `20/0` comparison is not used here.

Image1 callback0x3934 performs independent byte copies:

| Source VA | Operation |
| --- | --- |
|0x393e /0x3942|Gets the corrected mapped derived object into R6.|
|0x3944 /0x3948|Gets fixed context CPU0x20000500 into R5.|
|0x394e /0x3952|Copies derived+0x3d8 into context+0x6c7, CPU0x20000bc7.|
|0x3956 /0x3958|Copies derived+0 into context+0x6c8, CPU0x20000bc8.|

These copies are sequential and share no recovered atomic snapshot protocol. C7 and C8 are different source fields, so C7=1/C8=0 is not internally contradictory.

## The positive runtime zero writer

Image0 function0x32764 contains a complete short clear body. It calls fixed getter0xe76c at0x32766, saves the derived pointer in R4 and, at **0x3277e/0x32780**, executes `MOVS R0,#0; STRB R0,[R4]`. This clears the exact source later copied into C8.

The same body clears derived bytes+0x2a..+0x2f, derived+0x26, and the image0-local callback slot CPU0x20000e70. Its only call is the fixed-object getter. It does not clear derived+0x3d8 or write the image1-root logger halfword. Those facts come from the complete bounded body, not merely its name.

The aligned direct-BL census identifies three positive callers:

| Image0 callsite | Locally recovered condition |
| --- | --- |
|0x32aa0|In decision0x329ce, the branch at0x32a8a reaches this block when its computed R7 is nonzero. It calls the clear only when derived flag+0x2d is nonzero, tested at0x32a96..0x32a9a. The R7 computation is source-pinned in the complete parent span; no physical meaning is assigned.|
|0x327bc|In function0x32790, a nonzero callback slot is invoked at0x327b6; comparison0x327b8 and branch0x327ba call the clear when its result equals1.|
|0x31486|In function0x31458's prefix, derived flag+0x2e must equal1 and the original first argument must equal0xc before this call is reached. The trace stops at this prefix.|

Thus ordinary runtime control can change the source from3 to0, independently of reset/startup. A later image1 callback can then copy0 to C8 while preserving C7=1. The checker models this **finite source witness**, not the cause or timing of FH's failed cycle.

Other positive paths clarify the value domain:

- Image0 startup0x333a8 explicitly clears derived+0 at0x333e8/0x333ea.
- Setter0x3286c preserves its caller byte in R5 and stores it to derived+0 at0x3287c.
- Its four aligned direct callers pass4 at0x329f8,1 at0x32a0c,2 at0x32a2e and3 at0x32ab6.

The bounded syntactic scan of image1 finds the immediate-offset C8 store at0x3958 and reads at0x3a12 and0x18c9e. Both reads compare with3 and take existing non3 branches when zero. This is not an alias-complete writer/reader census: computed stores, arbitrary indirect calls, later-loaded code and corruption remain outside this finite analysis.

## Restore-only consequence and its boundary

The stock formatter/sink at image1VA0x1b8c8 gets the main root through0x38fc. At0x1b8d6..0x1b8e0 it reads root+0x2406, masks bit0 and returns without formatting when that bit is zero. The exact pinned sink body contains no direct C8 reference. C8 is also a different object/domain from this root-relative logger field.

ET already qualifies the fixed logger write header and original restoration payload: root-relative logger CPU0x20012406, bus0x47012406, exactly two bytes `00 00`. FL verifies that FG retains that exact header and payload. Therefore the source dependency for turning off this previously owned logger does not require the AP_EXCO-derived selector to remain3. A known stock zero at C8 can be admitted **for restoration only**, with all other existing ownership and source checks retained:

- Positively reconstructed HeaderReady phase, no ambiguous header/payload or unjoined transfer, and valid device binding.
- Fresh source/root/mode/geometry and other profile checks, including fixed root0x20010000 and the existing AA/AC restrictions; independently qualified lagged scan0/1 semantics remain unchanged.
- Fresh exact logger halfword0 or1 with no upper-bit drift. Restore only the owned original zero halfword when1; an already-zero observation remains a no-write outcome.
- Exact completed restoration pair followed by checked readback0; successful transfer count alone is not restoration verification.

This is a narrow source justification for removing C8==3 as an *immutable cleanup identity requirement* when the known stock value is0. It does not justify dropping geometry/root/profile checks, accepting unknown C8 values, changing readiness or retrying a pending/ambiguous transaction.

FG's current implementation also has a separate control-flow issue: its exception handler records `o.Error`, and `finally` permits cleanup only while `o.Error==null`. A full-pair semantic context refusal therefore suppresses its cleanup even if the transport phase is ReadyForHeader. FL reproduces that source condition but does not edit it or retroactively relabel a failed receipt accepted. Since the original owner has closed, any recovery must be a separately reviewed finite restore owner based on the independently reconciled transaction/phase evidence. C8 zero alone does not erase a prior transport error or make the original process resumable.

No physical cause, event-time operand or real-time callback execution follows from this source result. It supplies the missing ordinary zero writer and removes the unsupported inference that C8 zero necessarily means context replacement.

## Reproduction and pins

Run from FL:

```
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/tcon-capstone python3 -B audit.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/tcon-capstone python3 -B -O audit.py
```

Both modes pass103 explicit checks and emit byte-identical JSON. Fifteen retained inputs are pinned, including the selected package, corrected object/callback provenance, FG Engine/Protocol/input pins, ET report/pins, FD pins, ER source verifier/parent pins and FI's frozen source audit. Source spans retain image, VA, file offset and SHA256 without copying OEM bodies. `validation.json` and `source-inventory.json` freeze the derived results. No target test was performed.
