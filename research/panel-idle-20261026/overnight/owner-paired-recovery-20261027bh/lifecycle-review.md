# BH lower-lifecycle and guarded post-X review

Recorded 2026-10-27 UTC. This is an offline review of the completed BH
artifacts. It made no TV, network, USB, I2C, GPIO, reset, power, UI or
controller request and did not alter or rerun a collector. The owner-visible
screensaver report remains a separate human observation; this review does not
rewrite the collector's preserved `physical_state`.

## Decision

**The narrow lower kernel/I2C lifecycle and cleanup channel passes the AU
channel-scoped criteria. The fresh post-action USB metadata also passes. One
delayed invocation of the unchanged X observer is therefore eligible, with no
retry and with its ordinary first-uncertainty stop rules unchanged.**

The whole physical/AVOC collector does **not** pass. Its original record stays
`accepted=false`, `diagnostic_eligible=false`,
`technical_capture_complete=false`, and `physical_state=unobserved-or-incomplete`.
Its error is `ValueError: pending runtime operation overlaps physical window
at drain`. No AVOC, physical absence, light-state, or observer-timing claim is
accepted from that record.

## Exact retained acquisition

The rejected collector nevertheless returned all seven declared sidecars,
`CAPTURE_COMPLETE`, empty stderr, and byte-identical complete/`partial-*`
copies. The important retained hashes are:

| artifact | bytes | SHA-256 |
| --- | ---: | --- |
| trace | 12,311,012 | `428152c29a5887d5a025cb37c5249f575e1c84e1bdd1dcfbd6c4ce84ca94b51e` |
| metadata | 494,811 | `f7b2cbafce95b67eb2e7faab8ac256e9e47a9e1800d839e4e8baf1488e170701` |
| samples | 84,362 | `70e00a709ab7b36e69aa2f5f8ef1e51fd3ac984cec4995b70c4321ed0e188465` |
| sample errors | 144,373 | `712354b055537505909d7d86757dd87e79c536d6c5e59c18175b06e21267b6ec` |
| vlog | 28,152,698 | `877f27255141d3d4c7c077c206cb48e6f7d25980fd6a1a1c55c52f5001112035` |
| kernel artifacts | 156,528 | `560353bb45c22fd7932884cb6710c8603cdc4975acc5c80207b6f00bbee31ba4` |
| FD snapshot | 5,739 | `37b883a4038e69cc5d1a3265f68e9eef87c00bd957530763d43e414846f8f7bb` |

The record itself is SHA-256
`d8bace4204b8d28e445d45a61004010f857f658419068f0f9edc7df25b72f65c`.
The kernel-start and kernel-end gzip/base64 sections both validate on boot
`00000000-0000-4000-8000-000000000000`. Their decoded sizes/hashes are:

- start: 499,526 bytes,
  `08ce15a5e289a2b27748c38160507092a5672a6d899c1cce1315bc698e13faba`;
- end: 498,420 bytes,
  `75252e3505d28a769441d87e64fc5b4da452612958c48fbbabff71d1ccc64cb9`.

The pinned offline runtime-context replay accepts only its predeclared
technical subset: 912 runtime-PM pairs, three pairs whose mutable printed
ftrace context differs (lines `62465/62466`, `70195/70196`, and
`85867/85868`), loss-free trace accounting, zero unmatched rows, and exact
sidecar/metadata identities. Device-callback and system-PM pairing remain
strict. This identifies the original drain rejection as the already-qualified
runtime-context false-negative class; it does not convert the original
collector into an accepted physical capture.

## Exactly one lower lifecycle

`bracket/dispatch.json` records one attempt with `at_most_one=true`, baseline
age 139.235 seconds, and readiness at uptime 156878.67. The fixed operation-41,
mode-2 helper record is accepted, one-shot, cleanup-confirmed, non-retryable,
and SHA-256
`953336ed4a25bfb257366d10fcb8ff53f936ae6b7c3bed2abb4d5a6f682aafce`.
Its PID is 9841. Its ioctl return zero alone remains only
`kernel_return_zero_only`; the retained lower channel supplies the following
positive boundaries:

1. PID 9841 records QDF `Reset(2)` and `Tcon Power Off` at
   `156880.856924..156880.856933`, with GPIO425 driven low in ftrace.
2. The off mailbox `[01 3f 01 01 00]` and `Reset TCON power=1 ret=0` occur at
   `156880.895072..156880.895090`.
3. USB device 47 (`04e8:2001`, `STL1 CDC and Bulk`, Samsung) disconnects and
   completes disappearance at `156881.036080..156881.042772`.
4. `Tcon Power On`, the on mailbox `[01 3f 00 01 00]`, and
   `Reset TCON power=0 ret=0` occur at
   `156882.018941..156882.043091`.
5. USB device 48 enumerates at `156882.498974`; the same vendor/product,
   revision 2.50, product/manufacturer/serial, and configuration 1 are logged
   by `156882.647792`.
6. PID 9841 drives GPIO425 high and samples GPIO125 raw zero at
   `156882.884045..156882.884069`, followed by the named init/access/display
   checks. Those names are software log interpretations, not electrical
   measurements.

The unchanged offline I2C decoder reproduces ring accounting
`108922/108922`, exactly 108,922 observed event lines,
`semantic_capture_complete=true`, zero parse errors, and zero orphan results.
PID 9841 owns exactly 346 transfers from `156882.884080` through
`156883.189794`: 233 write6/read4 and 113 write6/write4. All 346 are
structurally complete and report `ret=2`. That is a complete observed Linux
replay for the action PID, not proof that the MCU semantically accepted every
value.

There is one separate, later failed transfer in the full 60-second trace:
AVEMonDIM PID 1013 issues an `F3:01` read at `156923.244608` and receives
`ret=-6` without a reply. It is about 40 seconds after the complete PID-9841
replay. It is retained explicitly and prevents saying that every I2C transfer
in the full capture succeeded. It is not ring loss, a decoder error, an orphan
result, or an incomplete MODE2 replay, so it does not invalidate this narrow
lifecycle/phase decision.

The separately accepted helper records agree with the raw trace: status
`0x10 -> 0x00`, GPIO125 raw `1 -> 0`, and duty `256 -> 256`. These are
sequential software/bus samples, not physical luminance or rail measurements.

## Cleanup and guarded first-header eligibility

The authenticated quiesce response exits zero with `QUIESCED`. The
authenticated cleanup response exits zero with stdout `0\nCLEAN\n`, empty
stderr, global tracing off, and the trace instance, output directory, staging
directory, and expiry residue absent. Their hashes are respectively
`6fc136ad7d5a03a759693b750d428748b963f8a0b7bfe35c68f9da4793969d5b`
and
`5e56fd592b363ad5a7006c10d097087c0c2498df69fc1255f49efe2e2ae47ec1`.

The later authenticated host-only snapshot
`post-host-metadata.json` (SHA-256
`4d5974052dbd7b1d8b759f33ea2f8c317bd6d826434cf3d9f1f8d8fdc60b1ec2`)
runs from uptime `157083.35` through `157108.71` on the same boot. It finds:

- device number 48, `04e8:2001`, `bcdDevice=0250`;
- authorized 1, configuration 1, runtime active;
- interfaces 0, 1, and 2 unbound; and
- zero file-descriptor holders for the current usbfs node.

Together with the observed complete disconnect/re-enumeration, serialized
recorded action lineage, clean collector teardown, and absence of another
recorded vendor OUT, this satisfies the AU practical first-header premise for
one unchanged delayed X invocation. It is a bounded phase assumption, not a
direct observation of the controller's receive descriptor and not a global
absence proof for unknown actors.

## Physical observation and limits

The separate owner record, SHA-256
`188ef8dea81c3b0a2e565bbde58b0d4977c4495d0201a2fceb2e6f59db345f6c`,
records two owner confirmations that the screensaver picture was visible
after the action without a button press. That is valid owner-observed picture
evidence. It does not prove that MODE2 is the exclusive cause, locate the
recovery instant, establish a permanent repair, or show prevention of the
next fault.

The eligible X result will be a delayed software observation. It must retain
its own raw windows, terminal `ReadyForHeader`, release/close and guarded
cleanup requirements. It may not retroactively make the rejected AVOC record
accepted or turn owner visibility into an inferred controller state.
