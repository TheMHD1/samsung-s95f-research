# QD fault next-discriminator corpus audit

Recorded 2026-10-27 UTC. This is a bounded offline audit of already retained
files and owner photographs. It made no TV, root, network, controller, GPIO,
SSB, firmware or display call. It did not modify any prior evidence.

## P0 finding: retained logs already select one matching factory-data asset

The most useful discriminator available before another owner-visible state is
not a new verifier. It is a correlation that the existing reports missed.
The raw TCON monitor text repeatedly contains this exact tuple:

```text
[TCON INFO] PANEL[77A3OUSOF]
[QDF]FW[FA024C300/F:FA024C300]
MD[F77ABUAE20312300/F:F77ABUAE20312300]
```

The authenticated 45-slice catalog
`overnight/factory-qd-data-fields-20261026a/fields.json` (22,859 bytes,
SHA256 `b1f0df94dfc81d7774293314e03e668b3056709169985fc31defa0c4ea8dc327`)
was decoded independently across all nine 5 MiB files. Exactly one row has all
three runtime strings:

| Source asset | Source offset | Exact leading ASCII | Slice SHA256 |
| --- | ---: | --- | --- |
| `F_RSM1_BN9659934B_COMMON.bin` | `0x4ffe00` | `FA024C300` | `615b7ff5155850fdf79e57113d6e4a446befeff865a226ed676130c102938207` |
| same | `0x80100` | `F77ABUAE2` | `5a018e3d479bba24c5777719583587c13d0a8fe6c6631027d38a36fe95cd0fda` |
| same | `0x8000a` | `12300` | `aa0ab07bbde39d4fe5463bc2710a347ac4a604bc66beafa6f421df64118a6daa` |

The 16-character runtime MD value `F77ABUAE20312300` has exact first-nine
`F77ABUAE2` and exact final-five `12300`; its intervening `03` is not claimed
to come from either sampled file field. The tail field is exactly the runtime
QDF FW value `FA024C300`. The source asset's retained full-file SHA256 is
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
The authenticated source response is
`overnight/factory-qd-data-fields-20261026a/client.stdout`, SHA256
`ad0090732901edfadd0c202e855a7bacd660af5acd1e94967710b360a849cdd0`.

The other eight catalog rows fail at least one of those three exact
first-nine/final-five/FW comparisons. This is
therefore a unique **runtime-tuple-to-packaged-asset match within the retained
nine-file set**. It is stronger than choosing by `77`, the retail model, or a
shared `F77` prefix.

It is not proof that this pathname was opened this boot, that this asset was
flashed, that all current controller bytes equal the file, or that the asset
caused RT Protect. The meaning of the displayed `/F:` side was not recovered
from this audit; the defensible observation is only that both displayed sides
are identical and that their bytes uniquely match this packaged asset.

## Raw-log census and state limit

A bytewise census excluded Markdown, source code and disassembly and searched
the retained corpus for the complete `PANEL[...] [QDF]FW[...]MD[...]` shape.
It found 48 occurrences in 28 raw files and exactly one distinct tuple: the one
above. Representative byte-exact evidence includes:

| Evidence | SHA256 | Relevant retained occurrence |
| --- | --- | --- |
| `on-then-black-20261026.json` | `abf60c6e220a19f9ed08cfa051b3c8fb5c55336e12e421260749bdc2f90893a9` | uptime `3904.813804` |
| `factory-ss-trial/physically-black-after-trial.json` | `e66a95d8c971079735a118d5c481214f91120de7ea05416d46b31682b9b502fe` | `5405.640112`, `5705.806809` |
| `paired-capture/apps-visible-control.json` | `1bde448993899ef749fd666159343e81c8c740d7102ff6d69e7479e86bd02c40` | `6907.132280`, `7207.291749` |
| `paired-capture/black-after-live-b0.json` | `30a9f287515e559db474c25b4c2c4ea75a4a5c72b9f4ab4d880ab5775d44590b` | retained `7207.291749` line |
| `paired-capture/black-volume-b1.json` | `a3a7d9cbf3a6f8d9c51e83b1ba949fd3f19f6da9a254b35fbe488531a84aff9a` | same tuple retained |
| `overnight/current-kernel-vlog.json` | `14ab0b47e156415bfeba4af5627b0d2a8dae323aae02fc9b339b05526c6851d8` | `9009.053630` |

The remaining files are four recovery captures and all 18 transition-trace
captures. The owner-confirmed visible Apps summary is
`paired-capture/apps-visible-control-summary.json` (SHA256
`6b9195dd382f24fd9ceea7972287c681e32c458208696d5cb60354c2442c3fdc`);
the owner-confirmed physical-black summary is
`paired-capture/black-after-live-b0-summary.json` (SHA256
`6c2263a50151ee02fa621533656010101dd857c8d4c3711bf6dab603d3f27392`).
The TCON lines are periodic retained-log events, not synchronous picture-state
samples. Their presence in both evidence sets identifies a stable reported
tuple but does not itself distinguish visible from black.

## Why the known fault observations do not provide a second discriminator

1. The accepted one-shot status result
   `overnight/managed-tcon-status-read/result-20261026c.json` (SHA256
   `5ccac8a789fd83b3b276b39e6bf33201087c8e4354d580f7bb316075ed04bea6`)
   returned `0x10`. The retained dmesg result (SHA256
   `d454a04995c5298f31693260f1243e7dcb4f5cf8335312e798b3e99e27b7e9f9`)
   names it `ERR DET Status:0x10`; the exact host decode labels bit 4
   **RT Protect**. It was physically unobserved and does not establish whether
   the value was live, latched, or read-to-clear.

2. The accepted independent cdev sample
   `overnight/managed-errpin-cdev/input-result-20261026a.json` (SHA256
   `59116acf54ebd8e492f6f94d792a1b40e33e78cc6acdbb72b4161d656f46ae5f`)
   read GPIO125 as `1`. It occurred roughly 3,032 seconds after the status
   read, with machine physical state `unobserved`; it is not a simultaneous
   pair with `0x10`.

3. The exact recovery CFG in
   `qd-monitor-exact-recovery-predicates.md` (SHA256
   `2cab8b090de232224a4d9b5ceb6c2ecf576d5a5a17bcbc8aa046ced116c87a1d`)
   separates a no-current-ERR/`err_det_reboot_try==1` operation-two path, a
   current-ERR/nonproduction/below-terminal-threshold operation-two path, and
   terminal operation-zero+latch paths. The accepted visible Apps capture
   already contained repeated `[QD_TCON_OFF] = 1`, so the historical latch is
   not sufficient to classify the picture state and suppresses fresh monitor
   work at the next entry.

4. Direct inspection of the ten owner images agrees with
   `owner-photo-board-map.md`: panel `CY-AF077FLLV2H`, separate main/T-con/DCDC
   topology, and a thumb-sized lower-edge black patch with a narrow vertical
   line are visible. No obvious photographed burn or disconnected ribbon and
   no image establishes a rail, link, controller, or bonded-driver failure.
   The photos support real local panel damage but cannot attribute the
   intermittent whole-panel emission loss.

## F77 executable and other ordinary-file searches

The separate controller text remains:

```text
[Int.Tcon]FW[F20D]DATA[F77ABU2D20]
```

`overnight/micom-log-read-20261026b/micom-log.bin` (1,477 bytes, SHA256
`bd600476b7a081b58759128cff8bacd8f4fef8d8c45c33327cc575a1c65d7110`)
also says `SPI Flash : 2048KB` and `TCON Image Info : F77ABU2D20`. This is a
startup identifier, not the 5 MiB CAD filename or payload.

The finite ordinary-file review found no matching 2 MiB executable:

* `/factory_peq/tcon_data/QD` contained the nine exact 5 MiB
  `F_RSM1_BN..._COMMON.bin` assets and no `TconFw*.bin` entry.
* all 20 exact removable `TCON/` resolver roots were absent/not directories in
  the retained metadata acquisition;
* `/prd/lib/firmware/tcon` contained only the documented zero-byte dummy
  payloads;
* `binaries/factory-data/Factory_Part1.dat` (SHA256
  `687b6b019cb1b1fd5f3ae826949cfbe4dd38027cb8d0e2d8f321fd055e2ce417`)
  contains table row `3027-77A3OUSOF` at `0x6a08`, but no `F77ABU`,
  `BN9659934`, `F_RSM1` or `TconFw` token. `Factory_Part2.dat` (SHA256
  `bbaac89c4a3ad1ab56b664180d5b6445c86f703c275d228b37b66947736a0b01`)
  contains none of those searched tokens.

The corrected SSB reports (`qd-ssb-readback-acquisition-boundary.md` SHA256
`911c230c3509752f318af6e8ca7aa846547510c41c28a4fcdcbb02f6c72c7607`
and `ssb-transport-driver-binding.md` SHA256
`c35361bce02aae2946b5b0f4e22cab80af20c348c63a4cafd9267f3cfb05bbe7`)
do not supply a passive alternative. Their backup path writes a protocol
header, may runtime-resume the USB interface, performs USB transfers, and
creates/truncates an output file; named SSB nodes were not exposed in the
captured metadata. Static VID/PID and the present Samsung USB device do not
bind that address space to the 2 MiB F77 image.

An official full MSD host acquisition completed while this audit was being
written. I independently streamed the resulting local file once: its exact
size is 1,493,538,434 bytes, SHA256
`790584c7a91391bc6e9964c8f1c4649c225d2f9e6aeffabfc5e58e8a64fb7fc3`,
and CRC32 `a8e4a70a`, agreeing with
`overnight/external-msd-parser-20261027a/acquisition-result.json` (SHA256
`86660fc413c97130aa68d37416e47a437750e944b040dc468156674222bd22c6`).
The clear header's stored CRC32 `1f54c22c` equals CRC32 over its 216-byte
declared region; the nine section ranges are contiguous from offset 4,290 to
EOF; the encrypted header has its recorded `Salted__` marker. A direct
bytewise scan of the still-opaque MSD found none of `F77ABU2D20`,
`F77ABUAE20312300`, `F77ABUAE2`, `FA024C300`, `BN9659934B`, the full selected
asset basename, or `TconFwQd77A3OUSOF`. Because encrypted sections can hide
all of those strings, that is not an absence result. Until section decryption
and signatures are independently validated, the clear ranges do not establish
that a matching F77 executable or this BN asset is extractable.

## Decision

The single useful pre-visible-state discriminator is the unique existing
tuple match to **`F_RSM1_BN9659934B_COMMON.bin`**. It should be recorded before
building another equivalent reader. After that correlation, the retained
corpus provides no second independent state discriminator: the profile tuple
is not picture-state aligned, the F77 executable is not present as an
ordinary recovered file, the SSB route is not passive and lacks a proved live
interface binding, and the accepted fault observations are temporally
separated.

Copying or parsing the uniquely matched 5 MiB asset can now be source-bounded
instead of copying all nine, but it would characterize a packaged profile,
not prove current controller contents or explain RT Protect. The next actual
fault-attribution discriminator remains a same-session, owner-annotated
visible-versus-black comparison of the existing controller-status and raw
ERR_DET inputs; the Apps-visible historical latch and software screenshots
cannot substitute for emitted-light observation.

## Materially stale claims to supersede, not edit in place

* `qd-cad-tcon-ex-proc-provider.md` currently says “No retained passive
  evidence chooses among the nine BN filenames” and that only an invocation
  pathname/comparison-pointee artifact could bind one. The unique three-field
  runtime tuple above supersedes that conclusion while retaining all of its
  flashed/current-byte cautions.
* `qd-firmware-resolver-exact-paths.md` still ranks acquisition of the exact
  `tcon_ex_proc` provider as a future step and calls that provider the smallest
  source gap. The exact provider has since been copied as `sdp_pqe_frc.ko` and
  analyzed. Its separate claim that no explicit retail-model/panel/F77-to-BN
  lookup table was found remains literally true, but “no profile selected” is
  now stale because of the independent field-tuple match.
* `overnight/controller-fault-followup-20261026.md` still says the recovered
  fields do not identify which asset applies. It needs an additive correction
  for the unique tuple match. Its provider-closure and SSB limitations remain
  current.
* `CURRENT-INVESTIGATION.md` already correctly says the missing provider was
  acquired; it is not provider-stale. It omits the newly recovered unique
  profile binding and should link this audit when next updated.

No statement here establishes fault causality, validates a permanent fix, or
authorizes applying an asset, invoking CAD operation `0x20`, opening SSB,
overriding protection, or changing firmware.
