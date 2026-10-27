# RGB command 0x400: retained SDP sampler dispatch and external-controller boundary

2026-10-27 UTC. Offline analysis of existing copied artifacts only. No TV command, device/network contact, installation, module load, target execution, or new sampling took place. This report owns only `sources/rgb-controller-dispatch/` and this report; prior evidence was read-only. Addresses below are offsets within the stated ELF section, not live kernel addresses.

## Result

The exact retained implementation closes the RGB-measure chain through a **host SDP FRC memory-mapped sampler**, conditionally on ordinary stock initialization and dispatch gates. `sdp_frc_ex_proc` handles operation `0x400` itself and calls `sdp_frc_dev_cust_get_pixel_measure`; its three suboperations use a local condition table and two MMIO register sets. It does not forward this case to `sdp_tcon`, a message box, `tcon_ex_proc`, or the external QDF I2C route.

The concrete transport conclusion is stronger than the earlier unresolved callback, but the pixel pipeline tap remains undocumented: the acquired code proves the `sdp_frc` register aperture, configuration and RGB reads; it does not identify whether those registers sample before/after a particular scaler, compositor, FRC interpolation or protection block. The evidence does not establish optical output, a new-frame acknowledgment, or any dataflow edge into external-QDF Pre-PD `[0x584109a4,0x58410aa4)`.

New operationally relevant static findings:

- This backend enforces exactly two slots, indices **0 and 1**, for setting and reading.
- Stored nominal condition is `{2,16,16,20,3840,2160}`: slot count, block width/height, reported delay in ms, full width/height. It is mutable software metadata, not a hardware-freshness response.
- The setter accepts nonnegative x/y **up to and including** the stored full width/height. It does not subtract the 16×16 block extent. This is what the comparisons implement, not a recommendation to use an edge coordinate.
- RGB reads are three independent register loads without a new-frame wait, sample sequence, done acknowledgment or position/read pairing. A read immediately after setting can therefore lack freshness proof.
- The returned RGB words are masked to 10 bits only if another register at `+0x22188` reads zero; a nonzero value leaves the three full 32-bit words unchanged. A universal `0..1023` output contract is not proved.
- Dummy device access can turn reads into logged zeros and writes into logging while the sampler operation returns zero. Existing upper-layer zero-return skip/cache cases also remain applicable.

## Inputs and reproducibility

| Retained module | SHA-256 |
| --- | --- |
| `rosem_frc.ko` | `c646b45d8ab5028defca91b5f8188bf905b8d29f8927fae292be591c94cdbd34` |
| `tztv_frc_tcon_api.ko` | `3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6` |
| `tztv_frc_tcon.ko` | `aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd` |
| `sdp_frc.ko` | `05dea2eaad34a23def837fb86d2f7a4e99ef630066ad6fed18d0cf55ba37063d` |

Inputs are `panel-idle-20261026/binaries/`; there was no `panel-idle-20261026/kernel/` directory. The retained device-tree subtree is `overnight/devicetree/soc/sdp_frc/`. `source-inventory.json` pins module/function bodies, DT files and the prior measurement/identity reports. `derived-manifest.json` pins generated evidence and this report. All modules here are AArch64; the prior `libave` caller is ARM32, and the proposed external-controller executable is Thumb MCU code. Equal terminology across these architectures is not a dataflow relationship.

From the sources directory, using only already available dependencies:

```sh
PYTHONPATH=/tmp/tcon-capstone python3 extract.py
PYTHONPATH=/tmp/tcon-capstone python3 verify-evidence.py
```

`extract.py` writes bounded symbol-body Capstone listings with each ELF relocation, complete relocation/symbol maps for the four inputs, and function hashes. `verify-evidence.py` gates four full-file hashes and independently checks selected dispatch, bound, mask, MMIO and mapping instruction/relocation landmarks, the nominal condition table, and retained DT resource. Its PASS is not emulation or exhaustive path verification. `evidence.json` contains exact register offsets and the bounded literal census. No acquired ELF code is executed by either script. An independent `aarch64-linux-gnu-objdump -dr --section=.text --start-address=0xa0b0 --stop-address=0xa480` listing is retained as `sdp-frc-pixel-handler.objdump.txt`; it agrees on the handler branches, register constants and call relocations.

## Registration and route, with the indirect edges resolved

The prior [video measurement report](video-measurement.md) established rosem's `tztv_frc_tcon_ext_cmd(0x400,payload,size)` calls. This audit also retained the corresponding public registrations: `tztv_frc_tcon_api` has callback storage `tztv_frc_tcon_ext_cmd` in `.bss+0x3d8`; bridge probe at `.text.unlikely+0x3204..0x3214` writes relocated `_tztv_frc_tcon_ext_cmd` into that imported storage. Public RGB wrappers use the table at API `.bss+0x618`, slots `+0x290/+0x298/+0x2a0`; rosem's `.init.text` installs its condition/set/read methods and calls `map_frc_functions` at `+0x3c8`. That API mapper stores the table pointer at `.bss+0x618`.

For ordinary bridge probe initialization, `_tztv_get_chip_type` (`.text.unlikely+0x8c`) writes 14 into bridge BSS `+0x30`, passed by probe at `+0x2ec4..0x2ed4`. The bridge `_tztv_frc_tcon_ext_cmd` (`.text+0x2d78`, size `0x160`) selects `sdp_display_ex_proc` for chip 14; other compiled chip values can select NVT/MTK names. It resolves via `find_symbol`, caches the callback at BSS `+0x80`, and calls it at `+0x2e10` preserving operation/buffer/length. The exact SDP string is `.rodata.str1.8+0x2438`. Cold lookup failure returns -1; initialized-null callback returns zero without forwarding. A first successful initialization operation -1 skips forwarding, but -1 on an initialized callback forwards. No such operation was invoked here.

The same-file SDP initializers close the subsequent indirections:

| Edge | Retained instruction/initialization evidence |
| --- | --- |
| `sdp_display_ex_proc` → `dispay_coordinator_ex_proc` | `.text+0x1efd0`, call relocation |
| coordinator → object slot `+0x48` | `.text+0x2206c..0x22074`, loads pointer at BSS `+0x8cc10` |
| coordinator pointer → output singleton | `.text.unlikely+0x1440` calls `disp_coord_set(...,4)`; `.text+0x21fe0` selects `get_instance_of_display_output_coordinator` at `+0x22ea8` |
| output singleton → `display_output_do_process` | `display_output_coordinator_Init` at `+0x22818`; relocation for function `+0x22d08` in x6 and `stp x7,x6,[x19,#0x40]` at `+0x22878` install slot `+0x48` |
| operation 0x400 → FRC device slot `+0x30` | output `+0x22d48` treats only operation 1 specially; `+0x22d50..0x22d6c` calls getter slot `+0x70`, then returned device slot `+0x30` |
| getter → FRC device singleton | `get_display_device_frc` `+0x22608` loads BSS `+0x8cda8`, initialized at output `+0x22890..0x22894` with `get_instance_of_abstract_display_device_frc` |
| FRC device slot → `dd_frc_send_trig_bypass` | `display_device_frc_Init` `.text.unlikely+0x1c28..0x1c78` installs `.text+0x25ac0` in slot `+0x30` |
| bypass callback → `sdp_frc_ex_proc` | only 0x600/0x601 are special; operation 0x400 calls it at `.text+0x25afc` |
| exact 0x400 dispatch | `.text+0x2798 cmp w20,#0x400`; `+0x279c b.eq +0x28e8`; `+0x28f0` relocation calls `sdp_frc_dev_cust_get_pixel_measure` |

These are conditional stock table relationships, not a capture of current callback addresses. `sdp_frc_ex_proc` additionally has initialized-state, optional callback, completion, runtime-power, mutex and policy gates. Its optional callback at `+0x2288..0x2298` can return early with saved result zero. The command-0x400 branch passes only instance and payload into the handler and does not check length against suboperation size. The traced rosem caller supplies fixed lengths 28,16,20.

## Exact downstream payload behavior

Handler `sdp_frc_dev_cust_get_pixel_measure` is `.text+0xa0b0`, size `0x3d0`. It rejects null payload, unknown suboperation and invalid slot/coordinate with -22. The dispatch compares payload word 0 against 2,3,1 at `+0xa138..0xa14c`.

**Suboperation 1 (condition)** copies 24 bytes from `.data+0xf88` into request `+4..+27` at `+0xa1b4..0xa1cc`. On-disk words are `2,16,16,20,3840,2160`. If instance `+0x1a0 == 5`, `+0xa344..0xa34c` stores 1920×1080 into the shared condition's last two fields. If instance `+0x2c0 == 60`, `+0xa334..0xa33c` doubles the **stored** delay; this is a persistent update in the examined body, with no reset/cap in that body. Repeated direct condition dispatch in that state could double it repeatedly. The upstream rosem condition-cache path can suppress repeated downstream calls, so this is not proof of repeated target doubling. No sampler register is read for condition and no fresh acquisition is triggered.

**Suboperation 2 (set)** consumes `{2,slot,x,y}`. At `+0xa27c..0xa280`, unsigned `slot > 1` fails, including negative signed representations. X must have its sign bit clear (`+0xa284`). The combined compare at `+0xa290..0xa2a0` requires y nonnegative and rejects `full_width < x`; `+0xa2a4..0xa2ac` rejects `full_height < y`. Equality passes. Accepted input writes three registers in this order, then returns zero:

| Slot | Control written with 4 | X written with x | Y written with y |
| --- | --- | --- | --- |
| 0 | aperture `+0x22190` | `+0x22194` | `+0x22198` |
| 1 | aperture `+0x221a0` | `+0x221a4` | `+0x221a8` |

Writes occur via `wrap_write` calls `+0xa2c0/+0xa2d4/+0xa2e8`. The code does not expose the meaning of control value 4. No delay, poll, completion wait, register readback or accepted-frame marker follows these writes in this handler. The three writes are serialized against other extension calls by higher locks, but hardware frame timing and ownership across separate set/read calls are not established.

**Suboperation 3 (read)** consumes `{3,slot,...}`. It first reads `aperture+0x22188` at `+0xa1f0`, **before** validating slot. Thus an invalid slot still causes this register read if dispatch reached the handler. Unsigned `slot > 1` fails at `+0xa1f8..0xa1fc`. It then reads R/G/B at these offsets and stores them at payload `+8/+12/+16`:

| Slot | R | G | B |
| --- | --- | --- | --- |
| 0 | `+0x221b4` | `+0x221ac` | `+0x221b0` |
| 1 | `+0x221f0` | `+0x221e8` | `+0x221ec` |

Calls at `+0xa210/+0xa224/+0xa238` perform the reads. If the first read at `+0x22188` was zero, `+0xa250..0xa25c` masks each color with `0x3ff`; otherwise `+0xa248 → +0xa324` returns the raw words. No recovered register specification establishes the semantic name of `+0x22188`, so it is called a normalization selector here, not “done” or “fresh.” Both cases normally return zero.

The downstream request has **only three color words**. Rosem initializes the separate caller LowInput/status word from its software flags at `.text+0x6a54..0x6a8c`. On successful downstream return, `+0x6ad8..0x6ae4` copies slot/R/G/B from its local request back to caller offsets 0..15 while preserving LowInput at caller `+16`. `libave` then copies R/G/B/LowInput as the previously proved 16-byte caller output. That fourth output is not a hardware acquisition acknowledgment.

## Concrete MMIO endpoint and its limits

`wrap_read` `.text+0xce48` loads instance `+0x138`, adds the unsigned register offset and calls `ft_read`. `wrap_write` `.text+0xcdb0` performs the same base/offset operation and calls `ft_write`. `ft_read`/`ft_write` dispatch through `.data+0x21650` (`devio_access`), table slots `+0x18/+8`.

The on-disk relocation at `.data+0x21650` selects `allowed_access` at `+0x21678`; its `+8` relocation selects `__devio_write` `.text+0x1e680`, and its `+0x18` relocation selects `__devio_read` `.text+0x1e6d8`. These reduce to barrier plus `str w1,[x0]`, and `ldr w0,[x0]` plus barrier respectively. There is no Linux I2C transaction or message-box submission on this leg.

The mapping is also recoverable. `sdp_frc_resource_init` at `.text+0x1c30` calls `platform_get_resource_byname(...,0x200,"frc-reg")` at `+0x1e10`, calls `devm_ioremap_resource` at `+0x1e2c`, and stores its result into exactly instance `+0x138` at `+0x1e30`. The resource string is `.rodata.str1.8+0x1260`. The retained `soc/sdp_frc` DT files identify compatible `samsung,sdp-frc`, reg name `frc-reg`, and big-endian resource cells **`0x00b90000,0x0005f000`**. Every recovered sampler register offset fits that span. This provides the actual retained driver/resource endpoint rather than a guessed controller name. Parent bus `ranges`/cell metadata was not retained in the reviewed subtree; this audit therefore does not independently certify a final CPU physical translation or current mapped base. It supplies no direct-MMIO invocation.

`devio_access_disable` `.text+0x1e710` changes the pointer to adjacent `dummy_access` `.data+0x21658`; `devio_access_enable` `+0x1e728` restores allowed access. Dummy read `.text.unlikely+0x7d4` logs and returns zero; dummy write `.text.unlikely+0x82c` only logs. With dummy access, suboperation 3 can read selector zero and three zero colors and still return zero. No current value or complete writer census of `devio_access` was acquired.

## External-QDF Pre-PD boundary and diagnostic consequence

The [retained identity-boundary audit](../../panel-idle-20261026/tcon-research/qd-rt-controller-identity-boundary.md) establishes the separate external-QDF status route through adapter5/address0x76 and distinguishes it from internal SDP/RHEA shared-memory identity. Command0x400 now closes to a third concrete *function* within the same host SDP/FRC stack: the local MMIO sampler. It does not become an external-QDF firmware command merely because the public callback is named `frc_tcon_ext_cmd`.

The reviewed 0x400 branch and handler provide no pointer, write, DMA descriptor, address translation or transport carrying these colors into `[0x584109a4,0x58410aa4)`. A bounded four-module literal census found neither boundary as a four-byte literal in either endian order; that is corroborative only and cannot exclude computed addresses or missing firmware. The positive reason the producer remains open is that this route terminates in host register reads plus caller copies, with no recovered subsequent consumer edge into the external MCU. No shared RT source is inferred from a prefix, shared color vocabulary, or equal black/zero values. The exact selected external controller executable also remains incompletely bound.

The smallest unresolved artifacts for this route are (1) a register specification or matched hardware-source description identifying the tap and `+0x22188`, (2) a demonstrable frame/position freshness contract, and, separately, (3) an actual external-QDF writer/DMA/transport edge for Pre-PD. A few sampler values, without those first two, cannot distinguish decoded-content loss from a downstream blanking/protection state; even qualified changing values would establish activity at this host tap, not physical light or the external protection-table producer.

ForYou/content black with audio alive and Apps-selected stock operation41/mode2 recovery remain the supplied incident context. This analysis neither reproduces those states nor establishes prevention, a protection bypass, or fault causality. No new collector or target experiment was built.
