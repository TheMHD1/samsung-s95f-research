# Platform and function map

```mermaid
flowchart TD
    host[Research host: access, acquisition and offline analysis] --> root[Authorized target command channel]
    ui[Tizen Home / Apps / Live / ForYou] --> avoc[AVOC, deviced and display policy]
    avoc --> frc[Kernel FRC / QDF / SDP / HDMI providers]
    frc --> stock[Stock controller transport]
    root --> observer[Bounded native / managed observers]
    observer --> usb[External-controller USB read protocol]
    stock --> controller[QD controller firmware / RT protection]
    usb --> controller
    controller --> output[Panel electrical / optical output]
    swu[SWU CoreTV normal-world decoder] --> tee[libteec wrapper / common / backend]
    tee --> ta[Trusted application: acceptance and policy not fully established]
```

The arrows identify researched call or transport relationships. They do not prove a causal chain from a particular UI image to physical blackout. The external MCU, SoC MMIO, CPU addresses, bus windows and firmware load domains must remain distinct.

| Area | Concrete anchors | Boundary |
| --- | --- | --- |
| Access | Archive-root and host-assisted controller lifecycle; source modifications and e2e tests | Root availability is separate from reboot persistence and untethered boot changes |
| UI | Stock `/usr/bin/input_keyevent`, compositor D-Bus `org.enlightenment.wm.Test.EventKey`; managed Home / Apps / Terra components | Cached tab state does not establish focus or visible light |
| Display | AVOC panel mute, deviced policy, FRC/QDF ioctls, SDP registers, HDMI DPMS and AVMUTE | Successful IPC/ioctl and composited screenshots do not prove optical output |
| USB observer | Fixed read windows R/M/C/H/L, exact 12-byte OUT header followed by matching IN | Single USB owner; accepted OUT must receive its matching IN before any next OUT |
| Ordinary RT predicate | Stored image-1 caller around `0x1e68..0x2040`; aggregate at CPU `0x2000d0e4 + 4*i`; `low16(A[i]) > selected_fp`; fault literal `736 / 0x2e0`, reported fault 1001 | Retained tail execution does not recover missing operands at the comparison |
| Source map | Held table `0x584109a4..0x58410aa4`, four lanes of 16 unsigned words | Runtime writer, PrePD units and any DMA ownership remain unresolved |
| Callback lifecycle | Descriptors 8 and `0x1c`; teardown disables callbacks | Source-proven lifecycle is not observed runtime restoration after a fault |
| SWU / TEE | `TEEC_Context` 4 bytes, session 4, shared memory prefix 36; target operation requires at least 60 bytes, including backend word at offset 56 | A generic 56-byte operation is unsafe for this implementation |
| Header decode | First record `[1,2,1,2]`; full-byte parameter types; metadata-only commands 0 / 1 / 2 | No command-3 capture fallback belongs in the isolated metadata helper |

The detailed instruction excerpts, symbol maps, reproducers and independent reviews remain in the [research tree](research-map.md). See the [evidence rules](evidence-and-methods.md) before applying a map from stored firmware to a live image.
