# Independent review: managed TCON status read

## Outcome

**CLEAR for one finite, physically coordinated query only**, using the exact
bytes below and the runner's `--run --reviewed --output <new-absolute-path>`
gate.  This clearance does not cover retries, repeated polling, a recovery
action, a setter, or a physical-causality claim.

I performed only offline reads, dry generation, syntax checks, and source/ABI
review.  I did not access the TV, device, network, or root transport.

## Exact reviewed bytes

| artifact | SHA-256 |
| --- | --- |
| `Program.cs` | `a7700d974cc9cf38fe793603bfb8520346ea5546ae92094f6f7e7d49cc000c9a` |
| `run-status-read.py` | `c6e7539c6f413bcd4cfb199d2efbb0474ea041c47e42367cd3f32f27edd54417` |
| `build-manifest.json` | `2044cff99668687ec4956b50a19f97af83bedad34e6ba2746665f535ce223b87` |
| `TconStatusRead.dll` | `b218d8f4a76ed22f081d9e26a8047af1fdffbfe3faa9ebc42898fdbb560f6eab` |
| ABI report | `3812ca30cd846e0aee4e85da0716577c781939972d1836eeca41624b2ef0e3d1` |
| ABI reproducer | `ce08ad96c1e7908274c1b82b8ebbe199783dace74d77fbcc19fb261a3e32270e` |

The manifest contains exactly the reviewed source/project/runner and the
three staged portable build products.  Every manifest digest matches the
local bytes.  The dry plan has ten root commands, maximum 8,083 bytes; all ten
generated commands pass `/bin/sh -n`, and the Python source compiles.  Live
mode is dry by default and requires both `--run` and `--reviewed`; the output
record must be a new absolute path.

## ABI and single-call boundary

The managed helper refuses anything other than little-endian ARM32, a
four-byte pointer, and the 16-byte four-`uint` structure with output at byte
offset four.  It cross-checks libc `getpid()` with raw ARM EABI syscall 20 and
requires UID/EUID zero before opening the device.

The only device sequence in the helper is:

1. one `open("/dev/tztv_tcon", O_RDWR | O_CLOEXEC)`;
2. one `ioctl(fd, 0xc010749f, &payload)` with words
   `[0x1f, 0xa55a5aa5, 0, 0]`; and
3. one `close(fd)` in `finally`.

There is no setter, retry, loop over the ioctl, power/PM call, tracing change,
or recovery interface.  The pinned static ABI report establishes that this
request dispatches operation `0x1f`, copies a 16-byte buffer in and out, and
places the returned word at payload word one.  It also establishes that the
driver's open body is a zero-return stub and that the acquired fops table has
no release callback.  The runner pins the installed ARM32 CLR/CoreLib and the
three relevant installed module files, including exact `qdf_tcon.ko`.

Acceptance requires open/ioctl/close return success, zero captured errno,
unchanged operation and opaque words, output changed from the sentinel, exact
managed field inventory with duplicate fields rejected, helper exit zero,
empty managed stderr, and confirmed private-directory cleanup.  A successful
result is deliberately classified only as `kernel_output_written`.  It does
not prove a controller transaction, current hardware status, physical panel
state, or absence of the QDF debug override.  The proprietary controller read
may be read-to-clear; that unresolved semantic side effect remains explicit.

## Process, staging, and cleanup review

The replacement runner resolves the earlier blocking PID-reuse issue.  A
private `/bin/sh` child writes its own PID and `/proc/<pid>/stat` start ticks,
then waits at most two seconds for a root-owned mode-0600 GO file.  The CLR
cannot start until the parent has verified that the ready PID equals `$!` and
that the current start ticks match.  With no validated handshake, the parent
does not signal the PID and the child exits 83 on its own.  With a validated
handshake, every TERM and KILL is preceded immediately by the PID/start/state
guard.  `wait` is used only to collect the owned child and does not authorize
a signal.  The normal deadline is eight seconds plus a one-second guarded
TERM interval.

The runner stages only the three hash-pinned build products in a random,
root-owned mode-0700 directory; individual files are mode 0600 and are checked
for exact length and hash before execution and again after it.  All root calls
use the pinned client, `--persistent-only`, a 25-second remote timeout, strict
UTF-8 JSON, exact echoed-command binding, authenticated root/model/global-file
invariants, and retained raw responses.  There is no retry.

The create-attempt flag is now set before the CREATE RPC, so a lost response
still enters cleanup.  Cleanup accepts absence, otherwise requires the exact
owner/mode/type, refuses symlinks or unknown entries, removes only the
allowlisted staged/output/handshake files, removes the private directory, and
must be authenticated before the record can be accepted.  A cleanup or
postflight failure forces `accepted: false` and `read_usable: false`.

## Residual limits

The watchdog cannot make the usual impossible guarantee of immediately
terminating a task stuck in uninterruptible kernel sleep; the remote and host
transport timeouts still bound the controlling calls and retain partial raw
responses.  Installed module-file hashes identify the on-disk sources, not a
cryptographic measurement of already-loaded kernel text.  Neither limitation
widens the result classification, and neither is a blocker for this one
ordinary diagnostic query under the stated scope.
