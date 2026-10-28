# Recovery case study

The observed recovery sequence was: select the populated Apps tab using ordinary local keys, verify its cached selection, issue one stock display-controller operation 41 / mode 2, then obtain a physical visibility report. Four documented owner-confirmed recoveries were retained under BH, BI, BU and BW. This is a case-specific recovery observation, not a permanent prevention result.

A reset while ForYou was selected did not establish visible recovery. Cached selection, keyboard focus, a screenshot, `lcdon`, `screen=1`, and ioctl success are different facts. The optical result requires a person or suitable optical measurement.

The [retained runbook](../research/RECOVER-PANEL.md) and [quickpath implementation](../research/panel-idle-20261026/overnight/recovery-quickpath-20261027bv/recover.py) document exact preconditions, one-shot behavior and cleanup. The public copies have redacted boot identity, network addresses and local paths. They are review material; their placeholders are not a deployable configuration. Adapt identity checks to a separately verified target rather than weakening them. The observer itself does not perform a reset.

The investigation used a physically damaged panel. No conclusion about other panels or the safety of repeated resets follows from these observations. No firmware patch, reset loop, persistent global change, or universal remedy is claimed.


## One source-instrumented MODE2 observation

The [HF projection](firmware-controller-20261028.md#actual-hf-observation-with-rejected-outcomes-retained) records one accepted stock helper, positive source-associated normal-tail reports, a positive USB lifecycle and a later complete clean software read. The helper terminal itself is only kernel-return-zero. This particular attempt does not prove all-domain reset, image0 startup, instruction reload, universal RAM clearing or physical recovery. A separate later CEC standby request is not established as RTP relapse.
