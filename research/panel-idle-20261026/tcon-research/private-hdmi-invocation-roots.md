# Static invocation roots for private HDMI power helpers

This is offline analysis of copied kernel modules. It identifies a concrete V4L2 extended-control route to the two private HDMI helpers. It does **not** show this route ran on the TV, identify the userspace issuer, bind a Home/content/source change to a control, report panel light, or establish a blackout cause.

## Exact inputs

| copied module | SHA-256 |
|---|---|
| `binaries/tztv_hdmi_switch.ko` | `11d9c53a0e08300bb12b1cafd513e3fc6ee84ba1bcd434007e459dce70fa82b6` |
| `binaries/tztv_hdmi_switch_api.ko` | `c586a2601665a778a1e7401cd6b7553e03684f2e4536a282047b17059b7eec97` |

The API module exports `suspend_hdmi_suspend` at `.text+0x1bb8` (152 bytes) and `suspend_hdmi_resume` at `.text+0x1c50` (188 bytes). Its `__ksymtab` relocations are `+0x3fc` and `+0x3f0`. The switch module has two undefined imports and exactly four `R_AARCH64_CALL26` code relocations to them:

| switch `.text` call site | import | controlling case |
|---|---|---|
| `0x1930` | `suspend_hdmi_suspend` | direct suspend case |
| `0x2034` | `suspend_hdmi_suspend` | delayed-work-present suspend case |
| `0x1948` | `suspend_hdmi_resume` | direct resume case |
| `0x20d0` | `suspend_hdmi_resume` | delayed-work-present resume case |

Each is a direct `BL` placeholder at module-link time; its eventual loaded address is deliberately not inferred from this static ELF.

## Proven framework-to-helper path

`hdmi_switch_probe`, `.text+0x3998` (1,064 bytes), allocates/registers a video device. At `0x3a54..0x3a64` it assigns the video device's first callback pointer from `.rodata+0xae8`; relocation `.rodata+0xb08` binds that file-operation slot to imported `video_ioctl2`. At `0x3a68..0x3a84` it assigns the device's ioctl-ops pointer from `.data+0x28`; relocation `.data+0x288` binds that ops-table member to `hdmi_switch_vidioc_s_ext_ctrls`, `.text+0x23c0` (368 bytes).

That is static publication of the Linux V4L2 ioctl framework route. The framework implementation and a runtime file descriptor/issuer are outside these copied module bodies, so evidence stops at the framework boundary.

Inside `hdmi_switch_vidioc_s_ext_ctrls`, the extended-controls header must have class `0x00a00000` (`0x23d8..0x23e4`) and nonzero control count (`0x23fc..0x2404`). It iterates 20-byte entries and makes the direct local call to `hdmi_switch_set_ctrl` at `0x2468..0x246c`. The `sus_flag` test at `0x2448..0x2468` can choose a logging detour for controls other than `0x00a009bf`; both paths converge at that local call. It is not a suppressor of either private-control route in this function.

`hdmi_switch_set_ctrl`, `.text+0x15e8` (3,540 bytes), subtracts `0x00a00998` (`0xa00 << 12`, then `0x998`), range-checks to `<=0x3d`, then uses the signed-halfword branch table rooted at `.rodata+0` (`0x1600..0x1624`). Entries index `0x26` and `0x27` resolve from base `0x1628` to these cases:

| V4L2 control ID | dispatch entry | outcome |
|---|---:|---|
| `0x00a009be` | `0x191c` | calls private suspend helper |
| `0x00a009bf` | `0x1938` | calls private resume helper |

Retained strings independently label those IDs `V4L2_CID_DV_S_SUSPEND` and `V4L2_CID_DV_S_RESUME`; the table arithmetic above, not names alone, establishes selection.

## Case gates and scheduling behavior

Both cases first load a pointer from switch-module `.bss+0x78`.

- `0x00a009be`: `0x1924..0x1928` takes direct call `0x1930` if zero. Otherwise it reaches `0x2020`, calls the same helper at `0x2034`, conditionally cancels delayed work at the pointed object's `+0xc0` (`0x2038..0x2040`), then clears bits in switch BSS state. The helper return is not retained.
- `0x00a009bf`: `0x1938..0x1940` takes direct call `0x1948` if zero. Otherwise it calls resume at `0x20d0`; if its subsequently loaded object field is nonzero, `0x20d8..0x20ec` queues that object's `+0xc0` delayed-work object on CPU 4 with delay 250. This is a static scheduling fact, not a duration in a particular live kernel configuration. The helper return is again not tested by surrounding switch code.

The API-side idempotence and exact stock trace messages are pinned in [hdmi-private-power-log-markers.md](hdmi-private-power-log-markers.md): suspend proceeds only when its API-local cached byte is zero; resume proceeds only when it is one. Those `sdp_runtime_pm_put/get` markers are future passive-correlation candidates, not proof of callback success, hardware output, or origin through this V4L2 route.

## Scope boundary

This establishes one stock control-plane route from a V4L2 extended-control request with either exact control ID to the private API. It does not establish which component submits that request, whether the component is invoked by a source/content/UI event, whether the IDs occur during the symptom, or whether the private PM record has a live callback. It also does not exclude additional callers absent from the copied corpus. A byte-string scan of copied `binaries/` and `overnight/` module files found the names only in this API exporter and switch consumer; that is a scoped discovery aid, not a whole-system absence proof.

## Reproduction

[The offline verifier](private-hdmi-invocation-roots-reproduce.py) hash-pins both modules and its shared ELF reader. It checks exports, four import relocations, direct calls, framework-table relocations, branch-table arithmetic, and bounded dispatcher/gate landmarks. It writes [a saved disassembly](private-hdmi-invocation-roots-v3.disasm) only with exclusive creation and otherwise requires byte-for-byte equality.

```sh
PYTHONPATH=/tmp/tcon-capstone python3 private-hdmi-invocation-roots-reproduce.py
PYTHONPATH=/tmp/tcon-capstone python3 -O private-hdmi-invocation-roots-reproduce.py
python3 -m py_compile private-hdmi-invocation-roots-reproduce.py
```

The verifier confirms landmarks; V4L2 structure interpretation and register/dataflow are manually reviewable static conclusions. No TV transport, kernel control, network request, or display experiment was made.

### Arithmetic correction

An initial draft incorrectly transcribed `sub w0, w0, #0xa00, lsl #12` as an `0xa0000000` subtraction. On AArch64 that instruction contributes `0x00a00000`; together with the following `#0x998`, the actual base is `0x00a00998`. The IDs and class above were corrected before producer analysis; no live operation was involved.
