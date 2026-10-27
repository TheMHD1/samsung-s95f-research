# Independent audit of the incomplete PM idle smoke

Status: independent offline audit of retained evidence. This audit made no TV,
root, network, trace, display, power, or device call. It does not alter or
reclassify the raw capture.

## Result

The five-second passive smoke did **not** reach its physical capture window.
The collector armed its private trace instance and then intentionally failed
closed during the pre-roll syscall-quiescence sweep because AVOC thread 1011
was observed inside ARM32 syscall 54. Consequently there is no completed trace,
sample series, PM pairing result, or physical observation from this attempt.

The retained `record.json` correctly says `accepted=false`,
`technical_capture_complete=false`, `diagnostic_eligible=false`,
`physical_state=unobserved-or-incomplete`, and
`absence_claim_supported=false` (lines 4-9 and 85-95). Its original error is
`ValueError: capture completion missing` (line 40). That broad host-side error
is consistent with the more specific retained remote evidence below.

## Exact inputs and retained hashes

| Evidence | SHA-256 |
|---|---|
| Reviewed source `observed-pm-onset-capture.py` | `c7b07bbcb508005c028824763c84109d18aee1d9df8813a5f59c476093616d06` |
| Offline tests | `08dc2d93af4630c308d52ad8f0fe9a8150a95d856f753921f39d0c7186e9dbcd` |
| Idle addendum | `365b10d403ce3d18e4e5fb5268d81aa73f8dff37f4322a79851d0998c1ee96ff` |
| Saved 108-test output | `e6811a681ac39e07e5eda7beddb7b0e3ed00bc9447f34512e5e15c38f8f51936` |
| Generated `remote.sh` | `082aaf8c9bb8a76a314fc4528119bfef0079847372288b01cf19ea4a8546e08b` |
| `record.json` | `247298a3adb37a33ace809438fc6301424c0a3ae5519bca4e59d69b45babfe29` |
| `partial-fds.txt` | `75ba03cce48df409ac270420416d40da724a99ad6ff86a6dfd44ec33eeb46bbc` |
| `partial-meta.txt` | `e76a4caa8546423c6ce5d1526765e1c429f4a735389d75d1b96889de29cbdabc` |
| `partial-artifacts.txt` | `54417c5189aea63e38b272807e195cb33b97ced444c53bc0759f4babad2ab5dd` |
| `partial-sample-errors.txt` | `68161cb4caff266caa4128b4b50a81d36a4cd63b1e3b746e86d11008d7055c58` |
| `partial-vlog-after.txt` | `20b896713735bedf9bee8f5dc7c978abc5d020f8a39e1dad697be594a54440e7` |
| `launch-root-response.json` | `16e6b5034ddfd560e48af555de7f283c01054e88994240e5f90b66096d30f2ba` |
| `quiesce.json` | `1e750d3e998ce55a4121ff84450c386c5961a52d522bacc456bbfa441e4ccc49` |
| `cleanup.json` | `06ea3651f60d074c1c731565e46b4f504ae7bb230199db6333db1ffecd8e2d42` |
| Host driver stderr | `f1828278b5deba23d70ec2238311c5bc0128063d1d69163713a4940058f15581` |

The record binds the staged script as 35,323 bytes, nine chunks, persistent-only,
with the same `082a...` hash (lines 10-16). It schedules target TV uptime
`68293.53` (lines 18-30) and records the owned collector as PID/process group
14899 with start ticks 17070409 (lines 32-38).

## Exact abort point

The retained thread snapshots are equal:

- `TIDS_START` is `partial-fds.txt` lines 1-24;
- `TIDS_PRE` is lines 70-93;
- `TIDS_ARM` is lines 98-121.

The private trace enable bracket and marker body are all TV uptime `68292.29`
at lines 94-97. The generated shell enables tracing and writes
`CAPTURE_TRACE_ARMED` at `remote.sh` lines 58-59, then performs the bounded
`/proc/<avocd>/task/<tid>/syscall` sweep at lines 62-63.

The sweep retained non-54 syscall rows for TIDs 706 through 1010 at
`partial-fds.txt` lines 123-130. Line 131 is:

```text
ATTEMPT|1011|1|68292.35|54 0x21 0xc010643a 0xf4efe4ac 0x10ac5 0x0 0xf4efe4ac 0xf4efe44c 0x42edcf2c
```

`remote.sh` line 63 expressly executes `exit 86` when that first syscall word
is 54. The evidence ends there: it has no `TIDS_QUIESCENT`, `FDS_PREROLL`,
`TRACE_ARMING_END`, `CAPTURE_PREROLL_START`, or `CAPTURE_START`. The target
uptime was still `68293.53`, about 1.18 seconds after this rejected sample.
There is likewise no retained trace or samples file and no
`CAPTURE_COMPLETE` transport line.

At the earlier `FDS_START` snapshot, fd 33 (`0x21`) mapped to
`/dev/dri/card0` (`partial-fds.txt` line 53). The tool's static request table
names `0xc010643a` as `DRM_IOCTL_WAIT_VBLANK`. Because the run aborted before
`FDS_PREROLL`, endpoint stability was not established at the syscall sample;
the earlier fd mapping is therefore contextual evidence, not a fully paired
runtime attribution. The retained row establishes only why the conservative
quiescence gate aborted.

The partial metadata is equally bounded: it contains PM kernel/source and all
seven start/config format sections plus `TRACE_CONFIG`, but has no
`PM_CONFIG_END`, `PM_SOURCE_ID_END`, `PM_CPU_STATS`, sampler identity, end
identity, or capture-window section. It cannot support PM event accounting or
ring-loss conclusions.

## Authentication and cleanup

The launch response is authenticated as model `QN77S95FAFXZC`, uid/euid 0,
host-assisted persistent root, with
`global_system_files_unchanged_at_acquisition=true`. Its sole launch command
returned zero, did not time out, had empty stderr, and returned the exact owned
PID/start/PGID tuple `14899 17070409 14899 14899`.

After the incomplete result:

- `quiesce.json` is likewise authenticated uid/euid 0; its command returned
  zero, did not time out, had empty stderr, and returned `QUIESCED`;
- `cleanup.json` has the same authentication properties; its command returned
  zero, did not time out, had empty stderr, and returned `0` then `CLEAN`;
- the final `0` is the read-back global `tracing_on` value, and the cleanup
  command verifies the owned trace instance, output directory, stage
  directory, and expiry artifact are absent before printing `CLEAN`;
- collector stdout/stderr and their partial copies are all empty.

The record's `quiesce_verified=true` and `cleanup_verified=true` are therefore
supported. Cleanup success does not upgrade the capture to complete.

## Scope and limits

This attempt did not exercise the corrected PID-0 `<idle>-0 (-------)` PM
pairing logic: it stopped before the physical window and before trace export.
It provides no evidence about a Samsung private-PM callback, SerDes polling,
panel power, the reported blackout, or its cause. It also cannot support an
absence claim. The observed syscall-54 row is a pre-start eligibility failure,
not evidence that the display fault occurred, and this audit does not justify
an automatic retry or any control change.
