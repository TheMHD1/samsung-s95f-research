# ED table-read-01: independent offline replay

The completed read observed **all 68 primary halfwords equal to zero and all 68 secondary bytes equal to zero** for logical lanes 568–635. The captured SB override is false. Every sampled lane therefore passes the two local table conditions in the selected unpacker source. This establishes captured table values and local eligibility only; it does not establish that the comparator was called for every lane, that these gates held during an earlier fault, or that these logical lanes map to physical pixels.

`analyze.py` strictly replays the saved EB native receipt, both three-blob envelopes, all 16 raw files, the wrapper result, the readiness decision and all 11 evidence references. It regenerates the frozen manifest and reproduces the parent source and predecessor checks. A mock transport then reproduces all 28 generated root commands and every saved output artifact byte for byte. The mock imports no real root adapter and performs no TV or network operation. All 113 input files are byte-pinned in `input-pins.json`; originals remain unchanged.

## Actual boundary and context

The accepted operation made one native invocation, 16 header/data pairs and 32 bulk transfers, with zero writes, UI actions, resets or retries. It ended `ReadyForHeader`, released its own claim, closed the device, and removed its exact stage (`STAGE_ABSENT`). The saved identity is the same boot and USB instance 60 as the accepted DY predecessor. EB manifest SHA-256 is `e7df47861e25aca4df6fc18e82b646a53eada192451b9b16383c5b31a9f44a11`; captured readiness SHA-256 is `57c5888f37e7b8837c8d66b9666ede5627a0096ce1cda2a8afafeee46e1e71c3`.

| Captured field | Value and limit |
| --- | --- |
| Root / x base | CPU `0x20010000` / 0 |
| Geometry | 2160 rows, 1920 lanes, 2880 packed bytes |
| AA / AC / byte 4cc | 0 / 2 / 0; SB = false |
| R operating mode | 4; distinct from the AA/AC record-category selection |
| C7 / M publication-bound mirror | 0 / 200 |
| R start and end | Byte-identical; stop/fault/gate = 0/0/1; alternate limit 40; mode-1 record latch 69 |
| N start and end | Byte-identical, all 36 bytes zero: six ordinals and six source counts |
| M metadata | Current row 81, saved row 1970, scan byte 1; sequential metadata, not proof of a record epoch |

The primary interval is `47010470/136` and retains the full 16-bit value for each lane, including high bits. The secondary interval is `4700cb94/68`. The source formula is `(primaryHalfword & 1) == 0 && (secondaryByte == 0 || SB)`, where `SB = (AA == 1 || AC == 1) && byte4cc != 0`. Earlier comparator return-zero paths can terminate the unpacker loop before a later locally eligible lane is reached. The live code probe fingerprinted a small unpacker entry fragment; it did not fingerprint the complete gate body.

## Record and reference interpretation

All 48 X, Y and RGB entries are zero. B and Diff retain nonzero candidate bytes, and both entire 96-byte arrays are **exactly identical** to `DK/dv-final-clean-01`. Current X and Y differ from that prior capture. This is consistent with retained/remnant columns and separately cleared coordinates. It establishes neither a current valid record prefix nor an actual selected-A reconstruction. Current N counts are zero; the separate historical R latch 69 must not be substituted for a current ordinal. No score H window was read here.

The two 104-byte fixed candidates independently decode to 68 packed 12-bit lanes each using their first 102 bytes. Selected values are:

| Logical lanes | Top candidate | Bottom candidate |
| --- | ---: | ---: |
| 570 / 571 | 2168 | 460 |
| 622 / 623 | 2155 | 1363 |
| 624 / 625 | 2170 | 377 |
| 632 / 633 | 2164 | 980 |

`decoded.json` retains all 68 decoded values on each side. The two candidates are source-qualified fixed reference regions; their later values do not prove which A source was selected for a historical comparator call, nor a matching epoch, physical row or physical light state. The samples do not identify table writers, initialization/reset causes, a safe modification, a root cause or a fix.

## Timing, framing and provenance

The first OUT-before timestamp is 182726197550 us and final IN-after is 182726204160 us, a **6610 us sequential read span**. Start-R spans [182726197550, 182726201851], the primary table [182726203624, 182726203692], secondary [182726203707, 182726203782], and end-R [182726204081, 182726204160]. All full read-pair brackets are retained. OUT handling may stage a later IN reply, so the full pair is the conservative software bracket. The observations are conditional on source freshness and are not atomic table/comparator snapshots or optical timestamps.

The private semantic receipts are decoded independently of diagnostic stdout. The selftest reports 2071 checks and zero target operations; its separate opaque stdout is 981 bytes, while production stdout is 109 bytes. Both stderr blobs are empty. Envelope lengths/hashes, canonical raw encodings, three native binding proofs, paired phases/times, exact result and manifest, and the zero-write action surface are checked. The largest recorded root command is 7712 bytes, below the 8192-byte limit.

The cached readiness census saw zero matching holders, zero other errors and two classified numeric-path ENOENT disappearances. The three wrapper censuses also saw zero holders/errors. These are bounded snapshots, not continuous exclusion or endpoint-queue proof. The coordinator's byte-pinned closed-world vendor-OUT lineage premise remains an explicit premise; the replay does not convert it into hardware queue evidence. The accepted predecessor read sampled only 64 code bytes and did not measure RT state.

The verifier rejects 102 cloned malformed cases covering wrong windows, short/ambiguous pairs, failed flags, invalid geometry/mode, corrupted envelopes and transport records. Two additional cloned nonzero-table cases are accepted and decoded as locally excluded, showing that the decoder does not force expected-zero values. No original input is modified.

Run `PYTHONDONTWRITEBYTECODE=1 python3 analyze.py --check` and the same command with `python3 -O`. `validation.json` records both results; `source-inventory.json` pins this analysis checkpoint. The acceptance claim concerns this bounded software capture. Physical picture state and historical gate execution remain unobserved.
