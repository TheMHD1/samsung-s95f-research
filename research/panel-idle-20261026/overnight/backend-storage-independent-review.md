# Independent review: live backend and factory storage continuation

This record preserves the scope and corrections from read-only reviewer
`runtime_reader_review`. It is not a physical recovery report.

## Live diagnosis-backend reader

Before the single live capture, review required explicit ARM PLT/GOT binding
and a readable-range guard for the singleton pointer. Both were added and
seven host-only fixtures passed. The reviewer then independently decoded the
saved [raw capture](factory-backend-runtime-20261026T145801Z.json): exactly
44 bytes, successful transport/dd counts, matching source hashes, identity,
before/after maps and cross-stage maps, and expected pointer targets. It
cleared that bounded `accepted:true` result. This is a non-atomic capture of
userspace pointers; source-file hashes are not running-text hashes and no
factory function was invoked by the capture. Concurrent daemon activity is
not excluded.

## Storage corrections before any live setting action

The first storage interpretation used the separate 0x164-byte UI record to
classify the getter as type 1 / volatile vconf. Independent instruction review
rejected it: the actual index lookup uses 32-byte entries and UID 0x506e's
tuple has type 2. The resulting report/checker now trace NVRAM operations.

Additional reviewed corrections were:

- The public wrapper and implementation wrapper each make one or two backend
  calls depending on the first result; early failure can bypass the second.
- The logical factory-area offset and translated driver-request offset are
  distinct. The latter is not an established physical-media address.
- The TIFS simple-setter import, simple-to-detailed FC overload edge, and
  exact PRD/FC vtable slot bindings need explicit evidence beyond checking
  the eventual method bodies. They were added to the verifier.
- FC and PRD are separate implementations. Exact NVRAM/EEPROM libraries show
  their static routes reaching the same named `/dev/eeprom` interface, using
  read `0x80044906` and write `0x40044905`; neither is equated with the other.
- The full factory-interface SHA is
  `1fc40fa93b3bf81ee79b610d8c699ba94e3f4ee49e3a737d4dfe1e2e803425dd`;
  the truncated documentation copy was corrected.

The worker's revised storage report hash is
`4b5996173e7d7c9966579590b2dd49f8a80cda5f79bd8abf38f161385ab5d7ae`,
and its checker hash is
`e5f428b3b2daac8aeaa9f2ba0634b3f751754bedd184e51c31c06f851226b028`.
The parent ran the checker successfully. Final independent review of that
stable pair found no material factual blocker. Its PASS is a bounded
hash/instruction/relocation/slot landmark check, not symbolic execution or a
live API transaction.

The reviewer independently checked additional static edges not fully encoded
in the checker: nvram_inject/init_array backend slot installation, the chained
PLT-to-GOT bindings, and the `/dev/eeprom` literal and argument propagation.
These are paired static/manual findings; the checker alone is not a complete
control-flow proof.

Live PPI-table selection, EEPROM-driver persistence/notification, reload
timing, exact deletion/rollback and causal relevance to the sparse-menu
blackout remain unresolved. No getter invocation or write was performed in
this phase.

## Combined observer

The first 15-test draft was not cleared or run. Its separate
[review record](onset-capture-review.md) preserves physical-classification,
coverage, syscall ABI, process lifetime and resource-accounting defects.
The corrected observer is still under implementation and must receive a
stable-hash review before any live smoke. A physically unobserved smoke, if
later cleared, cannot establish an onset, recovery or maintenance expiry.
