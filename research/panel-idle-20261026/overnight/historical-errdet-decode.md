# Historical TCON ERR DET 0x10: exact-build decode

The historical October12 fault is now decoded further from the owner's matching binaries. This does **not** establish the initiating cause of the current menu blackout: no ERR-DET transition has yet been aligned with its physical onset. Fault/status fields from different messages must not be combined merely because they contain similar numbers.

## Meaning of the returned bitfield

`libave.so.0.1` SHA256 `a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777`, Thumb code start `ave_tcon_qd_err_detect_status`0x268cbc, calls the error-status getter and tests each bit. Existing logs identify QD PRODUCT, so its separate WOLED interpretation is not applicable.

| Bit / mask | Literal Samsung label | Mask/log branch offset |
| --- | --- | --- |
|0 /0x01|EL OCP|0x268d00|
|1 /0x02|EL OCP2|0x268d2c|
|2 /0x04|BLACK OCP|0x268d4a|
|3 /0x08|FFC Connection OCP|0x268d68|
|4 /0x10|**RT Protect**|0x268d86|
|5 /0x20|DSI Protection|0x268da4|
|6 /0x40|AC_DET pin low|0x268dc2|
|7 /0x80|PMIC fault|0x268de0|

The function returns the unmodified status word. Therefore the historical `ERR DET Status:0x10` means bit4, labeled **RT Protect**. No expansion of RT, exact electrical threshold, damaged component, or repair follows from this label. In particular, do not rename it temperature protection, resistance protection or a decoded row-driver condition without further evidence.

## How the word reaches userspace

```text
ave_tcon_get_err_det_status                 libave0x25d164
    ioctl0xc010749f, payload command0x1f
        → QDFTcon_GetErrDetStatus           qdf_tcon0xa000
        → m_read_cmd
        → transmit f3 80 00 00 00 08
        → receive4bytes, reverse byte order, return32-bit word
```

This is a QDF/TCON read transaction or mailbox-style command. The code does not prove it is a directly memory-mapped status register. `QDFTcon_GetErrDetStatus` logs the raw result at0xa06c/0xa074 **before** an optional debug override at0xa0d0. That override would additionally log `ERR DET Status Debug`. The retained historical excerpt contains the raw0x10 line and no corresponding debug line; it is not evidence of debug injection.

Override names are precise: QDF BSS+0x28 is enable `m_err_debug`; +0x11c is GPIO-fault override `m_err_det_debug_status`; +0x120 is returned-status override `m_err_det_status_debug_status`. No override was enabled or written by this investigation.

## Fault GPIO is a separate gate

`_tztv_frc_tcon_read_err_det_status` at module offset0x1af0 calls `gpiod_get_raw_value_cansleep` at0x1bb0. QDF `GetErrDetFault`0x5608 logs the asserted GPIO fault only when that raw value is nonzero; its optional returned-value override happens later. The GPIO is thus a one-bit fault indication. **0x10 is not the GPIO number, raw GPIO value or a recovery reason enum**: it is obtained by the separate TCON status transaction above.

The driver getter's lifecycle can request/direction/read/free a line, so its existence is not an instruction to invoke it externally. Logical DT GPIO125 is documented separately; no new GPIO was requested, driven or polled in this analysis.

## Monitor and historical recovery sequence

`ave_tcon_monitor_ddr_pmic_check_qd_oled` starts0x2695fc. It calls the fault checker at0x269666; an asserted fault leads to status decode at0x2696aa and retries. Its terminal classification calls SetErrorLog(0) at0x269824, corresponding to the QDF message `TCON ERR Detect fault detected`. A separate following branch calls the status decoder again at0x269b20, then power-control(2) at0x269b26. This matches the historical second status query and Reset(2) sequence. SetErrorLog classifies the path; it does not synthesize the0x10 response. More specifically, the monitor’s recovery decision is driven by the asserted fault GPIO: ave_tcon_qd_err_detect_check reduces that raw fault to0 or-1. It ignores the returned status bitfield when deciding retries/reset, including the query immediately before power-control(2). The bit labels are telemetry about the TCON-reported cause. Zeroing or suppressing the status query would not stop this host recovery path; it would only obscure evidence.

This historical event establishes that the vendor monitor saw an asserted fault and the TCON reported RT Protect before recovery. The current owner-confirmed menu incident has valid composition and sampled lock/power flags without an aligned fresh RT-Protect event. Suppressing its logger or monitor would not establish a repair, and no such change was made.

Raw machine-code excerpts are retained alongside this note as `errdet-libave.disasm.txt`, `errdet-qdf.disasm.txt`, and `errdet-gpio.disasm.txt`. Addresses in the ARM library are ELF link VAs/Thumb code starts; kernel-module offsets are section-relative. Matching binary hashes remain in `analysis-input-manifest.json`.
