# Ugoos media-path comparison: PROGRAM_04 and PROGRAM_A's Farm

Recorded 2026-10-27 UTC. This is a read-only Jellyfin API and existing Kodi
session review. It did not start, stop, seek, transcode, reconfigure, refresh,
or otherwise control playback; it made no TV call.

## Exact failing item

The owner identified the reproduction as *PROGRAM_04*, “episode 1”, at the
beginning. A live Kodi-session read before the PROGRAM_A comparison independently
matched the active item to the Jellyfin episode titled **PROGRAM_LABEL**, EPISODE_REDACTED. It was
`DirectPlay`, not transcoding, on the existing Kodi/CoreELEC Ugoos session.

The source is a local MKV file (not the separately indexed HTTP/STRM version
of that series):

| property | observed value |
| --- | --- |
| video | H.264 High, level 4.1, 1920x1080, 23.976025 fps |
| pixel format / depth | yuv420p, 8-bit |
| range / colour | SDR; no Dolby Vision or HDR metadata returned |
| video bitrate | 19,887,312 bit/s |
| audio | DTS-HD MA, 5.1, 48 kHz, 24-bit; reported DTS bitrate 4,200,000 bit/s |
| delivery | direct file source, MKV, Jellyfin `DirectPlay` |

This establishes that the file itself is not encoded with HDR or Dolby Vision.
It does not establish the HDMI output mode: Kodi or the TV can retain, leave,
or transition from another HDR/display mode independently of this file. It
therefore does not rule out HDMI timing, decoder/output state, audio format, a
particular frame cadence, or the panel/controller fault already reproduced
independently.

## Current independent comparison case

During the owner-approved current comparison, the live Ugoos session was
*PROGRAM_A's Farm* EPISODE_REDACTED, **PROGRAM_16**. It too was Jellyfin `DirectPlay` with
no `TranscodingInfo`, but it has a distinctly different local MKV format:

| property | PROGRAM_04 EPISODE_REDACTED (failure) | PROGRAM_A's Farm EPISODE_REDACTED (comparison) |
| --- | --- | --- |
| video | H.264 High 4.1 | HEVC Main 10 level 150 |
| size / frame rate | 1920x1080 / 23.976025 fps | 3840x1744 / 25 fps |
| depth / range | 8-bit SDR | 10-bit HDR10+ |
| colour | no colour triplet returned | BT.2020 non-constant luminance, PQ, BT.2020 primaries |
| video bitrate | 19.89 Mb/s | 14.81 Mb/s |
| audio | DTS-HD MA 5.1 | E-AC-3 5.1 |
| delivery | local file, DirectPlay | local file, DirectPlay |

The user had also said PROGRAM_08 had worked. The 2017 local PROGRAM_08 record is a
4K, 23.976-fps, HEVC Main 10 Dolby Vision profile 8 with HDR10 fallback and
TrueHD Atmos, but it was not the item playing in this comparison. It is useful
historical context only.

## Interpretation limits

These are server metadata and session observations, not a capture of HDMI
InfoFrames or what Kodi actually selected at the physical output. The episode
title search also finds a separate HTTP/STRM catalogue copy of *PROGRAM_04*
and an analogous PROGRAM_A catalogue copy; neither was used for the observed
Kodi session. File paths, streaming URLs, tokens, account identities and
remote endpoints were intentionally omitted.

The two active cases are format-independent enough to test a useful hypothesis:
a fault occurring with both the SDR/H.264/DTS case and the HDR10+/HEVC/E-AC-3
case would weaken a media-mode-only explanation. A successful PROGRAM_A run
does not clear the TV, because the panel/controller fault is intermittent.

## Evidence method

Authenticated, read-only requests were made from the established Media CT102
administrative connection to Jellyfin's `Sessions` and per-item metadata
endpoints. The server health endpoint returned `Healthy`. Only compacted media
fields required for this comparison were retained in the terminal evidence.

PROGRAM_04 match came from the then-active Kodi session: its returned item
was `PROGRAM_LABEL`, series *PROGRAM_04*, season 1, episode 1, `DirectPlay`, with a
local-file media source carrying the metadata tabulated above. The subsequent
PROGRAM_A session was reread at **2026-10-27T01:55:24Z** and returned *PROGRAM_16*,
*PROGRAM_A's Farm* EPISODE_REDACTED, `DirectPlay`, no transcoding, and the tabulated local
file-source streams. The two observations were separate in time; no claim is
made that the first session was still active during the second read.

