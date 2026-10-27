# Notification, factory receiver and ARM32 availability follow-up

This phase continues the owner's request for deep diagnosis without requiring
a remote-control test from the absent physical observer. No repair is verified.
The owner clarified that the visible damaged patch is no larger than a thumb;
the two closeups were viewed, and that scale remains an owner estimate.

## Work and evidence boundaries

1. The exact installed notification client, provider daemon and provider library
   were acquired with source/copy SHA and length checks. The real system-bus
   destination is `org.tizen.data_provider_service`; the noti and noti_event
   names are interfaces. The service runs as app_fw with System SMACK label.
   [The cancellation contract](../idle-research/stock-notification-cancellation-contract.md)
   now traces successful legacy deletion with changed-count>0 to
   delete_single_notify(1,priv_id,uid), then the client's detailed callback
   event1 and the viewer's local countdown destruction. This depends on active
   registration and delivery; it does not undo an issued sensing request,
   disable policy or prevent future reinforcement. No lookup, deletion,
   synthetic event or app-control payload was sent.
2. Independent review rejected the intermediate factory selector mapping.
   FactoryIndex slot4=5 is not the runtime driver-module field. The serialized
   record's+0x44 is16 and survives the construction copy. Selector16 calls two
   PPI routes. The [transmit audit](../tcon-research/factory-off-sensing-transmit-target.md)
   follows the real VE/AVE and diagnosis receivers, with conditional storage.
   Under the statically paired/non-error route, AVE FRC/TCON perform no lower
   setter for this UID and diagnosis returns-95 without changing status. TIFS
   discards that return, preserves skip=false and reaches storage. The actual
   live backend pointer and any write/reload are unobserved. These corrections
   happened before any factory write; none has been made.
3. The existing CLR was located and pinned by SHA. One independently reviewed
   ARM32 probe completed at14:22:30: BPF and perf both returned ENOSYS. Its
   source, runner, artifacts, raw transport and cleanup evidence are in
   [managed-kernel-abi-probe](managed-kernel-abi-probe/README.md). The earlier
   ARM64 native helper remains unexecuted; there was no execution-policy change.
4. A passive factory-process map and eight-byte GOT read resolved the real
   diagnosis function to `libvideo-misc.so.0.1.0`, replacing a dependency-only
   guess. PID1085/start1203 remained the same before/after the read; installed
   TIFSDaemon SHA matched the offline copy. Neither function was invoked.

## Retained raw observations

All paths below are in `overnight/` unless otherwise stated. File contents
retain exact commands, timestamps, stdout, stderr and exit status, including
failed glob lookups and missing-file discovery results.

| File | Purpose / result |
| --- | --- |
| installed-observer-runtime-lookup-20261026T140355Z.json | Installed command lookup: dotnet present, common alternative interpreters absent from PATH. |
| installed-dotnet-runtime-discovery-20261026T140457Z.json | ELF32 ARM launcher; unsupported list-runtimes option prints custom help. |
| runtime-and-notification-provider-discovery-20261026T141120Z.json | Bounded path search; initial maxdepth4 misses the deeper CLR path; provider service/config found. |
| runtime-and-provider-targets-20261026T141158Z.json | Framework symlink points to6.0.9; unit ExecStart names data-provider-master; notification runtime config targets net6.0. |
| installed-clr-identity-20261026T141257Z.json | Exact launcher/CLR/CoreLib hashes, ARM header and framework paths; absent .version retained. |
| factory-diagnosis-library-path-20261026T141550Z.json | Power-control wrapper found in/usr/lib; absence under/prd retained, not treated as symbol-provider proof. |
| factory-daemon-runtime-maps-20261026T142126Z.json | TIFSDaemon PID1085/start1203 and mapped provider implementations. |
| factory-live-ppi-got-20261026T142147Z.json | GOT0x165924→0x47590fd9/libvideo-misc; GOT0x1650d4→0x46f3cc35/libvideoenhance, eight total memory bytes. |
| managed-kernel-abi-probe/result-20261026T142228Z.json | Actual ARM32 probe, two ENOSYS returns, eight clean root calls, confirmed private-directory removal. |

The source-acquisition allowlist/manifest were deliberately extended beyond
the prior phase snapshot. That prior snapshot is historical and is not
rewritten to conceal the later changes. The current phase manifest records
the new copies and resulting documentation separately.

## Remaining diagnosis requirements

The [independent review record](factory-notification-abi-independent-review.md)
retains the rejected field mapping, discarded-error mistake, checker defects,
ABI validation and the separation between observed pointers and paired static
implementations. Passing exact-site checks do not replace manual path review.

The owner-observed sparse-menu blackout still needs a capture aligned to its
physical transition, distinct from the fully traced warning countdown. The
visible/black pair showed changing composed frames and a history latch in
both states; it did not identify the initiating lower-level command. Factory
value6's classifier predicate is not proof of all-route maintenance disable,
nor a repair for a damaged panel. A successful source audit is not a physical
recovery/prevention result. Root remains host-assisted, not permanent.
