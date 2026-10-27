# Ugoos PROGRAM_A Farm comparison against PROGRAM_04 failure

Date: 2026-10-27 UTC

## Bottom line

The owner reported that *PROGRAM_A's Farm* was running with the picture
visible and staying on. This gives a useful working comparison to the earlier
*PROGRAM_04* run, where the owner reported a black picture with audio
continuing.

The clearest measured differences are:

| Evidence | PROGRAM_04, black/audio | PROGRAM_A's Farm, visible |
|---|---|---|
| Jellyfin/Kodi item | EPISODE_REDACTED “PROGRAM_LABEL” | EPISODE_REDACTED “PROGRAM_16” |
| delivery | local MKV, DirectPlay | local MKV, DirectPlay |
| source video metadata | H.264 High 4.1, 1920x1080, 23.976, 8-bit SDR | HEVC Main 10, 3840x1744, 25 Hz, HDR10+/BT.2020 PQ |
| negotiated HDMI report | 1920x1080, `vfreq=2400` | 3840x2160, `vfreq=5000` |
| AVE HDR log after relock | `MetaType[0]`, `HDR10+[0]` | `MetaType[1]`, `HDR10+[1]` |
| QD selector `0x128` | 51 writes: 292, 256, then 255..207 | 2 writes: 339, then 375 |
| screen-saver selector `0xc4` | one write of 0 | no `0xc4` write retained |
| I2C transfer failure | one `-6` read result, missing reply | none |
| `CLEAR_AVMUTE` vlog rows | 1,114 | 1 |
| post-cleanup TCON status | accepted `0x10` | accepted `0x00` |
| post-cleanup fault-pin sample | accepted value 1 | formal read rejected; complete raw managed output says value 0 |

This is a real paired state discriminator. In particular, the accepted status
returned from `0x10` after the failed playback to `0` after the working
playback. The fault-pin direction agrees in the raw data, but the PROGRAM_A
pin read is not accepted and is used only as supplemental evidence.

The comparison does **not** isolate a single media property as the trigger:
codec, cadence, HDMI timing, dynamic range, colour metadata and audio codec
all changed together. It does show that the fault is not a permanent state of
the TV on this boot and gives concrete dimensions for a future one-variable
test.

## Capture validity

Both onset captures are rejected by the same strict endpoint rule:

- `ugoos-movie-20261027a.onset`: `ValueError: AVOC maps changed`;
  AVOC's second heap mapping grew from end `0x0229d000` to `0x022d1000`, a
  change of `+0x34000` (212,992 bytes).
- `ugoos-PROGRAM_A-20261027a.onset`: `ValueError: AVOC maps changed`;
  the same heap mapping shrank from end `0x022d6000` to `0x022d4000`, a
  change of `-0x2000` (8,192 bytes).

Each start/end map set has 1,345 rows and exactly 1,344 rows are identical;
the heap boundary is the only difference. These look like heap-brk changes,
not source-library replacement, but neither is waived. Both records remain
`accepted=false`, `technical_capture_complete=false`, and
`diagnostic_eligible=false`. Both collectors reached `CAPTURE_COMPLETE`, had
empty collector stderr, and verified quiesce and cleanup.

The PROGRAM_A physical trace window was:

```text
TRACE_ARMED       87360.640533
PREROLL_START     87360.849088
CAPTURE_START     87361.884239
CAPTURE_END       87421.997713
DRAIN_END         87422.103221
```

PROGRAM_04 window was `86932.696670..86992.860027`, with drain end
`86992.969342`.

All seven PROGRAM_A final sidecars are byte-identical to their corresponding
`partial-*` copies. Their hashes are:

| Artifact | SHA-256 |
|---|---|
| `record.json` | `9d34a16fb63163cd7f19955c9974169057d4c57e70ba302b65530834a9d8aee1` |
| `trace` | `dfb92dd85f9f495ef6ea833e976b41d9e7d31337a4389c606206e682a7979aca` |
| `meta.txt` | `c6805498d8ab424c81bced8a4b83baaf4875a51132d267f8d4554cf711b6d2c8` |
| `samples.txt` | `5cf8950c6cd17177eea81ea0cc7dbcae895eccda18197c88e2dd74dbb9c6b30b` |
| `sample-errors.txt` | `f3ebb7728601b25a9f61108d97100bebbb33db6eb711f680373b4d2d32873815` |
| `vlog-after.txt` | `4cb5bdc2d73f03bd4e4ac48720b6b2edc00712b5d4bee3a9856fd8c596b8cfc7` |
| `artifacts.txt` | `048b4e815d49c17e8f5e8b5ffc11789291730313e33946594e9867d7de419c61` |
| `fds.txt` | `0b63fd46e91789d6bbfb925b825f2102b4ff4e5c8024beec4da92672a0ca9e57` |

## Owner observations and timing

The original PROGRAM_A `observer.jsonl` contains the GO note at estimated TV
uptime `87377.122` and the owner's “done” acknowledgement at `87415.511`.
Neither is a calibrated physical picture annotation.

The explicit later messages—“picture visible and staying on” and “and
PROGRAM_A farm is running”—arrived after the observer input loop had ended.
They are preserved in
`overnight/hdmi-blackout-20261027a/owner-playback-observations.jsonl`
(`647b9fc978d538bc30c6e6bcce3b086b60ce5019640027018baa182dc6532fb6`).
They establish the owner's working-state report, but have no calibrated TV
uptime and are not retroactively inserted into the rejected capture.

The PROGRAM_A HDMI transition starts around `87398.39`, approximately 21
seconds after the GO note, and returns to normal by `87401.052`. The “done”
note is about 14 seconds later. In PROGRAM_04 run the analogous transition
returned to normal at `86944.584`, while the black/audio owner report was
received around `86966.244`, roughly 22 seconds later. Thus neither run
places a calibrated physical picture transition at the HDMI relock itself.

## Media and negotiated-mode comparison

The independently acquired media/session report is
`overnight/ugoos-media-comparison-20261027.md`
(`0e5ac173616c7a862426d558d66873bcb63f730c873e571c30be3ff950858da1`).
Both items were local-file DirectPlay sessions, not transcodes:

- PROGRAM_04: H.264 High level 4.1, 1920x1080 at 23.976025 fps, 8-bit SDR,
  DTS-HD MA 5.1.
- PROGRAM_A's Farm: HEVC Main 10, 3840x1744 at 25 fps, HDR10+ with BT.2020/PQ,
  E-AC-3 5.1.

Those are source-file/session properties. The embedded kernel snapshots show
the actual HDMI receiver reports:

### PROGRAM_04

```text
86941.849024  vid_mute
86941.867131  NORMAL -> PWR_UP
86941.870950  input lock = 0
86941.895293  S_RESOLUTION 720x480, vfreq=2400
86943.845932  WAIT_PKT_FILT -> LINK_STABLE
86944.584493  CONN_VID_PATH -> NORMAL
86944.590930  input lock = 1
86944.638818  S_RESOLUTION 1920x1080, vfreq=2400
86944.771796  DRM-DP mute off
```

### PROGRAM_A's Farm

```text
87398.392953  vid_mute
87398.411100  NORMAL -> PWR_UP
87398.426918  input lock = 0
87398.503314  S_RESOLUTION 720x480, vfreq=6000
87400.619760  WAIT_PKT_FILT -> LINK_STABLE
87401.051794  CONN_VID_PATH -> NORMAL
87401.054958  input lock = 1
87401.078679  S_RESOLUTION 3840x2160, vfreq=5000
87401.304416  DRM-DP mute off
```

AVE logs follow that mode difference. PROGRAM_04 transition contains only
`MetaType[0]` / `HDR10+[0]` rows; PROGRAM_A changes from those initial values
to `MetaType[1]` / `HDR10+[1]` between `87401.084` and `87401.222`.
This is consistent with, but more direct than, the server metadata. It does
not mean the HDMI raster equals the encoded 3840x1744 source dimensions.

## QD wire comparison

The frozen offline `decode-qd-trace.py` reports:

| | PROGRAM_04 | PROGRAM_A's Farm |
|---|---:|---:|
| grouped transfers | 293 | 141 |
| parse errors | 0 | 0 |
| partial/failed transfers | 1 | 0 |
| decoder focus rows | 0 | 0 |
| decoder maintenance rows | 0 | 0 |
| decoder dimming-focus rows | 52 | 2 |

Both raw rings have complete retained/written accounting, and both pass the
decoder's transfer-grammar checks. That narrow decoder result does not repair
either observer's map rejection.

PROGRAM_04 trace has:

- screen-saver selector `0xc4` value 0 at `86937.845748`;
- configuration groups at `0x21c..0x258` and `0x31c..0x358`;
- selector `0x128` writes 292, 256, then 255 down to 207 from
  `86941.269531` through `86944.250072`;
- a status-handshake-shaped read at `86944.133660` with no reply and Linux
  I2C result `-6`.

The PROGRAM_A trace instead has:

- no selector `0xc4` write;
- different configuration groups at `0x49c..0x4d8` and `0x39c..0x3d8`;
- selector `0x128` values 339 then 375 at `87401.167549` and `87401.198030`;
- no partial or failed transfer.

The configuration ranges are reported as raw selectors because the pinned
decoder does not assign them a semantic name. Successful Linux transfer
counts are not controller acknowledgements.

## Kernel and vlog comparison

The PROGRAM_A kernel snapshots validate as nonempty gzip/base64 on the same
boot. START was taken at uptime `87351.33` and covers ring timestamps
`87295.577755..87351.378966`. END was taken at `87422.49` and covers
`87305.366569..87422.531662`, temporally bracketing the trace window. Their
plain ring hashes are respectively:

- `2f15987a7156b247c5b1e20221f6feab697f5dbe7c298a47bc2732fceb64b8ab`
- `54982d2c07ee009f05304dbf72899cfb57ba9fade65e986f5fb800d8a13ec759`

The new PROGRAM_A kernel rows include the negotiated-mode sequence and QDF
configuration traffic. They contain no `ERR DET` or `RT Protect` line during
the capture.

Two high-volume userspace indicators do not discriminate the outcomes:

- `QD_TCON_OFF = 1`: 65 times in each vlog, approximately once per second;
- `spdif out mute (0)`: 1,144 PROGRAM_LABEL rows and 1,143 PROGRAM_A rows.

The sharp log difference is HDMI `CLEAR_AVMUTE`: 1,114 PROGRAM_LABEL vlog rows
from `86943.860..86994.997`, but only one PROGRAM_A row at `87400.604`.
PROGRAM_04 receiver repeatedly issued the clear indication after relock;
PROGRAM_A did not. This is a useful HDMI-state difference, not by itself an
error code or explanation for panel protection.

Periodic DRM-DP rows in both captures continued to report sync 1 and mute
tuple `(0 0 0 0)` after their respective transitions.

## Post-cleanup status and pin

The working PROGRAM_A status read is accepted and cleanup-confirmed:

- path: `overnight/hdmi-blackout-20261027a/ugoos-PROGRAM_A-on-status.json`
- SHA-256: `f84246b6a04693eb489ce31946bd90d1c529c66552f77dc94f1c6e0213c20ade`
- execute uptime: `87576.21`
- ioctl return: 0
- sentinel changed to status `0x00000000`

This reverses the accepted `0x00000010` obtained after PROGRAM_04 black
state at `87101.04`. Both readers still classify only
`kernel_output_written`; controller read-to-clear and QDF debug override are
not excluded by the managed result alone.

An immediate raw kernel acquisition was itself marked rejected because its
host parser accidentally changed a marker token from `PAYLOAD` to
`PAY87573AD`. The authenticated command nevertheless returned a valid
base64/gzip payload. Offline decoding of those retained bytes gives 5,982
plain bytes (SHA-256
`2d19ceaa3f25add9b87dbb468b5dc745f6aecf4a6938f6bd674f8df432a3250e`)
and includes the exact same-process kernel row:

```text
[87576.145035] [TCON:QDF] QDFTcon_GetErrDetStatus[24391:TconStatusRead.]: ERR DET Status:0x0
```

The decoded bytes are preserved as
`ugoos-PROGRAM_A-query-kernel-offline.txt` with that SHA-256. The extraction
record is `ugoos-PROGRAM_A-query-kernel-offline-extraction.json`
(`339ee3cb63ba0d4129071177b15cd438604ab378a822b158fa6c4a11af45b0c0`).
The pinned QDF ABI analysis places this log before its debug-override branch,
so this is stronger evidence for a raw zero at that call than the managed
payload alone. It still does not prove the physical panel state or repair the
rejected capture.

The rejected wrapper record is
`ugoos-PROGRAM_A-query-kernel.json`
(`69abf9d29493b49f2e740572cdeaf45d4d6d0fb9f31fb795e325d8446a6783ce`).
The decoded row does not convert that wrapper record to accepted.

The PROGRAM_A pin reader is also formally rejected:

- path: `ugoos-PROGRAM_A-on-pin.json`
- SHA-256: `0c6947705a1e0ce5886d1af7d4234597c20bfe393757fe5471a64a46eb523467`
- error: `ContractError: Remote command stderr`
- cleanup: confirmed

The stderr was:

```text
cat: /proc/24696/stat: No such file or directory
```

This is a process-poll race in the shell wrapper, not a reported managed
helper failure. In `pstart`, `/proc/24696/stat` passed the readability test,
then disappeared before the following `cat` after the helper exited. The
same command records `HELPER_EXIT=0`, `HELPER_DEADLINE_HIT=0`, complete
managed output, successful input request/get, both closes returning zero, and
`VALUE0=0`. Because any remote stderr is forbidden, the host correctly
rejected the read. Raw value 0 is therefore supplemental only and must not be
presented as an accepted pin measurement.

## What the pair now tests

The working and failing cases establish a practical comparison axis:

- The failure is associated with a 1080p/24-style SDR HDMI mode, repeated
  `CLEAR_AVMUTE`, a long downward selector-`0x128` sequence, one failed QD
  read, and later status `0x10`/accepted pin 1.
- The working case is associated with a 2160p/50-style HDR10+ HDMI mode, two
  upward selector-`0x128` writes, no failed QD transfer, status 0, and a
  rejected-but-complete raw pin value 0.

The next informative comparison would hold the HDMI output mode constant
across both items—most directly, run PROGRAM_04 while Ugoos stays at the
PROGRAM_A-observed 2160p/50-style output, then compare it with PROGRAM_A under
that same output. A complementary test would hold PROGRAM_04 constant and
compare its current 1080p/24-style output with 2160p/50-style output. Those
tests separate output timing/raster from the media item better than another
random title. The present evidence does not justify a blanket “HDR is safe”
or “SDR causes the fault” conclusion: codec, cadence, output mode, dynamic
range, audio and content-dependent dimming policy all changed together.

No TV, root, network, playback, key, getter, setter or ioctl action was made
for this report. It only parses the already retained local evidence.
