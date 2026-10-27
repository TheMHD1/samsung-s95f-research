# Stock MODE2 transport audit

## Result

The one MODE2 trial did execute the stock QDF off-then-on path at the Linux
GPIO/reset/I2C boundary.  The retained kernel ring and ftrace agree on this
ordered sequence for helper PID9931:

1. QDF logged `Reset(2)` and `Tcon Power Off` at uptime94420.463964.
2. ACDET GPIO425 was driven low, and the OCL reset callback logged
   `Reset TCON power=1 ret=0`.
3. The Samsung USB device `04e8:2001`, product `STL1 CDC and Bulk`,
   disconnected.
4. QDF entered `Tcon Power On` at94421.635032; the OCL reset callback logged
   `Reset TCON power=0 ret=0`.
5. The same USB identity enumerated again, ACDET GPIO425 was driven high, and
   ERR_DET GPIO125 was sampled as raw0.
6. QDF's normal check/re-registration tail performed346complete I2C-5
   transfers to address0x76 between94422.496806 and94422.799187.  It logged
   successful init/display checks and then replayed the stored controller
   settings.

This is positive evidence that the requested stock lifecycle reached the
recovered lower callbacks; it is stronger than the helper's ioctl return0
alone.  It is **not** electrical rail-voltage proof, controller semantic
acceptance, emitted-light proof, or recovery proof.  The trial was physically
unobserved.  The containing 60-second observer record remains rejected with
`ValueError: duplicate AVOC ioctl enter`; this offline I2C decode does not and
must not rehabilitate that record.

## Preserved inputs and offline decode

The analysis used only local retained files.  No TV, root, network, GPIO,
ioctl, or controller operation was performed for this report.

| Artifact | SHA-256 |
|---|---|
| Rejected capture `sleep-mode2-20261027a.onset/record.json` | `357e7f517ff019c1f185de4233a87f1a8ccd44e9716f5ccdf9e82e003eb86df0` |
| Raw trace | `5ade657ba4c253e70cbb26eab2431a0a8bde2acd73f85386d9e7d1fce78633ab` |
| Kernel artifacts | `e95377fe9dd44cac41bcf54fe6e030a783a1d556411829545d33ebc4367379e4` |
| Vlog | `b85d7c51898abacaf4900bf74068f432d147df8a36f5d60dd90244f286e37b8a` |
| Metadata | `64cf663811e29e7a2ff8da0ffec0d4643a5140fa734604e5008eff7e173355d5` |
| Existing decoder `decode-qd-trace.py` | `cc69c38cb78c94b3e044dc546ce1d0d6328b0c2f5aace308499ead0baf375be3` |
| Static hardware-sequence report | `01cb7aa76093d74b4ccd8124a667f0d0e58c68fdde6270a010445e57606f319d` |
| Static userspace ABI report | `ff63e0c5c5c1679d870e4b816a47fcff51d6ccaf62aac0491f737962cb8e3983` |

The new local decode is
`stock-mode2-trace-decoded.json`.  The frozen decoder reports104,917 observed
event lines,379 I2C transfers, zero partial transfers, zero orphan results,
zero parse errors, `ring_accounting_complete=true`, and
`semantic_capture_complete=true` for its I2C grammar.  Those are deliberately
narrow transport properties.  The decoder does not validate the observer's
AVOC syscall-pair contract, which is where the enclosing capture failed.

The original and `partial-*` sidecars have the hashes and byte counts pinned
in the rejected record.  Cleanup and quiesce were verified, but
`accepted=false`, `technical_capture_complete=false`,
`diagnostic_eligible=false`, and there were zero observer annotations.

## Actual lower-path chronology

The managed record's `execute_uptime=94422.87` is a post-execution wrapper
anchor, not the start of the hardware action.  PID identity plus the kernel
and trace clocks place the action earlier:

| Uptime | Preserved evidence | Bounded interpretation |
|---:|---|---|
|94420.461099|ftrace `gpio_value: 425 set 0`, followed by direction/output and a second set0|Actual Linux GPIO operation.|
|94420.463964-.464004|QDF `Reset(2)`, power-off logs; frc-tcon `gpio [ac-det][425] value set [0]`|Stock off branch and named ACDET callback.|
|94420.503051-.503080|`OCL_MAILBOX Write [01 3f 01 01 00]`; `Reset TCON power=1 ret=0`; QDF reset-callback log|Lower reset request returned0; physical rail state is not measured.|
|94420.641740-.649049|USB `04e8:2001` disconnect and completion|The retained host USB stack observed disappearance of that device.|
|94421.635032|QDF `Tcon Power On`|Start of stock on branch.|
|94421.655057-.655090|`OCL_MAILBOX Write [01 3f 00 01 00]`; `Reset TCON power=0 ret=0`; QDF reset-callback log|Lower reset request returned0.|
|94422.123180-.272003|USB high-speed enumeration, identity `04e8:2001`, `STL1 CDC and Bulk`, Samsung|The same retained identity reappeared at the host USB layer.|
|94422.496752|ftrace GPIO425 set1/direction/set1|Actual Linux GPIO operation.|
|94422.496790-.496792|ftrace GPIO125 input, raw get0|Actual ERR_DET input sample in the action path.|
|94422.499661|frc-tcon ACDET GPIO425 value set1|Named callback corroborates the ftrace row.|
|94422.499691-.500114|QDF normal check tail, first `f380...0000` reply `abababab`, `TCON Access Success`|Complete I2C transfer and QDF branch/log result, not independent MCU health proof.|
|94422.683279-.683637|QDF display check and monitor status log `PMIC(OK), LPDDR4(OK) val:abababab`|Software interpretation of complete read replies.|
|94422.683703-.683707|ELVDD checker logs wait then `Stop checking due to tcon off`|The log is retained; it is not evidence that light returned.|
|94422.684050-.802091|frame-mode read0, no frame recovery, then controller-setting replay completed (`226 reg ->89 count`)|The normal on-tail progressed through state replay.|
|94422.813545|PID9931 exit; helper later records ioctl return0 and clean close|Process completion, not physical success.|

The observed approximately1.17-second off interval and the reset/ACDET order
match the platform-type-4 branch statically recovered in
`qd-power-control-hardware-sequence.md`: off ACDET, reset(1), waits; then
reset(0), waits, ACDET on, ERR_DET sample, and the normal QDF tail.  The exact
wait durations include scheduling and logging overhead.  The trace also
continued to show the AVE monitor's pre-existing `[QD_TCON_OFF] = 1` once per
second after the helper, including at94422.810,94423.810, and later samples.
That software history/cache log did not clear merely because the lifecycle
returned0.

## I2C transaction accounting

### PID9931: stock on-tail

All346 PID9931 transfers are on bus5/address0x76, are structurally complete,
have two reported messages and `ret=2`, and are classified by the decoder as
`all-messages-reported-transferred`.  Their message shapes are:

- 233 write6/read4 transfers;
- 113 write6/write4 transfers;
- 226 of the reads are `f30100000000` status-handshake reads, two after each
  of the113 setting writes;
- six are accepted `f380` reads; and
- one is the complete write6/read4 request `f30000000160 -> 00000000`, which
  the frozen decoder intentionally leaves semantically unclassified.

Initial observed reads were:

| Start uptime | Request | Reply |
|---:|---|---|
|94422.496806|`f38000000000`|`abababab`|
|94422.497226|`f38000000003`|`00000000`|
|94422.556037|`f38000000003`|`00000000`|
|94422.620047|`f38000000003`|`00000000`|
|94422.680021|`f38000000003`|`abababab`|
|94422.680389|`f38000000001`|`abababab`|

The113 writes include controller-setting replay, not merely a single power
bit.  Source-backed named examples include screen-saver method1, brightness7,
waiting policy2, slope2, low-power policy6, VRR controls0, and finally
`f30000000128 + 000000cf` at94422.792305.  Every such Linux transfer completed;
the following F301 values are retained raw in the JSON.  Neither `ret=2` nor
an F301 value is promoted here to MCU semantic acceptance.

### Post-action status and duty

The separate one-shot records are individually accepted/read-usable and have
verified cleanup.  Their bus evidence is also present in the rejected
observer trace:

- PID12004 at94425.163263: complete
  `f38000000008 -> 00000000`, bus5/address0x76, `ret=2`.  The kernel ring at
  94425.166538 logs the same PID and `ERR DET Status:0x0`.  This proves the raw
  observed controller reply was zero on that transaction.  It does not prove
  emitted light; selector08 may be read-to-clear, and the stock wrapper's
  debug-override possibilities remain part of the ABI limits.
- PID14296 at94430.337512: complete
  `f30000000128 -> 000000cf`, bus5/address0x76, `ret=2`.  The kernel ring at
  94430.340778 logs the same PID, command, and value207.  The frozen decoder
  marks this transfer's *semantic shape* false because its older whitelist
  does not classify F300 generic reads; the raw message grouping, lengths,
  reply and Linux transfer result are nevertheless complete.  Value207 is
  within the packaged low-10-bit range and agrees with the value replayed by
  PID9931.  It is not a physical-brightness or panel-current measurement.

The independent GPIO helper records a raw change from pre-action
gpiochip15/line5 value1 at uptime94417.71 to post-action value0 at94427.94.
Both reads are accepted input-only samples.  They bracket rather than sample
the transition atomically.  The mode2 trace's GPIO125 raw0 is the direct
in-action ERR_DET sample and is consistent with the later line value0.

Two further same-boot checks were made about302seconds after MODE2, outside
the capture window.  `late-status.json` (SHA-256
`130c780f7bb69f5e9028f7b0800d692072930c0c2bbeae17a43801a31a657edc`)
is accepted/read-usable and reports status0 for PID32491 at execute
uptime94724.79.  The separately retained kernel row at94724.688087 records
the same PID and raw QDF status0.  `late-pin.json` (SHA-256
`267acc2b16fc2bc4480b26d04d2af667b5f4a52290b5615d7a5025dd8a49b203`)
is accepted/read-usable and reports gpiochip15/line5 value0 at94726.97.
Thus both zero observations persisted at those later sample points.  They are
not additional coverage of the rejected observer window and still do not
identify panel light.  The authenticated `late-state.stdout` (SHA-256
`f834c24924bd00f0c41420b730912a83fe5e1aa7d28f6b98c1e60c8199de721c`)
also records global tracing off and the exact capture instance, output tree,
and stage tree absent.

## What is and is not established

Established from retained bytes:

- operation41/mode2 reached the QDF off and on bodies for PID9931;
- named ACDET GPIO and reset callbacks ran in the expected order;
- the associated USB identity disappeared and re-enumerated;
- ERR_DET was sampled low in the action path;
- the normal I2C check and controller-setting replay ran with complete Linux
  transfer accounting;
- the later raw status reply was0 and the later selector0x128 reply was207.

Not established:

- that any rail reached its specified voltage, the controller accepted every
  setting, or the panel emitted light;
- that zeros mean a healthy/lit state.  During or after a power lifecycle,
  zero may also reflect a cleared latch, an unpowered/default response, a
  read-to-clear result, or wrapper policy;
- that return0 covers every lower action.  Static analysis shows null callback
  and discarded-return paths, and QDF's status/recovery-tail returns are not
  incorporated into the mode2 result;
- that the rejected 60-second observer is technically complete or eligible
  for any absence, onset, physical-state, or causal conclusion.

The narrow conclusion is therefore: **the stock MODE2 software/hardware-I/O
sequence genuinely ran and reset/re-enumerated the controller-facing path,
but the preserved evidence does not demonstrate restored light or resolution
of the original fault.**
