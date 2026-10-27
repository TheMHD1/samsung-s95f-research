# Overlay/fullscreen paired-control evidence note

Recorded 2026-10-27 UTC. This is documentation only. No TV, root, media,
playback, helper, firmware, or diagnostic action was made while recording it.

## Owner observations carried forward

- A populated, full Apps page has repeatedly been reported visible/stable long
  enough to serve as the practical control context.
- Entering sparse/empty **For You** or **Live** has repeatedly been reported to
  take the physical panel black rapidly while the TV/audio can remain active.
  Blind navigation back to Apps is not a reliable recovery.
- Full-screen video has often been reported as more stable than sparse native
  navigation, but this is not universal: the owner separately reproduced
  persistent black with PROGRAM_04 and with the offered PROGRAM_B
  diagnostic run.
- Latest state: the owner deliberately left the TV black after For You and is
  asleep; there is no current visual feedback, timing, or recovery report.

The evidence does not identify a particular overlay, frame, application, or
source plane as causal. A later parent re-review of the two relevant UI photos
reads the following visible labels: `1x01. PROGRAM_B EPISODE_REDACTED PROGRAM_LABEL` /
`PROGRAM_B`, with featured `PROGRAM_15`; and `1x01. PROGRAM_LABEL` /
`PROGRAM_04`, with featured `PROGRAM_A's Farm 5x08.PROGRAM_16`. These are
parent-verified still-photo labels, not a continuous decode, timing anchor,
or proof that either featured tile/current-playing line was the live source at
the later black state.

## Photo review

The ten supplied photos were re-opened visually. They show the rear chassis,
main/control boards and ribbon links, speaker assemblies, the green panel-side
board, plus two close images of the visible panel defect. The panel photos
show a narrow, dark vertical line reaching upward from an irregular local dark
area. They corroborate the owner's pre-existing physical-damage description;
they do not show the live blackout, prove board failure, prove the affected
component, or establish whether the visible mark initiates a full-panel event.

| retained photo | SHA-256 |
| --- | --- |
| f1004d7049ba45048b2e0f9d0e9f5bf9.jpg | 7a8eb6c6bae0afce4190502bf232026d7029825c44b91aad5b52bd96eea0361b |
| 08a640cb477f4ac7a0bfa581d35ca5e5.jpg | 285e970b00d1e41a2aa8f056234377886b1b01c603112db46706a858af65798d |
| f1964de7072f4b0bbeefe9ae46833769.jpg | cb7f2e9932f1b46d26b4983ccba7c45938cec925e9d7c6375d4838c660245154 |
| 08307a8da9e94c4282e21003a4ca7a42.jpg | bc80dd2da9669d32a985033d8b079637f90b587ae4547f6bc19b2190b16c57cd |
| 08c46f21fb3547788e73ef9e1b9dd8d9.jpg | 4dee84e1653352b5360f2ab5b887cc55adfbbb6ec85c792788b03910a21bf3e7 |
| 14edfce10c7840b7b4a2831fe304aeec.jpg | bcd67f9fac559a5cd11062071e0bfc1a9cee49e637e38076f8a52163faf5a0f5 |
| 0b11312318f84576b7d543f902a42146.jpg | 7a15269051503b224e41282c595534fe3903c5dec24d15db65fbdb990c4e24c6 |
| 3954092b14e643669c22b1a728378269.jpg | 1fb848d36b247a9c2d5aedf4e599dae967306eb0c57b049d5d841c874b1d1cc4 |
| ff5e6f2ecbe8450095379a9311f2b529.jpg | 5137ca4f5cd2e61ec661d3e0c67be9807ad7c2a84416c3435539b9437fd2f5c0 |
| c4203dbaa5f24283868583dec537f0ee.jpg | d047ba31358effdfe47063fea94762c5e581a93d380adcc5e36e688e723af0ca |

## Investigation links and limits

This note complements the [two-week content controls](ugoos-researcher-two-week-controls-20261027.md), the [paired-restart record](paired-restart-progress-20261027.md), the [causal map](diagnostic-causal-map-20261027.md), helper independent reviews, the long observer/design documents, and the firmware [RTP scan](../tcon-research/qd-rtp-scan-invocation.md). These cross-links do not promote any helper/design/research result into an installed mitigation.

No helper or fix is installed or physically verified. A future paired control
needs contemporaneous owner-visible annotation (including exact label if
visible), source/app identity, and retained trace boundaries before it can
separate sparse UI, overlay, full-screen scene, or source transition.
