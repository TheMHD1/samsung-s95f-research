# Private HDMI control roots and expanded passive capture audit

No incident-aligned cause, physical recovery, permanent prevention or
untethered root is established. This follow-up continues the full owner
objective; it does not substitute instrumentation success for a panel fix.

## Prior findings preserved

The [181-file private-resume/OCIF snapshot](private-resume-ocif-evidence-manifest.json)
has SHA-256 `cd91625dc37877be30576459d5dffd7a6b7969091d3cb36141eb22ec8be26824`.
Publication, normal/optimized verification and refusal of a second publication
passed. Independent review checked every curated row and all 494 prior rows
across five earlier snapshots. That phase includes the private PM
return/state analysis and both rejected PM captures. Those records remain
rejected and unchanged. This subsequent follow-up is outside that snapshot.

## New derivative implementation and actual passive smoke

**Independent runtime review did not accept the executed `ee4ee2b` revision for reuse.** The
raw capture is complete, but returned staging metadata uses the parent tool's
path, while the actual staged execution used the derivative's path. The host
cleanup check also used the parent trace-instance prefix instead of the
actual derivative prefix. The successful collector did remove its own
actual trace instance before emitting `CAPTURE_COMPLETE`; this does not
validate the intended redundant host cleanup or the failure paths. The
historical record's acceptance and cleanup booleans below are preserved as
tool output, not an independent clearance. See the
[runtime audit](quiescent-pm-smoke-runtime-audit.md). The independently reviewed
successor below does not retroactively validate this historical run's cleanup
contract. The hash table identifies the archived executed revision, rather than
the successor now at the working source paths.

The new [quiescence derivative](observed-quiescent-pm-onset-capture.py)
hash-pins the frozen seven-event PM observer. It retains numeric syscall-54
and `running` samples as intermediate observations, retries within the old
eight-attempt/2 ms and absolute 0.500-second prelude bounds, and requires a
later numeric non-54 point sample for every tracked TID. An unanchored trace
exit never substitutes for that sample. It uses new private namespaces.

| Reviewed artifact | SHA-256 |
| --- | --- |
| `observed-quiescent-pm-onset-capture.py` | `ee4ee2b9568f8618e8f4d16f5402ebb882f4bf380bf84326e072c03079f4b847` |
| `observed-quiescent-pm-onset-capture-tests.py` | `f4e185cf7e6aa6b7f0ec496a0a630b09cc8f89abe91ddd5d6b0540f9c7584784` |
| `pm-prestart-quiescence-addendum.md` | `b72e70e640d9b32420d14d0c9bb76c1ec62ed2f254cb5c181e6d8f06a6b98678` |

Parent and independent reviewer each passed 120 offline tests. Compilation,
default-dry execution and generated shell syntax checks passed. Review
cleared one passive five-second smoke, without full-duration or physical
inference clearance. Parent test output is retained in
`quiescent-pm-parent-offline-tests.txt`.

That single run is
[`qpm-smoke-20261026t204819.onset`](qpm-smoke-20261026t204819.onset/record.json).
The host driver exited zero, started at
`2026-10-26T20:48:19.220549+00:00` and finished at
`2026-10-26T20:48:53.791510+00:00`. The record reports:

```text
accepted = true
technical_capture_complete = true
cleanup_verified = true
diagnostic_eligible = false
physical_state = unobserved-or-incomplete
absence_claim_supported = false
human annotations = 0
```

The capture retained/wrote/decoded 10,777/10,777/10,777 events. CPU 0..3
reported zero overrun, commit overrun and dropped events. The seven PM
formats and private enable endpoints passed the implemented checks. There
were 238 PM rows (28,831 formatted bytes, maximum row 131 bytes), 119
completed runtime pairs, no malformed/unmatched PM rows and no positive
`sdp-hdmi` framework correlation. One runtime pair had the real idle PID-zero
identity; this run therefore exercised that correction. The framework rows
included MMC activity, not proof of the panel's private callback execution.
Missing framework correlation cannot exclude Samsung's private dispatcher.

| Marker | Trace clock |
| --- | ---: |
| TRACE_ARMED | `69322.564756` |
| PREROLL_START | `69322.785861` |
| START | `69323.820136` |
| END | `69328.884180` |
| DRAIN_END | `69328.991193` |

The prelude was 0.221105 seconds, declared pre-roll 1.034275 seconds and
physical-eligibility window 5.064044 seconds. All 23 tracked AVOC TIDs had
terminal numeric non-54 anchors; none required an intermediate syscall-54
retry in this particular run. Consequently actual retry behavior remains
supported by offline adversarial shell/parser tests, not a fabricated live
retry. No tracked AVOC fork/exit or relevant FD change was reported. This
run contained no start-boundary or window-tail pair; those cases retain their
separate offline evidence limits.

The vlog had 32,550 ordered records with the required endpoints, a 0.01-second
maximum observed record gap and a natural exit. Sequential samples met the
declared bounds. Software continuity is not emitted-light evidence.

Authenticated root cleanup returned exit zero, empty stderr and stdout
`0\nCLEAN\n`. It checked the correct derivative output/staging directories
but the wrong parent trace-instance prefix; its result cannot be promoted
into full cleanup-contract acceptance. No capture remains running from this
experiment, and no automatic retry or longer capture was launched.

A separate fixed [read-only residue verification](verify-quiescent-smoke-residue.py)
then checked the six exact actual/parent trace, staging and output paths.
Its authenticated same-boot response reported every path absent and global
tracing `0/nop` at both endpoints. Evidence is retained in
`quiescent-smoke-residue-20261026`. This later absence check establishes the
specified residue state at that check; it does not repair the earlier
metadata mismatch or prove that a failing collector would clean correctly.

## Independently reviewed offline successor

The rejected source/tests/addendum are preserved in
`observed-quiescent-pm-rejected-ee4ee2b`. The successor source has SHA-256
`8390e85eff9a40fe774c5e2bd7488ebaaa703c734af20a19fd0a780b58cdc43f`,
tests `ae330c948f7f66cb229ee88e7eb44fbf45d4cd92b914a9da439a3b5213ecb2e8`,
and addendum `595e0faa6fb6eefb2193a28b1c812b2482a4a016e1589c0dc0817e5b994cc92e`.
It normalizes all ancestor namespaces at the terminal transport boundary and
validates the returned staging path. Independent review passed 121 offline
tests, compilation and four duration-mode shell syntax checks, including
mocked public success/failure staging and cleanup paths. It cleared only a
future bounded passive five-second use; no successor target run is established
by this review, and no full-duration or physical diagnostic clearance follows.

## Control-producer investigation

New offline work recovered a V4L2 extended-control route in the HDMI switch
module to the private suspend/resume helpers. The exact controls are
`0x00a009be` and `0x00a009bf`, within class `0x00a00000`. Parent review
caught and rejected an initial transcription that incorrectly evaluated a
shifted immediate; corrected verification must derive these
values from the instructions and table arithmetic. The original incorrect
numbers are not runtime evidence and must not be used in a request.

The corrected static invocation package and the scoped 41-file userspace
producer census independently cleared review. The census covers exact literal
and specified ARM AL-condition/Thumb immediate-construction forms, not all
possible ways to compute a control ID. No control was submitted. The missing connection is
which userspace caller sends those controls, under which policy conditions,
and whether that happens at the owner's physical blackout. The separate
private-PM state/return report establishes plausible suppression mechanisms,
not that this control route or any callback caused the symptom.

The exact live-mapped `/usr/lib/libhdmi-control.so.0.1` was then copied through
13 fixed read-only chunks and independently reconstructed by the parent from
the raw authenticated responses. The 415,124-byte file has SHA-256
`067ddb8f639f8e91d02524f0820fb3a56e2d9f174d0f3f75a5dec963f7339410`.
The initial [library trace](../tcon-research/hdmi-control-library-producers.md)
finds no raw private control literal. Source/background/foreground wrappers
instead dispatch through runtime backend callback-table slots. Those callback
bindings remain unresolved; neither a direct control producer nor a UI-to-panel
causal chain is established by this initial library analysis.

## Exact implementation libraries and policy follow-up

The [main-library acquisition audit](private-hdmi-library-acquisition-audit.md)
independently cleared all 13 chunks for offline analysis. The follow-up
[backend acquisition audit](hdmi-backend-acquisition-audit.md) independently
cleared two additional exact versioned implementations, reconstructed from
four raw authenticated chunks:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `libhdmi-input-control-impl-sec.so.0.1` | 29,650 | `5f822a6f297e1d24a65ad8dd4363a1dcf43b7d15f405fa7799ddf20f01410126` |
| `libhdmi-control-impl-sec.so.0.1` | 75,882 | `5eaef7e92eac9468bf41073ccece56a64a70339c3056c3ca2b62391171f4d2a1` |

These were file reads, not library loads or calls. Metadata positively maps
the control implementation into AVOC at one sample. The unversioned loader
names are symlinks to unexamined `.so.0` intermediates, so acquisition does not
prove their final resolution or a live input-backend binding. The first
metadata attempt exited before its two silent file tests could be
distinguished; it remains preserved, not an absence result.

The [DPMS control chain](../tcon-research/hdmi-control-dpms-chain.md) is now
independently reviewed through its v2 correction. The control implementation
statically builds callback slot `+0x38` for the DPMS implementation, constructs
control `0x00a009d5`, and sends it through `/dev/video28`. The kernel switch
case requests a one-byte copy, ignores the copy result, and calls the API
notification. Its resolved handler `NotifyDpmsType` writes `s_dpmsType` at
`.data+0xa38`, logs and returns zero. A failed one-byte copy can still notify
zero. No failed copy or incident execution is established, and this bounded
notification body is not a direct physical panel-off operation.

The [DPMS suspend-policy trace](../tcon-research/hdmi-dpms-suspend-policy.md)
then finds positive consumers of that byte: conditional branches choose
external-mode call arguments `2` when the byte equals `1`, otherwise `1`.
Those mode returns are discarded. The cold wrapper returns zero after a
present callback and -19 for absent operations/slot; the enclosing private
suspend caller ignores that result and returns zero. Both lower mode helpers
normalize a negative transfer result to INT_MIN. Independent review caught
and corrected the earlier null-return/negative-return descriptions, then
cleared the exact revised package. Actual runtime flags, mode meanings,
transfers and a blackout connection remain unproved.

The [input implementation trace](../tcon-research/hdmi-input-implementation.md)
statically identifies source and foreground/background callback bodies, with
an implementation-table construction and V4L2 operations. Independent review
cleared the final source and listing after requiring exact PLT/GOT identity
proof. No input live-table binding is claimed. Its foreground/background
device association and kernel dispatch are separate follow-up questions;
the private suspend/resume controls must not be substituted by name.

A new [control-backend pointer reader](read-hdmi-control-binding.py) is
default-dry and has not run on the TV. Its
[review hold and remaining checks](hdmi-control-binding-reader-status.md)
require complete command fixtures and raw-result validation before a
single finite read-only process-memory sample, with exact file identities,
boot/PID/start/maps guards, repeated flag/table/callback observations and
strict four-byte reads. Added source/entry-word guards are not independently
cleared yet. Eight local shell tests cover partial reads,
pipeline errors, mapping boundaries and invalid addresses. A later saved-response
parser and complete generated-command harness now pass local normal/optimized
checks; independent review is pending and the reader remains unrun. It would establish
only a sampled callback binding, not physical panel state or fault causality.

The [capacity assessment](quiescent-pm-capacity-assessment.md) independently
cleared after correcting the 238 PM rows to 224 pre-roll and 14 window rows.
It is planning evidence and does not authorize a long capture or supply
physical/private-path coverage. The later short successor capture is recorded
below; no display-control experiment was launched.

## Owner returns and corrected short capture

The owner asked how far diagnosis had progressed and then reported being home
and available to observe a test. Current physical picture state was requested
and remains pending; presence alone is not a visible/black observation.

One previously cleared five-second passive successor was executed with label
`qpm-home-smoke-20261026`, using unchanged source SHA-256
`8390e85eff9a40fe774c5e2bd7488ebaaa703c734af20a19fd0a780b58cdc43f`.
Its [record](qpm-home-smoke-20261026.onset/record.json) spans host UTC
21:32:34.444630 through 21:33:12.143292 on 2026-10-26. The command exited zero;
the record reports technical capture complete, accepted and cleanup verified.
All 10,521 written trace events were retained and decoded. The producer log
has 38,571 records covering uptime 71977.002 through 71986.996, with maximum
gap 0.010 seconds and natural source exit zero. No key or display control was
sent. There are zero physical annotations, so diagnostic eligibility remains
false; these results validate instrumentation rather than a blackout cause.
The [independent runtime audit](quiescent-pm-home-smoke-runtime-audit.md)
confirms the corrected namespaces, sidecar hashes, process/thread/FD identity,
complete trace accounting, seven PM formats, and actual cleanup. Together with
the capacity assessment it clears one separately coordinated 85-second run
of the unchanged source under the existing limits, with no automatic retry.
This is workload-limited instrumentation clearance, not proof of physical
state, coverage of all proprietary paths, or a repair. The numeric-54 retry
branch was not exercised in this actual smoke.

The separately [reviewed input/kernel boundary](../tcon-research/hdmi-input-kernel-control-boundary.md)
now distinguishes two handle descriptors: source falls back to video28,
foreground/background to video21/22, and callers can supply either descriptor.
The switch requests minor 28. Its default -EINVAL for the foreground/background
IDs is conditional on requests actually reaching that switch; it is not proof
those operations fail on the actual target device. No live association or
incident execution is established.

## Next evidence requirement

### Actual owner-observed recovery request and restart identity

The owner returned, reported the panel black, and explicitly said no
optimization cycle was running. The reviewed standalone
[stock request](stock-unmute-once.py) was then executed once. The
[raw evidence and interpretation](stock-unmute-once-20261026/interpretation.json)
and [independent runtime audit](stock-unmute-once-runtime-audit.md) establish:
authenticated persistent root; stable boot/AVOC identity and source hashes;
both baseline mute getters zero/zero; exactly one public `SetPanelMute(0)`
reply zero with D-Bus exit zero; both post-getters still zero/zero; no retry.
The request was bracketed at TV uptime approximately 72719.20--72719.24.
The owner's subsequent report was "stYed black". Therefore this stock request
did not demonstrate physical recovery. It does not establish whether lower
I/O ran or was skipped. Chat observations have no calibrated reaction/clock
bounds and are not direct local-observer annotations.

A later filtered retrospective log query returned zero log rows for the
requested 72717--72723 interval, when executed at 72782--72784. Historical
coverage was not established, so this is failed diagnostic coverage, not
evidence of absent gate/fault/maintenance activity. No trace, remote file,
watchdog, persistent configuration or power action was created by this test.

After the owner performed their usual restart, For You appeared and the
physical picture disappeared within about one second. A fresh
[identity response](owner-restart-identity-20261026/client-stdout.json)
shows unchanged Linux boot `00000000-0000-4000-8000-000000000000`, AVOC
706/start603 and deviced675/start560 at uptime72944.63, with global tracing
zero/nop. Thus this particular reported restart did not restart Linux or
those daemons. A passive collector can potentially span the same display
power cycle. A true OS reboot would still invalidate its lifecycle assumptions.

One independently cleared 85-second unchanged collector run was then executed
across one owner-performed ordinary TV off/on, starting from the reported black
state. This differs from the earlier Apps-to-sparse-page protocol. The run is
`owner-power-on-20261026a`; rendered collector SHA-256 is
`236a5f93f11c60f18fd7adf36f0818884f2a7e88767af1f79c69f887a510f3cb`.
A separate passive readiness read verified private tracing on and the actual
START marker before the owner was instructed to act. The owner reported
performing the cycle, recurrence of the brief-picture-to-black failure, and
audio staying on. Those receipts arrived late relative to scheduled END;
there are only two chat-receipt/instruction notes in the collector, and no
calibrated local picture annotations or invented timing uncertainties.

The [original record](owner-power-on-20261026a.onset/record.json) is rejected:
completion manifest missing, technical/diagnostic/cleanup flags false. Initial
quiesce and cleanup each stopped at the collector-group check, before output
deletion. A later read proved the collector and group absent, private trace
absent, same Linux/core identities, and global tracing zero/nop. Original
files remained available for rescue. The 64 MiB capped vlog is a strong
shutdown-failure lead, not proof of the sole failure site.

The [rescue audit](owner-power-on-rescue-audit.md) independently replayed all
354 fetches, original/compressed hashes, gzip checks, decompressed sizes and
byte identity for all seven saved sidecars. Original files are preserved on
the host in [the retained directory](owner-power-on-20261026a-rescue/retained).
The trace has all five markers and all 172,200 written events, with zero
per-CPU overruns/drops. START is 73052.233218, END73137.840506 and DRAIN_END
73138.033049. Final boot/process/pointer/map/FD/TID and vlog-completion blocks
are absent, so valid trace inventory cannot promote the whole run to accepted.

The bounded [I2C decode](owner-power-on-20261026a.qd.json) contains 264 complete
syntactic transfers and no parse errors. Positive writes include deviced
mute-one at73132.587104, dimming request207 at73136.593759, deviced mute-zero
at73136.725190, and AVEMonDIM screen-saver-brightness-zero at73137.318289.
Linux transfer success is not MCU acceptance or emitted-light proof. The
brightness-zero command already occurs in prior visible wakes; it is not a
newly diagnosed cause. Logs and Q/monitor samples require separate analysis.

After independent host rescue verification, a separately retained
[guarded final cleanup](owner-power-on-final-cleanup-20261026/client-stdout.json)
completed with authenticated root, status zero, empty stderr and output
`0`, `CLEAN`, `RESCUE_DIRECTORY_ABSENT`. It removed the owned original
output/stage paths and compressed rescue directory and verified private trace
absence. It does not rewrite the original rejected cleanup flags or undo the
missing end-state evidence. No further capture or control was run.

The complete short data capture supports its bounded parser/data path. The
corrected successor has now run and passed independent runtime review. An
owner-observed visible-to-black capture still needs
appropriate duration/resource review, physical annotations and aligned
positive output/controller evidence. Compare populated Apps with one
controlled sparse-page transition while preserving source, composition,
settings and sensing state as far as that particular comparison permits.
Live also changes video/source state, so source and image-content changes
must not be conflated. The rare Ugoos/playback interruption with paused audio
remains a separate pattern requiring its own capture.

The desired end state remains a tested prevention/recovery mechanism across
reboots, useful selected apps/casting and documented rollback—not a quiet
log, success return, root shell or full-menu workaround alone.


## Subsequent decoded wake evidence and current diagnostic candidate

The [mute-readback correction](../tcon-research/qd-mute-readback-wire-correction.md)
resolves an earlier command-prefix error from exact QDF instructions: stock
mute-status read uses `F3 00 00 00 01 64`, not prefix `80`. The untouched generic
decoder's semantic flag therefore misses this read. A separate hash-gated
[extractor](trace-qd-mute-readback.py) locates one completed read in the rescued
wake trace at73137.280043 returning `00000000`. It follows mute-zero and precedes
SS brightness-zero. This is a positive wire response, not emitted-light or
physical-onset timing evidence. The previous public unmute test had no such
trace and cannot inherit this transaction evidence.

The [sample-state analysis](owner-power-on-state-analysis.md) decodes370 M rows
and85 Q rows. All38 monitor words remain unchanged, including historical off
latch1, fault0/0/0 and recovery2/0/0. The power index changes lcdon1 to standby3
and back to lcdon1; OP+24 changes0/1/0 without assigned semantics. Duty/cache207,
Weber1023/1023/0 and AutoDim argument0 remain stable. Last Q completes before
final unmute, and last M precedes the final readback/brightness transaction.
No post-black conclusion can be drawn from that missing tail. The
[log analysis](owner-power-on-log-analysis.md) treats capped binary-unclean vlog
as a positive-prefix source, not complete fault coverage.

The [stock error-query ABI audit](../tcon-research/qd-error-status-read-abi.md)
reconstructs a possible next diagnostic query: ARM32 ioctl c010749f, op31,
four u32 words, status output at+4. Several skipped paths return zero without
writing output, so a sentinel is essential. Open/close have no TCON driver
power/reset/release callback. The actual query performs I2C and proprietary
read-to-clear semantics remain unknown; this is not a passive memory read.
No controller query or repair has yet been performed from this new helper.


A fresh one-shot passive process-memory snapshot was then attempted. The `a`
wrapper wrongly escaped `tr`, deleting literal `n` characters from compressed
map encodings. That record remains rejected, with source and raw transport
preserved in `post-wake-branch-20261026a/`; it made no TV control change.
The corrected `b` command preserves wrapped base64 and decodes it on the host,
then reuses the frozen branch validator. After independent pre-run review,
one new read completed at uptime74541.43..74542.35 (0.92s), preserving boot,
AVOC706/start603 and the exact base QDDimming/backend chain. Its software
snapshot is accepted: working duty207/207, backend cache207, AutoDim argument0,
AutoPowerOff count0, Weber gain/target/count1023/1023/0. This fills a later
software-state gap but is not an instantaneous onset sample or emitted-light
observation. The owner's last physical report was black with audio; no new
calibrated physical annotation is embedded. The [independent runtime audit](post-wake-branch-audit.md) replayed both
map archives, the frozen validator and all raw DD accounting; it confirms
the accepted software snapshot and preserves the earlier rejected `a` record. No setting/control was sent.


The [upstream SS-brightness trace](../tcon-research/owner-wake-ssbrightness-upstream.md)
now distinguishes a base RoseMQD logo-detection caller from an MNT screen-saver
caller. The baseline active base backend's screen-saver virtual slot is a stub;
therefore the AVEMonDIM task label alone cannot attribute the retained zero to
that generic vsync route. The actual upstream caller remains unresolved.

A new managed controller-query package has been built offline but is **on
hold** for a concrete helper-lifecycle correction: an initial failure trap
could signal a reused child PID. No status ioctl has run from that package.
The query remains planned as one ordinary operation31 with sentinel, with no
retry or physical-health inference from a zero word.


The [error-word interpretation](../tcon-research/qd-error-status-bit-interpretation.md)
separates bits0..7 (EL OCP, EL OCP2, BLACK OCP, FFC Connection OCP, RT Protect,
DSI Protection, AC_DET low, PMIC fault) from the independent GPIO assertion that
drives the AVE monitor's stock retry/reset predicate. The observed historical
`qd_tcon_off=1` takes an early report/return before both current GPIO/status
checks. Thus stable monitor counters during this wake are not proof of healthy
fault inputs. No monitor latch, retry count, protection or recovery entry has
been altered or invoked. A transient rearm remains only an offline assessment.


### Controller query attempts and retained failures

The managed helper was independently reviewed and parent-operated. Attempt
`managed-tcon-status-read/result-20261026a.json` stopped after one authenticated
preflight request: target newline-format printf emitted literal backslash-n,
so the parser rejected anchors. No staging/helper/device call occurred.
Original source/manifest/review were archived before the echo-only correction.

Attempt `result-20261026b.json` passed preflight, private creation and five
staging calls. Its execution RPC returned exit1 with no output. Read-only
inspection verifies all staged hashes, a ready tuple PID896/start18751314,
zero-byte stdout/stderr, and an existing zero-byte GO file. The guard expected
stat `%F` to be `regular file`; this target reports `regular empty file`.
Because GO was created before that failed guard, the child may already have
started the CLR. No managed banner or ioctl result was retained: device-query
issuance is unresolved and no returned fault word can be claimed. This is not
a fresh-zero result, nor proof that no query occurred. The original cleanup
also rejected the empty-file wording.

A separate [guarded cleanup](managed-tcon-status-read/failure-b-cleanup-corrected/client.stdout)
verified the original child generation not live, found no process command line
for this private DLL, checked exact file allowlist and numeric owner/group/mode,
removed only those seven files, and verified the directory absent. It returned
authenticated root/exit0 with `ORIGINAL_CHILD_NOT_LIVE`, `PRIVATE_REMOVED` and
empty stderr. A preceding cleanup script failed locally before starting the
root client due an embedded NUL in its command; it made no TV request. No
original rejected acceptance/cleanup flags were rewritten.

The empty/nonempty regular-file checks are being corrected offline using
`test -f`, no symlink, and numeric owner/group/mode. A deliberate subsequent
ordinary query, if reviewed and executed, must retain that b may already have
issued one read; it must not present itself as the first-ever transaction or
ignore unresolved controller read-to-clear semantics. No reset, monitor-rearm,
panel power, protection, factory, or firmware operation was sent.


### Positive controller-query indication

After independent review of numeric file guards, one deliberately new `c`
query completed accepted with confirmed cleanup. It returned **0x10**, bit4
labelled **RT Protect** by this firmware. A subsequent dmesg read positively
matches raw `QDFTcon_GetErrDetStatus[3216:TconStatusRead.]: ERR DET Status:0x10`
at75262.252253, before the optional debug override. See the
[actual result and limits](tcon-status-actual-result-20261026.md).
No simultaneous bus trace or time-calibrated physical onset was captured;
live-versus-latched controller semantics remain unresolved. This is a useful
fault indication, not a proven initiating cause or recovery. The prior b
attempt remains potentially consumed. No protection/reset/power change or
monitor rearm was performed, and no additional status query was repeated.


### Black-context GPIO query and prepared visible control

A separately reviewed ordinary operation0x1d query completed once after the
owner confirmed the panel remained off. It returned u32/i32 **1**, ioctl0,
all errno0, with successful postflight and cleanup. The stock monitor treats
nonzero as its fault predicate, distinct from controller RT Protect0x10.
See [actual GPIO result](tcon-gpio-actual-result-20261026.md). The immediate
filtered dmesg had zero matching rows, so no pre-debug electrical-raw claim is
made and no missing-log negative inference is drawn. No state/control change
beyond the stock getter's temporary GPIO request/input/free was sent.

The parent then requested one ordinary short-press owner off/on and populated
Apps control, with no hold/unplug/repeat, and is awaiting physical confirmation
before any new control-state reads. No permanent repair has been deployed.


### Standard GPIO route assessment while physical comparison is pending

Actual metadata exposes GPIO cdev15 / bankgpio15 / offsets0..7 and binds ERR_DET
to offset5/global125, with no existing sysfs export. The
[route assessment](gpio-direct-route-progress.md) records the actual reads and
new exact-Linux ABI caveat: both cdev input requests and sysfs export also set
persistent-state configuration, unlike the reviewed stock getter. Neither
route was invoked. The bound bank driver is sdp-pinctrl-v2, whose config
callback must be understood before using that route as independent raw input
provenance. A passive later kernel-log read had zero matches; no missing-event
or physical-state conclusion is made. The standard input-only routes cannot yet be treated as having the same
side effects as the stock getter. Visible-control physical confirmation is
still required before the prepared comparison queries.


### Paired-Image GPIO callback closure

The [exact driver analysis](../tcon-research/sdp-pinctrl-v2-config-binary.md),
independently checked, resolves the preceding persistence-callback gap for
the acquired paired kernel Image: the gpio15 driver's `set_config` slot is
null. Descriptor flag changes remain, and input direction still performs
register writes. Live kernel text identity has not been measured. No cdev
line request or sysfs export was performed; a metadata-only compatibility
probe is being prepared separately. Owner clarified that the panel is off;
visible Apps control is still unconfirmed.


### Independent ERR_DET value now sampled

A reviewed standard-cdev metadata probe passed first, then a separately reviewed
one-shot input sample returned **1**, bypassing QDF cached-power/debug branches.
See [actual result](errdet-direct-actual-result-20261026.md) for exact raw result,
identities,11calls, close/cleanup and non-passive direction/software-flag side
effects. This strengthens fault-input provenance; no simultaneous physical
annotation, visible control, initiating cause or repair is established. No
power/reset/protection control or retry was performed. Earlier vendor getter
provenance remains as originally qualified.


### Controller assets and shared-log follow-up

The [controller follow-up](controller-fault-followup-20261026.md) records exact
retry predicates, new factorydata assets and one bounded shared-log read. The
newly analysed read-count defect changes the permitted buffer size; actual b
uses4KiB reads, preserves the rejected wrong-module-path preflight a, verifies
all1,477 transferred bytes and cleans up. The changed log contains additional
mailbox text, not an aligned fault or reboot diagnosis. No power, protection,
reset, firmware apply, or extra GPIO query occurred.

### SSB readback and loaded-provider distinction

The [same follow-up](controller-fault-followup-20261026.md#ssb-acquisition-boundary-and-current-registration-metadata)
now records the embedded USB driver, update-verification reader and separate
fixed5MiB backup branch. The latter sends request headers and creates/truncates
an output file; its controller storage identity and read semantics remain
unknown. Exact metadata finds the provider module loaded and a USB device
matching its static04e8:2001 criterion, with no exposed named SSB nodes/classes
or matching `*ssb*` driver directory. USB parent-driver metadata does not
establish interface-child binding. No driver registration, device open,
USB request or power/control operation was performed. This narrows an
acquisition route, not the cause of the blackout. Latest owner report remains
panel off; the visible Apps comparison remains pending.
