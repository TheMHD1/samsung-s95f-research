# Samsung S95F panel-blackout reverse engineering

This project investigates content-dependent loss of physical panel output on
an owner-controlled Samsung S95F. The objective is to prevent the blackouts,
keep the TV usable, and preserve enough evidence and procedure for another
engineer to continue. **Permanent prevention has not been demonstrated.**

## Start here

| Need | Entry point |
| --- | --- |
| Current diagnosis, newest results and outstanding gaps | [CURRENT-INVESTIGATION.md](CURRENT-INVESTIGATION.md) |
| Demonstrated Apps-selected recovery | [RECOVER-PANEL.md](RECOVER-PANEL.md) |
| Full trigger/recovery confirmation | [BW findings](panel-idle-20261026/overnight/full-confirmation-20261027bw/findings.md) |
| Detailed controller fault model | [Working model](panel-idle-20261026/overnight/ordinary-fault-model-20261027.md) |
| External source research and compatibility review | [Research project](research-20261027-external/README.md) |
| Earlier driver/kernel evidence map | [Historical RE index](panel-idle-20261026/overnight/RE-INDEX.md) |
| Photographed physical topology | [Board map](panel-idle-20261026/tcon-research/owner-photo-board-map.md) |

The current investigation supersedes pending-work statements in historical
reports. Frozen captures, rejected experiments and corrected interpretations
remain preserved; a successful later test does not make an earlier rejected
record valid.

## Target and demonstrated behavior

The software-reported TV is `QN77S95FAFXZC`; the panel label is
`CY-AF077FLLV2H`. A photographed board has a different regional model marking,
`QN77S95FAFXZA`; it is recorded separately rather than silently reconciled.
The saved running-build-matched kernel is Linux `5.4.261`. Native kernel code,
compatibility userspace, managed assemblies and external controller firmware
are separate analysis targets.

The owner reports a thumb-sized impact-damaged black region at the bottom
edge and a vertical dark line. Sparse For You/Live pages and some fullscreen
videos can produce persistent black while audio and Linux continue. Populated
Apps and the same video playing behind Ugoos Home can remain visible. Other
titles normally play successfully. Rare brief recovering interruptions are
tracked separately from the persistent-black case.

In BW, normal keys selected For You and the owner confirmed black. Two Right
keys selected Apps while black. One stock controller operation 41/mode 2 then
restored visible Apps, confirmed by the owner. A kernel status query changed
from `0x10` to `0`, but that query is not a raw MCU RT read or light sensor.

## Evidence conventions

- **Target observation:** captured from this TV with provenance and limitations.
- **Owner observation:** physical visibility/audio feedback, preserved separately
  from software acknowledgements and with timing uncertainty.
- **Source result:** a code path reconstructed from a pinned binary or source.
- **Locally reproduced:** a result independently checked on retained artifacts;
  it is not automatically proof of executing live code.
- **External report:** another project's claim, requiring compatibility and
  implementation review before use on this TV.
- **Hypothesis/open gap:** an explanation or missing edge without sufficient proof.

A compositor frame, selected UI tab, successful ioctl or `lcdon` value does
not prove emitted light. A getter can still perform I2C or acknowledge state.
Cross-model addresses, connector pinouts and flashing procedures require
their own target binding. Public source code is reviewed as evidence; it is
not executed merely because a README recommends it.

## Layout and handoff

`panel-idle-20261026/` contains the historical investigation and per-experiment
artifacts. `root-access/` and `live-cast/` retain the source and tooling used
for access. `research-20261027-external/` is the new source registry, comparison
reports and work plan. Dates identify acquisition phases rather than a claim
that every file describes the latest state.

Keep new experiments in fresh directories with intent, exact source/input
identities, commands, stdout/stderr, cleanup, outcome and limitations. Keep
physical feedback separate from helper results. Add a manifest after writers
finish, and verify it by rereading the files. Update the current entry point
without overwriting frozen history.

This workspace includes private access material and raw device responses.
A handoff should use the reports and intentionally selected artifacts; do
not publish the entire directory as a repository dump.
