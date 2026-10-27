# Acquired kernel and Samsung runtime-use mechanism

## Provenance and reproducibility

The owner authorized kernel/machine-code diagnosis. Only reads were made of boot storage. `kernel-image-inventory.json` records the partition table; `kernel-slot-metadata.json` records paired uImage partitions5/6 and current root partition19. The named uImage symlink selects p5, whose first128KiB are zero. Partition6 contains a legacy uImage header plus an uncompressed ARM64 Image.

`pull-kernel-image.py` reads only that known partition, caps the header's payload length at20MiB, validates header CRC and data CRC, and saves host copies. It neither mounts nor writes the partition. Total acquired length11,786,816bytes; payload11,786,752bytes. Payload SHA256:

`77b6070c12a53f2b7ede3b7c503e242759e22dbaef2d12cc91b556416fed455d`

The embedded banner and `/proc/version` in `kernel-running-baseline.json` exactly agree: Linux5.4.261, abuild@A2001DPG, GCC9.2.0, SMP PREEMPT, July1,2026 16:51:36UTC. This is strong matching-image evidence, not a live-text hash or proof no runtime patch exists.

The [upstream vmlinux-to-elf tool](https://github.com/marin-m/vmlinux-to-elf), version1.0 installed only into temporary host analysis storage, could not find kallsyms. Its failure log is retained; no fully symbolized original vmlinux was recovered. No IKCFG_ST/ED markers were found. `recover-kernel-exports.py` instead reconstructs9,379 contiguous namespace-zero PREL32 export records at file offsets0x997ef0–0x9b3688. It checks the payload SHA, handles BSS targets using ARM64 Image's declared in-memory size0xd99000 and distinguishes file-backed targets from BSS. This is an export index, not every internal symbol. `build-kernel-export-view.py` also creates a host-only ELF view using artificial base0 and NOTYPE export symbols, retaining the original payload bytes unchanged. `kernel-export-view-manifest.json` fingerprints it. It is not original vmlinux, a runnable replacement, or a firmware update; original section permissions, internal names, source lines and unwind metadata remain absent. Standard objdump can use it to label exported call targets.

## Exact exported functions

All following addresses are **Image file offsets**, not runtime virtual addresses. Raw machine code is retained in `kernel-runtime-pm.disasm`.

| Export | Offset |
| --- | --- |
| sdp_runtime_pm_disable |0x3fbbd0|
| sdp_runtime_pm_disuse |0x3fbbe8|
| sdp_runtime_pm_tryuse |0x3fbc58|
| sdp_runtime_pm_getdev |0x3fbee8|
| sdp_runtime_pm_init_and_get |0x3fbf10|
| sdp_runtime_pm_init_done_nr |0x3fbfc0|
| sdp_runtime_pm_get |0x3fc040|
| sdp_runtime_pm_put |0x3fc1c0|

Module wrappers `hdmi_rpm_dev_tryuse`0xaa808 and `...disuse`0xaa828 load the cached record pointer from module BSS+0x164c8 and call these imported functions. They are proprietary Samsung bookkeeping helpers, not directly Linux's standard runtime-PM usage counter.

## Actual tryuse/disuse semantics

The recovered code establishes:

```text
tryuse(record):
    if global_bypass: return 0
    if record == NULL: return -EINVAL
    irqflags = raw_spin_lock_irqsave(record + 0x38)
    if record.state_at_0x44 == 0:
        record.busy_at_0x40 += 1
        unlock_irqrestore
        return 0
    update timing/rate-limited diagnostics
    unlock_irqrestore
    return -ENXIO

disuse(record):
    if global_bypass: return 0
    if record == NULL: return -EINVAL
    lock_irqsave(record + 0x38)
    record.busy_at_0x40 -= 1
    unlock_irqrestore
    return 0
```

Disuse has no underflow guard. Lock helpers are resolved exports at0x7e5128/0x7e4598. Failure diagnostics use ktime_get0xa70a0, printk0x7cdc48 and, under a rate/error condition, dump_stack0x7dd920. Tryuse does not resume hardware itself.

`put(name)` shows the busy count's consequence. When the ordinary use count at+0x3c reaches zero, it sets state+0x44 to2, sets timeout policy+0x48 to500, then waits for busy+0x40 to reach zero. It polls every10ms for up to1,000 passes, logs periodically, and calls the suspend callback after either count<=0 or timeout. An unmatched increment can therefore delay that helper-driven suspend by roughly10seconds; it is not an exclusive permanent lock. This is a separate mechanism from the owner's estimated three-second persistent-black threshold. No correlation between them has been demonstrated.

The global bypass byte is at image offset0xc249c8 in zero-initialized BSS. `disable()` stores1. No direct built-in BL/B reference to disable was found, but external modules can call the export, so a static default0 does not establish its live value. There is no recovered stock proc/debugfs observer for the live record count/state. No direct runtime-memory read or write was attempted.

## What the HDMI CRC read did and did not establish

One `hdmi/crc` read at uptime10224 returned EINVAL while native TV was active. The HDMI handler merges two causes into that error: tryuse failed, or tryuse succeeded and source enum>5. The latter branch skips disuse. Thus:

- If global bypass was off and tryuse succeeded, that call retained exactly one proprietary busy reference.
- If tryuse failed, no reference was added; if bypass was active, the successful return was a no-op.
- The following TX getter succeeded, so an exclusive gate was not left blocked.
- No live count is available to determine which case occurred. A speculative disuse can underflow, so none was sent.
- The read happened after all owner-confirmed native blackout captures at uptimes7206–7424. It cannot explain those blackouts, which also predate root. It may affect the timing of a later suspend and must be recorded as a possible observer effect.

Do not repeat that getter, treat EINVAL as a measured HDMI failure, or balance the count by guesswork. No reboot/suspend or PM modification was done to clean this up while the owner was unavailable.

## Actual baseline and IRQ observer

At04:45:57UTC `kernel-running-baseline.json` records the same boot, normal HWC deactive0, AVOC panel mute0/return0, global tracing0, no private instances. Physical emission at that moment was not confirmed. Relevant Linux IRQs are HDMI53/67, FRC80(MC),81(VA),82(PRE),83(FMT). These numbers are boot-specific, not universal identifiers.

An initial proposed `/sys/kernel/debug/frc/irq_status` path did not exist. Metadata lookup found the actual node **`/sys/kernel/debug/frc/frctest/irq_status`**. Its reviewed handler0x114b0 formats four BSS u32 counters without MMIO, runtime-use, notifier, reset or counter clear. At04:47:53, uptime11682.68, the read returned mc0, me700215, pre700218, fmt0. Zero alone is not a failed stage: driver debug labels and physical IRQ names need mode-specific interpretation. Compare modulo2^32 deltas to a visibly working baseline. Counter progress never proves OLED light output.

No kernel image, module, runtime code, factory state, power policy, calibration or panel rail was changed during this analysis.
