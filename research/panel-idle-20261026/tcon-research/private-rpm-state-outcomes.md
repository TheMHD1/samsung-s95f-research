# Private PM can advance software state without confirming resume success

This is an offline exact-build result, not a diagnosed incident. The private
Samsung dispatcher has an additional retry-suppression mechanism: after an
invoked resume callback returns, it clears its transition state and increments
the software use count without checking the callback's return. A subsequent
`get` with a positive count increments again without invoking resume. That is
a plausible way software and hardware could disagree; no retained blackout
has yet been linked to this record, callback, count, or failure outcome.

## Sources and reproduction

- `overnight/kernel-Image.bin`: 11,786,752 bytes, SHA-256
  `77b6070c12a53f2b7ede3b7c503e242759e22dbaef2d12cc91b556416fed455d`.
- `binaries/sdp_hdmi.ko`: 3,299,534 bytes, SHA-256
  `f7cffd19934ef459b0263ceddddf003306b399e01d0ddee48df3f64a86667994`.
- [Reproducer](private-rpm-state-outcomes.py) authenticates PREL32 exports
  directly from the Image and pins the earlier ELF reader. It checks
  decisive instructions, module identities/relocation and literal bytes,
  and reproduces [full bounded disassembly excerpts](private-rpm-state-outcomes.disasm).
  Manual control-flow interpretation remains necessary.

```sh
PYTHONPATH=/tmp/tcon-capstone python3 private-rpm-state-outcomes.py
PYTHONPATH=/tmp/tcon-capstone python3 -O private-rpm-state-outcomes.py
```

All Image offsets below are file/image-relative. They are not live kernel
addresses. Module offsets include their section. The Image declares a
`0xd99000` memory extent; its saved payload does not include BSS at
`0xc249c8`. Neither a static zero assumption nor an on-disk value is a
measurement of the live bypass flag.

## The private state machine

The earlier [registration/dispatch analysis](hdmi-private-resume-dispatch.md)
connects the `sdp-hdmi` name to saved suspend/resume callbacks. Its named
record contains the following statically consumed fields:

| Offset | Consumer meaning established by the code |
| --- | --- |
| `+0x10` | Name used in lookup and messages; bounded 15-byte compare/copy |
| `+0x20` | Saved device argument |
| `+0x28` | Saved suspend callback |
| `+0x30` | Saved resume callback |
| `+0x38` | Spinlock storage passed to lock/unlock helpers |
| `+0x3c` | Signed software use count |
| `+0x40` | Busy-use count, consumed by the suspend wait |
| `+0x44` | Private state: code writes 1 before resume, 0 after resume, 2 before suspend/busy wait, and 3 after suspend returns |

These states are software bookkeeping. In particular, state 3 is not a
measurement that the physical panel is off, nor evidence of a module reboot.

### Get: callback result does not determine success or later retry

Exported `sdp_runtime_pm_get`, Image `0x3fc040..0x3fc1c0`:

1. A nonzero global bypass byte returns zero immediately. Otherwise the
   helper obtains/creates the named record and waits while its state is 1
   or 2. The wait includes sleeps and repeated warnings; it is not a bounded
   recovery deadline established by this analysis.
2. At `0x3fc104..0x3fc114`, an already-positive use count takes the
   increment-only branch. No resume callback is invoked on that branch.
3. With a non-positive count, a null saved device or null resume pointer also
   reaches the increment-only branch. Zero return therefore does not even
   prove a callback was present.
4. With both pointers present, it stores state 1 at `0x3fc14c`, unlocks,
   loads the argument/function and invokes `BLR x1` at `0x3fc164`.
5. The instruction immediately after the callback overwrites `x0` with the
   lock address; the callback's return is neither tested nor saved. The
   dispatcher locks, writes state 0 at `0x3fc170`, emits a `resumed` message,
   reloads/increments the count and returns zero.

For the conditional example count 0 with valid pointers, a returning failed
callback can leave count 1/state 0. A later ordinary `get` can then increase
the count to 2 without retrying the callback. This example assumes the
shown path completes and does not establish live concurrent counts, an
actual callback failure, or that this record controls the incident.

### Put: suspend completion is also software bookkeeping

Exported `sdp_runtime_pm_put`, Image `0x3fc1c0..0x3fc3e8`, decrements the
software use count before deciding whether to invoke suspend. With an exact
zero new count and both device/suspend pointers present, it writes state 2,
unlocks and waits on the busy count. If that wait exhausts its loop, the
`suspend timeout. device is still busy.` message at `0x3fc380` falls through
to the callback call; it does not abort suspend.

The saved suspend callback executes at `0x3fc388`. Its return is immediately
overwritten by the lock argument, with no success/error test. The code then
writes state 3 at `0x3fc39c`, emits `suspended`, unlocks and returns zero.
Consequently that log means the callback returned to this dispatcher; it
does not establish hardware acceptance. Negative use counts follow a
separate unmatched-put path and are reset to zero; no balance-repair action
was performed or proposed from this static fact.

## The HDMI callback adds another state-dependent skip

`sdp_hdmi_resume_ext`, module `.text+0x5120` (132 bytes), calls
`sdp_hdmi_pm_resume` at `0x5144` and returns its result without replacing it.

`sdp_hdmi_pm_resume`, `.text+0x4e60` (700 bytes), reads a private context word
through this chain for a nonnull input device:

```text
context = *(device + 0x78)
object  = *(context + 0x18)
base    = *object
word    = *(base + 0x29f40)
```

It initializes its result to zero at `0x4ea8` and calls the substantive
resume path only when that word equals 3 (`0x4ebc/0x4ec0`). A different word
returns zero without calling `sdp_hdmi_resume_fxn`. This private context
word has not been sampled live; it is not labeled a measured hardware
register or equated with the dispatcher's separate record state at `+0x44`.

When it does call `sdp_hdmi_resume_fxn` at `0x4f84`, the result is saved in
`w21` at `0x4f8c` and returned via `0x4ec4`. Subsequent reporting/cleanup in
the wrapper does not convert that result into a verified hardware success.
The outer kernel dispatcher still discards it as described above.

## Why the apparent disable/getter options are not passive fixes

Exported `sdp_runtime_pm_disable`, Image `0x3fbbd0` (the bounded 20-byte
body), stores one to the global byte at Image-relative BSS `0xc249c8` and
returns zero. It does not resume a device, reconcile counts or retry a
failed callback. The acquired get/put/init/getdev entry points consult that
byte and bypass their normal work when nonzero. No inverse operation is
claimed. Calling this after a blackout could preserve stale state rather
than restore a picture. It has not been called.

Exported `sdp_runtime_pm_getdev`, Image `0x3fbee8`, is also not a guaranteed
nonmutating status query. With bypass clear it calls the helper at
`0x3fbe10`. On a name miss that helper allocates a 96-byte record, copies the
bounded name and inserts the record into its list. Therefore invoking a
getter-shaped interface to inspect a suspected name can create state. This
helper has not been called for this follow-up.

## New discriminators and remaining gap

Two stock early-trace messages distinguish more than the outer caller's
IN/OUT pair. On entry to the substantive `sdp_hdmi_resume_fxn`, the code
copies literal `[HDMIRX] resuming ...\n` from `.rodata.str1.8+0x2910` to
its stack and calls `trace_early_message` at `.text+0x494c`, before its
nonnull-platform-argument gate. The wrapper's full-work branch later formats
`@PM Resume_time [sdp_hdmi_pm_resume] /HDMIRX_MODULE/%d/msec\n` from
literal `+0x2b60` and emits it at `.text+0x50c0`. These sites have no local
print-level gate on their shown paths, although the imported trace emitter
and acquisition still have their own runtime/coverage limitations.

An emitted entry can therefore support substantive resume entry; the outer
IN/OUT markers alone cannot. The elapsed-time marker is reached after the
resume function returns even when its saved result is nonzero: its text does
not contain that result or establish output success. The state-word-not-3
early-success branch does not reach either of these sites. Exact relocations,
stack arguments and literal bytes are checked by the reproducer. A missing
marker remains insufficient to exclude execution.

The exact kernel log literals `resumed`, `suspended`, busy timeout and
unmatched-put now have bounded control-flow meaning. `resumed` does not
report a callback result; `suspended` does not prove a panel powered off.
They complement the caller-specific stock trace markers already recovered,
but a missing log cannot exclude private PM activity.

The next incident evidence must establish a positive invocation near an
owner-observed onset, then distinguish callback entered/returned, software
state/count changes, actual controller traffic, and physical light. Normal
Linux PM traces alone do not cover the private function-pointer dispatcher.
No kernel RAM reader, live record, private callback binding or incident
return value was acquired here. No TV access, kernel patch, policy write,
factory change, power action or recovery experiment was performed.

Independent offline review checked the full get/put control flow, both
distinct state machines, callback-result propagation/discard, the allocating
lookup, bypass-byte location and both stock trace-marker dataflows. Normal
and optimized reproduction passed. This clearance covers the stated static
interpretation, not a live callback failure or physical repair.
