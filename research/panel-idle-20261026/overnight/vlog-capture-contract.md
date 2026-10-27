# Installed vlog time-window and format contract

## Actual read-only observations

`vlogutil-help-discovery-20261026T145901Z.json` records the installed
`/usr/bin/vlogutil` usage. It defines `-t <seconds>` as logs written during
the last seconds, `-v kerneltime`, unfiltered default `*:V`, and streaming
`-s` with absolute monotonic `--start-from` / `--end-to` or relative `now`.
The help was bounded through head120, so its individual exit status was not
captured; the actual complete usage text was retained. No display API ran.

A separate unfiltered `vlogutil -v kerneltime -t 2` is retained in
`vlogutil-kerneltime-format-20261026T150016Z.json`. On the same recorded boot:

| Field | Actual value |
| --- | --- |
| Query-start uptime |48423.82 |
| Actual first/last log timestamps |48421.831 /48423.827 |
| Actual log span |1.996seconds |
| Parsed actual log rows / reported count |6327 /6327 |
| Entire shell stdout |936079bytes,6431lines including header/footer/multiline text |
| Dump footer time / post-query uptime |48426.669 /48426.70 |
| Leading writer |PID660,5097 of6327 timestamped records |
| Header setting |`vlog_size(32)`, unit/retention not independently established |

The dump takes about2.84seconds after query start even for that last2second
window. This is throughput/format evidence, not a physical blackout capture.
It contains repeated QD_TCON_OFF1 history messages at48422.302 and48423.302;
the old visible/black pair already shows why that latch alone is not a new
power-off event. The present physical picture remains unobserved.

## Parser and coverage requirements

An actual row is shaped like:

```text
    tcon-monitor: 48422.302 E/AVE     (P  706, T 1019): ...
```

The timestamp follows the thread-name colon and precedes severity/tag. It is
**not** the footer's bracketed timestamp. A parser matching
`^.*?:\s*(\d+\.\d+)\s+[VDIWEF]/` finds exactly6327 rows in this fixture,
matching the tool's reported count. Multiline continuations are retained as
source but not assigned invented timestamps or separate log-event counts.

Help establishes the intended last-seconds contract; actual first/last record
times establish retained coverage. A successful command is not proof that the
finite history contains an entire future90second capture. At this observed
rate, a long unfiltered artifact can be tens of MiB; plan bounded storage and
throughput, and do not assume the unit/retention of header32. A concurrent
bounded stream can avoid relying solely on post-capture history, but must
still prove interval coverage, completion, size/hash and absence of loss before
supporting an absence claim. Over-limit, truncated or uncovered artifacts are
retained as incomplete. No filters may be silently treated as global absence.
