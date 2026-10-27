# Offline reset reference for the fixed window

No live target operation was performed. This reference is derived from the
already acquired current 5 MiB image and the selected packaged image, plus the
two retained static-analysis reports below.

Source report SHA256 values:

- `qd-rt-return-guard-initialization.md`:
  `e3d49087363c88f21517e2a2047e76b756e01b8dbe70ba184d8b6cdf102f8cad`
- `qd-emergency-loop-output-sequence.md`:
  `02fe780962a6c4894351aea6b547aa03628c92d64b95a56f69f1d3b717230a6d`

For the current acquired image, scatter row 11 is
`(source 0x3e4c4, destination 0x20000f3c, length 0x15248, handler 0x1d8)`.
For the packaged image, row 11 is
`(source 0x3e764, destination 0x20000f4c, length 0x16438, handler 0x1d8)`.
The retained analysis identifies handler `0x1d8` as zero-fill. Both rows fully
cover CPU `0x2000f0c0..0x2000f0ff`, so their reset prediction for this fixed
64-byte window is all zeroes, SHA256
`f5a5fd42d16a20302798ef6ed309979b43003d2320d9f0e8ea9831a92759fb4b`.

Thus the predicted reset values at snapshot offsets 32 (common guard) and 48
(selector) are both zero. This is only a reset prediction. Runtime,
configuration, computed, external, or DMA writers may change either value,
and the prediction does not establish the live core-tag mapping.
