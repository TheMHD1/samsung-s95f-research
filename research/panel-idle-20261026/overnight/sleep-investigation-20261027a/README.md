# Investigation while the owner sleeps — 27 October 2026

The owner left the panel black after returning to For You and then explicitly
authorized commands, tests, reversible instrumentation, and consideration of
firmware/protection changes without visual feedback. The requested constraint
is avoiding a brick. The earlier collection hold is superseded. Every new
physical outcome is **unobserved** until the owner can confirm emitted light.

## New measured result

One stock off-then-on panel lifecycle request (operation41, mode2) has now
been executed, exactly once, on the same Linux boot. The pre-action ERR_DET
input was1. The immediate post-action status was0 and ERR_DET was0 in
separate sequential samples; one deliberate later sequential check, about
302seconds after helper wrapper completion, again returned0/0.
Every individual helper completed and cleaned up. The drive selector remained
207. The owner was asleep: **physical picture recovery is unobserved**.

The raw trace and kernel records establish that this request reached the
stock lower path: ACDET low, reset-mailbox1, USB04e8:2001 disconnect, reset0,
USB re-enumeration, ACDET high, ERR_DET sample0, then346complete controller
I2C transfers for checks and settings replay. This is stronger evidence than
a zero ioctl return, but it does not prove rail voltages, light or prevention.
The host QD_TCON_OFF history/cache flag remained1.

The encompassing60-second capture remains **rejected** for an actual duplicate
AVOC syscall-enter before the power action. Its rejection is preserved; no
process crash or reset cause follows from that pairing failure. The separate
raw I2C decoder reports379complete transfers and no partial/orphan transfers.
See [transport audit](stock-mode2-transport-audit.md),
[sequence audit](mode2-sequence-runtime-audit.md), and
`stock-mode2-trial/outcome.json`. This was not a reset loop. All target trace,
stage and output paths were removed and global tracing was0 afterward.

### Pre-action controller-value measurements

One newly prepared, independently reviewed fixed controller-value query
completed successfully and cleaned up. The selector was hexadecimal0x128,
operation decimal19. The sentinel changed to207, with unchanged command words
and successful ioctl/close. The independent raw kernel row agrees:

```text
[93210.778827] QDFTcon_ReadOneCommand[4231:ManagedTconDuty]: cmd = 0xF30000000128, value =207
```

A subsequent single stock status query also completed and cleaned up. It
returned0x10; its matching raw kernel row is:

```text
[93259.828033] QDFTcon_GetErrDetStatus[4792:TconStatusRead.]: ERR DET Status:0x10
```

Both are on Linux boot `00000000-0000-4000-8000-000000000000`. They are
sequential, about49seconds apart, rather than atomic simultaneous samples.
The preceding accepted five-second passive capture supplies separate software
cache context. No physical recovery or brightness is inferred. The new result
weakens the simple claim that the stored0x128 drive value must have become
zero to explain the persistent fault. The exact RT subcause remains unknown.

Raw evidence: `controller-duty-once.json`, `duty-log.stdout`,
`status-after-duty.json`, `status-log.stdout`. The active controller request
is not a passive memory read. No private firmware-update flag was observed,
so concurrency with such an operation is not formally excluded. The status
wrapper has its own flash-update guard; the generic-value wrapper does not.

## Logger work actually tested

The five-second SDP/console checkpoint probe captured48/48records with zero
per-CPU loss and removed its private trace instance. All46non-marker records
were console output; the four selected memory-driver events emitted no rows.
Its default trace clock differs from uptime/embedded-printk by about61.5s;
those domains must not be merged numerically.

The new longer-recorder implementation then passed20offline tests normally
and under optimized Python and completed a separate five-second target smoke:
`sleep-smoke-20261027a.onset`. That run is accepted as an instrumentation test,
retains9,932/9,932trace events, and has verified cleanup. It deliberately has
no physical annotations and is not a blackout-onset or repair record. Its
private trace clock was explicitly mono and agreed with marker uptime.

Separate AVEMonMain syscall-filter probes were subsequently performed without
UI or controller commands. V1 rejected a padded per-CPU timestamp format;
V2 retained zero-loss CPU statistics but rejected its475651-byte raw trace
against a40000-byte export cap. Neither exported a syscall trace, and both
cleaned up. A separately reviewed V3 uses a2-second window and bounded
gzip/base64 export. It retained a190711-byte decoded trace with1922/1922
events and verified cleanup. Parent and independent CRC/decoded-length checks
pass. The [separate runtime audit](avemon-all-syscalls-20261027c-runtime-audit.md)
qualifies its narrow transport/interior-pair inventory:959complete ordered
pairs, with an initial exit and final entry explicitly retained as boundary
half-pairs. There is no interior duplicate or ID mismatch in this2-second
sample. The source receipt remains unaccepted; the separate eligibility JSON
records the scoped decision. This does not explain the earlier anomaly or
establish whole-window pairing. No old rejected record is reclassified.

The smoke does not qualify180-second capacity. Its vlog contained4,632,040B
over about9.992s; simple scaling to185s predicts roughly85.8MB, above the
old64MiB cap. A separate budget revision is prepared and independently
reviewed offline, but has not run on the TV. It requires384MiB MemAvailable
before allocating its larger ring; the last smoke's351804KiB would fail that
guard. Its180-second capacity remains unqualified. Earlier rejected
capture records remain rejected; the narrower heap-growth policy does not
retroactively change their status.

## Where the reverse engineering now points

1. **Fault plus nonzero drive:** distinguish controller protection/latching
   from an ordinary scalar zero-brightness request. Do not infer that207
   means actual panel current or light.
2. **Same episode, UI overlay versus full screen:** retain actual HDMI
   timing/color/PQ state and host image-statistic logs. Both photographs show
   a visible library UI with the failing episode in the current-playing
   label; the featured title is a separate item. The owner reports that
   returning to full screen causes the blackout after restart.
3. **Controller scan input:** normal packaged startup installs a conditional
   scan path and a hardware-data buffer producer. The descriptor units,
   runtime gates and connection to the live RT indication remain unresolved.
4. **Recovery mechanism:** the stock AVE -> ioctl operation41 -> QDF
   lifecycle is reconstructed, independently reviewed and now exercised once.
   Its lower sequence is observed; separate status and ERR_DET samples were
   zero immediately afterward and at the later approximatelyfive-minute
   check. Continuity between samples and status latch/read semantics remain
   unproved. Physical recovery and persistence under
   known triggering content remain untested.
5. **Reset-coupled USB endpoint:** the disconnect/re-enumeration now gives a
   concrete topology/lifecycle association. It does not by itself identify
   the device as a particular controller core or establish a safe USB command
   protocol. Offline identity and logging analysis continues.

The live kernel has static trace events but only the nop tracer at the checked
surface. Dynamic kprobe/uprobe, kallsyms, dynamic-debug control and the three
TCON modules' parameter directories were absent. Existing `ftrace/function`
format metadata alone does not establish an attachable function tracer.
The exact Image does export working tracepoint registration/enumeration APIs,
so a tracepoint-only observer module is theoretically possible. Matching
headers/configuration, module ABI and Samsung UEP acceptance are unresolved;
no new module has been built or loaded. Arbitrary kprobe/kretprobe and
function-ftrace registration APIs were not found among the reconstructed
exports. See the [kernel capability audit](../../tcon-research/kernel-instrumentation-capability-audit-20261027.md).

## Related source reports

- [Controller-value runtime audit](controller-duty-runtime-audit.md)
- [Stock reset result and next tests](diagnostic-next-tests.md)
- [MODE2 transport audit](stock-mode2-transport-audit.md)
- [MODE2 sequence runtime audit](mode2-sequence-runtime-audit.md)
- [Reset-coupled USB identity](reset-coupled-usb-identity-provenance.md)
- [Future syscall/transport parser design](duplicate-avoc-parser-design.md)
- [Checkpoint runtime audit](sdp-checkpoint-runtime-audit.md)
- [Function logging plan](../../tcon-research/qd-function-logging-plan-20261027.md)
- [Stock power-control ABI](../../tcon-research/qd-power-control-userspace-abi.md)
- [Fault-state semantics after MODE2](../../tcon-research/qd-mode2-reported-fault-clear-semantics.md)
- [RT-window alias evidence](../../tcon-research/qd-rt-window-alias-evidence-20261027.md)
- [RT-window reset output](../../tcon-research/qd-rt-window-reset-output-20261027.md)
- [USB versus UART RT-field reader](../../tcon-research/qd-usb-ap-rtp-logical-read-route.md)
- [Logical RT-field read review correction](../../tcon-research/qd-usb-ap-rtp-logical-read-route-review-erratum.md)
- [RTP scan invocation](../../tcon-research/qd-rtp-scan-invocation.md)
- [Host histogram provenance](../../tcon-research/drm-histogram-logging-provenance.md)
- [Overlay/full-screen evidence](../ugoos-overlay-paired-control-20261027.md)

No kernel replacement, controller firmware flash, EEPROM write or protection
change has been performed in this block. No persistent blackout fix is yet
established. These are progress and evidence records, not completion claims.

**Reader review correction:** an interim independent review incorrectly
reversed the unsigned comparison at the generic reader's CMP/BHI branch.
The parent independently disassembled it: with row length0x100 and low
offset0x0a, BHI is taken to the first-region path. The original mapping
`0x21000a -> 0x4701240a`, count1word/2bytes, is supported. The new branch
checker covers both outcomes and the equality boundary. The interim review
is retained as superseded history; it does not supersede the earlier loader
binding. A USB ingress to that reader remains unproved, and no proposed
logical-address command was sent. Live status, GPIO and MODE2 evidence are
unaffected.

## Frozen evidence snapshot

[sleep-evidence-manifest.json](sleep-evidence-manifest.json) pins260files and
98276246bytes, including the rejected MODE2 bracket, independently audited
transport, immediate/later helpers, all three new syscall probe attempts,
source/build payloads and static reports. SHA-256:
`956d690aae4dad5309db6af6324c329d4e67bf29f8bd9e7601f8c26ae4157296`.
Normal and optimized verification passed; a second publication was refused
without changing the manifest. This README and the next-test plan are mutable
navigation and are explicitly outside the snapshot. Later additional files
are also outside its explicit file list. Publishing the index does not change
any capture's eligibility or establish physical recovery.

The [post-publication independent audit](sleep-evidence-publication-audit.md)
separately checked all260rows, sizes and hashes. It is a later file outside
the snapshot. The subsequent [official kernel-source feasibility note](../../tcon-research/qn77s95f-official-kernel-source-feasibility.md)
is also outside that snapshot: official material identifies the model/platform
family but does not yet bind an available source tree and generated ABI
artifacts to this exact installed build. No source request was submitted.
