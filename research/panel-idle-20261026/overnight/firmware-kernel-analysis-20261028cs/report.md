# Decrypted kernel and board DTB findings

The official firmware kernel's declared uImage header and payload are byte-identical to the previously acquired /dev/mmcblk0p6 image. Both CRCs independently pass. The important new board evidence is the decrypted ten-tree DTB bundle: one tree's dtsversion exactly matches the retained runtime command line and positively maps the TCON fault/control GPIO properties to named GPIO controllers and lines.

All analysis was offline. No TV/root/network/device operation, kernel execution, GPIO request, MCU transaction, reset or firmware write occurred. OEM kernel/DTB/disassembly copies and complete decoded trees are confined to private/ (0700; files0600), excluded from public artifacts. Small derived tables below are evidence summaries, not a root-cause finding.

## Kernel identity and appended bytes

| Item | Evidence |
|---|---|
| Original decrypted uImage |11892528 bytes; SHA256131aa441564f1bd1db019f5284c6f115e1e667e3a7a570407389633105209350|
| Header CRC |stored/computed0x6f63cd7c; magic0x27051956|
| Declared payload |offset64,11786752 bytes; data CRC stored/computed0x9ed20a65|
| Payload SHA256 |77b6070c12a53f2b7ede3b7c503e242759e22dbaef2d12cc91b556416fed455d|
| Header+declared payload SHA256 |a8ded6b0975ac7097d3e285e31b4554f0b7ed68b70b09a477a0f145f1c45ba20; exact previous kernel-uImage.bin equality|
| Header timestamp/name/load/entry |2026-07-01T16:53:03Z; Linux-5.4.261;0x40008000/0x40008000|
| Payload banner |Image offset0x7f0098; Linux5.4.261, abuild@A2001DPG, GCC9.2.0, #1 SMP PREEMPT,2026-07-01T16:51:36Z|

The image interpretation is specifically ARM64: the ARM64 header magic is at payload+0x38. The image remains raw, without an original vmlinux/debug section table. The ELF at0x7f7000 is an embedded AArch64 ET_DYN with __kernel_clock_gettime/__kernel_gettimeofday names, compatible with a vDSO rather than full vmlinux. No IKCFG_ST/IKCFG_ED or CONFIG_IKCONFIG marker was found. No full kallsyms table was recovered; absence of its literal names is not proof that compressed internal symbol data cannot exist.

The existing9379-entry PREL32 export index was revalidated record-by-record against the new payload (relative target, name and zero namespace). Existing tracepoint/GPIO/runtime-PM analysis therefore remains attached to exact bytes; this acquisition adds no different kernel functions or runtime addresses. Retained runtime metadata gives kernel5.4.261/build T-RSMFAKUC-0090-REL-202607141953 and a paired active-root slot, but executing kernel text was not hashed. /proc/kallsyms and /proc/config.gz were absent in the retained probe sample. Module ABI/signature and observer deployment gaps remain as documented previously.

The105712 extra bytes start at uImage offset11786816 (outside the uImage data CRC scope). SHA2561fd6b1e91c3aae312a0ab6e8dd8089777feba60d06f3f3b4c17f3e338f226861. The first7696 bytes have entropy7.964bits/byte, followed at absolute0xb3f850 by6126 repetitions of one exact16-byte block. No bounded FDT/ELF/gzip/XZ/UEP/config signature was found there. This is opaque appended material, not identified DTB/config or a proven signature/encryption scheme. The authenticated original-item CRC covers the whole original section separately; it does not explain this material's inner purpose.

## Board selection and exact DTB scope

DTB source: firmware-extracted-20261028/dtb.bin,1564672 bytes, SHA2565021c20fba8b6b04303faf5b02a8132071e94b6e834498878b895bf9e0a00396. Ten valid version17 FDTs begin at i*0x15000. Each tree fits inside its86016-byte slot, with all bytes between its total_size and the next slot zero. The file also has material beyond the ten slots; no additional FDT magic was found. These extra bytes were not interpreted as a tree.

The selectors are13781814_0_rosem-2.75G-builtin; _1_rosem-2.75G-oc; _2_rosem-2.75G-monitor; _3_rosem-3.0G-builtin; _4_rosem-3.0G-woc; _5_rosem-3.0G-monitor; _6_rosem-4.0G-builtin; _7_rosem-4.0G-oc; _8_rosem-2.75G-builtin-RGB; _9_rosem-4.0G-builtin-RGB. All roots identify samsung,sdp-rosem. Tree1 (bundle offset0x15000,total_size70752,SHA2562a59b19dd734081033ce37cc44905f5f42b04b6e2c9ee0981e43ae5f68b344c0) contains exactly the retained runtime dtsversion13781814_1_rosem-2.75G-oc in /chosen/bootargs.

Tree1 is the best source-backed candidate, not proof of the complete live tree: its default root=/dev/mmcblk0p18, console=ttyS0 and rs232=0 differ from the retained runtime root=/dev/mmcblk0p19, console=ttyS3 and rs232=1. Boot configuration patches are therefore positively apparent. Firmware tree properties below are not claimed to have been read live. In particular, using tree0's GPIO phandles would give different wiring.

## Candidate board TCON GPIO bindings

All offsets are absolute within dtb.bin and point to the property's value bytes. Each phandle resolves to a gpio-controller node with #gpio-cells=2. Line and raw flags are the following cells; no global Linux GPIO number or electrical assertion polarity is inferred.

| /tztv_frc_tcon property | Source offset | Controller | Line | Raw flags |
|---|---:|---|---:|---:|
|samsung,sw-pvcc|0x241d4|/soc/pinctrl/gpio18|0|1|
|samsung,tcon-i2c-en|0x241ec|/soc/pinctrl/gpio32|3|0|
|samsung,tcon_pmic_fault|0x24204|/soc/pinctrl/gpio15|1|0|
|samsung,err_det|0x2421c|/soc/pinctrl/gpio15|5|0|
|samsung,vdd_det|0x24234|/soc/pinctrl/gpio15|6|0|
|samsung,err_det_w|0x2424c|/soc/pinctrl/gpio16|1|0|
|samsung,s_done|0x24264|/soc/pinctrl/gpio16|0|0|
|samsung,qsmen|0x2427c|/soc/pinctrl/gpio22|6|0|
|samsung,ac_det|0x24294|/soc/micom-gpio/gpio_mc3|1|0|
|samsung,el_vdd|0x242ac|/soc/micom-gpio/gpio_mc3|7|0|
|samsung,tcon_on|0x242c4|/soc/micom-gpio/gpio_mc3|5|0|
|samsung,sync_done|0x242dc|/soc/pinctrl/gpio15|7|0|
|samsung,ffc_cable_check|0x242f4|/soc/pinctrl/gpio18|4|0|
|samsung,tcon_dpc|0x2430c|/soc/micom-gpio/gpio_mc4|3|0|

/tztv_micom separately maps sw_inverter_gpio to gpio_mc4.5 at0x24470, and dongle_en_gpio to gpio_mc4.4 at0x24488. The micom GPIO provider declares15 banks/index-base400; a bank-to-global-number formula still requires exact driver qualification. The existing ERR_DET ioctl reconstruction consumes samsung,err_det, so the new tree supplies a concrete static wiring endpoint for that existing provider path. Its request/direction/read/free side effects and power/debug ambiguities remain unchanged; this does not authorize treating that getter as passive.

## MMIO and MCU/logging distinctions

/soc has one address/size cell and an identity ranges mapping into the root's two-cell address space. Tree1 /soc/sdp_tcon reg values at0x1e00c pair with reg-names at0x1e050:

| Named resource | DT bus/CPU address | Extent |
|---|---:|---:|
|tcon-bif-reg|0x8d0000|0x2d0|
|tcon-reg|0x850000|0x4000|
|tcon-conf|0x9d0620|0xc|
|msgbox-rx|0x9d0400|0x44|
|msgbox-tx|0x9d0480|0x44|
|tcon_indirect_async|0x9d04d4|0x8|
|vx1-reg|0x8f0000|0x5400|

This TCON node has interrupts cells[0,142,0]. The separate /soc/msgbox (samsung,sdp-messagebox,reg at0x1ac64) is0x9c0400/0x100 with interrupts[0,3,0]; /soc/mcctrl (samsung,sdp-micom-ctrl,reg at0x1acd4) is0x9c0500/0x100 with interrupts[0,4,0]. They are distinct from the TCON's msgbox resource ranges. Their presence does not identify the external OLED controller protocol or make an MCU transaction a TCON read.

/chosen/samsung,sdp-micom-gpr at0x15104 describes0x9c12c0 with bootprog+0x18, logbufaddr+0x38, logbufsize+0x3c and bootmode+0x04. This is a static boot/logging descriptor, not a demonstrated host-readable current MCU log. No direct register access was attempted. The dummy_panel timing is1920x1080 with zero clock and zero porches, so it is not evidence of the77-inch panel's actual operating timing. No explicit panel regulator/power-domain node was found by the bounded relevant-node inspection.

Two additional bounded exact-image observations, useful to keep future telemetry honest:

- vlog_write at Image0x5c2f28 and vlog_print at0x5c2f68 load the ops pointer from Image-BSS offset0xd8c4a0, then callback slot0; null pointers return zero. vlog_print formats at most140bytes through vsnprintf before dispatch. vlog_set_ops at0x7dced4 writes that global pointer and prints a marker. It is a mutating routing setter, not passive logger discovery. Binding its existing owner is the next static step; no live pointer/ownership is established.
- sdp_mc_ctrl_syscall_get_version at0x5baab0 constructs a message, calls sdp_mc_ctrl_send_nonblcok at0x5bab38, then waits for completion. Its name does not imply a cached passive getter. The DT compatible positively identifies the block as micom control; external panel-MCU equivalence remains unproven. No such call was made.

All Image offsets above are file/artificial-view offsets, not usable live kernel virtual addresses. DT physical resource descriptions do not establish a permitted read width, safe access semantics or a mapped host interface.

## Practical handoff

The strongest new fact is a source-bound candidate board wiring map: ERR_DET/PMIC/VDD/sync fault inputs share main GPIO bank15, while TCON power/ELVDD/AC signals use micom bank3. A future independently qualified live-tree identity comparison can determine whether those same properties survived boot patching; existing exact module code can then resolve the corresponding provider registration semantics. Nothing here establishes a content-triggered root cause, current electrical fault or emitted light.

image-validation.json, appended-analysis.json and dtb-summary.json retain numeric/hash/offset evidence. fdt_bundle.py parses bounded headers/reservations/structure/strings and writes complete OEM trees only under private/. Its eight host tests pass, including independent synthetic offset/value fixtures, malformed bounds/tokens, and the pinned actual tree1 selector/ERR_DET property. Private listings cover only the selected kernel interfaces; no broad symbol-analysis replay was needed.
