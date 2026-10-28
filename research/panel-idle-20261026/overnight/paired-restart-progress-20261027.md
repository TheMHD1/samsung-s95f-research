# Working Apps control and paired-fault capture, 2026-10-27

## Later stock recovery-path experiment

After the owner authorized unattended tests, exactly one stock panel
off-then-on request was executed (operation41/mode2). The lower ACDET/reset
mailbox path, USB disconnect/re-enumeration and complete I2C settings replay
are observed. Pre-action ERR_DET was1; immediate and about302seconds after
helper wrapper completion, separate sequential status/pin samples were0/0
on the same Linux boot. Every helper cleaned up. No continuity between samples
or controller latch/read semantics is inferred.
The owner was asleep, so physical picture recovery remains unobserved.
The containing60-second recorder is still rejected for a duplicate AVOC
syscall-enter before the action. This does not invalidate the separately
audited raw I2C/GPIO/kernel substreams or rehabilitate the whole capture.
See [sleep investigation](sleep-investigation-20261027a/README.md),
[transport audit](sleep-investigation-20261027a/stock-mode2-transport-audit.md),
and [sequence audit](sleep-investigation-20261027a/mode2-sequence-runtime-audit.md).
No protection patch, flashing or reset loop was used. Earlier sections below
retain phase-specific plans and results as history.

Later documentation-only context, including the owner's latest left-black/no-
feedback state and the photo review, is retained separately in
[ugoos-overlay-paired-control-20261027.md](ugoos-overlay-paired-control-20261027.md).
It does not alter this record's retained measurements or claim a helper/fix.

The owner offered another working restart and failed restart comparison, then
reported “okay i want to apps now ajd it works.” The parent requested staying
on populated Apps before proceeding. This reply establishes an owner-reported
working control, but does not provide an exact onset timestamp or explicitly
confirm which power action was performed. No physical observation is inferred
from software. The direct observations are retained in
`paired-restart-20261027a/owner-observations.jsonl`.

## New working-state measurements

Two deliberate, separately bounded existing helper runs completed:

| measurement | working Apps result | target uptime | helper PID |
| --- | --- | --- | --- |
| stock controller status operation 0x1f | 0x00000000 | 83948.26 | 17962 |
| independent gpiochip15/line5 one-shot input | raw logic 0 | 83960.86 | 18272 |

Both original records say accepted/read usable/cleanup confirmed. All helper
files and the input handle were removed/closed. The GPIO request briefly
claims the line and sets input direction; no line handle spans the capture.
The current boot is 00000000-0000-4000-8000-000000000000, unchanged from
the earlier black-context queries. The kernel log retained in
`paired-restart-20261027a/good-apps-kernel.txt` independently contains:

```text
[83948.230741] QDFTcon_GetErrDetStatus[17962:TconStatusRead.]: ERR DET Status:0x0
```

The exact line contains the ordinary TCON/QDF prefix as retained in the raw
file. This is the pre-debug-override source log from the same helper PID.
Earlier accepted black-context readings were status0x10 and independent raw
pin1, acquired at different times. This establishes a useful state difference,
not by itself a synchronized onset, root cause, physical rail reading or fix.

## Working software policy snapshot

The one additional proc-memory snapshot at83983.62..83984.41 retained matching
boot, AVOC PID706/start603 and typed object identities. Its transport wrapper
initially rejected expected `dd` record summaries because the status helper's
transport validator requires empty stderr. The original record remains rejected.
No automatic requery was made. A separate offline review of the exact returned
response decompresses both maps, uses the original branch-specific validator,
and checks every expected successful dd summary. That review passes; it is
retained as `good-apps-branch-offline-review.json`.

Its sequential software values include duty207/cache207, AutoDim argument0,
AutoPowerOff count0 and Weber gain1023. Those same headline values existed in
the prior black-context snapshot. They do not explain the physical output by
themselves. The stronger new discriminator is fault status/pin0 versus the
prior0x10/pin1.

## Firmware and logging follow-up

The new emergency-loop analysis
`../tcon-research/qd-emergency-loop-output-sequence.md` proves that the packaged
RT action can divert normal main-loop execution indefinitely after action and
status/history changes. It does not prove this path executed in either incident.

The new `qd-usb-log-output-route.md` separates CDC USB diagnostic output from
the RT/common-error RAM ring, which flushes through UART-shaped MMIO40150000.
An early interim claim that DTR gates every first USB packet was corrected:
the idle first submission lacks that test, while session transitions still
alter transfer state and can clear queued text. USB is therefore not established
as the RT history source. No USB/serial endpoint was opened or driver bound.
UART host bridging remains under offline investigation.

## Next capture

The owner remains requested to stay on Apps. A new isolated 30-second observer
is being prepared and reviewed offline to avoid the earlier85-second capture's
64MiB vlog cap. It must preserve boot/daemon identity and exact cleanup checks.
The next physical transition will be owner-triggered only after preparation;
no further restart, Live navigation or protection modification has been sent.
No permanent prevention or recovery has yet been demonstrated.

## Completed owner-triggered For You test

The owner clarified the first short recording had not included a manual switch.
The parent then started distinct capture `apps-foryou-20261027c` and issued GO
in commentary after its scheduled start. The owner responded “donr”, followed
by the explicit “panel is black.” These were recorded as notes and a black
picture annotation without invented reaction/clock uncertainty. There is no
structured baseline visible-picture annotation, so calibrated physical onset
eligibility is not established. The working Apps context and actual owner
manual transition remain retained evidence; the exact physical onset is unknown.

After the capture's cleanup was verified, the same bounded helpers returned:

| measurement | after For You black | uptime | helper PID |
| --- | --- | --- | --- |
| stock controller status operation0x1f | 0x00000010 | 84517.99 | 13669 |
| independent gpiochip15/line5 input | raw logic1 | 84549.36 | see raw record |

Both records are accepted/read usable/cleanup confirmed. The raw kernel line
at84517.921691 names matching helper PID13669 and `ERR DET Status:0x10`.
The boot remains00000000-0000-4000-8000-000000000000 across working and
black samples. There was no parent power/reset/protection command. The parent
subsequently told the owner one ordinary off/on back to full Apps could be
used for viewing, because all acquisition was complete. No subsequent owner
recovery result has yet been reported here.

This is the first newly coordinated working Apps -> owner-triggered sparse
Home/For You blackout with fresh independent before/after status and pin
readings. It strengthens association of RT protection with the blackout; it
does not prove the electrical subcause, that protection initiated the loss
rather than reacted to it, or the selected packaged firmware's current image
identity. The diagnostic reads were sequential after reported light state,
not simultaneous electrical samples.

## Short recorder results and retained failures

Attempta stopped on a host-only `allow_short` keyword TypeError before any
stage/root/target call. Its empty observer and explicit host-failure note are
preserved. The corrected source is5c0e4ff02d1b54f4493dede7c7cda5eb78d2163d936b207c26f572a5ab00f7c4,
with five offline tests and independent review.

Both b (no confirmed transition, baseline context) and c (owner-triggered
For You blackout) return all seven manifest-bound sidecars, CAPTURE_COMPLETE,
empty collector stderr and verified guarded cleanup. Their original records
remain rejected by the PM parser's `pending runtime operation overlaps
physical window at drain` guard. This is not a panel failure or collector
crash report. Offline review identifies mutable printed IRQ/reschedule context
as a conservative pairing discriminator that can split otherwise matching
runtime-PM entry/return rows. A corrected offline replay is being implemented;
raw capture records and strict results will remain unchanged.

c retained sizes: trace5,722,930; meta494,781; samples42,420;
sample-errors73,798; vlog8,766,607; artifacts3,739; fds5,710 bytes.
Both short captures are below the prior64MiB vlog cap. No observer helper,
private trace instance or diagnostic GPIO handle remains from these runs.
Kernel/service/firmware trace analysis continues on the saved host files.

## Completed offline validation and controller traffic

The independent [short-capture runtime audit](short-baseline-runtime-audit-20261027.md)
checks all seven sidecar hashes, complete samples/dd/vlog coverage, identical
23-TID/FD identity, zero ring loss and successful cleanup for b and c. Its
specific PM rejection is a parser false negative: an entry and immediate
matching return have a changed printed need-resched/IRQ token. Those are
5–8microsecond pairs, not long hanging operations. Both original records
remain rejected.

The new offline-only `pm-runtime-context-replay.py` retains all other guards,
pairs runtime-PM tasks by stable task identity (CPU-specific idle), and keeps
both raw context tokens as evidence. Normal/optimized tests passed. The parent
replayed both original datasets with the final source and got exact equality
to their separately retained reports: b has1166 runtime pairs, c has460;
each has three changed-context pairs. Physical-onset eligibility remains
unestablished. No target operation or original-record rewrite was needed.

The independent [paired diagnostic audit](paired-fault-status-runtime-audit-20261027.md)
reproduces all22 authenticated root envelopes in the two new black queries
and kernel snapshot; exact command echo, model/boot/runtime/module pins,
timeouts/stderr, syscall counts and cleanup all pass. Both queries begin
after the c observer's verified cleanup.

The [transition analysis](apps-foryou-transition-analysis-20261027.md) also
reconstructs an actual in-window controller exchange: stock
`QDFTcon_GetPowerLevel` selector0x0d replies1,1,0 at84419.767,
84429.794 and84439.838, while the Apps baseline replies1,1,1. The final
reply is literal four zero bytes from the recorded Linux I2C exchange, with
complete transfer status, not simply an untouched caller output. However,
the packaged controller code computes selector0x0d as a ratio capped at100.
It is NOT a Boolean power-on flag; raw0 does not prove a module switched off.
Its formula and upstream measurements are now under offline investigation.

## Additional retained kernel window

The parent subsequently copied43911 raw kernel bytes for uptime84413..84452
as `paired-restart-20261027a/foryou-kernel-window-b.txt`, SHA256
`21048d338b089df2a860e59e5bf09872dcda32d49f292e06dc93a7454bf67a2b`. The acquisition brackets the
same boot and retains ring edges84404.004879..84898.857634, encompassing
the selected interval. Offline review verifies519 timestamped rows. These
messages include stock screen-saver brightness0 before TRACE_ARMED and host
vblank changes; neither is a measured physical blackout instant.

The first regex-based window selection returned no bytes and remains
accepted=false; replacing the selection with explicit bracket/timestamp
parsing produced the bounded copy. The precise regex/filter incompatibility
was not diagnosed. The earlier baseline window had already rolled out of the
kernel ring, so it is unavailable as a full raw-kernel comparison. There is
no absence-of-errors claim from either empty selection.

Recurring SIG11 delivery lines identify the same nonzero userspace handler;
they are not independently classified as process crashes. The host graphics
`disable_vblank` line is not proof of physical panel scanout stopping. A
source trace of that distinction is now underway without TV access.

## Owner viewing while analysis proceeds

The owner asked whether restarting and watching TV would affect the work.
All current live captures and diagnostics had finished and cleaned up. The
parent confirmed an ordinary off/on and return to full Apps could be used;
analysis now uses saved host files. A further physical recovery result is
not assumed, and no new target sampler, reset, firmware patch or protection
bypass has been deployed. Any next live experiment must be separately
coordinated around the owner's viewing.

## Follow-up that changes the next reverse-engineering step

The [selector0x0d producer](../tcon-research/qd-power-level-ratio-producer.md)
now gives the exact rounded ratio and numerator cache/cadence. Zero is an
ordinary arithmetic result, not a Boolean panel-power value or local RT
fallback. The retained1->0 controller reply is real but cannot identify a
power-off event. The RT/error field and independent pin remain the stronger
working-versus-black discriminator.

The [vblank callback analysis](../tcon-research/qd-idle-vblank-controller-boundary.md)
finds interrupt-mask bookkeeping in the matching host graphics body. Its
log alone does not establish stopped panel scanout. Its generic runtime-PM
boundary and indirect binding remain distinct from a direct TCON operation.

A more consequential correction came from positive firmware startup tracing:
each executable has a512-byte prefix. The [new address erratum](../tcon-research/qd-firmware-load-address-erratum.md)
supersedes earlier linked-address conventions. Independent audit preserves
the relative packaged RT/status path, while one absolute USB callback was
proved to target different bytes than previously decoded. The corrected
image1 scatter loader initializes its context base to0x20010000; image0's
RT checker uses0x47010000. A physical interconnect/window alias between these
separate address spaces is neither proved nor excluded. That bridge and the
correct USB notifier target are now being traced offline.

The owner has permission to watch normally while these static analyses run;
no new target action is needed or underway.


## Ugoos HDMI control preparation (2026-10-27)

The owner reported a new blackout while watching an Ugoos movie through HDMI,
then explicitly requested no collection until a coordinated repeat. Collection
resumed only after their ready instruction. The first `ugoos-on-20261027a.onset`
record covered an Apps-to-Ugoos-menu transition; the movie had not yet started.
The owner subsequently confirmed the Ugoos menu and physical panel were on.
The capture completed and cleanup was verified, but its original strict result
is rejected because an ioctl file-descriptor target changed during the source
transition. It is retained as raw evidence, not an accepted full comparison.
The later managed status query `hdmi-blackout-20261027a/ugoos-menu-status.json`
returned 0x00000000 with cleanup confirmed. It was sequential to the owner's
visible-menu report, not simultaneous physical/electrical measurement.

The first attempted raw kernel-window preservation was too late: the requested
uptime interval was 86139..86178, while the remaining ring started at
86171.948013. Only the tail overlapped. Nonempty output and the acquisition's
accepted flag do not establish complete coverage. No absence-of-errors claim
is supported. The next finite 60-second HDMI recorder is being extended to
preserve nonclearing kernel-ring snapshots locally at START and END before
large sidecar downloads. This is recorder work, not a firmware fix. The owner
is waiting at the Ugoos menu for the next explicit GO to start the movie.


The finalized HDMI recorder source is SHA256
`ab0a8d101bd1058ce4b25becb3ae5294cc29ac38a600ecf23c4dcf3658b886f3`;
tests SHA256 `05c5001dd56e1666382d5565f301bb541fbbe94cdb183fb7872102d8e8b2f4aa`.
Parent and independent review checked nested live dispatch, bounded appends,
shell syntax and unchanged cleanup. The snapshots still require separate
offline base64/gzip/content/ring-coverage validation: pipeline last-command
success alone cannot prove the dmesg producer succeeded. The original test
fixture for a bytes-count header is stale and does not validate the actual
embedded snapshot format; it is not treated as such evidence.

Live `ugoos-movie-20261027a.onset` was launched with a scheduled target near
01:42:01.100 UTC. GO was issued near the start. The owner then reported:
“done screen went dark but audio is running.” This is now the HDMI failure
case, rather than the intended normal-playback baseline. No successful
movie playback or exactly timed physical blackout is inferred. A black
picture annotation was entered at01:42:34.664 UTC; that timestamp is local
entry after the report, not a calibrated physical onset or exact message
receipt. No control/status/GPIO queries were made during the passive window.


## HDMI failure: saved results and owner media context

All7 downloaded files match the TV manifest and their corresponding partial
salvage copies. Collector completion was present, stderr empty, and quiescence
and cleanup were verified. Original acceptance remains false: AVOC maps changed.
Independent review identifies heap growth by0x34000 bytes; that observation does
not waive the original identity contract or establish valid memory sampling
throughout. This run is not promoted to a fully accepted onset trace.

After cleanup, the managed status query returned0x10 at uptime87101.04 and the
independent one-shot input pin read returned1 at87129.47. Both helpers were
accepted and cleanup confirmed, on boot00000000-0000-4000-8000-000000000000.
The preceding visible Ugoos menu had returned status0 at86297.39. The new
status/pin signature matches the previous Apps-to-ForYou black case, extending
the failure context beyond sparse Home pages. The queries are sequential and
follow the owner's report; they do not give exact physical fault onset.
A later attempt to retain the query's raw kernel lines found the ring had
already rolled past them: at87300.82 its first row was87263.671267. The requested
87098..87132 selection was empty and remains accepted=false. No raw-QDF debug
override exclusion is claimed for this new postquery lookup.

The embedded capture START and END kernel snapshots separately pass strict
base64 and gzip integrity checks and are nonempty on the same boot. START
range86456.707672..86922.083797; END86709.316088..86993.414940. The actual trace
window is86932.69..86992.85. The END ring spans those times, unlike the failed
post-download lookups. This establishes retained temporal range, not absence
of dropped kernel events or a calibrated physical-onset interval.

The owner clarified the failed playback was PROGRAM_04, episode1 starting
from the beginning, from their Jellyfin library through Kodi on Ugoos. Season
and exact media file are not yet verified. They previously watched Cars3 and
PROGRAM_A's Farm successfully. A media agent is checking the actual server
metadata; no codec/HDR cause is inferred from programme names alone. The next
proposed owner-coordinated capture is one successful Cars3 playback through
the same path, pending a visible picture and readiness confirmation. No new
failure reproduction is currently requested, and no repair has been deployed.


## Working PROGRAM_A playback comparison completed

The owner selected PROGRAM_A's Farm instead of Cars3, said they had rebooted
the TV, and acknowledged playback after GO. They then explicitly reported
“picture visible and staying on” and “and PROGRAM_A farm is running.” Those last
reports arrived after the recorder's input loop ended and are preserved in
`hdmi-blackout-20261027a/owner-playback-observations.jsonl`, with persistence
time distinguished from message receipt and physical observation time. They
are not retroactively inserted into the original observer log. GO was entered
at01:49:25.521 UTC against a scheduled start01:49:10.270 UTC; owner action
acknowledgement was entered01:50:03.910 UTC.

`ugoos-PROGRAM_A-20261027a.onset` retained all7 matching-hash files and identical
partial copies, completed its collector and verified quiescence/cleanup. Its
original result is also rejected for AVOC maps changed: the heap shrank by
0x2000. Neither original result is being rewritten. Both embedded kernel
snapshots are valid base64/gzip, nonempty, and on the same boot; the END ring
spans87305.366569..87422.531662, enclosing the trace window87361.87..87421.99.
No absence-of-kernel-events or fully validated memory-sampling claim follows.

The postcleanup managed status query was accepted with cleanup confirmed,
returning0 at uptime87576.21. An immediate raw-kernel acquisition retained a
matching PID24391 row at87576.145035: `ERR DET Status:0x0`. Its host parser
initially failed because an overly broad placeholder replacement also changed
the PAYLOAD delimiter. The original failed record is preserved; offline
extraction of its already-retained authenticated stdout recovered5982 bytes,
SHA256 `2d19ceaa3f25add9b87dbb468b5dc745f6aecf4a6938f6bd674f8df432a3250e`,
without another TV call. The separate extraction report pins its source.

The input-pin helper's original result is rejected/read_usable=false because
the shell emitted `cat: /proc/24696/stat: No such file or directory`. Its raw
managed output reports value0, successful GET and both closes, deadline0 and
helper exit0; cleanup was confirmed. This is supplemental rejected-run output,
not an accepted independent pin0 result. No retry was performed.

| Case | Owner picture report | Postcleanup status | Independent pin | Negotiated HDMI in saved logs |
| --- | --- | --- | --- | --- |
| Ugoos menu | Visible | 0 accepted | Not sampled | Not used as a movie baseline |
| PROGRAM_LABEL PROGRAM_LABEL | Black; audio continues | 0x10 accepted | 1 accepted | 1920x1080, ~24Hz, SDR metadata |
| PROGRAM_A's Farm | Visible and staying on; playback confirmed | 0 accepted + raw QDF row0 | Raw0; helper rejected as above | 3840x2160, 50Hz, HDR10+ metadata |

The media-server/session review independently identifies the actual source
files as PROGRAM_LABEL PilotS01E01, H2648-bitSDR23.976fps/DTS-HD MA, and PROGRAM_A
S05E08PROGRAM_16, HEVC10-bitHDR10+25fps/EAC3; both direct-play localMKV. Source
format and negotiated HDMI output are separate observations. SDR source alone
does not exclude switching away from HDR or some other output-mode transition.
The different modes and QD brightness commands are testable leads, not a proved
fault producer. User's broader populated-Apps versus sparse-Home behaviour
remains part of the diagnosis. No firmware/kernel/protection patch, new reset
command, or permanent blackout fix was deployed in these captures.


## Follow-up: history, source frames and controller initialization

The owner clarified that many researcher-profile titles work, including Cars3,
PROGRAM_10, PROGRAM_151/2 and PROGRAM_09. The read-only media agent inspected
97 resume rows and321 completed movie/episode rows for that profile. The
[new history comparison](ugoos-researcher-history-comparison-20261027.md) identifies
a closer file-format counterexample: completed-history PROGRAM_B
EPISODE_REDACTED is1080p/H264High/8-bitSDR/23.976025fps/DTS-HD MA5.1, matching the broad
PROGRAM_LABEL format. Historical played/progress metadata is not a physical
panel-success observation or a record of historical HDMI output/DirectPlay.
The owner's general successful-viewing report is kept as a separate source.

A bounded read-only source decode sampled the first60seconds of PROGRAM_LABEL at
1fps; seconds0..9 have mean encoded limited-range YAVG16.65, near video black.
This is a content fact, not a physical blackout measurement or established
trigger. The HDRClarkson source sample hit its resource bound before usable
metrics, so no SDR-code/PQ-code brightness comparison was made. The source
report is `ugoos-source-luminance-comparison-20261027.md`.

The [HDMI ISR analysis](../tcon-research/hdmi-clear-avmute-loop-boundary.md)
also falsifies a tempting black-only interpretation: repeated CLEAR_AVMUTE
occurs at roughly24Hz in both the failed PROGRAM_LABEL and physically visible
Ugoos-menu recordings. It is a GCP packet/pending-state marker in the recovered
ISR, not a proved panel-reset loop or fault-specific signal. Working PROGRAM_A
uses a different50Hz output and only one retained initial message.

A new [AP_RTP load analysis](../tcon-research/qd-config-rtp-table-load.md)
recovers a positive packaged initialization path that earlier direct-literal
searches had missed. The21-entry table, type4 metadata and executable loader
bind FILE183800/100 to fixed47012400 and FILE183a00/2400 to47010000. This
narrowly supersedes the prior missing-loader conclusion. RT flag/history gate/
threshold fields now have concrete packaged sources/defaults, including
initialRTbit0 and history thresholdbyte100. Live contents/current-flash
identity, external-core alias and the fault producer remain unproved. The
independent review and normal/optimized reproduction both pass. No parameter
or protection value was changed.

The controller write-payload analysis separately resolves observed F300:128:
receive bytes6..9 become BE32 scalar; the gated write dispatcher masks low10
bits and stores controller RAM2000d7c2. A previous handler was the distinct
getter, not that setter. Bounded consumers calculate derived RAM values; the
apply/RT hardware boundary remains unresolved. New reports are
`../tcon-research/qd-f300-write-payload-dispatch.md` and
`../tcon-research/qd-final-duty-controller-consumers.md`.

## Fresh host UART metadata, without opening a serial device

Two authenticated read-only root calls acquired UART DT paths, all four
UART-node properties and tty device/driver symlink mappings. Same boot,
uptime88942.12..88942.15 and88980-range; no TTY open, driver bind, mux write,
GPIO request or port setting occurred. The44-member gzip archive is1015B,
SHA256 `ce20e991a2849682f5dbedada20a3b1bede5418ec1c3c3918cc8685fad8a1c16`,
retained as `qd-uart-dt-nodes-20261027a.tgz` with full root envelopes.

| host port | DT register base | retained description / compatibility |
| --- | --- | --- |
| ttyS0 | 0x190a00 | add-debug-port property |
| ttyS1 | 0x550e00 | serdev-ctrl/direct-io/sdp-uart2 compatible chain |
| ttyS2 | 0x550f00 | explicit CEC interface with OCBox using ttyS2 |
| ttyS3 | 0x551000 | host console, as established earlier |

Allfour bind sdp-uart2; `/sys/bus/serial/devices` is empty. The prior targeted
DT corpus lacked these UART properties. This closes that corpus gap and gives
a concrete ttyS1 direct-IO source lead, not an electrical connection to the
QD controller TX. An offline audit is tracing receive/consumer/log paths.
No new display control or firmware patch was deployed; PROGRAM_A was last
reported playing visibly by the owner.


## Owner hold: no PROGRAM_B test data

The owner explicitly said they are not ready and instructed: “dont use that
data i will tell you when to rearm.” PROGRAM_B is ON HOLD. No program_b
capture was armed or launched; local inspection finds no program_b onset directory.
No session poll/current playback read was made for it. The prepared session
record is marked excluded_as_test_data=true; its historical expected format
is provenance only and is not a successful control. A fresh explicit owner
rearm message is required before any dependent recording/session observation.
Earlier PROGRAM_LABEL and PROGRAM_A captures remain preserved with their original
results and both have verified quiescence/cleanup. Offline code work continues.

The UART follow-up is now complete in
`../tcon-research/qd-uart-dt-binding-followup.md`: ttyS1 uses the ordinary
sdp-uart2 driver. The separate direct-IO serdev client requires an absent child
compatible, and no serdev bus device exists. Its source-backed receive path
would pass bytes through uart_insert_char, but available dynamic-probe/function
tracer interfaces were not found at the acquired paths. The failed first
kallsyms acquisition is preserved; the adapted metadata read succeeded. No
serial port, mux or probe was opened/changed. This is not proof that the kernel
was compiled without every tracing feature, and not a QD electrical binding.

## Offline gate and RTP follow-up during the owner hold

The [new F300 gate report](../tcon-research/qd-f300-write-gate-provenance.md)
and [independent review](../tcon-research/qd-f300-write-gate-independent-review.md)
trace RAM byte200008e8 and its literal-backed producers. Value1 suppresses
the F300 setter; value2 with EXCO+6 nonzero permits only selector0x180, while
EXCO+6 zero clears the gate and permits ordinary dispatch. Recovered producers
include the `Start PTM` / `End PTM` state machine, selector0x160's bounded
transition, and selector0x180's state writes. No live gate was measured and no
RT-to-gate edge is established. A successful host scalar transfer therefore
does not prove the staged RAM field accepted it.

The [generic-read ABI](../tcon-research/qd-generic-read-command-abi.md) and
[independent review](../tcon-research/qd-generic-read-command-independent-review.md)
positively connect ARM32 operation19 to QDF ReadOneCommand, distinct from
operation18 SendOneCommand. The exact in-scope command is
0x0000f30000000128 (hexadecimal selector0x128, decimal296), wire
f3 00 00 00 01 28 followed by a four-byte read. An earlier offline draft used
0x80 after a decimal/hex misunderstanding; it was corrected before any helper
was built or any command sent. No generic-read helper was deployed, and the
runtime/controller identity and read semantics remain separately bounded.

The [primary RTP input trace](../tcon-research/qd-rtp-primary-event-input-provenance.md)
narrows image1 event0x338 to packed12-bit RAM inputs, permitted mode routes,
an index counter above its bound, and a helper returning zero. Image1's
local2001240a store is still not positively bridged to image0's4701240a read.
The [final-duty application trace](../tcon-research/qd-final-duty-application-callers.md)
finds only calculation/policy/RAM paths among the bounded direct consumers;
the physical application edge remains unresolved. All this work was offline.

## Fresh explicit program_b rearm and actual test

The owner later explicitly said, “im ready for PROGRAM_B tell me
when you are ready.” This lifts the prospective test hold; it does not turn
the old excluded preparation into an observation. A new unique capture
`ugoos-program_b-20261027a.onset` used the unchanged60-second HDMI collector SHA
`ab0a8d101bd1058ce4b25becb3ae5294cc29ac38a600ecf23c4dcf3658b886f3`.
The recorded countdown was02:41:29.901340UTC with at least±1.132s mapping
uncertainty. A separate authenticated read found actual CAPTURE_START at
uptime90501.62, trace marker90501.630636, and private tracing_on1 at90532.58
on the same Linux boot00000000-0000-4000-8000-000000000000. GO was then sent
for program_b EPISODE_REDACTED from the beginning, roughly31seconds into the60-second window.
This leaves limited recording time for a delayed owner start; the physical
onset cannot be assumed to be in the trace.

The owner said “okay it is running,” then later “it was running but screen
just went dark.” Those exact observations are retained in
`hdmi-blackout-20261027a/owner-playback-observations.jsonl`; persistence times
02:42:38.931482 and02:45:14.514611 are not calibrated message receipt or
physical onset times. Audio was not explicitly stated in the latter message.
The second report came after the recording input window ended and is not
retroactively inserted into its observer log.

The collector finished02:43:55.851445UTC with original error
`ValueError: AVOC maps changed`, acceptedfalse and diagnostic_eligiblefalse.
Cleanup_verified and quiesce_verified are bothtrue. The original rejection
is preserved; the local raw evidence is undergoing a bounded offline review.

Two separate status reads bracket the *reports*, not a calibrated onset:

| diagnostic | execution uptime / PID | result | retained raw corroboration |
| --- | --- | --- | --- |
| `ugoos-program_b-status.json` | 90686.42 /23379 | accepted0, cleanuptrue | QDF row90686.406468, status0 |
| `ugoos-program_b-after-black-status.json` | 90804.58 /23859 | accepted0x10, cleanuptrue | QDF row90804.470007, status0x10 |
| `ugoos-program_b-after-black-pin.json` | 90827.89 /24189 | accepted independent input1, bothcloses0, cleanuptrue | gpiochip15/gpio15 line5, input-once interface |

The first query finished02:44:35.147224, before the latest persisted blackout
report; it is not independently labelled as a visible-picture control. The
after-report result and pin reproduce PROGRAM_04/ForYou fault signature.
The raw QDF rows precede optional debug override. The independent pin request
still has documented input-direction/descriptor side effects; it is not
called a passive electrical probe.

The first raw-kernel lookup failed due awk escaping in the root transport;
its response/stderr remain saved under `ugoos-program_b-query-kernel-*`. A separate
adapted lookup without backslash regexes succeeded and retained the matching
earlier row (`ugoos-program_b-query-kernel-adapted-*`). The after-black lookup also
succeeded. Neither failure nor adaptation issued another hardware query.

The media session observation failed first at local hostname resolution and
then, using the recovered documented Proxmox→CT102 route, with HTTP401. No
session payload was obtained; no current program_b item/DirectPlay/format/position
claim is made from those attempts. Original failed artifacts are preserved
separately. Owner playback reports and historical source metadata remain
distinct evidence.

The parent told the owner the diagnostics were finished and they could
restart to restore the picture if needed. No recovery control, new setting,
firmware/protection patch, or permanent repair was applied. No capture or
helper remains running from this program_b test.

The completed [program_b comparison](ugoos-program_b-comparison-20261027.md), SHA256
`4fae490c744558a965ad8619299fb70ab6a86915062e1ab927cba3cf9fbc24cd`,
independently verifies all7 matching final/partial sidecars and isolates the
sole AVOC map difference to heap growth0x3000; the original rejection remains.
There are113,096 retained/written trace events and292 grouped transfers with
no incomplete transaction or decoder error. program_b negotiated1080p/vfreq2400/SDR
and repeats exactly PROGRAM_0451-write scalar sequence292,256,255..207,
plus selector0xc4=0. The working PROGRAM_A record instead negotiated4K50/HDR
and sent two scalar values339,375. These are source/mode-policy differences,
not a causal identification; visible Ugoos-menu operation also has sustained
24Hz CLEAR_AVMUTE, so that marker remains non-specific.

The new [test evidence index](ugoos-program_b-20261027a-evidence-index.json) pins
the rearm/readiness/capture record and allthree accepted one-shot results.
It explicitly preserves the old excluded preparation, uncalibrated physical
onset, absent current server metadata, and incomplete repair state.

## Owner's wider working controls and collection finished for now

The [new owner clarifications](owner-control-clarifications-20261027.md)
record that Cars, PROGRAM_A's Farm, PROGRAM_09, PROGRAM_06, PROGRAM_LABEL and
normal researcher-profile viewing in the lasttwo weeks are owner-confirmed working
examples. This physical testimony is stronger than a bare played flag, while
actual title matching, encoded streams and historical HDMI modes remain
separate evidence questions. The coordinated PROGRAM_LABEL/program_b failures remain
explicit exceptions. The owner also confirms Samsung TV Plus generally works
with **rare, brief, self-recovering blackouts**. No fault signature or onset
trace is newly supplied for those rare incidents; persistent and recovering
patterns remain separately classified.

The owner asked if TV collection was finished for now. The parent confirmed
it was finished, all capture/diagnostic helpers had stopped and cleaned up,
and the owner could use the TV normally. There is no new TV collection armed.
Offline firmware/capture work and the requested historical media comparison
continue. The overall fault-prevention/recovery objective remains incomplete.
