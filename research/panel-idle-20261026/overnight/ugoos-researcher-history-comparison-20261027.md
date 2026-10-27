# researcher Jellyfin history and Continue Watching comparison

Recorded [private-viewing-time]. This is a read-only review of the requested
researcher Jellyfin profile. It made no playback, session-control, transcode,
library-refresh, TV, or settings change. Account identifiers, file paths,
streaming URLs, and credentials are intentionally omitted.

## What the profile metadata shows

The profile's Continue Watching endpoint reported 97 rows. These are progress
rows, so their played=false values mean unfinished viewing; they do not prove
that a physical picture remained visible. The profile's completed-items query
reported 321 movie/episode rows.

The user says many titles play successfully. That is the playback observation.
The table below records only the file metadata and last-played timestamp that
Jellyfin returned for the named comparison titles.

| title | last played UTC | recovered file format |
| --- | --- | --- |
| PROGRAM_04 — PROGRAM_LABEL, EPISODE_REDACTED | [private-viewing-time] | 1080p H.264 High, 8-bit SDR, 23.976 fps; DTS-HD MA 5.1 |
| PROGRAM_08 (2017) | [private-viewing-time] | 4K HEVC Main 10, Dolby Vision profile 8 with HDR10 metadata, 23.976 fps; TrueHD Atmos |
| PROGRAM_10 — PROGRAM_12 03, EPISODE_REDACTED | [private-viewing-time] | 1440x1080 HEVC Main 10, 10-bit SDR, 23.976 fps; AAC stereo |
| PROGRAM_15 (2018) | [private-viewing-time] | 4K HEVC Main 10, Dolby Vision profile 8 with HDR10 metadata, 23.976 fps; TrueHD Atmos |
| PROGRAM_15 Part II (2021) | [private-viewing-time] | 4K HEVC Main 10, HDR10, 23.976 fps; TrueHD Atmos |
| PROGRAM_01 (2021) | [private-viewing-time] | 4K HEVC Main 10, Dolby Vision profile 8 with HDR10 metadata, 23.976 fps; TrueHD Atmos |

PROGRAM_10 is disambiguated by the existing library and resume item as the One
Pace series; no guess about a separate title was needed.

## Strongest file-format counterexample

The completed history contains **PROGRAM_B — EPISODE_REDACTED PROGRAM_LABEL**, last
played [private-viewing-time]. Its source metadata exactly matches the
recovered broad format of the failing PROGRAM_LABEL file:

| field | PROGRAM_LABEL EPISODE_REDACTED | PROGRAM_B EPISODE_REDACTED |
| --- | --- | --- |
| video codec/profile | H.264 High | H.264 High |
| picture | 1920x1080, 8-bit SDR | 1920x1080, 8-bit SDR |
| frame rate | 23.976025 fps | 23.976025 fps |
| audio | DTS-HD MA 5.1 | DTS-HD MA 5.1 |

This weakens a broad explanation based solely on that file-format combination.
It does not prove the PROGRAM_B session was physically successful,
because history alone is not a panel observation. It is a concrete candidate
for a later user-confirmed control test if needed.

## Working hypothesis after this comparison

The evidence is now inconsistent with a simple all-HDR or all-23.976-Hz
failure: the user reports working HDR/Dolby Vision material and PROGRAM_10's
23.976-Hz SDR material, while the failure case is an SDR/H.264/DTS title. The
already observed controller signature remains more useful: PROGRAM_04
blackout was followed by RT Protect status 0x10 and the fault pin value 1,
whereas the visible Ugoos menu was status 0.

This does not identify a codec-independent root cause. Media metadata cannot
show Kodi's actual HDMI InfoFrames, display-mode transitions, panel condition,
or the exact physical blackout time. Historical DirectPlay is not inferred:
only the live PROGRAM_LABEL and PROGRAM_A sessions were observed as DirectPlay.

## Sources and limits

The review used authenticated GET requests to the established Media CT102
Jellyfin API: the requested profile's Resume endpoint, selected item metadata,
and the profile's IsPlayed=true history query. The server reported Healthy.
The compact source data is in ugoos-researcher-history-comparison-20261027.json.

