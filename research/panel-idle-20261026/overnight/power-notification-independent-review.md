# Power sequence and physical timeline: independent review record

Parent-preserved record of read-only review against exact copied modules and
saved paired captures. The reviewer did not contact the TV or edit files.
This is a code/evidence review, not validation of panel recovery.

## Power implementation corrections

The reviewer corrected the initial power-sequence report in four areas:

* Monitor-mode off waits 1000ms before DVDD(0), then reaches the common final
  1000ms wait. Non-monitor off has10ms plus that final wait; platform4 adds
  100ms. The direct sleep helper wraps kernel `msleep`, establishing units.
* The normal on tail is transitively panel-command/I2C affecting through
  `m_check_tcon_status(2)`, frame recovery and cached-register recovery. The
  QDF function's own body has no direct command-helper call, but that does
  not make the whole operation GPIO-only. Nested reads/frame setters/send
  sites exist; their returns are discarded by the outer power function.
* The ERR_DET sampled word differs from the callback return. A nonzero sample,
  including a possible negative read result, bypasses recovery while setting
  cached power/PVCC=1. A request failure can leave the initialized sample0;
  the caller records the callback error yet still runs its normal recovery
  tail and sets cached on-state. The provider does not validate direction/read
  results in its own status.
* Direct-GPIO ELVDD/ACDET preserve only GPIO-request status; they discard the
  direction-output return and do not check the following set operation.
  Consequently the accumulated callback result is incomplete even before
  considering ignored recovery-tail results. Parent added the exact
  0x7ff4..0x8024 /0x81c4..0x81f4 qualification after final review requested it.

The reviewer confirmed the corrected manual CFG, cache offsets and stores,
operation mapping, flags, reset arguments and delay units. The parent narrowed
the reproducer's PASS wording: it checks exact source hashes and textual
disassembly landmarks; it does not structurally assert every branch, both
wait placements or all discarded errors. Full manual review is recorded
separately from that limited automated coverage.

## Paired physical timeline

The reviewer checked the physical labels from saved summaries, common boot
ID, P706/T1019 log identities, uptimes, decoded-stdout line/byte ranges,
terminal-string absence and the168.089s /11.001s gaps against raw sources.
No blocking timeline finding remained. Latch1 already appears around the
owner-confirmed visible Apps control, but the unsampled interval prevents
excluding a new reset/re-set/terminal action before the later black capture.
An unchanged latch value is neither a fresh off command nor a light sensor.

## Native warning, countdown and service boundary

Independent review confirms both exact catalog hashes/sizes, all seven
selected keys, and the executable's warning-key reference at0x50af60. The
copier's exact-name allowlist, persistent-only access, per-file size limits,
before/after source hash and local copy validation match its documented scope.
The326/666 application scans and1162 system-file scan are bounded scopes.

The initial native report incorrectly called60 a progress-update interval.
Review recovered Create/Reset(1000,60), counter increment,60-counter display,
counter==60 expiry and the direct off-sensing request at0x26d5b2. The ongoing
type1 notification and one-minute-timeout diagnostic corroborate intended
one-minute expiry. Return1 from the callback is not assigned an unproved
alarm-return meaning. The explicit button separately requests sensing;
event cases1/100/101 converge on timer destruction without a direct request.
Possible already-due/in-flight callback ordering remains qualified.

The exact lower library supplies mode0 and propagates the service integer
reply to the UI wrapper's zero/nonzero test. Both GetQDDisplayState and
RequestOffSensing use `/Org/Tizen/System/DeviceD/Display`; an early reviewer
short-path attribution was corrected, not retained as an ABI difference.
The local UI wrapper returns void. No inference of a live accepted request,
sensing completion or physical blackout is made from this static chain.

## Producer timing and query-contract corrections

The startup caller is the anonymous GLib callback at0x14950, not exported
Init. Its initial30 countdown invokes CheckQDDisplayState when reaching25,
on the sixth delivered callback. The exact side-effecting QD query may run
naturally; the researcher did not manually call it. Its reproducer checks
two source hashes,14 ARM sites, setter relocation/key and client bindings.

The reviewed reinforce default is172800seconds. Positive persistent time
overrides with×60 in Set48; after a cancel-key event the callback rereads
that persistent key and uses×5, otherwise14400seconds. The memory cancel key
triggers the callback but its value is not the scaled duration. The support
gate, power-state result check, software-upgrade branch and associated writes
match source. Static configured durations do not prove a live timer fired.

## Factory candidate and final bounded review

The FactoryService executable was present; a draft claim that it was missing
was corrected. Its generic decimal setter enters TransmitAItemToChip for a
resolved item. Only return0 and status byte0 lead to SetFactoryUID storage.
This proves persistence capability, not the UID506e-specific chip receiver
or an all-route maintenance-disable effect. The original absent database key
is not exactly restored merely by writing displayed0 later.

Final rechecks after these corrections found no blocking factual issue in
the native countdown, producer/query contract, timeline or factory reports.
Both countdown and factory verifiers pass. Automated coverage stays bounded
to their explicit assertions; full hardware recovery was not tested. No
notification, sensing request, power/factory control or patch was executed.
