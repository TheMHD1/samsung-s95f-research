# Independent audit: private HDMI library acquisition

Date: 2026-10-26 UTC

## Outcome

**CLEAR for offline static analysis of the retained bytes.** I independently
replayed the retained metadata and all 13 chunk responses without contacting
the TV. The decoded chunks concatenate to exactly 415,124 bytes with SHA-256
`067ddb8f639f8e91d02524f0820fb3a56e2d9f174d0f3f75a5dec963f7339410`,
and those bytes are byte-for-byte identical to the retained
`serdes-hdmi-control-copy-20261026/libhdmi-control.so.0.1`.

This establishes the identity of the copied file and a point-in-time
observation that the same file was mapped by PID 706 (`avocd`). It does **not**
establish a stable runtime pointer, a callback-table binding, an invocation,
or any relationship to the physical panel fault.

No TV, root, or network request was made during this independent audit.

## Hash-pinned acquisition code

- `read-private-hdmi-library-metadata.py`: SHA-256
  `c53f8ceda4691b3f7a4885d2027ce0739e206c9cce23bb0ac29c7efd96949348`
- Its pinned implementation, `read-pm-idle-format.py`: SHA-256
  `47262917994451714b3dbfb8f53d761c61232587f2e83b3303cd5ce94a1b28e9`
- `pull-private-hdmi-library.py`: SHA-256
  `ed3dd8ed78ae100956723459ee8932f3acd6211a5e8c5d3299ecb13762cd57bc`
- Its pinned dispatcher, `pull-serdes-modules.py`: SHA-256
  `62fa8107cb3a50b20949d59370fa5a4ed33d48c71153f11643e5b370f680ea11`
- The dispatcher's pinned parser, `complete-sdp-sys-provider-copy.py`:
  SHA-256
  `b587e16d4e85a056c248b1adc3f04dccbabed682fe50a8dfdd9987a1543c4582`
- The root client named by the metadata intent, `s95f-access.py`: SHA-256
  `3a92e02003ce51d2faeace231191f6f0c73731f2bfca9caa196e05b195b439a5`

Both top-level acquisition programs remain default-dry. Running the copy
wrapper without `--run` printed only the fixed path, byte count, and 13-chunk
plan.

## Metadata evidence

The four retained metadata artifacts hash as follows:

| Artifact | SHA-256 |
| --- | --- |
| `intent.json` | `b1f81137efce46d54f508cc6f507b98d25a1e81f506def2f2a450488ccaa0cb6` |
| `client-result.json` | `139c3765f658be53dba8dcb726b1b031ad6f5cd46ff834c2161231ff0e4ff500` |
| `client-stdout.json` | `6ce68b3a661c54b6935722fda4346034baee57d459d68f9ca4f0b6c2e0574b5a` |
| `client-stderr.txt` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

For a reproducible inventory check, hashing the UTF-8 lines
`<sha256><two spaces><basename>\n` for those four files in basename order
produces SHA-256
`90740fb3f79c16564dce49faa74c7a635be63eb84e231c3386b3fd6f7abe4499`.

I verified all of the following directly from the raw response:

- The local client returned 0, did not time out, and emitted no stderr.
- The response identifies model `QN77S95FAFXZC`, host `198.51.100.20`,
  authenticated UID/EUID 0, `host-assisted` root persistence, and
  `global_system_files_unchanged_at_acquisition=true`.
- Exactly one remote command was retained. Its bytes equal the intent command,
  whose SHA-256 is
  `1e8dd0320f0a61f2d45c88e9a55dc66e60b8e092484f664f2ddfaf8606836384`.
  The remote exit was 0, `timed_out=false`, and remote stderr was empty.
- Boot ID is
  `00000000-0000-4000-8000-000000000000` at both ends. Epoch time is
  `1793048181` at both ends and uptime advances from `69790.66` to
  `69790.68` seconds.
- `/proc/706/exe` resolves to `/usr/bin/avocd`. The retained stat row parses as
  PID 706, comm `avocd`, state `S`, and start ticks 603.
- Four mappings name the exact library path and the same device/inode
  `b3:1a`/`62055`:
  `47e10000-47e70000 r-xp 00000000`,
  `47e70000-47e80000 ---p 00060000`,
  `47e80000-47e82000 r--p 00060000`, and
  `47e82000-47e84000 rw-p 00062000`.
- The target-side path was a non-symlink regular file, mode 0755, UID 0,
  415,124 bytes, with the expected SHA-256.

The command consists only of reads and predicates: boot/time/uptime reads,
`readlink`, `/proc` reads, `awk` over maps, `test`, `stat`, and `sha256sum`.
It does not load or call the library and does not issue a display or hardware
control.

The process identity and maps were sampled only once between boot/time
brackets. There is no second `/proc/706/exe`, stat-start-tick, or maps sample.
Consequently the evidence supports a point observation of the mapping, not a
claim that PID identity or mappings were unchanged across the metadata read.
This limitation does not weaken the separately hash-authenticated on-disk file
copy.

## Thirteen-chunk reconstruction

The copy allowlist fixes exactly one source:
`/usr/lib/libhdmi-control.so.0.1`, 415,124 bytes, at the expected whole-file
hash above. Each of the 13 commands:

1. authenticates the same boot;
2. hashes that exact file before the read;
3. reads only one fixed 32,768-byte chunk with `dd if=...` and no output file;
4. base64-encodes the bytes to stdout;
5. hashes the same file again; and
6. records time/uptime and the ending boot ID.

The commands use `set -euo pipefail`, so a failed `dd` in the pipeline cannot
be masked by a successful `base64`. There are no target-side writes, loads,
library calls, getters, tracing changes, display controls, or retries.

For every chunk I independently required:

- client return 0 and empty client stderr;
- the same authenticated root/model/host/access-provenance fields as above;
- exactly one command, byte-identical to its intent and to the expected fixed
  command for that index;
- correct intent-command SHA-256;
- remote exit 0, no timeout, and empty remote stderr;
- exact complete framing with the same boot ID;
- the expected whole-file hash and path both before and after the data;
- ordered wall and uptime values spanning no more than 25 seconds;
- strict base64 decoding and the exact expected decoded length; and
- agreement of decoded chunk hash, raw client-response hash, command hash,
  uptime endpoints, and index with `manifest.json`.

Chunks 0 through 11 each contain 32,768 bytes. Chunk 12 contains 21,908
bytes. Their retained decoded hashes are:

| Index | Bytes | SHA-256 |
| ---: | ---: | --- |
| 0 | 32768 | `c2274ce1858a1f3fa73582009b9a400aaf49b6974281f7044f7d4ca1a258863c` |
| 1 | 32768 | `a721e0266dcbf07f802e4bdba036d31176e48e3cab0285be60380e2863f1b5c6` |
| 2 | 32768 | `7f426fcaf242a8ea461a7ddb0f5ccc4432ab96383cb0684eda1bd9ca83da939b` |
| 3 | 32768 | `4bab5cfd0999d0c8c1159c1db407f1c348bf4295c3ff56c3a6873344d11bb8b3` |
| 4 | 32768 | `c6dcaf58832392510abe7c26c6e70638235fd97291ceb3931e7237df7de01878` |
| 5 | 32768 | `17b664fe3506f866c6380c87fd1dfd9b63015eda2459ca64ce7bdd3f6bb215d9` |
| 6 | 32768 | `4f8d7535ecbb54aa2aa136803b55e1037ab7f15b395ad9b502636a6058640c40` |
| 7 | 32768 | `ffb9494f39bc7f23670119b053aef639a94cc81e6ee7a474de3ef948b31139d9` |
| 8 | 32768 | `a891e6168d2edf9fbbddc5e7e262168c15593a267c4457d32cf259b477fe8427` |
| 9 | 32768 | `02b9967cd75f17b64a342177c2493bad42f35e3d7a532ea51370bc135123c2d2` |
| 10 | 32768 | `657e4e9b8a8421bf9c18586027075f18d7c397b6704e3c3879d524a7f5bf36c2` |
| 11 | 32768 | `63f197cca2e83308dad05659b0b907a328414fa213385ac8a816c908019fb2ea` |
| 12 | 21908 | `56934b4ca8d30c97c1019f9f856db50778650601442818f2ab1bff620e5783d5` |

The first chunk spans uptime `69799.98` to `69800.00`; the last spans
`69802.34` to `69802.35`. Every chunk uses the same boot ID and identical
pre/post remote file hash. As the manifest correctly states, this was a
sequential, non-atomic copy; the authentication is per chunk. The repeated
whole-file hash and exact final reconstructed whole-file hash make the
retained byte identity suitable for offline analysis without implying an
atomic runtime-memory snapshot.

The 52 raw per-chunk files (intent, client result, client stderr, and client
stdout for each of 13 indices) are all regular non-symlink files. A
reproducible inventory computed as
`<sha256><two spaces><basename>\n`, sorted by basename, has SHA-256
`1b4342f73e9ac4a303bee7bd8644c503b22c034daf9655e25e50c8aa793af974`.

The copy manifest is 7,965 bytes with SHA-256
`116cbacb816db3c4fd8988e324d16635168f01a6d540190b9029318c2b9088b3`.
It accurately records `sequential_nonatomic=true`,
`loaded_or_called_by_capture=false`, and `physical_picture="unobserved"`.
The retained local ELF is 415,124 bytes with the expected SHA-256 and parses
as an ELF32 little-endian ARM EABI5 shared object (build ID
`6f7439f28010fe6ac1abc0ec99919e147cc8b098`).

## Claim boundary

The acquisition proves the exact on-disk bytes available for offline reverse
engineering and one contemporaneous AVOC mapping of that same path. It does
not prove which runtime object or callbacks AVOC used, whether any exported
or internal function ran, what values any runtime state held, or that this
library caused, prevented, or recovered the black-panel condition.
