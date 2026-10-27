# Fixed read-only eMMC sector probe

This derivative requests only target0x203, address0, length512. Header:
`030200000000000000020000`. The corrected packaged parser selects operation3,
mode1 and the eMMC-sector read leaf. The adjacent write operation needs0x204
and is not selected. Both alignment checks pass and the512-byte buffer bound
fits the recovered scratch region and minimum chunk cap.

All prior ARM32 ABI/device/boot/FD/interface guards, one OUT/one IN, two-second
transfer timeout and finally cleanup remain. Default invocation accesses no
device.26 injected cases and four host checks pass. No retry, reset, restore,
protection change or payload/NV write is implemented.

The actual request completed OUT12/IN512, release/close0, Accepted=true and
verified stage removal. The independently audited reply has build tag241205A
and differs in13 bytes from the selected package's241230A header. Both retain
the same structural magic and mcu_ata/compiler/builder labels. See the raw
sector and audit in `../rt-onset-memory-20261027c/emmc-sector-read-once`.

The firmware ignores the eMMC leaf's return before scheduling USB IN.
Accepted therefore proves exact USB transport and cleanup, not fresh successful
storage acquisition or active executable identity. A stale buffer, another
stored object/slot or genuinely different installed content remains possible.
This result requires a larger separately verified backup/fingerprint before
considering any patch based on the selected package's absolute offsets.
