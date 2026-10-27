# Runtime audit: rejected MODE2 paired sequence

Recorded 2026-10-27 UTC from retained artifacts only. No TV, root, media,
network, controller, or display call was made for this audit. The collector
rejection is preserved; this report does not reinterpret it as an accepted
physical experiment.

## Outcome

The orchestrator correctly rejected the sequence as a technically unusable
passive bracket:

```text
capture exit code                 = 1
collector accepted                = false
collector technical_capture_complete = false
collector cleanup_verified        = true
outcome accepted_sequence         = false
outcome sequence_completed        = true
```

The rejection was raised by the retained collector parser as
`ValueError: duplicate AVOC ioctl enter`. It is a real inconsistency in the
saved raw-syscall record under the parser's one-enter/one-exit-per-TID
assumption. It does **not** establish that `avocd` restarted, that MODE2
caused a restart, or that a display/panel event occurred.

## Helper sequence actually recorded

All five helper records report `accepted: true`, `cleanup_confirmed: true`,
and the same retained Linux boot ID. Their managed classifications remain
narrow kernel/line-read results, not physical proof.

| Step | Preflight uptime | Execute uptime | Result |
| --- | ---: | ---: | --- |
| pre-pin | 94416.18 | 94417.71 | GPIO input value `1` |
| fixed MODE2 | 94418.86 | 94422.87 | operation `41`, mode `2`, kernel return `0`; action acknowledgement is explicitly false |
| post-status | 94423.68 | 94425.24 | kernel output `0x00000000`; controller transaction/hardware truth not proved by this helper |
| post-pin | 94426.13 | 94427.94 | GPIO input value `0` |
| post-duty | 94428.71 | 94430.42 | kernel output `207` (`0x000000cf`); no physical-brightness inference |

The passive capture's retained target/start/end are `94414.110 / 94414.11 /
94474.17`; every recorded helper execute uptime is before that end. Each saved
execute command includes the reviewed private-trace-on and `uptime + 15 <
94474.110` gate. In particular the actual MODE2 execute transport began at
03:46:48.081 UTC, ended at 03:46:51.083 UTC, and its saved command is 8,066
bytes. These facts establish the bounded orchestration sequence, not what the
TV hardware did with the mode request.

The two readiness observations also passed before helper execution:

| Observation | Uptime | Retained condition |
| --- | ---: | --- |
| before pre-pin | 94415.76 | private `tracing_on=1`; exactly one START and no END |
| before MODE2 | 94418.37 | same condition |

## Later independent state check (outside the rejected bracket)

About 302 seconds after the MODE2 execute timestamp, separately retained
one-shot helpers completed on the **same boot ID**:

| Check | Execute uptime | Narrow result |
| --- | ---: | --- |
| late status | 94724.79 | kernel output `0x00000000` |
| late pin | 94726.97 | GPIO input value `0` |

The late status helper's managed PID is `32491`; the late pin helper's PID is
`322`. The lower PID is consistent with ordinary PID reuse/wrap and is not a
boot identity: both records independently report the unchanged boot UUID.
The paired late-state read at uptime `94815.06` also records global tracing
off and absence of this trial's private trace instance, output directory, and
stage directory. Its retained kernel rows show status zero at both
`94425.166538` and `94724.688087`.

These are valid, individually accepted helper records, but they are outside
the failed 60-second capture and cannot repair its rejected paired-capture
classification or establish a physical recovery.

## Duplicate-enter dissection

The raw trace has no reported ring overwrite:
`entries-in-buffer/entries-written: 104917/104917`. Both syscall tracepoints
were enabled with the same ID-54 and captured-TID predicate, including TID
`1011`, and trace time is monotonic. The parser therefore did not reject a
syntactic malformed row or an unrelated task.

The first invalid pairing is this same-TID sequence in the physical window:

```text
line 4532  94415.763058  AVEMonMain-1011 (TGID 706)
           sys_enter NR 54 (21, c010643a, f4efe4ac, 170d0, 0, f4efe4ac)
line 4538  94415.863044  AVEMonMain-1011 (TGID 706)
           sys_enter NR 54 (21, c010643a, f4efe4ac, 170d0, 0, f4efe4ac)
line 4540  94415.867624  AVEMonMain-1011 (TGID 706)
           sys_exit  NR 54 = 0
```

The parser retains the first enter as pending, sees the second enter for that
same TID before an exit, and raises exactly at its
`require(item["pid"] not in pending, "duplicate AVOC ioctl enter")` guard.
The sequence is 100 ms between the two enters and 4.58 ms from the second
enter to the visible zero exit. It is **not physically possible for one user
thread to execute two syscalls concurrently**; the raw record therefore lacks
the simple one-entry/one-return representation the parser requires.

Two explanations remain consistent with these bytes:

1. a kernel raw-syscall tracing/restart representation in which a blocked or
   restartable syscall gets a second `sys_enter` but no separately visible
   intermediate `sys_exit`; or
2. a missing/misassociated `sys_exit` trace record despite the collector's
   no-overwrite accounting and matching enter/exit filters.

The retained artifacts cannot distinguish those explanations. The first is a
possible restart **representation**, not evidence of a process restart. The
second is a trace-pair completeness gap, not a license to invent the missing
return. The existing parser correctly fails closed rather than silently pairing
the last exit with one of two incompatible enters.

## What this rules out, and what it does not

* The duplicate occurred at 94415.763/94415.863, after capture start but
  **before** pre-pin execution (94417.71) and MODE2 execution (94422.87).
  It therefore cannot be an effect of the fixed MODE2 execute request.
* The start/pre-roll/end TID listings retain TID 1011 and the rest of the
  `avocd` thread set. The trace has no relevant tracked AVOC
  `sched_process_exit`/replacement evidence. This weighs against an `avocd`
  daemon or AVEMonMain thread restart during the bracket; it does not prove no
  untraced subsystem reset occurred.
* The ordinary recurring AVEMonMain request has raw arguments
  `0x21, 0xc010643a, ...`.  The parser correctly reads those register tokens
  as hexadecimal: FD `0x21` is decimal 33, which the retained FD snapshots
  map to `/dev/dri/card0` at start, pre-roll, and end.  The request number is
  consistent with a DRM wait-vblank encoding, but this report does not rely on
  that name for any causal inference. Its normal-looking enter/exit pairs
  resume after the anomaly; that does not identify the missing first return or
  establish display health.
* The event is not an I2C transport conclusion; the separate I2C audit owns
  that question.

## Provenance

| Artifact | SHA-256 |
| --- | --- |
| `stock-mode2-trial/pre-pin.json` | `1ee01f60e24f72ecb13e147d642c9fda472fa346b94440e859d3c26bfde404a8` |
| `stock-mode2-trial/mode2.json` | `5571bc79ca021113f76428969f8f6d2e3ebf18224438e5cd168cfb5a9ec315d2` |
| `stock-mode2-trial/post-status.json` | `e838bf5eeefbe58831a5577b57dee52288c7e45dc8bf0207acd1071b80f55500` |
| `stock-mode2-trial/post-pin.json` | `8bea346a446cbeff5bb483e9301d595ef54ade8436b6455544e6e5b09fc5c20e` |
| `stock-mode2-trial/post-duty.json` | `b3a2e6939efe8ff8ca4198c4bab6874b51e7ae15288463604371327ecaebf299` |
| `stock-mode2-trial/outcome.json` | `647723f1950603a1423f5ded97e1d5e74bfc06fc7d65ce0b29573bc43ee505e2` |
| `sleep-mode2-20261027a.onset/record.json` | `357e7f517ff019c1f185de4233a87f1a8ccd44e9716f5ccdf9e82e003eb86df0` |
| `sleep-mode2-20261027a.onset/trace` | `5ade657ba4c253e70cbb26eab2431a0a8bde2acd73f85386d9e7d1fce78633ab` |
| `sleep-mode2-20261027a.onset/meta.txt` | `64cf663811e29e7a2ff8da0ffec0d4643a5140fa734604e5008eff7e173355d5` |
| `sleep-mode2-20261027a.onset/fds.txt` | `fe6cea5257805af725f62bb944f3db14151a584b27b8596a1140547f0e95ec6b` |
| `stock-mode2-trial/late-status.json` | `130c780f7bb69f5e9028f7b0800d692072930c0c2bbeae17a43801a31a657edc` |
| `stock-mode2-trial/late-pin.json` | `267acc2b16fc2bc4480b26d04d2af667b5f4a52290b5615d7a5025dd8a49b203` |
| `stock-mode2-trial/late-state.stdout` | `f834c24924bd00f0c41420b730912a83fe5e1aa7d28f6b98c1e60c8199de721c` |

