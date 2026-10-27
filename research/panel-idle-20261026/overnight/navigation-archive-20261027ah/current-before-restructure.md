# Samsung S95F: current investigation entry point

This is the mutable navigation page for the owner's TV investigation. Historical evidence snapshots and the files they fingerprint are preserved separately. No permanent blackout fix or physically verified recovery/prevention has been established. Root is host-assisted; untethered persistence remains unverified.

New offline source/invocation work (2026-10-27): the fixed source has a
minimum observed four-lane layout, each lane 16 u32 words, not just the three
used by the first helper. The fourth lane is copied to a selected-package CPU
RAM literal and a stack array; neither is qualified as a live diagnostic
buffer here. The [reviewed source trace](panel-idle-20261026/overnight/ap-table-source-20261027y/table-source-trace.md)
now associates the full table range with the enclosing packaged `Pre-PD`
record. Its bounded code census finds readers but no runtime producer; field
names, units, content relationship and live loading remain unresolved. [Invocation trace](panel-idle-20261026/overnight/ordinary-invocation-20261027aa/invocation-findings.md)
recovers descriptor28 registration and the matching stored-vector callback.
Its debounce threshold30 is an invocation count: continuous qualification
from counter0 first setsF0 on call31. No frame/second cadence, active vector
or physical IRQ source is established. Both local verifiers pass normal/-O;
independent reviews are clear after corrections.

The [reviewed stored-value comparison](panel-idle-20261026/overnight/pre-pd-stored-values-20261027ab/stored-values.md)
finds the packaged table region allzero and the companion's exact16descending
constants960..0. These are stored facts, not live pixel/luma units or runtime
source values; they alone do not reproduce W's nonzero returned sum mirrors.

The [incident evidence comparison](panel-idle-20261026/overnight/incident-separation-20261027z/incident-comparison.md)
keeps brief recovering/audio-pausing glitches separate from persistent
black/audio-continuing incidents. No synchronized technical capture of a brief
event exists. program_b's raw capture ended before the black report was persisted;
its absence of a transfer error in that earlier window does not exclude an
onset-time error. No TV command, write, flash, protection change or physical
observation occurred in this offline follow-up.

Latest evidence checkpoint: [S–X manifest](panel-idle-20261026/overnight/rt-passive-observer-20261027x/evidence-manifest.json)
freezes 98 files / 1,719,391 bytes, SHA-256
`4a68594f94a3ad5138c144cee17b4c86251efc1554ab7954df0ffa5ffbbba235`.
Normal, optimized and [independent checkpoint verification](panel-idle-20261026/overnight/rt-passive-observer-20261027x/checkpoint-review.md)
passed, including 113 unchanged M/N/O parent entries. The [final analysis review](panel-idle-20261026/overnight/rt-passive-observer-20261027x/analysis-review-closure.md)
identifies the accepted alias-qualified decoder outputs and superseded outputs.
The owner permits firmware changes if necessary; no flash, code patch, protection
bypass or new persistent root modification was performed in this checkpoint.

Newest accepted X passive-recorder run (2026-10-27): production native and
supervised wrapper are built, independently reviewed and now validated on the
TV at126642.16 on the same boot. The result correctly reports AlreadyFaulted,
OnsetMissed; it is not a new event. Six fixed reads/12exact transfers ended
ReadyForHeader with clean release/close and stage removal. NewH data has
A=[44,0,0,0,0,0], allq0, mode1history[6,0,0,6]. M/C/L/R repeat earlier hashes.
Under the qualified CPU aliases and selected-code interpretation, sampled
aa0/ac2 andbc7=1 would select mode1 alternate40; A1=44 matches the shared
latch44 and satisfies44>40. H returned mode6A0 before L returned latch54;
this sequential difference does not prove simultaneous divergence or staleness.
C/H/L/R CPU meanings remain conditional; no live core tag was sampled. See [X runtime
audit and limits](panel-idle-20261026/overnight/rt-passive-observer-20261027x/runtime-review.md).
No reset, write, physical observation or repair occurred. No finite collector
remains running. The instrument is ready for a future clean-start/onset
capture, which remains untested on a live new transition.

W aggregate analysis also reproduces the first-helper output: configured
thresholds7464960 equal90% of reported3840x2160, and sampled sums are about
8.25million with maturecounter30. This supports a testable distribution/
content hypothesis; table producer and physical units remain unproved. See
[exact arithmetic and hypothesis boundaries](panel-idle-20261026/overnight/ap-exco-input-snapshot-20261027w/aggregate-interpretation.md).

Newest accepted W input snapshot (2026-10-27): three fixed reads completed
at125699.16 on the same boot. Both pointer anchors match; ordinary824 and
derived1004 bytes are retained. Currente6=1,2fc=0,e2=30/e0=30 andderived3d8=1
numerically reproduce the selector through the first-helper output. This
closes the earlier missing late ordinary-input observation, without recovering
V6's event tuple. All six transfers, ReadyForHeader, release/close and exact
stage cleanup passed; the independent runtime audit is clear. See [W live
findings and limitations](panel-idle-20261026/overnight/ap-exco-input-snapshot-20261027w/capture-findings.md).
No reset, gate/threshold/protection change or physical observation occurred.
The new passive observer's native candidate is built and reviewed offline;
its supervised host wrapper is still being completed and is not deployed.

Fresh state check (2026-10-27): Linux is still on the same boot. One reuse
of the reviewed fixed two-window reader ended cleanly at uptime124639.19.
All320bytes match the earlier117834.25 capture exactly: RTfault1001,
loggergate0 and context0/54/44. The113.4-minute separation corroborates retained
state, not continuous immutability or an event-time tuple. Generic stock
`QD tcon status [OK]` and HSM0 do not clear this directly sampled fault.
Repeated SIG11 rows were attributed to the living stock csfs process, not
proved panel/module reboots. See [fresh observations and limits](panel-idle-20261026/overnight/current-host-health-20261027v/findings.md).
No reset, setting change, physical observation or repair occurred. All four
USB transfers, ReadyForHeader, release/close and stage removal passed.

New offline S/T traces: the ordinary selector is fed by stateful debounced
conditions, whose live inputs were absent from earlier small reads. Stored
zero inputs are not runtime invariants; an earlier helper recomputes X before
the later condition. The event helper ORs action4 into mode buckets; late
bucket2486=7 is compatible with mode1 but lacks freshness and cannot identify
V6's mode. A downstream emergency path has concrete MMIO writes, with no
proved physical-output register meaning. Hoststatus10 has three competing
selector10 producers, so it does not uniquely identify the recurring RT poll.
See [review corrections and exact accepted sources](panel-idle-20261026/overnight/current-host-health-20261027v/ordinary-trace-reviews.md).
A fixed ordinary-input snapshot and a separate passive finite observer are
being built offline. No new logger or modification has been deployed yet.

Newest accepted callback-source read (2026-10-27): three fixed reads
completed cleanly on the same boot at terminal uptime123267.81. The pointer
again names450158a8; raw source+0=3, +1=10 and+3d8=1. The3/1 fields agree
numerically with the much earlier copied-context sample, without recovering
an atomic source/mirror pair or V6 event-time operands. All six transfers,
release/close and stage removal passed; no reset, write, flash or physical
observation occurred. See [actual corrected source findings](panel-idle-20261026/overnight/ap-exco-callback-source-20261027o/capture-findings.md).
No helper remains running. Ordinary producer/writer provenance is being
checked offline; the exact event-time comparison and sample physical meaning
remain the decisive gaps. No permanent blackout fix or untethered root is
established.

Completed ordinary selector provenance (selected-code facts): the distinct
AP_EXCO object's+3d8 is derived after helper calls from Boolean
`(ordinary+e6 &1) OR u16(ordinary+2fc)`. The helper order matters and is
[pinned with the review correction](panel-idle-20261026/overnight/ap-exco-derived-object-provenance-20261027p/review-closure.md).
Ordinary callers supply explicit constants to+0/+1; one+1 branch selects10
when+3d8 is nonzero and8 otherwise, compatible with the late1/10 source
values. [Caller provenance](panel-idle-20261026/overnight/ap-exco-caller-provenance-20261027q/ap-exco-caller-provenance.md)
keeps field names/units unassigned and adjacent strings unbound.
The [code-write readiness review](panel-idle-20261026/overnight/code-write-readiness-20261027r/code-write-readiness.md)
finds no positive mutable-backing/write-acceptance, RAM-execution or rollback
proof in its finite reset/scatter scope. No code-write probe is justified
by readable matching bytes alone. No logging patch, protection bypass or
flash has been deployed.
O--R evidence is frozen in a [36-file/552155-byte checkpoint](panel-idle-20261026/overnight/ap-exco-callback-source-20261027o/callback-provenance-evidence-manifest.json),
SHA256c8876fcb5c6d2f5e41e21d2e202f35c4304629524c2f7cdc7bea94ed44c2d404,
with both full N28/M49 parents verified unchanged. The [independent byte/inventory audit](panel-idle-20261026/overnight/ap-exco-callback-source-20261027o/checkpoint-review.md) passes all36files and both complete N28/M49 parents unchanged. Its review is explicitly excluded from the frozen file map.

Prior source-lineage correction (2026-10-27): the fixed source read completed three exact
pairs on the same boot at terminal uptime122020.20, with ReadyForHeader,
release/close and stage removal. It rejected the old expected pointer at cc.
A subsequent ordinary startup trace explains that mismatch as an earlier
static interpretation error: c4/c8 are ordinary AP_EXCO blocks, while cc is
a distinct AP_EXCO object450158a8 obtained from a different registry root.
The entire captured neighborhood agrees with that selected startup layout;
no global eight-byte relocation is supported. See the
[pointer-lineage correction](panel-idle-20261026/overnight/ap-exco-source-read-20261027m/source-lineage-erratum.md)
and [exact trace](panel-idle-20261026/overnight/ap-exco-source-read-20261027m/pointer-layout-followup.md).
The raw20/0 reads sampled the ordinary blocks, not the callback source, so
the earlier suggested20/0→1/3 source mutation is withdrawn. Captured faults
and numeric predicate facts are unchanged. No reset, protection change or
flash occurred. A newly identified ordinary code-domain mapper is being
qualified for small running-code fingerprints; it is distinct from the
previous RAM-only mapper analysis.

Completed H--M ordinary provenance is frozen in a
[49-file /615,642-byte checkpoint](panel-idle-20261026/overnight/ap-exco-source-read-20261027m/ordinary-provenance-evidence-manifest.json),
SHA25626b5cc4faa8a3c03917b92ac48254ba359362bd201830cdf29fb229154b3dd0b.
Publication, optimized verification and the [independent checkpoint audit](panel-idle-20261026/overnight/ap-exco-source-read-20261027m/checkpoint-review.md) pass, including all353listed file entries in the
three complete D7 parent checkpoints. Mutable navigation and working model
are outside this snapshot. New code-map/fingerprint work is in N and a new
helper directory; no listed H--M file may be rewritten.
The N [independent byte/inventory audit](panel-idle-20261026/overnight/code-map-qualified-followup-20261027n/checkpoint-review.md) also passes all28files/543563bytes and the complete49-file M parent unchanged.
The [positive code-domain mapper follow-up](panel-idle-20261026/overnight/code-map-qualified-followup-20261027n/code-map-qualified-followup.md)
qualifies the proposed fixed windows by an explicit selector-nonzero mapping,
while preserving that selector1 is not proved to be the currently executing
image-1 core. One independently reviewed candidate code capture has now completed: all
three nonadjacent windows (1152bytes total) match the selected/current stored
bytes exactly, including the full472-byte predicate, getter and startup
lookup/mapping bodies. It endedReadyForHeader with release/close and stage
removal at terminal uptime122877.73 on the same boot. See [actual code-view
fingerprints](panel-idle-20261026/overnight/code-map-qualified-followup-20261027n/capture-findings.md).
These local mapped-view matches do not prove a corePC, whole-image identity
or code-writability. No code modification occurred. The corrected callback source read has since completed as described at the
top of this page; it did not reuse the rejected ordinary-block interpretation.

Latest checkpoint (2026-10-27): a live20.06second V6 capture recorded
RTfault0→0x1001,31RTP sample rows and two `rtp_act_736` records. A later
stock query returned0x10 with matching raw QDF kernel row, and an independent
fault-pin input returned1. This is the first new detailed controller event
capture in this work block. The logger restored gate0→1→0 and closed cleanly;
its stage and the UI helper stage are removed. The fault state is preserved.
The owner was asleep: physical light and blackout onset are unobserved. The
normal ForYou API request returned but sampled UI stayed Apps, so its causal
role is unproved. See the [incident details and limits](panel-idle-20261026/overnight/finite-onset-logger-20261027g/fault-incident-v6.md).
The ordinary action/setter path and numeric predicate are now traced. A
subsequent fixed two-window read completed cleanly on the same boot and
retained fault1001, low-score latches54/44 and candidate limits200/0/0/200/40.
Those sequential samples were about32minutes after V6; they do not select an
event-time mode or limit. See the [retained-context findings](panel-idle-20261026/overnight/finite-onset-logger-20261027g/fault-context-after-v6-findings.md).
The score's input is now traced to delayed history of qualifying sample
counts, rather than a sum of printed difference amplitudes. A newly found
PC-relative literal-resolution error in the frozen source-A fallback note
is corrected additively in the [source-address erratum](panel-idle-20261026/overnight/finite-onset-logger-20261027g/rtp-packed-source-address-erratum.md);
the raw capture and numeric event predicate are unaffected.
A further accepted selector capture returned the expected root pointer,
aa=0/ac=2, numeric alternate mirror1 and candidate alternate byte1. The
candidate window also matches three startup constants. These later values
support a mode1/alternate-limit40 hypothesis consistent with the earlier
score44, without recovering the V6 event-time comparison. Its mirror-control
field is0; an ordinary increment-and-clear path now explains why that field
need not remain Boolean after the numeric mirror is refreshed. See
[selector findings](panel-idle-20261026/overnight/finite-onset-logger-20261027g/selector-context-after-v6-findings.md).
The completed follow-up is preserved in a
[75-file / 1,111,428-byte checkpoint](panel-idle-20261026/overnight/finite-onset-logger-20261027g/diagnostic-followup-evidence-manifest.json).
Its [independent byte/inventory review](panel-idle-20261026/overnight/finite-onset-logger-20261027g/diagnostic-followup-manifest-review.md)
passes all listed artifacts and both complete parent checkpoints.
The earlier code-bus qualification did not establish a live executable
address. A separate mapper with an explicit low-code domain has since been
identified and is under independent qualification before any logging patch.
No permanent blackout fix, protection bypass or flash is established. The
owner permits such changes if needed while requiring that the TV not be bricked.

New ordinary-input traces (2026-10-27, offline): the printed `x` is a
software 12-bit lane ordinal, with 1,920 nominal lanes under the retained
2,880-byte extent. Printed `y` and `RGB` instead descend from an input-header
handoff whose producer reaches unresolved MMIO at `0x58601408`. The adjacent
header field, rather than printed `y`, is compared to `2160-1`. Thus `y=2159`
is not yet a proven physical bottom-row coordinate. See the
[scan-input provenance](panel-idle-20261026/overnight/rtp-scan-input-origin-20261027i/rtp-scan-input-origin.md).
A controller-local manufacturing-console writer addresses the ordinary
AP_EXCO blocks, whose retained baseline bytes include `20/0`. The later
pointer-lineage correction shows these are distinct from the callback source;
that writer does not explain the copied-context `1/3` observations. See the
[runtime-writer trace](panel-idle-20261026/overnight/rtp-alternate-runtime-origin-20261027j/rtp-alternate-runtime-origin.md).
These traces are outside the frozen D7 follow-up manifest. The subsequent fixed source capture is now completed with accepted transport
but rejected pointer binding, as detailed at the top of this navigation page.

The [packed-buffer producer trace](panel-idle-20261026/overnight/rtp-packed-buffer-origin-20261027l/rtp-packed-buffer-origin.md)
now positively connects prior/current descriptor fields to two successive
ring slots using CPU copies from a computed `0x60000000` aperture. It
supersedes the older same-slot-overwrite statement additively; the frozen
original is preserved. The descriptor source is associated with the packaged
`EXCO_PAR2_S0` record, but aperture ownership/physical meaning remains
unproved. An [independent root review](panel-idle-20261026/overnight/rtp-packed-buffer-origin-20261027l/root-review.md)
confirmed the slot transition and closed a header-field distinction before
acceptance.

A concise [working fault model](panel-idle-20261026/overnight/ordinary-fault-model-20261027.md) now separates the owner-observed cases, captured event, reconstructed numeric chain, later measurements, corrections and missing decisive evidence. It is a mutable interpretation outside frozen manifests.

The owner's current priority is the content-dependent panel blackout: populated Apps often keeps the picture visible, sparse Home/Live can produce a persistent black panel while audio continues, and Settings can cause flicker. The impact damage is no larger than the owner's thumb, with a narrow vertical dark line above it. Some Ugoos/live-playback losses also pause audio briefly and recover; those remain a separate uncaptured incident pattern.

Start with the [owner history and main diagnosis](panel-idle-20261026/overnight/diagnosis-20261026.md). That document's phase-specific observer status is historical. The [later observer validation report](panel-idle-20261026/overnight/onset-observer-validation-progress.md) records actual passive runs and their limitations. Its [176-file evidence manifest](panel-idle-20261026/overnight/onset-observer-validation-evidence-manifest.json) was independently verified, with the preceding 43-file snapshot unchanged.

Current low-level follow-up:

- **Current finite-onset runtime evidence preserved:**84files /4,515,096bytes,
  [manifest](panel-idle-20261026/overnight/finite-onset-logger-20261027g/runtime-evidence-manifest.json),
  SHA2562d1d1427ea37c70e5b6ee37e301488027f6b2a0ff64f7d591884ca6faa252534.
  Includes failed and ambiguous attempts without promoting them, the accepted
  marker-only launcher runtime and accepted Apps API-return qualification.
  No physical panel recovery or further controller run is established.

- **Preserved complete acquisition checkpoint:**145files /33,070,645bytes,
  [manifest](panel-idle-20261026/overnight/firmware-fingerprint-20261027d/firmware-acquisition-evidence-manifest.json),
  SHA256e1f11fe681fa6047ba995a796315b712428ff75c415b3e9042d7e52127960d0f.
  A single5MiB request completed640 exact8192-byte INs in281ms. The raw
  replay audit reconstructs247 authenticated calls, the full record state
  and all retained files. First32KiB and all six sectors repeat earlier
  fingerprints. [Findings and compatibility failures](panel-idle-20261026/overnight/firmware-fingerprint-20261027d/progress.md),
  [runtime audit](panel-idle-20261026/overnight/firmware-fingerprint-20261027d/backup-runtime-audit.json),
  [independent review](panel-idle-20261026/overnight/firmware-fingerprint-20261027d/independent-review-record.md).
  No flash, protection change or physical fix is established.

- **Next executing-image discriminator:** the current stored first image
  initializes a callback table at the same RAM address as the selected
  package, with different function pointers. The table was located from
  reset code and relative scatter-table offsets rather than a global shift.
  [Pending fixed-read work](panel-idle-20261026/overnight/executing-image-identity-20261027e/README.md)
  and [offline initializer predictions](panel-idle-20261026/overnight/executing-image-identity-20261027e/callback-initializers.json).

- **Current stored-code fingerprint work:** six exact512-byte replies and
  one exact8192-byte prefix completed with full cleanup, on the same boot.
  Prefix bytes0..1023 repeat the earlier individual header/vector sectors.
  The returned parser and callbacks are mapped locally; the local0x29c shift
  is not a global relocation rule. No flash/protection change or physical fix
  is established. [Current work and interpretation](panel-idle-20261026/overnight/firmware-fingerprint-20261027d/progress.md),
  [transport/build audit](panel-idle-20261026/overnight/firmware-fingerprint-20261027d/runtime-audit.json),
  and [current returned-code checks](panel-idle-20261026/overnight/firmware-fingerprint-20261027d/current-protocol-audit.json).

- **New preserved recorder/header checkpoint:** [41files /6,166,952bytes](panel-idle-20261026/overnight/rt-onset-memory-20261027c/rt-recorder-evidence-manifest.json),
  SHA256c012fdadd49d8f5dec30e6fff53d5e43a14fed1bb0c04a2bfb00f1883f3dc98f.
  Full independent hashes and optimized checks pass; prior90/260-file snapshots
  remain unchanged. No capture/helper from this block remains running.

- **New storage-header discrepancy and qualified short recorder:** a clean
  512-byte target0x203 reply identifies241205A, differing in13 bytes from the
  selected profile header241230A. Read-leaf status/freshness and executing-code
  identity remain unproved, so absolute-offset patching against that package
  requires new backup/fingerprint evidence. A new full256-byte RT read and
 20-sample recorder smoke also completed; all21 RT blocks matched, and the
  series ran at250–251ms start intervals with exact transport/cleanup.
  [Current result, interpretation and next work](panel-idle-20261026/overnight/rt-onset-memory-20261027c/progress.md)
  and [raw/runtime audit](panel-idle-20261026/overnight/rt-onset-memory-20261027c/runtime-audit.json).
  Physical picture state and permanent repair remain unverified; helpers ended
  and their private stages are absent.

- **New preserved controller-access checkpoint:** [90 files /6,549,528 bytes](panel-idle-20261026/overnight/rt-telemetry-followup-20261027b/controller-access-evidence-manifest.json),
  SHA256c543b3d24a8cd7b807990e46e25ee4ede3420724d47c43fc752af472800a2c38.
  Runtime audits and full independent byte/hash scans passed; the prior260-file
  checkpoint remains unchanged. Current helpers ended and their stages are absent.

- **Direct RT-state read now verified, October27:** one fixed32-byte memory
  read from0x47012400 completed with OUT12/IN32, successful interface/FD cleanup
  and stage removal. Thirty bytes match the selected initializer; offsets08/0e
  changed0->1, fault halfword0a is0 and mode10 is4. A later stock query also
  returned0, with a matching raw QDF row. These are sequential, physically
  unobserved samples. This supersedes prior RT-access-not-established notes
  for this prefix only. [Current progress and paired-capture plan](panel-idle-20261026/overnight/rt-telemetry-followup-20261027b/controller-memory-access-progress.md)
  and [runtime audit](panel-idle-20261026/overnight/rt-telemetry-followup-20261027b/rt-prefix-runtime-audit.json).
  No protection change, flash, reset loop or permanent fix is established.

- **Verified controller-memory access, October27:** the corrected fixed reader
  completed one direct18-byte controller-RAM read with exact known descriptor
  content, OUT12/IN18, successful release/close and private-stage cleanup.
  Its predecessor stopped before USB open on a sysfs-length bug and remains
  preserved. [Actual result](panel-idle-20261026/overnight/rt-telemetry-followup-20261027b/usb-known-descriptor-read-once-v2/stdout.txt)
  and [runtime audit](panel-idle-20261026/overnight/rt-telemetry-followup-20261027b/known-descriptor-runtime-audit.json).
  This supersedes earlier not-yet-executed statements for this narrow RAM
  reader only. No RT-window access, full-image match, flash, protection change
  or physical recovery is established.

- **Mode-gate correction, October27:** a new
  [instruction-bound follow-up](panel-idle-20261026/tcon-research/ssb-mode-gate-followup-20261027.md)
  supersedes the earlier unresolved-mode conclusion. The header parser itself
  replaces sentinel2 with mode0 for operations1/2 and mode1 for operations3/4,
  through reused references to the same literal. The ordinary read path is
  locally reachable. A separate fixed18-byte descriptor-memory reader is built
  and undergoing independent review. No active request has yet been sent at
  this checkpoint; installed-image identity and physical recovery remain open.

- **Controller diagnostic-route follow-up:** the new
  [work log](panel-idle-20261026/overnight/rt-telemetry-followup-20261027b/README.md)
  records three authenticated cached UART/USB metadata reads and new offline
  protocol censuses. `ttyUSB0` is the SmartThings Dongle, distinct from the
  reset-coupled Samsung bulk interface. The bounded I²C getters do not expose
  the identified RT history/live window. New scatter reconstruction exactly
  matches all18 USB device-descriptor bytes; the vendor-bulk `0x203` branch
  is now traced to an eMMC read, with a discarded storage-error return. A
  one-shot helper passes22 injected I/O/cleanup cases and independent code
  review. Its no-device dry run and22 fake cases also completed on the TV's
  ARM CLR, with private staging removed. A newly identified command-execution
  gate at controller byte0x20000571 remains unresolved for both storage and
  addressed-memory reads; no USB endpoint open/read occurred. The owner
  explicitly authorizes active I/O, bypass and flashing if needed; installed
  image identity and recoverability remain engineering gaps. No new panel
  reset, protection write or flash occurred, and physical recovery after the
  prior single MODE2 cycle remains unobserved.

- **New preserved work block:** the unattended investigation now has a
  [260-file evidence snapshot](panel-idle-20261026/overnight/sleep-investigation-20261027a/sleep-evidence-manifest.json),
  verified normally and with optimized Python. It includes the one stock
  panel-cycle result, rejected recorder attempts, a valid bounded compressed
  syscall inventory, and kernel/firmware analyses. See the
  [next-test plan](panel-idle-20261026/overnight/sleep-investigation-20261027a/diagnostic-next-tests.md).
  There is still no physical recovery or permanent prevention result.

- **Single stock panel power-cycle, October27:** exactly one operation41/mode2
  request reached the stock ACDET/reset-mailbox/settings-replay path. ERR_DET
  changed1→0; immediate and approximatelyfive-minute later sequential
  status/pin samples were0/0 on the same Linux boot. Physical picture recovery
  is unobserved; no continuity between samples is inferred.
  The containing capture remains rejected for a pre-action duplicate AVOC
  syscall-enter; separate raw transport analysis is bounded to its complete
  I2C/GPIO/kernel substreams. All helpers and tracing cleaned up. See the
  [sleep investigation](panel-idle-20261026/overnight/sleep-investigation-20261027a/README.md)
  and [runtime audit](panel-idle-20261026/overnight/sleep-investigation-20261027a/mode2-sequence-runtime-audit.md).
  No flash, kernel replacement, protection suppression or reset loop was run.

- **While the owner sleeps, new controller-value evidence:** fresh fixed `F300:0x128` read returned207 with matching raw QDF log; a subsequent status query returned0x10, also raw-log corroborated. Both cleaned up. The preceding five-second recorder smoke was accepted with9,932/9,932events and cleanup; no physical picture was observed. Owner authorization now permits commands/tests without visual feedback. See [sleep investigation](panel-idle-20261026/overnight/sleep-investigation-20261027a/README.md). No recovery, flash or protection change is claimed.

- **Overlay/fullscreen evidence note, October27:** a documentation-only
  [paired-control note](panel-idle-20261026/overnight/ugoos-overlay-paired-control-20261027.md)
  now preserves the owner-reported full-Apps versus sparse For You/Live pattern,
  the latest sleeping/black/no-feedback state, and photo hashes. Current
  Playing/Featured labels were resolved by the parent photo review. It links the two-week
  controls, helper reviews, long design work and RTP scan without claiming an
  installed helper or fix. The two parent re-reviewed UI stills label Person
  of Interest EPISODE_REDACTED/PROGRAM_15 and PROGRAM_04 PROGRAM_LABEL/PROGRAM_A's Farm
  PROGRAM_16 respectively; they are not continuous timing evidence.

- **PROGRAM_B rearmed and tested:** the owner explicitly said they were ready, then confirmed playback and later reported the picture went dark. The new `ugoos-program_b-20261027a` recording is finished with verified cleanup; its original result remains rejected for an AVOC maps change. A first status check returned0 before the latest blackout report; a separate check after that report returned0x10, corroborated by the raw QDF kernel row, followed by accepted independent fault input1. All helpers cleaned up. The old HOLD preparation stays excluded; it has not been promoted into test data. See [current progress](panel-idle-20261026/overnight/paired-restart-progress-20261027.md). The physical onset is not calibrated or proved to fall within the trace window. No permanent fix is established.

- **New offline gate and read-ABI results:** the [F300 write-gate trace](panel-idle-20261026/tcon-research/qd-f300-write-gate-provenance.md), independently reviewed, identifies concrete gate producers and explains why a host scalar request need not reach controller RAM. It does not show that an RT fault sets a gate. The [generic read ABI](panel-idle-20261026/tcon-research/qd-generic-read-command-abi.md) positively maps operation19 to the read callback for hexadecimal selector0x128; operation18 is the separate write route. A fixed read helper was subsequently reviewed and exercised in the sleep investigation; no generic write was sent. The [RTP input trace](panel-idle-20261026/tcon-research/qd-rtp-primary-event-input-provenance.md) narrows the local event predicates but leaves the inter-core window bridge and incident-time producer unresolved.

- **New matched-format history and startup binding:** researcher's requested history review finds a completed PROGRAM_B PROGRAM_LABEL matching the failing PROGRAM_LABEL source format, weakening a broad codec/frame-rate explanation. [History and source-frame findings](panel-idle-20261026/overnight/ugoos-researcher-history-comparison-20261027.md) are separate from physical success. The [new AP_RTP loader proof](panel-idle-20261026/tcon-research/qd-config-rtp-table-load.md), independently audited, now binds the selected packaged parameter block to the fixed RT field window; it supersedes the prior missing-loader conclusion. No live RT threshold or fault producer is measured. Fresh UART-node metadata also reveals a direct-IO host UART lead under offline review; no serial device was opened.


- **New failed-versus-working Ugoos playback, October27:** PROGRAM_04 PilotS01E01 produced a persistent black picture with continuing audio, followed by accepted status0x10/pin1. After owner recovery, PROGRAM_A's Farm EPISODE_REDACTED played with the picture staying on and accepted status0, corroborated by a raw QDF kernel row. Actual HDMI output was1080p/~24Hz SDR versus2160p/50Hz HDR10+. The [comparison report](panel-idle-20261026/overnight/ugoos-PROGRAM_A-comparison-20261027.md) and [current progress](panel-idle-20261026/overnight/paired-restart-progress-20261027.md) retain all capture/physical-timing limits: both overall trace records remain rejected for AVOC heap changes; the working pin helper also remains rejected despite complete raw0 output. Both captures cleaned up. [Media metadata](panel-idle-20261026/overnight/ugoos-media-comparison-20261027.md) identifies direct-play sources separately from negotiated HDMI mode. No permanent fix is established.

- **Emergency-loop guard initialization:** the [new static review](panel-idle-20261026/tcon-research/qd-rt-return-guard-initialization.md) finds both return guards zero after packaged reset scatter and a configuration writer for the second guard. Runtime values and entry into the permanent loop during the incident remain unproved. No guard or protection patch was applied.

- **Load-address correction, October27:** each embedded executable has a512-byte prefix. Earlier code labels generally identify stored file offsets, not linked addresses. The [address erratum](panel-idle-20261026/tcon-research/qd-firmware-load-address-erratum.md) records the corrected mapping, independent survival of the relative RT-to-wire path, a concrete USB callback misbinding, and a positive image1 startup pointer. Absolute function/scatter pointers require the corrected mapping before use. Runtime status/pin evidence is unaffected; no repair is established.

- **New owner-reported working Apps control, October27:** working Apps status0/pin0 was followed by a coordinated manual For You blackout and new accepted status0x10/pin1 readings on the same Linux boot. Both finite helpers cleaned up, and matching raw kernel status is retained. The [paired-capture progress](panel-idle-20261026/overnight/paired-restart-progress-20261027.md) records the physical-timing limits, working policy snapshot and new USB-versus-UART logging distinction. Later coordinated HDMI recordings and postcapture diagnostics are now complete as described above; no repair is established. This supersedes older navigation statements that a visible Apps control is still wholly pending.

- **New executable protection lead:** the matched5MiB file contains two Cortex-M images; [image0 analysis](panel-idle-20261026/tcon-research/qd-selected-profile-content.md) reconstructs an EEPROM-labelled RT-protection check entering error handling with selector0x10. The [wire analysis and independent review](panel-idle-20261026/tcon-research/qd-profile-rt-wire-independent-review.md) now prove that packaged error field feeds the exact F3:08 reply; this is more than a numeric/string match. The [controller-layer audit](panel-idle-20261026/tcon-research/qd-rt-controller-identity-boundary.md) separates that external QDF I2C route from internal RHEA shared memory. Current-flash equality, live upstream trigger and incident execution remain unproved; no write/control or repair was performed.

- [New firmware/profile progress, October27](panel-idle-20261026/overnight/firmware-profile-progress-20261027.md): retained raw FW/MD strings uniquely match packaged profile`F_RSM1_BN9659934B_COMMON.bin`; the full5MiB regular file is now copied with matching source SHA. This supersedes the older “no candidate selected” statements without claiming current controller bytes match. The complete official main MSD member is also acquired and independently CRC/SHA checked on the host; sections remain opaque. Additional telemetry and primary-source maintenance research do not define RT's subcause. An exact installed TEEC library was copied as an ordinary file only; no crypto/TA/USB/controller invocation or physical repair occurred.

- [New controller follow-up](panel-idle-20261026/overnight/controller-fault-followup-20261026.md): exact retry predicates, nine newly found distinct factory TCON data assets, and one safely bounded shared-log snapshot. The log reader's count bug is reconstructed; the1,477-byte new snapshot shares1,404 bytes with the earlier startup text and adds mailbox messages. The exact missing CAD provider has now been copied and independently audited; its host parser and45 small factory-file fields are reconstructed. New SSB analysis separates update verification from a fixed5MiB active USB backup path. Current metadata finds the module loaded and a matching04e8:2001 USB device, but no exposed SSB nodes or matching driver-directory name. Neither the endpoint's TCON identity nor its storage layout is established; no USB command or registration was sent. No fault cause, MCU executable recovery or physical repair is established. Visible Apps comparison remains pending.

- **New positive fault indication:** one successfully completed stock status
  query returned **0x10**, labelled **RT Protect** in this exact firmware.
  The matching raw kernel log for PID3216 at75262.252253 corroborates that
  value before optional debug override. The [actual result](panel-idle-20261026/overnight/tcon-status-actual-result-20261026.md)
  retains all execution details, rejected predecessors and cleanup. Its
  physical meaning, live-versus-latched semantics and causal connection to
  the blackout remain under investigation; this is not a repair. No power,
  reset, monitor-rearm or protection change was sent. The
  [controller boundary](panel-idle-20261026/tcon-research/rt-protect-controller-path.md)
  and [host recovery predicate](panel-idle-20261026/tcon-research/rt-protect-host-recovery.md)
  are traced separately. The separately reviewed
  [black-context GPIO query](panel-idle-20261026/overnight/tcon-gpio-actual-result-20261026.md)
  returned1, which the stock monitor treats as fault; its debug override is
  not excluded and no electrical-raw claim is made. Both helpers cleaned up.
  One normal owner off/on into populated Apps is requested for a visible
  control; no dependent readings will run before confirmation.
  A subsequent [GPIO metadata read](panel-idle-20261026/overnight/gpio-direct-route-progress.md)
  found a standard cdev route to bankgpio15/line5; the acquired paired kernel now
  [proves a null vendor persistence callback](panel-idle-20261026/tcon-research/sdp-pinctrl-v2-config-binary.md),
  independently checked. Input direction still writes registers. The first
  metadata-only cdev check completed accepted
  with verified cleanup: expected chip/line identity, flags0/empty consumer.
  Its [runtime audit](panel-idle-20261026/overnight/managed-errpin-cdev/runtime-audit.md)
  establishes interface compatibility, not a pin value or physical state.
  A subsequent separately reviewed [one-shot independent input sample](panel-idle-20261026/overnight/errdet-direct-actual-result-20261026.md)
  returned1 through the GPIO interface, bypassing QDF cache/debug branches.
  Both closes and helper cleanup succeeded. Input-direction/descriptor side
  effects are documented; no output/protection/reset command or retry was sent.
  Owner latest clarified panel off; visible Apps control is still pending.

- Owner is home. One stock public unmute request returned zero while the owner
  reported the panel stayed black; its [runtime audit](panel-idle-20261026/overnight/stock-unmute-once-runtime-audit.md)
  records a failed recovery, with no lower-I/O claim. A subsequent ordinary TV
  off/on preserved Linux and daemon identities. One 85-second passive capture
  was then run across an owner-performed off/on and another reported brief
  picture followed by black with audio. That run is rejected for missing final
  completion and end-state evidence. All seven retained files were rescued and
  [independently verified](panel-idle-20261026/overnight/owner-power-on-rescue-audit.md),
  including 172,200/172,200 trace events with zero ring loss. The vlog is capped
  at 64 MiB. A later guarded cleanup verified the original output/stage/private
  trace and rescue directory absent, with global tracing off. No capture or
  recovery loop remains active. The [decoded state samples](panel-idle-20261026/overnight/owner-power-on-state-analysis.md)
  show lcdon→standby→lcdon with stable duty/cache207 and historical monitor
  fields. The [corrected mute readback](panel-idle-20261026/tcon-research/qd-mute-readback-wire-correction.md)
  positively returns zero after unmute; this still does not prove physical
  panel output or diagnose the failure. Last Q samples precede final unmute.
  The [controller error-query ABI](panel-idle-20261026/tcon-research/qd-error-status-read-abi.md)
  is now reconstructed. The first helper attempt stopped at preflight; a
  later attempt staged correctly but failed at an empty-file guard after GO.
  Query issuance is unresolved and no status word was obtained. A separate
  guarded cleanup verified the helper stopped and its directory removed.
  The corrected deliberate follow-up completed with the positive0x10
  result above; failed predecessors remain unchanged.
  A later [passive branch snapshot and audit](panel-idle-20261026/overnight/post-wake-branch-audit.md)
  validates duty/cache207, AutoDim argument0 and AutoPowerOff count0 after the
  owner's last black-panel report. It is sequential software evidence, not
  a time-calibrated physical sample. A preceding map-encoding failure is
  retained as rejected; the corrected read made no TV setting change.
  Owner chat does not supply calibrated onset timestamps.

- The corrected five-second passive successor
  `qpm-home-smoke-20261026` completed with all 10,521 written events retained,
  technical acceptance and verified cleanup independently confirmed in the
  [runtime audit](panel-idle-20261026/overnight/quiescent-pm-home-smoke-runtime-audit.md).
  Zero physical annotations means no fault or recovery
  conclusion. No display control was sent.

- [Private controls and expanded passive capture audit](panel-idle-20261026/overnight/private-control-and-quiescence-progress.md): new exact HDMI implementation libraries were copied and independently audited. Independently reviewed code traces now connect a DPMS notification to a cached kernel byte and conditional suspend policy, and reconstruct input source/foreground/background operations. Several error results are discarded or normalized along those bounded routes; none is incident-aligned. Live callback binding remains unproved, and a prepared finite pointer reader remains unrun pending full fixture/result validation. The executed quiescence observer revision's cleanup-contract rejection is preserved; its corrected successor passed 121 tests and independent offline review, then completed the new five-second target capture noted above. The original five-second run retained all 10,777 events, with zero physical annotations; its runtime-contract rejection remains preserved. No repair or display control was performed in this follow-up.

- [181-file private-resume/OCIF evidence snapshot](panel-idle-20261026/overnight/private-resume-ocif-evidence-manifest.json): SHA-256 `cd91625dc37877be30576459d5dffd7a6b7969091d3cb36141eb22ec8be26824`. Normal/optimized verification and refusal of a second publication passed. Independent audit verified the exact 181-file set and every prior 494 evidence row across five snapshots. This freezes both rejected PM captures, their cleanup/audit and the latest private-PM state/return interpretation; it establishes no physical repair. The subsequent quiescence derivative and HDMI control-producer work are outside this snapshot.

- [Private PM return/state outcomes](panel-idle-20261026/tcon-research/private-rpm-state-outcomes.md): another statically established retry-suppression candidate. Samsung's dispatcher discards callback returns and advances its use count/state; later gets can skip resume. The HDMI wrapper can also return zero without substantive resume when its separate context word differs from 3. Stock resume entry/timing markers are reconstructed. No incident-aligned invocation, live record, or tested fix. Neither the global disable helper nor the potentially allocating getter was invoked.

- [Private HDMI resume and OCIF follow-up](panel-idle-20261026/overnight/private-resume-and-ocif-progress.md): positive proprietary callback registration/dispatch, cached availability producers, conditional boot support, and caller-specific stock log markers are reconstructed. The resolved AckPolling provider requests a one-byte zero write; no callback was invoked. A seven-event PM candidate passed offline review but its first passive smoke rejected legitimate idle-context rows; all 10,521 events and verified cleanup are preserved. The idle-identity correction passed 108 offline tests and independent review. A separate five-second passive run failed to complete; partial evidence and verified cleanup are retained. Neither run establishes a blackout cause or repair.

- New exact-code reports: [private resume dispatch](panel-idle-20261026/tcon-research/hdmi-private-resume-dispatch.md), [OCIF cache producers](panel-idle-20261026/tcon-research/ocif-cache-producer.md), [boot-input provenance](panel-idle-20261026/tcon-research/serdes-support-boot-provenance.md), [stock power log markers](panel-idle-20261026/tcon-research/hdmi-private-power-log-markers.md), and [AckPolling transfer semantics](panel-idle-20261026/tcon-research/ocif-ack-polling.md). These remain static/metadata evidence; standard PM traces do not cover every Samsung private path, and current I2C filters do not cover the newly resolved AckPolling addresses.

- [163-file resource/pre-roll/SerDes evidence snapshot](panel-idle-20261026/overnight/resource-preroll-serdes-evidence-manifest.json): SHA-256 `f84677589fadefb42eb40214683d6da27539f7f4b5356ed91b85738007353906`. Publication, normal/optimized verification and refusal of a second publication passed. Independent audit verified the exact 163-file curated set and every prior 331 evidence row unchanged. Includes the [reviewed PM/RPM extension design](panel-idle-20261026/overnight/pm-rpm-onset-extension-design.md), which is not implemented or enabled.

- [SerDes probe/resume path and available PM tracepoints](panel-idle-20261026/tcon-research/serdes-probe-resume-path.md): a kernel helper has an exported cached OCIF provider and callers in HDMI probe/resume. The same-named fallback register-reader body is unexported, so that dynamic edge remains unresolved. Requested sleeps are not a diagnosed three-second blackout timer. Six PM/RPM formats are captured but not enabled; onset, live binding and cached-state producer remain unresolved.

- [Accepted pre-roll observer smoke and next physical step](panel-idle-20261026/overnight/preroll-observer-runtime-progress.md): corrected new implementation passed 78 offline tests and one independently accepted five-second passive TV smoke, retaining all 10,488 trace events with verified cleanup. Zero physical annotations; no live start-boundary pair; no blackout diagnosis or repair.

- [SDP resource translation and production-mode gate](panel-idle-20261026/tcon-research/sdp-resource-and-production-gate.md): explicit parent DT cells/ranges close the static address gap; newly copied `tztv-battery.ko` resolves the callback to a cached production-mode field. A bound read-only sysfs sample is zero, lowering this gate's priority without proving onset behavior or live callback binding. Corrected metadata decoder independently reviewed; no recovery/control experiment.

- [Owner progress status and remaining fault attribution](panel-idle-20261026/overnight/owner-progress-status-20261026.md): latest separation of reconstructed paths, observed blackouts, candidate mechanisms and missing onset evidence. Includes the new DT resource translation and independently reviewed pre-roll design; neither is a tested repair.

- [Reviewed SDP register path and rejected combined-observer smoke](panel-idle-20261026/overnight/sdp-register-path-and-observer-smoke-progress.md): static dimming path now reaches an allowed mapped-register store; Linux I2C trace coverage alone is insufficient. Actual five-second passive capture was rejected on process-parser stderr; raw artifacts and verified cleanup are preserved. Corrected tool is independently reviewed and archived offline (57 tests); it has not run on the TV. No physical/fix inference.

- [Reviewed monitor provenance and FRC lifecycle progress](panel-idle-20261026/overnight/monitor-and-frc-reviewed-progress.md): independently reviewed GPIO/error interpretation and positive QD dimming-selector save/replay paths, with reproducible exact-binary checks. No incident-aligned cause or repair; expanded combined observer still under review.

- [Kernel PQE event record layout and producers](panel-idle-20261026/tcon-research/pqe-kernel-event-records.md): six producer tags and a 52-byte user ABI; ioctl -11 is the queue-empty outcome, not a panel-off error.
- [Deferred Home-exit restoration](panel-idle-20261026/tcon-research/newhome-exit-restore-path.md): later resolution processing consumes the exit flag; caches can advance before successful output programming is established. This is not incident causality.
- [Current policy/Home-exit progress](panel-idle-20261026/overnight/pqe-policy-and-home-exit-progress.md) links the completed userspace consumer, content-to-dimming, GSR and FRC read-ABI analyses. These are additions after the historical snapshot.
- [Actual passive policy baseline](panel-idle-20261026/overnight/pqe-policy-baseline-runtime-results.md): one independently accepted 0.77-second typed software-state read, with the earlier timed-out attempt preserved as incomplete. Physical picture state was unobserved; software values do not prove output application or fault cause.
- [Final-duty branch analysis](panel-idle-20261026/tcon-research/qd-final-duty-branch-analysis.md): the normal immediate backend candidate is clamped above zero after AutoPowerOff. A separate prewritten cache can suppress an identical request after a failed send; no incident-aligned failure is established.
- [Weber statistics producer](panel-idle-20261026/tcon-research/qd-weber-input-producer.md) and [DLSR PQ route](panel-idle-20261026/tcon-research/dlsr-class-pq-route.md): further content-dependent edges are now bounded, with static versus captured-runtime bindings distinguished.
- [81-file policy follow-up snapshot](panel-idle-20261026/overnight/pqe-policy-followup-evidence-manifest.json): SHA256 `775f470de4109b6fc66996fc0408f431fcac94ea424068a3dddd71ae8ff534af`. Local verification passed; a second publication was refused without changing the snapshot. Both prior snapshots and all their 176/43 file entries remain unchanged.
- [Request replay and expanded branch-state follow-up](panel-idle-20261026/overnight/cache-replay-and-branch-state-progress.md): positive kernel replay includes F3:0x128; a separate userspace record table is resolved; send-wrapper copyback uncertainty is closed. A new accepted 0.88-second physically unobserved read adds branch inputs, with a conditional arithmetic consistency match. None establishes the fault or a repair.
- [31-file replay/branch-state snapshot](panel-idle-20261026/overnight/cache-replay-followup-evidence-manifest.json): SHA256 `3b784160b3ba9566c93270d01d1099000347253789f5f02664601ee9b6d429ac`. Publication and local verification passed; a second publication was refused without altering it. It anchors the earlier 81/176/43-file snapshots.

The revised observer passed 35 offline tests and a real five-second TV smoke. It captured a display wait call returning after the observation window during a bounded trace tail, eliminating the earlier end-boundary rejection. These were unobserved passive runs: accepted instrumentation does not establish physical panel light, cause, repair, or health.

Before any new repair conclusion, link a physically observed onset or recovery to controller traffic, fault/state samples and software actions. Software screenshots, cached off flags, zero status codes and temperature getter values cannot substitute for emitted-light observations. No further control experiment is left running from the latest completed smoke.

- Live controller callback identity (2026-10-27): the corrected DMA-alias read
  at `0x45000580` returned six nonzero callback pointers matching packaged
  build241230A, rather than stored build241205A. The earlier CPU-address
  read returned zeros and is inconclusive. Both single reads completed exact
  transport and cleanup. See [D5 live identity investigation](panel-idle-20261026/overnight/executing-image-identity-20261027e/README.md)
  and its authenticated runtime audit. This establishes observed callback
  generation, not whole-image equality, physical output, or repair. The
  storage/runtime mismatch must be resolved before applying stored-code offsets.

- [D5 internal controller logs and live state](panel-idle-20261026/overnight/executing-image-identity-20261027e/progress.md): read8 fixed USB windows, including a full secondary log baseline and active main text history; all exact native transfers and cleanup passed. Main active log layouts and secondary root pointer further support the packaged generation. The later host getter/kernel log returned0, separated in time from the historical0x10; there is no current emitted-light annotation or repair claim. Persistence logging continues in both emergency and ordinary loops and does not distinguish them. A delegated high-storage-path follow-up was automatically blocked and remains incomplete. A finite volatile diagnostic logger qualification is under implementation in the next block; no logger write or flash has been deployed.

- D5 evidence frozen:167 files /13,379,142 bytes, manifest SHA256
  `63162c7d8c44e6090a9b2c2d8646811152b6fb1d19db6a6d1770ea0ba0464fd6`.
  Normal publication and optimized read-only verification passed; parent
  D4/D3 snapshots remain unchanged. Future logger work is in the D6 block.

- **D6 actual volatile logging qualification:** one independently reviewed
  invocation enabled the controller diagnostic gate, held it for3seconds and
  verified restoration. All16 USB transfers and25 authenticated calls passed;
  prearm/restored RT64 blocks are identical. The ring advanced5→11 with the
  six-byte span `t[10]\n`; its meaning is under bounded offline analysis,
  not assumed to be a fault. See [actual result and remaining diagnostic gap](panel-idle-20261026/overnight/volatile-logger-qualification-20261027f/progress.md),
  [runtime audit](panel-idle-20261026/overnight/volatile-logger-qualification-20261027f/runtime-audit.json),
  and [independent runtime review](panel-idle-20261026/overnight/volatile-logger-qualification-20261027f/independent-runtime-review.md).
  No physical picture observation, initiating blackout, flash, protection
  bypass or permanent repair was established. No test/helper remains running.

- **D6 evidence frozen:**53files /1,084,601bytes,
  [manifest](panel-idle-20261026/overnight/volatile-logger-qualification-20261027f/logger-qualification-evidence-manifest.json)
  SHA256`e2bd3a19dd06aab6524da2a2d4142c0e02b242f5045c37a09842b69346942d6d`.
  Optimized read-only verification passed; all353files across D5/D4/D3
  independently listed checkpoints also verified unchanged in this block.
  New message-source analysis is a packaged-code candidate, not live call-site
  proof; the initialfault/physicalblackout remains uncaptured by this logger.
