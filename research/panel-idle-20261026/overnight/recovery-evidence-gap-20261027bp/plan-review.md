# Recovery evidence gap and bounded next diagnostic plan

Recorded 2026-10-27 UTC. This is an offline design review. It made no TV,
network, root, USB, I2C, GPIO, UI, power, reset or controller request and did
not build or restate an AL-style combined native collector. The owner's
currently visible screensaver is intentionally preserved.

## Why active work stopped

The investigation did not stop for lack of a hypothesis or because the two
owner-observed recoveries were dismissed. It stopped at a predeclared safety
and evidence boundary:

- BH produced a complete lower lifecycle and a valid phase premise, but that
  epoch ended before BI.
- BI again produced an owner-visible recovery, but its bracket is not valid
  for a delayed X/read. The recorder forced its vlog process to stop and the
  action PID itself recorded one failed I2C transfer.
- The current visible screensaver is therefore a valuable recovered state.
  Sending another reset, vendor header, or controller query now would change
  the state before the missing comparison is acquired.

BI's no-X/no-retry decision remains in force. Fresh USB metadata alone does
not reinstate parser readiness or repair the failed scientific bracket.

## Two different failures, not one generic “collector error”

The distinction matters for what can be learned next.

### Host recorder/export failure

BI's exact recorder `CAPTURE_WINDOW` ends `143 1 0 0 0 0`: the long-running
`vlogutil` process did not finish inside its deadline, was deliberately
terminated, and returned 143. The strict validator consequently reports
`vlog/trace/hash export failed or window malformed`. This is a host-side
coverage/completion failure. The saved 28 MB vlog may contain useful positive
rows, but it cannot support a complete-window or absence claim. Cleanup later
returned `QUIESCED` and `0\nCLEAN\n`; cleanup success does not retroactively
complete the export.

### Driver/I2C failure

The fixed decoder independently accounts for BI's entire trace ring
(`106329/106329`, zero parser errors and zero orphan results). MODE2 PID 31720
has one real failed bus transfer at uptime `157462.986311..157462.987034`:
an `F3:01` write/read receives no reply and the Linux adapter reports
`ret=-6`. It is transfer 148 of 347 for that PID. The immediately preceding
`F3:01` succeeds, and an `F3:01` about 13 ms later succeeds; 199 PID-31720
transfers follow the failure. Thus the bytes positively support a single
observed transient Linux I2C failure followed by continued replay. They do
not identify why the address did not answer, prove an electrical reset,
classify the four-byte controller status, or prove whether that one failure
affected the physical picture.

The host vlog timeout and the driver `ret=-6` are independent defects. Fixing
or reinterpreting one cannot erase the other.

## Evidence actually missing

The physical result of the Apps navigation attempts is no longer missing.
The owner confirmed after both requests that the screensaver remained visible
and no click occurred. That is positive physical observation of an unchanged
visible screensaver, not proof that AppControl did or did not execute inside
the UI framework. No further owner query is needed for that point.

| Missing fact | Why it matters | Present evidence cannot supply it |
| --- | --- | --- |
| Current RT tuple after BI recovery | Tests whether the owner-visible recovery coincided with clearing `stop/fault/gate`, as the earlier delayed AV sample did. | Public screen state, compositor rows, GPIO and generic TCON logs do not expose the RT window. X would require a vendor header and BI did not satisfy its technical phase/integrity contract. |
| Event-aligned visible-to-black comparison after recovery | Separates a stable recovered interval from the next natural relapse and tests whether host/UI state and ERR_DET change with emitted light. | Existing samples are sequential and usually after the owner report; no light sensor exists. |
| Whether `ret=-6` is isolated to reset replay or recurs during ordinary operation | A recurring ordinary-path failure would be materially different from the single observed reset-time miss. | One successful continuation proves recovery of that replay, not future reliability. Absence in an incomplete vlog cannot answer it. |
| A new positive parser-phase premise for any direct RT read | Prevents a 12-byte vendor header from being consumed in an unknown phase. | Device identity/configuration/unbound state and zero host holders are metadata, not the controller receive phase. BH clearance cannot be carried through intervening BI traffic. |

No additional static threshold, mode, or numeric-transform report closes
these gaps. The direct-RT gap requires new technical phase qualification, not
new user permission: the owner has already broadly authorized diagnosis. The
remaining ordinary evidence work can proceed offline and through existing
host/Linux read-only channels without waiting for a new blackout.

## Existing channels that do not need a vendor header or reset

These are already reviewed mechanisms, not proposed new collectors.

| Channel | Suitable now? | What it can establish | Important limit |
| --- | --- | --- | --- |
| Owner report with UTC/host receipt time | Already resolved for the Apps attempts; zero device traffic. | Both requests left the screensaver visible without a click; a future natural transition can still be timestamped. | Human observation has reaction-time uncertainty and no electrical measurement. |
| Proc/sysfs host snapshot | Yes as a current recovered-state control or after an event. Existing patterns read boot/uptime, USB identity/configuration/runtime state, interface links, and current usbfs FD holders. | Linux continuity/re-enumeration, positive driver binding, current host ownership, same-epoch anchors. | Unbound/zero-holder metadata is sampled and does not prove parser phase or no prior transaction. |
| Public VCONF/D-Bus getters from `stock-lifecycle-followup-20261027au/maintenance-preflight.md` | Yes, read-only host/service context. | Sampled software-upgrade key, `lcdon`, screen-state integer, and public burn-in Boolean. | They are daemon policy values, not emitted light, RT state, MCU state, or an atomic maintenance gate. |
| Existing host-health snapshot pattern in `current-host-health-20261027v` | Yes after a relevant transition. It reads boot/uptime, process state and retained kernel rows without opening controller USB. | Linux continuity, process survival, kernel TCON/USB/error rows already present in rings. | Log absence is not global absence; generic `QD tcon status [OK]` does not clear RT fault `0x1001`. |
| Bounded historical `vlogutil -v kerneltime -t 2` contract in `vlog-capture-contract.md` | Only as a short post-event history dump, not as a future-window recorder. | Positive log rows and their retained timestamp span if the tool finishes and row count/coverage validate. | It took about 2.84 s for a two-second history in the retained fixture. Timeout, truncation or missing span supports no absence claim. Do not reuse BI's long `-s` stream as if it passed. |
| Compositor/debugfs status already used in host artifacts | Yes as supporting host state. | Whether Linux compositor/windows/vsync bookkeeping continues. | A framebuffer/window/compositor row is not panel light. |
| `managed-errpin-cdev/run-errpin-cdev-input-once.py`, reviewed SHA-256 `cd0a34ffd719945bb369ecae16f4ca0672dbbaddea11be068e0f31465e185cde` | Only as a separately intentional one-shot after a physical transition. | One raw GPIO15/line5 logic sample with no SET-values ioctl. | It is not passive: it temporarily owns the line, requests input, and the vendor direction-input callback performs MMIO read/modify/write. It does not prove polarity, RT memory or light. Busy/nonempty line is a no-retry stop. |

The following existing tools are **not** host-only substitutes:

- `managed-tcon-status-read` and duty reads open `/dev/tztv_tcon` and perform
  controller I2C transactions. A “getter” name does not make them passive.
- X and all direct RT/context readers send vendor USB headers. They remain
  forbidden after BI until a new positive phase premise exists.
- The old observed onset recorder changes host trace state and its BI instance
  failed its own completion contract. It must not be automatically retried or
  treated as a technically qualified combined collector.
- Another MODE2 would alter the recovered state and is not diagnostic
  observation. Two owner-confirmed recoveries do not technically justify a
  reset loop.

## Concrete bounded plan

### 1. Continue now with offline driver-error propagation

The next technical task does not require the TV. Use the retained BI trace,
BH successful replay, and already copied Linux/QDF sources to trace the exact
error propagation for the failed `F3:01` transaction:

1. bind the failed transfer to its exact ordinary caller and return-value
   consumer;
2. establish whether `-6` increments a retained error/retry field, is returned
   to the operation-41 caller, or is locally tolerated before replay resumes;
3. compare the same sequence neighborhood in BH and BI, including the write
   immediately before the failed handshake and the first successful read
   after it; and
4. identify which already retained kernel/QDF log fields would distinguish a
   transient address NACK from a higher-level replay failure without naming
   electrical cause that the bytes do not prove.

This is finite propagation analysis, not another broad firmware census. Stop
at the hardware-input boundary. Do not derive a bypass, suppress error
handling, alter retry thresholds, or propose a patch from one transient
sample.

### 2. Establish one current host/Linux control if useful

The owner has already established the current physical control: the
screensaver remains visible after both Apps requests without a click. A
single existing host-only snapshot can add the matching software control
without disturbing controller state. Use the already retained command
patterns, not a new collector:

1. boot ID and uptime before/after;
2. USB identity/devnum/configuration/runtime state, interface bindings, and
   current usbfs-holder census;
3. public power/screen/burn-in/upgrade getters;
4. bounded kernel-ring rows for USB, QDF/TCON, I2C and process faults; and
5. compositor/debugfs bookkeeping if needed.

Do not include X, `/dev/tztv_tcon`, a GPIO request, a vendor USB open, a reset,
or long-running `vlogutil -s`. This control can show continued Linux/UI/USB
state while the owner sees a picture. It still cannot prove RT state or
emitted light by itself. If the exact existing command cannot satisfy its
authentication, timing and output bounds, retain the failure and do not
retry it automatically.

### 3. Prepare a conditional future-event capture after technical review

If the picture goes black without a commanded reset, first preserve the owner
description: visible source immediately before, whether the transition was
brief or persistent, whether audio continued, and the best wall-clock time.
Do not recover it immediately unless the owner prioritizes viewing over the
diagnostic.

After the exact host-only command is technically reviewed and pinned, take one
serialized host-only snapshot using the already retained command patterns:

1. boot ID and uptime before/after;
2. USB sysfs identity/devnum/configuration/runtime state, interface bindings,
   and current usbfs holder census;
3. public `GetPowerState`, `GetScreenState`, burn-in Boolean and upgrade key;
4. bounded kernel-ring rows for USB, QDF/TCON, I2C and process faults; and
5. a short completed `vlogutil -t 2` history only if it can be acquired
   immediately and its actual timestamp span/count validate.

This uses ordinary Linux/service reads. It does not open controller USB,
write controller state, or reset the panel. Save raw authenticated envelopes;
do not infer physical light from any software field.

Optionally, and only after checking its current line-identity/ownership gates,
execute the already-reviewed
ERR_DET input-once helper exactly once after the owner black report. Compare
that raw line with the already retained recovered post-BI value zero. Do not
loop it and do not retry a busy/identity/close failure.

This future-event branch is useful but is not a prerequisite for the offline
propagation work or current host-control snapshot above.

### 4. Classify the result before any controller access

The host-only comparison can answer bounded questions:

- same boot and live compositor/audio with owner-black narrows away a Linux
  reboot or entire UI death;
- a new USB disconnect/re-enumeration is positive lifecycle evidence;
- a new kernel I2C `ret<0` is positive recurrence evidence;
- ERR_DET `0 -> 1` associated with owner-visible loss strengthens the
  protection/fault association, while unchanged zero is a useful falsifier
  for “this sampled pin always asserts”; and
- public screen state remaining `1` while owner reports black confirms only
  that daemon bookkeeping and emitted light diverge.

None of these by itself identifies the damaged panel component or proves a
safe firmware bypass.

### 5. Direct RT state only after new technical phase proof

If a direct RT read remains technically necessary, stop and perform a new
phase review. The user's authority is already present; the missing input is
engineering evidence. Required inputs are a new closed-world controller
lineage and an independently established parser
reinitialization/first-header premise. Fresh metadata alone is insufficient.
Do not carry BH's prior clearance across BI, do not use BI's incomplete replay
as the premise, and do not “test” phase by sending a speculative header.

A later reviewed decision may use a new independently evidenced full device lifecycle
with complete same-identity re-enumeration and no intervening controller
actor, followed by at most one unchanged fixed reader that stops on its first
uncertainty. That requires a separate technical qualification decision, not a
new request for user permission, and is not a reason to build an
AL-equivalent combined observer.

## Stop conditions

Stop the affected operation without retry or escalation to controller access
if any of the following
occurs:

- an action would disturb the currently stable picture without adding the
  specific missing evidence; offline and host-only work may continue;
- boot, USB identity, configuration or device lineage changes unexpectedly;
- a host snapshot is unauthenticated, times out, truncates, or has ambiguous
  timestamps;
- `vlogutil` does not terminate cleanly or does not cover the claimed span;
- a USB holder/interface binding or unknown controller transaction appears;
- the GPIO line is busy, has a consumer/flags mismatch, or close is not clean;
- any proposal depends on treating public screen state, compositor state,
  generic TCON `OK`, or fresh metadata as physical light or parser readiness;
- any step would send a vendor header, controller-setting write, reset, or
  repeat MODE2 without the missing technical qualification.

## Actionable next step

Begin the offline `ret=-6` propagation trace now, comparing BI's failed
sequence with BH's successful one and pinning the caller's actual error
handling. In parallel only at the workflow level—not through a combined
collector—one existing bounded host/Linux snapshot may record the current
screensaver-visible control state without opening controller USB. A later
natural black transition is an additional conditional comparison, not a
prerequisite for continued investigation. Direct RT access remains withheld
until parser phase is technically requalified; user permission is not the
missing gate.
