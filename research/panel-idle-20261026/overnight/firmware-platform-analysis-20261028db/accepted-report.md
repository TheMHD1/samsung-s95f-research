# Accepted platform extraction and bounded new-library map

The complete platform.img is now accepted and both contained VDFS filesystem extractions completed without reported errors. This supersedes the pending state in report.md; that original provisional checkpoint and source-inventory-prefix-checkpoint.json remain unchanged. OEM binaries, decoded catalogs, disassembly and complete trees stay under private/ and are excluded from public export.

Parent acceptance inventory SHA256 is60a1b0582ce0cf8563ebfa66b044abbf35ee139f0ea01b00bf85d033948123bc. The fixed extractor independently rehashed all1455423488 original bytes to2dfddafce5759b65982262aac7c5327bdfb032f5a774f23da665a106a3446349 before copying partitions. Its accepted-record gate requires ciphertext RSA, strict padding and original CRC acceptance. Both GPT headers and entry arrays pass CRC and primary/backup identity checks. Previously provisional prefix/superpage/table samples were compared byte-for-byte against this accepted file and match.

| Partition | Original image offset | Bytes | SHA256 |
|---|---:|---:|---|
|pltf_t.img|1048576|1391460352|0e6bbbca5a2659c830875a077cdb25f06b270ebc51bbec6282a30278aa7d949f|
|prd_t.img|1392508928|61865984|e369344dbb9d4a814e297f5f92d9e75a10127ab24776148a2aff7fccfb324c39|

Both partitions are VDFS2007. The DC reader wrapper and patched binary were hash-checked before execution: wrapper961e08dd2bae7b6d2cf840c993659472f1740975a28767bb1b02578c0fb82222; binary3009d0ae8ee77b0a4bdd491675897cdace71ea9b1d7ea03cd08a4e25f7c85c7a. Runs used its minimal read-only-root/network-isolated userspace sandbox with only fresh private result trees writable. Filesystem images were not mounted and OEM code was not executed. Sandbox private bind mounts are recorded separately.

| Result | Catalog records reported | Files | Links | Directories | Decompressed bytes | Errors |
|---|---:|---:|---:|---:|---:|---:|
|PLTF catalog/full extraction|167689|58457|26073|24124|2316227025|0|
|PRD catalog/full extraction|2737|1122|246|247|119602453|0|

Full extraction took8.654seconds PLTF and0.496seconds PRD in their retained result records; source identities and full hashes remained unchanged. Catalog-only runs also report0errors. Emitted CATALOG lines number108654 PLTF/1615 PRD, corresponding to the supported record classes; the larger catalog-record counters must not be confused with emitted paths. No VDFS per-file RSA authentication or full filesystem-schema validation is claimed. These outcomes are stronger than an exit-code-only assertion: the wrapper additionally checks final counters, empty stderr, timeout absence and unchanged input SHA.

Qualified private roots, relative to this analysis directory:

- private/pltf-extracted/tree/root/
- private/prd-extracted/tree/root/

Partition-inventory.json and each catalog/extraction result.json retain exact inputs, tool pins, counts and qualifications. Source symlinks are interpreted as link metadata for analysis; they are not followed as host paths. Full trees are not public report attachments.

## Known binary identity

The newly decompressed qdf_tcon.ko(403294bytes), tztv_frc_tcon.ko(254406), tztv_frc_tcon_api.ko(317998), sdp_frc.ko(1053302), sdp_tcon.ko(226262) and sdp_pqe_frc.ko(1015070) all match the existing live-acquired copies byte-for-byte. Exact paths/SHA256/source matches are in module-identity-comparison.json. This confirms existing offsets for these files; a smaller compressed fork size in a catalog is not evidence of a changed module.

The emitted PRD catalog and extracted tree contain only two zero-byte dummy.bin files under lib/firmware/tcon/default_tcon/{tcon_flash_data,tcon_flash_fw}. The FRC default firmware/data directories likewise contain placeholders. No TconFw/F_RSM1 basename was found in the bounded emitted platform catalogs. This closes only these package filesystem paths; it does not establish that the separately decrypted factory_peq section or executing MCU lacks firmware. Broad strings such as rtp in media libraries do not identify the panel's packed RTP ring.

## New libtconfw.so

PRD usr/fwupdate/controls/libtconfw.so is12790bytes, ARM32 EABI5 ET_DYN, not stripped; SHA25632b8b7005a239e2cbfe0327f2ef829c2571b2138300583d07a7c3af1a1696df4, build-id e0382c3996f80cf24ee10dfbf0e617a00f492d91. A bounded search of existing binaries/overnight copies found no prior live-acquired counterpart. Runtime loading/binding was not observed.

Its dependencies include libave.so.0 and libdlog.so.0. The symbol/source metadata identifies tconfwUpdateAPI.cpp under a libave-6.5.0.0/firmwareupdate/tconfw build path. The small plugin provides eight exported wrappers:

| Exported Thumb symbol VA | Function | Direct AVE import/call site |
|---:|---|---|
|0x7c9|setContext|strcmp at0x7d6; local context store at0x80c|
|0x871|doUpdate|ave_api_do_update at0x890|
|0x985|doUpdate_decryption|ave_api_do_update_decryption at0x99c|
|0xa71|getExpectedTime|ave_api_get_update_expected_time at0xa86|
|0xb59|getActiveVersion|ave_api_get_active_version at0xb64|
|0xbed|getEMPID|ave_api_get_emp_id at0xbfc|
|0xcb9|checkVersion|ave_api_check_doupdate at0xce8|
|0xdf1|allUpdateDone|ave_api_all_update_done at0xe00|

Addresses are ELF symbol/code VAs in this particular file, not runtime addresses. Remove the Thumb bit for instruction addressing. libtconfw-map.json retains exact function extents/hashes and PLT relocation mapping; full selected disassembly/readelf evidence is private.

setContext compares the first argument with literal libtconfw and, on equality, stores its second argument to local update_type at ELF VA0x1204c. doUpdate accepts unsigned types0..2 and calls ave_api_do_update with first argument2, followed by its two caller arguments. doUpdate_decryption requires exactly type3 and calls ave_api_do_update_decryption with the same subsystem argument2. allUpdateDone similarly permits0..2 before calling AVE. No enum meaning beyond these exact values is inferred. Version/EMPID/time/check wrappers delegate to their corresponding AVE APIs, with argument/output/error handling and dlog formatting.

This is a firmware-update plugin, not a newly established packed-RTP producer. Its bounded call map contains no direct ioctl/USB/MMIO or separately named quiesce/reset endpoint; downstream AVE behavior is not resolved by this wrapper. Aligned word scans do not find0x20253002,0x60000000,0x4701240a or0x584109a4, which is only a bounded literal observation, not proof that a downstream indirect path cannot reach them. No updater or version call was invoked.

.gnu_debuglink requests libtconfw.so.debug with CRC0x11125ef6. No matching target pathname or matching build-id entry was found in either emitted catalog. The existing symtab improves function identity but is not full DWARF/source recovery. The PLTF build-id directory does contain266 symlink metadata entries, none matched qdf_tcon/libave/libtconfw in the bounded target check; unrelated debug links must not be treated as symbols for these files.

## Handoff

The complete accepted filesystem trees now support targeted static work without additional TV reads. The next useful edge is resolving the seven ave_api_* definitions in actual retained/packaged providers and following their update/resource/blanking behavior, while preserving byte identity and address conventions. Separately, controller assets/configs must be positively matched to the selected known factory image and the CB packed-RTP producer predicates; the updater's existence does not close that bridge or prove blackout causation.

The parent owns deeper display-path analysis and live trial coordination. DB adds no live operation or proposed protection change. platform_partitions.py and its12-test suite remain frozen at their passing source pins. accepted-outcomes.json supplies qualified machine-readable roots/counters, and public source inventory explicitly excludes OEM tree content.
