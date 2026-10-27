# Samsung S95F: current investigation

Updated 2026-10-27 UTC. This page is the mutable entry point. The
[working fault model](panel-idle-20261026/overnight/ordinary-fault-model-20261027.md)
contains the fuller explanation and evidence links. Historical progress is
preserved in the [navigation archive](panel-idle-20261026/overnight/navigation-archive-20261027ah/current-before-restructure.md);
its pending-work statements can be superseded by the results below.

## Current result

**Selecting populated Apps with normal local keys, then running one stock
controller MODE2 restart, returned a visible Apps picture that stayed on.**
The owner confirmed Apps and later a visible screensaver. See the
[quick recovery runbook](RECOVER-PANEL.md),
[BU recovery record](panel-idle-20261026/overnight/apps-selected-panel-recovery-20261027bu/),
and [checked routine](panel-idle-20261026/overnight/recovery-quickpath-20261027bv/README.md).
The routine is bounded to one restart and requires an owner-observed black
panel; it is not a background reset service or permanent prevention.

BH and BI previously returned visible screensavers. BH also has a later
owner-paired 20-second clean RT observation. Home then showed For You briefly
before black returned; a subsequent sample was faulted. The intended onset
observer did not prove the keypress occurred inside its window. See
[BH](panel-idle-20261026/overnight/owner-paired-recovery-20261027bh/findings.md)
and [BI](panel-idle-20261026/overnight/owner-repeat-recovery-20261027bi/findings.md).

The later BT stock restart while For You was selected did not visibly
recover the picture. After actual normal-key navigation selected Apps, BU
recovered Apps without a post-reset wake key. Direct AppControl Apps
requests had returned without changing the cached page. The newly verified
local key route uses the stock input_keyevent utility, 150 ms down/up pairs,
and per-step cached-page checks. Selected-tab highlighting alone does not
prove keyboard focus. Details are in the runbook and
[navigation records](panel-idle-20261026/overnight/ui-navigation-20261027br/).

The owner's requested Apps → For You → black → Apps → single restart
confirmation passed in [BW](panel-idle-20261026/overnight/full-confirmation-20261027bw/findings.md).
The owner saw the blackout and the returned Apps picture separately from the
software observations. BW is the fourth owner-confirmed recovery overall.

The rejected BI scientific bracket remains rejected. Offline driver tracing
now shows its single failed F3:01 read was followed by the stock retry and
expected checksum e6, then continued replay; this narrower result neither
repairs the recorder nor proves physical setting application. See the
[driver analysis](panel-idle-20261026/overnight/stock-error-propagation-20261027bo/driver-error-review.md).
No fresh raw RT read was performed in these new navigation/recovery trials.

The reconstructed controller fault0x1001 comparison and scan-gate path still
lack physically paired onset operands, the input table's producer/units,
and the final electrical loss-of-light edge. A further
[producer-edge trace](panel-idle-20261026/overnight/rt-input-producer-gap-20261027bq/source-review.md)
finds interrupt scheduling, not the missing table writer. The
[USB phase audit](panel-idle-20261026/overnight/recovered-replay-phase-audit-20261027bs/phase-review.md)
separates checksum-retry completeness from endpoint phase and liveness; it
does not authorize a new vendor transaction by itself.

Linux remained on the recorded boot throughout the latest recovery. Root
is host-assisted. No autonomous permanent root, firmware patch/flash,
protection bypass or permanent blackout fix is verified.

## External-source research: new exact-target results

The [research project](research-20261027-external/README.md) reviews all seven
supplied GitHub links plus additional primary sources, with immutable commits,
claim audits, local reproduction and independent checks. It is a continuation
of the prevention goal, not a claim that source discovery repaired the TV.
The [gap register](research-20261027-external/GAPS-AND-EXPERIMENTS.md) records
what each result changes and what remains missing.

- Both native and compatibility BPF/perf syscall paths in the saved matching
  Image resolve to unconditional ENOSYS stubs. The independent audit checks
  original uImage provenance and actual dispatch callers; executing-text
  identity remains unproved. Switching ABI alone is not a useful next probe.
- The retained official update prefix contains the complete encrypted metadata
  block and nine contiguous payload intervals. An independent parse matches
  the original ZIP endpoint. Target section names, salts, plaintext CRCs,
  signatures and installed-image correspondence remain unverified.
- Target video RGB APIs have a 16-byte pixel output, while one external class
  allocates 12 bytes. The backend can copy even on an error return. This is
  an ABI mismatch, not a reproduced crash. Their downstream sampler has two
  host-FRC MMIO slots and no recovered freshness acknowledgment; no link to
  the external MCU Pre-PD table producer was found.
- The parent's bounded ordinary-file copies acquired exact installed SWUCoreTV
  and TEE client libraries without invoking them. Static work now matches the
  normal client's SWU command 0/1/2 frames, and a stored selector sample chose
  the master encrypted-items file. Independent review found the public
  56-byte operation prefix also has a backend-accessed word at offset 56:
  allocating only 56 bytes would be too small. No TEE command was executed.
- Source claim audits retain prior target boot-hook failures and identify
  weak success markers, a relay-port wiring discrepancy, and incomplete
  cross-model impossibility claims. HyperTizen and TizenWLED share one reviewed
  S95F research lineage; they are not independent hardware replications.

See the [independent audit](research-20261027-external/reviews/independent-audit.md)
and [target acquisition record](research-20261027-external/TARGET-ACQUISITION.md).
The latest panel-controller action remains BW. New source analysis and file
copies did not reset the controller, change Home, patch firmware or establish
permanent prevention. A [minimal metadata-only source prototype](research-20261027-external/reports/minimal-swu-helper-design.md)
now passes host sanitizer/mock tests and independent review. It has no live
TEE adapter and wipes unvalidated plaintext. Target bindings, file preflight,
timeout and plaintext validation remain unfinished before a decryption test.

## Owner observations to preserve

The panel has a thumb-sized impact-damaged black region at its **bottom edge**
and a narrow dark vertical line above it. Populated Apps often stays visible;
sparse For You or Live can go black within seconds while audio continues.
Once persistently black, blind navigation back to Apps usually fails until a
TV off/on and quick navigation to Apps. A screen saver has also remained
visible after the populated Apps control.

Ugoos/Kodi supplies an independent content comparison: PROGRAM_04 PROGRAM_LABEL
and PROGRAM_B episode 1 have failed fullscreen, while the same
playing content behind Ugoos Home could remain visible after a TV restart.
PROGRAM_A's Farm, PROGRAM_08, PROGRAM_09 and many other watched titles worked.
Samsung TV Plus usually works. Rare brief recovering picture interruptions,
sometimes with audio pauses, are a separate symptom group without a
synchronized technical capture. See the [incident comparison and timing limits](panel-idle-20261026/overnight/incident-separation-20261027z/incident-comparison.md).

A TV off/on need not reboot Linux. A compositor screenshot is not a
measurement of physical panel light. The unattended reads alone do not establish physical light. BH and BI now
add separate owner-confirmed screensaver recoveries; BH also pairs a later
clean RT run with the owner confirming that the screensaver stayed visible.

## Latest ordinary-input findings

The fixed source at `0x584109a4` has a minimum observed four-lane layout of
16 unsigned words per lane. Its enclosing packaged block is named Pre-PD;
this names neither individual fields nor their physical units or producer.
The [source trace](panel-idle-20261026/overnight/ap-table-source-20261027y/table-source-trace.md)
and [stored-value check](panel-idle-20261026/overnight/pre-pd-stored-values-20261027ab/stored-values.md)
show a stored all-zero table and a companion containing 16 descending
constants. Stored bytes do not establish live source contents.

The [companion-consumer trace](panel-idle-20261026/overnight/pre-pd-companion-consumers-20261027ac/companion-consumers.md)
recovers exact prefix/peak selection, numeric bin boundaries, tie rules,
unsigned wrap, caps and floating scaling. It distinguishes outputs
`NPC_AP+0x56/+0x58/+0x5a` from the separate divisor fields
`NPC_AP+0x16/+0x18/+0x1a`. The two sets must not be conflated. Cap arrays
belong to the enclosing packaged [NPC record](panel-idle-20261026/overnight/npc-cap-record-20261027ag/cap-record.md),
which is distinct from the RAM object NPC_AP. Their individual meanings and
live producers remain unknown.

The [reference delta](panel-idle-20261026/overnight/ap-exco-reference-delta-20261027ae/reference-delta.md)
compares the exact stored AP_EXCO initializer with W's retained prefix:
366 of 412 halfwords match, 46 differ. The 90%/98% numeric thresholds already
exist in the stored reference; they are not evidence of a live resolution
calculation. W contains mature debounce/output state and nonzero sum mirrors.

The newest [divisor provenance](panel-idle-20261026/overnight/npc-ap-divisor-provenance-20261027af/divisor-provenance.md)
finds stored defaults `1024/1024/1024`, two direct floating-input writers and
one common dispatcher. All three recomputed indexes use the same
`AP_EXCO+0xea × AP_EXCO+0xf0` numerator. With W's captured numerator and caps,
stored divisors predict indexes `3/3/3`, while W retained `6/6/6`. W did not
capture the divisors; old outputs and sequential sampling remain alternatives.
The minimum missing values are six bytes at `NPC_AP+0x16..+0x1b`. Their
transport alias and observation timing must be qualified before a new read.
AF normal/optimized verification and independent review pass after correcting
halfword truncation before clamping, the count-zero case, conditional output
copies, and the distinction between payload length and allocation extent.

The [upstream floating-input trace](panel-idle-20261026/overnight/npc-ap-floating-inputs-20261027ai/floating-inputs.md)
closes a further source-code edge: the received F3:0x128 low-ten-bit value at
NPC_AP+a6 can contribute to the saved floating triple passed to those writers.
Clamps, factors, dispatcher controls and writer gates can mask or replace the
contribution. The fourth input is feedback-derived; the integer pair is
retained before its same-pass increment. Exact code and mutation checks and
independent review pass. No physical unit or runtime branch choice is
established by this trace.

The [minimal-read qualification](panel-idle-20261026/overnight/npc-ap-read-qualification-20261027aj/read-qualification.md)
derives an eight-byte envelope at mapped address4500d730 for the missing six
bytes, wholly inside the named allocation. Its mapper/address review passes.
There is no NPC-specific live pointer gate; a future result must retain its
conditional selector-zero object interpretation. The fixed helper passed
source/build review and has now run once, as described below.

The [invocation trace](panel-idle-20261026/overnight/ordinary-invocation-20261027aa/invocation-findings.md)
recovers a registered callback and matching stored vector. Threshold 30 is an
invocation count: starting at zero under continuous qualification, F0 first
sets on call 31. Live callback/vector identity, physical IRQ source and
cadence are unmeasured. A bounded [image-1 census](panel-idle-20261026/overnight/pre-pd-cross-image-20261027ad/cross-image-census.md)
found no exact direct Pre-PD reference in the tested forms; this is not a
whole-firmware producer-absence proof.

## Subsequent offline findings and stopped recorder

The reviewed [AM writer-math trace](panel-idle-20261026/overnight/npc-ap-writer-math-20261027am/writer-math.md)
shows that the divisor pipeline reads and updates retained float tables
before applying more factors and a final transform. In its finite bounded
writer model,118 identifies only the final quantization interval
[0.115234375,0.1162109375). It does not recover upstream inputs or a producing
branch. AM did not name the final transform from its constant alone. The subsequent
AP analysis below identifies its mathematical operation from the body and tables.

The [AN sensitivity analysis](panel-idle-20261026/overnight/ordinary-condition-sensitivity-20261027an/condition-sensitivity.md)
shows why the118 measurement is not itself a repair target. With source
held fixed to the retained tail sums, divisor1024 selects the initial
tail12..14, which already exceeds the threshold in all three lanes. The
modeled mature first-helper output remains1. Extending this result to every
positive writer divisor1..1024 requires a fixed table and no u32 addition
overflow; constructed witnesses demonstrate why those qualifications matter.
The exact arithmetic and scope passed independent review. No value was changed.

The [historical inventory](panel-idle-20261026/overnight/npc-historical-evidence-20261027ao/historical-inventory.md)
finds no broader NPC_AP RAM capture in the71 scanned record.json metadata
files. Two accepted historical F3:128 readings returned207, but the latest
is about10.20hours before AK and is not raw NPC_AP+a6 RAM evidence. These
values cannot identify the factors that produced118.

A proposed combined low-level recorder was [automatically rejected and stopped](panel-idle-20261026/overnight/ordinary-onset-observer-20261027al/attempt-status.md),
with the stated reason possible cybersecurity risk. It was not built or
deployed; only a copied root adapter remains in a marked partial directory.
Root stopped dependent work without retrying or implementing an equivalent
collector. Existing reviewed readers and evidence are unchanged. Further work
is offline ordinary-writer/math analysis, separate from that rejected task.

The [AP transform analysis](panel-idle-20261026/overnight/numeric-transform-20261027ap/transform-math.md)
identifies image-0 VA2dbd0 structurally as a binary32 power operation from its
split-log2 reduction, multiply-by-exponent and exp2 reconstruction. The
ordinary caller's exact exponent is0.45454543828964233. This identifies the
mathematical operation, not a particular library implementation or universal
rounding contract. It does not identify a physical meaning or establish a
producing runtime branch.

The [AQ lookup analysis](panel-idle-20261026/overnight/npc-ap-interpolation-lookup-20261027aq/lookup-math.md)
recovers the five-point integer interpolation used by the stateful writer.
The stored X table is[1024,256,128,64,32]; its four stored Y tables bound the
unforced factor to16..1023 over the complete post-cap input domain. The
positive crossing rule excludes zero-width interior division, and the stored
products do not overflow signed32. These are package-only bounds; the live
tables and active selector were not observed. AP/AQ both pass normal and
optimized verifiers and independent instruction/math review, with no material
corrections. Review records are stored beside each report.
Neither analysis contacted or changed the TV.

## Unattended test readiness after AP/AQ

A fresh [authenticated host/UI read](panel-idle-20261026/overnight/unattended-test-assessment-20261027ar/current-ui-read.json)
at uptime133210.63 confirms the same Linux boot, cached Apps and mapped
screensaver/CSFS windows. It establishes neither physical light nor clean
controller state. No UI command, power action or USB/controller read was
performed in that check.

The [independent X reuse assessment](panel-idle-20261026/overnight/unattended-test-assessment-20261027ar/review.md)
finds that another unchanged observer run in the retained fault state would
likely repeat AlreadyFaulted/OnsetMissed. Current KEY_POWER is a toggle with
no verified two-phase standby/wake acknowledgement. No blind power sequence
or redundant X run was performed. The next causal test still requires a
visibly lit Apps control, clean first RT sample and physical onset annotation.
An optional physical-state question is pending; silence is not a picture
observation. No new collector was launched.

The same assessment also found no live first-R/clean-state acknowledgement
in X: its local inflight flag precedes remote preflight and the first read,
and its foreground root call holds the root-command gate. A future GO must
state that dispatch has begun and clean state is unknown; acceptance must be
checked retrospectively against retained read timestamps and bounded owner
annotations. No second root UI request should be assumed to run concurrently.

The [causal-gap audit](panel-idle-20261026/overnight/unattended-test-assessment-20261027ar/causal-gap-audit.md)
confirms the unresolved link between the image-1 event, actual image-0 poll
execution and emitted light. The independently reviewed [AS status-lifetime census](panel-idle-20261026/overnight/host-status-lifetime-20261027as/status-lifetime.md)
proves selected reset zero-fill, a successful startup AP-load overwrite with
stored0, and full-halfword selector overwrite. Four direct common-handler
sites supply selector0, so zero alone is not proof of no earlier error. Their
startup ordering does not prove handler return or error co-occurrence. The
linear pointer-use scan is heuristic and cannot establish a sole writer;
positive bulk copying is itself another write route. Normal/optimized
verification and10mutation checks pass after review corrected the scope and
added missing loader/wrapper linkage checks. Review closure preserves those
initial failures. None of these findings proves a physical cause or repair.

The independently reviewed [AT historical raw-zero audit](panel-idle-20261026/overnight/historical-common-status-20261027at/historical-zero.md)
recovers additional meaning from E's old64B read: raw halfword at bus4500f0f0
was0 during uptime106924.06..106924.58, conditionally the fixed common status
field under the qualified+25000000 mapping. All16authenticated calls, uploaded
helper bytes, one exact OUT12/IN64, raw bytes and clean cleanup pass. It is
at least8962.81seconds before V6, with no physical observation or uninterrupted
controller-instance proof. The later host10 record proves a kernel-written
output, not the raw controller transaction. AT therefore supplies only a
qualified raw-zero lower premise; it does not establish a raw0-to-raw10
transition or attribute it to V6. Normal/optimized verification and independent
review pass after making that missing upper premise explicit.

The [AU lifecycle readiness review](panel-idle-20261026/overnight/stock-lifecycle-followup-20261027au/readiness-review.md)
and its follow-ups distinguish a useful delayed RT-state test from a physical
recovery claim. The source trace establishes vendor configuration's idle/header
initialization, while a separate kernel/I2C lifecycle channel may qualify
without rehabilitating a rejected AVOC record. The updater and stock power
operation use distinct locks: there is a real residual scheduling race, and
the public zero/busy getters do not prove atomic exclusion. The
[practical decision](panel-idle-20261026/overnight/stock-lifecycle-followup-20261027au/practical-test-decision.md)
permits one ordinary stock action with fresh negative busy signals, a changed
status sentinel, exact transport lineage, strict capture gates and no retry.
Unknown vendor transaction phase remains a hard stop. Selector0x160 was traced
to frame mode; it is not a missing maintenance/readiness getter.

The [AV trial](panel-idle-20261026/overnight/stock-rt-lifecycle-trial-20261027av/findings.md)
obtained a fresh accepted faulted X baseline at uptime136101.80,
matching all six raw windows of the older X. It has dispatched one unchanged
stock MODE2 inside the unchanged kernel collector after the reviewed gates
passed. Pre/post host status is0x10/0; the independent error input is1/0;
selector0x128 is256/256. Independent audit accepted the lower kernel/I2C
lifecycle and cleanup; the enclosing AVOC record remains rejected for an
orphan ioctl exit. The one delayed post-X started536.016seconds after the
I2C tail and reported80clean cycles/480reads/960bulks, terminalReady with
release/close/stage removal. Only cycle80 raw bytes remain; earlier79clean
cycles are native summary. Its raw R tuple is0/0/1. These are sequential
software/input samples, not light measurements. Later UI context is cached
Apps with mapped screensaver windows; no failing For You/Live transition was
requested. A physical-picture question is pending. No firmware flash, bypass,
new native collector or automatic repeated reset was performed.

The reset-domain source audit adds a useful limit: USB re-enumeration does
not prove which core/RAM domain reset. Image1 scatter alone does not clear
the pointed-to RT object. Selected and older stored image1 slots are byte
identical, including the three-offset setter, so these two sources support
layout compatibility without proving active whole code or reset chronology.

The [AW state/input comparison](panel-idle-20261026/overnight/stock-rt-state-delta-20261027aw/findings.md)
now separates the selective RT changes from the ordinary input condition.
In saved AV pre/post windows, stored candidate limits remain200/0/0/200/40
and aa/ac remain0/2, while the alternate selector1→0 changes the conditional
mode1 source40→200; mode1 aggregate/history also clears. A new unchanged W
read then returned ordinary e6=0,2fc=0 and derived3d8=0, versus older AK's
1/0/1. Sampled setup and indexes match AK, but recomputed sum mirrors fall
from about8.25million to31,868/21,738/35,229. The source-bound restricted
model changes from true/mature to false/counter0 and matches those outputs.
This narrows the next input-producer trace without proving execution or a
physical cause. W is about13minutes later than AV's retained clean R and
does not read RT; it is not a current clean-RT/physical-state observation.
All three offline reproducers pass normal/optimized runs and independent
reviews. No UI, power or parameter action was sent in AW.

The [AX source/log follow-up](panel-idle-20261026/overnight/prepd-source-followup-20261027ax/findings.md)
reconstructs the AV kernel snapshots from their original compressed artifact.
After removing overlapping snapshot timestamps, all58retained six-label
histogram groups have identical reported values; the closest groups bracket
MODE2 without covering its interval. Copied-driver attribution of the labels
to register reads remains conditional on live binding; the observed rows do
not establish fresh content, physical light, or a dataflow to Pre-PD. A separate
bounded header-prefix trace found no new runtime producer/readiness edge;
the known bounded copy/write path remains the package loader, whose execution
was not observed. Independent review passes after these attribution qualifiers.
AX was offline
and did not change the TV. Its recovery assessment distinguishes a retained
storage backup from a demonstrated restore route. Owner willingness to flash
is recorded; neither an identified repair payload nor recoverable execution
has been established.

The [AY offline restore audit](panel-idle-20261026/overnight/restore-integrity-20261027ay/restore-integrity.md)
adds a concrete reason the existing restore function is not a demonstrated
recovery fallback. It caps the source length rather than requiring an exact
backup, accepts nonnegative short source reads while sending the requested
chunk length from a reused buffer, and has no mandatory host readback/checksum.
Its ioctl wrapper discards the restore return. These are source-level findings,
not evidence that a transfer failed on this TV or that the remote endpoint
has no internal checks. The write/read target address-space identity and an
independent recovery service remain unproved. No restore or flash was invoked.
Normal/optimized verification and six focused model/mutation checks pass;
the [independent review](panel-idle-20261026/overnight/restore-integrity-20261027ay/independent-review.md)
found no material source/control issue. This closes the bounded host restore
audit, not the blackout investigation.

The [AZ output/command trace](panel-idle-20261026/overnight/mmio-block-attribution-20261027az/findings.md)
finds all four emergency MMIO addresses also used during selected-image
initialization, including three identical address/value pairs. The code
exposes a six-block indexed configuration/status family, but the finite
primary-document search supplies no fitted-chip/register-map binding or
physical-output names. Shared addresses do not prove shared state or harmless
effects.

AZ also follows the existing mute-wire correction through the selected
controller parser: ordinary mute readback uses **F3:00 selector0x164**, not
F3:80. Older next-session descriptions using F3:80 for this read are
superseded. The getter returns1 only when word0x58200060 bits23:22 equal2;
raw0/1/3 all return0. A zero is neither raw-state-zero nor physical light.
The setter stages bits in derived MULTI/AP_EXCO+0x80; both scalar branches
set bit2, and the zero branch additionally copies two saved words into a
different fixed block. Existing W/AK/AW captures all have that staged word0,
not its immediate post-call pattern. Source checks and root independent
disassembly/raw replay pass. The staged-word consumer remains a bounded next
source lead. No target operation was made in AZ.

The [BA staged-consumer trace](panel-idle-20261026/overnight/mute-request-consumer-20261027ba/findings.md)
closes that source gap:0x314c4 consumes derived+0x80 pending/requested bits and
attempts raw2 or raw1 in the getter's field. The zero request waits for three
qualifying pending/zero-state calls after its counter reset, not a proved
time/frame delay. Pending clears after a pre-read match or unacknowledged
write attempt. Startup and gated callback0x132c0 call the consumer.
Successful registration binds that callback to descriptor8; the existing
fault teardown directly visits the same descriptor's IRQ field and invokes
the clear-enable helper. This is a positive source connection that could
interrupt later mute application, not observed live causality or a reason
to re-enable/patch the interrupt. Runtime registration/IRQ, later re-enable,
physical output and actual callback execution remain unmeasured. Normal/
optimized verification and root independent disassembly pass. BA made no
TV change. Fresh physical/RT pairing is still the first live-test requirement.

The [BB primary-log follow-up](panel-idle-20261026/overnight/primary-log-followup-20261027bb/findings.md)
reuses one unchanged fixed reader after fresh host/USB/phase-lineage checks.
It returns 3072 bytes of routine controller log text, with exact transfers,
release/close and stage removal. No `Failmode:`, `F-Set` or `F-Clr` text is
retained. This late finite buffer supplies no execution-absence, freshness,
physical-picture or prevention conclusion. `RT-P activate!` uses a separate
source logging path, so it is not a qualified expected primary-ring marker.
No UI, reset, power or firmware change was made in BB.

The [BC callback-lifecycle follow-up](panel-idle-20261026/overnight/callback-lifecycle-20261027bc/findings.md)
reconstructs the packaged descriptor-8 initializer (IRQ39, pointer58220024)
and its matching vector wrapper, which passes descriptor8 to the mute
callback. In ordinary operation, the distinct descriptor0x1c callback has a
gated pending-clear/enable path for descriptor8. Crucially, fault teardown
disables descriptor0x1c too, before descriptor8, so that ordinary handoff is
not a demonstrated post-fault recovery. The state gates read byte2000087c
twice; a later clear targets the different byte2000087e. No cadence or current
IRQ state follows. Source identity is narrower; physical causality and a
repair remain unproved. BC made no target operation.

The [BD RT refresh](panel-idle-20261026/overnight/rt-state-refresh-20261027bd/findings.md)
reuses the unchanged X observer once after fresh same-boot/device46,
unbound-interface, zero-holder and closed phase-lineage checks. It reports
80clean cycles,480exact reads/960bulks,TimeLimit/Ready/release/close and stage
removal. The retained final cycle has RT0/0/1; C/H/L match AV's earlier final
clean cycle byte-for-byte, while R has2changed bytes and M12. The gap was
unobserved. This establishes a later clean sampled software state, without
current physical light, onset, continuous-clean or recovery proof.

The later [UI log snapshot](panel-idle-20261026/overnight/ui-receiver-logs-20261027bn/findings.md)
remains rejected for stderr/PID-filter failure. Its retained filtered rows
start230seconds after the Apps-key request, so it cannot establish receipt,
rejection or nonconsumption of that request. No retry or navigation followed.

## Last controller operations and current next steps

The latest controller action is BW's single stock MODE2 after normal keys
selected Apps. The owner confirms For You was black before the two Right
keys, and Apps is visibly on after the controller restart. The prior BU
Apps-selected recovery also returned visible Apps. No additional key was
sent after either successful restart. See the [full confirmation record](panel-idle-20261026/overnight/full-confirmation-20261027bw/findings.md).

The latest direct RT observation remains BH/after-for-you-x at monotonic
157360.898267..157360.911911: AlreadyFaulted, stop1/fault0x1001/gate0.
It predates BI, BT, BU and BW; it must not be treated as current after these
controller restarts. The latest primary-ring and ordinary-input snapshots
remain BB and AW. The new kernel status queries do not replace raw RT reads.

BI's scientific bracket remains rejected and does not qualify further vendor
reads. Its later offline checksum-retry analysis is a narrower technical
finding, not repair of the rejected recording. The separately authorized
operational recoveries used the unchanged standalone stock helper, with
public reject checks and one action each. No retry loop was installed.

Leave Apps working after the requested BW cycle. The next causal experiment
still needs a qualified last-clean/first-fault observation of the actual
mode, selected limit and aggregate at the comparison edge. The BH keypress
was not proved inside its intended observation interval. The table producer,
units and final electrical light-loss edge remain unresolved. Preserve a
visible Apps/faulted counterexample if one is later measured rather than
resetting it to fit the model. No inline patch or flash is presently qualified.

## Evidence integrity and older work

The additive BH checkpoint freezes139files/85,541,114bytes with manifest
SHA-256709b1914bc031799033ee8f6188396a6292c26c3faa257ae91d765e7ee794df7.
The BI checkpoint freezes91files/84,257,027bytes with manifest
SHA-256bbe442ed4d97a48b4e6b5d1464b92ede6104ade349c5e49f013e7695f7c36dff.
Every retained file was reread against size and SHA-256 after publication.
These checkpoints preserve rejected collector artifacts alongside positive
owner reports; they do not convert rejected runs into accepted captures.

The [S–X evidence manifest](panel-idle-20261026/overnight/rt-passive-observer-20261027x/evidence-manifest.json)
freezes 98 files / 1,719,391 bytes, SHA-256
`4a68594f94a3ad5138c144cee17b4c86251efc1554ab7954df0ffa5ffbbba235`.
Publication, normal/optimized verification and independent review passed,
including unchanged M/N/O parent entries. Y–AU are additive reports/captures and
verifiers outside that frozen checkpoint; individual review records describe
accepted claims, corrections and limits. Earlier frozen artifacts are not
rewritten to hide rejected runs or superseded interpretations.

The [archived entry page](panel-idle-20261026/overnight/navigation-archive-20261027ah/current-before-restructure.md)
retains older Linux/kernel, PM, HDMI, GPIO, UI, content-policy and controller
research links. Its exact archive SHA-256 is
`1c0f64035821f4005b2f10058b0ed1e03d992899d708aa292d1a52baba04f152`.
These older findings remain available but are not all active fault hypotheses.
