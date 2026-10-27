# NewHome / FSAV path into AVE — offline trace

## Boundary and evidence

CSFS reaches AVOC's `SetNewHome(0|1)` through its lifecycle/full-home logic.
`avocd` imports `ppi_ve_set_newhome_inout_state`; that PPI entry is hosted by
the initialized AVE service, not an API suitable for a separate helper.

In the copied AVE binary the service path is:

```
ppi_ve_set_newhome_inout_state(bool)  [AVOC-owned PPI wrapper]
  -> impl_set_newhome_inout_state      0x2a53f9
       -> VideoEnhancerImpl::set_newhome_inout_state(bool) 0x29f25d
            -> ave_api_set_newhome_inout_state(int)         0x28c039
                 -> ave_frc_api_set_newhome_inout_state(int) 0x246849
```

## What `ave_api_set_newhome_inout_state` demonstrably does

The routine receives the `0|1` input, records it in the AVE NewHome state
(`m_iNewHomeMode`), calls an indirect method on the currently initialized
dimming instance, and invokes the FRC NewHome helper.  The helper gates a
vendor FRC operation through ioctl `0xc00866ff`; this is inside AVE's already
initialized driver/service context.

The routine also contains model/low-power-art gating and queries an AVE FRC
NewHome vfreq helper for some models.  Therefore it can affect FRC mode and
the dimming policy context associated with full Home.

## What it does *not* establish

No direct call edge from `ave_api_set_newhome_inout_state` or
`ave_frc_api_set_newhome_inout_state` reaches:

* `ave_tcon_qd_set_power_control` (TCON reset/off/on);
* `ave_tcon_api_set_qd_ss_brightness`;
* `ave_api_set_panel_mute` / `ave_tcon_api_set_panel_mute`.

Update: the formerly opaque QDDimming virtual edge is resolved in
[newhome-qd-dimming-policy.md](newhome-qd-dimming-policy.md). Exact slot+0x158
reaches the base GetDynamicBrightnessMode stub, which returns zero without a
QD setter. The separate FRC branch is traced through its eight-byte selector3
request to RosemFrc_SetNewhomeMode in
[newhome-frc-output-policy.md](newhome-frc-output-policy.md); it can change
source-rate/output policy. Neither result establishes physical emission or a
sparse-page timer. The deep QDF frame-mode path can itself use the0x164
output gate around mode programming; the absence of direct AVE mute calls
must not be generalized to an absence of downstream gating.

## Consequence for the observed behaviour

The user's stable full Apps/Home state is consistent with NewHome changing the
FRC/render context.  The firmware evidence does not show it clearing a TCON
fault latch or issuing a recovery action.  Conversely, it does not justify
disabling NewHome/FSAV or calling the PPI/ioctl directly.  The legitimate
instrumentation is correlation only: timestamp existing AVOC `SetNewHome`,
AVE NewHome logs, frame/vfreq mode logs, panel-mute getters, and the existing
kernel TCON monitor output across a physical stable/black transition.
