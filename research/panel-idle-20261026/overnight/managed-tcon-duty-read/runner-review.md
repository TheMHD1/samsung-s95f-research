# Duty-read runner preparation review

Recorded 2026-10-27 UTC. `run-duty-read.py` is dry by default and was locally
exercised only in that mode. Its manifest is separate from the immutable
`build-manifest.json`; it verifies the latter's SHA-256 and the three staged
portable-IL payload digests without modifying that build manifest.

The dry plan accepts no selector, command, setter, or arbitrary target
argument. It pins `/dev/tztv_tcon`, ioctl `0xc010749f`, operation 19 and
selector `0x128`. The strict parser accepts only the fixed
`QD_TCON_DUTY_READ_V1` field inventory, ARM32 ABI values, unchanged command
envelope, one changed output word, successful close, and a value no greater
than 1023. Its output is still classified only as `kernel_output_written`; it
does not infer brightness, emitted light, panel state, transaction completion,
or a fix.

The existing status runner is a lifecycle reference for authenticated guarded
transport, bounded responses, staging/cleanup and deadlines. This preparation
does **not** reuse it to make a target call: no staging, open, ioctl, cleanup,
or target preflight ran. The user has now authorized diagnostic work, so there
is no historical permission hold asserted here.

The missing hard condition is an identified target-supported kernel
firmware-update/flash flag. A quiet process list is not evidence that firmware
is not updating. Live invocation is therefore fail-closed/deferred until that
flag and a concrete lifecycle binding are independently reviewed; no race is
claimed absent. There is no retry or polling implementation.

Local dry validation passed: the plan reports dry mode/no target calls, exactly
three hash-pinned staged payloads, fixed selector/request, and the flash-guard
deferral. Runner SHA-256 is
`1a96f8f64c1750cd623ec3d0a1fb802107d6c13daf0b91495a85f776566aa53a`;
separate runner-manifest SHA-256 is
`d815dca4de6b0e02c7ad636247bed78a33f09afacd23b05aa27a48680efd846a`.
