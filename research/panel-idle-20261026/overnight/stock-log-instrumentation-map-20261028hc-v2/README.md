# Stock kernel log instrumentation v2: numeric file guards

HC-v2 supplies a host-qualified fixed snapshot/archive/filter CLI and a retained-source map. It has made **zero target calls**. It can prepare a non-clearing `dmesg` request for the central operator's existing authenticated, serialized root adapter. It contains no root transport, automatic execution, GPIO query, native controller helper, USB transfer, trace enable, log-level change, recovery action, or retry.

The useful next observation is whether an instrumented ordinary stock MODE2 attempt prints the QDF ERR-skipped message or reaches its normal status/frame/register-replay tail. This is an observation of existing messages. It does not add a kernel probe, recover the controller, or establish the current callback provider. `stock_log.py` preserves the original **dmesg stdout bytes**, then filters them offline. The file named `kernel.raw` is not a dump of kernel ring-memory representation.


## Additive correction after the first actual v1 refusal

The first actual HC-v1 snapshot stopped before its terminal capture frame after dmesg had produced its two files. Separate accepted read-only stage inspection found a root-owned mode-0600 nonempty `kernel.raw` (500,857 bytes, SHA-256 `fdfa320430224b166d3e37f03f51c297f18ee87b13b13f114b7c3f87424a0150`) and zero-byte mode-0600 `stderr.raw`. GNU `stat %F` labels the latter **regular empty file**, whereas v1 required the human description **regular file**. The frozen v1 source and original refused acquisition remain unchanged. The original dmesg exit is **unknown**: its shell-local `rc` was never emitted. Empty stderr and a readable raw file do not reconstruct that exit or promote the refused capture.

V2 replaces those human-description comparisons with explicit `test -f` plus `! -L`, followed by exact numeric UID/GID/mode/size guards. The directory similarly uses `test -d`, `! -L` and exact numeric ownership/mode. All root ownership, 0600/0700 modes, sizes, inventory, whole hashes, caps, one-dmesg/no-retry contract and raw-before-filter sequence remain. V2 has a unique schema (`s95f-stock-log-hc-v2`) and fresh stage prefix, so it does not adopt or overwrite the old stage.

`verify_delta.py` proves the complete production source equals v1 after exactly seven named transformations (schema, prefix and five type checks); all other function ASTs are identical. `test_actual_stat.py` executes actual host GNU stat and the two file-type predicates against private empty/nonempty/symlink/directory/FIFO fixtures. It confirms the observed descriptions, accepts both kinds of regular nonlink files, rejects other kinds, independently tests numeric metadata and permission drift, and confirms the literal production root-owner guard is unchanged. The host owner is not rewritten to root: nonroot fixtures would fail the production root ownership check, as intended. No full capture command or root transport executes in these tests.

Original-stage forensic acquisition is separate from a new capture. A future or parent-owned ordinary-file archive must bind the exact known old stage, same boot, two-file numeric-mode/type inventory and observed full hashes before and after each chunk; it must label `dmesgExit=null`, `captureAccepted=false`, `forensicArchiveVerified` independently, and must not manufacture an HC capture frame. It must not invoke dmesg, delete the stage, or infer completeness/freshness from the filenames. Parent has authored a separately reviewed fixed forensic archive; it is not part of this v2 capture package.

## Concrete source map

Offsets below are offsets within the retained ELF `.text`, not live kernel virtual addresses. `source-audit.json` pins all five ELF files, exact string sections/offsets and relocations, bounded branch spans, imported early-trace calls, historical runtime evidence, and classifier marker fragments. Its `nearbyPrintkCalls` lists bounded candidates; it is explicitly not a control-flow/data-flow proof for every format relocation. The critical branch/call instructions are checked separately.

| Printed evidence | Exact retained QDF coordinate | Meaning and limit |
| --- | --- | --- |
| `Reset(2)` | format relocation `0x11cd0`, string `0x8520`; calls `0x11ce0`, `0x11cec` | Operation-41 mode2 requests off then on, aggregating the two body returns. Optional callback absence can still return zero. |
| `err_det is fault. skip the tcon recovery.` | branch `0x118f4 -> 0x11994`; format relocation `0x119bc`, string `0x83e0` | Positive report that this power-body invocation used the ERR-skipped path. It does not identify the electrical source or prove shared fault-state clearing. |
| `Check Tcon and register recovery` | format relocation `0x1191c`, string `0x8438` | Entry to normal tail; subsequent status, frame, and register replay calls at `0x1192c/0x11930/0x11934` discard their return values. A zero top-level receipt is not a success report for each stage. |
| `Qd init check[...]`, `TCON Access ...`, `Qd Display check[...]` | function span `0xb250..0xb730`, strings `0x5038/0x50d0/0x5100/0x5130` | Reports from status/access/display checks. The word “init” does not establish that both controller images restarted or scatter initialization ran. |
| `read frame mode`, `Same frame mode`, `Set Frame mode for recovery` | `0x107e8..0x10928`, strings `0x7b60/0x7be8/0x7c30` | Frame-mode read/comparison/request reports. No actual frame-rate measurement is inferred. |
| `resume npc_lut data [done...]` | `0xf6d8..0xf910`, strings `0x7120/0x7188` | Cached register replay entered/completed according to its printed report. This is not proof of firmware reload, shared-root reinitialization, or optical recovery. |
| `tztv_set_sdp_jp_tcon_power_reset[1/0]` | relocations `0x11b34/0x11a10` | Optional OCL reset callback was reached far enough to print. Exact branch/provider binding must be considered. |

OCL's retained `.text+0x2b6c` references string `0xb40`, `Reset TCON power= %d ret = %d`. The underlying sender invokes mailbox command `0x3f`; source does not close its receiver/reset domain. FRC-TCON GPIO messages reference `samsung,sw-pvcc` and `samsung,tcon_nreset_gpio` implementations at `0x5b90` and `0x5a48`. Printed GPIO intent/return is not a rail measurement. The prior GZ source guide contains the detailed receiver/domain limitations and is hash-pinned, rather than duplicated here.

The actual historical `stock-rt-lifecycle-trial-20261027av/kernel-end.txt` contains the mode2 request, off/on/OCL messages, normal-tail entry, access/display status, frame comparison and NPC replay messages. HC checks that positive retained example; it does not reuse its outcome as the current fault diagnosis. The classifier keeps exact byte/line locators, source marker names, textual printk timestamps and printed PIDs. It does not automatically join messages into a successful invocation. Multiple invocations, interleaving and missing messages require explicit assessment.

## What tracing/log controls actually exist in the retained evidence

Five retained modules have no matched `__dyndbg`, tracepoint/trace-event sections or dynamic-pr-debug/tracepoint symbols in the scoped audit. QDF, FRC-TCON, API and OCL declare no module parameters; SDP-FRC declares only `TIMESTAMP:20260701_1717`. The API exports `tcon_debug_level`, `frc_debug_level` and `frc_tcon_debug_level` as BSS **objects**, not demonstrated sysfs parameter files. HC does not set them. This bounded ELF evidence does not establish global dynamic-debug absence or rule out other log-control interfaces.

The critical QDF branch strings above are direct printks. QDF's identified `trace_early_message` call is in `m_check_vdd_det_high_status` at `.text+0x1e34`, so collecting early-trace alone would miss the ERR/normal-tail distinction. FRC-TCON has source calls in DPMS off/on, module insertion, resume thread and PM resume/suspend functions; OCL has HDMI context calls. `source-audit.json` records their exact relocation coordinates and containing functions without inventing a common live enable gate.

Historically advertised static events include `early_trace:early_event`, GPIO value/direction, I2C read/write/reply/result, IRQ entry/exit, PM callback start/end, suspend/resume and raw syscalls. Retained actual formats and the accepted DH private-instance recorder qualify those historical paths. They provide context; no QDF-specific static event was qualified here, and current event availability is not inferred from a build symbol. Existing DH private tracing, if separately used by the central operator, already has finite expiry, per-instance buffers/filtering and cleanup. HC does not alter global or private tracing.

Recent actual GP discovery reports `nop` only and unavailable filter functions. A second discovery retained four absent kprobe/dynamic-event interfaces, then refused because `/proc/kallsyms` could not be opened. That original partial refusal remains a refusal; its four explicit absence observations are narrower evidence. Function-graph/kprobe instrumentation is therefore not implemented.

Parent's separately retained DT observation resolves `samsung,sw-pvcc` cells `0x47/0/1` to provider `gpio18`, offset zero, flag cell one. A fixed read-only debug snapshot has no requested line under that chip. No `samsung,tcon_nreset_gpio` property matched the completed tree query. Provider identity is metadata, not polarity, live rail level, absent hardware, or current callback selection; source can free a GPIO after setting it. HC pins the parent's careful integrated note without re-querying any GPIO.

## Fixed capture and archive contract

`stock_log.py` supports four offline subcommands. They print plans or process already captured files; none submits a target request.

1. `plan --nonce <32 lowercase hex> --boot <exact boot UUID>` emits one fixed shell command and bounds. Stage is exclusively `/tmp/s95f-stock-log-v2-<nonce>`. The central adapter must bind its authenticated envelope, exact command, uid/euid zero, command count, boot, remote exit, timeout and stdout/stderr to the request. A missing terminal frame or failed outer request is a retained refusal; there is no resubmission.
2. That command creates one fresh root-owned mode-0700 stage with two mode-0600 ordinary files, runs plain non-clearing `dmesg` **once**, records its exit, byte counts, SHA-256s and `/proc/uptime` brackets, and emits a small terminal frame. A shell file-size limit applies before dmesg; its implementation-dependent units are not a byte-size attestation. Independent accepted-file caps are 1,048,576 stdout bytes and 2,048 stderr bytes. Exit nonzero, nonempty stderr or oversize refuses the capture. Any files already created remain retained; ambiguous requests are never automatically retried.
3. Save the returned decoded stdout privately, then use `receipt --nonce ... --boot ... capture-frame.txt`. Save its JSON privately. `fetch-plan receipt.json` emits exact guarded fetch commands for 16,384-byte chunks. Each command rechecks boot, stage/file modes, regular-file/no-symlink status, exact two-file inventory, whole sizes/hashes before reading, and both hashes/boot again before its terminal marker. Only the two fixed files and exact bounded chunk indices are allowed. The central adapter must validate every enclosing root receipt separately. No cleanup or deletion is generated.
4. Save decoded successful chunk stdout as the exact plan names in a fresh **0700** directory, all files **0600**. `archive receipt.json chunks/ output/` verifies exact inventory, all frames, exact lengths, canonical base64 and whole-file hashes before creating an exclusive 0700 output. It writes `kernel.raw` and `stderr.raw` as 0600, flushes/fsyncs both and their directory **before** classifying. `analysis.json` retains capture acceptance/refusal and the derived marker projection. A bounded refused capture may be forensically archived; archival success never changes `captureAccepted=false`.

No generic target path/reader-size/command interface exists. File guards use `test -f`/`test -d` plus `! -L` and numeric stat fields, never localized or empty-sensitive `%F` prose. All generated commands avoid backslashes, accounting for the observed root-agent quoting behavior. The remote private stage is deliberately retained even after verified host archival. Host receipt and command files are private too: they contain exact boot/nonce bindings and may contain sensitive kernel messages.

| Bound | Value |
| --- | ---: |
| Command body | ≤8,192 bytes; host-qualified maximum recorded in validation |
| Decoded root response | ≤65,536 bytes |
| Chunk frame | ≤24,000 bytes, including framing/base64/newlines |
| Raw capture accepted cap | 1,048,576 bytes |
| Stderr forensic cap | 2,048 bytes |
| Fetch calls | ≤65 (64 raw + 1 stderr); ≤66 including capture |
| Parent adapter per-request remote/host deadline | 45 / 75 seconds |

The program enforces framing/file bounds. The parent adapter must enforce its transport/envelope/deadline limits. Those deadlines are process-level attempts, not proof that a blocked kernel read has rolled back. File-size and transport caps can yield a refused partial capture; files and refusal are retained. The capture contains no force timeout claiming recovery or rollback.

The dmesg read is one snapshot of the utility's output. Buffer overwrites, lost messages, truncation or utility/kernel formatting can precede acquisition. It is never labeled a complete kernel log. Before/after snapshots should be kept separately; HC does not clear the ring or manufacture a lossless delta. `/proc/uptime`, printk timestamps and native controller timestamps are distinct clock evidence unless independently calibrated. Source-associated messages do not establish physical recovery, executed controller image identity, reset of all domains, fault-flag clearing, optical state or absent execution from absent text.

## Host qualification and reproducibility

Run from this directory, using its HOME-backed scratch directory:

```
python3 -B audit.py > source-audit.replay.json
python3 -B -O audit.py > source-audit.optimized.replay.json
python3 -B verify_delta.py > delta.replay.json
python3 -B test_actual_stat.py > actual-stat.replay.json
python3 -B test_host.py > validation.replay.json
python3 -B -O test_host.py > validation.optimized.replay.json
```

`audit.py` uses the retained Capstone/ELFtools installation at `/tmp/tcon-capstone`; it installs nothing. It reads the pinned local modules and retained observations. Reviewers can set `HC_TEST_TMPDIR` to their own existing HOME-backed private scratch directory. The inherited suite executes only `/bin/sh -n` for syntax; the added stat suite executes host-only GNU stat and type predicates against private fixtures. Neither executes generated capture/fetch commands. They cover maximum raw/stderr chunks, malformed/missing terminal frames, mode/instance/extent/hash drift, canonical encoding, exact private/exclusive archive behavior, refusal-preserving archival, positive/missing/interleaved marker cases and scientific false flags. The normal and optimized outputs are byte-identical. `source-inventory.json` freezes authored files; `source-audit.json` pins source inputs without copying OEM binaries or private raw logs. No target acquisition or deployment has occurred for HC.
