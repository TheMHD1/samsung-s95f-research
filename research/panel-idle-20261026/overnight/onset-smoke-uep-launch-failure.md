# First live onset smoke: unsigned-script launch rejection

Outcome: **incomplete, unclassified; no physical observation or repair**.
One explicitly unobserved five-second smoke was attempted with reviewed
observer source SHA
`51e00a387036f1a1be2366b230814e213aac9463afa86ede4b2de3163a52bea7`
and tests SHA
`f487b4d4bf75fe81a35d876c2182fc09bcfa6bd9c73778fc7d12802a098fc2a8`.
Both are archived with four generated shells in
`onset-review-archives/51e00a387036f1a1-f487b4d4bf75/`.
The predecessor `0725e9...` remains separately archived and was never cleared.

## Executed action and retained evidence

The reviewed source passed 27 offline fixtures, including actual host-owned
setsid scheduling and leader-exit/TERM-ignoring-child cleanup tests. A separate
reviewer cleared this exact revision for one bounded passive smoke, without
claiming full-duration capacity or physical state.

At host 16:17:21.367–16:17:23.204 UTC, the tool staged 16,974 shell-data bytes
in five chunks and verified the expected size/hash. The staged data hash was
`26434450775293afc3a312f2aaff8756fe8fe3b372eb906867edef8416e489c9`.
The pre-capture anchor recorded TV UTC 1793031443 and uptime 53052.66, with
scheduled target uptime 53064.66 and 1.136 seconds mapping uncertainty.
Launch failed before that target. No trace, sampler, vlog or display-artifact
sidecars were produced; the collector stderr was retained before cleanup.

The exact useful stderr line, excluding ANSI colouring, is:

```text
[uep][bash] the file is NOT signed!! : /tmp/researcher-observed-onset-stage-20261026/smoke-20261026t1620/capture.sh
```

This is a specific installed-shell signature-policy rejection of the staged
script-file launch. It is not a sample-parser, trace-loss, factory, panel
failure or physical-blackout result. The generated collector body did not
produce any acquisition sidecar. The software/panel's current physical state
remains unobserved.

Retained directory: [smoke-20261026t1620.onset](smoke-20261026t1620.onset/).
It contains the exact host `remote.sh`, stage metadata, empty observer input,
partial collector stdout/stderr, record, quiesce and cleanup responses.
The outer CLI stdout/stderr are also retained in the adjacent `.driver.*`
files. This revision did not save the failed launch's complete root response;
that provenance gap must be corrected before another attempt.

## Cleanup and classification

The saved root cleanup response has uid/euid0, exit0, timed_out=false,
empty stderr and stdout `0` then `CLEAN`. The source's residue checks require
the exact private trace instance, output directory, stage directory and
expiry-log path to be absent before CLEAN. The record reports quiesce and
cleanup verified. No acquisition sidecars remained to salvage.

`accepted=false`, `technical_capture_complete=false`,
`diagnostic_eligible=false`, and `absence_claim_supported=false` are retained.
No display/factory/sensing/power control or execution-policy change ran.
The cleanup's global tracing read is0; no global trace-setting write appears
in this attempt's source or retained cleanup command. This is not a full
before/after global-state measurement because the collector never acquired
its baseline metadata.

## Next concrete correction

The established root agent already executes command strings through installed
`/bin/sh -c`. Adapt the collector launcher to pass the exact verified staged
data as a command argument instead of asking the shell to execute the unsigned
file path. Preserve its target positional argument, private-data hash checks,
FD/process-group ownership and controller command-length bound. This requires
no security-policy or firmware change. Runtime expansion and the installed
shell's acceptance remain to be verified by a separately reviewed attempt.

No automatic retry ran. A revised source must receive a new archive and
review; preserve this failed result rather than relabel it as a capture.
