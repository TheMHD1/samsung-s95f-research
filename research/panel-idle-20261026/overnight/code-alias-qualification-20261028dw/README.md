# Selected image1 code alias and fixed fingerprint proposal

**The selected source positively identifies0x46000000 as the image1 code-bank alias.** This closes the source-level bank/tag ambiguity for a bounded read-only fingerprint proposal. It does not establish live USB DMA accessibility, full executing-image identity, executable write permissions, or hook installation safety. This work performs no target/root/network access and creates no helper, deployment, patch or hook.

The input is the5242880-byte selected package `selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin`, SHA256 `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`. Image0 file=VA+0x200; image1 file=VA+0x40200. All source slices are pinned in `source-qualification.json`; `reviewed-disassembly.txt` contains bounded instruction excerpts. The check script passes194 explicit checks in normal and optimized Python with identical generated artifacts.

## Exact mapper and tag meaning

Image1 VA0x1bb74 and image0 VA0x39d4c contain the same80bytes, including the upper-bound literal. They implement this address conversion:

| Tag and pointer range | Result |
|---|---|
| Any tag, pointer0 |0/null|
| tag0,0<pointer<0x40000 |pointer+0x44000000|
| tag0,0x20000000≤pointer<0x20020000 |pointer+0x25000000|
| nonzero tag,0<pointer<0x20000 |pointer+0x46000000|
| nonzero tag,0x20000000≤pointer<0x20020000 |pointer+0x27000000|
| Otherwise |0/null|

The tag is not a length, a Thumb bit, USB operation, or a request to map the caller's current core. It selects the global image/resource bank. The branch treats all nonzero tags alike; the actual caller below uses exactly1. The mapper only checks the start pointer, so the proposed complete read interval is independently bounded below0x20000.

This meaning is established by concrete callers and packaged directory contents, rather than naming the branches from their constants:

1. Image1's AP_EXCO lookup at0x1bcde..1bce2 passes tag0 and resolves image0's directory at0x1000c. The resolved image0 context is0x200158a8, translated to0x450158a8. This is the prior DF cross-core SLG bridge.
2. The reciprocal image0 function at0x3a120 waits for its selected readiness condition, then0x3a134 supplies the literal name AP_EXCO,0x3a136 sets r0=1, and0x3a138 calls resolver0x39dac.
3. Resolver0x39dac preserves that tag in r6. Its literal at0x39dd0 is directory selector0x1000c. Walker0x39dd4 maps the directory through0x39d9c→0x39d4c, then maps its count pointer, table pointer and each name pointer with the same saved tag.
4. The **image1** directory at linked0x1000c contains `[0x1c458,12,0x1c44c]`; count0x1c458 is12. Its sole row at0x1c44c is `[name0x1d64c,context0x20000500,length0x96c0]`, and that name is AP_EXCO. Those values differ from image0's directory.
5. Therefore the actual tag1 lookup reads directory0x4601000c, count0x4601c458, table0x4601c44c and name0x4601d64c. The name is passed to strcmp0xc04, whose0xc08/0xc20 instructions load words from its translated r0 pointer. After the match,0x39dc6 loads the row's context pointer and0x39dc8 translates it to0x47000500.

Thus the source already uses the0x460… bank for ordinary resource/count/name reads and pairs it with the0x470… image1 SRAM bank. These are explicit source-backed code/resource aliases, not a guessed peripheral/MMIO interval. The selected lookup is conditional source behavior; this audit does not claim its live execution was observed.

## USB target0x101 interpretation

The resource tag above and the USB header's numeric target are different interfaces. **No resource tag is transmitted in the proposed USB packet.** The packet contains the already converted bus address.

Image0 header parser0x28f50..28f60 copies header length/target/address into state+8/+c/+4. Validator0x29266 extracts the target's high family; for0x101 this is1. The validator's nonzero-family branch0x2927e..29282 writes the remap flag0. The explicit0x101 acceptance is0x292de..292e6. The address-range checks0x29388..293ae apply only to family2; they do not authorize arbitrary family1 memory.

The low-operation normalization at0x28fbe..28fc4 reduces0x101 to1. Operation1 sets transfer mode0 at0x2905a..2905e, superseding the parser's initial sentinel2. The remap flag0 skips selector mapper0xefa4 at0x290cc. Operation1 then loads the **unaltered state+4 address** into r2 at0x290fe, loads the clamped length into r3 and calls IN scheduler0x8054 at0x29106.

Scheduler0x8054 retains the source pointer at endpoint-state+0x10/+0x14. The IN path at0x2ac42..2ac48 passes that pointer and exact active length to descriptor builder0x280c. At0x296e..2970 the builder places source+offset into the descriptor. A16-byte nonzero IN uses its requested remainder, rather than widening it to a full endpoint packet. Optional additive checksum handling may also read the same four32-bit words through helper0x4650; it does not execute the sampled code. This audit does not depend on that checksum flag being disabled.

The handler changes protocol state and DMA registers as any normal request does. It does not select the0x102 memory-write path, call through the sampled code pointer, or write the sampled code region. Source-level ordinary CPU reads through the bank do not prove the USB DMA master can read it successfully. Existing descriptor and SRAM acceptance qualify their own addresses; they are not live proof of the new code interval. A timeout/short/ambiguous transfer must retain the Unknown phase and prohibit another header.

## Smallest fixed proposal

`fixed-read-plan.json` proposes exactly four16-byte reads,64 input bytes,4headers/8bulks, with no scan, alternate bank, fallback or retry:

| DS role | Image1 linked window | Bus address | Package file offset | Covered DS site |
|---|---|---|---|---|
| Predicate |0x2020..202f|0x46002020|0x42220|0x2024|
| Selection |0xbd58..bd67|0x4600bd58|0x4bf58|0xbd58|
| Tuple |0xc5d0..c5df|0x4600c5d0|0x4c7d0|0xc5d0|
| Common setter |0xc1e0..c1ef|0x4600c1e0|0x4c3e0|0xc1e0|

All four windows are32-bit aligned and wholly within the nonzero-tag code range. The requested bd58 window is8-byte aligned, **not16-byte aligned**; its16-byte size must not be confused with16-byte alignment. All windows cover their complete4-byte DS displaced span, and every expected image1 window differs from image0 at the same linked address. The plan records exact little-endian0x101 headers and SHA256 identities without duplicating raw OEM instruction bytes.

A future fixed reader would need an exclusive allowlist of these four headers, the current device/boot/FD/descriptors/native owned-claim proof, centrally maintained fresh first-header premise, exact matched OUT/IN obligations, bounded native/transport execution, exclusive receipts, raw hashes and final release/close/stage cleanup. It must complete each full pair before the next header, retain mismatching payloads as negative evidence, and stop after ambiguity. Those transport mechanics are already available in reviewed read-only helpers but are not implemented or retargeted by DW.

Successful comparison means only that these four sampled64bytes at the source-qualified bus aliases match the selected package during that capture. It does not prove whole-image equality, every potential branch/caller, active instruction-fetch mapping at the same instant, code writability, cache visibility, scratch ownership, atomic install/remove, logger timing or rollback after transport failure. All other DS deployment blockers remain. The exact next bounded evidence is these fixed payloads under a separately reviewed reader—not a guessed wider MMIO scan or an executable patch.

Reproduce offline with `PYTHONPATH=/tmp/tcon-capstone python3 check_source.py` and the same command using `python3 -O`. The script reads the pinned local package and writes only its own deterministic plan, source qualification and disassembly. It imports no root/USB adapter and performs no OEM code execution.
