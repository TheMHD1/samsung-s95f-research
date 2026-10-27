# HDMI resume registration and private dispatch

## Result

The exact `sdp_hdmi.ko` contains two different-looking resume mechanisms, but
only one has a recovered positive registration and consumer chain.

- A 184-byte `sdp_hdmi_pm` object is consistent with a 23-pointer
  `dev_pm_ops` table and points to `sdp_hdmi_pm_suspend` and
  `sdp_hdmi_pm_resume`. No relocation-backed attachment of that object to the
  module's registered `platform_driver`, or any other static consumer of the
  object, was recovered.
- The separately compiled global `sdp_hdmi_resume` legacy-style body has only
  its unwind-metadata reference. It is not in the module export table and no
  code/data registration reference was recovered.
- The module probe positively registers `sdp_hdmi_suspend_ext` and
  `sdp_hdmi_resume_ext` with Samsung's proprietary `sdp_runtime_pm_*`
  mechanism under the name `sdp-hdmi`. The matching saved kernel Image stores
  those callbacks in a named record, and `sdp_runtime_pm_get` invokes the
  saved resume callback directly. `sdp_hdmi_resume_ext` then calls
  `sdp_hdmi_pm_resume`, which calls `sdp_hdmi_resume_fxn`.

This closes a static callback path; it does not show that the registration
succeeded in the running kernel, that `get` ran during a physical blackout, or
that the callback caused, recovered, or prevented panel emission.

## Exact sources and reproducer

- `binaries/sdp_hdmi.ko`: 3,299,534 bytes, SHA-256
  `f7cffd19934ef459b0263ceddddf003306b399e01d0ddee48df3f64a86667994`
- `overnight/kernel-Image.bin`: SHA-256
  `77b6070c12a53f2b7ede3b7c503e242759e22dbaef2d12cc91b556416fed455d`
- `hdmi-private-resume-dispatch-reproduce.py` is a standard-library-only,
  hash-gated ELF/Image checker. It parses ELF64 sections, symbols and RELA
  records without executing target code. It passes under ordinary Python and
  `python -O`; its checks do not depend on `assert`.
- `hdmi-private-resume-dispatch.disasm` records the exact instruction words
  checked by the helper. The helper requires byte-for-byte equality with it.

The helper checks exact instructions and relocations. The CFG and structure
interpretation below was also reviewed manually; a `PASS` line is not a proof
of live state or physical causality.

## Standard-looking PM table is not attached in the exact ELF

Symbol identities in the module are:

| Object/function | Section-relative location | Size |
| --- | ---: | ---: |
| `sdp_hdmi_pm` | `.rodata+0x470` | 184 |
| `sdp_hdmi_pm_suspend` | `.text+0x46c8` | 416 |
| `sdp_hdmi_pm_resume` | `.text+0x4e60` | 700 |
| `sdp_hdmi_driver` | `.data+0x3f0` | 192 |
| `sdp_hdmi_resume` | `.text+0x5348` | 492 |

The only two relocations within the zero-filled 184-byte PM object are:

- `.rodata+0x480`, object slot `+0x10`, ABS64 to
  `sdp_hdmi_pm_suspend`;
- `.rodata+0x488`, object slot `+0x18`, ABS64 to
  `.text+0x4e60` (`sdp_hdmi_pm_resume`).

Those offsets and the object size are consistent with a `dev_pm_ops` table
whose system-suspend and resume callbacks occupy slots `+0x10/+0x18`.
However, no relocation in the exact module points to symbol `sdp_hdmi_pm` or
to `.rodata+0x470`.

`init_module` constructs `.data+0x3f0` and passes it to
`__platform_driver_register`. The four relocations inside that 192-byte
`sdp_hdmi_driver` object are the probe at object `+0`, name at `+0x28`, module
owner at `+0x38`, and OF-match table at `+0x50`. The legacy platform-driver
suspend/resume slots at object `+0x18/+0x20` are both zero, and there is no
relocation to `sdp_hdmi_pm` elsewhere in the driver object.

Neither `sdp_hdmi_pm` nor `sdp_hdmi_resume` appears in `__ksymtab`.
The only relocation whose target is `.text+0x5348` (`sdp_hdmi_resume`) is
`.rela.eh_frame+0xac4`, unwind metadata rather than a caller or dispatch
table. This check recognizes both section-plus-addend and direct named-symbol
relocations. A fixed four-byte scan of all 187,259 instruction words in every
executable PROGBITS section also finds no direct same-section AArch64 `B` or
`BL` to `.text+0x5348`. No conventional static registration or caller for the
legacy body is therefore established by the acquired ELF. This is a scoped
negative: runtime patching, name lookup, indirect computed calls, and code
outside the acquired static module are not excluded.

## Positive proprietary registration path

In `sdp_hdmi_probe` (`.text.unlikely+0x53c`), the incoming platform-device
pointer is retained in `x21`; at `+0x584` the code sets `x20=x21+0x10`, the
embedded device pointer. At `+0x1784..0x1798`, the call arguments are:

```text
x0 = embedded device
x1 = sdp_hdmi_suspend_ext (.text+0x4868)
x2 = sdp_hdmi_resume_ext  (.text+0x5120)
call hdmi_rpm_init
```

The corresponding ADRP/ADD pairs have exact relocations to those two local
functions. Probe then calls `hdmi_rpm_dev_init` at
`.text.unlikely+0x17a4`.

`hdmi_rpm_init` at `.text+0xaa7b0` constructs a stack record whose fields are:

```text
config+0x10 = device
config+0x18 = suspend_ext
config+0x20 = resume_ext
```

It passes that record and the exact string `sdp-hdmi` to imported
`sdp_runtime_pm_init_and_get`. Its return value is not tested by this wrapper.
`hdmi_rpm_dev_init` calls `sdp_runtime_pm_getdev("sdp-hdmi")` and stores the
returned pointer at module BSS `+0x164c8`; there is no non-null validation at
that store.

`sdp_hdmi_resume_ext+0x20` moves its saved device argument into `x0` and its
direct same-section `BL` at function `+0x24` (`.text+0x5144`) targets
`sdp_hdmi_pm_resume`. At `.text+0x4f78`, the latter reconstructs the
platform-device pointer as `device-0x10`, and at `+0x4f84` calls
`sdp_hdmi_resume_fxn`. This is the positive module-side callback chain.

The separate legacy `sdp_hdmi_resume` also calls `sdp_hdmi_resume_fxn` at
`.text+0x5444`, but this proves only the behavior of that body if invoked; no
registration or caller for the legacy body was recovered.

## Matching kernel consumer

The helper directly authenticates the PREL32 export records for:

| Export | Image file offset |
| --- | ---: |
| `sdp_runtime_pm_init_and_get` | `0x3fbf10` |
| `sdp_runtime_pm_get` | `0x3fc040` |
| `sdp_runtime_pm_put` | `0x3fc1c0` |

In `sdp_runtime_pm_init_and_get`, Image `0x3fbf58..0x3fbf7c` copies the caller
record's fields `+0x10/+0x18/+0x20` into named-record fields
`+0x20/+0x28/+0x30`, respectively. Thus the private record holds device,
suspend callback, and resume callback at those offsets. It increments the use
count at record `+0x3c` and clears state at `+0x44`.

In `sdp_runtime_pm_get`, when the use count at record `+0x3c` is non-positive,
the device at `+0x20` and resume callback at `+0x30` must both be non-null.
The code sets state `+0x44` to one, unlocks, then at Image
`0x3fc15c..0x3fc164` loads the device into `x0`, the callback into `x1`, and
executes `BLR x1`. It later clears state and increments the use count. The
callback return is not used by this path.

The complementary `sdp_runtime_pm_put` path loads device and the suspend
callback together from record `+0x20/+0x28` and executes `BLR x1` at Image
`0x3fc388`, after its private count/state/busy handling.

## Consequence for onset tracing

The positive consumer is a Samsung private named-record dispatcher that calls
the saved function pointer directly. It is not the normal Linux
`dev_pm_ops` callback attachment recovered from the module's registered
`platform_driver`. Accordingly, the standard `power/device_pm_callback_*`
and `rpm/*` tracepoints can provide positive evidence when a standard
framework path occurs, but silence from those six events cannot exclude this
private `sdp_runtime_pm_get` route.

The static evidence does not establish:

- successful live initialization or the live contents of the `sdp-hdmi`
  record;
- the live value of the proprietary global bypass byte;
- which thread or subsystem called `sdp_runtime_pm_get/put`, or when;
- absence of runtime patching relative to the saved matching kernel Image;
- any invocation aligned with an owner-observed picture loss;
- OLED light output, hardware fault, physical recovery, cause, or a safe
  prevention mechanism.

No TV call, runtime callback, PM transition, setter, kernel interface, or
firmware change was made for this analysis.
