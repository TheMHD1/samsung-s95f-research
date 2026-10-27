# Video measurement: target ABI confirmed, measurement-to-Pre-PD link absent

2026-10-27 UTC. Offline source/binary audit only; no TV/network-device command, installation, native capture execution, or target change. Read the current investigation and BQ producer-gap record before this review. All new artifacts are in `sources/video-measurement/`; upstream snapshots were read-only. Repository statements below are author reports unless explicitly corroborated from the retained target binaries.

## Concrete result

The retained target **does export the three `ppi_ve_*` RGB-measure functions**, and the matching saved `libave` backend establishes their actual call chain and output extents. Most useful new findings:

* **Pixel output is four 32-bit words (16 bytes).** BigSant's older `PixelSamplingCaptureMethod.Color` allocates only three words (12 bytes), yet passes it to the matching P/Invoke. This is a concrete ABI mismatch, not a reproduced crash. The same snapshot's V2 pads its color to 64 bytes; TizenAmbilight uses 256-byte unmanaged buffers.
* **The backend copies all 16 output bytes even when its `frc_ioctl` returns negative.** A condition limited to successful ioctl calls would miss this error-return path. A missing frontend backend can return `-95` without reaching this copy; the mismatch is conditional on reaching the identified `libave` backend with a non-null output pointer.
* **The kernel RGB getters have cache/skip paths, and some return zero without fresh acquisition.** In particular, one read path zeros RGB and computes its fourth status field before a hardware-disabled branch returns zero. `rc=0, RGB=0/0/0` is therefore insufficient to prove either current black content or loss of panel light.
* The dedicated kernel path reaches `tztv_frc_tcon_ext_cmd(0x400, payload, size)` with RGB suboperations 1/2/3. This supplies a specific next offline dispatcher edge. **No reviewed edge identifies, writes, aliases, or describes the MCU Pre-PD source `[0x584109a4,0x58410aa4)`.** Shared use of an FRC/TCON transport name is not such an edge.

## Source pins and evidence level

| Source | Pin / license | What was actually reviewed |
|---|---|---|
| RitwickVerma/TizenAmbilight | `ccb646600286a02150aa353db261ca3753a44a9e`, MIT; local git status clean | `PpiCapture.cs`, `VideoPlaneCapture.cs`, README, architecture docs, AGENTS, license |
| BigSant/HyperTizen | snapshot `e6b4acea23bd4fd53a779ac23f371db70a55eda1`; GPL v3 license text | old/V2 pixel samplers, selector, README, analysis/decompile reference, AGENTS, license |
| Retained target libraries | `libvideoenhance.so.0` SHA256 `3ce4e4741bad4883d7f097b7939e7b1f8853a354329b17398da496bf624228c9`; `libave.so.0.1` SHA256 `a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777` | ELF exports, Thumb instruction bodies, PLT relocations and backend table GOT slots |
| Retained target kernel modules | `rosem_frc.ko`, `sdp_frc.ko`; SHA256 in inventory and kernel pins | AArch64 symbol bodies/relocations; condition/position/pixel functions; bounded ioctl function review |

`inventory.json` records URLs, commits, licenses, reviewed paths and file hashes. The target files are pre-existing local captures; this audit did not establish that every stored file is the currently executing mapped image. `libvideoenhance` BuildID is `855ebdee8726d9b3af4907aab4ada26031fa73b3`. Its odd exported addresses carry the Thumb bit. These are file virtual addresses, not freshly measured process addresses. ARM32 user libraries and AArch64 modules match the stated mixed architecture; an AArch64 process must not be assumed able to call these ARM32 functions.

The BigSant README's [QE77S95F 1296.8 report](https://github.com/BigSant/HyperTizen/blob/e6b4acea23bd4fd53a779ac23f371db70a55eda1/README.md#L24-L63) says EFL UI captures became black during Plex playback, the pixel fallback selected, and coherent decoded-video capture remained unavailable in the regular developer app. That is a different reported setup, not reproduction on QN77S95FAFXZC / CY-AF077FLLV2H. TizenAmbilight's [S84F slot/freshness figures](https://github.com/RitwickVerma/TizenAmbilight/blob/ccb646600286a02150aa353db261ca3753a44a9e/README.md#L95-L111) are likewise author measurements: two slots, reported 20 ms settling, roughly 3.3–4.1 updates per second per spot at 24 positions. They are not target-S95F limits. No manufacturer-published ABI contract for these private entry points was found in the bounded Samsung/Tizen documentation search; manufacturer Hue usage is an upstream attribution, not independent authority for this ABI.

## Actual target call chain and structures

The saved frontend exports are:

| Function | Exported VA | Backend slot |
|---|---:|---:|
| `ppi_ve_get_rgb_measure_condition(void*)` | `0x46f445fd` | `+0xb0` |
| `ppi_ve_set_rgb_measure_position(int,int,int)` | `0x46f44549` | `+0xb4` |
| `ppi_ve_get_rgb_measure_pixel(int,void*)` | `0x46f44499` | `+0xb8` |

The frontend checks backend availability, may initialize it, and tail-calls the selected slot. Missing method/table paths return `-95`. The retained `videoenhancer_impl_set_funcs` stores GOT-resolved `impl_get_rgb_measure_condition`, `impl_set_rgb_measure_position`, `impl_get_rgb_measure_pixel` into exactly those slots (`0x2a091c`, `0x2a0926`, `0x2a0930`); `backend-slot-resolution.json` records those relocations. The impl wrapper may initialize its instance. The chain then passes through `VideoEnhancerImpl` → `ave_api_*` → `ave_frc_api_*` → `frc_ioctl(unsigned long,void*)`. Local annotated disassembly files retain each edge and PLT symbol resolution.

At the user-library boundary:

| Operation | `frc_ioctl` request | Backend payload / caller-output extent |
|---|---:|---|
| Get condition | `0xc0186672` | six 32-bit words, 24 bytes copied to caller |
| Set position | `0xc00c6673` | slot, x, y: three 32-bit words, 12 bytes |
| Get pixel | `0xc0146674` | slot followed by four output words in 20-byte ioctl payload; four words copied to caller |

These sizes are recovered from request construction and copies, not inferred solely from request encoding. The condition getter at `libave:0x24645c` copies offsets 0 through 0x14 into the caller. The pixel getter at `0x24669c` zeros its four local output words at `0x2466e0/0x2466e4`, sends the ioctl at `0x2466e8`, then copies two doubleword pairs to caller offsets 0 and 8 at `0x2466f4/0x2466fc`. A negative ioctl branches to logging at `0x24675e` and then back to that same copy at `0x24678e → 0x2466f0`; its negative return is preserved. The null-pointer case at `0x246790` skips the copy. Native output capacity is not supplied as an argument, so a small managed struct cannot protect itself after dispatch.

Kernel diagnostic strings identify the six condition fields as block count, block width, block height, delay, full width, full height. The pixel diagnostic labels the returned words R/G/B and LowInput. That corroborates the fourth field as a status-like input-lag value, rather than a fourth color channel; it supplies no photometric unit or calibrated luminance contract. The frontend/backend bodies reviewed here do not enforce the upstream 0..1023 color assumption.

The old BigSant source has [12-byte Color and 24-byte Condition](https://github.com/BigSant/HyperTizen/blob/e6b4acea23bd4fd53a779ac23f371db70a55eda1/HyperTizen/Capture/PixelSamplingCaptureMethod.cs#L237-L262), [P/Invoke of `ppi_ve_get_rgb_measure_pixel` using `out Color`](https://github.com/BigSant/HyperTizen/blob/e6b4acea23bd4fd53a779ac23f371db70a55eda1/HyperTizen/Capture/PixelSamplingCaptureMethod.cs#L214-L233), and [a validation call to that output before capture](https://github.com/BigSant/HyperTizen/blob/e6b4acea23bd4fd53a779ac23f371db70a55eda1/HyperTizen/Capture/PixelSamplingCaptureMethod.cs#L591-L620). The selector contains both [V2 and old implementations](https://github.com/BigSant/HyperTizen/blob/e6b4acea23bd4fd53a779ac23f371db70a55eda1/HyperTizen/Capture/CaptureMethodSelector.cs#L19-L35). This establishes a reachable source candidate, not proof that the old implementation ran on either TV. V2's [64-byte color padding](https://github.com/BigSant/HyperTizen/blob/e6b4acea23bd4fd53a779ac23f371db70a55eda1/HyperTizen/Capture/PixelSamplingCaptureV2Method.cs#L321-L350) covers the identified 16-byte output; its Condition remains 24 bytes. TizenAmbilight's comment that HyperTizen pads *both* structs is not true of these reviewed BigSant classes. No managed stack corruption was reproduced.

## Kernel behavior and side effects

In `rosem_frc.ko`, `m_rosem_get_rgb_measure_conditon` at `.text+0x22d8` returns a cached six-word object when the condition-init flag is one. Otherwise an enabled path locks and invokes the external command callback with command `0x400`, suboperation 1 and size 28. On success it copies six result words. Disabled/no-data paths can return zero without filling that result. Thus the condition getter does not guarantee a fresh hardware inquiry.

`RosemFrc_SetRgbMeasurePostion` at `+0x2760` sends suboperation 2, slot/x/y, size 16 through the same callback when enabled. This **programs sampling positions**. It is not a passive memory read. No explicit slot bound was found in these reviewed frontend/libave/rosem setter bodies; limits must come from a valid condition and the downstream implementation. Its disabled path can also return zero.

`RosemFrc_GetRgbMeasureInfo` at `+0x6a10` reads the index, clears RGB in its request object and sets the fourth field from shared flags, then conditionally sends suboperation 3, size 20 under a lock. A hardware-disabled path returns zero after those local zero/status stores. Other early skip branches can return without fresh acquisition. Return success and in-range zeros alone are inadequate freshness evidence. This is an offline path result; no sampled branch/flag/value is claimed for the current black-panel state.

TizenAmbilight's [native buffer and slot checks](https://github.com/RitwickVerma/TizenAmbilight/blob/ccb646600286a02150aa353db261ca3753a44a9e/TizenAmbilight/src/PpiCapture.cs#L111-L158) and [guarded setters/readers](https://github.com/RitwickVerma/TizenAmbilight/blob/ccb646600286a02150aa353db261ca3753a44a9e/TizenAmbilight/src/PpiCapture.cs#L191-L216) are useful source patterns, not a safety guarantee. It bounds slots to the reported count and at most16, uses one sampler thread, programs positions, waits and reads batches. The return from `SetPos` is not used to discard the associated later sample in [Step](https://github.com/RitwickVerma/TizenAmbilight/blob/ccb646600286a02150aa353db261ca3753a44a9e/TizenAmbilight/src/PpiCapture.cs#L341-L375), so stale slot contents can be accepted if setting failed and reading succeeded. Its 1..100 ms clamp can shorten a larger reported delay, and user overrides can change waiting. Neither codebase provides a proved freshness contract on this target.

The full-frame alternative also needs care. TizenAmbilight calls `secvideo_api_capture_video_main(reqW,reqH,param)` with ARM32 pointer offsets, 256-byte parameter storage, and caller-owned 960×540 Y / half-sized chroma buffers. Its first `Capture()` performs six extra capture calls sweeping color-format values0..5 before the normal call ([source](https://github.com/RitwickVerma/TizenAmbilight/blob/ccb646600286a02150aa353db261ca3753a44a9e/TizenAmbilight/src/VideoPlaneCapture.cs#L248-L295)). Its getter returns static buffers reused on the next capture. This is active native acquisition/scaler use, and post-call dimension clamps do not bound native writes retrospectively. The author reports capture wedges after deployment while capturing and API errors under protected content; those effects and return-code interpretations were not reproduced here. No saved target `libvideo-capture` binary was located in the reviewed binaries directory, so this ABI was not independently matched to target code.

## What this can and cannot distinguish

A **qualified, fresh** upstream video-plane result that continues changing while an independently observed panel is black would narrow a decoder/content-loss explanation; it would still not prove the last electrical output edge or the MCU protection-table producer. A compositor/UI screenshot is weaker because the video plane can be excluded, as both projects report. A few perimeter RGB spots also cannot characterize the whole frame or the damaged lower-edge region without known coverage. Failure, zero, repeated/stale results, and unqualified success have several software explanations and cannot be treated as a TCON-fault discriminator.

The retained AVOC introspection has607 unique method names. Filtering RGB/measure/capture yields only RGB-only-mode, custom-RGB color-space and RGB-sensor methods; no `rgb_measure`/`rgbmeasurement` operation appears. `saved-avoc-summary.json` records the source hash and exact matching method names. Those mode/sensor controls must not be relabeled as frame samplers. A bounded filename/literal search located no captured native RGB condition/value result in the retained panel-idle JSON records; absence in that search is not whole-system API absence.

This report supplies no bridge to BQ's missing `[0x584109a4,0x58410aa4)` writer/DMA descriptor. The content-sensitive blackout, persistent latch, stable populated Apps control and repeated Apps-selected operation41/mode2 recoveries remain the stronger target-specific evidence. None of the external repository tests diagnoses this impact-damaged panel or proves that image brightness is the physical fault trigger.

## Concrete next offline work

1. Resolve the retained `tztv_frc_tcon_ext_cmd` registration through `tztv_frc_tcon.ko` / its backend, then trace exactly command `0x400` and suboperations1/2/3. Determine the sampling stage, callback handler and whether it has a freshness/done acknowledgement. Keep this edge separate from the Pre-PD producer until an actual address/descriptor/dataflow connection is found.
2. Recover downstream bounds, field widths and maximum output size before considering a new target invocation. Preserve the16-byte caller output requirement and error-return copy behavior; do not reuse the old12-byte BigSant Color. This is a source-review requirement, not authorization or a proposal to install a capture application.
3. If a later separately authorized observation is designed, first specify which fresh stage can answer a concrete question, which position-setting writes it performs, and which owner-observed visible/black bracket it needs. Full-frame vs few-spot coverage, data freshness, slot ownership and an independent physical-light observation must be explicit. No new collector or target experiment was built by this audit.

Artifacts are regenerated offline by `disassemble-local.py` and `disassemble-kernel.py` using already present Capstone/pyelftools in `/tmp/tcon-capstone`. Export-size disassembly can include literal pools; only the explicit instruction/copy/relocation sites identified above are semantic claims. The inventory pins original inputs and current derived artifacts.
