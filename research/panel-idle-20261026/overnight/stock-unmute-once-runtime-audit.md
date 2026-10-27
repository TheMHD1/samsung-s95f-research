# Independent runtime audit: one stock unmute-zero

Offline audit performed 2026-10-26. I did not call the TV, root transport,
D-Bus, tracefs, or the network. This report reads the already retained bytes.

## Evidence identity

The executed runner remains `stock-unmute-once.py`, SHA-256
`75fab2314fdfbfbf937777c02cdd8ca7160e7b867a5e560b8e0570dfa0e4738f`.
The rendered command is 1,868 bytes with SHA-256
`a879b2f90ae2ac23dcda2c3e0a4b8f99b6714c037b2638e6e70485fde8ad32e4`.
It is byte-identical in the intent, intent argv and returned command field.

The retained result files are:

| File | Bytes | SHA-256 |
|---|---:|---|
| `intent.json` | 4,599 | `486e948747aa03b9d574dcfbe0cdb934f853d4ac70b7e06f14b0f6fe252cbf4e` |
| `client-stdout.json` | 3,727 | `d3ab16983eb56740c8bd715c2752138f4fc6d25b5609e9dd59b2237d74e1299e` |
| `client-stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `client-result.json` | 101 | `f87400dc4427b56fc13c043d71b760d6afd59f9188ad4a1605305cbe263a0aa3` |
| `interpretation.json` | 940 | `762e5f787a6bf915b0f814b2f4c3cb2c2203867767dbbb82d3cf8958608155c0` |

The intent pins root client SHA-256
`3a92e02003ce51d2faeace231191f6f0c73731f2bfca9caa196e05b195b439a5`,
uses `root --persistent-only --timeout 25`, and records `retry:false`.

## Transport and guard result

The outer client started at `2026-10-26T21:45:07.902493+00:00` and finished
at `21:45:08.367548+00:00`, about 0.465 seconds later. Its host return code is
zero and `host_timeout` is false. Host client stderr is empty.

The root envelope has exactly one command and reports:

- model `QN77S95FAFXZC`, authenticated true, uid/euid0;
- host-assisted persistence;
- `global_system_files_unchanged_at_acquisition:true`;
- command exit0, `timed_out:false`, and empty command stderr.

Both identity blocks completed. They retain the same boot
`00000000-0000-4000-8000-000000000000`, AVOC PID/start `706/603`, and exact
AVOC/libave hashes at the start and end. Because the command is `set -eu`, the
successful completion marker also establishes that the build-id, executable,
hash, global `tracing_on=0`, and `current_tracer=nop` preconditions passed both
times.

Every expected section marker appears exactly once, including
`BEFORE_SINGLE_UNMUTE_ZERO`, `AFTER_SINGLE_UNMUTE_ZERO`, `COMPLETE`, and
`SINGLE_REQUEST_NO_RETRY`. The command text contains exactly one literal
`SetPanelMute int32:0` and no mute-one, sensing, power, factory, trace-write,
remote-file, or retry operation.

## Public API result

The captured public result is internally consistent:

- baseline `GetPanelMute`: two `int32 0` values;
- baseline `GetPanelMuteCaseStatus`: two `int32 0` values;
- the single `SetPanelMute(0)`: one `int32 0` and `SETTER_DBUS_EXIT=0`;
- post `GetPanelMute`: two `int32 0` values and `POST_MUTE_EXIT=0`;
- post `GetPanelMuteCaseStatus`: two `int32 0` values and
  `POST_CASE_EXIT=0`.

The TV uptime anchors put the request between approximately `72719.20` and
`72719.24`. This supports the narrow classification **public accepted once**.
It does not show a kernel transfer, QDF gate passage, panel-controller
acceptance, command emission, or emitted light.

## Physical result

The preserved owner-chat reports before the command were `panel is off` and
`no cycle runnjng`; the fresh report afterward was `stYed black`. Those spellings
are retained verbatim in `interpretation.json`. They support the qualified
statement: **the owner reported that the panel stayed black after the one
publicly accepted zero request, so this request did not demonstrate physical
recovery**.

The operator did not directly see the TV, and there is no calibrated message
timestamp, reaction bound, or clock bound. The report therefore cannot locate
the physical observation precisely inside the roughly 40 ms API interval or
prove causation. It also does not establish the internal sensing state; `no
cycle runnjng` remains an owner qualification.

## After-the-fact log query

The separate read-only log query retained these files:

| File | Bytes | SHA-256 |
|---|---:|---|
| `intent.json` | 1,744 | `5e65d203e5f25c30b6e0fdfa8cb6961ef3cc15854469bd4d48d6ad948c61bf16` |
| `client-stdout.json` | 1,272 | `730513dccb5536d59bb481ebb19d1feb5cc19b1a501f97fc64d64248e65de12f` |
| `client-stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `client-result.json` | 101 | `c7e49315a144ce67ee282ecb2b03bff3eba73e1f7d2c1856102d9a6028368bff` |

Its exact intent/returned command hash is
`bf1d989809afe9e39433bbf8969e2b2b231d00d1717d344e671f717df01b4fdb`.
The root envelope is authenticated on the same boot and returned exit0 without
timeout. It requested vlog uptime `72717..72723`, which encloses the API
anchors, but the filtered stdout region is empty and vlog stderr says
`Write 0 logs to STDOUT`.

This is **failed diagnostic coverage, not negative evidence**. The query was
made later at uptime `72782.53..72784.77`, retained no full underlying stream,
and provides no coverage or retention certificate for the historical interval.
It cannot show that mute/PVCC/QDF/sensing/error events were absent and cannot
resolve wire emission or a suppression gate.

## Bounded conclusion

The one authorized ordinary attempt completed exactly once, with stable
identity, public return0, no retry, and no persistent-configuration command.
The owner reported no picture recovery. No on-wire or lower-gate conclusion is
available, and the zero-row retrospective log query must not be used as an
absence claim. Any future reboot and passive onset capture are separate events;
they must not relabel this result or turn it into an automatic unmute retry.
