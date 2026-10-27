# QD protection: bounded inventory of additional read telemetry

## Result

The copied host stack contains **no source-backed, ordinary read that expands
the accepted `0x00000010` result beyond the literal QD label `RT Protect`**.
Several interfaces expose useful context, but they fall into three different
classes that must not be conflated:

1. QDF getters that only return cached kernel words;
2. host-side counters, latches, and persistent configuration values; and
3. functions whose getter-like names actually send another controller, GPIO,
   extended-command, or engineering transaction.

The first two classes can qualify host history if sampled with exact identity
and timing guards. They do not identify the MCU condition that produced bit 4.
The third class is not a passive retrospective read and is not proposed here.
In particular, the copied code does not recover an RT-specific counter,
threshold, raw register bank, history queue, or log buffer.

The most useful already-retained additional evidence is the stock KPI sweep at
uptime `73112.460..73112.463`: it logged external temperature data, cached
error counters, TCON status, PMIC-init info, Vx1 lock, TCON-IP state, and HSM.
It precedes the late `73131..73137` power sequence by about 19 seconds and the
`CAPTURE_END` marker by about 25 seconds. It therefore cannot exclude a later
or transient condition and does not explain the fresh status word read at
uptime `75262.252253`.

This is an offline result. No TV, root, network, device, GPIO, controller,
getter, callback, reset, retry, power, or protection operation was performed.

## Pinned corpus and scope

| Input | SHA-256 |
| --- | --- |
| `binaries/libave.so.0.1` | `a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777` |
| `binaries/qdf_tcon.ko` | `97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63` |
| `binaries/tztv_frc_tcon.ko` | `aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd` |
| `binaries/tztv_frc_tcon_api.ko` | `3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6` |
| accepted `result-20261026c.json` | `5ccac8a789fd83b3b276b39e6bf33201087c8e4354d580f7bb316075ed04bea6` |
| filtered status-c dmesg bytes | `d454a04995c5298f31693260f1243e7dcb4f5cf8335312e798b3e99e27b7e9f9` |
| rescued `vlog-after.txt` | `eac02d7bf3a4fb216295edba8be99466d7b80c7a43f7535841f882b052c1c3d3` |
| `owner-power-on-log-analysis.md` | `37dbe0bd4f4474cb31eed81a979c0ec52e0fc224e4d897df30330df101c290b2` |
| `rt-protect-controller-path.md` | `e0513f03aee37aeeaa63a7765210c626aa7d4e4b6e86b55c87ae573cdb21403e` |
| `monitor-input-status-provenance.md` | `382a4783d5b2313b76816eea4ebb7a5847fe8abe47adb1194a5e4a4cf2d04aca` |
| `tcon-monitor-selector-0c-analysis.md` | `8516000034da348d287159c5e99d4d04a203273cbb934ad08d21684734646727` |

AVE addresses below are ELF virtual addresses. QDF addresses are offsets in
the module's `.text`. The inventory covers named/direct paths in these copied
objects and the retained logs; it is not a whole-program proof over arbitrary
indirect callbacks or unrecovered MCU firmware.

## The accepted word remains the only RT-specific telemetry

The accepted one-shot path was AVE `ave_tcon_get_err_det_status(int *)` at
`0x25d164`, ioctl `0xc010749f` operation `0x1f`, and
`QDFTcon_GetErrDetStatus` at QDF `.text+0xa000`. QDF sends the proprietary
read `F3 80 00 00 00 08`, raw-logs the returned word, and may only afterward
apply its debug override. The retained matching row is:

```text
[75262.252253] [TCON:QDF] QDFTcon_GetErrDetStatus[3216:TconStatusRead.]: ERR DET Status:0x10
```

The AVE QD decoder names bit 4 `RT Protect`. Bit 7, whose literal label is
`PMIC fault`, was clear in this particular word. That does not exclude a
separate PMIC problem, an earlier pulse, or a condition not represented by
this eight-bit decoder. The copied host code still does not define bit 4's
producer, physical threshold, persistence, clear condition, or read-to-clear
semantics.

## Read-looking QDF interfaces

### Cached values: low side effect, limited freshness

These reviewed QDF bodies contain no controller or GPIO read:

| Function | Exact body | Returned source | Supported interpretation |
| --- | --- | --- | --- |
| `QDFTcon_GetTconStatus` | `+0x4e0`, 224 bytes | BSS power word `+4` and TCON state `+0x10` | cached software state |
| `QDFTcon_GetPMICResultMode` | `+0x698`, 180 bytes | BSS `+0x20` | cached result of another PMIC path, not a live PMIC register |
| `QDFTcon_GetTconDataStatus` | `+0x750`, 92 bytes | BSS `+0x24` | cached data-status word |
| `QDFTcon_GetHsmStatus` | `+0x978`, 284 bytes | BSS power/state and words `+0x30..+0x3c` | cached five-bit aggregate |
| `QDFTcon_GetCurrentTemperature` | `+0x2b38`, 104 bytes | BSS `+0x58`; validity gate `+0x68` | cached monitor temperature |
| `QDFTcon_GetCurrentTcon2Temperature` | `+0x2ba0`, 108 bytes | BSS `+0x5c` | cached second temperature |
| `QDFTcon_GetCurrentTcon3Temperature` | `+0x2c10`, 108 bytes | BSS `+0x60` | cached third temperature |

`QDFTcon_GetHsmStatus` synthesizes bits from cached power/TCON, PMIC, LPDDR4,
ELVDD, and I2C-communication state. Its body is already resolved in
`monitor-input-status-provenance.md`. A zero HSM word is not a fresh
electrical-health result. The current-temperature getters similarly copy
cached words written by a separate monitor; their units, update time, and
relationship to RT bit 4 are not established by these getter bodies.

### Fresh or externally sourced values: not passive retrospective reads

The following functions have material transitive behavior despite their
names:

| Function | Proven direction / behavior | Why it is not an RT-source discriminator |
| --- | --- | --- |
| `QDFTcon_GetExtTemp` `+0xa1b0`, 400 bytes | sends controller read `F3 80 00 00 00 02`, reads four bytes, and retries once after a 10-ms sleep if the low byte is `0xff` | temperature field layout/units and any relationship to RT are unproved; controller read side effects are unknown |
| `QDFTcon_GetExtTempPcb` `+0xaeb0`, 124 bytes | forwards to the separately reviewed selector-`0x0c` controller monitor path | exposes two external PCB-temperature fields, not an RT producer or protection history |
| `QDFTcon_GetTconPMICFault` `+0xa5c8`, 652 bytes | sends controller read `F3 80 00 00 00 01`; compares the raw word with mode-dependent patterns such as `0xabababab`, `0xabeeabab`, or `0xeeeeeeee` | caller receives a collapsed fault result rather than the raw word; query semantics and relation to RT are unproved |
| `QDFTcon_GetPMICInitInfo` `+0x13e8`, 368 bytes | on its active gated path takes the TCON lock and calls `tztv_frc_tcon_ext_cmd` with operation `0x11` and an 8-byte buffer | it is an extended command, not a cached read; returned zero in the earlier stock KPI sweep but is not fault-source history |
| `QDFTcon_GetPMICStatus` `+0x6dd8`, 628 bytes | calls the EW/engineering helper with command word `0xf7090000`, parses seven results, and caches the first at BSS `+0x20` | it is an engineering test transaction, not an ordinary passive status getter |

`QDFTcon_ReadOneCommand` at `+0xa140` is a generic caller-supplied controller
command boundary. A function that can send an arbitrary command is not a
bounded diagnostic until the exact controller opcode and its side effects are
known; this report does not construct or recommend such a command.

The GPIO-backed ERR_DET and VDD_DET getters are also not passive. Their lower
provider requests GPIO ownership, makes the line input, reads it, and frees
it. That path is already closed by `monitor-input-status-provenance.md` and is
not relabelled as an additional controller register.

## Host counters and history

The QD monitor has a compact, directly symbolized userspace state block. In
the exact `libave` image it begins with named words at `0x005bfc5c`:

| VMA | Named state |
| --- | --- |
| `0x5bfc5c/60/64` | ERR_DET, VDD_DET, and ELVDD/I2C per-invocation counts |
| `0x5bfc68/6c/70` | ERR, VDD, and ELVDD/I2C retry counts |
| `0x5bfc74` | `si_ok_count` |
| `0x5bfc78` | `qd_tcon_off` host history latch |
| `0x5bfc7c/80` | one-time-execution and IP-status count |
| `0x5bfc84` | `s_pmic_fault_type` |
| `0x5bfc88` | monitor-local `fault_occurred` |

`ave_tcon_get_pmic_fault_type(int *)` at `0x26c459`, 92 bytes, merely copies
the cached word at `0x5bfc84`; it performs no fresh hardware read. The nearby
`ave_tcon_check_pmic_fault_type` at `0x26b1b9`, 256 bytes, classifies a buffer
supplied by its caller and does not acquire that buffer. Neither defines an RT
subtype.

The existing onset observer already samples a guarded 38-word range starting
at `A+0x5bfc5c`. That is the appropriate mechanism for aligned host-policy
evidence: exact executable/hash/PID/start/maps guards, raw words, and timing
must remain attached. A later standalone memory read can describe current
host bookkeeping, but cannot reconstruct when a counter changed or whether a
value changed away and back.

`libave` also exposes vconf-backed getters for:

- `db/frc_tcon/main_out_error_count_prd`;
- `db/frc_tcon/pmic_error_count_prd` and the `_2_prd`/`_3_prd` variants;
- `db/frc_tcon/usit_error_count_prd`; and
- `memory/factory/pmic_fault_prd`.

The matching getter functions at `0x29352d`, `0x2936e9`, `0x29377d`,
`0x293811`, `0x2939cd`, and `0x2932dd` call vconf/product-data accessors and
copy an integer result. Matching setters exist. These are host storage and
policy history, not raw controller registers. Persistence, writer cadence,
reset policy, and temporal relation to the accepted `0x10` are not recovered
by the getter bodies.

Two superficially promising high-level APIs do not close the gap. In the
copied `libave`, `ave_api_get_pmic_fault_with_reason` (`0x28e099`) dispatches
through `VideoEnhancerImpl::get_pmic_fault_with_reason`; that local method
(`0x29fbc9`) calls the public API through its PLT. The analogous
`ave_api_get_pmic_fault_register_status` (`0x296f51`) and
`VideoEnhancerImpl::get_pmic_fault_register_status` (`0x2a0605`) form the
same local PLT cycle. Runtime symbol interposition or a different provider
could alter those calls, but no such binding is retained. These names alone
therefore do not establish a working normal raw-register read, its data
source, or its side effects.

## What the retained stock logs already say

The rescued vlog contains two stock KPI sweeps, at approximately
`73052.450..455` and `73112.460..463`. The later sweep reports:

- external temperature raw value `0x472d0000`;
- two external-PCB values `0x17, 0x17`;
- vconf `main_out_error_count=0`, `pmic_error_count=0`, and
  `usit_error_count=0`;
- cached TCON status `1`;
- PMIC-init info `0`;
- Vx1 lock status `1`;
- QDDimming TCON-IP status `0`, picture-mode word `0xA0000`, and logo
  brightness `0`; and
- QD HSM status `0`.

Those are positive records of what the stock software returned then. They do
not prove physical light, a healthy controller, or absence of a fault at the
later transition. Some of that KPI sequence is itself active—the log also
shows `StartLocalDimmingTest`—so its presence is not a template for a new
standalone read.

The rescued vlog is exactly the configured 64-MiB cap and ends 37.5 ms before
`CAPTURE_END`. Its lack of `RTProtect` text is not negative evidence. The
later bounded kernel-buffer read retained the raw `ERR DET Status:0x10` row,
but no additional RT-specific payload. Reading existing log buffers can
preserve messages that were already emitted; it cannot recover an unlogged
MCU register, counter, or historical transition.

## Practical boundary

There is no newly justified stock call that can distinguish the physical
source of `RT Protect` without the missing exact controller semantics. The
bounded options that remain genuinely passive are:

1. retain already emitted kernel/vlog records with explicit ring and endpoint
   coverage limits; and
2. during a future observed event, retain the already reviewed, guarded AVE
   monitor-state sample alongside exact software/wire/log timing.

Those can distinguish some **host-observed classes**—for example an ERR retry
transition versus VDD/ELVDD bookkeeping, or a cached PMIC-fault-type change.
They still cannot show what caused MCU bit 4, whether bit 4 caused the black
picture, or whether an Apps/non-Apps content state was relevant. Without an
aligned visible-picture timeline they also cannot associate a state change
with physical onset.

A fresh external-temperature, PMIC-pattern, PMIC-init, raw-command,
engineering-status, GPIO, or repeated ERR-status call would add a new
transaction whose freshness and side effects are not fully defined. It is not
recommended by this inventory. No callback, reset, control, retry, or recovery
recipe follows from the available evidence.

## Bounded negative statement

Within the four pinned host ELFs and retained logs, the reviewed named/direct
surface comprised QDF status, HSM, temperature, PMIC-result, PMIC-init,
PMIC-pattern, engineering PMIC-status, generic-command, ERR/VDD GPIO, AVE
monitor counters/latches, vconf fault counters, cached PMIC fault type, and the
two high-level PMIC fault APIs. No RT-specific detail beyond bit 4's literal
label was found.

This does **not** prove that no such telemetry exists in the unrecovered F77
MCU firmware, an unexamined indirect provider, a different build, or external
factory tooling. It only closes the tempting host-side getter/counter routes
above as a normal, source-backed way to identify the present fault's physical
origin.
