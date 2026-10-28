# Offline VDFS2007 userspace reader acquisition, build and qualification

**Working and qualified for the two actual accepted S95F platform partitions.** The pinned userspace reader built from source, cataloged both VDFS2007 volumes, and extracted their contents inside a minimal private namespace with zero reported file failures. No TV/root-controller request, filesystem-image mount, kernel module load or OEM executable execution was used for this work.

## Reproduction and provenance

Primary reader upstream: [gtors/vdfs-unpack](https://github.com/gtors/vdfs-unpack/tree/0bc1e65b74016fbd59d5d68f09ab7920044be1f9), commit `0bc1e65b74016fbd59d5d68f09ab7920044be1f9` (the acquired master was the same commit). The existing research snapshot contained only README/decompression fragments; this task acquired the complete fifteen tracked files into a new private build tree without changing that snapshot. The upstream is MIT, copyright Andrey Torsunov; its complete notice is retained in `LICENSE.upstream-MIT` and the source tree. Local reader changes are supplied in `vdfs-reader.patch` under the same MIT terms, preserving the upstream notice.

Primary format reference: [vdfs-team/vdfs4](https://github.com/vdfs-team/vdfs4/tree/dfb2450427477c7b1eefb0a8580e92c24feba3b4), commit `dfb2450427477c7b1eefb0a8580e92c24feba3b4`. Its Samsung source notices state GPL version 2 or later. This was a read-only format reference; no driver was compiled, mounted or loaded. The `vdfs-team/vdfs-tools` repository was empty when checked, so it was not treated as a usable build source. The Rust reader avoids requiring the older bundled OpenSSL/LZO build from other Samsung-derived unpacker trees.

`acquisition-manifest.json` records all 15 reader and 34 reference file sizes/SHA-256 values, pinned commits and exact git-archive hashes. Private archives and source trees are retained under `private/`. `upstream-source-manifest.json` separately records the pristine Rust source. Rust/cargo versions and pristine/patched binary hashes are in `reader-pin.json`. `dependency-provenance.json` records all 64 Cargo.lock package versions, license expressions and registry archive SHA-256 values, independently checked against the downloaded crate archives. Dependency notices remain their own; they are not relicensed by this research project.

Build a fresh upstream checkout, detach at the pinned commit, apply `vdfs-reader.patch`, then run `cargo build --release --locked` and `cargo test --release --locked`. Nine Rust test functions pass, including 12 compression authentication-trailer/signature-size combinations, exact decompressed lengths, raw Linux CRC seed, malformed metadata, truncated input, decompression overflow and path-component rejection. The installed build used Rust/cargo 1.99.1. The locked patch adds no dependency or lockfile change.

## Why the patch was necessary

The upstream accepts VDFS2007, but its `hZip` branch assumes one compressed stream before the descriptor and ignores the chunk table. The primary driver defines `h` as SHA-256 metadata authentication, not a different single-stream data format. Its `inode.c` compressed-file preparation subtracts the extent table, `(extent_count + 1)` authentication hashes, optional 128/256-byte signature and descriptor from the compressed fork tail. `vdfs4_layout.h` defines the layout06 descriptor and 16-byte extent records. The patch uses these exact sizes, verifies the compressed-metadata Linux CRC with the descriptor CRC field zeroed, bounds each extent before metadata, inflates each chunk separately, and requires the exact descriptor-derived output length for every chunk and whole file. It does not claim to verify file RSA signatures or authentication hashes.

The superblock and extended-superblock checks also use Linux `crc32_le(seed=0)` without final xor, and run regardless of the whole-image CRC-present flag. Standard CRC32 defaults differ. Actual DB superpage checks independently established this convention; both actual volumes subsequently passed the reader's checks.

The upstream logs individual extraction/link failures yet returns success and prints Done. The patch counts them, emits a structured `VDFS_RESULT` and returns nonzero if any occur. Truncated file records and silently truncated inline data refuse. Catalog names must be valid UTF-8 single components with no empty/dot/parent/slash/NUL form. A block-span calculation was corrected to include an intra-block start offset. `--catalog-only` inventories metadata without extracting OEM file contents. LZO remains explicitly unsupported; an encountered LZO file produces a recorded failure, never a false successful extraction. Neither actual partition needed that path.

## Contained command/API

Use the wrapper, not the raw binary, for firmware data:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 run_reader.py \
  --input /private/path/to/pltf_t.img \
  --sha256 EXACT_ACCEPTED_PARTITION_SHA256 \
  --output /private/path/to/fresh-result \
  --catalog-only
```

Omit `--catalog-only` for file extraction. Input/output paths are host-local. Output must be fresh; no prior partial directory is reused. The wrapper checks the exact input SHA before/after, pins the patched reader, and runs it through unprivileged bubblewrap. Only the fresh `/work` output is a writable persistent bind; host `/usr` and libraries are read-only, input/reader are read-only, home/credentials are absent and networking is unshared. It enforces CPU/address-space/file-size/descriptor limits and a 900-second wall attempt. Reader policy additionally limits individual files to 512 MiB, chunks to 16 MiB and aggregate emitted regular bytes to 16 GiB. Those are refusal policies, not claims about all possible VDFS volumes.

The minimal namespace was tested: reader help worked, a host-root write probe failed and an invalid image was rejected with unchanged source. The wrapper accepts only exit zero, empty stderr, one structured zero-error result, matching mode and unchanged input identity/hash. Catalog TSV columns are record type, object ID, mode, fork byte count, compressed flag and UTF-8 path encoded as hex. A compressed fork count is its stored compressed span, not its decompressed file length. Raw/catalog logs and extracted files remain private.

## Actual qualification

The platform source was first accepted through the separate CX02 raw-stream receipt reconciliation, exact padding and authenticated original CRC check. DB then validated GPT and extracted the exact partitions before running this wrapper. This reader did not use the previously provisional streaming bytes as an accepted input.

| Partition | Input bytes | Catalog file records | Catalog link records | Host regular files | Host symlinks | Extracted regular bytes | Errors |
|---|---:|---:|---:|---:|---:|---:|---:|
| pltf_t.img | 1,391,460,352 | 58,457 | 26,073 | 57,038 | 3,369 | 2,316,227,025 | 0 |
| prd_t.img | 61,865,984 | 1,122 | 246 | 912 | 210 | 119,602,453 | 0 |

PLTF SHA-256 `0e6bbbca5a2659c830875a077cdb25f06b270ebc51bbec6282a30278aa7d949f`; PRD SHA-256 `e369344dbb9d4a814e297f5f92d9e75a10127ab24776148a2aff7fccfb324c39`. Full extraction took about 8.65 and 0.50 seconds respectively. Both catalog runs also completed without reported errors. An independent no-follow host tree walk agrees with the regular byte totals. The extracted PLTF `qdf_tcon.ko` is 403,294 bytes, SHA-256 `97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63`.

`actual-qualification.json` records exact source/tool/result hashes and independent host counts. The qualified patched binary SHA-256 is `3009d0ae8ee77b0a4bdd491675897cdace71ea9b1d7ea03cd08a4e25f7c85c7a`; the wrapper SHA-256 is `961e08dd2bae7b6d2cf840c993659472f1740975a28767bb1b02578c0fb82222`. No selection feature was added: the complete contained extraction was fast and made it unnecessary.

## Boundaries

This is a content reader, not a metadata-faithful filesystem backup or filesystem authenticator. Upstream hard-link records may be materialized as duplicate regular files or directory placeholders; owner/mode/device metadata is not fully reproduced. Catalog record counts therefore differ from unique host regular-file counts. The report labels them separately. Symlinks are preserved as links and must not be followed by later analysis outside this controlled context. The containment boundary prevents writes through absolute/escaping symlinks into the host.

Compressed metadata CRC and exact output lengths are checked. File RSA/per-chunk authentication, every filesystem schema invariant, full tree semantics and firmware applicability are explicitly not established. Exit zero alone is insufficient; retain the wrapper result, logs, source pins and independent integrity evidence. Extracted OEM content, whole images, binaries and private transport/configuration material remain outside public source exports. Original patch, wrapper, manifests and reproducible runbook may be published with their proper upstream notices.
