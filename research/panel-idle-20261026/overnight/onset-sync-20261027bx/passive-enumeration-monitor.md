# Optional passive enumeration monitor: central coordination plan

This is an offline design, not an executable target helper or an instruction to run a reset automatically. The monitor would observe a centrally coordinated, separately invoked existing stock MODE2 operation while Apps remains selected. It would perform no UI, power, reset, USB ioctl, vendor transaction, driver binding, forced collection, ftrace or VLOG operation. The already authorized operation and all TV actions remain centrally coordinated by the parent.

## Proposed bounded lifetime and artifacts

Use a fresh root0:0 mode0700 UUID directory under `/tmp`, with fixed root0:0 mode0600 files: `monitor.sh`, `events.txt`, `pid.txt`, `pid-stat.txt`, and `done.txt`. Stage only reviewed exact script bytes, verify size/hash and exact inventory. Cap `events.txt` at8192 bytes by construction; do not run a general log follower or append arbitrary diagnostic text. Avoid recording process environments.

A single start request launches exactly one foreground-shell monitor as a background child, with stdin `/dev/null` and stdout/stderr `/dev/null`; its only outputs are the fixed bounded files. Parent obtains `$!`, validates its positive numeric form, records it in `pid.txt`, and saves `/proc/PID/stat` immediately in `pid-stat.txt` as the process-identity anchor. No `kill`, reset or cleanup action is hidden in start, sample, finish or collection. The monitor stops itself. If it cannot stop, a later decision belongs to central coordination; this plan supplies no automatic kill.

A background process surviving the authenticated root-request lifecycle is a technical qualification requirement. The present adapter's45-second remote deadline and process-group behavior must be checked using an ordinary dummy bounded sleeper before relying on this design. Redirecting all inherited streams avoids waiting on an open output pipe but does not itself prove survival. The start request must return immediately with a fixed receipt, stage path, PID and identity record. An ambiguous start receives no retry and no MODE2 invocation under this plan.

Set an absolute monotonic deadline of start `/proc/uptime` +2000 centiseconds, plus a maximum of200 samples. Sample immediately, then `sleep 0.1`; check the deadline before and after every sample and sleep. Use shell builtin `read` with redirects for cached attribute files rather than launching a subprocess per attribute. A maximum iteration count alone does not provide a20-second duration bound when sampling incurs overhead. Conversely, userspace scheduling can delay observation of a passed deadline; the claim is self-termination on the first scheduled deadline check, not an uninterruptible kernel timer.

Kernel `/proc/uptime` normally supplies two decimal places. A proposed reviewed shell conversion can validate `seconds.fraction` with exactly two decimal digits, then compute `seconds*100 + (1fraction -100)` to avoid leading-zero octal interpretation. Unrecognized time formatting, backward time or invalid numeric fields terminates with an explicit bounded error record. No wall clock timestamps are needed inside the monitor.

## Sample contents and record bounds

Read only `/proc/uptime` and these cached sysfs paths for physical port7-1:

- `/sys/bus/usb/devices/7-1/` existence;
- `busnum`, `devnum`, `bConfigurationValue`, `authorized`;
- directory presence of `7-1:1.0`, `7-1:1.1`, `7-1:1.2`.

Read `devnum` both before and after the other attributes. Keep each snapshot's first and last uptime. A stable populated sample requires port present throughout, bus7, equal valid devnum1..127 at both reads, and all attributes successfully parsed. Otherwise record `ABSENT` only when the port is absent at both boundaries; record `UNSTABLE` for mixed presence, disappearing attributes or changing devnum. Never turn a read failure into a stable configured sample. Root access and expected sysfs path permissions are qualified separately; persistent failure is UNKNOWN.

Represent a stable state with only bounded numbers and enumerated tokens, for example:

```
S begin_cs=16720000 end_cs=16720001 state=PRESENT bus=7 dev=53 cfg=1 auth=1 if=111
S begin_cs=16720112 end_cs=16720112 state=ABSENT
S begin_cs=16720233 end_cs=16720234 state=PRESENT bus=7 dev=54 cfg=1 auth=1 if=111
```

These are shape examples, not target observations. Interface bits mean directory presence only; they do not prove driver absence or interface readiness. Preserve the initial snapshot and append only changes to the state tuple, plus a final snapshot and one terminal line. At most32 state records, each at most160 ASCII bytes, plus two terminal records at most160 bytes gives an upper bound5440 bytes. Explicitly check the projected append length against8192 before each write, and stop with `OVERFLOW` while reserving terminal space if additional changes exceed the record limit. A full file or failed append makes the monitor result incomplete. Use an exact final byte count and hash when collecting. The parent must not infer missing states from coalesced or overflowing output.

On normal deadline/sample completion, append a bounded `END reason=DEADLINE|SAMPLE_LIMIT samples=N changes=N` line, then create a fixed `done.txt` receipt only after the event log is closed. `ERROR`, `OVERFLOW`, absent completion, unexpected inventory or a still-live anchored PID at collection prevents a complete-result claim. The PID may be reused; compare `/proc/PID/stat` start identity before interpreting liveness. A vanished PID plus a valid completion receipt supports normal exit; a PID mismatch alone does not supply the missing receipt.

## Serialized central sequence

1. Verify Apps and header focus using the parent's existing preparation workflow. Acquire the ordinary pre-state and exact port53 identity outside this monitor.
2. Start one reviewed passive monitor. Require the fixed successful start receipt and at least its first stable state. The monitor has at most20 seconds from its own start.
3. Issue one existing stock MODE2 helper in a separate centrally serialized root request. Its invocation, return, operation/mode and host/root timing are recorded independently. This monitor invokes none of them.
4. Let the monitor terminate itself. Retrieve the bounded files in a separate root request with exact inventory, permissions, maximum size, hashes and authenticated framing. Do not launch a second monitor to fill an ambiguous interval.
5. Independently acquire fresh cached descriptors, exact sysfs/device-node identity, configuration/activity/interface binding and a bounded FD census for the new instance. Use the corrected reviewed wrapper census only after its target qualification. Retain any new dmesg USB rows if still present, as corroboration. Cleanup of the known private stage occurs only after the evidence is saved and normal exit/inventory are established; otherwise retain it for central inspection.

The20-second monitor window must contain the actual MODE2 request, not just the preceding staging. Ensure sufficient remaining time after the first stable receipt; if staging/root scheduling consumed the window, classify the attempt as missed rather than automatically repeating it. The root requests remain serialized; the child monitor is the only concurrent reader.

## What the evidence could establish

A stable old-instance snapshot, an observed `ABSENT` sample, and a later stable different-devnum/config1/authorized1/interface111 snapshot on the same port support an observed enumeration boundary within the sampled intervals. Report the actual old/new devnums; do not prefill54. Bind that record to the parent's exact MODE2 timing without asserting an instantaneous USB event timestamp. A new devnum without an observed absent sample supports only a sampled instance change; a short disconnect can fall between100ms samples. No instance change, `UNSTABLE`, overflow or missing completion is inconclusive.

A sampled disconnect/re-enumeration and configuration boundary still do not prove positive endpoint queue state, protocol readiness, controller RAM reply freshness, physical picture restoration or the absence of vendor traffic between samples. The parent's closed-world source/lineage premise remains explicit. In particular, passive polling must not silently clear an unknown prior vendor-OUT phase. The monitor supplies observed identity lifecycle evidence for a later reviewed readiness decision, not that decision itself.
