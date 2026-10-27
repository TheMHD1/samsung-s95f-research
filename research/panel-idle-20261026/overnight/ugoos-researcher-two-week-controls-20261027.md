# researcher two-week Jellyfin controls and diagnostic exceptions

Recorded [private-viewing-time] UTC. This report separates the owner's physical-use
statement from read-only server metadata. It makes no TV, playback, HDMI,
root-device, or server-setting action.

## Owner-confirmed interpretation

The owner confirms that normal researcher Jellyfin viewing during the preceding two
weeks works, specifically naming PROGRAM_08, PROGRAM_A's Farm, PROGRAM_09,
PROGRAM_06, and PROGRAM_07; this is the physical-success source for
the controls. PROGRAM_04 EPISODE_REDACTED and the offered PROGRAM_B EPISODE_REDACTED
run are diagnostic **failure exceptions**, not controls. Samsung TV Plus is a
separate incident class: the owner says it generally works but can have rare,
brief, self-recovering blackouts. No current TV Plus state is asserted here.

Watch-history state (including `completed`) is metadata, not independent proof
that a picture stayed lit. Conversely, the owner's normal-viewing statement is
not a server capture of HDMI output, output colour mode, or panel state.

## Read-only two-week snapshot

The retained direct-database snapshot was scoped to the same requested profile
as the prior PROGRAM_LABEL record, identified internally by that exact record
rather than retaining an account identifier. It selected history rows dated
from `[private-viewing-time]` onward and joins the server's indexed stream metadata. No
media path, user/account ID, token, URL, or endpoint is retained.

| owner-named control found in timeline | server last-played timestamp | indexed source metadata |
| --- | --- | --- |
| PROGRAM_08 (2017) | [private-viewing-time] | HEVC Main 10, 3840x2160, 10-bit, 23.976; BT.2020/PQ; DV profile 8; TrueHD Atmos 7.1 |
| PROGRAM_A's Farm EPISODE_REDACTED, PROGRAM_16 | [private-viewing-time] | HEVC Main 10, 3840x1744, 10-bit, 25; BT.2020/PQ; HDR10+; E-AC-3 5.1 |
| PROGRAM_06 EPISODE_REDACTED | [private-viewing-time] | HEVC Main, 3840x1920, 8-bit, 23.976; BT.709 triplet; E-AC-3 5.1 |
| PROGRAM_06 EPISODE_REDACTED | [private-viewing-time] | same indexed HEVC Main, 3840x1920, 8-bit, BT.709 / E-AC-3 5.1 family |
| PROGRAM_07 (2013) | [private-viewing-time] | HEVC Main 10, 3840x2160, 10-bit, 23.976; BT.2020/PQ; DTS-HD MA 5.1 |
| PROGRAM_10: PROGRAM_11 and PROGRAM_12 entries | [private-viewing-time] through [private-viewing-time] | primarily HEVC Main 10, 1440x1080, 10-bit, 23.976, BT.709 where indexed; AAC stereo. PROGRAM_11 08 is separately H.264 High 4:2:2, 8-bit, 1440x1080. |

Additional timeline diversity includes PROGRAM_13 EPISODE_REDACTED (H.264 High,
1920x1080, 8-bit, 29.970, BT.709; AC-3 stereo), PROGRAM_14 EPISODE_REDACTED (HEVC Main
10, 3840x1920, 10-bit, BT.2020/PQ, DV profile 8/HDR10+; E-AC-3 Atmos), and
several 4K HDR titles. Those rows support the owner's broad “normal viewing”
context, but are not individually re-confirmed physical controls in this
report.

No PROGRAM_09 row falls in the selected `>=[private-viewing-time]` server timeline. A
prior retained history snapshot contains PROGRAM_01 (2021) dated
[private-viewing-time], just outside that cutoff. It is therefore not silently substituted
for a two-week row. The title matches above are exact server title/series/year
matches: `PROGRAM_06` is the 2026 EPISODE_REDACTED series entries, and `The
PROGRAM_LABEL` is the 2013 movie; no variant was guessed.

## Exceptions and resulting constraint

PROGRAM_04 EPISODE_REDACTED is indexed as H.264 High level 4.1, 1920x1080, 8-bit,
23.976, no HDR/DV colour metadata, DTS-HD MA 5.1/24-bit. PROGRAM_B
EPISODE_REDACTED is indexed as H.264 High level 4.0, 1920x1080, 8-bit, 23.976, no
HDR/DV colour metadata, DTS-HD MA 5.1/16-bit. They are the two explicitly
diagnostic failure cases—not evidence that these formats universally fail.

The controls span indexed SDR/BT.709 and BT.2020/PQ sources; H.264, HEVC;
8-bit and 10-bit; approximately 23.976, 25, and 29.970 frame rates; and AAC,
AC-3, E-AC-3, DTS-HD MA, and TrueHD audio. That contradicts a theory that one
of those source-format labels is a necessary, sufficient explanation by
itself. It does not establish the actual HDMI output mode or rule out a
mode-transition, device/output state, timing, content-start, or intermittent
panel/controller interaction.

## Method boundary

The prior X-Emby-token-only request was not repeated. The route recovery used
the documented Proxmox-to-CT102 path. A documented separate key-file source
was located without disclosing it; the compact API history attempt produced no
retained payload, so this report bases its actual timeline and source fields
on read-only SQLite SELECTs from the existing Jellyfin metadata database.
There was no write, new key, token reset, authentication change, polling loop,
or current-session query.
