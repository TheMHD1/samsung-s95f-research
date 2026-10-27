# Ugoos movie transition: rejected-capture salvage analysis

Date: 2026-10-27 UTC

## Result

The capture is **rejected and remains rejected**. `record.json` records
`accepted=false`, `technical_capture_complete=false`,
`diagnostic_eligible=false`, and `ValueError: AVOC maps changed`. The exact
map change was growth of the AVOC heap by `0x34000` (212,992 bytes):

```text
START 020cd000-0229d000 rw-p 00000000 00:00 0 [heap]
END   020cd000-022d1000 rw-p 00000000 00:00 0 [heap]
```

The other 1,344 map rows were byte-identical. This looks specifically like a
heap-boundary change, not evidence that `libave` was unmapped or reloaded, but
the reason for the growth is not established and it violates the observer's
predeclared endpoint-identity contract. This report therefore treats every
sidecar result as rejected-run salvage evidence, not as an accepted onset
capture.

Within that limit, the retained data establishes the following chronology:

1. The physical trace window was `86932.696670` through `86992.860027`
   uptime seconds; the drain marker was `86992.969342`.
2. The HDMI receiver underwent a source/mode transition beginning near
   `86941.849`: video mute, loss of input lock, a temporary 720x480 report,
   then link recovery and 1920x1080 lock by `86944.639`. DRM-DP logged mute
   off at `86944.771796`.
3. During the same early transition, the QD command trace contained a
   screen-saver-brightness write of zero at `86937.845748`, followed by 51
   selector-`0x128` writes from 292/256 down through 255..207 between
   `86941.269531` and `86944.250072`.
4. One status-handshake read at `86944.133660` ended with Linux I2C transfer
   result `-6` and no reply payload. It is a failed transport, not a
   controller acknowledgement.
5. The HDMI receiver subsequently logged repeated `CLEAR_AVMUTE`, while
   periodic DRM-DP summaries continued to show sync 1 and mute tuple
   `(0 0 0 0)`. Userspace audio getters repeatedly returned `spdif out mute
   (0)` and device mute `onoff=0`.
6. The owner's later raw report, “screen went dark but audio is running,” was
   received at estimated TV uptime `86966.244`. Its recorded uncertainty
   interval is `86965.145..86967.344`, but reaction and clock uncertainty were
   incomplete and there was no preceding calibrated visible-picture
   annotation. It is not a qualified physical onset timestamp.
7. After capture cleanup, on the same boot, a separately accepted one-shot
   status read returned `0x00000010` at uptime `87101.04`; a separately
   accepted input-only GPIO read returned value 1 at `87129.47`. An earlier
   accepted status read while the owner reported the Ugoos menu visible had
   returned zero at `86297.39`.

The paired status and pin results are the strongest new discriminator: the
later owner-reported black state was associated with status bit `0x10` and the
fault input value 1, whereas the earlier menu-visible state had status zero.
Prior source work names bit `0x10` **RT Protect**, but neither this association
nor the retained traffic proves the physical producer, the threshold that
asserted it, the moment it asserted, or that it caused the panel to stop
emitting light. The status helper's own contract proves only that the kernel
wrote a value different from its sentinel; controller read-to-clear and QDF
debug-override paths were not excluded.

## Inputs and integrity

Primary capture directory:
`overnight/ugoos-movie-20261027a.onset/`.

The seven final sidecars and their `partial-*` salvage copies are pairwise
identical. Principal hashes are:

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `record.json` | 6,697 | `2a8b8f922cf8dc0ae4d06fc8cefe3115c81434f1de4642ec149fb2ec7d4b0f59` |
| `trace` | 12,866,350 | `bcf829dac0631d93627f26fd9f8bfdd53c9a5393838e3f113d8590a789c2c97f` |
| `meta.txt` | 494,771 | `69dfa246263cd49d429f9614e92dc0942682ea32b826450a6210633cb75b5ee2` |
| `samples.txt` | 84,840 | `0124530650056d220c63e0d54f1af44bbf461a56eccdecb6eb1da0adb0009b06` |
| `sample-errors.txt` | 144,689 | `b6b0dd7ebe7327c59936b6e0e7c0f2da415a27a79728327d3ebbf2109cccc1ad` |
| `vlog-after.txt` | 17,205,396 | `90dc0dcdc4ef4abf59707f2686603053c3a01dd4fbb98c4880a15fbdd82b2543` |
| `artifacts.txt` | 175,509 | `05c32544e2079d7fdc97c6c8ad6913d3499b9d524c9713a3c1e1b0000c0fcb55` |
| `fds.txt` | 5,809 | `f722537188652a0acd1e4ded9053ebd2a513d3733d8ee1995a0cfab21379481e` |

The collector reached `CAPTURE_COMPLETE`; collector stderr is empty;
quiesce and cleanup are both verified true. Those lifecycle facts do not
override the map-identity rejection.

The embedded kernel snapshots have independently parsed metadata in
`overnight/ugoos-movie-20261027a-hdmi-kernel-evidence/`:

| Snapshot | Snapshot uptime | Ring timestamp span | Plain ring SHA-256 |
|---|---:|---|---|
| START | 86922.09 | 86456.707672..86922.083797 | `a89e66c09edb5944b2552cfbd108ec0c1d2bd3b2362331a92f44e6fa822c3b64` |
| END | 86993.35 | 86709.316088..86993.414940 | `a95ebe22df81851b31d700a803732c2549c39e3302d0ba77fe513f66e75eaff4` |

The END snapshot temporally brackets the physical trace window. That does
not prove complete kernel-ring coverage, although the relevant window lies
inside the retained timestamp range.

## QD/I2C trace inventory

`overnight/decode-qd-trace.py` was run offline against the immutable trace.
Its report had 293 grouped transfers, zero parse errors, complete retained vs
written ring accounting, and `semantic_capture_complete=true` in the
decoder's narrow transfer-grammar scope. That decoder status does not repair
the observer rejection.

Command inventory relevant to this analysis:

| Count | Command / interpretation | Outcome |
|---:|---|---|
| 186 | `f30100000000`, status-handshake shape | complete Linux transfers |
| 1 | same command at 86944.133660 | missing read reply, result `-6` |
| 51 | `f30000000128`, dimming-level request | complete Linux transfers |
| 6 | `f30000000174`, query preparation | complete Linux transfers |
| 6 | `f3800000000d`, selector-0x0d read | complete Linux transfers |
| 5 | `f3800000000c`, selector-0x0c read | complete Linux transfers |
| 1 | `f300000000c4`, screen-saver-brightness=0 | complete Linux transfer |
| 1 each | selector ranges `0x21c..0x258` and `0x31c..0x358` | complete Linux transfers |
| 1 each | late selectors `0x02` and `0x09` | complete Linux transfers |

“Complete Linux transfer” means the trace recorded the expected I2C message
count and result. It is not a controller acknowledgement and is not proof of
panel output.

The decoder's focus and maintenance-focus lists were empty. There was no
captured command that the decoder classifies as an error-status query, and no
wire read of the later `0x10` status occurred inside this trace. Therefore
the capture does not timestamp assertion of the later fault bit.

### Detailed early sequence

| Uptime | Evidence |
|---:|---|
| 86937.845748 | QD selector `0xc4` write, value 0 (`screen-saver-brightness` in the pinned decoder) |
| 86941.849024 | kernel HDMI receiver `vid_mute` |
| 86941.867125 | HDMI state machine `UNLOCKED`; `NORMAL to PWR_UP` |
| 86941.870950 | input lock becomes 0 |
| 86941.895293 | receiver reports 720x480; this is transient source/mode bookkeeping, not panel state |
| 86941.269531..86944.250072 | QD selector `0x128`: 292, 256, then 255 down to 207 |
| 86943.832741 | HDMI `CLK_SYNC_DET to WAIT_PKT_FILT` |
| 86943.845932 | HDMI `WAIT_PKT_FILT to LINK_STABLE` |
| 86943.863362 | first retained `CLEAR_AVMUTE` in this transition |
| 86944.133660 | status-handshake-shaped transaction starts; read reply missing |
| 86944.133711 | transaction result `-6` |
| 86944.571161 | HDMI `LINK_STABLE to CONN_VID_PATH` |
| 86944.584493 | HDMI `CONN_VID_PATH to NORMAL` |
| 86944.590930 | input lock becomes 1 |
| 86944.638818 | receiver reports 1920x1080, 24.00-style timing fields |
| 86944.771796 | DRM-DP logs mute off |

These events describe movie/source startup and recovery. The owner-report
receipt is roughly 21 seconds later. With no calibrated visible-to-black
annotation, none of the early writes or HDMI events can be selected as the
physical blackout onset.

## Kernel and vlog evidence

The END kernel snapshot adds 3,212 timestamped rows after the START
snapshot's end. Within that retained delta:

- QDF logs mirror the screen-saver write, configuration writes, selector
  `0x128` ramp, and the `m_read_cmd_no_lock ... read fail` at
  `86944.136616`.
- There is no line containing `ERR DET` or `RT Protect` in the capture-window
  snapshot.
- At `86974.537666`, a stock `sp-kpi` query logged `QD tcon status [OK], tcon
  power(1)`; immediately adjacent logs show PMIC info 0 and HSM status 0. This
  is a different query surface from the later accepted `0x10` status read and
  does not contradict it or prove absence of the fault bit.
- HDMI source state was synchronized after recovery. Repeated
  `CLEAR_AVMUTE` continued through the END snapshot, and periodic DRM-DP
  status rows showed sync 1 and the four mute fields all zero.

The unfiltered vlog contains:

- 65 `QD_TCON_OFF = 1` lines from `86930.352` through `86994.389`, roughly
  once per second. This is an AVE userspace/cached-state log, not a direct
  read of current MCU status and not proof that the TCON was physically off.
- Seven `AUTO_BRIGHTNESS_REDUCTION false` lines between `86941.222` and
  `86944.711`.
- 1,144 `spdif out mute (0)` getter returns from `86930.000` through
  `86994.996`, plus device-mute `onoff=0` messages. This is consistent with
  the owner's audio report but proves software control state, not acoustic
  output.
- 1,114 `CLEAR_AVMUTE` rows from `86943.860` through `86994.997`.
- No exact `[TCON:QDF]`, `QDFTcon`, `ERR DET`, or `RT Protect` line in this
  vlog source. QDF kernel evidence instead comes from the embedded kernel
  snapshot.

At the owner's report interval (`86965.145..86967.344`), the logs continue
to show 1920x1080 HDMI resolution polling, alternating software
stable/unstable filter bookkeeping, repeated `CLEAR_AVMUTE`, and audio mute
getters returning zero. There is no logged QDF status read at that interval.
That combination narrows the observed failure away from a simple loss of
HDMI link or software audio mute, but it does not prove the HDMI source was
rendering valid pictures or identify a panel-side cause.

## Paired post-cleanup discriminator

All three reads below were accepted by their own bounded readers, cleaned
up, and occurred on boot ID
`00000000-0000-4000-8000-000000000000`:

| Reported situation | Uptime | Read | Raw result |
|---|---:|---|---:|
| Ugoos menu visible (owner report) | 86297.39 | TCON status | `0x00000000` |
| movie black/audio running (owner report; post-capture) | 87101.04 | TCON status | `0x00000010` |
| same later condition | 87129.47 | gpiochip15 line 5, input-only | `1` |

Evidence paths and hashes:

- `overnight/hdmi-blackout-20261027a/ugoos-menu-status.json` —
  `2b1005f4368f083160d7474d8874fc8c45382f4ddb3ef63f76700f9ace7e765c`
- `overnight/hdmi-blackout-20261027a/ugoos-movie-black-status.json` —
  `89a547caac70f5990fb68236275330ffe18e0edea05f4317e41ddc6a6ec98735`
- `overnight/hdmi-blackout-20261027a/ugoos-movie-black-pin.json` —
  `51a60db891bbe892966c7c41ecb29337224a43148b92050ce6bdc32fc3b62a65`

The movie was described by the owner as *PROGRAM_04*, episode 1, started
from the beginning via Jellyfin/Kodi on the Ugoos HDMI source. Season and
exact media file are not established. The owner's historical statement that
*PROGRAM_08* and *PROGRAM_A's Farm* worked is context only; those titles were not
captured in this run.

A later attempt to retain the kernel messages around the two post-cleanup
queries is itself marked `accepted=false`: by uptime `87300.82`, the very busy
kernel ring began at `87263.671267`, so the requested `87098..87132` interval
had already rolled out. Its record is
`overnight/hdmi-blackout-20261027a/ugoos-movie-black-query-kernel.json`
(`c8354261f2fe65c0ab9e74c8b3042973c1d5a35698c9e87429d3d27a93c0cb30`).
Consequently there is no preserved raw QDF/dmesg corroboration for the
post-cleanup status call, and the managed reader's explicit
`qdf_debug_override_excluded=false` remains controlling. The independent
input-only pin value is still a separate positive observation, not proof that
the status came directly from the controller.

## Comparison with the earlier Ugoos-menu capture

The earlier `ugoos-on-20261027a.onset` run is itself rejected, for unstable
or missing physical-overlap ioctl FD attribution. It is not an accepted
control capture. Its QD decoder nevertheless offers a bounded raw comparison:

- 79 grouped transfers, no partial transfer and no decoder parse error;
- selector `0xc4` value 7 at `86151.296614`, then value 0 at
  `86159.922226`;
- no selector-`0x128` ramp in its retained trace;
- no decoder focus or maintenance-focus row.

The movie trace therefore contains a much larger source-initialization and
dimming sequence than the earlier menu trace, plus one short I2C transfer.
That difference is real in the two retained windows, but the captures differ
in activity and timing and both are rejected. It is not proof that the ramp
or short transfer caused the later black state.

## What this does and does not establish

Supported:

- The movie/source transition completed an HDMI re-lock to 1920x1080 and
  software paths continued to report sync/unmuted after the early mode
  change.
- The controller command stream included brightness/dimming writes and one
  failed query during that early transition.
- The later black/audio-running report was followed by a persistent paired
  status `0x10` and GPIO value 1 on the same boot; the earlier menu-visible
  state had status zero.
- No retained kernel/vlog line timestamps assertion of status bit `0x10`.

Not supported:

- A calibrated physical blackout onset time.
- A claim that status `0x10`, the GPIO value, selector `0xc4`, selector
  `0x128`, the one failed I2C read, or `QD_TCON_OFF` caused the black picture.
- A controller acknowledgement inferred from Linux I2C transfer counts.
- A claim that repeated `CLEAR_AVMUTE`, sync, or software mute zero proves
  visible picture or audible sound.
- A claim that absence of an error log means absence of an error. Kernel
  ring coverage is temporally bracketed but not proven complete, and the
  specific fault query was made only after cleanup.
- Any inference about season, exact episode file, codec, or media integrity;
  those require separately acquired media metadata.

The practical next discriminator is a deliberately paired known-working
title and failing title under the same bounded observer, with the status/pin
read performed only after each capture cleanup. That would test whether the
`0x10`/pin-1 pair tracks the failure state across content without treating
software logs as physical labels. This report does not authorize or perform
such a run.

## Offline method

No TV, root, network, key, getter, setter, ioctl, or control action was made
for this analysis. Work was limited to hashing and parsing already-retained
local files; offline QD decoding; exact start/end `/proc/maps` comparison;
gzip/base64 validation of the two kernel snapshots; timestamp-bounded kernel
and vlog inventories; and read-only comparison of the already accepted
post-cleanup result JSON files.
