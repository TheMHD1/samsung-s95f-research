# Ugoos PROGRAM_B comparison

Date: 2026-10-27 UTC

## Result

The *PROGRAM_B* capture is **rejected and remains rejected**. The
collector completed and cleanup succeeded, but AVOC's second heap mapping
grew by `0x3000` bytes during the window:

```text
START 020cd000-022d4000 rw-p 00000000 00:00 0 [heap]
END   020cd000-022d7000 rw-p 00000000 00:00 0 [heap]
```

The other 1,344 AVOC map rows are byte-identical. This is consistent with a
heap-brk change, not a library replacement, but it violates the observer's
predeclared endpoint rule and is not waived. `record.json` therefore remains
`accepted=false`, `technical_capture_complete=false`, and
`diagnostic_eligible=false` with `ValueError: AVOC maps changed`.

The rejected-run salvage evidence nevertheless gives a clear comparison:

| Evidence | PROGRAM_04, later black | PROGRAM_A, visible | PROGRAM_B, later black |
|---|---:|---:|---:|
| final HDMI report | 1920x1080, `vfreq=2400` | 3840x2160, `vfreq=5000` | 1920x1080, `vfreq=2400` |
| AVE state after relock | SDR, `MetaType[0]`, `HDR10+[0]` | HDR, `MetaType[1]`, `HDR10+[1]` | SDR, `MetaType[0]`, `HDR10+[0]` |
| selector `0x128` writes | 51: 292, 256, then 255..207 | 2: 339, 375 | 51: 292, 256, then 255..207 |
| selector `0xc4` write | one value 0 | none | one value 0 |
| `CLEAR_AVMUTE` vlog rows | 1,114 | 1 | 349 |
| grouped QD transfers | 293 | 141 | 292 |
| incomplete/failed transfer | 1 | 0 | 0 |
| separately accepted status | `0x10` after black report | `0` while reported visible | `0` before the later report was recorded; `0x10` after |
| separately accepted fault-pin sample | 1 | formal run rejected; raw output 0 | 1 after black report |

Thus program_b reproduces the measured PROGRAM_LABEL-side 1080p24/QD pattern much more
closely than the working PROGRAM_A run. In particular, the same-boot status
changed from zero before the owner's later report was persisted to `0x10`,
and the subsequent input-only fault-pin sample was 1. That is a useful
repeated discriminator. The zero query was not a proved visible-state sample,
and persistence order is not a calibrated message-receipt or physical-onset
time. None of this proves that an HDMI event, QD write, status bit, or pin
transition caused the panel to go dark.

Sustained `CLEAR_AVMUTE` is specifically **not fault-specific**. The earlier
owner-visible Ugoos-menu control contained 695 rows (587 inside its physical
window) at the same approximately 24 Hz cadence. It is therefore a
source/mode packet-pattern discriminator, not a black-picture discriminator.

## Capture and artifact integrity

The trace window is:

```text
TRACE_ARMED       90500.378907
PREROLL_START     90500.576628
CAPTURE_START     90501.630636
CAPTURE_END       90561.782582
DRAIN_END         90561.889096
```

The collector reached `CAPTURE_COMPLETE`, collector stderr is empty, and
both `quiesce_verified` and `cleanup_verified` are true. Each final sidecar
is byte-identical to its `partial-*` copy. Those lifecycle and byte-integrity
facts do not override the AVOC-map rejection.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `record.json` | 5,839 | `67a53c338b5676cbe0fec91baf4e163057fd66e4249d5f31f650b8f23452fade` |
| `trace` | 12,564,510 | `2de96df438b36355aefa7dcde904565780e3c23bc7066d448a6c10d1fd9da484` |
| `meta.txt` | 494,761 | `1112c1cda9c19e9240e53fb9ed42c90ce0800eb1f2b48a87a3fdb92937cb9349` |
| `samples.txt` | 84,840 | `8bf081420929a6faa564b924b3da3e5349694cf5e6ff2899c034c8b5153ebae7` |
| `sample-errors.txt` | 144,738 | `b4f868aa80a12d53e0b2f6fb5a3580d279f015edfacebfe8fb6c203181921355` |
| `vlog-after.txt` | 18,641,372 | `0c1cf0227b4bd7e79124e388a9fa4b8aad0668456fabdf47d273e8b54d8670c2` |
| `artifacts.txt` | 162,224 | `24d4fe72d13c3d971852dc82bacb71aecb513d6dd71d8da8ca00e49448c8c0fe` |
| `fds.txt` | 5,710 | `95434a1afcc5b01247b6d1bec5ec14275e09bf347f82a2a85d128477a254b180` |

All seven sidecar hashes above were independently recomputed from the local
final files and match the collector/record sidecar inventory; the table also
gives the separately recomputed `record.json` hash.

## Owner observations and timing

The coordinated-session record says the requested item was *Person of
Interest* EPISODE_REDACTED from the beginning. Session acquisition had two bounded
stages. The first local attempt failed before connecting because its
administrative route name did not resolve. A later recovered route issued
one actual read-only Jellyfin `Sessions` GET, which returned HTTP 401 with no
session payload. Thus no current title, stream, codec, dynamic range, delivery
mode, or transcode state was independently observed. Unlike the
PROGRAM_LABEL/PROGRAM_A pair, this report cannot compare server media metadata.

The original observer records only:

- GO after the parent had verified an active trace and marker; and
- “okay it is running,” classified at capture time as playback
  acknowledgement without an explicit picture or audio state.

The later preserved owner statement—“it was running but screen just went
dark”—was persisted at `2026-10-27T02:45:14.514611Z`, after the capture had
ended. Its timestamp is persistence time, not a calibrated physical onset or
message-receipt time. It is not forced into the earlier trace window and does
not make the rejected capture physically observed or diagnostic-eligible.

The observation log is
`overnight/hdmi-blackout-20261027a/owner-playback-observations.jsonl`
(SHA-256
`fa079a7ab98d9e569e1f211f6219c31173affb7dc91fe3f4366d9c2e2108420b`).
The first-stage failure record is
`overnight/ugoos-program_b-actual-session-20261027a.json`
(`f15e886a63881607d8400b6904f5efc8e89e329b592856805e8e9fed0a978b2c`).
The actual-GET records are
`overnight/ugoos-program_b-actual-session-20261027b.json`
(`d1373a0685728a7103fe2961ca6bee331f85932e23b31cffe905240b99bbc88c`)
and its report
`overnight/ugoos-program_b-actual-session-20261027b.md`
(`dbb8660313e4192b7cef0ee81a5f8c8cba53bda3048404ed8a87febed61c7f43`).

## HDMI and HDR chronology

The END kernel snapshot contains the complete trace-window time range. The
source/mode transition is:

```text
90546.472939  vid_mute
90546.491125  NORMAL -> PWR_UP
90546.506926  input lock = 0
90546.598899  transient 720x480, vfreq=5000
90548.697755  CLK_SYNC_DET -> WAIT_PKT_FILT
90548.711029  WAIT_PKT_FILT -> LINK_STABLE
90548.738145  first CLEAR_AVMUTE
90549.434883  LINK_STABLE -> CONN_VID_PATH
90549.448295  CONN_VID_PATH -> NORMAL
90549.454942  input lock = 1
90549.498549  1920x1080, total 2750x1125, vfreq=2400
90549.796612  DRM-DP mute 1 -> 0
```

The userspace logs change from the preceding 4K50/HDR state to SDR:
`MetaType[0]`, `HDR10+[0]`, and HDR tone-map 0. This matches the final
1080p24-style receiver timing seen in PROGRAM_04 failure, not PROGRAM_A's
4K50 HDR10+ state. It does not reveal the encoded source resolution or codec.

`CLEAR_AVMUTE` then repeats at about 24 Hz through the end snapshot. program_b's
349 rows are fewer than PROGRAM_04 count because the program_b transition occurs
late in the 60-second window; the behavior itself is the same sustained form.
PROGRAM_A has only one row, but the owner-visible Ugoos-menu control has 695
rows at the same frame-paced cadence. The source-bound analysis in
`tcon-research/hdmi-clear-avmute-loop-boundary.md`
(`21c6468f8f623edaf11f7c4fbfb783d1e392babbfe2cfc2cf8f389c9fd92e44f`)
shows that each row is an HDMI-receiver GCP event record. It is not an error
code, an acknowledgement from the panel controller, proof of visible output,
or a failure-specific signal.

The unfiltered vlog contains 65 `QD_TCON_OFF = 1` rows in each of all three
captures. That periodic userspace/cache log does not distinguish the outcome.
It also contains repeated `spdif out mute (0)` getters in each run. Those are
software-control observations, not proof of acoustic audio.

## Kernel snapshot coverage

Both embedded snapshots validate as nonempty gzip/base64 on boot
`00000000-0000-4000-8000-000000000000`:

| Snapshot | Snapshot uptime | Ring timestamps | Plain bytes | Plain SHA-256 |
|---|---:|---|---:|---|
| START | 90490.99 | 90041.003639..90491.005145 | 494,597 | `56198dd0c54ef19cf01d471f2b3aaea2fdbd4cfdc71b0d5b8862a154300181a3` |
| END | 90562.27 | 90245.219667..90562.293853 | 499,521 | `36b5d1cb912fd65cb53cb0fb417b332b43090c621bedc626698aae511061cb70` |

The START ring ends before the physical trace starts; the END ring spans the
whole trace interval. This is temporal coverage from the retained END ring,
not proof that the finite kernel ring lost no overwritten events. There is no
`ERR DET` or `RT Protect` line in the capture window. No status query was
performed in that window, so this absence cannot exclude a fault status.

The snapshot parser is
`overnight/parse-hdmi-kernel-snapshots.py`
(`545c918b3b13c6e22965c34027541f0e27ce20643378e4a48db5644977ea7eb6`).

## QD/I2C comparison

Offline decoding with `overnight/decode-qd-trace.py`
(`cc69c38cb78c94b3e044dc546ce1d0d6328b0c2f5aace308499ead0baf375be3`)
found:

- 113,096 trace events retained and 113,096 written;
- 292 grouped transfers;
- zero parser errors, zero partial transfers, and zero orphan results;
- `semantic_capture_complete=true` in the decoder's narrow transaction
  grammar; and
- 52 dimming-focus transactions.

That decoder result does not repair the observer's map rejection.

The important QD sequence is:

- one selector-`0xc4` write of value 0 at `90542.420331`;
- 51 selector-`0x128` writes from `90545.460948` through `90549.040912`:
  292, 256, then 255 down through 207;
- configuration selector groups `0x21c..0x258` and `0x31c..0x358`; and
- 186 complete `f30100000000` transaction shapes.

This exactly matches PROGRAM_04 `0xc4`, `0x128`, and configuration
pattern. PROGRAM_A instead has no `0xc4`, only `0x128` values 339 and 375,
and different raw configuration ranges (`0x49c..0x4d8` and
`0x39c..0x3d8`).

Crucially, each program_b `f3 00 00 00 01 28` transaction is a **write**: message
0 writes the six-byte command and message 1 writes a four-byte value. It is
not the proposed generic-read ABI and no four-byte reply was captured. For
example, the first transaction writes `00000124` (292) and ends with Linux
I2C result 2. “Complete” means the expected Linux messages were reported
transferred; it does not establish a controller acknowledgement or physical
effect.

## Ordered post-capture discriminator

Three later, separate readers were accepted and cleanup-confirmed on the
same boot:

| Ordering | Execute uptime | Result | Evidence |
|---|---:|---:|---|
| before the later report was recorded | 90686.42 | status `0x00000000` | `ugoos-program_b-status.json` |
| after the later owner black report | 90804.58 | status `0x00000010` | `ugoos-program_b-after-black-status.json` |
| after that status | 90827.89 | gpiochip15 line 5 value 1 | `ugoos-program_b-after-black-pin.json` |

Hashes are respectively:

- `f9c82c4d815899a6862e2ade3f81fe17ff8284ef6c3dcb476f87ba49d0b9a879`;
- `a77ed41e64631acec905697a228441b6bf761a5e4b5ac57176abdc5709532162`;
- `96158be36530bb047af7c7787365340d1dfdd992c393f4db5d4d80d7450e03ce`.

Separate retained kernel rows bind each status to the same helper PID and
value before any QDF debug-override branch:

```text
[90686.406468] ... QDFTcon_GetErrDetStatus[23379:TconStatusRead.]: ERR DET Status:0x0
[90804.470007] ... QDFTcon_GetErrDetStatus[23859:TconStatusRead.]: ERR DET Status:0x10
```

Their raw-output hashes are
`4017d44588cf10d68ae862c8122055a60518f44e9fc2aaff9673ccdf130d1d68`
and
`d9a39d33d8168a3404bba4ffb552d6dec24e4d852a07fbd4b50a112960866cfa`.

Source analysis names bit `0x10` **RT Protect**, and the independent pin value
1 agrees with the previous PROGRAM_LABEL black-state pair. The status-reader
contract still classifies only `kernel_output_written`; it does not prove the
physical producer, controller read-to-clear behavior, or that the bit caused
loss of picture. The zero result also cannot be called a visible-state sample
because the owner had not explicitly reported picture visibility at that
query time.

## What this comparison establishes

This second owner-reported failure materially narrows the reproducible
pattern:

1. Both later-black items negotiated 1080p24-style SDR and generated the
   identical 51-step selector-`0x128` ramp plus selector-`0xc4` zero.
2. Both produced sustained `CLEAR_AVMUTE`; the working 4K50 HDR PROGRAM_A run
   did not, but the visible 24-Hz Ugoos-menu control did. This identifies a
   mode/source packet pattern, not a fault-specific event.
3. Both later black reports were followed by status `0x10` and fault-pin 1;
   the working PROGRAM_A run had accepted status zero.
4. program_b supplies a zero-to-`0x10` status change ordered around the persistence
   of the owner's later black report. The zero is not a proved visible-state
   sample, and neither status read is a calibrated physical-onset or
   message-receipt measurement.

The capture does not establish which media property selected the 1080p24 SDR
path, because the current Jellyfin session metadata was not acquired. It also
does not locate when status bit `0x10` asserted: the owner's black report and
positive status occurred after the trace window. The **onset-timing gap for
this comparison** is a time-bounded, source-checked status/pin observation
that overlaps a calibrated visible-to-black report alongside the established
passive HDMI/QD logging. That is not the only unresolved technical gap:
upstream RT-protection production/application and the relevant controller
window/alias binding remain unresolved. This report does not authorize or
perform another measurement and makes no repair, recovery, or
physical-causality claim.
