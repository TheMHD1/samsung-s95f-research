# TCON receiver boundary: shared mailbox DMA resolved, executable still unidentified

The retained Linux source establishes another concrete edge into the boot receiver's shared-memory protocol: **the TCON-info resource DMA base also supplies the mailbox payload address, at DMA+0x20000**. This ties the existing boot-register handoff to the driver's actual mailbox sender. It does not identify a receiver executable or the instruction that appends the log at resource+0xa0000. No source-backed connection to the selected external RTP image1 was recovered in this finite analysis; a receiver that relays another processor's messages remains possible.

This directory contains host-only analysis. No target, network, root, USB, MMIO, driver operation, debugfs read, firmware execution, executable patch or deployment was performed. All new files are in this directory. OEM inputs remain in their original private retained locations; outputs contain derived coordinates, hashes and limited identity strings. Runtime metadata collected separately by the parent is outside this source audit and is not a loaded-image attestation.

## Positive source result

The exact module remains `soc/sdp_tcon.ko`, 226262 bytes, SHA256 `9b7c1cb8e2bb8d11e5465a41fa402e71bd8d15a5dabd6b3d76de98a7a42549ee`. Section offsets below are source coordinates in this AArch64 relocatable ELF, not live kernel addresses. FI pins FD/FF's reports, analyzers and input-pin files, and independently checks the additional instructions and relocations described here.

FF resolves the ordinary non-skip power-on handoff: `.text+0x2c00..0x2c28` gets resource-table row3's DMA slot, stores its low32 bits at boot-register base+8, and `.text+0x2c30..0x2c3c` writes magic `0x12345678` at the register base. The mapping instructions at+0x2ccc/+0x2cd4 construct physical `0x9d0654`. Consequently the base handoff destination is `0x9d065c`. This is a conditional source path, not an observed current boot or execution acknowledgment.

The new source chain is:

| Source coordinate | Exact relation |
| --- | --- |
| `.data+0x2b8` | Row3 is named `samsung,tcon_info`; row+64 is DMA slot `.data+0x2f8`. Its two physical cells at+0x2ec/+0x2f0 remain a distinct value. |
| `.text.unlikely+0x76c`, +0x77c | Both relocations name `.data+0x2f8`; the latter `LDR X1` obtains this same resource DMA result in `sdp_tcon_probe`. |
| `.text.unlikely+0x78c`, +0x790 | `ADD W1,W1,#0x20000` truncates to32 bits, then calls `sdp_tcon_msgbox_init` at `.text+0x7560`. |
| `.text+0x7594`, +0x75c4, +0x75d4 | Initializer preserves argument W1 and stores it in `.data+0xe7c`. |
| `.text+0x769c..0x76a4` | `sdp_tcon_send_to_msgbox` loads the saved low32 mailbox DMA into W24 and the mapped mailbox pointer from device+0x368 into X23. |
| `.text+0x7834..0x7844` | Computes `buffer_pointer - mapped_mailbox_pointer`, adds its low32 bits to W24 and writes the result to mapped TX register+8. |
| `.text+0x7848..0x7854` | Writes the packet length to TX+0xc. |
| `.text+0x7860..0x7870` | Writes `1 << channel` to TX+0x40 through `ft_write`. The helper at+0x4938/+0x493c is a store barrier followed by a32-bit store. |

`__sdp_tcon_send_msgbox` at `.text+0x79e0` positively connects the shared buffer to that sender: +0x7a48 loads device+0x368, +0x7a58/+0x7a60 passes it to the pack callback, +0x7a64 takes the callback's length, +0x7a6c takes the channel from packet+8 and +0x7a74/+0x7a78 passes the buffer into `sdp_tcon_send_to_msgbox`. These are source edges into the receiver protocol; FI did not call them.

The probe separately maps resource `msgbox-tx`: string relocations at `.text.unlikely+0x298/+0x29c`, `devm_ioremap_resource` call at+0x2c8 and device+0x360 store at+0x2cc. Candidate DTB1 associates `msgbox-tx` with physical `[0x9d0480,0x44]`, and `msgbox-rx` with `[0x9d0400,0x44]`. Thus the candidate TX pointer/length/trigger registers are `0x9d0488`, `0x9d048c` and `0x9d04c0`. These literals describe this candidate firmware tree; no live DT/register check was made. They are not target-operation instructions.

The actual source arithmetic is:

```
boot_base_low32 = low32(resource_DMA)
mailbox_base_low32 = low32(resource_DMA + 0x20000)
packet_pointer_low32 = low32(mailbox_base_low32 + buffer_relative_offset)
```

This common resource proves that the driver's boot and mailbox paths belong to a shared protocol layout. It does **not** prove how the unseen receiver extends these32-bit values, what a live DMA mapping returns or that physical and DMA addresses coincide. Candidate DTB physical `0x15fe00000` is not substituted for `resource_DMA` in this audit. The arithmetic examples in the report are explicitly hypothetical values.

## Why the update loader does not identify the receiver

The function named `sdp_tcon_load_update_image` is a tempting lead, but its exact destination differs from the log and mailbox:

| Resource-relative offset | Mapping bytes | Device pointer slot | Source mapping coordinates |
| ---: | ---: | ---: | --- |
|0|0x20000|+0x390; alias+0x330|`.text+0xc94..0xcac`|
|0x20000|0x40000|+0x368|`.text+0xcb0..0xcc0`|
|0xa0000|0x20000|+0x378|`.text+0xcc8..0xcd8`|
|0xc0000|0x30000|+0x370|`.text+0xce0..0xcf0`|

At `.text+0xcdc4/+0xcdcc`, the caller-supplied update-body branch copies into device+0x370 using imported `__memcpy_fromio`. The file branch clears the same mapping at+0xce04..0xce10, opens a caller-supplied filename at+0xce1c, and reads into that pointer at+0xce48..0xce58 before closing. This positively identifies **update staging at physical-resource base+0xc0000**. It does not locate the initial receiver image, establish an initial executable load, or make the staged update body the producer of the adjacent log. No update path was invoked.

## Bounded retained-asset search and its limits

The already retained historical1405-byte log prefix contains three precise search anchors: banner `RHEA_M_TCON_FW_20250103_1715`, the separate field `TCON Image Info : F77ABU2D20`, and `Msgbox ISR In Ch : 2`. These are historical text identities, not a current receiver-PC assertion. In particular, the image-info field does not by itself name the image that runs the banner/append code.

FI searched the three exact anchor prefixes `RHEA_M_TCON`, `TCON Image Info` and `Msgbox ISR In Ch` in these frozen retained corpora:

| Corpus | Regular files scanned | Regular-file bytes | Exact anchor matches |
| --- | ---: | ---: | ---: |
|Accepted extracted PLTF root|57038|2316227025|0|
|Accepted extracted PRD root|912|119602453|0|

The manifest is a sorted digest of each regular path, size and complete file SHA256. Symlinks are counted and skipped without following their targets; no device or special file is opened. These counts describe the analyzer's regular-file corpus and must not be substituted for the extractor's catalog-record/link counters. Every read error is fatal. The frozen manifest hashes are in `input-pins.json` and `derived-report.json`.

Separate pinned raw-body checks also find no exact anchors in `seret.bin`, `secos.bin`, `secos_drv.bin`, `ddr.init`, the extracted kernel Image or the selected5MiB external package SHA256 `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`. The latter package is already the source-qualified external image1 container; its linkage remains FILE=VA+0x40200 in DF. FI adds no claim about live instruction fetch.

These are finite **exact-text search results**, not executable absence proofs. They do not decode every compressed/encrypted object, qualify unretained boot partitions, or identify firmware loaded before Linux. Even a raw register/magic search is insufficient: FI checks that the known Linux writer's entire `.text+0x2af0..0x2e3c` body contains neither raw little-endian `0x9d0654` nor raw `0x12345678`, although positive instruction decoding establishes both constructed values. A receiver may similarly construct constants or receive pointers indirectly.

## Exact unresolved edge

The required missing artifact is still a source-qualified receiver body with its loader/container and instruction-address mapping. A bounded next source task can now require all of the following positive edges in that body:

1. Consume the `0x9d0654` boot magic and base published at+8, or a source-qualified translated alias of that interface.
2. Resolve the mailbox payload pointer handed off by the TX protocol above, including the receiver's32-bit address-extension/translation rule.
3. Define the resource+0xa0000 header and find the actual append/index-update instructions, ideally anchored to the retained exact banner/ISR strings.
4. Follow that producer's inputs to determine whether it generates only internal messages or receives external-controller data. A concrete handler/buffer/message edge to the selected image1 logger/decision is required before attributing any log text to RTP.

The new mailbox edge sharply specifies an input to match; it does not supply its destination instruction. No receiver container was identified, no producer instruction was recovered and no proxy was excluded. Nothing here closes FP, selected-A, comparison score or caller-LR blindspots. FD's separately bounded reader candidate and ET's external stock event-argument design retain their existing qualifications; FI implements neither.

## Reproduction and freeze

From this directory, run:

```
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/tcon-capstone python3 -B audit.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/tcon-capstone python3 -B -O audit.py
```

Both modes pass207 explicit checks and emit byte-identical reports. The checks include19 individual retained input pins, both complete regular-file corpus identities and exact-anchor scans, source instruction/relocation facts, mapping destinations, DMA arithmetic and search-boundary assertions. They are host source/model checks, not hardware tests. `validation.json` records report hashes/equality; `source-inventory.json` inventories only FI's derived artifacts. No OEM binaries or complete disassembly are copied into FI.
