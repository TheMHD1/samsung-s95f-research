# Independent policy review and corrections, October26

Scope: exact copied `libave`, `deviced`, QDF and TCON API binaries; offline
analysis only. The reviewer checked the raw instructions, symbol identities,
vtable layouts, PLT/GOT edges and decoder fixtures. The review is not an
observed blackout test or a validated repair.

## Rejected interpretations, corrected before central diagnosis use

- `ELSensing::onOffSensingByELSensingDone` at0x756f0 was initially mislabeled
  `onSensingPrepared`. Only the separately identified Y23 method at0x7d628
  has that latter identity. Both report and reproducer were corrected.
- EL start's indirect call through object+0x3c is `PowerAdapter`, not
  `OledDeviceTimer`. Its `lockBGStandby(5,0xdbba0)` call does not establish
  a fifteen-minute maintenance timer; units are not assigned in this audit.
- EL start virtuals were initially misidentified because the C++ address
  point was applied incorrectly. With symbol+8, legacy+0x30 and Y23+0x2c
  resolve to `turnOn`; both+8 resolve to `startELSensing`. The PPI enable
  request is attempted before the standby lock when the guards pass.
- The claimed absence of a direct off-sensing user caller was false.
  `gdbus_request_off_sensing` calls its ordinary user wrapper at0x5dfe0;
  its tester branch is separate. This establishes IPC capability, without
  identifying a Home/menu client. A whole-section linear decode through data
  is not a valid absence proof.
- Terminal EL callbacks cannot be called bookkeeping-only: state/reason
  branches in `stop` dispatch `stopELSensing`, which requests PPI scalar0.
- ARM `$d` literal pools initially appeared as fake instructions. Parent
  extended both daemon reproducers to honor mapping symbols and use the
  preceding section mapping at each segment boundary. The regenerated raw
  files supersede the earlier transcripts.

## Verified and added mechanisms

The reviewer corroborated the parent QDMNT arithmetic ramp,12/51..1023
host scalar clamps, relocated backend slot+0xd8, and operation18 generic
command ABI leading to0x128. A 300-invocation ramp is not a measured clock
duration or a panel power-off command.

Two additional SS caches were added to the content/duty report: backend
store0x1cb382 and QDF store0xecbc occur regardless of lower success. The
parent used the actual backend BLX site0x1cb356 (0x1cb354 is the argument
move). An identical subsequent request can skip retry at either layer.

The off-sensing report now records a corresponding TCON-state gap:
`turnOnTCON`/`turnOffTCON` call PPI at0x7b244/0x7b2e4, then cache
state1/0 at0x7b2a8/0x7b348 unconditionally. Legacy start trusts that cache
and can skip a turn-on attempt. Neither cache mechanism was observed at an
incident-aligned failure, and none was patched or forced.

## Verification and final transcript lineage

All four source hashes matched the documented acquisitions. The16 decoder
fixtures passed in both parent and independent runs. The two retained traces
still contain four complete transfers each and no mute/frame, maintenance or
dimming focus item; they are short post-onset samples without fresh physical
confirmation, not proof that no initiating request existed.

After the reviewer messages, parent added explicit stop/init ranges to the
EL reproducer and factory/wrapper ranges to the off reproducer, excluded data
pools, regenerated both successfully, and applied the terminal/cache findings
to the reports. Final raw SHA-256 values:

| Transcript | SHA-256 |
| --- | --- |
| qd-content-duty.raw.disasm | `21fc6f79803a7e1c8bcbafd395953d243546703c698f9ca89cd48c604e8c6b67` |
| deviced-el-sensing-policy.raw.disasm | `3a7c2531acdcb6ead949a1f180c3f5a89115669dd63725dbf476876edbe68741` |
| deviced-off-sensing-policy.raw.disasm | `c5605fe97e37deada844352b4f9419fd6f4567335909ca3d1588860a60d99341` |

The last two hashes differ from the reviewer's earlier snapshots because of
the documented range/mapping corrections. The reviewer did not rerun those
last parent revisions; parent ran them successfully. No live control test
occurred and no permanent fix, recovery or untethered root was established.
