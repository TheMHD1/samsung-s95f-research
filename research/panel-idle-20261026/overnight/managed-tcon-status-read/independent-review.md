# Independent review: managed TCON status read

## Outcome

**COMPLETE for the one deliberate follow-up query.**  The exact reviewed
package below produced accepted result `c` and authenticated cleanup.  No
additional ioctl, retry, polling, recovery action, or setter is cleared by
this review.

The preceding rejected attempt `b` released its GO gate before failing an
empty-file type-description check, so it may have issued a query even though
it retained no managed output.  A follow-up result must preserve that fact.
In particular, a non-sentinel output is new positive kernel output, but a zero
cannot exclude a previously latched value because the status may be
read-to-clear and attempt `b` may have consumed it.

Attempt `c` returned the nonzero word `0x00000010`, so it supplies new positive
evidence even with the uncertainty around `b`.  The result remains bounded to
the QDF raw-status boundary described below; it is not a physical-causality or
component diagnosis.

I performed only offline reads, dry generation, syntax checks, and source/ABI
review.  I did not access the TV, device, network, or root transport.

## Exact reviewed bytes

| artifact | SHA-256 |
| --- | --- |
| `Program.cs` | `a7700d974cc9cf38fe793603bfb8520346ea5546ae92094f6f7e7d49cc000c9a` |
| `run-status-read.py` | `7ca9bf01f3df4524f4f04e561dc4839d0805f4062f665b5c1b9a397adf788c8a` |
| `build-manifest.json` | `3241a1b6106c0447ba33a57b2b223d6ef88fc71daf444b3e4c03b2d880a34943` |
| `TconStatusRead.dll` | `b218d8f4a76ed22f081d9e26a8047af1fdffbfe3faa9ebc42898fdbb560f6eab` |
| ABI report | `3812ca30cd846e0aee4e85da0716577c781939972d1836eeca41624b2ef0e3d1` |
| ABI reproducer | `ce08ad96c1e7908274c1b82b8ebbe199783dace74d77fbcc19fb261a3e32270e` |

The manifest contains exactly the reviewed source/project/runner and the
three staged portable build products.  Every manifest digest matches the
local bytes.  The dry plan has ten root commands, maximum 7,885 bytes; all ten
generated commands pass `/bin/sh -n`, and the Python source compiles.  Live
mode is dry by default and requires both `--run` and `--reviewed`; the output
record must be a new absolute path.

## Accepted actual result `c`

`result-20261026c.json` is 125,361 bytes with SHA-256
`5ccac8a789fd83b3b276b39e6bf33201087c8e4354d580f7bb316075ed04bea6`.
I independently reapplied the exact runner's response validator to each of
its ten retained raw root responses and independently reran its preflight and
execution parsers.  The regenerated dictionaries equal those retained in the
record.  All ten calls authenticate the expected model, UID/EUID zero,
host-assisted persistent root, unchanged-global-files invariant, exact echoed
command, remote exit zero, no timeout, and empty remote/client stderr.

The calls comprise preflight, exclusive private-directory creation, five
staging chunks, one execution, postflight identity/hash verification, and
allowlisted cleanup.  Preflight and execute anchors are on boot
`00000000-0000-4000-8000-000000000000`, uptime 75260.86 and 75262.27.
The helper is ARM32/root, PID 3216/start ticks 18815474; libc and raw EABI PID
agree.  It reports:

| item | retained result |
| --- | --- |
| open | fd 26, return nonnegative, errno 0 |
| request | `0xc010749f` |
| payload before | `0000001f,a55a5aa5,00000000,00000000` |
| ioctl | return 0, errno 0 |
| payload after | `0000001f,00000010,00000000,00000000` |
| close | return 0, errno 0 |
| helper | exit 0, deadline not hit, empty stderr |
| cleanup | `PRIVATE_REMOVED`, accepted true |

The changed sentinel, preserved envelope, success returns, exact source and
ABI guards, postflight, and cleanup satisfy the runner's technical contract.

### Raw QDF log and bit-4 boundary

The later read-only filtered kernel-ring capture is independently
authenticated.  `status-c-filtered-dmesg/client.stdout` is 943 bytes, SHA-256
`d454a04995c5298f31693260f1243e7dcb4f5cf8335312e798b3e99e27b7e9f9`;
its client stderr is empty.  Its complete retained match is:

```text
[75262.252253] [TCON:QDF] QDFTcon_GetErrDetStatus[3216:TconStatusRead.]: ERR DET Status:0x10
```

The timestamp, PID, and helper name align with accepted execution `c`.  The
filtered retained `dmesg` scan found exactly this one matching line and no
`ERR DET Status Debug` form.  Exact QDF control flow logs this raw word before
the optional debug override, so this positively grounds `0x10` at the raw QDF
status boundary.  It does not provide an I2C trace or independently expose
the controller's internal electrical source.  The absence of a retained
debug-form line is evidence against an override in this call, but is stated as
a retained-log fact rather than a global log-completeness claim.

The exact-build AVE decoder tests masks independently.  Its branch at
`0x268d86` labels bit 4 / mask `0x10` with the literal vendor text
`RT Protect`.  That is the complete supported interpretation.  It does not
establish what “RT” expands to, an electrical threshold, a failed component,
or a repair.  The status word is also distinct from the separate one-bit
ERR_DET GPIO that drives the monitor's retry/reset decision.  This result has
no aligned fresh GPIO assertion and does not by itself show that RT Protect
caused the current physical blackout.

The earlier filtered vlog query scanned uptime 75260--75264 and found zero
matching vlog records; its raw stdout is SHA-256
`36bb2d056a1ce92d03d0e0c53c72333ae74a6d7fa3b2e2217bcb4d92cd36eaac`.
That source's lack of a match is not negative evidence against the later
same-PID kernel-ring line and is not used to infer transport absence.

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

### Rejected preflight predecessor

The prior reviewed runner/manifest (`c6e7539c...` / `2044cff9...`) and its
review were preserved read-only under `rejected-preflight-a`.  Its one actual
run is also preserved as `result-20261026a.json`, SHA-256
`45a5771625ed621fcd6a69313380a93e15a421dc9bea118423dab63ab55e9970`.
That record has exactly one authenticated preflight command, remote exit zero,
no timeout, and empty stderr, but the target emitted literal `\\n` text rather
than line feeds.  Host parsing rejected it before private-directory creation,
staging, helper launch, device open, or ioctl.  It remains `accepted: false`
and `read_usable: false`; it is not a status-query result.

The corrected runner replaces every newline-dependent target `printf` in the
preflight, stat helper, child-ready tuple, helper status, and execute anchors
with `echo`.  The only remaining target `printf` is the deliberately
newline-free `printf %s '<base64>'` staging operation.  Thus this correction
does not change the managed ABI or add an operation.

### Rejected file-guard predecessor

The next retained attempt, `result-20261026b.json`, is 100,217 bytes with
SHA-256
`4dbf85689e3d81ca71c4e401f3a1e7c06a2d220337e00a49be5ea39902df9116`.
It authenticated and completed preflight, private-directory creation, and all
five staging chunks.  Execute then exited one with empty shell stdout/stderr,
and the initial cleanup hit the same guard.  The record correctly remains
`accepted: false`, `read_usable: false`.

Authenticated inspection showed exact staged hashes, ready tuple
`896 18751314`, and root-owned mode-0600 zero-byte `helper.go`,
`managed.stdout`, and `managed.stderr`.  The target labels an empty regular
file `regular empty file`; the rejected runner required literal
`regular file`.  Since GO existed before that post-creation check, the child
could briefly have exec'd CLR before the guarded EXIT trap stopped it.  Empty
managed output demonstrates no call and no kernel result, but cannot prove a
call never occurred.  Attempt `b` is therefore a potentially consumed query,
not a negative status result.

The authenticated corrective cleanup verified that the original PID/start
generation and any matching staged-DLL command line were absent, then checked
the exact allowlist, numeric ownership/modes, DLL hash, and zero output sizes.
Its sole command returned zero with `ORIGINAL_CHILD_NOT_LIVE` and
`PRIVATE_REMOVED`; raw stdout SHA-256 is
`078866b2f34ec66f296e13dfd036723ede9df6c7e8c1c2b4c5a4b45ec8b58f22`
and client stderr is empty.

The presently cleared runner fixes only this target-compatibility defect:
regular files are established by `test -f`, symlink refusal, and exact numeric
UID/GID/mode, while sizes and hashes remain checked where applicable.  It no
longer depends on localized/content-sensitive `%F` prose.  An offline empty
file whose `%F` is `regular empty file` passes the corrected guard; syntax,
size, mode, and symlink negatives remain fail-closed.

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
