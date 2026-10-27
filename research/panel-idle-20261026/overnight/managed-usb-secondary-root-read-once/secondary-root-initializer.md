# Image-1 secondary-root initializer prediction

This is an offline prediction for the fixed 64-byte read at DMA candidate
`0x470004c0`. No TV or USB operation was performed.

The checker pins the current acquired 5 MiB image and the selected packaged
image, pins the D5 callback-initializer verifier and its known-answer scatter
decoder, independently locates image 1's scatter table through its vector and
reset data, and decodes its first row. Current and packaged image 1 produce
the same bytes.

The requested CPU-side range is `0x200004c0..0x200004ff`. Its first 56 bytes
come from decoded row 0, ending at `0x200004f8`; the final eight bytes come
from the following zero-fill row. The combined expected SHA-256 is
`a43ca5561d3e7d98c1b8475c68857c35263532edd9b93f822582b466824d8df4`.

The predicted halfword gates at CPU offsets `0x4c6`, `0x4c8`, and `0x4ca`
are all zero. The pointer slot at CPU `0x200004e0` contains `0x20010000`.
These are reset-time initialized values. Matching them later would support
the secondary RAM namespace hypothesis, but byte shape alone cannot prove
which live core-tag mapping branch supplied the read.

Artifacts:

- `extract-expected-secondary-root.py` SHA-256
  `226665bc0db27fe0652353eda02068b06fa5155960348dfaf7207406f6ca001b`;
- `expected-secondary-root.bin` SHA-256
  `a43ca5561d3e7d98c1b8475c68857c35263532edd9b93f822582b466824d8df4`;
- `secondary-root-initializer.json` SHA-256
  `fe47d5e96a18f02ebccf31c7d37ae5e84312a185af9463e8ed66c5e3ead4c1c8`.
