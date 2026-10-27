# Qualified detached onset wrapper

This directory is an offline-only orchestration successor to
`managed-usb-secondary-logger-onset`. The native source, DLL, deps,
runtimeconfig, native build script, native tests, and native manifest remain
byte-identical to the independently cleared build. The new wrapper changes only
how its finite native process is detached, identified, diagnosed, and cleaned.

The staged mode-0600 supervisor is read as data and passed to stock `/bin/sh -c`.
Before that exec, a private subshell closes every inherited numeric descriptor
above 2, invokes `nohup`, and uses `setsid -f`. `$!` is retained only as a
dispatch receipt. The supervisor runs `set -eu` and atomically publishes its
PID, full proc stat, boot ID, and uptime before creating the native child. The
same launch request binds the actual supervisor's PID, process group, session,
and start ticks, then repeats the live identity check after 200 ms.

Launcher stdout and stderr are private bounded artifacts. Accepted completion
requires both to be empty, preserves all existing native READY/final outcome
and urgent-restore checks, and permits exact cleanup only after terminal host
retention. A timeout, malformed handshake, identity change, missing completion,
or diagnostic anomaly receives no retry, signal, fetch-after-ambiguity, or
cleanup.

The wrapper is dry by default and its offline build/test path performs zero
target operations. No TV or USB execution was performed while producing this
directory.

## Deployment block

The earlier control-v2 attempt remains protocol-unresolved. Absence of its old
processes, stage files, or markers is necessary but does not reveal the firmware
parser phase and is not sufficient proof of clean state. Deployment requires
either closed-world no-transfer lineage from the prior run (for example D6 or
an already-running complete USB trace) or an independently established
controller-parser reinitialization. This wrapper does not perform or authorize
that reinitialization, a reset, a UI action, or any target call.
