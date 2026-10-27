# Paired ordinary-restart capture review — 2026-10-27

## Scope and inputs

This was an offline, read-only review. I made no TV, root, network, getter, setter, or trace call.

- accepted collector `observed-quiescent-pm-onset-capture.py`: `8390e85eff9a40fe774c5e2bd7488ebaaa703c734af20a19fd0a780b58cdc43f`
- tests: `ae330c948f7f66cb229ee88e7eb44fbf45d4cd92b914a9da439a3b5213ecb2e8`; independently rerun, 121/121 passed
- accepted five-second audit: `acbe53047adc540b6f994ba9e8d2c76b969ab63398f4c61c5001a70a2120c466`
- failed 85-second rescue audit: `53755fe062f15b13c790c3163aa2941a9606067391bfe17c5f7ad682a58d02e7`
- one-shot status runner: `7ca9bf01f3df4524f4f04e561dc4839d0805f4062f665b5c1b9a397adf788c8a`

The current 85-second render for label `paired-restart-20261027a` is 35,484 bytes, SHA-256 `01bc01d3f447fe60b1121b81804611e17abccf8c8c43c9af0828d41bbb8779b4`. It was not executed in this review.

## Prioritized findings

### P0 — do not repeat the unchanged 85-second collector

The earlier owner-restart run retained a loss-free trace and all five markers, but never emitted a complete acceptance record. Its vlog was exactly 67,108,864 bytes, the configured 64 MiB ceiling, and its final identity, semantic, and cleanup-sidecar blocks were missing. This makes another unchanged 85-second run likely to repeat the same failure. It does not prove the cap was the sole cause, so simply raising the limit is not cleared either.

The smallest useful change is a **new, separately reviewed, full-observed 30-second derivative**. The first candidate (`5eb3b89067c3c2b72ef9fa9bc89fc4af3e2e00e2b8ba4ba4515ccbcd4c926f9c`) was rejected after a host-only launch attempt exposed a missing inherited `allow_short=` keyword in its builder signature; it made no target call and started no helper. The corrected source is `5c0e4ff02d1b54f4493dede7c7cda5eb78d2163d936b207c26f572a5ab00f7c4`, with tests `a37a60807502d2dfc17bda002a035528dc483c67c6014c9b713515518be13f03`. Its five offline tests pass, including a nested quiescent-to-PM keyword-dispatch regression. The exact `apps-live-20261027b` shell is 35,381 bytes, SHA-256 `b3d9db65a75b4d90fdfb18dbf67609a9bacec8187687ad390f38c3b8c6542d10`, and passes `/bin/sh -n`. The cleared invocation is:

```sh
cd ${S95F_EVIDENCE_ROOT}/panel-idle-20261026
python3 overnight/observed-short-onset-capture.py \
  apps-live-20261027b --seconds 30 --run --reviewed
```

The derivative should change only the full-observed duration and use a new namespace. It must preserve the 12-second scheduled lead; five markers; pre-roll quiescence; AVOC/deviced PID, start-time, executable, TID, FD, maps and pointer guards; exact source/stage hashes; trace pairing and loss checks; sample inventories; owned process-group termination; exact cleanup; observer grammar; and fail-closed rejection on boot or process identity change. It must not reinterpret the existing no-observer smoke mode or introduce an unreviewed vlog filter.

Thirty seconds is only an engineering bound that sharply reduces the dominant log volume. Any cap, burst, missing endpoint, identity change, or cleanup failure must still reject. This clearance is for one Apps-to-Live transition, not for 85/90 seconds or an off/on restart inside this shorter window.

### P0 — the newly captured Apps control is a real correlated difference, but not causal proof

The owner report `okay i want to apps now ajd it works` logically preceded both queries and was recorded as Apps visible and working. The `received_recorded_utc` field in `owner-observations.jsonl` is the later time when the host persisted the record, not the message-receipt time; its name is misleading and it cannot order the physical report against the query timestamps. The exact onset and chat/report latency were not calibrated, and the owner did not explicitly confirm an ordinary off/on in that message.

Within the same Linux boot (`00000000-0000-4000-8000-000000000000`):

- `good-apps-status.json` (`4dd3f5cb6c414f1f1f90d6ec40713b31e791379e93c5dfe3279f6e5b46d872d2`) is accepted and cleanup-confirmed. At uptime `83948.26`, helper PID 17962 returned ioctl 0, changed the sentinel, and produced status `0x00000000`.
- `good-apps-kernel.json` (`34e4984246681661011f7cddb1570eabaecac4550b701d8a1132497b9b80d781`) independently retained the matching kernel line at uptime `83948.230741`: PID 17962, `QDFTcon_GetErrDetStatus`, `ERR DET Status:0x0`. This positively binds the public call's returned zero to the kernel QDF function/log path; it does not exclude that function's debug override or prove the underlying controller transaction or hardware freshness.
- `good-apps-pin.json` (`76cea107152dbfa4d21e39f1f58accf2673b5a46ee603c781c2870b2471be577`) is accepted and cleanup-confirmed. At uptime `83960.86`, it requested ERR_DET line 5 as input once and returned raw value 0 with zero tail and successful closes.
- the accepted offline replay of the non-atomic branch snapshot reports duty/cache `207/207/207`, AutoDim 0 and AutoPowerOff count 0. The original snapshot record remains rejected because its strict stderr contract did not accept expected `dd` summaries; the replay does not make the original accepted or atomic.

The reads were intentionally launched immediately after the working-Apps report, but the missing receipt/onset calibration precludes a measured physical-to-query latency. The earlier black-context samples on the same boot returned status `0x10` and ERR_DET GPIO value 1. The paired evidence establishes a state-correlated difference:

```text
reported black context: status 0x10, ERR_DET pin 1
reported working Apps: status 0x00, ERR_DET pin 0
```

This is now the strongest discriminant in the corpus. It does **not** establish that ERR_DET caused the blackout, that zero means a healthy panel, or that either read is simultaneous with the physical report. The status may be read-to-clear, the standalone status read does not exclude a debug override, the pin read itself requests input direction, and chat timing remains uncalibrated.

### P1 — run one restart only, and annotate the intentional off interval correctly

The working Apps state already supplies the good control immediately before the future capture. Do not put two restart cycles in one window.

For a separately coordinated restart capture, the annotation rules below remain the correct design, but the currently cleared 30-second run is instead limited to one Apps-to-Live transition and must not add an off/on restart. The restart sequence, when an adequately reviewed window is available, is:

1. Keep Apps visibly stable until launch and scheduled start.
2. At `START+2..7s`, submit `apps visible` and a note. Do **not** submit a structured baseline `picture visible`; the classifier selects the first eligible visible event and could pair it across the intentional powered-off interval.
3. At about `START+8s`, press ordinary Power once to turn the presentation off. Record a note only; do not label intentional power-off as `picture black`.
4. After a fixed 2–4 seconds, press ordinary Power once to turn it on. Record a note and do not navigate Home, Apps, or Live.
5. If a picture appears, immediately submit `picture visible`. If it then unexpectedly blacks out while the TV remains logically on, immediately submit `picture black`. Submit `audio present` only if physically heard.
6. Leave the TV untouched through the remaining physical window and through fetch, validation, quiesce, and cleanup.

The existing grammar is:

```text
apps visible reaction_ms=R_GOOD clock_ms=C_GOOD
note good-control full Apps visible and stable
note bad-cycle ordinary power-off pressed
note bad-cycle ordinary power-on pressed; no navigation
picture visible reaction_ms=R_FLASH clock_ms=C_FLASH
picture black reaction_ms=R_BLACK clock_ms=C_BLACK
audio present reaction_ms=R_AUDIO clock_ms=C_AUDIO
```

Only send lines for events actually observed. `reaction_ms` must conservatively cover perception/report latency; `clock_ms` must cover chat relay and operator entry. Do not invent small values. Overlapping uncertainty intervals correctly make diagnostic eligibility false while retaining the raw timeline.

### P1 — separate all one-shot diagnostic reads from the passive window

Do not run the TCON status ioctl, GPIO query, filtered dmesg query, panel-mute setter, or another getter/setter during the passive capture. The status may be read-to-clear, and both status and GPIO calls alter the event stream being observed. If another comparison read is needed, do it before launch or after verified cleanup, preserve its exact order, and do not make it an automatic retry.

### P1 — ordinary standby is allowed; a Linux/process transition invalidates the pair

Use ordinary remote standby off/on only. Do not unplug power, long-press Power, service-reboot, or factory-reset. Historical evidence shows ordinary standby can retain the Linux boot and daemon identities; it is not a promise for the next cycle.

If boot ID, AVOC PID/start, deviced PID/start, relevant maps, or source identity changes, reject. If transport is lost, preserve all raw local/remote evidence and do not auto-rerun. The 900-second expiry is not cleanup proof. On a stable boot, separately verify the exact owned output/stage/process-group/private-trace paths and global tracing `tracing_on=0`, tracer `nop`; remove only exact owned, generation-guarded artifacts. Do not press Power again while fetch or cleanup is active.

## Conclusion

The Apps control materially strengthens the diagnosis: accepted reads launched immediately after the owner-visible report differed from the prior black-context reads, with QDF status changing from `0x10` to `0` and ERR_DET pin changing from 1 to 0 on the same Linux boot. It still does not identify the failing component or justify a bypass. The currently cleared next capture is one 30-second passive Apps-to-Live transition with no in-window query or restart—not another unchanged 85-second attempt.
