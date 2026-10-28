# Read-only review: root timeout and future section-stream transport

Reviewed 2026-10-28 UTC. **The unchanged active foreground path supports a maximum120-second requested execution budget. Its underlying root-agent protocol and target payload support a300,000ms command budget, but both the access CLI and persistent daemon independently refuse requests above120seconds.** Increasing only the45/75-second root-with-margin constants cannot overcome those limits.

For a section stream that can exceed120seconds, the smallest additive route preserving the existing controller/session is a one-launch, separately bounded background job with short authenticated status requests and a dedicated private bulk channel. A foreground extension to at most300seconds instead requires coordinated changes to both host bounds and a controlled daemon lifecycle change; it is not an adapter-only change against the already-running daemon. Above300seconds, foreground execution also requires a new target root-agent payload/protocol qualification. No existing source was changed and no TV/root/network operation was performed by this review.

## Actual source limits

| Layer | Current bound and behavior |
| --- | --- |
| `managed-ui-tab-launch/root-with-margin.py` |Fixed remote45seconds, outer subprocess75seconds; command8192bytes, combined retained response65536bytes. Calls the existing access CLI with `--persistent-only`. |
| `root-access/s95f-access.py` |CLI integer range1..120; nonblocking owner flock; firewall/route/model/developer-host/build/root checks. Persistent request uses an owner Unix socket; the execution request is sent once. Its response socket timeout is requested execution +15seconds and its response line limit4MiB. |
| `root-access/persistent-root.py` |Owner Unix peer check; command8192bytes; independently requires integer timeout1..120. `Controller.gate` serializes command execution with keepalive/acquire/release. Its direct async client waits timeout+10seconds. |
| Python `RootAgentConnection.execute` |Encodes100..300000ms; command up to65536bytes at this lower layer, but existing callers retain8192. `_request_lock` serializes authenticated sequence-numbered EXEC/RESULT frames. Host response waits requested timeout+2seconds. Any exception/cancellation after submission invalidates the connection, rather than resubmitting. |
| Target `SamsungTvRootAgent.cs` |Independently rejects EXEC timeouts outside100..300000ms. Uses `/usr/bin/setsid /bin/sh -c ...`, then `WaitForExit(timeout)`. On timeout, kills the process group (fallback process kill) and returns exit124/timed_out when final capture completes. |
| Root data/output framing |Target retains at most1MiB per stdout/stderr stream and marks truncation. Python authenticated line/file transfers have4MiB limits; the additive root wrapper accepts only64KiB combined output. A roughly1.455GB section cannot be transported through command output or the existing READFILE path. |

The execution timeout is a process-wait budget, not a proven end-to-end wall-clock bound. After kill the target calls unbounded `WaitForExit()` and `Task.WaitAll(output,error)`. A detached descendant that inherits captured stdout/stderr can hold those readers open after the launcher exits. The host receive timeout will invalidate a stalled connection, but that does not prove the remote worker stopped or its TA resources rolled back. Every detached launcher must redirect/close stdin, stdout and stderr before returning, and its long-running worker needs its own finite lifetime and per-I/O bounds.

Four actual Python protocol tests were executed against in-memory readers/writers with synthetic HMAC secret/nonce, without sockets:120 and300seconds encode/complete correctly;300001ms and99ms reject before any frame is submitted. These validate the lower protocol boundary only; they do not override the two120-second host policy checks or qualify a long target run.

## Additive options and recommended contract

### Foreground extension when a measured budget fits below300seconds

A new hash-pinned access/controller revision could expose a separately bounded long-exec capability up to300seconds while preserving the current default120. It must change both the access argument validation and daemon handler validation, preserve owner peer/identity/firewall/route/build/boot checks, retain the same gate/HMAC/sequence/no-retry behavior, and account for the active daemon actually running the revised source. Merely copying the client or sending a raw Unix request still reaches the old daemon's120-second check.

The existing target agent could then remain unchanged. Native worker lifetime must be below the remote execution budget to leave normal cleanup time. The access socket timeout and outer host timeout must also cover preflight/status/build requests, dispatch, execution, receipt retention and cleanup; choosing only `remote+small_margin` ignores those other waits. No empirical throughput measurement establishes that the full platform stream fits in300seconds. A configured deadline must not silently grow in response to slow output, and a timed-out or ambiguous dispatch must not be resubmitted.

A daemon restart/reacquisition is a real access lifecycle change. This report does not perform or prescribe it as a prerequisite for all stream development. The active session need not be disturbed to implement and review the background route below.

### One bounded background job using the unchanged controller

A new adapter can leave both120-second host limits and the target agent unchanged. Its root calls remain short fixed launch/status/terminal-check operations; only the separately reviewed worker persists for the longer finite streaming lifetime. The bulk section bytes use a distinct bounded authenticated/confidential channel and never root stdout.

The concrete minimum contract is:

1. Hash-pin the unchanged access module, persistent-controller/agent source lineage, new launcher/worker, immutable section plan and all stage inputs. Require the existing ready persistent connection and the same model/build/route/firewall/boot checks; never bootstrap/fallback from this job adapter.
2. Acquire the existing global owner access flock once for the entire job, including launch, bulk exchange, terminal classification and known cleanup. **Do not then spawn `s95f-access.py` for each poll:** each child opens and attempts the same nonblocking flock, conflicting with the held lock. A hash-pinned additive client can reuse the existing module's guard functions and `persistent_request()` directly under the already-held lock. This reaches the same owner-only daemon, gate and authenticated sequenced root-agent connection without reading or replacing protocol secrets.
3. Create one exact private0700 stage and fixed0600 job/status/output files. Persist dispatch state before sending exactly one fixed worker launch. Redirect all child standard descriptors into the protected stage, detach deliberately, and receive a bounded ready/identity receipt. Record boot, PID, process starttime, stage identity, immutable plan digest and actual target monotonic start/deadline. A PID alone is insufficient for later termination/cleanup decisions.
4. Enforce a fixed native lifetime plus finite connect/handshake/read/write/flush/finish waits. The pure CG engine is synchronous and does not itself bound a blocked backend/source/sink; outer timing and I/O bindings must cover those paths. Abrupt termination is failure/unknown and cannot be described as normal session/shared-memory cleanup or TA rollback.
5. Keep one logical job owner while the bulk stream runs. Polling the same fixed status is not another native invocation; reissuing launch, replaying a TEEC chunk, resuming at a guessed cipher offset or selecting an alternate crypto frame is a retry and is outside this contract. A lost launch response remains dispatched/unknown, never permission to launch again.
6. Require exact input length/EOF and rolling expected encrypted-input digest, bounded chunks/output capacities, fixed first-failure retention, terminal cleanup facts and final host/target output length/digest agreement. Treat received plaintext as provisional private data until all required authentication/format gates succeed. CG's eventual raw seal must not be relabeled full payload authenticity.
7. Retain a terminal record or the unresolved job evidence. Clean only the exact known stage after validating the worker's identity/terminal state. Do not delete files still held by an unknown live worker or signal a recycled PID. A failure must not cause automatic root/job reacquisition or native relaunch by this adapter.

The legacy daemon can reacquire its root session after connection failure as part of existing host-assisted persistence; that is distinct from retrying a submitted command. The additive job adapter must not turn such session recovery into automatic replay of a section job. Holding the normal access flock blocks the ordinary CLI/acquisition path, but the Unix socket trusts same-owner callers and the daemon's command gate lasts one request only. Central coordination still excludes another direct same-owner socket caller from starting an overlapping job; the lock is an operational serialization mechanism, not a boundary against a hostile owner.

A minimum offline test matrix covers absent/non-ready root, owner-lock contention and child-lock self-conflict, wrong source/plan/stage/boot, launch lost before/after dispatch, exactly one worker start, inherited-pipe closure, bounded worker/I/O timeouts, status truncation/unknown identity, digest/count/EOF mismatch, socket loss mid-input or output, partial sink write, terminal native cleanup failure, and no promotion/cleanup/relaunch after an ambiguous result. None requires a TV to make the source and mocked adapter reviewable.

## Standard TLS evidence and remaining qualification

A retained target process map in `managed-plugin-inventory.json` establishes mapped paths for `/usr/lib/libssl.so.1.1`, `/usr/lib/libcrypto.so.1.1`, `/usr/lib/libcrypto.so.3`, `/usr/lib/libcurl.so.4.8.0`, and `/usr/share/dotnet/shared/Microsoft.NETCore.App/6.0.9/System.Net.Security.ni.dll`. CE separately demonstrated the actual target RSA/SHA512/PKCS1 crypto-provider path. This is concrete evidence supporting a standard .NET `SslStream` implementation rather than inventing a custom encrypted stream.

The map and CE RSA result do not prove a specific target TLS handshake, cipher/protocol negotiation, trust-store behavior or async cancellation path. A source prototype should pin the exact host server certificate/public identity, reject mismatches, use an independently reviewed client/job authorization mechanism, keep one fixed job/section binding, enforce handshake/I/O/overall limits and never fall back to plaintext or accept every certificate. This can be developed and host-tested now; a future bounded target handshake is a separate technical qualification, not an assumed consequence of library presence.

The existing root-agent socket is TCP with nonce/sequence/HMAC authentication, not TLS encryption. Its HMAC is not confidentiality for command contents or future bulk plaintext. Secret provisioning and bulk-client authorization therefore need explicit review; they cannot simply assume the existing root command transport hides a supplied capability. No credential, live endpoint, secret or certificate private key is introduced by this report.

## Input lineage

| Retained input | SHA-256 |
| --- | --- |
| `root-access/s95f-access.py` | `3a92e02003ce51d2faeace231191f6f0c73731f2bfca9caa196e05b195b439a5` |
| `root-access/persistent-root.py` | `06009dea3ebebabdfca043938928f85736d3a5843818ece39a6cedfd9b282bff` |
| Python root-agent implementation | `ee959b0e3c315d819a2a0fe89f3a45b744cea7f0330482b8059a82893b2a9c87` |
| Target root-agent C# source | `3b53e8c9de66331ca5336f57bc8eba33adf66ca2860a29daedbbeb3a98ea8405` |
| Existing root-with-margin adapter | `bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a` |
| Retained target process-map acquisition | `996cdb304923c6508aa9638010451642bd6aaaf544c540e71f35d356ec206402` |

These source caps establish supported design limits. They do not independently attest that every source byte was compiled into the currently running root agent. No current process, socket, filesystem or TLS endpoint was queried on the TV. The later frozen CG engine will receive its own independent source/host review; no CG source identity or integration approval is claimed here.
