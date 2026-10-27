# Qualified detached onset wrapper: receipt framing correction

This directory is an offline-only orchestration successor to
`managed-usb-secondary-logger-onset-qualified`. The native source, DLL, deps,
runtimeconfig, native build script, native tests, and native manifest remain
byte-identical to the independently cleared build.

The only production-command behavior changed from the qualified predecessor is
the `LAUNCH_ACK` record separator. Its Python command template now contains an
actual line feed, matching the successful marker qualifier. This avoids the
common root agent's `QuoteArgument()` doubling a textual backslash before `n`.
`parse_launch()` remains strict and unchanged.

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

The focused regression compiles and runs a harmless local .NET 6 harness whose
`ProcessStartInfo.Arguments` and `QuoteArgument()` body match the common root
agent. It passes the exact production `launch_command()` through that transport
while substituting a marker-only supervisor. The pinned predecessor command is
shown to emit a literal backslash-`n` and to be rejected by the production
parser; the corrected command emits byte `0a` and is accepted. No production
native helper or controller path is invoked by this test.

## Deployment block

Control v3 is protocol-UNKNOWN until its retained execution is reviewed to a
terminal conclusion. Its host-side launch receipt failed after the detached
supervisor handshake completed, so native execution and USB transfers cannot be
excluded. Absence of processes, stage files, or markers does not reveal the
firmware parser phase and is not sufficient proof of clean state. This wrapper
does not perform or authorize a metadata fetch, parser reinitialization, reset,
UI action, or target call.
