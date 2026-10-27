# Independent onset-v4 runtime audit

## Classification

The framing-corrected logger run is accepted. It had a live host-observed READY
state, one bounded 20-second observation, verified volatile gate restoration,
an exact terminal protocol boundary, and verified logger-stage cleanup.

The concurrent For You operation is classified only as **one attempted and
returned AppControl request inside the logger window**. It is not a confirmed
CSFS tab transition. This capture is also **not a confirmed blackout
reproduction**: there was no physical panel observation, the cached post-run
tab remained Apps, the sampled RT fault was zero at both endpoints, and the
ring contains no corresponding fault record.

This does not prove that the request was never consumed or that a transient
For You view or physical blackout did not occur. The available evidence simply
does not establish either event.

## Source and transport binding

The onset record is SHA-256
`f11d41b4ee460818725e53a3ea96142536cb2aee977a0e7058e2db28e37f2fd6`.
It binds the exact reviewed components:

- framing aggregate:
  `b1ffc0f91b614163e10e4132b9410c60116d22101b5666f1614ef471b4938780`;
- framing wrapper:
  `489c4391db6622918befcf365b5952f08cd3f58f3989925b8b6d0fa51a1ab36f`;
- native manifest:
  `316d92b64be47767cb8461d4cbde30b9446d901060b2de798da605d9f1c8131c`;
- root adapter:
  `bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a`.

All five framing aggregate rows match the files on disk. All 38 onset record
calls have exact command byte counts, authenticated UID/EUID zero responses,
one matching command echo, exit zero, no timeout, and empty stderr. The largest
command is 7,878 bytes. The target self-test reports the fixed `85 = 26 + 59`
tests, zero target operations, and a bounded target-dependent output size.

The corrected launch receipt parses without normalization and binds dispatch
PID `13193`, supervisor PID/process group/session `13197`, start ticks
`28891153`, and supervisor start uptime `115564.62 431365.08`. The live READY
probe binds the same running supervisor and native PID `13210`, whose exact
command line is the pinned onset DLL plus `--execute` in the private stage.

The UI action record is SHA-256
`3370873013cf58294891f83cf03f186e7ae57b6b0bb87eed74d220d3872fc5f1`.
Its prepared-record hash, wrapper
`985b97762e1379cc062b4b222873588566ad81f8e07043c46ac1a9f3fadc2b97`,
and manifest
`79815f8e9d0a00f49de31f3e80a0e73ac549c4681097ef7f0453b518d3fb58ee`
all match the reviewed six-file UI sender. The action consists of exactly one
authenticated root call and one invocation of the fixed `--for-you` mode; it
contains no upload, retry, second send, or controller request.

## Live READY and action window

The host observed the exact READY JSON during the live run. Its PID, stage,
boot ID, gate `1`, `ReadyForHeader` phase, and SHA-256 bind the final native
outcome. The READY status was 0.19 seconds old at the poll and 0.36 seconds old
at the live-process probe.

Target-uptime ordering is exact:

| Event | Target uptime |
|---|---:|
| Logger observe start / READY payload | `115564.84` |
| Host READY poll end | `115565.03` |
| Live READY probe end | `115565.20` |
| For You sender before | `115565.99` |
| For You sender after | `115566.01` |
| Logger observe end | `115584.91` |
| Cached tab/compositor read | `115614.31` |

Thus the UI call occurred 1.15–1.17 seconds after observation began and wholly
inside the logger window. It also falls inside the wrapper's 22.01-second root
silence between the READY liveness probe and completion poll, so the logger
made no USB request during that hold.

The fixed request was:

- application: `com.samsung.tv.csfs`;
- extra: `switch_page=d/ug.tab@ForYou`;
- no `Operation` and no `__NO_RAISE_WINDOW` field.

The managed sender reports ARM32/little-endian and boot preflights accepted,
request construction, one `SendLaunchRequest` attempt, a normal return, no
exception, and safe-handle disposal. It deliberately reports
`execution_confirmed=false` and `physical_picture_observed=false`; a normal API
return is not receiver consumption or rendering proof.

## Native outcome and log delta

The native outcome SHA-256 is
`2926fdd194141784cbfa13f605e256aef950b0e5cdabf3f6bf093a833dea5e7e`.
It passes the reviewed validator and an independent exact-sequence check:

- `Accepted=true`, `Stage=complete`, no errors, and no deadline violation;
- exactly 16 ordered transfer steps with the expected directions and sizes,
  exact counts, errno zero, and valid before/after protocol phases;
- gate transition `0 -> 1 -> 0` and `PreArmFault=0`;
- pre-arm and restored 64-byte RT samples are byte-identical;
- the armed sample differs only at logger-gate byte offset 6;
- open, claim, release, close, observation, restore, and restore verification
  all succeeded;
- `RestoreUnverified=false` and `LogFlagMayRemainChanged=false`;
- the managed protocol model ended at `ReadyForHeader`.

The baseline ring is byte-identical to the post-ring artifact from the recovered
v3 control, establishing capture continuity at cursor `67`. During v4 the
write/read cursors advance together from `67/67` to `87/87`; the flag remains
zero. Exactly 20 new bytes appear in the forward span:

```text
t[6]
t[7]
t[8]
t[9]
```

Everything outside the two cursor bytes and this append span is unchanged.
There is no captured `[RTP]` fault/status record in this interval. The RT fault
halfword is zero before arm and again in the restored endpoint sample. These
are endpoint observations, not continuous proof that no transient state
occurred between them; endpoint ring snapshots likewise cannot absolutely
exclude an unseen whole-ring wrap.

## Cached UI state and cleanup

The one post-capture metadata call is authenticated and read-only. At uptime
`115614.31`, 29.40 seconds after the logger observation ended, it reports:

- cached `memory/eden/current_tab = d/apps.tab`;
- logical compositor `Display State: On`;
- visible full-screen `ScreenSaverContent.dll` and `ScreenSaver.dll` windows;
- the CSFS process/window still present.

This does not confirm the requested For You transition. Because it is a later
snapshot, it also cannot rule out a brief transition followed by return to
Apps. Logical compositor state and window metadata are not physical OLED-panel
feedback.

The onset logger's final, source-reconstructed cleanup command is the 38th
authenticated call. It validates the exact private-stage inventory, removes
only those files and directory, returns `STAGE_ABSENT`, and leaves
`cleanup_deferred=false`.

The separate UI result still states `cleanup_required=true`. No matching v4 UI
cleanup receipt is present in the supplied evidence, so UI-stage cleanup is
not established by this audit.

## Limits

- No observer reported whether the physical panel stayed lit, switched tabs,
  or blacked out.
- `SendLaunchRequest` returning is not proof that CSFS consumed or rendered the
  destination.
- The cached Apps tab and screen-saver windows were sampled after the logger
  window, not at request time.
- The four `t[...]` records do not diagnose or exclude the hardware/panel
  failure.
- The run establishes neither a repair nor a causal relationship between the
  For You request and the user's blackout symptom.
