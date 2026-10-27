# Independent onset-v5/v6 runtime audit

## P0 — V6 captured an actual controller RT fault event

V6 is an accepted, source-bound capture of a real controller-side technical
event. It is not merely a host-window, UI, or physical-picture inference.

The V6 record has SHA-256
`e577ac51905973b3e505683e8344b02c49239ad147998da52ddd0a3c248c12e7`.
It binds the same reviewed implementation used by V5:

- framing aggregate
  `b1ffc0f91b614163e10e4132b9410c60116d22101b5666f1614ef471b4938780`;
- deployed wrapper
  `489c4391db6622918befcf365b5952f08cd3f58f3989925b8b6d0fa51a1ab36f`;
- native manifest
  `316d92b64be47767cb8461d4cbde30b9446d901060b2de798da605d9f1c8131c`;
- native DLL
  `4870eed095247b8f5c86a58044e10e8c3682248b4c0465c49e5d4642cb8e54e9`;
- root transport adapter
  `bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a`.

All five aggregate local-file rows and all native-manifest payload rows match
the current files. All 38 V6 record calls have exact UTF-8 command byte
counts, authenticated UID/EUID zero envelopes, exactly one matching command
echo, exit zero, no timeout, empty stderr, and a decoded transport response
identical to the recorded response object. The largest command is 7,878
bytes. The fetched `native.stdout` is exactly bound by the completion size and
SHA-256; its first JSON line is exactly the separately retained native outcome
(SHA-256
`1dad737eac2e3f9d9ca08b13e6e57484f84e3af9aafa81c856f9a39b1d6752d9`),
followed only by the expected four GC lines.

The native outcome is internally complete:

- `Accepted=true`, `Stage=complete`, no errors or deadline violation;
- exactly 16 ordered transfers with expected direction and size, exact counts,
  errno zero, and valid before/after protocol phases;
- open, claim, release, close, arm, observation, restore, and restore
  verification all succeeded;
- logger gate `0 -> 1 -> 0`, `RestoreUnverified=false`, and
  `LogFlagMayRemainChanged=false`;
- final phase `ReadyForHeader`; and
- final source-reconstructed cleanup returned `STAGE_ABSENT`.

The fault transition is in the exact 64-byte RT samples. Pre-arm and armed
fault state are zero, and the armed sample differs from pre-arm only at the
intended logger-gate byte `+6`. After the 20-second observation, the restored
sample has:

```text
root + 0x2400 = 0x0001
root + 0x240a = 0x1001
root + 0x240e = 0x0000
```

These are the only pre-arm/restored byte differences: offsets `0`, `10`, `11`,
and `14`. Thus **logger-gate restoration is verified, but the restored RT
sample is deliberately not described as byte-identical to pre-arm**.

The ring independently corroborates that state transition. V6 begins with the
exact V5 post-ring bytes (SHA-256
`b889e9001401d03257a0673e483da061b6788a5832e891dccd6cb9fbb1ff588e`),
so capture continuity is established. Its write/read cursors advance together
from `143/143` to `1899/1899`, flag remains zero, and the exact forward span is
1,756 bytes. All changes are confined to the two cursor words and that append
span. The span contains:

- `[RTP]END` and `[RTP:NORMAL][395]`;
- 31 `RGB:0` diagnostic rows at `y:2159`, sampling
  `x=570/571/620/621/630/631`, with codes `0`, `4095`, and
  `464..492`, and differences `1065..1864`; and
- exactly two terminal `rtp_act_736` lines.

The previously reviewed packaged common-setter candidate writes precisely the
three fields above, then invokes the gated `rtp_act_%d\n` sink twice. Its
direct caller at linked VA `0x203a` supplies `0x2e0`, decimal 736. The live
field transition plus the exact duplicated text therefore match that reviewed
event-736 signature. The earlier live callback-table read supports the
selected packaged generation, but does not prove immutable equality of every
executing code byte; the packaged call-site attribution remains qualified by
that limit.

## P1 — This does not establish For You causality or a physical blackout

The For You action occurred inside V6's logger interval:

| Event | Target uptime |
|---|---:|
| V6 pre-view snapshot | `115882.31` |
| V6 observe start / READY payload | `115887.39` |
| V6 READY liveness probe | `115887.77` |
| For You sender before / after | `115888.93` / `115888.95` |
| V6 in-window view snapshot | `115889.81` |
| V6 observe end | `115907.45` |
| V6 completion marker | `115907.61` |

The action record SHA-256 is
`924d08abf90cb3f60cded3240d3cb4afb7ead3ca78d01a3babe0230e39e507e4`.
Its sole authenticated call invokes the reviewed six-file managed sender once
with the fixed request:

```text
application = com.samsung.tv.csfs
switch_page = d/ug.tab@ForYou
Operation absent; __NO_RAISE_WINDOW absent
```

It returned without exception, but intentionally records
`execution_confirmed=false` and `physical_picture_observed=false`. Both the
pre-action and in-window V6 view snapshots report cached
`memory/eden/current_tab=d/apps.tab`, logical compositor `Display State: On`,
and the full-screen CSFS window at the front of the application layer. Neither
snapshot contains a screen-saver window. This establishes neither receiver
consumption nor a For You render transition.

V5 is an important but non-identical control. It used the exact same logger
and fixed For You sender. Its action ran at `115803.51..115803.57` inside the
`115802.04..115822.11` observation, and the in-window view at `115804.56`
still reported Apps. V5 completed with RT gate `0 -> 1 -> 0`, fault zero,
byte-identical pre-arm/restored RT samples, and only a 56-byte ordinary ring
append:

```text
t[10]
t[11]
[RTP]Frame end
t[12]
[RTP:NORMAL][393]
t[1]
```

Unlike V6, V5's view showed screen-saver windows, so it is not a strict
same-visual-state A/B trial. It nevertheless proves that one normal return
from the same managed For You request is not by itself sufficient to produce
the captured RT event.

No person observed the physical panel during V5 or V6. Logical compositor
`On`, a CSFS window row, and the absence of screen-saver rows are not emitted
light measurements. The strongest supported classification is therefore:

> V6 captured a real controller RT fault event in the same bounded interval as
> an attempted For You AppControl request. It did not confirm that the request
> changed tabs, caused the event, or caused the physical OLED panel to go
> black.

## P2 — V5 and V6 runtime/cleanup evidence is complete

V5's record SHA-256 is
`b5e0f11b867f17167ca9217969f3fdf650f9edebb5cdf199a374acb797055dd0`;
its native outcome SHA-256 is
`33ec6c83f54e9d538d31338ff5e558ebc22d2f0fcd17fe398e537db26c09d8e1`.
The same independent raw-envelope and exact-sequence checks used for V6 pass
all 38 calls, all 16 native transfers, all fetched artifact hashes, the
completion binding, final `ReadyForHeader`, and `STAGE_ABSENT`. V5 and V6 both
had a live host-observed READY state and no controller traffic during their
20-second hold.

The view records are also exact authenticated one-call read-only envelopes:

- V5 in-window view SHA-256
  `9295abaca69556809cc53cdc5a0378cc73244466d8fb839c02ec14c328f9f31e`;
- V6 pre-view SHA-256
  `371004127f3b1c332c99a571791e5391f999c5f16747b9c23859681e5475141b`;
- V6 in-window view SHA-256
  `3e5aaec9ef810689aceda6d5814d6f0c0aa472fd98e23c01b2249d0279bc2259`.

The shared UI staging directory was later removed by the explicit zero-target-
operation cleanup. Its cleanup record SHA-256 is
`dfffbb861386dbb04278328389b22cdced9987322201b540ae0d3a95baecec6d`
and its result is `stage_absent=true`.

## P3 — Delayed stock-host corroboration agrees, with important limits

Two separately reviewed one-shot helpers were subsequently run on the same
boot. Their raw transport envelopes, exact command echoes, helper results, and
cleanup receipts audit cleanly:

- At uptime `116071.70`, 164.25 seconds after V6 observation ended, the stock
  TCON status wrapper returned `0x00000010` with classification only
  `kernel_output_written`. The result is SHA-256
  `5f8662e4cfed25563b59a303bd94190d2463e5c584dd117de15b219fd2e0e6e0`.
  A later read-only cached-kernel capture preserves the matching same-PID row
  at `[116071.646556]`: `QDFTcon_GetErrDetStatus... ERR DET Status:0x10`.
- At uptime `116125.46`, 218.01 seconds after V6 observation ended, the
  reviewed GPIO character-device input helper claimed `gpiochip15` line 5
  once and read value `1`. The result is SHA-256
  `ce16a42b0bdac28fa78498a52a860b128d13693243de278ce76d0d4708da19c0`.

These delayed results agree with a persisting error condition, but are not
atomic with V6 and do not establish the initiating cause or physical panel
state. The proprietary status getter may be read-to-clear and proves only
that the kernel wrote an output word; debug override and controller semantics
remain unresolved. The GPIO helper requests input direction and one raw line
value does not prove panel emission or identify what electrical condition set
the line.

For future explicitly authorized one-shot corroboration, the exact reviewed
CLIs are:

```text
python3 ${S95F_EVIDENCE_ROOT}/panel-idle-20261026/overnight/managed-tcon-status-read/run-status-read.py --run --reviewed --output /absolute/unique.json

python3 ${S95F_EVIDENCE_ROOT}/panel-idle-20261026/overnight/managed-errpin-cdev/run-errpin-cdev-input-once.py --run --reviewed --output /absolute/unique.json
```

The status wrapper SHA-256 is
`7ca9bf01f3df4524f4f04e561dc4839d0805f4062f665b5c1b9a397adf788c8a`
and its manifest is
`3241a1b6106c0447ba33a57b2b223d6ef88fc71daf444b3e4c03b2d880a34943`.
The GPIO input wrapper SHA-256 is
`cd0a34ffd719945bb369ecae16f4ca0672dbbaddea11be068e0f31465e185cde`
and its input-once manifest is
`2c9b1283e718c34e40656099ff9181c9481208fd669d6adda0d4558cc5a46d9f`.
Neither helper retries, resets, repairs, or supplies physical-picture proof.
