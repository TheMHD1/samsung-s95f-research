# Physical-blackout incident comparison

Date: 2026-10-27 UTC

## Scope and result

This is an offline comparison of retained evidence only. No TV, media-server,
network, root, USB, GPIO, playback, UI, power, or controller operation was
performed. Paths below are relative to
`${S95F_EVIDENCE_ROOT}/panel-idle-20261026/` unless shown
otherwise.

The retained data supports two useful conclusions and one important absence:

1. The persistent *PROGRAM_LABEL* and *PROGRAM_B* failures both have a
   later accepted stock status `0x10` and independent fault-input value `1`.
   The owner-visible Ugoos menu and owner-visible PROGRAM_A control instead
   have accepted stock status `0`. These are sequential state associations,
   not event-time samples or proof that the status caused loss of light.
2. The compositor-to-light equivalence is directly falsified: the compositor
   returned nonblack Apps imagery while the owner confirmed the physical panel
   was black throughout B0/B1. Other high-volume markers are not useful
   discriminators at the retained timing resolution: an owner-visible Apps
   evidence set contains a nearby periodic `QD_TCON_OFF=1` row, and the raw
   Ugoos-menu recording associated with an owner-visible control contains
   repeated HDMI `CLEAR_AVMUTE`. The latter recording is rejected and its
   owner timing is uncalibrated, so those two points are retained as
   non-specific associations rather than strict event-time falsifiers.
3. The evidence does **not** yet falsify or prove the narrower proposition
   “RT halfword `root+0x240a == 0x1001` means the physical panel is black.”
   The only accepted fresh `0 -> 0x1001` capture, V6, had no human observation
   of emitted light. Conversely, none of the owner-confirmed black incidents
   sampled that RT halfword at the physical transition. Stock status `0x10`
   and RT halfword `0x1001` are different observations and are not silently
   equated here.

There is also no retained log comparison that distinguishes the owner's rare,
self-recovering picture losses with an audio pause from the persistent losses
where audio continues. The brief Ugoos/JBL and TV Plus incidents were reported
historically but were never captured with calibrated physical/audio timing or
fault-status/RT data.

## Evidence matrix

“Fresh/bracketed” below asks whether the physical transition itself is bounded
by an accepted technical capture. It does not treat a later status query, a UI
screenshot, or an uncalibrated chat-persistence timestamp as an onset marker.

| Case | Owner-observed panel and audio | Retained timing and primary artifacts | Host/controller evidence | Fresh physical onset? | Retained playback metadata |
|---|---|---|---|---|---|
| Populated Apps control | Full Apps page explicitly visible; later owner account says it can remain visible through a moving screensaver. Audio not relevant. | `paired-capture/apps-visible-control.json`, `paired-capture/apps-visible-control.png`, and `paired-capture/apps-visible-control-summary.json`; `2026-10-26 03:33:17 UTC`, target uptime `7206.74`. A separate next-day owner-reported working-Apps state precedes `overnight/paired-restart-20261027a/good-apps-status.json` at uptime `83948.26` and `overnight/paired-restart-20261027a/good-apps-pin.json` at `83960.86`. | Screenshot is nonblack. Separate accepted sequential values are stock status `0` and pin `0`; their records themselves say physical state unobserved. | No. This is a visible control, not an onset capture; the next-day status/pin reads are not synchronized with the owner's report. | Native Apps catalog only; no media playback. |
| Owner-triggered Live persistent blackout | Owner went to Live, physical panel stayed completely black, blind return to Apps failed, and audio/menu clicks continued. | B0: `paired-capture/black-after-live-b0.json`, `paired-capture/black-after-live-b0.png`, and `paired-capture/black-after-live-b0-summary.json` at `2026-10-26 03:36:24 UTC`, uptime `7393.61`; B1: `paired-capture/black-volume-b1.json`, `paired-capture/black-volume-b1.png`, and `paired-capture/black-volume-b1-summary.json` at `03:36:55 UTC`, uptime `7424.12`; annotation in `owner-observations-20261026.json`. | Both captured images are nonblack Apps/UI imagery despite the confirmed black physical panel. No stock status, pin, or RT read was taken for this exact incident. | Controlled navigation followed the earlier Apps control, but no exact physical transition time or event-time controller bracket exists. | Samsung Live/native UI; no stream metadata retained. |
| Ugoos menu baseline | Owner confirmed the Ugoos menu and physical panel were visible before starting the movie. Audio state was not separately annotated. | Raw transition record `overnight/ugoos-on-20261027a.onset/record.json` is rejected for changing FD identity. Sequential accepted status record `overnight/hdmi-blackout-20261027a/ugoos-menu-status.json`, created `2026-10-27 01:31:24..01:31:26 UTC`, uptime `86297.39`. | Stock status `0`. The rejected source recording contains sustained approximately-24-Hz `CLEAR_AVMUTE` associated with this owner-visible control, which makes the marker non-specific in the retained comparison; owner timing is not calibrated tightly enough to call it an event-time physical falsifier. No pin sample. | No. Owner visibility and status are sequential, not calibrated/simultaneous; the observer is rejected. | Ugoos menu, not a movie baseline. |
| *PROGRAM_04* EPISODE_REDACTED persistent failure | Owner: screen went dark and audio continued while the episode played from the beginning. | Rejected-but-complete raw observer `overnight/ugoos-movie-20261027a.onset/record.json` (SHA-256 `2a8b8f922cf8dc0ae4d06fc8cefe3115c81434f1de4642ec149fb2ec7d4b0f59`), trace window uptime `86932.696670..86992.860027`, drain `86992.969342`; owner black/audio report estimated near `86966.244`, with timing uncertainty retained in `overnight/ugoos-PROGRAM_A-comparison-20261027.md`. Exact owner wording is in `overnight/hdmi-blackout-20261027a/owner-playback-observations.jsonl`. | Trace shows HDMI relock complete by `86944.584`, then normal sync/mute reporting; no in-window `ERR DET` or `RT Protect` query log. Later accepted `overnight/hdmi-blackout-20261027a/ugoos-movie-black-status.json` returned `0x10` at uptime `87101.04`; accepted `overnight/hdmi-blackout-20261027a/ugoos-movie-black-pin.json` returned `1` at `87129.47`. Raw QD comparison includes the 51-value selector-`0x128` ramp, one `0xc4=0`, sustained `CLEAR_AVMUTE`, and one failed I2C read/no reply. | No accepted bracket. The owner report plausibly lies inside the raw trace, but there is no calibrated visible-to-black annotation and the whole observer remains rejected because the AVOC heap map changed. Status/pin are later. | Jellyfin/Kodi local MKV DirectPlay; H.264 High 4.1, 1920x1080, 23.976025 fps, 8-bit SDR, DTS-HD MA 5.1/24-bit. HDMI receiver reported 1920x1080, `vfreq=2400`, SDR. Source/session report: `overnight/ugoos-media-comparison-20261027.md`. |
| PROGRAM_A's Farm EPISODE_REDACTED stable control | Owner explicitly reported “picture visible and staying on” and that PROGRAM_A was running. Audio was not separately annotated. | Rejected-but-complete raw observer `overnight/ugoos-PROGRAM_A-20261027a.onset/record.json` (SHA-256 `9d34a16fb63163cd7f19955c9974169057d4c57e70ba302b65530834a9d8aee1`), capture uptime `87361.884239..87421.997713`, drain `87422.103221`. Explicit visible messages arrived after the recorder input loop and were later persisted in `owner-playback-observations.jsonl`; exact physical time is uncalibrated. | Accepted `hdmi-blackout-20261027a/ugoos-PROGRAM_A-on-status.json` returned `0` at uptime `87576.21`; matching raw QDF row is at `87576.145035`. The formal pin run is rejected, although its complete managed output says `0`. Raw trace has two selector-`0x128` writes, no failed QD transfer, one `CLEAR_AVMUTE`, and no `0xc4` write. | Not an onset case. It is a useful owner-visible stable control, but its observer is rejected for an AVOC heap-map change and the status read is later. | Jellyfin/Kodi local MKV DirectPlay; HEVC Main 10, 3840x1744, 25 fps, HDR10+/BT.2020 PQ, E-AC-3 5.1. HDMI receiver reported 3840x2160, `vfreq=5000`, HDR. |
| *PROGRAM_B* EPISODE_REDACTED persistent failure | Owner first said playback was running, then “screen just went dark.” Audio was not stated for this incident. The supplied photos later show the title in Ugoos UI, but are not continuous playback or onset evidence. | Rejected-but-complete raw observer `overnight/ugoos-program_b-20261027a.onset/record.json` (SHA-256 `67a53c338b5676cbe0fec91baf4e163057fd66e4249d5f31f650b8f23452fade`), capture uptime `90501.630636..90561.782582`, drain `90561.889096`. Playback acknowledgement persisted `2026-10-27T02:42:38.931482Z`; black report persisted `02:45:14.514611Z`, after the capture ended. Persistence time is not physical onset time. | Accepted `overnight/hdmi-blackout-20261027a/ugoos-program_b-status.json` returned `0` at uptime `90686.42`, before the later black report was persisted but with physical state unobserved. Accepted `overnight/hdmi-blackout-20261027a/ugoos-program_b-after-black-status.json` returned `0x10` at `90804.58`; accepted `overnight/hdmi-blackout-20261027a/ugoos-program_b-after-black-pin.json` returned `1` at `90827.89`. The earlier raw trace resembles PROGRAM_LABEL: 1080p24 SDR, the same 51-value `0x128` ramp and `0xc4=0`; it records no failed transfer in that sampled window. Because the black report was persisted after the trace ended and onset is uncalibrated, this does not exclude a transfer failure at or before the physical event. There is no in-window `ERR DET`/`RT Protect` query log. | No. The black report is not forced into the already-ended trace; both status reads are point samples, and the first `0` is not a proved visible sample. | Current Jellyfin session fetch returned HTTP 401, so DirectPlay/current-stream metadata was not observed. Indexed library metadata says H.264 High 4.0, 1920x1080, 23.976, 8-bit SDR, DTS-HD MA 5.1/16-bit. HDMI logs reported 1920x1080, `vfreq=2400`, SDR. |
| Rare Ugoos/HDMI brief loss | Owner history: occasional one or two brief dark intervals with an audio pause, then recovery. The physical route is Ugoos -> JBL Bar 1300X -> TV, so the audio pause cannot be assigned to the TV alone. | `owner-observations-20261026.json`, especially “Expanded owner account before overnight diagnosis”; topology qualification in `tcon-research/overnight-physical-topology.md`. | No synchronized trace, status, pin, RT sample, or timed audio record exists for one of these brief incidents. | No. Historical testimony only. | No incident-specific title/session/output metadata. |
| Rare Samsung TV Plus brief loss | Owner says TV Plus generally works but rarely goes black and comes back. Audio behavior was not stated. | `overnight/owner-control-clarifications-20261027.md` and `overnight/ugoos-researcher-two-week-controls-20261027.md`. | No onset trace, status, pin, RT value, or recovery log for a rare TV Plus event. This must not be merged with the persistent Live-page blackout above. | No. Historical testimony only. | Samsung TV Plus/live; no incident-specific stream metadata. |
| V6 technical RT event, physical state unobserved | No person observed the physical panel; logical Apps/compositor snapshots are not emitted-light evidence. Audio unobserved. | Accepted `overnight/finite-onset-logger-20261027g/onset-v6/record.json`, observe uptime `115887.39..115907.45`; audit `onset-v5-v6-runtime-audit.md`; summary `fault-incident-v6.md`. | Exact RT block changed `root+0x240a: 0 -> 0x1001` during the 20-second bracket and ring appended two `rtp_act_736` rows. Delayed stock status was `0x10` at `116071.70`, and delayed pin was `1` at `116125.46`. | The controller transition is freshly bracketed and accepted; the physical panel state is entirely unobserved. It is therefore not a physical-black onset capture. | No confirmed playback; attempted For You AppControl returned, but sampled UI still showed Apps and receiver consumption was unconfirmed. |

## Exact comparison findings

### Persistent blackouts have a repeated follow-up signature

The strongest repeated state association is:

| Owner context | Accepted stock status | Independent input |
|---|---:|---:|
| Working Apps | `0` at `83948.26` | `0` at `83960.86` |
| Visible Ugoos menu | `0` at `86297.39` | not sampled |
| PROGRAM_LABEL black, audio continuing | `0x10` at `87101.04` | `1` at `87129.47` |
| PROGRAM_A visible/stable | `0` at `87576.21` | formal run rejected; raw output `0` only |
| program_b later reported black | `0` at `90686.42` before report persistence; `0x10` at `90804.58` after | `1` at `90827.89` |

All values are sequential point samples. Their source records explicitly retain
`physical_state="unobserved"`; the owner annotation supplies the surrounding
context, not an invented electrical simultaneity. program_b is especially useful
because it contains a same-boot `0 -> 0x10` sequence ordered around report
persistence, but the first query is not a proved visible sample and report
persistence is not physical-onset time.

### The HDMI raw traces separate modes, not the physical failure by themselves

PROGRAM_LABEL and program_b share 1080p/`vfreq=2400`/SDR receiver state and the same
51-write `0x128` sequence (`292`, `256`, then `255..207`) plus `0xc4=0`.
PROGRAM_A instead uses 4K/`vfreq=5000`/HDR10+ and only two `0x128` values
(`339`, `375`). That is a reproducible source/mode-policy difference.

It is not a complete fault discriminator:

- the rejected 24-Hz Ugoos-menu recording associated with an owner-visible
  menu also contains sustained `CLEAR_AVMUTE`. This makes the marker
  non-specific in the retained comparison, but the uncalibrated owner timing
  prevents calling it a strict event-time counterexample;
- both PROGRAM_LABEL and program_b observer records remain rejected for AVOC heap-map
  endpoint changes, even though their sidecars completed and were preserved;
- PROGRAM_LABEL contains one sampled failed QD read/no reply. The earlier program_b
  60-second trace contains no failed transfer while recording the same SDR
  ramp, so this error is not common to those two **recorded ramp windows**.
  program_b's black report was persisted after its trace ended and physical onset
  is uncalibrated; a failure in the unobserved interval is not excluded, and
  the evidence does not show that transfer failure is unnecessary for a
  blackout;
- the two failed titles have similar broad indexed source metadata, but the
  owner's normal two-week controls span SDR/HDR, H.264/HEVC, multiple frame
  rates, and multiple audio formats. A single broad codec/HDR label is not a
  sufficient explanation.

### Bounded counterexamples and the remaining `0x1001` gap

The retained corpus gives one direct physical counterexample and two narrower
non-discrimination results:

- **nonblack screenshot = lit panel:** false in the B0/B1 Live incident;
- **`QD_TCON_OFF=1` as a sufficient black marker:** the accepted
  owner-visible Apps evidence contains the row at uptime `7207.291749`, about
  `0.55` seconds after the `7206.74` screenshot time. It is a periodic
  retained-log/cache row, not a simultaneous electrical sample, but its
  presence in this tightly adjacent visible evidence means it is not a usable
  sufficient classifier at the recorded resolution;
- **repeated `CLEAR_AVMUTE` as a black-only marker:** the rejected Ugoos-menu
  control recording associated with owner-visible operation contains the same
  frame-paced pattern. This weakens a black-only interpretation but, because
  the observer is rejected and the owner-visible timing is not calibrated, it
  is not promoted to a strict event-time physical falsifier.

The corpus does **not** falsify a requirement for a QD/I2C transfer failure at
physical onset. It only shows that PROGRAM_04-specific sampled error is
absent from the earlier sampled program_b ramp window; the program_b physical onset is not
inside a qualified trace, so the intervening period remains unobserved.

The corpus does **not** yet contain the needed falsifier for
`RT+0x0a == 0x1001` versus emitted light. Specifically, it lacks either:

- an owner-confirmed visible state sampled with that exact RT halfword still
  `0x1001`, or
- an owner-confirmed persistent black state sampled at the same time with the
  exact RT halfword still `0`.

V6 supplies the fresh technical `0 -> 0x1001` event but no physical observer.
The Apps/Live/PROGRAM_LABEL/program_b cases supply physical observations but no event-time
RT-halfword sample. Delayed stock `0x10`/pin `1` agreement does not close that
cross-layer gap.

## Brief recovering versus persistent audio-continuing incidents

The two symptom groups are observationally different:

- rare Ugoos/JBL incidents: picture briefly dark, audio pauses, both recover;
- persistent Live/PROGRAM_LABEL incidents: picture remains black while TV/audio
  or menu clicks continue; ordinary blind navigation does not restore light.

But the logs do not yet establish distinct mechanisms. The brief group has no
synchronized raw trace at all. The persistent PROGRAM_LABEL case has a rejected
but preserved HDMI/QD trace and later `0x10`/pin `1`; the controlled Live B0/B1
case has strong physical annotation and compositor captures but no fault read.
TV Plus brief recovery has neither an audio annotation nor technical capture.

Therefore the exact missing comparison is a single rare self-recovering event
with all of the following retained in one timing model: a pre-event visible
annotation, exact picture-loss and recovery annotations, independent audio
continuity/pause annotation, accepted controller/RT bracket, and source/output
mode. This states the evidence gap; it does not authorize or schedule a new
measurement.

## Source integrity and interpretation limits

Primary owner-observation sources:

- `owner-observations-20261026.json`, SHA-256
  `f76a44254141c1371c6e9336cd5b403983215e9d1b67aa07deb48030c6312866`;
- `overnight/hdmi-blackout-20261027a/owner-playback-observations.jsonl`,
  SHA-256
  `fa079a7ab98d9e569e1f211f6219c31173affb7dc91fe3f4366d9c2e2108420b`;
- `overnight/owner-control-clarifications-20261027.md`.

Primary comparison reports:

- `overnight/ugoos-PROGRAM_A-comparison-20261027.md`, SHA-256
  `eb89f779b776764c7fb3c7287f704d0d95912458fead332b2d1b4683215e676e`;
- `overnight/ugoos-program_b-comparison-20261027.md`, SHA-256
  `4fae490c744558a965ad8619299fb70ab6a86915062e1ab927cba3cf9fbc24cd`;
- `overnight/ugoos-media-comparison-20261027.md`, SHA-256
  `0e5ac173616c7a862426d558d66873bcb63f730c873e571c30be3ff950858da1`;
- `overnight/ugoos-researcher-two-week-controls-20261027.md`, SHA-256
  `eda1643994a9c2b4d5d399f4d2f31f38d9f4e925a5ba714c6ed1ecb5d92a853d`;
- `overnight/finite-onset-logger-20261027g/onset-v5-v6-runtime-audit.md`.

The two photos showing Ugoos title overlays and the earlier screenshot API
outputs are retained context only. They do not prove continuous playback,
physical emission, onset timing, or recovery. No framebuffer, compositor
state, UI return value, or server played flag is promoted to a physical-panel
observation in this comparison.
