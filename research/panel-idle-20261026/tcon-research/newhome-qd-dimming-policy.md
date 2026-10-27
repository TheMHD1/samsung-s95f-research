# NewHome → QD dimming policy: resolved vtable path and content boundary

Scope: offline disassembly of the copied matching `libave.so.0.1`. No AVOC,
CSFS, PPI, D-Bus, ioctl, QD command, or TV control was called. Addresses below
are Thumb virtual addresses with the low state bit omitted.

## Conclusion

The apparent NewHome-to-dimming virtual call is now resolved: on the
QDDimming vtable used by this image it reaches the base
`DimmingInterface::GetDynamicBrightnessMode(int *)` stub at `0x155554`, which
simply returns zero and does not dereference its argument. It does **not**
invoke QDDimming APL filtering, screen-saver policy, low-power mode, panel
mute, or a QD/TCON setter.

NewHome does set an AVE byte and sends a separate FRC NewHome ioctl, so it can
still affect FRC/full-Home context. The no-op finding applies to this dimming
virtual edge only: [deeper FRC/QDF frame-mode programming](newhome-tcon-vfreq-backend.md)
can use a real temporary panel-mute bracket. It must not be generalized to
absence of gating throughout the entire downstream call graph.

## Exact NewHome path

```text
CSFS/AVOC PPI wrapper
  impl_set_newhome_inout_state             0x2a53f8
    VideoEnhancerImpl::set_newhome...      0x29f25c
      ave_api_set_newhome_inout_state      0x28c038
```

At `0x28c0ce–0x28c0e2`, `ave_api_set_newhome_inout_state(int enter)` obtains
the initialized dimming object and makes this virtual call:

```text
object->vtable[0x158 / 4](object, enter)
```

The QDDimming vtable starts at `0x59f2e0`; an object vptr addresses its first
virtual entry at `0x59f2e8`. Therefore the slot used is `0x59f440`. The
relocation for that exact vtable word names:

```text
DimmingInterface::GetDynamicBrightnessMode(int *)  0x155554
```

Its complete effective body is only `r0 = 0; return`. The odd-looking `enter`
value is harmless on this implementation because that base stub does not read
the nominal output-pointer argument. There is no QDDimming override at that
slot. This closes the previously opaque virtual edge.

## What NewHome actually writes/calls

After the virtual query, `ave_api_set_newhome_inout_state` stores
`enter ? 1 : 0` into the one-byte AVE global `m_iNewHomeMode`
(`libave BSS 0x5bfe08`; store at `0x28c0e4–0x28c0f2`). It then calls the FRC
NewHome helper, not a TCON/QD helper:

```text
ave_frc_api_set_newhome_inout_state(enter)  0x246848
  -> frc_ioctl(0xc00866ff, { selector=3, value=enter })
```

The NewHome body contains no direct call edge to:

* `ave_tcon_api_set_qd_ss_method`, `...brightness`, `...waitingtime`,
  `...slope`, or `...sensitivity`;
* QD low-power command `F3 ... 0140`;
* `ave_api_set_panel_mute`, `ave_tcon_api_set_panel_mute`, or QD mute
  command `F3 ... 0164`;
* QD TCON power control, reset, or fault handling.

The routine also has model/configuration and eco/ambient branches, including a
shared-state check at `+0x8b3f4`; those are outside the dimming virtual call
and do not become QD screen-saver setters in this binary. They must not be
mistaken for a panel-recovery mechanism.

## Where the real QD content-adjacent work occurs

QD dimming's normal per-vblank dispatch is
`QDDimming::t_vSyncCallBack` at `0x17b35c` (and the QDMNT variant at
`0x19b1c8`). It is controlled by initialized-state checks and bits in its
internal control word at `inner + 0x18c`; it is not called by the NewHome
setter above. Among its conditional calls are:

```text
QDDimming::m_SetAPLFilter()    0x17b190
QDDimming::m_SetScreenSaver()  0x17b204
```

### APL-filter route

`m_SetAPLFilter` packages seven current inner-state fields into a
`BackendSetNpcGain_t`-like stack record:

```text
inner+0x160, +0x15a, +0x159, +0x44c, +0x294, +0x0c, +0x124
```

and calls backend virtual slot `+0x210`. On the QDMNT backend vtable,
`DimmingBackendRoseMQDMNT` (`0x5a177c`), that slot resolves to the base
`DimmingBackendInterface::t_SetAPLFilter` stub (`0x1886cc`), which returns
without a QD write. Thus this exact QDMNT route carries policy state but does
not, in the host code provided, turn APL into a TCON power/mute/low-power
command.

Other backend families may override that slot (for example the MWOLED backend
has an implementation at `0x1bf93c`), so the conclusion is deliberately
specific to the QDMNT vtable rather than a claim about every Samsung panel
family.

### Screen-saver route

`m_SetScreenSaver` is vblank-dispatched only when its control bit permits it.
It first requires `inner+0x450 != 0`, then builds a five-word policy record
from `inner+0x284`, `+0x2b8`, `+0x15a`, `+0x124`, and `+0x520`. It performs no
NewHome-global read and no pixel/framebuffer scan in this function.

For the QDMNT backend, virtual slot `+0x200` resolves to the real
`DimmingBackendRoseMQDMNT::t_SetScreenSaver` at `0x1cb2d8`. That function
uses cached/factory policy values, including factory UID `0x5019`, and sends
only screen-saver-family setters when their desired values change:

```text
ave_tcon_api_set_qd_ss_method(1)
ave_tcon_api_set_qd_ss_brightness(value)
ave_tcon_api_set_qd_ss_waitingtime(1)
ave_tcon_api_set_qd_ss_slope(0)
```

Those are the already-known QD commands `...00c0`, `...00c4`, `...00cc`, and
`...00d0`; none is QD mute (`...0164`) or QD low-power level (`...0140`).
The backend uses static “last sent” values to avoid repeat writes. It contains
no elapsed-time comparison or NewHome condition. The code available here does
not assign real-world units or a duration threshold to the waiting-time
payload, so no seconds/minutes claim is made.

## Evidence boundary for the UI correlation

This resolves an important negative: entering/leaving full Home does not
directly switch the QD APL or screen-saver policy through AVE's NewHome setter.
The observed richer-Apps versus sparse-Home/Live difference may still change
the independent compositor/FRC context, vblank policy flags, or the
panel-internal response to rendered content. The binary does not contain a
host rule of the form:

```text
NewHome or sparse UI → N seconds → QD mute / LPM / power change
```

Accordingly, no NewHome suppression or QD policy write is justified by this
path. A useful future passive discriminator is whether a *confirmed* visible
versus black transition changes the `...00c0/c4/cc/d0` screen-saver command
sequence, without issuing any new command.
