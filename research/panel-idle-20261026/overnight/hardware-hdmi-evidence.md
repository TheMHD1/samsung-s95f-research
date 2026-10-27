# Hardware and HDMI investigation, 2026-10-26

This is an evidence map, not a verified schematic or a repair. Exact firmware/build and binary hashes are recorded in the adjacent manifests. All GPIO numbers below are Linux software identifiers, not connector pins. No GPIO was requested, driven, or directly sampled for this work; no connector was disturbed.

## Owner's two failure classes

The persistent native-menu failure has owner-confirmed physically black screenshots B0/B1 whose software images remain rich and changing. The owner reports sparse For You/Live is especially likely to trigger it; a populated Apps page helps prevent entry, but blind navigation back after black does not reliably recover it. Settings over a full page can cause repeated flicker. Once black for roughly three seconds, it usually remains black. This is a reported tendency, not a measured timer.

Ugoos movies usually work but occasionally suffer one or two brief picture losses with an audio pause, then recover; Live TV is worse. No such Ugoos incident was captured. The historically confirmed chain is Ugoos → JBL Bar 1300X HDMI input → JBL HDMI output → Samsung. JBL audio need not traverse the TV. Source playback, repeater/HDCP/link changes and downstream panel loss must remain separate possibilities until synchronized evidence exists.

The impact damage is an irregular black spot no larger than the owner’s thumb (latest size clarification), with a one-pixel-wide vertical black line above it. It predates root. No software method to repair that physical damage has been established, and the full-screen blackout has not been proved to originate at that spot.

## Manufacturer board topology

Samsung's [Canadian support page for QN77S95FAFXZC](https://www.samsung.com/ca/support/model/QN77S95FAFXZC/) links the [S95F-family repair guide](https://org.downloadcenter.samsung.com/downloadfile/ContentsFile.aspx?CDSite=UNI_CA&OriginYN=N&ModelType=N&ModelName=QN77S95FAF&CttFileID=11121872&CDCttType=EU&VPath=EU%2F202511%2F20251120162206263%2F77.Repair_Guide_S95FH_QNxxS95FDFXxx_Ver1.0.pdf), archived here as `samsung-s95f-repair-guide.pdf` and extracted text. Its cover says Basic Model QN55S95FAFXZC and Applicable Model QN**S95FD****. This makes it S95F-family and 77-inch-relevant topology evidence, not an unequivocally exact-model schematic for this unit.

- PDF page17, step10 labels separate **TV Main**, **T-con board**, and **IoT Hub** inside the panel assembly.
- Page18, step12 includes a separate **DCDC board only for 77-inch**.
- Page24, step19 identifies **OC Main** inside One Connect, separate from its SMPS.

The photographs show board-level cabling but supply no usable pin numbers, signal voltage specifications, fault-code definitions, or full schematics. In particular, the guide does not justify assuming all processing is in One Connect. Exact placement of the running SoC, FRC and individual firmware blocks remains unverified. Replacement-board factory provisioning instructions are not a blackout reset and were not executed. Rendered evidence is in `repair-board-17.png`, `repair-board-18.png`, and `repair-oc-board.png`.

```text
Software path established on the running system:
  CSFS/NUI → Enlightenment/HWC → DRM/DP/FRC → VX1/TCON → OLED emission

Physical board names established by family guide:
  One Connect: OC Main + SMPS ── external cable ── panel assembly
  Panel assembly: TV Main + T-con + 77-inch DCDC + IoT Hub

Mapping every software block to a particular physical board is unresolved.
```

## Exact device tree and stock driver control lines

`display-devicetree.tar`, `gpio-devicetree.tar`, their JSON transport records, `gpio-chip-map.json`, and `gpio-control-map.json` retain the actual firmware properties, phandles and Linux bank ranges. Addresses and GPIOs were resolved from that data rather than assumed from bank names.

| DT name | Linux GPIO | Interpretation limit |
| --- | ---: | --- |
| sw-pvcc |144| DT active-low flag1; stock raw setters do not automatically apply DT polarity |
| ffc_cable_check |148| presence in DT is not proof this model reads it |
| tcon_on |429| output control candidate; do not toggle |
| tcon-i2c-en |259| transport enable; do not toggle |
| err_det |125| stock getter requests/directions/reads/frees line |
| s_done |128| same non-passive getter lifecycle |
| vdd_det |126| same non-passive getter lifecycle |
| err_det_w |129| wiring metadata only |
| el_vdd |431| output control candidate |
| tcon_dpc |435| wiring metadata only |
| qsmen |182| model-gated output control |
| sync_done |127| stock getter requests/directions/reads/frees line |
| tcon_pmic_fault |121| stock getter requests/directions/reads/frees line |
| ac_det |425| model-gated control |

The GPIO272 polls seen in the passive trace resolve to GPIO34.0, not any of these TCON signals. Stock fault getters are not harmless external observers: their request/direction/free sequence can contend with or reconfigure a line. Their exact call chains are in `../tcon-research/overnight-gpio-dt-driver-chain.md`. No private getter was called. I²C bus5 is the DT controller at 0x550500 with 400kHz maximum; those are software bus parameters, not a connector pinout.

## Native output/link observations

Visible Apps and owner-confirmed black B0/B1 retain the same sampled `sdp_jp_get_clock_cable_detection` values: clk_det 0xeeeeeeee, cable_det 0xf873dd17, val0x4f0. B1 also records VX1 lock1 at uptime7400.632. This does not show an One Connect clock/cable transition in those samples, but neither sampled link lock nor vblank proves OLED emission. The later five-second passive trace is only a pipeline baseline: physical state during that exact interval was not reconfirmed.

Repeated HDMI-switch Current_Src0x80001 Disconnect messages during native Apps/Live are background source polling, not evidence the Ugoos disconnected. No timed Ugoos event has been associated with HPD, TMDS/FRL validity, SCDC changes, re-acquisition, HDCP errors, receive-error counters, or audio-clock drift.

## Exact HDMI status handlers and rejected getter paths

The SHA-verified `sdp_hdmi.ko` defines debugfs `lock` handler0xa9fd0 and `tx_en_sts` handler0xa9e08. These read cached switch/OCM state under a runtime-use wrapper, pairing use/disuse on successful reads. The native-source baseline in `hdmi-cache-baseline.json` reports lock0 and TX0; an inactive HDMI receive path during TV Plus is not fault evidence.

Do **not** poll `hdmi/crc`. Handler0xa9e70 is a cached status enum, not a frame CRC. It returns EINVAL before reading status when `(current_input & 0xff)>5`, or if runtime-use fails. For HDMI0–3, lock0 gives2; otherwise cached field+0x23ac nonzero or counter+0x20e8<=10 gives1, else0. Inputs4–5 give3. Semantic labels beyond this code have not been recovered. More seriously, the successful-use/native-source EINVAL branch at0xa9ea8→0xa9f28 skips the disuse call made by normal branches at0xa9ed8. One baseline read was performed before discovering this. The thin wrappers at0xaa808/0xaa828 call imported sdp_runtime_pm_tryuse/disuse; the implementation is not in the acquired modules. The subsequent TX getter succeeded, ruling out an exclusive gate left blocked. The kernel shows an increment/decrement busy count; whether this one EINVAL call incremented it remains unknown because tryuse failure returns the same error and the live bypass/count was not observed. This read occurred at uptime10224, after the owner-confirmed incidents at7206–7424, so it cannot explain those incidents. It is an unmatched successful-use path/possible retained state, not a proven reference leak or blackout cause. Do not attempt manual balancing or repeat it.

`tztv_hdmi_soc_switch_get_blink_err_info` at0xa0e8 returns success without filling output; its API caller then copies stack data. `get_no_signal_err_info` variants and `GetTMDSClkStatus` also contain stubs. Apparent blink counters therefore cannot be trusted on this build. External-switch GetLockStatus/GetClockDetect/GetHDCPType call actual inv479x transactions; they are not passive caches and were not polled.

## Next HDMI capture is separate from native-menu capture

`diagnostic-trace.py` is prepared for native Apps versus For You/TCON. It cannot, as written, classify Ugoos/JBL audio-picture pauses. A separate reviewed HDMI session needs:

1. Owner confirmation of the current TV input and physical chain, plus distinct timing of picture loss, JBL audio loss, JBL format changes and whether Ugoos playback time stopped.
2. Before/after lock and TX cache snapshots, no CRC getter; verified cached FRC IRQ-counter deltas from `/sys/kernel/debug/frc/frctest/irq_status` (the earlier assumed top-level path does not exist). FRC irq_status handler0x114b0 formats four BSS u32 counters through getters ME0xc370/PRE0xc3a8/FMT0xc3e0/MC0xc418; it performs no MMIO, runtime-use, notifier or counter clear. Compare deltas modulo2^32; IRQ progress is not physical-light proof.
3. Read-only `/proc/interrupts` mapping before selecting the relevant HDMI IRQ events. Trace only those IRQs, not the whole system.
4. Natural driver logs for HPD, TMDS/FRL validity, SCDC/HDCP/re-acquisition and audio-clock changes, synchronized with Ugoos decoder/kernel/HDMI-TX logs.

DT HDMI cable lines resolve HDMI1→286, HDMI2→285, HDMI3→116, HDMI4→115. `gpio:gpio_value` records software get/set operations, not autonomous electrical edges. Absence of an event cannot establish stable cabling: the driver may use direct register access, IRQs or OCM. No GPIO request/read/drive should be added to compensate for absent trace events.

No HDMI recovery, PM balancing, factory/power setting, firmware patch, calibration, connector change or panel-output action was performed as part of these findings.

## Actual-unit photographs added

Ten owner-supplied images are fingerprinted in `owner-photo-manifest.json`: eight internals/closeups and two screen-damage photographs. Panel label reads CY-AF077FLLV2H; both wide panel ribbons read BN96-60461A REV00. Board/cable roles and uncertain identifiers are recorded separately in `../tcon-research/owner-photo-board-map.md`. The damage images show the patch at the lower edge and a narrow dark line above it while surrounding pixels emit light. Camera moiré/repeating stripes are not additional defect evidence; upload time does not establish current panel state.
