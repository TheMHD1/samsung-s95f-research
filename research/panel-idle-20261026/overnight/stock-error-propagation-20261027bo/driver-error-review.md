# BI stock `F3:01` error propagation

Recorded 2026-10-27 UTC. This is a bounded, offline review of retained BI and
BH traces and already-copied stock modules. It made no TV, root, network,
USB, I2C, UI, reset, power, or controller request. It does not relax BI's
existing hard stop, retroqualify the rejected recorder, or propose a retry,
patch, or bypass.

## Result

BI's `ret=-6` was one incomplete **post-write status/checksum read**, not the
preceding setting write. Stock `qdf_tcon.ko` automatically performed its one
post-write re-read. That re-read completed, returned the exact checksum for
the already-sent setting, and the replay advanced to the next setting.

This establishes recovery of this individual stock transaction at the
driver's checksum protocol boundary. It does **not** establish physical panel
application, identify `-6` as a controller firmware fault, or cure the BI
recorder's independent export-integrity failure. The original BI decision to
withhold the delayed read remains correct under its predeclared complete-trace
contract.

## Pinned inputs

| input | SHA-256 |
| --- | --- |
| BI trace, `owner-paired-bi-20261027.onset/trace` | `c2eff8adb06b852f4fc612f6c338967eb5a127d08672e5526331b43088689801` |
| BH trace, `owner-paired-bh-20261027.onset/trace` | `428152c29a5887d5a025cb37c5249f575e1c84e1bdd1dcfbd6c4ce84ca94b51e` |
| copied `qdf_tcon.ko` | `97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63` |
| copied `tztv_frc_tcon.ko` | `aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd` |
| copied `tztv_frc_tcon_api.ko` | `3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6` |
| relocation-aware QDF transport disassembly | `f4ee158c1e2e410fb79520c282e8b04c16c672ec964d2738f6d28170e849f13b` |

The trace line numbers below refer to those exact trace bytes. The copied
module hashes also equal the identities checked by the BI stock helper.

## Exact BI transaction

PID 31720 performs the following sequence at BI trace lines 28045--28079:

```text
157462.985994  F3:00:000330, payload 000000c0
157462.986311  setting transfer ret=2
157462.986311  F3:01 read begins
157462.987034  no reply row; transfer ret=-6
157463.000065  F3:01 read begins again
157463.000430  reply 0000e604; transfer ret=2
157463.000432  F3:01 read begins
157463.000780  reply 0000e604; transfer ret=2
157463.000781  F3:00:000334, payload 000000c0
```

The first failed `F3:01` immediately follows the successful two-message
setting transfer. It is therefore the post-write check for raw setting
`F3:00:000330`, not a pre-read failure before `F3:00:000334`. The re-read at
`157463.000065` is the automatic post-write retry. The next read at
`157463.000432` is the ordinary pre-read for the following setting.

The returned byte is not merely plausible. QDF computes an eight-bit sum over
the six command bytes and four payload bytes at `.text+0xbd38..0xbd88`:

```text
(f3 + 00 + 00 + 00 + 03 + 30 + 00 + 00 + 00 + c0) & ff = e6
```

The retry reply is `00 00 e6 04`; QDF's post-write comparison loads the
selected response byte at `.text+0xbd98` and compares it with that local sum at
`.text+0xbda4`. Thus the retained retry reply supplies the exact expected
`e6`. The subsequent advance to `000334` is consistent with completion of the
`000330` stock send rather than an unbounded retry or repetition of its
setting write.

The roughly 13 ms wall-time gap from failed result to retry header does not
change the branch identity. The static path requests a 1 ms sleep; scheduling
and unrelated processes are visible in the interval, so the trace does not
justify treating 13 ms as a protocol timeout constant.

## Driver path and retry handling

The copied QDF function `m_send_cmd_with_lock.constprop.0` begins at
`.text+0xbba0`. Its relevant post-write path is:

```text
bd8c  call m_read_cmd_no_lock(F3:01)
bd98  load selected response byte
bda4  compare computed checksum with response byte
bdb0  if first mismatch, branch to retry setup
bdc4  if checksum matches, require read return == 0 for immediate success
bdcc  mark one post-read attempt
bdd0  ft_msleep(1)
bdd4  branch back to bd8c
be28..be4c  return saved send result
```

This means the retry is not a special interpretation of numeric `-6`. A
first post-read with a mismatching/stale response retries; a checksum match
with a nonzero read return also reaches the same one-time retry. In
`m_read_cmd_no_lock` at `.text+0xb9b8..0xb9e4`, the common-I2C callback return
is retained in `w19`; only a zero return copies the received word to the
caller's response buffer. The trace's absent reply and `ret=-6` therefore
describe an incomplete Linux I2C read transaction. This review deliberately
does not assign an errno name or a controller-internal cause to `-6`.

On the retry, the trace has a reply and Linux `i2c_result ret=2`; the QDF
common wrapper reports success to `m_read_cmd_no_lock`, and the selected `e6`
matches the locally calculated checksum. This is the positive edge that the
original lifecycle review did not attempt to establish.

## BH same-phase comparison

BH PID 9841 executes the same raw setting phase at trace lines 28244--28255:

```text
156883.119901  F3:00:000330, payload 000000c0
156883.120215  setting transfer ret=2
156883.120215  F3:01 post-read
156883.120570  reply 0000e604; ret=2
156883.120571  F3:01 next pre-read
156883.120920  reply 0000e604; ret=2
156883.120921  F3:00:000334, payload 000000c0
```

BH therefore has two successful `F3:01` reads between the two setting writes:
the post-read of `000330`, then the pre-read of `000334`. BI has three because
its first post-read was incomplete and the stock retry inserted one additional
`F3:01`. Apart from that inserted retry, BI rejoins the exact BH command/reply
shape, including checksum `e6` and the next raw setting. This is a stronger
comparison than merely noting that most BI transfers returned 2.

## Why MODE2 can report zero

There are two independent reasons that the userspace operation can report
zero without certifying every lower transfer:

1. For this exact `000330` send, the retained evidence shows the one-time
   post-read retry eventually obtained the expected checksum. The local send
   could therefore complete successfully despite the first incomplete read.
2. More generally, `m_register_recovery_noFramerate` calls
   `m_send_cmd_with_lock` from its generic replay loop at `.text+0xf880`,
   overwrites/discards each individual return, and returns zero unconditionally
   at `.text+0xf8f8..0xf90c`. `m_set_power_control(1)` invokes that replay at
   `.text+0x11934` and does not aggregate its return. The public MODE2 wrapper
   at `.text+0x11c48` returns the bitwise OR of its off and on power-control
   results, not a transaction-by-transaction replay verdict.

The copied `tztv_frc_tcon_api.ko` operation-41 dispatcher at `.text+0xed80`
loads callback slot `+0x458` and preserves the callback's integer return. QDF
installs `QDFTcon_SetQdTconPowerControl` into that slot. Consequently, the API
and ioctl layers can faithfully return QDF's zero while the lower replay has
either recovered a transient transfer or discarded another per-command
failure. Zero is an API return, not a complete I2C transcript certificate.

## Consequence boundary

The evidence now supports all of these narrow statements:

- the `F3:00:000330` setting write itself completed at the Linux I2C boundary;
- its first post-write `F3:01` check did not complete and returned `-6`;
- stock code retried that check once;
- the retry returned the exact expected command checksum;
- replay then advanced to the next setting;
- BH's successful path has the same sequence without the inserted retry.

It does **not** prove that the controller applied the setting to physical
output, explain why the first I2C transaction failed, or establish that no
controller reset/state loss occurred outside this bounded exchange. A matching
vendor checksum is a stronger driver-protocol observation than an ioctl zero,
but it remains below physical light/panel behavior.

To judge physical consequence rather than transport recovery would require a
time-aligned physical observation or a positively documented controller status
whose semantics include application of raw setting `000330`. Neither is in
the retained BI transaction. Controller/kernel diagnostic logging around the
same timestamp could help distinguish bus/controller causes, but absence of
such a log would not itself prove health.

Finally, BI's action trace still contains an explicit incomplete transfer and
its recorder still has the independent forced-vlog/export failure documented
by the lifecycle review. The AU eligibility rule required a complete action
replay, not merely evidence that stock code later recovered. Therefore this
new propagation result narrows the likely impact of `ret=-6`; it does not
change BI's rejected status, authorize a delayed read, or justify any retry.
