# NewHome FRC ioctl to Rosem output policy

Offline analysis of the matching libave, tztv_frc_tcon_api and rosem_frc copies. No ioctl, factory setting, display control, or power operation was issued. Reproduce the bounded excerpts and selector mapping using `PYTHONPATH=/tmp/tcon-capstone python3 overnight/trace-newhome-frc.py`. Inputs are fingerprinted in `overnight/newhome-frc-input-manifest.json`; addresses below are ELF link VAs (Thumb code addresses are even) or module section offsets, never runtime addresses.

## Exact dispatch, including the request envelope

`ave_frc_api_set_newhome_inout_state` (`libave:0x246848`) constructs **two 32-bit words `{3, enter}`** at stack +0x1c/+0x20 and calls the existing FRC ioctl wrapper with `0xc00866ff` at0x246882. Here 3 is the first selector word and enter the second value word. This is `FRC_Request`, not the similarly named `FRC_NewRequest` (which belongs to a different, 16-byte request route).

`tztv_frc_tcon_api` compares ioctl0xc00866ff at0x1800..180c, jumps0x27bc, copies eight bytes at0x27d0, then calls `FRC_Request` at0x27dc. The signed-halfword jump table at `.rodata+0x634`, relative to `.text+0xa6f0` in instruction words, maps selector3 to0xa778. That branch gets the registered FRC table from `.bss+0x618`, loads callback **+680 /0x2a8**, loads request word +4 into w0 and calls it. Absent table/callback returns zero; a successful envelope return alone cannot prove hardware action.

The Rosem module's `.init.text` resolves the pointer to `RosemFrc_SetNewhomeMode` at0x30c/310 and installs it at table+0x2a8 using the store at0x394 (`x2=table+0x298` from0x21c). Thus the selector-to-function edge is reconstructed from actual relocations and stores, not inferred from names.

## Entry changes rate policy; exit defers work

`RosemFrc_SetNewhomeMode` starts0x7bd8. Upgrade state or EW test suppresses work. Equal requested and cached `m_newhome_mode` also returns zero. On change it stores the requested state at `.bss+0x18c` before calling the lower routine. A request of1 with `m_vfreq_144 !=0` is logged/skipped. These early exits can be relevant to interpretation of future logs; they do not establish a current live flag value.

`m_rosem_set_newhome_mode` starts0x37b8. For input1:

- Nonzero `m_vfreq_144` (`.bss+0x194`) is rejected/skipped with the literal message `Invalid case for new home true`.
- `m_ambient_mode ==2` is skipped (`New home skip for Art mode Low-Input-lag mode(2)`).
- Otherwise it calls `m_rosem_low_input_lag(0, m_vfreq)` at0x3848.
- It selects `m_vfreq=5000` or6000, sending the duplicated-word vendor command0xf241f241 or0xf240f240 through `m_rosem_send_cmd`. These are the driver's hundredths-of-Hz values (50/60Hz); they are not evidence that the physical QD panel always runs at50/60Hz.
- It clears `m_vrr_max_vfreq` (`.bss+0xec`) at0x38e4, calls the view-angle helper at0x38e8, and calls `m_rosem_set_tcon_frame_rate` before or after selection depending on the WOLED cell-type branch. This QD-oriented trace does not rename the other panel branch.

The input-rate selection is explicit: for meaningful VRR maxima1..999, maxima49..50 and61..100 choose5000; remaining maxima choose6000. With no meaningful maximum, recognized current input ranges2300..2440,2800..3200,4700..4880,5800..6400,11800..12200 choose6000; the fallback chooses5000. This is static policy, not a measured rate during the owner's incident.

For input other than1, the routine logs `Skip setting of newhome off`, sets `m_newhome_exit_flag` (`.bss+0x190`) to1 at0x3a20 and returns. It does not itself immediately restore the prior rate or clear a fault. Later source/mode paths consume state; full exit restoration has not been proven here.

## Output-rate helper is a separate hardware edge

`m_rosem_set_tcon_frame_rate` starts0x290. It derives a selected rate from low-input mode, VRR and source rate. Its NewHome condition at0x2e4..2fc selects **12000 (120Hz)** when cached NewHome is1 and `m_vfreq_144` is0, rather than simply forwarding the 50/60Hz input-rate policy. A changed selected rate calls the table at `.bss+0x338`, slot+520 at0x3ec/3f8. The compatible QD backend of that slot is covered separately in [the vfreq-backend report](newhome-tcon-vfreq-backend.md): QDFTcon_SetVRRFrameRate converts cached rate to a frame-mode update. Independent review found that its nested frame-mode implementation can use the exact QD panel-mute command F3:0x164 around F3:0x160 programming; the prior claim that0x15c carried the rate was incorrect. All returning bracketed paths attempt the final mute0, but its failure can be discarded upstream and requested mode/rate caches can suppress an identical later request. The bracket does not update the ordinary mute-state cache. No incident-aligned failure has been captured. This static edge is not evidence of a live request, panel acceptance, or emitted light.

The helper stores its selected `m_tcon_frame_rate` at `.bss+0x340` at0x404 **even if callback fails or is absent**. Nonzero callback return produces `[error] frame rate set...` first. Therefore a cached frame-rate report is requested/remembered policy, not proof that the panel accepted timing or emits light. Logs worth preserving are `new tcon_frame_rate`, `[error] frame rate set`, and `tcon_frame_rate:..., vfreq:..., vrr_max_vfreq:...`.

`m_rosem_send_cmd` (0xe50) masks the secondary argument to16bits, packs the command and argument into an8-byte existing extension request, and calls `tztv_frc_tcon_ext_cmd(1, request,8)` if initialized. Uninitialized paths can return0 without sending. This is an actual vendor output-policy request path when initialized, but the command name alone does not identify an external QDF MCU command or physical reset.

## Consequence for diagnosis

Home can alter FRC/source-rate policy and output timing in addition to rendering menu pixels. That is a plausible dimension to measure; it does not explain why two tabs within full Home differ. Neither a direct content-density test nor an elapsed-time sparse-page timer appears in these functions. No power/fault-reset call is established here. A deeper nested frame-mode path can use the same0x164 panel-mute command, so the earlier blanket exclusion of mute/gating on the full downstream path was incorrect. This does not establish a gate transition during the owner’s blackout. Source content, Home lifecycle, independent dimming state and panel-internal behavior remain separate candidates.

The retained visible/black paired snapshots contain no matching NewHome/rate messages in their retained windows (`overnight/newhome-existing-capture-extract.json` records the zero-match result). This is missing correlation, not proof that no calls occurred before those windows. A fresh observed transition should record these existing logs alongside QD commands and fault/mute evidence before any rate-mode change is considered.
