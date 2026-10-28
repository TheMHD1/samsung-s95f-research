# Platform partition and VDFS analysis

This phase inspects bounded snapshots of the still-streaming platform output. Every finding below is provisional until the parent accepts complete native/transport counts, strict AES padding, original-size CRC and promotes the original platform.img. No whole-platform acceptance or VDFS signature verification is claimed here. No TV/root/network, mount, filesystem repair or OEM execution occurred.

The retained prefix is one fixed1MiB read at offset0, repeated identically, with SHA2561864037df7709fae4b232608d0328ae68c20ac5460fa93c53e2a34816f6f9a3e. The source was168558592 bytes at the snapshot; it subsequently grew. Source inode/device/size/time and all sample offsets/hashes are retained in prefix-snapshot.json and vdfs-provisional.json. Binary snapshots remain private0600 under private0700. They are not public export artifacts.

## Positively validated primary GPT

The protective MBR signature/type/extent is valid. The primary GPT is revision1.0,92-byte header,512-byte sectors. Header CRC is0x7c23616a and entry-table CRC is0xeb9c31ce; both independently recompute correctly. The128 entries are128bytes each. The GPT's2842624-sector image size is1455423488bytes, equal to the authenticated CF original-size expectation. The backup table/header are near EOF and are intentionally pending until complete verified input is supplied.

| Partition | First LBA | Last LBA | Byte offset | Byte count |
|---|---:|---:|---:|---:|
|pltf_t.img|2048|2719743|1048576|1391460352|
|prd_t.img|2719744|2840575|1392508928|61865984|

Both entries use Linux filesystem type GUID0fc63daf-8483-4772-8e79-3d69d8477de4. Their names do not by themselves bind a running mount or eMMC partition. There are no additional nonempty primary entries. pltf_t.img starts VDFS2007. prd_t.img's filesystem header had not arrived at the bounded snapshot and is not guessed. unsquashfs is therefore inappropriate for the observed first partition.

## VDFS2007 source-bound structure checks

The retained vdfs-team/vdfs4 layout header, pinned tree dfb2450427477c7b1eefb0a8580e92c24feba3b4, supplies field offsets for this bounded interpretation. Primary-source reference: https://github.com/vdfs-team/vdfs4/blob/dfb2450427477c7b1eefb0a8580e92c24feba3b4/vdfs4_layout.h . This analysis used its already retained offline copy and made no network request.

A fixed8192-byte snapshot at platform offset1048576 contains two identical4096-byte superpages. For each page, the volume-begin sector, superblock copy at+0x200, superblock at+0x400 and2560-byte EXSB at+0x600 all pass their own stored checksums. These use Linux crc32_le(seed0,no final xor), equivalent to zlib.crc32(data,0xffffffff)^0xffffffff, rather than zlib's default seed/result. Passing these checks is consistency evidence, not filesystem RSA authentication.

The superblock declares block size4096, metadata bnode size16384, read_only byte1, image_crc32_present byte0, raw hash_type2, raw sign_type1, mkfs1.64-241105, image_inode_count83168 and maximum_blocks339505. The EXSB's raw counts are60407 files and1 folder; no complete catalog was read, so these counts must not be substituted for observed extracted files. The meta extent begins at block324393 with15108blocks, near the end of the partition. Catalog availability therefore depends on the remaining transfer; scanning the early data prefix cannot replace the catalog.

The translation-table extent is block6,length15, already available. A fixed61440-byte snapshot at absolute platform offset1073152 starts CoWB. Its checksum offset0xec78, stored/computed CRC0xbc7e1711, sync1 and mount0 agree with the retained snapshot descriptor layout. Last-page indices are[3099,0,1,0,674]; translation offsets are[104,0,49704,0,49736]. Exact snapshot hashes/offsets are in vdfs-provisional.json; full metadata bytes stay private.

No VDFS userspace reader was installed. The existing gtors/vdfs-unpack snapshot was incomplete (README and decompress.rs only), although its full tree inventory pinned commit0bc1e65b74016fbd59d5d68f09ab7920044be1f9. The DC owner is independently acquiring/building and containing that reader. Its pristine implementation must not be treated as fully qualified: noted gaps include LZO support, hZip chunk/auth-trailer handling, path safety and success status despite per-file errors. DB does not run it uncontained or declare a filesystem extraction complete based on exit0 alone.

## Complete-input extraction tool

platform_partitions.py is dry by default and reads only the fixed retained prefix snapshot. Its explicit extraction path accepts only the fixed official private platform.img and an exact SHA256 pin of the parent extraction-inventory.json. The inventory must contain one1001/platform.img record with exact1455423488bytes, ciphertext RSA, strict padding and original CRC accepted, installed=false and a lowercase full-file SHA256.

Before creating output, extraction checks a private regular source, exact full source size/SHA, source identity stability, both GPT header CRCs, both entry-table CRCs, primary/backup agreement, nonoverlapping usable extents and this exact two-partition name/type/offset/count profile. It then copies only fixed PROFILE extents in bounded1MiB reads to exclusive private partial files, hashes/counts/fsyncs them, checks source stability and links them into fixed partition names. It never mounts, invokes filesystem code, uses names from the GPT as paths or executes extracted data. Failures retain evidence and stop without retries.

Expected output after acceptance: private/partitions/pltf_t.img, private/partitions/prd_t.img and private/partitions/partition-inventory.json. The output leaf must be fresh. No extraction of the actual still-streaming input has occurred in this phase. Twelve host tests pass normally and with python3 -O, including valid/malformed primary and backup GPT, checksum-preserving overlap rejection, acceptance-gate failures, exclusive fresh output, a complete tiny synthetic extraction and the actual provisional primary GPT.

## Targeted catalog handoff

After parent acceptance and DC catalog qualification, inventory names/IDs/modes/file lengths first. Priorities are:

- Exact installed module/library counterparts: qdf_tcon, tztv_frc_tcon/API, sdp_frc/tcon/pqe/display/micom providers, libave and HDMI/control libraries. Compare whole-file hashes to the retained live-acquired copies before reusing offsets or symbols.
- Controller firmware and board assets under firmware/tcon/QD, factory_peq/tcon_data/QD, TconFw/F_RSM1 naming families, and ELVDD/AP_RTP/PrePD/RT-P configurations. A name is a candidate, not proof of the executing controller image.
- Debug/symbol/config material: .debug/.symtab/build-id paths, kernel config/Module.symvers/generated ABI data, vendor DTBs, logging owner registrations and protection parameter schemas.
- The specific open producer edge: packed RTP ring0x20253002,stride0xb68; descriptor/aperture copies at0x60000000 and optionalA15000/15f10; C+7/0x4c4 selection; selected mode1 comparison threshold40 with observed A0count44. Candidate code must have positive instruction/dataflow evidence and exact source hashes/offsets. An unrelated0x584109a4 image producer is not an interchangeable explanation.

Full-platform acceptance, backup GPT validation, second-partition identification and actual catalog/file extraction remain pending in this checkpoint. No conclusion about root cause, prevention settings or physical emitted light follows from these partial bytes.
