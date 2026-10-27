# Controller clean-state options after the ambiguous onset launch

Recorded 2026-10-27 UTC. This is a read-only review of retained files. It made
no TV, root, network, USB, GPIO, I2C, power, UI, or controller request. It does
not propose a new reset command or treat an ordinary display action as a
controller reset.

## Conclusion

The one retained stock operation-41/mode-2 run positively establishes more
than a panel-cache or mailbox-log change: the QDF off/on path reached its lower
ACDET and OCL callbacks, Linux observed the `04e8:2001` device disappear, and
Linux then enumerated a new device at the same port with the same detailed
Samsung `STL1 CDC and Bulk` identity. The later QDF I2C check/replay tail also
completed.

It does **not** positively establish a controller-MCU reset or reinitialization
of the vendor bulk-command parser to `ReadyForHeader`. The receiver for OCL
mailbox command `0x3f` has not been recovered; the USB and I2C functions have
not been proved to be the same processor; and no retained bus-reset or startup
path is bound to the parser state machine used by the managed USB helpers.

Accordingly, mode 2 proves a fresh **host USB enumeration boundary**, not a
fresh **application protocol session**. No already-reviewed normal operation
can resolve the present protocol-state ambiguity without either already
knowing the command boundary or adding missing static reset-path proof. Mode 2
must not be treated as clean-state authorization for another vendor header on
the evidence currently retained.

## What the operation-41/mode-2 evidence proves

The managed helper requested operation decimal 41, mode 2 exactly once. Its
record reports kernel return zero and clean close, but correctly labels that
only `kernel_return_zero_only`. The stronger evidence is the independently
retained lower chronology for helper PID 9931:

| Uptime | Retained event | Supported conclusion |
|---:|---|---|
| `94420.461099` | GPIO425 ACDET driven low | A real Linux GPIO operation occurred. |
| `94420.463964` | QDF `Reset(2)` and `Tcon Power Off` | The stock mode-2 off body ran. |
| `94420.503051` | OCL mailbox `Write [01 3f 01 01 00]` | Command `0x3f` with one-byte value 1 was requested. |
| `94420.503080` | `Reset TCON power=1 ret=0` | The named lower callback returned zero; this is not an electrical measurement. |
| `94420.641740..94420.649049` | USB `04e8:2001` disconnect | Linux observed the USB device disappear. |
| `94421.635032` | QDF `Tcon Power On` | The stock on body began. |
| `94421.655057` | OCL mailbox `Write [01 3f 00 01 00]` | Command `0x3f` with one-byte value 0 was requested. |
| `94421.655090` | `Reset TCON power=0 ret=0` | The named lower callback returned zero. |
| `94422.123180` | New high-speed USB device on `7-1` | A new host enumeration began. |
| `94422.271427..94422.271451` | Samsung `04e8:2001`, revision 2.50, product `STL1 CDC and Bulk`, serial `0x12345678` | The reappearing device presented the same detailed identity. |
| `94422.496752..94422.496792` | ACDET high and ERR_DET raw zero | The later stock-on GPIO work ran. |
| `94422.496806..94422.799187` | 346 complete I2C-5/address-`0x76` transfers | The QDF normal check and cached-setting replay tail ran. |

The QDF status path accepted its `F3:0x0000 -> abababab` comparison and logged
`TCON Access Success`. This establishes that the separate controller-facing
I2C path completed that check. It does not establish the state of the USB
vendor parser.

The containing 60-second observer remains rejected for a duplicate AVOC
syscall-enter record. That rejection prevents whole-capture, absence, onset,
and physical-state claims. It does not erase the narrower complete kernel/USB
chronology or the separately decoded I2C transaction accounting.

## Why this is not proof of an MCU or parser reset

Static analysis binds the QDF platform-type-4 callback to exported
`sdp_ocl_reset_tcon_power`. The copied provider sends
`SDP_OCL_I2C_MBox_Write(op=1, command=0x3f, length=1, payload=value)`. The
observed OCL rows match that envelope. The receiver implementation for
command `0x3f` is still missing, so the following remain unknown:

- which electrical or logical reset domain values 1 and 0 control;
- whether the USB function's MCU, its RAM, or only a PHY/shared rail resets;
- whether the OCL receiver, USB function, and I2C address `0x76` are one
  processor;
- whether parser phase/state storage is cleared or reconstructed; and
- whether the first accepted vendor OUT after enumeration expects a new
  12-byte header.

The selected packaged image contains a USB personality strongly concordant
with the retained descriptors, but packaged identity is not live executable
identity. Later live callback pointers matching the packaged generation do
not make every immutable body or reset path equal. No retained transaction
captures the vendor bulk parser's initialization during the mode-2 USB
transition.

The stable product, revision, and serial are identity evidence only. They are
compatible with several unseparated mechanisms, including a device-function
restart, shared-power interruption, or PHY/hub-visible reset. Re-enumeration
also proves that the USB control plane could answer descriptor requests; it
does not prove that the independent vendor bulk application parser was reset.

The packaged CDC DTR rising-edge path clears local USBSerial
ring/transfer bookkeeping and primes receive state. That is a distinct,
state-changing CDC path, not evidence about the vendor bulk parser and not a
passive clean-state test.

## Already-reviewed operations and what each can establish

| Existing operation/evidence | Fresh host USB enumeration | Known vendor parser boundary | Fresh MCU/parser session | Present applicability |
|---|---:|---:|---:|---|
| Stock operation 41/mode 2 | **Yes**, in the one retained run | No | No | Establishes reset-coupled USB chronology only. It is an invasive QDF power lifecycle, not a proved parser reset. |
| Completed D6 three-second logger qualification | No | **Yes**, final phase `ReadyForHeader` after 16 exact transfers | No | Establishes the parser boundary at that completed invocation only. It does not make a later ambiguous invocation disappear. |
| USB open/claim/release/close | No | No | No | Manages the Linux handle/interface. No retained code or trace binds it to parser initialization. |
| CDC open or DTR transition | No | No | No | Separate state-changing CDC bookkeeping path; not a vendor-parser proof. |
| Normal Apps/For You AppControl or the marker-only launcher qualification | No | No | No | Does not contact the controller USB interface. It cannot classify controller protocol state. |
| Ordinary FRC PM suspend/resume | Not established | No | No | Static source uses a distinct unresolved `set_power_mode` callback plus conditional work. No retained run binds it to parser reset. |

The D6 qualification is the strongest prior protocol-boundary evidence: its
accepted native outcome ended in `ReadyForHeader`, with exact counts, verified
restore, release, and close. It is not a reset or a perpetual property. The
later D7 control-smoke-v2 record has a launch receipt but no supervisor PID,
stat, ready, stdout, or exit artifact. Because the failed supervisor used
`set -u`, absence of those files does not prove that the native process made
zero controller transfers. Its lineage is therefore unresolved. Starting a
new protocol transaction to discover that state would itself assume the
boundary that needs proof.

## What evidence would close the gap

A positive clean-state conclusion would require at least one of these bounded
proofs; none is present now:

1. Recover the actual command-`0x3f` receiver and prove that its observed
   value-1/value-0 path resets the processor and state memory containing the
   vendor parser.
2. Bind the running USB implementation to a reset/enumeration initializer that
   positively stores the parser's header-wait state, and prove that initializer
   executes across the observed disconnect/re-enumeration.
3. Retain an exact, accepted first vendor transaction after a proved reset and
   show it finishes at the modeled header boundary. This would be active
   controller traffic and is outside this report's read-only scope.

Passive Linux enumeration rows, an unchanged boot ID, process absence, stage
files, I2C success, GPIO status, or an ordinary UI action cannot substitute
for those edges.

## Decision for the current D7 state

There is no evidence-backed, already-reviewed normal action that converts the
current unresolved vendor-protocol lineage into a positively fresh parser
session. Operation 41/mode 2 is not cleared for that purpose by this review.
The correct current classification remains **protocol state unresolved; no
new vendor header based solely on mode-2 reset assumptions**.

This conclusion does not claim that the mode-2 sequence failed to reset an
MCU. It says only that the retained observations and copied source do not
prove that stronger fact.

## Provenance

| Artifact | SHA-256 |
|---|---|
| `sleep-investigation-20261027a/stock-mode2-transport-audit.md` | `70b0d0f2f7a8301d2b598d45a3510a4304bd493c2e7507e0bb1c8f270baf8847` |
| `sleep-investigation-20261027a/mode2-sequence-runtime-audit.md` | `e36f4893ba935da41674aaa804e4ce72694e90f55775a15e4c0347c600b2df65` |
| `sleep-investigation-20261027a/reset-coupled-usb-identity-provenance.md` | `7b8f86f4f1a685e011002d7d960c6712af31f8b28072a2511b6f843c80a2c45a` |
| `sleep-investigation-20261027a/stock-mode2-trial/mode2.json` | `5571bc79ca021113f76428969f8f6d2e3ebf18224438e5cd168cfb5a9ec315d2` |
| `sleep-investigation-20261027a/stock-mode2-trial/outcome.json` | `647723f1950603a1423f5ded97e1d5e74bfc06fc7d65ce0b29573bc43ee505e2` |
| `tcon-research/qd-full-reset-versus-mode2.md` | `82e44c95ed0c49482a023cbbf6973e571e76ace4ceb57ccea506535bbbdda904` |
| `tcon-research/qd-power-control-userspace-abi.md` | `ff63e0c5c5c1679d870e4b816a47fcff51d6ccaf62aac0491f737962cb8e3983` |
| `tcon-research/qd-power-control-hardware-sequence.md` | `01cb7aa76093d74b4ccd8124a667f0d0e58c68fdde6270a010445e57606f319d` |
| `tcon-research/qd-mode2-reported-fault-clear-semantics.md` | `10bd7a11c7bd0fbc7620929b7700bdff56f516bbf87622cb9698f64defc3e3a7` |
| `volatile-logger-qualification-20261027f/independent-runtime-review.md` | `e315bcae9a979060960ea9b9f111ade719b21e78d13e8e756a500a5268a2d2aa` |
| `finite-onset-logger-20261027g/control-smoke-v2/record.json` | `db6046dd91f056c7c0649adea3b933a2bd1399e36d91dd532827d4d96334fd02` |
| `finite-onset-logger-20261027g/control-smoke-v2/missing-completion-metadata.json` | `aa64bbe1df60332b218163c9cd91b7b93f49610d5df24c1e7e5d5fc9cb972da2` |
