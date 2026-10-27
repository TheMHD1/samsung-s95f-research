# Live protection-state memory access, 2026-10-27

The important result is direct access to the controller's protection-state
memory on this TV. No permanent blackout fix or physically observed recovery
has been established. This work did not flash firmware, replace/load a kernel
module, change a protection value, reset the panel or navigate the UI.
Root remains host-assisted; permanent untethered root is unverified.

## How this changes the investigation

The owner reports that populated Apps usually holds the picture, sparse
For You/Live can make it persistently black with audio continuing, and some
full-screen HDMI titles reproduce the loss while other titles and the Ugoos
Home overlay hold the picture. Previous owner-observed pairs gave status0/pin0
for visible Apps and status0x10/pin1 after a sparse-menu blackout. Similar
working/failing HDMI comparisons exist, with their recording limitations
preserved in the main investigation. This work adds no new physical annotation.

Earlier reverse engineering tied a packaged RT-field read to the exact fault
reply but could not observe its upstream fields on the TV. The newly verified
USB memory route now supplies those fields directly. It is suitable as the
basis of a future bounded paired logger; no continuous logger is installed.

## Corrections and executed tests

The apparent USB command gate was an analysis mistake. The parser initializes
mode2 as a sentinel, then replaces it with mode0 for direct-memory reads or
mode1 for buffered eMMC reads. These writes reuse the same PC-relative literal.
The [instruction-bound correction](../../tcon-research/ssb-mode-gate-followup-20261027.md)
is independently reproduced. Earlier no-producer/not-ready conclusions remain
historical and are superseded on that specific point.

| Actual test | Result | Cleanup |
| --- | --- | --- |
| First18-byte descriptor reader |23 fake cases passed; preflight EndOfStreamException; no USB open or request | Private stage absent |
| Streaming descriptor revision |27 fake cases passed; OUT12/IN18; exact known descriptor returned | Interface released, FD closed, stage absent |
| Fixed32-byte RT-prefix reader |26 fake cases passed; OUT12/IN32; runtime prefix returned | Interface released, FD closed, stage absent |
| Subsequent stock status query | Accepted kernel output0; matching QDF raw log from PID10844 | Helper stage absent |

The metadata bug was independent of the controller protocol. The sysfs
descriptor file advertises65553 bytes, but a bounded actual read yields116.
The first managed binary reader expected the advertised size. Its replacement
reads a stream with a117-byte cap, requires the exact116 cached bytes and
rejects oversize. Both original source/evidence and the corrected derivative
are preserved. No request was sent in the failed preflight attempt.

## RT-prefix observation

Same Linux boot:00000000-0000-4000-8000-000000000000.
The fixed request read32 bytes from image0 address0x47012400 during the
software window uptime100190.44–100190.96:

```text
0000400b7008000001000000c800010004000000f401f4010000000000000000
```

SHA256:0bc6e8374f85b3dc09ad1e3f863d9441f8136e5af36abd5c77c4a66c5e033821.
The selected package's initializer at FILE0x183800 matches30 of32 bytes.
Offsets+0x08 and+0x0e are each1 in the reply versus0 in that initializer;
their live meanings are not established. The RT fault halfword at+0x0a is0;
the mode halfword at+0x10 is4, matching the packaged mode. Nonzero matching
fields and exact layout similarity corroborate the intended region.

At later uptime100242.204712, a raw QDF kernel row for the actual status
helper PID10844 reports ERR DET Status0x0. The helper independently returned
0x00000000. These are sequential samples roughly51seconds apart, not a
simultaneous physical/firmware event or continuous zero interval. The status
call's possible read-to-clear semantics remain unresolved; the memory sample
was taken before it.

The [runtime audit](rt-prefix-runtime-audit.json) and
[reproduction script](audit-rt-prefix-run.py) reconcile raw authenticated
responses, build identities, exact counts, returned bytes, initializer deltas,
the later status result/raw row and cleanup. The read-only independent reviewer
also reassembled all three uploaded payloads from recorded base64 commands
and validated every response for both successful readers. Its findings are
retained in the parent-created [review record](../../tcon-research/ssb-known-descriptor-reader-independent-review-20261027.md)
and this work log.

## Limits and next diagnostic design

This proves access to this32-byte image0 window on this boot. It does not
prove whole installed-firmware equality, the image1-to-image0 alias, the
meaning of packed sensor samples, a protection trigger, physical light output
or a repair. A zero flag with an unobserved panel cannot be called recovery.
No current short/overcurrent/temperature threshold has been identified or tuned.

The next paired capture should retain the following order:

1. Establish a new owner-observed visible Apps baseline and read this prefix
   before any proprietary status query. Preserve boot and uptime anchors.
2. Start a finite, reviewed memory sampler alongside the existing bounded
   kernel/traffic observer; retain the exact same prefix and successful
   transfer/cleanup accounting. No implementation or sampling rate has been
   qualified yet. Polling overhead must be measured first.
3. Have the owner trigger the sparse-menu blackout after a clear recording
   window is armed, or repeat a known failing HDMI title. Retain physical
   annotations without treating UI screenshots as panel light.
4. If the RT field changes, preserve the sample before querying stock status.
   A separately bounded full RT-window/history read can then target the known
   event fields and guards. The new32-byte result does not qualify a larger
   transfer automatically.
5. Resolve whether the fault asserts upstream of the host notification and
   whether any hardware latch remains after the flag clears. A stock panel
   cycle already cleared software status in the preceding work block, but its
   physical outcome is still unreported. Avoid an automatic reset loop.

Flashing and protection changes are owner-authorized. Choosing an intervention
still requires a specific diagnosed mechanism, exact installed image and a
restoration path. The new read access is practical progress toward that diagnosis;
no new permission request is pending for these authorized operations.
