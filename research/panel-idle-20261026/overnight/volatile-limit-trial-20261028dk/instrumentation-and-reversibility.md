# Instrumentation and recovery boundary

The owner reiterates that unattended diagnosis and new instrumentation are
authorized, but changes must be reasonably safe or reversible: losing boot or
network access would also lose the current remote restoration route. This is
an operating constraint, not a request to pause for owner verification.

## Current instrumentation

- The DF reader is our code. It timestamps every fixed USB request/reply,
  preserves the triggering clean cycle, last clean cycle, first fault and
  post-fault windows, and records the normal key down/up calls. Two completed
  DH observations locate clean-to-fault software changes within about251ms.
  The USB brackets do not measure the physical light transition or establish
  an atomic firmware snapshot.
- The new DM reader targets the controller's own five record columns and
  associated root/mode/channel/source-count/descriptor context. It supplies
  another view of the comparator inputs and record publication path. Forty-eight
  retained entries per column are a bounded raw window, not a claim that every
  entry belongs to the current frame or fault. Some arrays can retain older
  samples. Baseline and faulted records must be interpreted with the source
  resets and guards.
- The earlier DH kernel trace used a private, finite trace instance and selected
  existing stock GPIO/IRQ events; it was stopped and removed. It did not force
  GPIO reads, request new pins, or change electrical outputs. No selected GPIO
  event in that capture is not proof that no hardware transition happened.
- The controller's original logs and AVE's existing emitted diagnostics remain
  separate evidence. A stale history latch is not used as an automatic detector
  of physical blackness. Kernel kprobe/uprobes were not available in the
  inspected target configuration; a claimed planted kernel breakpoint would
  be misleading. The new readers do not silently patch executing controller
  instructions.

## Live change inventory for this bounded comparison

DJ set-01: completed fake self-test only, zero production/vendor operations.
DL set-02: production entered once, claim succeeded, refusal before the first
vendor transfer, then release/close. DN set-03: same zero-vendor refusal at the
stricter owned-driver check, then release/close. All three unused stages have
separate accepted exact-file cleanup receipts; original refusals are preserved.
No threshold write has occurred in these attempts.

DO is a new zero-vendor binding diagnostic: it will open the fixed USB instance,
inspect kernel-cached driver metadata before/after one claim, release and close.
It contains no controller bulk/control transaction or reset path. Its purpose
is to observe the missing interface-binding evidence, not relax a failed guard
by assumption. Native runtime stdout is separate from its exclusive receipt.

The proposed future intervention is exactly one volatile halfword40-to200 in
the source-qualified alternate comparator/record bound, followed by separate
checked restoration. It does not overwrite instructions, boot/update storage,
EEPROM or kernel files. A successful write does not prove it is an adequate
physical repair. An uncertain transfer must stop further headers rather than
blindly restoring on a possibly desynchronized endpoint.

## Recovery rule

Ordinary navigation to cached Apps and one separately recorded stock MODE2
restart are the existing recovery route. Earlier owner-confirmed recoveries
are distinct from later unattended kernel-return-zero receipts. Do not claim
an unseen picture from the latter. Each action remains finite; no background
reset loop or persistent bypass is installed.

Any later proposed code checkpoint must identify its exact executing-image
match, overwritten bytes, rollback and recovery path first. Flashing boot,
kernel or controller images is outside this current experiment. A source
patch on the host may be explored without deploying it. Keep the TV boot and
network route available while diagnosing this damaged panel.
