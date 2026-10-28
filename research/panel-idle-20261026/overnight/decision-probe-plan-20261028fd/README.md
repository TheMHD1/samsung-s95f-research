# Decision-probe investigation: a resolved Linux log route and its boundary

The new source result is a concrete resolution of two Linux logging paths. The kernel `vlog` callback is supplied by `logger.ko`; a separate stock debugfs file reads an internal TCON/FRC log buffer. Neither path is currently connected to the external controller's RTP comparison. A **single fresh-open read requesting and allocating exactly4096 bytes** is source-bounded for the latter file, despite its small-request bug. This is a candidate for a separately reviewed observation, not an implemented or executed probe.

All work here is host-only. There is no target adapter, target read, shell command for deployment, executable patch, logger installation, USB transaction, network access or change outside this directory. No OEM module, firmware bytes, raw root envelope or device identifier is copied here. `audit.py` reads retained files and models the read-length branches; it does not open any target or special file.

## New source closure: who owns kernel vlog

The extracted, symbol-bearing `logger.ko` is111614 bytes, SHA256 `1ccf7188a64c9a2597f1a1aa0c6dc776e0b04a0c3382bba61d13f9f61f56a9dc`. Its ELF relocations establish:

- `.text+0x66bc` addresses `.data+0x418`; `.text+0x6844` adds0x68, making the argument `.data+0x480`.
- `.text+0x6848` calls imported `vlog_set_ops` with that argument.
- `.data+0x480`, named `g_vlog_ops`, has a slot0 relocation to `.text+0x5e50`, `_vlog_write`.
- `_vlog_write` tests the initialized logger state, applies severity/tag policy and reaches `vlog_write_internal` at `.text+0x5a40`.

This closes the callback-provider step left open in CS's kernel report. It does **not** establish the live pointer, current module configuration, transport of external-controller UART bytes into this callback, or access to the embedded CPU's registers. Registering/replacing these ops would mutate kernel log routing and is not proposed. Kernel Image offsets and module section offsets are source coordinates, never live kernel addresses.

## New source closure: the stock TCON/FRC debugfs reader

The extracted `soc/sdp_tcon.ko` is226262 bytes, SHA256 `9b7c1cb8e2bb8d11e5465a41fa402e71bd8d15a5dabd6b3d76de98a7a42549ee`.

| Exact source coordinate | Proven relation |
| --- | --- |
| `.text+0x71b0`, strings+0x2a98/+0x2b68 | Creates directory `tcon` and file `tcon_micom_log`; resolves candidate tracefs-independent path `/sys/kernel/debug/tcon/tcon_micom_log` if that debugfs is mounted there and the driver registered it. Current existence was not checked. |
| `.rodata+0x1670`, relocation | File read callback is `.text+0x61b0`, `tcon_dbg_tcon_micom_log`. |
| `.rodata+0x16d0`, relocation | File open callback is `simple_open`; retained kernel Image+0x1b6b60 only transfers inode private data into file private data and returns0. |
| `.text+0x970..0x9b4`,0xa48..0xa54 | Parses four resource rows,0x48 bytes apart, under DT node `sdp_mmap`. Fourth row `.data+0x2b8` is `samsung,tcon_info`; its physical cells are at+0x2ec/+0x2f0. |
| `.text+0xc84..0xcd8` | Builds the64-bit physical base, maps base+0xa0000 for0x20000 bytes, and stores the resulting pointer at device+0x378. |
| `.text+0x61c8..0x61cc` | Reader gets that pointer, reads its first unsigned16-bit value, and computes length `L = value + 1` in32 bits, so1<=L<=65536. |
| `.text+0x62ec..0x62f8` | Copies bytes from mapped buffer+4+file position into the user buffer. The length/header is **not included** in the returned payload. |

Candidate board DTB1's `/sdp_mmap` property `samsung,tcon_info` is `[0x1,0x5fe00000,0x100000]`. Thus the source-derived candidate log mapping is physical `0x15fea0000`, extent128KiB. This is a reserved-region description from the selected firmware tree, not a live physical address qualification or a `/dev/mem` plan. Boot-time DT modifications are already positively known from CS. No direct physical/MMIO read is proposed.

This buffer is distinct from the external-controller stock image1 ring at direct DMA address `0x20200000`, extent0x3c0c. No producer, shared-storage alias or message bridge between them was recovered here. Names containing “micom” or “TCON” do not supply that edge.

## Exactly what a fixed4096 read can and cannot promise

The reader contains a real count-contract defect for small requests: when `L<=4095`, `.text+0x6214..0x621c` chooses copy length `L` without limiting it to the caller's requested count or subtracting the file offset. For example, a request for16 bytes with header value100 can cause a101-byte copy. A small read is therefore not a sound bounded prototype.

The narrow alternative is one fresh open, initial file position0, **one direct native read with count4096 into an initialized4096-byte allocation**, then close. No buffered stream, `cat`, repeated read, seek, mmap, ioctl, setting change, init or print callback is part of this candidate. The offline branch model exhaustively checks every possible16-bit advertised length at initial position0:

- `L<=4095`: copy length `L`, hence at most4095.
- `L>=4096`: the source subtracts the admitted position and chooses the remaining count when it is at most4095; otherwise it uses the requested4096. The requested value is below the source's signed-INT_MAX/BUG boundary.
- Negative positions return EINVAL. Positions above0x3ffff or at/after `L` return EOF. Since admitted position is strictly below `L<=65536`, the subtraction cannot underflow; at fresh position0 the source span ends no later than mapped buffer+4100.
- Additional tested positive offsets also keep the copied source within the128KiB mapping, but **the candidate forbids all seeks and later reads**. It does not rely on that more permissive model.

A successful copy is not an ACK to this buffer in the audited body: every store in `.text+0x61b0..0x634c` targets the stack or the caller's VFS file-position pointer. The two helpers are unusually simple in this exact module: `tcon_rpm_dev_tryuse` at+0x270 reads a flag at device+0x4cc; `tcon_rpm_dev_disuse` at+0x280 returns0. Neither is a hidden runtime-PM get/put in this body. `simple_open` does not run the log initializer. Reading may still race a producer, and a failed/empty path may emit a kernel diagnostic. A stock I/O mapping is not by itself proof against every hardware read side effect.

Two limitations must be explicit in any future receipt:

1. The driver ignores `__arch_copy_to_user`'s uncopied-byte result and advances the VFS position. A positive driver return is not a checked complete-copy certificate. A valid initialized, prefaulted allocation reduces ordinary copy faults but does not repair this source behavior.
2. Only payload is returned. A4096-byte result may be a prefix; a shorter result still has no atomic producer/header freshness proof. No returned text proves that the external RTP decision generated it. Keep raw bytes, byte count, errno, host/native read brackets and separate `externalRtpProducerProven=false`/`completeLogProven=false` fields. No event absence conclusion follows.

This is the smallest newly source-bounded reader candidate from this audit. It is **not built or deployed**. Its usefulness is primarily to test whether this distinct stock log already reports a relevant internal message. It cannot close actual FP, selected-A or caller-LR blindspots without a producer bridge.

## Entry points that must not be substituted

` sdp_tcon_log_int_init` at `.text+0x6f38` calls `__memset_io` with length0x3ff00 when its separate pointer is nonnull. Driver debug initialization calls it. The ordinary log-out callback at `.text+0xfa0` can write halfword0x11 at its buffer+2 before invoking the printer; the error callback also updates a TCON-info field. These are distinct mutating paths, not passive ways to “enable the log.” No caller, sysfs knob, module parameter, initialization or acknowledgement operation is included in the4096-byte candidate.

## What can actually instrument the embedded decision

The four DS sites remain source-pinned image1 VAs with FILE=VA+0x40200:0x2024 (score/FP before202a),0xbd58 (selected-A/B entry),0xc5d0 (formatter and its qualified callers), and0xc1e0 (setter event/LR). FD pins their exact source spans. The selected asset SHA256 is `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`. Completed DX/EP sampled-code matches improve sampled identity/read reachability; they do not show writable instruction storage, active fetch, safe detour replacement, cache visibility or independent rollback.

Linux kprobes, function tracing and ordinary perf breakpoints operate in the Linux CPU/kernel domain. An image1 linked VA is not a Linux probe address. A Linux probe on a host status/read function can observe that function's request or result, not the embedded CPU's live `r7`, `fp`, `LR` or selected A. The retained runtime capability probes found no `kprobe_events`, `uprobe_events`, `available_filter_functions`, `/proc/kallsyms` or `/proc/config.gz` at those samples. The namespace-zero9379-export reconstruction contains `tracepoint_probe_register` but not `register_kprobe` or `register_ftrace_function`. This is not a complete symbol/config census and does not prove those configurations are disabled. Existing private-instance GPIO/IRQ/power **static tracepoints were actually exercised later**; broad claims that kernel tracing is unavailable would be wrong. Those events are host-side effects and have no source-PC/register payload.

The source-backed direct-event alternative is already fully designed in ET. Its stock ring actually captured V6's duplicated `rtp_act_736` after a gate0→1→0 lifecycle. That supplies the event **argument**, not an executing caller PC/LR; it does not retain score/FP/selected-A. FD does not duplicate ET's combined-owner design, change its deadlines or output-size obligations, or pretend an implementation exists. Building that finite combined owner is a concrete next implementation if event-code provenance is the chosen objective.

For actual decision-time operands, the exact remaining prerequisite is still an owned execution facility. DZ shows image1 startup/BSS through0x2000e19c, an unclassified7780-byte gap, owned RTP context at0x20010000 and fixed-reference buffers above it; a numerical gap or zeros are not a reservation for DS's5952 bytes plus stub/context. The image0 allocator is a different CPU bank, with no qualified remote invocation or transferable ownership. MODE2 proves a reset/transport lifecycle, not original instruction reload. No Linux log-mask setting resolves these controller ownership/installation/cache/rollback obligations.

## Finite next source task

The Linux-side uncertainty is now sharply located: trace the **producer and programming of `samsung,tcon_info +0xa0000`**, not an arbitrary UART or memory scan. Start from the exact `sdp_tcon` resource mapping and the stock FRC firmware path that programs/uses this shared region; require a source or message edge to the selected external image1 before calling it an RTP source log. A positive internal-only producer result would exclude this route for comparator logging. Current FD does not assign that producer from names, follow a persisted/high-bank/POFLG route, or prescribe new MMIO reads.

The practical choices are consequently explicit: ET's finite stock event logger can add an event argument; the newly bounded4096-byte stock Linux reader can test a different log domain if separately reviewed; actual comparison operands still require a positively owned controller hook/debug facility. No generic “turn on debug” command is warranted by the present sources.

## Reproduction and freeze

Run `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/tcon-capstone python3 -B audit.py` and the same command with `python3 -B -O`. The two196960-check outputs match byte-for-byte. Most checks exhaust the65536 first-read length values; they are arithmetic/source checks, not hardware tests. Explicit checks remain active under optimization. `source-audit.json` retains exact ELF relocation/instruction facts and range hashes; `input-pins.json` pins14 retained inputs, including source modules, the kernel/export index, candidate DTB metadata, and prior boundary reports. OEM inputs remain at their original private locations. No current runtime metadata, live driver identity or target acceptance is added.
