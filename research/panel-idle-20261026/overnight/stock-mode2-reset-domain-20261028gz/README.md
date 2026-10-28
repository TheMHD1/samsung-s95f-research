# Stock MODE2, ordinary PM and the controller emergency loop

**The recovered MODE2 route has no demonstrated full-context-reset contract.** It invokes QDF's off/on body and can acknowledge zero even when its later recovery work is skipped or reports errors. This follow-up adds two positive closures: the ordinary `set_power_mode` provider is present, but its current-family interface slots are initially null; and the selected image0 emergency routine tests its magic bypass only before entering a service loop that never revisits that test. A stronger existing user command that demonstrably clears the shared fault fields has not been qualified.

This package is host-only source research. It does not invoke or package a reset, USB request, root transport, memory write, firmware download or fault-state clear. Actual instructions run only against isolated synthetic memory with named callback stubs. Existing captures and reports remain unchanged. The parent's reported MODE2 acknowledgement/new USB instance with a later retained fault tuple is compatible with the recovered separation; this package does not independently replay that capture or identify the executing reset domain. The observation also does not exclude an unobserved clear followed by a new fault.

## Exact request and source domains

The frozen DH helper opens **`/dev/tztv_tcon`**, without a trailing zero. Its fixed request is decimal operation41, mode2, ioctl`0xc010749f`, with a zero-initialized 16-byte argument structure. The parent task's `/dev/tztv_tcon0` spelling is corrected here; the helper was not changed. Its existing ARM/root restrictions, native alarm and cleanup remain the predecessor's contract.

The retained API's `TCON_Request` arm at `.text+0xed80` loads the optional TCON interface and slot`0x458`; a missing interface/slot follows its zero-return branch. The QDF initializer registers `QDFTcon_SetQdTconPowerControl` at this slot. Mode2 calls `m_set_power_control(0)` at`0x11ce0`, then `(1)` at`0x11cec`, and ORs the two return codes at`0x11cf0`.

All Linux-module coordinates below are ELF section-relative offsets. The selected 5 MiB package has SHA256`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`; controller image0 linked VA maps to package file+`0x200`, image1 VA to file+`0x40200`. These CPU domains must remain distinct.

## What selects the MODE2 power branch

The complete QDF power body is `.text+0x11848..0x11b88`. It directly reads monitor field BSS`+0x1a8`, platform field`+0x1ac`, optional callback pointers and the ERR sample. It does not directly select a branch using QDF's low-power, panel-DPMS or suspend fields. Transitive transport/callback guards remain separate; the absence of a direct test here is not a statement that every lower operation always executes.

| Condition | Off body | On body |
|---|---|---|
|monitor exactly1|ACDET0; 1000 ms; optional DVDD0; final1000 ms|optional DVDD1; 700 ms; ACDET1; ERR check|
|monitor not1, platform exactly4|ACDET0; 10 ms; optional reset callback1; callback-present delay100 ms; final1000 ms|optional reset callback0; callback-present delay100 ms; 700 ms; ACDET1; ERR check|
|other platform|ACDET0; 10 ms; ELVDD selected from monitor zero/nonzero; final1000 ms|ELVDD selected from monitor zero/nonzero; 700 ms; ACDET1; ERR check|

On the platform4 path, `tztv_frc_tcon` resolves `sdp_ocl_reset_tcon_power` at`0x57d8..0x57f8`. The retained OCL implementation `.text+0x2b38..0x2b88` sends the byte argument through `SDP_OCL_I2C_MBox_Write` with operation1, command`0x3f`, length1. This is a positive sender binding. The mailbox receiver's rail/reset/core-domain behavior is not recovered. It is not sufficient to identify image0 startup, image1 startup, shared-root retention or instruction reload.

The off body zeros host cached power/state/PVCC fields before the hardware callbacks. The on body can set host cached power/PVCC to1 even on an ERR-status early exit. These Linux cached fields are not controller RTP-root readback.

## A zero acknowledgement does not attest the recovery tail

At`0x118e0` the on body's local ERR sample is initialized zero. If an ERR callback exists, its return code is ORed into the result, but its sampled value independently controls `0x118f4`:

- Nonzero ERR sample enters`0x11994`, logs “err_det is fault. skip the tcon recovery,” sets cached power/PVCC on and returns the callback aggregate. That aggregate can be zero.
- Zero sample, or no ERR callback, reaches the normal tail. `m_check_tcon_status(2)` at`0x1192c`, frame-mode recovery at`0x11930` and cached-register replay at`0x11934` are called. Their return values are not accumulated into the returned `w19`.
- A missing optional reset/DVDD/ELVDD/ACDET callback can be skipped without making the result nonzero. The API's absent-interface case adds another distinct zero-return path.

The isolated AArch64 oracle executes this complete retained QDF body in 13 finite cases. It verifies all-null on/off returns0, monitor/platform callback selection, nonzero ERR sample skipping the tail with return0, negative tail results being discarded with return0, and a negative reset callback being propagated. These are synthetic callback cases, not observations of the device's runtime bindings, ERR pin or electrical state. The oracle hooks external calls and does not execute their hardware implementation.

## Ordinary PM: provider recovered, current-family slots initially null

This explicitly supersedes two narrow statements in `tcon-research/qd-full-reset-versus-mode2.md`; the earlier report is preserved.

1. `set_power_mode` is defined **and exported** by retained `tztv_frc_tcon_api.ko`, `.text+0x7fc0..0x8058`. It loads the FRC interface from API BSS`+0x618`, optionally invokes slot`0x2b8`, then optionally invokes TCON slot`0x4c8`, ORing results. It is separate from operation41's slot`0x458`.
2. Exact straight-line initializer replay proves QDF clears its interface at BSS`+0x428`, size`0x758`, before pointer stores and `map_tcon_functions`; its slot`0x4c8` remains zero. RosemFrc clears BSS`+0x380`, size`0x3f0`, before its stores and `map_frc_functions`; its slot`0x2b8` remains zero. Thus, if these intended tables remain registered unchanged, the ordinary PM shim is initially a no-op. Live table binding or later mutation is not attested by this static result.

The host PM route also contains work outside that shim. Resume `.text.unlikely+0x174c` and`0x17c4` call **`_tztv_frc_tcon_set_pvcc(1)`**, not `tztv_frc_tcon_set_power(1)` as the old report's shorthand stated. Its subsequently started resume worker calls `tztv_frc_tcon_set_power(1)` at`0x1510`. Suspend's ordinary branch calls `tztv_frc_tcon_set_power(0)` at`0x2c68`.

The PVCC routine `.text+0x5b90` resolves DT property`samsung,sw-pvcc` and performs board-conditional GPIO/PS_ON/FPGA/PMIC work. `_tztv_frc_tcon_nreset_control` at`0x5a48` resolves DT property`samsung,tcon_nreset_gpio`. Resume invokes the latter only under its relevant runtime enable field, at`0x176c` or`0x1954`; these are conditional stock paths, not an established current-TV full-reset action. Its `gpiod_direction_output_raw` return is discarded before the value-set/free/log sequence. A GPIO success-format log is not readback of the GPIO or reset domain.

`set_power` has another important short path: if its requested mode equals cached field BSS`+0x284`, `0x60ec` branches to a log/zero return at`0x6304`. Otherwise it dispatches several optional FRC/TCON resume stages. The current QDF `Resume` implementation's ordinary stage0 performs internal-status/SSC work; stage10 conditionally performs status/frame/replay and sends its cached mute command; unsupported stages return0. Neither the top-level PM source nor the examined QDF power body supplies a proof that shared root`+0x240a` was initialized or that the selected instruction image was downloaded. The ordinary PM route may perform different physical work, but it has not been qualified as a stronger user-invocable recovery command here. No attempt to invoke it is proposed.

## Emergency entry and its actual service-loop boundary

GY independently traces the fault low-bit consumer: image0`0x214d4` reads RTP-root`+0x240a`, tests bit0 and can call `0xb660(0x10, "RTP_Monitoring")`. Its preceding effects include ordinary-gate-off, a reason field, AP_EXCO state and register/diagnostic operations. This is more than a report-only fault consumer, but execution in the current fault remains unobserved.

This task adds a precise loop correction. At`0xb6be..0xb6d6`, the routine checks AP first halfword`0x1234` and AP_EXCO-data first halfword`0xabcd`. Matching both permits an **initial bypass return**. Otherwise `0xb6da→0xb6f8→0xb6dc` starts the service loop. The backedge at`0xb6f8` goes straight to`0xb6dc`, not to the magic check. The loop calls `3ab34(1)`, `16fc0`, `39404(0)`, `276ec`, `20510` and `1f3e4` repeatedly. Therefore changing the magic words after entry is not, by itself, a demonstrated exit mechanism. No magic-word write is proposed.

Five isolated partial-tail cases execute these real instructions with service calls stubbed: all four initial match/nonmatch combinations and a case that changes both words after entering the loop. Only the initial double match returns through the pop. The late-mutation case keeps following the loop backedge for the bounded three observed entries. This proves the branch property of this slice, not that the real service routines cannot transfer control, reset a core or change the system asynchronously.

The suspected `0x276ec` mailbox-receiver bridge is not established. Its recovered positive path is:

```
276ec: enable byte getter38af0 -> CPU20000e30
        tick24df0, unsigned elapsed>=1 against CPU20000c38
27724(0) -> 2751c(channel0, selector0, bufferCPU20000c1c)
        -> 123d0(0, byteCPU20000c28, 1, 0,
                  length2, bufferCPU20000c1c, pointer398c5)
        -> 8a44: initialize channel transaction state and register-backed request
```

This is an outgoing transaction-initiation path with a fixed buffer/length and register-backed state. No decoded incoming command`0x3f`, image reset, magic recheck or RTP-root clear is recovered in this closure. The semantics of the bus descriptor/provider and the other service routines remain finite continuation boundaries; this is not an exhaustive assertion that the emergency loop has no external exit.

## Useful next evidence and scope limits

For a separately coordinated stock lifecycle observation, preserve a bounded kernel log interval that includes the action from before invocation, rather than only the latest noisy tail. Source-derived distinguishing markers are pinned in `validation.normal.json`:

- OCL sender's reset argument/result, and QDF power off/on plus ACDET/ERR messages identify the sender-side branch.
- Exact ERR-fault/skip-recovery versus “Check Tcon and register recovery” identifies the early return versus normal-tail entry; normal-tail entry still does not attest every command's effect.
- `[FRC Init Start]`, `[FRC Init End]`, `resume end` and the PM “already dpms on” message distinguish the separate host resume worker/short path.
- `gpio [tcon-nreset]` and `gpio [sw-pvcc]` messages distinguish conditional GPIO routes. They do not establish GPIO readback or controller-core reset.

Kernel log timestamps must retain their own clock domain unless a mapping to native timestamps is independently established. A new USB device number remains a lifecycle observation, not proof that image0's shared-root scatter row9 ran. GX positively proves that row9 initializes stop/fault/ordinary to0/0/0, while image1's local startup/counter clears can zero N without clearing that root. An operational clean0/0/1 requires an additional gate-on step and actual readback. A later full R tuple and independent descriptor/instance proof remain necessary to classify recovery; no universal clearing, instruction reload, optical outcome or causal fix follows from return0.

The smallest unresolved source gap for **MODE2** is the OCL mailbox`0x3f` receiver and its reset-domain/rail assignment. The smallest additional **ordinary PM** premise is the actual DT/runtime configuration of PVCC/nreset and the stock user-to-PM entry, followed by evidence of which branch ran. Neither gap is resolved by calling a named function remotely or selecting an undocumented reset command. No such command or live helper is added here.

The additive [trace continuation](trace-continuation.md) binds the actual nop-only runtime discovery, excludes function_graph, and also binds the later partial/refused capability request: all four fixed dynamic-probe interfaces absent before `/proc/kallsyms` lookup failed. It preserves a seven-event source candidate as an unimplemented conditional design; no function_graph/kprobe prototype is supplied on this observed system. Existing private static trace events and normal source-derived printk markers remain the available narrow route.

## Reproduction and frozen files

`audit.py` reads existing pinned ELF/package files in place, symbolically reconstructs both complete registration prefixes, checks exact relocations/instruction anchors and records 21 bounded source-span hashes. `body_oracle.py` provides only the 13 QDF-body and five emergency-tail synthetic cases. All 39 installed Unicorn files are rehashed against the retained official2.1.4 wheel-equivalence record before use. There are no tool installs/builds, OEM copies, network calls or device accesses.

Run from any directory with the retained dependencies available:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B audit.py > validation.normal.json
PYTHONDONTWRITEBYTECODE=1 python3 -B -O audit.py > validation.optimized.json
```

The checked-in normal/optimized outputs are byte-identical and use explicit checks unaffected by `-O`. `checkpoint.json` is the earlier initializer-only checkpoint, retained as such; the v2 validation files are authoritative for this completed follow-up. `source-inventory.json` seals only this directory's authored files; its input references do not authorize redistribution of retained OEM modules or firmware.
