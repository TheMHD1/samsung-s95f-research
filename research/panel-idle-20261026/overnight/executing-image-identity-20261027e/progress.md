# Controller live identity, state and internal logs — 2026-10-27

## Owner authorization and physical limits

The owner now permits protection bypasses and flashing if needed, while
retaining the requirement to avoid bricking the TV. This block performed
read-only controller/state acquisition and one existing QDF status getter.
It did not flash, write EEPROM, modify a kernel, bypass protection, reset a
controller, or establish permanent root. Root remains host-assisted.
The owner is asleep and no emitted-light observation accompanies these reads.

## Concrete results

1. The first CPU-address callback read returned64 zeros. It used the wrong
   namespace and is explicitly inconclusive. Static mapper/buffer dataflow
   established the correct DMA alias. The corrected0x45000580 read returned
   all64 bytes byte-for-byte equal to the packaged241230A initializer. Six
   callback pointers differ from the older241205A stored image. This is live
   callback-generation evidence, not whole-code equality or a boot-source proof.
2. The secondary window0x470004c0 exposes the expected context-root value
   0x20010000, alongside nonzero runtime fields3183/500/200 at the decoded
   input-bound/counter-threshold locations. This supplies live structural
   support for the secondary CPU/DMA relation which older reports had lacked.
   The core-tag register itself was not read.
3. The packaged common-error candidate at DMA0x4500f0c0 returned guard0 and
   selector0. Only one return guard is included; code identity and executing
   PC are not measured. It does not establish an emergency loop or refute an
   earlier fault.
4. The main controller history at0x20205000 yielded3072 readable log bytes.
   Copy counters197151..197182 can be recovered in consecutive order after
   an explicitly inferred circular rotation at0x6ff. Repeated lines report
   sensor/framework processing, eMMC data/header writes, and VD Degrad values.
   These are exact vendor strings, not diagnosed component failures. No
   `RT-P activate!` or `rtp_act_` occurs in this small retained window.
5. A later index sample exposes0x92d at the packaged index location versus1
   at the older stored-generation candidate. The558-byte advance from the
   inferred earlier cursor is coherent but non-atomic. The packaged byte-flag
   candidate at CPU0x20000e30 is0. These observations further support the
   packaged active layout without proving all running bytes.
6. The secondary log header at0x20200000 returned write/read-like words5/5,
   flag0, and the five bytes `[C1]\n`. Remaining bytes are not current text.
   The gated secondary logger was not proved active by this sample. A later
   complete15372-byte snapshot returned the same first64 endpoint bytes
   (5/5/0) at uptime108637.19..108637.69 and is retained as an opaque
   baseline. Equality across1124.65 seconds does not prove intervening stability.
7. One existing QDF getter at uptime~107708 returned0 instead of the old
   uptime~75262 result0x10. A non-clearing kernel-log read preserved the same
   helper PID26106 with raw `ERR DET Status:0x0`. No I2C capture establishes
   successful underlying transfer, debug behavior is bounded by the retained
   function filter, and controller read-to-clear semantics remain unresolved.
   The observations are separated in time and have no physical annotation.

## Corrections and failed assumptions

- CPU addresses0x200... cannot be assumed directly visible to USB DMA. The
  main SRAM alias is0x450... for tag0xA; the other mapper branch uses0x470....
- The translation range ends BEFORE0x20200000. Both log buffers20200000 and
  20205000 fall through unchanged; invented4520/4720 aliases were rejected.
- Earlier fault reports used container FILE numbers as if linked addresses.
  For image0 subtract0x200. For image1 subtract0x40200. In particular, the
  packaged error entry is VAb660, poller214d4, and callback28cf0.
- The secondary formatter wraps per byte, not once per call. Its entire body
  is gated by context+2406 bit0; both event-setter calls use the same format.
  Corrected checks use active exceptions under Python optimization.
- A preliminary helper manifest pinned mutable/inaccurate analysis. It was
  retained as a rejected pre-execution revision; the executed header helper
  pins immutable corrected local evidence copies instead. No rejected
  revision was deployed.

## Next discriminators

The persistence service is called by BOTH ordinary and emergency schedules;
its continuing messages cannot distinguish those paths. Its attempted storage
addresses exceed the qualified target203 validator range. The delegated
follow-up was stopped by an automated security check and has not been retried.
No high-bank request was made. The finite volatile secondary-log enable/restore
transaction now has separate protocol and architecture reviews. The logger flag is an instrumentation candidate, not a
protection threshold. A finite logger qualification is being implemented outside this snapshot; no
writer is reviewed or deployed at this point.
Future owner-observed transitions can align new internal logs, RT fields,
host transport and emitted-light reports. No repair has been demonstrated.

## Reproduction and retained records

`audit-callback-reads.py` and `audit-state-reads.py` authenticate raw root
envelopes, reconstruct every uploaded binary, replay exact deployment command
sequences offline, and validate transfer counts, bytes and cleanup.
`interpret-main-log.py` preserves raw bytes and creates an inferred chronology.
The static checkers pin image bytes and exact instruction anchors; they do not
claim runtime instruction identity. Native private stages were removed after
each bounded request. No capture/USB helper is left running from these reads.
