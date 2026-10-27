# Stock reset result and next discriminating tests

Recorded 2026-10-27 UTC. This is a mutable test plan, not a record that the
future tests have happened. The owner authorized unattended diagnostics and
consideration of deeper changes, including flashing. Avoiding a brick remains
an explicit requirement. The panel's physical state after the latest action
has not been observed.

## What actually changed

The owner previously reported content-dependent persistent physical blackouts
with the TV still responding and sometimes continuing audio. Full Apps and
the Ugoos library overlay often keep the picture visible; sparse For You/Live
and full-screen PROGRAM_LABEL/PROGRAM_B can trigger loss. The same
failing episodes can reportedly play behind the Ugoos menu after restart.
Working titles span SDR/HDR, codecs and frame rates. The damaged patch and
vertical dark line are documented separately; their electrical connection to
the whole-panel event is not yet proved.

Earlier visible Apps and black For You observations had sequential accepted
status/pin pairs0/0 and0x10/1. PROGRAM_04 black state also had0x10/1.
This establishes a useful discriminator. It does not establish whether the
RT-labelled protection initiated the blackout or responded to another fault.

During the unattended block, one stock panel lifecycle operation41/mode2 was
executed. It was not a Linux reboot or an installed retry loop. Exact anchors:

| Observation | Target uptime | Result |
| --- | ---: | --- |
| Last pre-action status query | 93259.94 wrapper completion | 0x10; raw kernel row93259.828033 |
| Pre-action independent pin | 94417.71 wrapper completion | 1 |
| Actual stock power-off branch | 94420.463964 kernel log | ACDET/reset sequence begins |
| Actual stock on-tail | 94422.496790 onward | in-action ERR sample0, complete checks/replay |
| Power helper wrapper completion | 94422.87 | kernel return0, helper cleanup confirmed |
| Immediate independent status | 94425.24 wrapper completion | 0 |
| Immediate independent pin | 94427.94 wrapper completion | 0 |
| Post-action drive selector0x128 | 94430.42 wrapper completion | 207 |
| Later independent status/pin | 94724.79 / 94726.97 | 0 / 0 |

The last pre-action status read is about19minutes before the action; the
pre-action pin is only a few seconds before it. No continuous fault-status
measurement is claimed. The later pair is about302seconds after the power
helper completed; no continuity between samples is claimed either. All share
the same Linux boot UUID. Managed execute_uptime anchors are post-execution
wrapper observations, not the time of the first hardware operation.

The reset-coupled USB disconnect/re-enumeration and346complete PID9931 I2C
transfers show the lower stock path ran. The surrounding60-second capture is
still rejected for a duplicate AVOC syscall-enter before the action. The
separate raw transport audit has379complete transfers; these are different
counts and different validation domains.

## First owner observation: preserve the current state

Before another Power press, reboot or navigation, record whether the physical
picture is visible, still black, or the TV is completely off. A pending owner
question already requests this. No further control is needed to answer it.

| Owner observation after the already-executed action | Interpretation and next step |
| --- | --- |
| Picture visible | First physical evidence that the stock panel cycle can recover this instance without a Linux reboot. Confirm source/page and timing, then separately test recurrence. It does not establish prevention. |
| Picture black, TV responsive | The reported fault/pin change did not establish emitted light. Do not install a reset loop; inspect stream/output state and controller-local diagnostics. |
| TV fully off | Distinguish whole-device power state from the prior audio-alive panel failure before drawing a recovery conclusion. |

## Controlled recurrence comparison

After a visible baseline is restored, keep source, HDMI timing, picture mode
and chosen episode fixed. Arm a finite observer, confirm its start marker,
then give the owner GO immediately. Retain ordinary overlays and full-screen
playback as separate trials. Do not use an unannounced transition as baseline.

The useful paired sequence is visible Ugoos menu with the same failing
episode playing behind it, then full-screen playback. Record actual HDMI
timing/HDR state and hardware input histogram context in both conditions.
Those variables can change when an overlay opens; the source file alone
does not fix them. A separate visible Apps→For You trial tests the built-in UI
path without HDMI. Do not combine the two paths into one onset assertion.

For every transition, preserve physical visible/black/audio observations,
complete typed controller transactions, GPIO/reset events, stock QDF logs,
AVE monitor latch/retry state and process identity. A status/pin pair after
the owner report is sequential follow-up evidence, not an onset timestamp.
If black occurs with0/0 rather than0x10/1, keep it as a separate failure
signature instead of assuming every blackout has the same mechanism.

## Logging and reverse-engineering work that remains

1. The new two-second, all-syscall AVEMon capture has now passed its separate
   technical/pairing audit: 1,922 retained events, zero reported ring loss,
   and 959 complete ordered interior syscall pairs, with explicit leading
   exit and trailing entry half-pairs. This addresses a bounded recorder
   question, not the old capture anomaly or physical onset. Preserve all
   rejected predecessors. An ambiguous AVOC return remains ineligible for
   ioctl attribution even when its complete I2C inventory is separately usable.
2. Reduce recorder load before attempting a long window. The old smoke's
   vlog rate projects beyond64MiB, and its MemAvailable would fail the new
   larger recorder's384MiB preflight. A longer duration is not qualified by
   the five-second smoke.
3. Trace the reset-coupled USB device's command ingress to an exact bounded
   diagnostic read, if one exists. New cached metadata positively identifies
   ttyUSB0 as the separate SmartThings dongle. The I2C getters and recovered
   CDC RX machinery do not currently provide the missing RT-history route.
   Work now targets the vendor-bulk read handler and stock backup bootstrap.
   A protocol header is active I/O, which the owner authorizes; the useful
   engineering questions are its storage mapping, side effects and complete
   byte-count validation. See the [new work log](../rt-telemetry-followup-20261027b/README.md).
4. Resolve the executable or hardware bridge between image1 local RT field
   0x2001240a and image0 reader0x4701240a. Matching object offsets and names
   alone are insufficient. Current controller-image equality also remains
   unverified.
5. Keep AVE history and QDF lifecycle caches distinct. AVE QD_TCON_OFF=1
   remained after the single stock cycle and suppresses later monitor
   sampling; QDF's separate cached power word explains its ELVDD checker log.
   Neither is a measurement of panel light. No monitor-memory write has been
   deployed.
6. A tracepoint-only kernel observer module is a possible engineering route,
   because its registration APIs are positively exported and non-stub in the
   exact retained Image. It does not supply arbitrary function probes. The
   installed modules' custom vermagic and Samsung UEP trailers, exact build
   headers/configuration and ABI acceptance must be resolved before loading
   a newly built observer. No kernel module was built or loaded in this block.

Flashing or protection suppression is not a demonstrated fix. Before choosing
either, the technical missing pieces are the fault-producing branch, the
specific byte/state change, installed-image compatibility and a tested
recovery route. These are engineering requirements for avoiding a brick,
not a new request for user authorization.

## Evidence links

- [Block overview](README.md)
- [Actual MODE2 transport](stock-mode2-transport-audit.md)
- [Helper/capture runtime audit](mode2-sequence-runtime-audit.md)
- [Reset-coupled USB identity](reset-coupled-usb-identity-provenance.md)
- [MODE2 fault-state semantics](../../tcon-research/qd-mode2-reported-fault-clear-semantics.md)
- [Future parser design](duplicate-avoc-parser-design.md)
- [Owner overlay/full-screen controls](../ugoos-overlay-paired-control-20261027.md)
