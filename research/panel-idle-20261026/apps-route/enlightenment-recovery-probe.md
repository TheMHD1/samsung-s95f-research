# Enlightenment post-composition recovery probes — static client audit

## Why these are now in scope

The B0/B1 captures show newly advancing rich-Apps compositor frames while the
owner reports the physical panel black.  At the same point the recorded state
is `DPMS_ON`, LVDS on, panel mute 0, screen state 1, and digital status OK.
This localizes the next diagnostic boundary *after* Enlightenment has composed
the UI.  It does not identify FRC, output hardware, TCON, or the damaged panel
as the cause.

The commands below are stock Enlightenment diagnostic requests.  They do not
write TV settings, Factory data, vconf keys, AVOC state, screen-saver state,
or TCON policy.  They may change the live compositor policy, so they must be
run only as a bounded owner-approved recovery experiment with evidence and an
explicit restore step.

## Exact client-visible semantics

The matching `enlightenment_info` client (ARM ELF Build ID
`168af6c4e9909d97de41857969d4783a73e5f0df`) uses the
`org.enlightenment.wm.info` service at `/org/enlightenment/wm`.  Its embedded
server-help strings define:

| Command | Exact documented request | Scope supported by evidence |
| --- | --- | --- |
| `-frender all` | “updates client's surface and canvas” | One force-render request for both client surfaces and the canvas. |
| `-frender cls` | “updates client's surface only” | One force-render request without explicit canvas damage. |
| `-frender canvas` | “updates canvas adding damage in fullscreen size” | One full-screen canvas-damage request. |
| `-hwc 0` | “HW composite policy … off(0)” | Live-verified request of HWC fallback/deactivation. |
| `-hwc 1` | “HW composite policy … on(1)” | Live-verified restoration of normal active HWC. |
| `-hwc 2` | “prints info(2) via dlog” | Diagnostic info only; normal stdout may be empty. |

The `-frender` parser accepts only `all`, `cls`, and `canvas`; it is not the
screen-saver interface.  `-hwc` accepts only `0`, `1`, or `2`; it is distinct
from `-hwc_wins`, which only prints HWC-window data.

## What cannot safely be inferred yet

The matching stock Enlightenment server resolves the apparent client-help
ambiguity.  Its `-hwc` D-Bus handler at `0x473a4` parses `0|1`, enumerates the
live output HWC objects, and calls exported
`e_hwc_deactive_set(hwc, value)` at `0x63c4c` on each one.  That setter changes
only bit 0 at runtime object offset `hwc+0x0c` and invokes runtime HWC
reconfiguration helpers (`0x5b434` when clear, `0x5b4cc` when set).  Neither
helper has a configuration-write call; both adjust live compositor-object
state and emit logging.  The handler contains no VCONF, file, Factory,
configuration-save, AVOC, or TCON call.

## Correction: live readback is authoritative

The original static argument mapping below was **wrong**.  The matching TV's
post-request HWC-object dumps provide the decisive result:

| request | handler operation | bounded-test meaning |
| --- | --- | --- |
| `-hwc 0` | live readback: `deactive=1`, `CL` fallback | disables the normal HWC path for this live runtime. |
| `-hwc 1` | live readback: `deactive=0`, `DV` normal path | restores normal active HWC. |

The client help's off/on direction is therefore correct.  The earlier static
trace was corrected: the callback branches are deliberately inverted before
the setter call.  Parsed CLI `0` branches to `0x47474` and calls
`e_hwc_deactive_set(..., 1)`; parsed CLI `1` falls through `0x473fc` and calls
`e_hwc_deactive_set(..., 0)`.  The original error was reading the two adjacent
branches as matching rather than opposite-value paths.  The live dumps confirm
that exact disassembly interpretation.  Continue to use the TV's `-hwc 2`
dlog readback as the operational guard.

The code proves a live-object change, not that the fallback is purely GPU,
not that every direct-scanout path is absent, and not that the state is
guaranteed to survive or be reset by a compositor restart/reboot.  It does,
however, exclude the command handler itself writing retained TV settings.

Neither command resets the TCON, disables fault/thermal recovery, changes
OLED compensation, changes AVOC panel mute, or changes the factory
screen-saver-brightness scalar according to the client protocol surface.

## Safe experiment order after a physical-black confirmation

1. Preserve the already-established black-state evidence first: timestamp,
   compositor PNG/hash, `-topwins`/`-topvwins`/`-compobjs simple`, and the
   passive AVOC/deviced values.
2. Run only `enlightenment_info -frender all` once.  Capture the same passive
   evidence again and ask the owner whether the physical image returned.
   This has the smallest policy footprint and directly tests stale output
   damage/frame submission.
3. With the existing owner-authorized black-state reproduction, record a
   baseline `-hwc 2`, run `-hwc 0` once, capture/observe for a short fixed
   window, then always run `-hwc 1` once and record `-hwc 2` again.  The
   restore is required even if the black panel recovers.
4. Stop the experiment if compositor/process stability changes.  Do not
   combine it with AVOC, screen-saver, Factory, or TCON commands; otherwise
   the observation loses attribution.

The handler and its runtime-only setter are now inspected.  The remaining
unknown is whether a later compositor/service lifecycle event independently
overrides this live state; the immediate `-hwc 1` restore minimizes that
window.  `-hwc 2` dispatches to the server's live HWC-object dump routine,
which queries each output's current HWC windows; its result is emitted to
dlog rather than necessarily to CLI stdout.  Record that dlog before the
deactivate request and after the restore.  A `DV`/`CL` per-window mode label
is useful evidence of the current path, but is not by itself the setter's
deactive bit.
