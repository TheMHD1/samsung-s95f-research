# Control-v2 launch lineage audit

## Scope and conclusion

This is an offline, read-only reconstruction of the failed `control-smoke-v2` launch. It uses only the retained authenticated transport record, the later missing-completion inspection, and the helper artifacts pinned below. It did not execute the old wrapper, contact the TV, run a controller/native binary, or alter any captured record.

The retained commands positively show that the outer remote shell passed its fixed integrity and boot guards, started one background `setsid` command, and returned launcher PID 2667. They do **not** show that `setsid` successfully executed `/bin/sh`, that the supervisor began running, or that the native process began. Every retained post-launch command was an observation-only poll or inspection; none could remove the supervisor markers, `native.stdout`, or `native.stderr`.

The strongest bounded inference is conditional: if no actor outside the retained command stream modified this private stage, the supervisor did not reach its first persisted marker. This is earlier than the native controller sequence. The evidence does not justify a blanket claim that no USB/controller operation occurred, because an unrecorded actor that removed artifacts after creation is not excluded by the retained command history.

## Evidence pins

- `control-smoke-v2/record.json`: 1,167,645 bytes, SHA-256 `db6046dd91f056c7c0649adea3b933a2bd1399e36d91dd532827d4d96334fd02`.
- `control-smoke-v2/missing-completion-metadata.json`: SHA-256 `aa64bbe1df60332b218163c9cd91b7b93f49610d5df24c1e7e5d5fc9cb972da2`.
- `control-smoke-v2/selftest.stdout.txt`: SHA-256 `a72c549dd24ba5dd55105e2e040076ee039a1262d400161426b7ef225cefd110`.
- Original helper aggregate `managed-usb-secondary-logger-onset/build-manifest.json`: SHA-256 `56f76bf3da0e85f394ab074c5003e5116b2600f30e54e049ba4c148dbef1e47f`.
- Original helper wrapper `managed-usb-secondary-logger-onset/run-once.py`: SHA-256 `85615c5dd2d85a811c5c19e8b9934b2ee6189ef106c5979a0ef495b0b1ce7478`.
- Pinned native source `managed-usb-secondary-logger-onset/Program.cs`: SHA-256 `db45feac5d5bda5e670da51be296cdb39769f898b4d7c8d9224a36cc65e13cdd`.
- The record pins native manifest SHA-256 `316d92b64be47767cb8461d4cbde30b9446d901060b2de798da605d9f1c8131c` and supervisor SHA-256 `2118a377f8a28ed0b11ae9c9bbccd7f8ffa49a519850001ea905e70c05e724bb`.
- Remote stage: `/tmp/researcher-usb-onset-5e113630055b4e81a0e0b94e5fd52ad6`.

The staged payloads were reconstructed offline from the base64 text retained in authenticated command echoes. Their sizes and SHA-256 values are:

| File | Bytes | SHA-256 |
|---|---:|---|
| `ManagedUsbSecondaryLoggerOnset.dll` | 71,680 | `4870eed095247b8f5c86a58044e10e8c3682248b4c0465c49e5d4642cb8e54e9` |
| `ManagedUsbSecondaryLoggerOnset.deps.json` | 460 | `d905733139977c0436bfd4ac520a13c29498c406961c0d9e39717dbac7b4b320` |
| `ManagedUsbSecondaryLoggerOnset.runtimeconfig.json` | 242 | `aeb46a15366e38511c192ccf65312442c64e8753b3c16fd2ca0b4cb34a5c59f3` |
| `supervisor.sh` | 1,105 | `2118a377f8a28ed0b11ae9c9bbccd7f8ffa49a519850001ea905e70c05e724bb` |

The reconstructed supervisor bytes exactly match the output of the pinned wrapper's supervisor generator for this recorded stage path. The original helper was not modified for this audit.

## Exact supervisor program

```sh
#!/bin/sh
set -u
umask 077
cd /tmp/researcher-usb-onset-5e113630055b4e81a0e0b94e5fd52ad6 || exit 91
printf '%s\n' "$$" > supervisor.pid.tmp
mv supervisor.pid.tmp supervisor.pid
cat /proc/$$/stat > supervisor.stat.tmp
mv supervisor.stat.tmp supervisor.stat
rc=0
/usr/bin/dotnet /tmp/researcher-usb-onset-5e113630055b4e81a0e0b94e5fd52ad6/ManagedUsbSecondaryLoggerOnset.dll --execute > native.stdout 2> native.stderr </dev/null &
child=$!
printf '%s\n' "$child" > native.pid.tmp
mv native.pid.tmp native.pid
wait "$child" || rc=$?
out_bytes=$(wc -c < native.stdout)
err_bytes=$(wc -c < native.stderr)
out_sha=$(sha256sum native.stdout | cut -d ' ' -f1)
err_sha=$(sha256sum native.stderr | cut -d ' ' -f1)
boot=$(cat /proc/sys/kernel/random/boot_id)
up=$(cat /proc/uptime)
printf '{"schema":"secondary-logger-onset-exit-v1","supervisor_pid":%s,"child_pid":%s,"child_exit":%s,"stdout_bytes":%s,"stderr_bytes":%s,"stdout_sha256":"%s","stderr_sha256":"%s","boot_id":"%s","uptime":"%s"}\n' "$$" "$child" "$rc" "$out_bytes" "$err_bytes" "$out_sha" "$err_sha" "$boot" "$up" > native.exit.tmp
mv native.exit.tmp native.exit
```

This supervisor contains no deletion operation. Static inspection of the pinned native source finds directory deletions only in three self-test temporary-directory cleanup blocks; the execute path does not remove the supervisor/native artifacts. The execute path publishes `logger.ready` later in its finite controller sequence using `logger.ready.tmp` followed by a non-overwriting rename. Therefore, absence of `logger.ready` alone is not proof that the native process performed no earlier controller/USB operation.

## Retained command lineage

`record.json` contains 101 authenticated remote calls. For all 101, the recorded command length is within the 8,192-byte bound, transport decoding reproduces the stored response, the echoed command is exact, there is one remote command envelope, transport and remote exits are zero, timeout is false, and remote stderr is empty.

1. Calls 0 through 27 created the private stage and uploaded exactly the four fixed inputs. The only `rm` operations in these calls removed the four temporary upload encodings: `ManagedUsbSecondaryLoggerOnset.dll.b64`, `ManagedUsbSecondaryLoggerOnset.deps.json.b64`, `ManagedUsbSecondaryLoggerOnset.runtimeconfig.json.b64`, and `supervisor.sh.b64`. Each removal preceded launch and targeted neither a supervisor marker nor a native output.
2. Call 28 rechecked the exact inventory and hashes and ran the fixed native `--self-test`. The retained result reports 85 tests total, 26 native-engine tests, 59 onset-state tests, and zero target operations. Its command contains no deletion of stage outputs or markers.
3. Call 29 rechecked inventory, hashes, and boot identity, then issued exactly:

   ```sh
   /usr/bin/setsid /bin/sh /tmp/researcher-usb-onset-5e113630055b4e81a0e0b94e5fd52ad6/supervisor.sh </dev/null >/dev/null 2>&1 3>&- &
   echo LAUNCHER_PID=$!
   ```

   The response was `LAUNCHER_PID=2667`, with remote exit zero and empty stderr. The call ran from `2026-10-27T08:46:40.439094+00:00` to `2026-10-27T08:46:40.575874+00:00`.
4. Calls 30 through 100 were 71 read-only polls. The first recorded uptime was `112413.10`; the last was `112477.26`, a 64.16-second interval. Every poll remained on boot `00000000-0000-4000-8000-000000000000`, found no `supervisor.stat`, no `native.exit`, and no `logger.ready`, and returned `WAIT`. These polls did not delete, signal, retry, or launch anything. They did not test `supervisor.pid`, `native.pid`, `native.stdout`, or `native.stderr`.
5. The wrapper reached its completion deadline. No cleanup call is present in the record, and the record explicitly carries `cleanup_deferred: true` and `no_retry: true`. In the pinned wrapper, the stage-removal path follows successful completion parsing, artifact retrieval, and outcome acceptance; that path was not recorded here.

## Launch and redirection ordering

For call 29's background command, the outer shell processes redirections from left to right before starting the command:

1. Open `/dev/null` as standard input.
2. Open `/dev/null` as standard output.
3. Duplicate standard error from the already redirected standard output.
4. Close file descriptor 3.
5. Start the `setsid` command as a background job.
6. Expand `$!` and print the shell-assigned background-job PID.

Consequently, `LAUNCHER_PID=2667` positively proves that the authenticated outer shell assigned a PID to the queued background job. It does not prove successful `setsid` exec, successful `/bin/sh` exec, or entry into `supervisor.sh`. Diagnostics emitted by `setsid` or `/bin/sh` would have gone to `/dev/null`.

If `supervisor.sh` entered after its `cd`, its durable-file ordering would be:

1. Open/truncate `supervisor.pid.tmp`, write the shell PID, then rename it to `supervisor.pid`.
2. Open/truncate `supervisor.stat.tmp`, copy `/proc/$$/stat`, then rename it to `supervisor.stat`.
3. Before starting `dotnet`, open/truncate `native.stdout`, then open/truncate `native.stderr`, and open `/dev/null` for the child's standard input.
4. Start the native child, then write and rename `native.pid.tmp` to `native.pid`.
5. Wait for the child; calculate output sizes and hashes; write and rename `native.exit.tmp` to `native.exit`.

The native process, if reached, publishes `logger.ready` only later. This ordering makes `supervisor.pid` the supervisor's earliest persistent stage artifact and makes `native.stdout` and `native.stderr` exist before the native child begins executing managed code.

## Later same-boot inspection

The separate `missing-completion-metadata.json` describes a read-only inspection with no controller traffic, retry, signal, or cleanup. At uptime `112546.91` on the same boot, it found:

- `/proc/2667/stat` absent (`LAUNCHER_MISSING`), and no matching managed native process in the captured process listing;
- the private stage directory still present with exactly the four input files and their recorded sizes;
- no `supervisor.pid`, `supervisor.pid.tmp`, `supervisor.stat`, `supervisor.stat.tmp`, `native.pid`, `native.pid.tmp`, `native.stdout`, `native.stderr`, `logger.ready`, `logger.ready.tmp`, `native.exit`, or `native.exit.tmp`.

Same-boot identity excludes a reboot between launch and this inspection. PID 2667 being absent proves only that this PID did not exist at inspection time; it does not establish why it ended or exactly how far it progressed. The later inventory records sizes rather than fresh content hashes, so content continuity from the guarded launch is not independently re-proved by that inspection.

## Proof boundary

The retained evidence positively establishes all of the following:

- The outer shell accepted the fixed launch after its integrity and boot guards and returned background PID 2667.
- The exact staged supervisor contains no deletion and, if entered, would create persistent supervisor artifacts before native execution.
- No recorded post-launch command removed, truncated, retried, signalled, or replaced the stage or any supervisor/native artifact.
- `supervisor.stat`, `native.exit`, and `logger.ready` were absent throughout the recorded 64.16-second polling window.
- At the later same-boot inspection, the launcher PID and managed process were absent and the stage contained the four inputs but none of the supervisor/native artifacts.

Under the closed-world assumption that only the retained commands and the staged supervisor/native program acted on this private directory, those facts imply that the supervisor did not complete its first marker publication and therefore did not reach native launch. This is a useful localization, not an unconditional execution-history proof.

The exact remaining assumption is narrow: the evidence cannot exclude a process or action absent from the retained command log that removed all created marker/output files, or removed and recreated the stage, between their possible creation and observation. No such actor is evidenced, and no retained command has that effect, but the record is not a system-wide file-access audit. For the same reason, the missing artifacts cannot by themselves prove zero controller/USB activity. They show that there is no retained evidence of native progress and that, absent an unrecorded artifact-removing actor, execution stopped before the supervisor's first persistent marker.
