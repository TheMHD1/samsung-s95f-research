# Independent review: packaged USB descriptor scatter match

Reviewed 2026-10-27 UTC. This review was offline only: it read the retained
5-MiB selected profile, the retained cached USB metadata, and the two
candidate source files. It made no USB, TV, root, network, or firmware call.

## Verdict: clear for the bounded claim

The report's bounded statement is supported: the unpacked row-6 reset data
contains the 18-byte device descriptor

```text
12 01 00 02 ef 02 01 40 e8 04 01 20 50 02 01 02 03 01
```

and it equals the first 18 bytes of the retained 116-byte cached descriptor
blob. The report correctly keeps current-executable equality false and does
not elevate descriptor identity into a controller-storage or RT-path claim.

## Independently checked facts

* The report and checker pin selected profile SHA-256
  `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`
  and cached metadata SHA-256
  `065113d8f9d133570a72a4c086e2fdbff26567c9f8c082612f794f7414430530`.
* Row 6 at file `0x3e3a0` is exactly
  `{source=0x3e89c, destination=0x20261000, output=0x4d4, decoder=0x17c}`.
  The pinned decoder consumes through exclusive file `0x3eac6` and its
  complete `0x4d4`-byte output hashes to
  `b7017446eabb7487bd28e612aa20df018b7b5442528664ca5990d3db80397fe0`.
  Descriptor bytes are output offsets `0x200..0x211`, hence RAM
  `0x20261200..0x20261211`.
* Row 0 at file `0x3e340` is exactly
  `{source=0x3e32c, destination=0x20000000, output=0xf4c, decoder=0x17c}`.
  The checker validates all `0xf4c` output bytes through SHA-256
  `685d8eda90bb3ce7e6210ad0dfe962f65ac3b8e1b2eb1a40962e0e5720d81eb3`;
  its word at output `+0x500` is Thumb pointer `0x2a1ed`.
* Under canonical image-0 `FILE = VA + 0x200`, independent Thumb decoding
  of file `0x2a3ec` / VA `0x2a1ec` shows `mov r2,r0; movs r0,#0x12; strh
  r0,[r1]; ldr r0,[pc,#4]; bx lr`. The literal at file `0x2a3f8` is
  `0x20261200`. This is consistent with an 18-byte descriptor callback.
* File `0xf978` / VA `0xf778` is `ldr r0,[pc,#0]; bx lr`, returning table
  address `0x20000500`. The row-0 pointer lands at that table's `+0x500`
  entry.
* File `0x24b0c` / VA `0x2490c` decodes such that `BL 0xf778` occurs at
  VA `0x24948`; its result is moved to `r5`, then to `r2`, immediately before
  `BL 0x28b36` at VA `0x2495a`. The reviewed report describes this precise
  table-to-initialization dataflow, without overclaiming a full USB request
  dispatcher.
* The supplied checker passed both normal and `python3 -O` execution. It
  validates the complete decoded row lengths/hashes, descriptor equality,
  pointer/literal, accessor, and initializer slice hashes; this is stronger
  than a plain-byte match alone.

## Limits retained

The scatter reconstruction proves a package-to-retained-device-descriptor
identity match, not that the package is the currently executing image,
that the configuration descriptor was fully reconstructed, or that any
USB endpoint read would be passive or access controller storage. Those
limits should remain explicit in subsequent work.

## Reviewed source identities

* `qd-usb-device-descriptor-scatter-match-20261027.md`:
  `ec6d1c4edf55b4d7738422ecfbf2f141ac2ae6f35dcb3a00e2c861dec527ff64`
* `qd-usb-device-descriptor-scatter-match-20261027.py`:
  `b940ad500d661e16b52cec39aed0327fc5bd7a3190075693a171169d1e3c1069`
