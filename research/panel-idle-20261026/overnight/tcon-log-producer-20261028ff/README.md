# TCON log buffer: exact address handoff, unresolved firmware producer

The log resource has a **concrete SoC boot-control handoff**. In the retained `sdp_tcon.ko`, the ordinary TCON power-on path publishes the `samsung,tcon_info` resource's DMA base to physical register `0x9d065c`, after publishing a separate resource at `0x9d0658`, and then writes magic `0x12345678` to `0x9d0654`. This is an on-chip register sequence, not an external controller F3/I2C/USB packet.

That establishes a consumer of the resource base in the boot-control path. It does **not** identify the firmware instruction that produces text at resource+0xa0000, name the loaded receiver binary, or exclude a firmware proxy for external-controller messages. The finite audit stops at that receiver/producer boundary. It does not promote the Linux log into an external RTP decision logger.

This is host-only source analysis. No target/root/network call, new physical read, operation invocation, reset, boot/flash action, UART scan, logger enable, executable modification or change outside FF occurred. No persisted/high-bank/POFLG route was followed. FD and all earlier source/capture/publication files are unchanged.

## Exact retained input and domains

Module: extracted `soc/sdp_tcon.ko`,226262 bytes, SHA256 `9b7c1cb8e2bb8d11e5465a41fa402e71bd8d15a5dabd6b3d76de98a7a42549ee`. It is symbol-bearing AArch64 ELF. Addresses written `.text+...` and `.data+...` below are **module section offsets**, not running kernel addresses. Hardware numbers in the register table are physical literals recovered from the driver, not target-read instructions or proposed `/dev/mem` addresses.

Five input pins cover this module, FD's frozen report/audit, CS's candidate DTB1 metadata and its firmware/kernel identity report. Exact function-range hashes and instruction/relocation checks are in `source-audit.json`; no OEM source bytes or complete disassembly are copied here.

## Resource identity survives through the handoff

The parser at `.text+0x920` finds DT node `sdp_mmap`. Its table starts at `.data+0x1e0`, has four0x48-byte rows, and each property supplies three32-bit cells. The first two form the64-bit physical address; a distinct64-bit slot at row+64 retains the mapped DMA address.

| Row | Property | Row section offset | DMA slot relative to table start |
| --- | --- | ---: | ---: |
|0|`samsung,tcon-y`|0x1e0|0x40|
|1|`samsung,tcon-c`|0x228|0x88|
|2|`samsung,demura`|0x270|0xd0|
|3|`samsung,tcon_info`|0x2b8|0x118|

At `.text+0xa58..0xa5c`, the driver saves the table pointer at device+0x3a8. The power-on path later loads exactly this pointer; thus the0xd0/0x118 loads are specific rows, not numerical resemblance to another memory object.

FD's Linux log reader uses the fourth row's **physical** cells, adds0xa0000, maps0x20000 bytes and saves the pointer at device+0x378 (`.text+0xc84..0xcd8`). The debugfs read callback at+0x61b0 loads device+0x378. Candidate DTB1 gives `samsung,tcon_info=[1,0x5fe00000,0x100000]`, yielding candidate physical base `0x15fe00000` and log subregion `0x15fea0000..0x15fec0000` exclusive. Live DT patching and live pointer identity remain unverified here.

The parser's DMA mapping result is separate from those physical cells: it can go through the platform DMA operation or direct resource-mapping path, then stores the result at row+64. The boot handoff uses this **DMA result**, not the physical cells. Do not silently equate DMA and physical addresses, or assume its upper32 bits are transmitted.

## The actual boot-control chain

`tcon_ctrl_power` contains direct calls to `tcon_ctrl_tcon_micom` at `.text+0x2ef4` and+0x2f70. The latter function starts at+0x2af0, takes the device as its first argument and uses a device mutex. Its off path calls `sdp_tcon_dev_POWER_OFF`; this investigation does not invoke either path.

The ordinary on path sets an internal execution flag to1 at+0x2bac, then calls `sdp_tcon_dev_POWER_ON` at+0x2bb4. The callee at+0x4d88 executes two fixed table loops through imported `sdp_set_clkrst_mux` at+0x4dc8 and+0x4e04. This is positive clock/reset-control code evidence; it is not an instruction-image reload proof.

The function separately maps a16-byte register region starting at physical `0x9d0654` (`.text+0x2ccc..0x2ce0`). On the admitted non-skip path, the exact ordered stores are:

| Source instructions | Destination | Value |
| --- | --- | --- |
|2bfc..2c10|register base+4 =0x9d0658|low32(table row2 DMA address), after `dmb oshst`|
|2c14..2c28|register base+8 =0x9d065c|low32(table row3 DMA address), after another `dmb oshst`|
|2c2c..2c3c|register base+0 =0x9d0654|0x12345678, after another `dmb oshst`|

The stores are `STR W...`, so only32 bits of each DMA result reach these registers. For example, **if** a DMA result were0x15fe00000, the written value would be0x5fe00000. This is an arithmetic example, not a measured DMA address or a proof of the receiver's address-extension rules.

The sequence is conditional: `.text+0x2bf0..0x2bf8` tests the register pointer and the execution flag, with a branch that skips these stores. The low-power-resume case can clear the flag at+0x2c98; its diagnostic contains “skip ucom.” No claim is made that every on request republishes the bases, that the on path ran on the current board, or that the boot magic is an execution acknowledgement.

Importantly, this handoff publishes the **resource base**, not a separate explicit `base+0xa0000` log pointer. The log offset is a positive Linux reader convention. The unseen receiver may share that layout, but this audit has not recovered the receiver code that establishes it.

## What this resolves and what it excludes

This closes the prior source gap between a generic mapped debugfs buffer and a concrete TCON boot-control resource. The same driver parses the named resource, maps its log subregion for Linux, and passes the corresponding DMA base into an on-chip power-on handshake. That is stronger than identifying the buffer by the string “micom.”

It does not establish an internal-only **text producer**. An internal receiver might generate its own logs, relay another processor's messages, or never run on this configuration. Neither names nor a boot-register address can exclude such proxy behavior. No direct producer store, current log contents or source PC was observed. The source result therefore retains `firmware_instruction_producer_identified=false` and `external_controller_proxy_excluded=false`.

It also does not bridge to selected external image1's ring at direct0x20200000, its logger gate at0x47012406, or its comparison/setter sites VA0x2024/0xc1e0. Those are another CPU/address domain. No hardware alias between them is established. The receiver handoff does not justify a Linux kprobe on an embedded linked VA.

## Exact next evidence gap and stopping point

The next needed artifact is the **receiver firmware/body for the0x9d0654 handshake**, with code that consumes the+8 resource base and defines/writes its+0xa0000 log layout. A matching retained binary plus its loader/base provenance would let a bounded follow-up locate actual text producers and any external-message proxy. This audit has not identified that binary or an instruction-address mapping for it, so it does not guess an FRC asset, scan arbitrary memory, follow an update/flash path, or call any driver operation to obtain one.

For immediate instrumentation choices, FD's one fresh-open4096-byte debugfs read remains only a source-bounded candidate in this separate domain. Its copy-completeness and producer limits remain intact. ET's prospective combined-owner stock external event logger remains the direct path to an external event argument; it still does not supply actual FP or caller LR. No new live helper is implemented by FF.

## Reproduction

Run `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/tcon-capstone python3 -B audit.py` and the same command with `python3 -B -O`. Both89-check outputs are byte-identical. Checks cover source hashes, ELF relocations, parsed row identities, exact handoff instructions/callers, conditional skip,32-bit store truncation, distinct DMA/physical values, and the candidate DTB resource. They are host source/model checks, not device tests. `validation.json` and `source-inventory.json` freeze the results without copying OEM inputs.
