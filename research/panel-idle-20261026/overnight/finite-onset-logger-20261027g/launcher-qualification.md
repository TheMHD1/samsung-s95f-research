# Detached launcher qualification

`qualify-launcher.py` isolates the root-agent background-launch boundary from
the USB logger. It is dry by default and has no managed binary, USB access,
device node, UI request, signal, retry, or fallback root bootstrap. Its only
target-side workload is a fixed shell marker that records its process identity,
boot ID, and uptime, sleeps for three seconds, records completion, and exits.
Every result fixes `target_device_operations` to zero and
`physical_picture_observed` to false.

Execution requires both a fresh absolute output directory and the reviewed
SHA-256 of the exact Python source:

```text
python3 qualify-launcher.py --execute \
  --script-sha256 REVIEWED_SOURCE_SHA256 \
  --output /absolute/new/output
```

The wrapper pins the reviewed root adapter at SHA-256
`bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a`
and the parent guard implementation at SHA-256
`eeb852c8e1b9a0d2611abc17e853ad2ee834f4e42712b2810bf8309eda5e59ca`.
Root commands and responses remain within the adapter's 8 KiB and 64 KiB
bounds.

## Target contract

Each execution uses a unique `/tmp/researcher-launch-qual-<32 hex>` directory,
owned by root with mode 0700. The marker source and all seven terminal files
are regular root-owned mode-0600 files:

- `marker.sh`
- `launcher.stdout`
- `launcher.stderr`
- `marker.pid`
- `marker.stat`
- `marker.start`
- `marker.done`

The marker runs with `set -eu`, writes PID, saved `/proc/PID/stat`, and start
metadata through same-directory temporary files followed by rename, sleeps
three seconds, then atomically publishes done metadata. It invokes no native
helper and performs no hardware or UI operation.

The launch follows the retained successful collector shape. A subshell closes
every numeric descriptor above 2, then executes `nohup`, `setsid -f`, and stock
`/bin/sh`; stdin is `/dev/null` and stdout/stderr are private files. `$!` is
retained only as a dispatch PID. In the same authenticated root request, the
wrapper waits at most one second for the marker handshake, binds the marker PID
and start ticks, requires `PID == process group == session`, waits 200 ms, and
revalidates the live identity before acknowledging launch.

After a local 3.4-second wait, one bounded root request requires the exact
seven-file inventory, fetches every artifact, and waits at most one additional
second for the marker PID to disappear. Host validation binds both marker
records to one boot, requires a 2.5-to-10-second uptime delta, validates the
saved process identity, and requires empty launcher stdout and stderr.

Only after terminal validation and durable host artifact/hash output does an
exact-inventory cleanup request remove the seven known files and private
directory. Any ambiguous launch, handshake, fetch, validation, or cleanup
failure is recorded without retry, signal, or speculative cleanup; the private
stage is retained for review.

This qualifier can establish that the detached shell-launch mechanism works.
It cannot qualify the USB protocol, native logger, physical panel, or any UI
transition. The retained D7 control-v2 attempt remains protocol-unresolved.
