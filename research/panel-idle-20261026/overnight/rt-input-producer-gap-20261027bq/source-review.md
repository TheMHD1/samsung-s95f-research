# Additional RT-input scheduling edge, with producer still unresolved

Root records the independent read-only rt_block_sampler_review analysis; no target operation occurred. All address meanings are conditional on selected image0. The full selected package and exact source slices are pinned in source-pins.json.

The direct BL caller census finds only13552 ->219c,1355a ->18ba0,13640 ->18b20. Function219c zeroes CPU200007bc, configures resource2 through27f30 with arguments1/4/1, then enables it via27e4c(2,2). This setup occurs in ordinary callback13464 before the already known Pre-PD consumer path18b20 ->19064.

Decoded scatter row0 maps resource2 at CPU20000448 to register block40122000 with paired value3. Generic27f30 passes that block to c98c, which writes offsets+c,+24,+14 then sets+c bit0. Enable27e4c sets block+4 bit0 and the NVIC enable bit derived from3. Matching vector19 is4055; wrapper4054 uses runtime slot20000928 when nonzero, otherwise table20000468+8 supplies27411. Scatter initializes the dynamic slot to zero.

The selected default handler27410 reads40122000+1c, acknowledges+20 and toggles+c. It does not touch584109a4. A runtime callback can replace that default, so this is source initialization, not proof of the current handler. This is a new cadence/register/IRQ edge before the reader; it is not the missing producer and supplies no physical sensor/pixel/histogram interpretation.

The unclosed boundary is the runtime writer or DMA descriptor for [584109a4,58410aa4). Existing source censuses have found packaged type7 loading plus readers, but no runtime writer. This address domain has no qualified CPU2000 SRAM alias or retained live view. Current stored image0 does not byte-match these selected functions, so no whole executing-image identity is claimed.

To close that boundary requires the owning firmware/core or descriptor, an authoritative address map, or a separately technically qualified view of those256bytes across content states. Repeating late44>40 calculations cannot identify its producer. No patch, protection bypass, new recorder or vendor read is proposed by this report.
