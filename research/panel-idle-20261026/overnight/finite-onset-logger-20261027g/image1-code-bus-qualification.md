# Image-1 executable bus-address qualification

Recorded 2026-10-27 UTC. This is a bounded offline analysis of retained local
firmware bytes. It performed no TV, root-agent, network, USB, device-node,
process-control, memory-read, firmware-write, reset, or UI operation.

## Result

**No hardware-visible executable address is qualified for image 1.** The
retained evidence positively identifies its stored bytes, linked addresses,
reset vector, and RAM scatter destinations. It does not contain a positive
ordinary-loader edge from image-1 linked code VA `0..0x3ffff` to a controller
bus address.

Consequently, this report does **not** propose a target/address pair for a
future predicate-code read. In particular, it rejects deriving one from the
`0x4700....` data alias, from image-0 placement, or from numeric symmetry.
That is a qualification gap, not evidence that image 1 is inactive or that no
mapping exists in boot ROM or hardware.

## What is positively bound

The pinned selected package is 5 MiB, SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
The recovered current storage is 5 MiB, SHA-256
`f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562`.
Their complete file range `0x40000..0x7ffff` is byte-identical, with SHA-256
`56bfea112d161a22f5bee8630c81306bf04fa9d8d3d901c6d8e7cdd89c09dfbf`.
This proves storage identity for that slot, not where its code executes.

The image-1 vector is at file `0x40200`. Its initial SP is `0x20020000` and
its Thumb reset word is `0x369`, so the reset linked VA is `0x368` and its
stored instruction coordinate is `0x40200 + 0x368 = 0x40568`. The coherent
reset trampoline calls ordinary startup and reaches the scatter dispatcher at
linked VA `0x140`. These facts establish the component-local translation:

```text
stored file coordinate = 0x40200 + image-1 linked VA
```

They do not establish an external/DMA/USB-visible code address.

The nine exact image-1 scatter records are:

| source linked VA | destination | output bytes | handler |
| ---: | ---: | ---: | ---: |
| `0x1d860` | `0x20000000` | `0x4f8` | `0x17c` |
| `0x1d95c` | `0x20015000` | `0xb50` | `0x17c` |
| `0x1d974` | `0x20015f10` | `0xb50` | `0x17c` |
| `0x1d98c` | `0x2020a000` | `0x2d30` | `0x17c` |
| `0x1d9e8` | `0x20253000` | `0x223c` | `0x17c` |
| `0x1da30` | `0x20209000` | `0x6c0` | `0x17c` |
| `0x1da40` | `0x20209800` | `0x6c0` | `0x17c` |
| `0x1da50` | `0x20269000` | `0x4890` | `0x17c` |
| `0x1d95c` | `0x200004f8` | `0xdca4` | `0x1d8` zero-fill |

Thus the image's own ordinary startup copies/decompresses or zero-fills data
RAM. It has no row whose destination is linked code VA `0..0x3ffff`, and it
does not supply the missing executable-bus mapping.

## Why the known RAM alias does not qualify code

The exact image-1 mapper body at linked VA `0x3084..0x30a7` was previously
decoded and its bytes are pinned here. Its input domain is CPU RAM
`[0x20000000,0x20200000)`: it adds `0x25000000` for core tag `0xA` and
`0x27000000` otherwise. Successful retained reads have made that mapping useful
for qualified RAM objects.

Image-1 linked executable VA `0..0x3ffff` is outside that mapper's input
domain. Applying `+0x27000000`, substituting `0x47000000`, or copying the
`0x4700....` prefix from a data address would be an unsupported extension.

There is one positive image-0 reset-scatter row with destination
`0x47010000`, but its source linked VA `0x3ea34` maps to image-0 file
`0x3ec34`, below the image-1 slot boundary. It therefore proves an image-0
data/window initialization, not a copy or launch of image-1 code.

## Bounded loader/configuration inspection

The ordinary retained mechanisms give no positive code-placement edge:

1. Image 1's reset/scatter path has only the nine RAM/data destinations above.
2. Image 0's `0x47010000` reset-copy source is inside image 0, not the image-1
   stored range.
3. Image-0 strings such as `Config_CopyData_To_MCU_v5`,
   `Config_CopyData_To_MCU`, and the `To_IP`/`DDR` variants occur at their
   already recorded single locations. Their selected callers do not establish
   a source range containing image-1 code plus a code destination/entrypoint.
   A diagnostic name is not a launch-vector proof.
4. Neither bounded executable range contains the raw little-endian Cortex-M
   VTOR address literal `0xe000ed08`. This is only a negative observation: it
   does not exclude a computed register address, remap peripheral, boot-ROM
   action, indirect loader, or hardware-local mapping.
5. The retained host whole-file transport does not decode the two executable
   components or expose a component-specific destination/launch address.

This is a finite check of the ordinary reset/scatter and already identified
configuration-copy mechanisms. It is not a whole-SoC absence claim and does
not inspect alternative banks, flashing behavior, persistence, protection
bypasses, return guards, or high-bank state.

## Consequence for a future code-identity read

The known predicate body at image-1 linked VA `0x1e68..0x203f` is stored at
file `0x42068..0x4223f`, is identical in selected and recovered-current
storage, and has SHA-256
`c3afd8863cf7f6d098fe7459ef91da9fd8827662041e77cd29497dccb2aae57a`.
Those are suitable comparison bytes **after** a bus mapping is independently
qualified. They do not qualify the address to read.

A future read becomes source-grounded only after one of these positive edges
is recovered:

- a loader/copy record whose source covers the image-1 stored or linked code
  bytes and whose destination is an explicit hardware-visible code range;
- a boot vector, reset-release, VTOR, remap, or code-window register with
  decoded address semantics that binds image-1 linked VA to a bus base; or
- another independently documented SoC/core address translation that
  explicitly covers linked executable VA `0..0x3ffff`, rather than only the
  `0x200...` RAM domain.

Until then, a read at raw file offset `0x42068`, raw linked VA `0x1e68`, a
guessed `0x27...`/`0x47...` address, or an image-0-corresponding address would
be exploratory rather than qualified. No such read or helper was performed or
built here.

## Reproducibility and pinned slices

Run the standard-library-only verifier normally and with assertions disabled:

```sh
python3 image1-code-bus-qualification.py
python3 -O image1-code-bus-qualification.py
```

It uses explicit exceptions rather than Python `assert`, verifies both whole
files, their exact image-1 slot equality, vectors, loader rows, mapper bytes,
image-0 comparison row, bounded VTOR-literal absence, and predicate bytes. It
prints one compact JSON result with `status=qualification_gap`,
`qualified_code_bus_address=null`, and `target_operations=0`.

| Artifact/slice | SHA-256 |
| --- | --- |
| image-1 slot, file `0x40000..0x80000` | `56bfea112d161a22f5bee8630c81306bf04fa9d8d3d901c6d8e7cdd89c09dfbf` |
| image-1 vector, file `0x40200..0x40208` | `bef0c9b5c39935347fe872bf9501a20bdbe3c11781d26f7bc521e0e106191b6d` |
| image-1 reset, file `0x40568..0x4058c` | `77428a5791705e4b966092c95715a84b617dfd7f414902ff35ae2089d92c93d6` |
| image-1 scatter dispatcher, file `0x40340..0x403f4` | `cf4020e3cdb1b314345608c30d00c1efa1e0ad4cf87bf8e54aa92f568fcb6330` |
| image-1 scatter table, file `0x5d8a4..0x5d934` | `73eaacb3784da627c734f46dceeca569c403209c3e3e969d813f2bf13d09caef` |
| image-1 RAM mapper, file `0x43284..0x432a8` | `64ef2153ee7053a16b6741c455535147ddb1d247aaf216482b5e46fba7c0f471` |
| image-0 scatter table, file `0x3e340..0x3e400` | `3f09781583f48d9b429fe8438b06bbd26196b3f673c79e6a2cf7adde356b612d` |
| known predicate, file `0x42068..0x42240` | `c3afd8863cf7f6d098fe7459ef91da9fd8827662041e77cd29497dccb2aae57a` |

Prior reports remain unchanged. The directly relevant retained context is
`tcon-research/qd-firmware-load-address-erratum.md`,
`tcon-research/qd-image1-context-initialization.md`,
`tcon-research/qd-secondary-core-window-loader.md`, and
`tcon-research/qd-rt-window-alias-evidence-20261027.md`.
