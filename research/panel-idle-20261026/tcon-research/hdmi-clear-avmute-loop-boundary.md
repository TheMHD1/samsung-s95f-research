# HDMI `CLEAR_AVMUTE` loop boundary

Date: 2026-10-27 UTC  
Scope: offline analysis of retained binaries and already acquired captures only  
Target actions performed for this report: none

## Result

The repeated line

```text
[HDMIRX][Port0] CLEAR_AVMUTE <...>
```

is an HDMI-receiver General Control Packet (GCP) event record, not a panel
TCON status, a DP-mute command, a recovery/watchdog message, or a periodic
software debug poll.

In the exact retained `sdp_hdmi.ko`, the only producer call is in
`hrx_isr`. The ISR merges and clears packet-received, packet-change, and HMON
packet-pending indications. Pending slot 4 invokes `hrx_get_infoframe` with
type 4. That function reads the per-port HDMI receiver registers `0x1120`
and `0x1124`; the low byte read from `0x1124` is the value tested by the ISR.
Value `0x10`, combined with a nonzero cached AVMUTE state, queues event type 2.
The workqueue later formats event type 2 as `CLEAR_AVMUTE`.

Consequently, one row means that the ISR processed a relevant pending GCP
condition and observed decoded status `0x10` after a nonzero cached state. It
does **not** show that the television acknowledged anything to the HDMI
source, that the panel accepted a command, or that a panel rail or TCON state
changed. The three pending sources are ORed before dispatch, so the row alone
cannot distinguish packet-received from packet-change or HMON-pending.

The 1,114-row PROGRAM_LABEL sidecar sequence is real and highly regular, but is
not fault-specific:

- 1,062 rows are strictly inside that run's `CAPTURE_START..CAPTURE_END`.
- Its median source timestamp interval is 41.7 ms. Every observed gap rounds
  to one through five multiples of 41.7 ms.
- The earlier owner-visible Ugoos menu capture also contains 695 such rows
  (587 in its physical window), with the same 41.7 ms median and the same
  one-through-five-frame gap pattern.
- The working PROGRAM_A capture contains one in-window row, at initial HDMI
  packet filtering, and no sustained sequence.

The two repeating cases both report input cadence about 23.975 Hz. PROGRAM_A
reports about 49.998 Hz. There is no explicit 24/50-Hz branch in the recovered
GCP/AVMUTE basic block: the code branches on pending slot, the decoded GCP
byte, and the cached AVMUTE state. The data therefore support a source/mode
packet-pattern discriminator—most plausibly repeated GCP clear observations
on the 23.976-Hz output path—but do not by themselves prove why that source
emitted the pattern or that it caused the later black picture.

## Exact binary provenance

Primary binary:

- [`binaries/sdp_hdmi.ko`](../binaries/sdp_hdmi.ko)
- size: 3,299,534 bytes
- SHA-256: `f7cffd19934ef459b0263ceddddf003306b399e01d0ddee48df3f64a86667994`
- ELF: AArch64 relocatable kernel module, not stripped
- GNU build ID: `4ceac571596ba4011b8c27c3fab68a34f6a593ff`
- `.text` file offset: `0x80`; addresses below are section-relative ELF
  addresses, not loaded kernel virtual addresses.

The two other locally retained HDMI modules were checked for the literal and
do not contain it:

| File | Size | SHA-256 |
|---|---:|---|
| `binaries/tztv_hdmi_switch.ko` | 87,934 | `11d9c53a0e08300bb12b1cafd513e3fc6ee84ba1bcd434007e459dce70fa82b6` |
| `binaries/tztv_hdmi_switch_api.ko` | 1,143,558 | `c586a2601665a778a1e7401cd6b7553e03684f2e4536a282047b17059b7eec97` |

Relevant exact `.text` slices, hashed directly from the ELF section bytes:

| Slice | `.text` range | Bytes | SHA-256 |
|---|---:|---:|---|
| full `hrx_isr` | `0x135b0..0x15b34` | 9,604 | `523b18e153b712bdb53ab115439b9281145799ed95beb6dbe1249136e899e287` |
| pending-source merge/dispatch | `0x13c58..0x13d04` | 172 | `e06abb98a01ef7c89feda20e1fcea74020f6a4c8ed6280997c4cb54d72343a9f` |
| GCP read and decoded-byte branch | `0x14038..0x140d4` | 156 | `2bb3c5f3d5525bdd5ee954bfb298c7a330294e532ecb723f2b05255793b9f183` |
| AVMUTE cached-state cases | `0x14d5c..0x15238` | 1,244 | `87ecdc35e93d03a77a21e49e3b832515f5456569b979449c1cf4185533f48512` |
| GCP register decode prefix | `0x79bb0..0x79d60` | 432 | `b4c327af048b5ecda3235444cb4137b8cb336eb8cfad2ac1fdf0e2723bb9c1cb` |
| queue helper and AVMUTE event constructors | `0x9a7a0..0x9a994` | 500 | `ac0b78de81b60067d0ae754d4f42de76af314df53614b3cad0744ab98f2263d2` |
| workqueue clear-format case | `0x9c854..0x9c8ac` | 88 | `5b61c8c559e830300061614ab449dca74c29a14f33951e4104d6c5bf58dad6f6` |

The format-string file offsets are `0x10a391` (colored variant, preceded by
the kernel log-level byte) and `0x10a3c0` (plain variant). Relocations at
`.text+0x9c87c/0x9c880` and `.text+0x9c88c/0x9c8a0` bind those strings to the
event-type-2 workqueue case.

## Machine-code route

### 1. Packet pending, not a timer

Within `hrx_isr`:

- `0x13c58` resolves the HDMI instance.
- `0x13c6c` calls `hrx_chk_and_clear_pend_pkt_received`.
- `0x13c7c` calls `hrx_chk_and_clear_pend_pkt_chg`.
- `0x13c8c` calls `hrx_hmon_pkt_port_pend_clear`; an instance-specific HMON
  pending clear follows at `0x13c9c` when its instance exists.
- `0x13ca0..0x13cf4` merges the three 16-byte pending arrays.
- Combined pending byte 4 is tested at `0x13cf8..0x13cfc` and branches to
  `0x14038`.

This is an interrupt packet-pending path. The helpers clear receiver pending
status; that is not evidence of an HDMI-source acknowledgement.

### 2. GCP status byte

At `0x14038..0x1404c`, the ISR calls:

```text
hrx_get_infoframe(handle, type=4, port, mode=1)
```

For type 4, `hrx_get_infoframe` uses register identifiers `0x1120` and
`0x1124` at `0x79c04..0x79c34`. At `0x79c38`, the low byte of the `0x1124`
read is selected and later stored as the decoded status byte. Back in the
ISR, that byte is loaded at `0x1407c`; `0x1408c..0x14090` compares it with
`0x10` and enters the clear path.

### 3. Cached-state gate and event queue

The per-port cached AVMUTE state is loaded at `0x14088`:

- decoded byte `0x01` follows the SET path; the cache becomes 1;
- decoded byte `0x00` makes the cache 2 without emitting a clear row;
- decoded byte `0x10` reaches `0x15058`.

At `0x15058`, a zero cached state skips the clear-event constructor. A
nonzero state branches to `0x151e4` and calls
`hrx_workqueue_print_clear_av_mute` at `0x151ec`. The same block then resets
the cache to zero at `0x1522c`.

`hrx_workqueue_print_clear_av_mute` (`0x9a940`, size `0x54`) obtains a
monotonic timestamp and constructs queue event type 2. The shared queue
helper at `0x9a7a0` copies the 32-byte record into a 64-entry ring and queues
the work item. `hrx_workqueue_func` (`0x9ae70`, size `0x1b28`) drains that
ring. Jump-table index 2 lands at `0x9c854`, whose only externally visible
operation is formatting/printing the retained `CLEAR_AVMUTE` row.

This rules out the workqueue itself manufacturing a 24-Hz print loop. Each
printed row originated in a separate ISR-side event enqueue. It does not
prove that every source packet produced a retained row; the ring, log
transport, and pending coalescing can omit observations.

## Retained-event comparison

Raw evidence pins:

| Capture | Record SHA-256 | Vlog SHA-256 | Artifacts SHA-256 |
|---|---|---|---|
| Ugoos menu | `3f0cf5c4be7210dbfbb15b5a3cf08e2edb5178053a712c54ae2f27e0fc52cc9d` | `1c4f4f9c6c39eb0c0faa827c1cc5130191d2a78a006434e73adb666ca8a39210` | not present in this older observer form |
| PROGRAM_LABEL | `2a8b8f922cf8dc0ae4d06fc8cefe3115c81434f1de4642ec149fb2ec7d4b0f59` | `90dc0dcdc4ef4abf59707f2686603053c3a01dd4fbb98c4880a15fbdd82b2543` | `05c32544e2079d7fdc97c6c8ad6913d3499b9d524c9713a3c1e1b0000c0fcb55` |
| PROGRAM_A | `9d34a16fb63163cd7f19955c9974169057d4c57e70ba302b65530834a9d8aee1` | `4cb5bdc2d73f03bd4e4ac48720b6b2edc00712b5d4bee3a9856fd8c596b8cfc7` | `048b4e815d49c17e8f5e8b5ffc11789291730313e33946594e9867d7de419c61` |

All three records remain rejected under their original observer contracts;
this report does not relabel them accepted.

| Retained sequence | All vlog rows | Rows strictly in physical marker window | First/last source timestamp | Median delta | Effective retained rate |
|---|---:|---:|---|---:|---:|
| Ugoos menu, owner-visible control | 695 | 587 | `86140.0246..86174.9773` | 41.7 ms | 19.86/s |
| PROGRAM_LABEL, later black/audio report | 1,114 | 1,062 | `86943.8604..86994.9966` | 41.7 ms | 21.77/s |
| PROGRAM_A, later visible/staying-on report | 1 | 1 | `87400.6037` | n/a | n/a |

For the menu sequence, 588 of 694 successive gaps are one 41.7-ms period;
the rest are 82 two-period, 13 three-period, 8 four-period, and 3
five-period gaps. For PROGRAM_LABEL, the respective counts are 1,022, 75, 11,
4, and 1. There are no non-multiple outliers under 0.1-ms timestamp
resolution. This is much stronger evidence for a frame-paced incoming
packet/pending sequence than for a free-running watchdog or debug timer.

The negotiated input cadences separately retained in the same vlogs are:

- Ugoos menu: `Cature read VFreq = [23975]`;
- PROGRAM_LABEL: `Cature read VFreq = [23975]`;
- PROGRAM_A: `Cature read VFreq = [49998]`.

The 41.7-ms period is the reciprocal of about 24 Hz. The evidence does not
establish whether the Ugoos/Kodi source deliberately transmits a clear GCP
every frame, whether the receiver produces multiple pending indications for
the same semantic state, or whether missing multiples are source omissions,
pending coalescing, or retained-log loss.

## Position in the HDMI state transition

PROGRAM_04 END kernel snapshot contains 1,076 rows. Around the first:

```text
86943.832741  State changed [CLK_SYNC_DET to WAIT_PKT_FILT]
86943.845932  State changed [WAIT_PKT_FILT to LINK_STABLE]
86943.863362  CLEAR_AVMUTE <86943.8604>
86943.905103  CLEAR_AVMUTE <86943.9021>
86943.927200  MainRx link is stable
86943.946859  CLEAR_AVMUTE <86943.9438>
```

The rows then continue without requiring repeated HDMI lock-loss transitions.
The first PROGRAM_A row is likewise part of initial packet filtering:

```text
87400.606673  State changed [CLK_SYNC_DET to WAIT_PKT_FILT]
87400.606714  CLEAR_AVMUTE <87400.6037>
87400.619760  State changed [WAIT_PKT_FILT to LINK_STABLE]
```

Thus the single row is normal at link acquisition, and the sustained rows can
continue in a stable link. Neither form is itself a lock-loss report.

## DP mute and panel/TCON boundary

The recovered clear basic block does not call a DP mute, QDF, panel-TCON,
power, reset, or recovery function. It queues a print record, updates
receiver-side cached fields, and sets a receiver software flag. The same ISR
does contain a separate call to `hsi_manage_dp_direct_mute` at `.text+0x14e3c`,
but control from the clear-event block does not enter that call.

This proves only the immediate call boundary. A later consumer of the updated
receiver state could influence another subsystem; that transitive consumer
was not required to explain the log and was not exhaustively traced here.
Likewise, temporally adjacent `QDFTcon_SendOneCommand` or DRM-DP lines do not
become call edges merely because they share a kernel snapshot.

The repeated rows therefore help diagnose the HDMI input packet pattern and
mode path. They do not directly diagnose the accepted TCON status `0x10`, the
fault GPIO value 1, panel light emission, mute state, or physical picture.

## Practical discriminator

The most informative controlled variable is the Ugoos output cadence/mode,
not `CLEAR_AVMUTE` presence by itself:

1. The visible menu and failed PROGRAM_LABEL playback both use the approximately
   23.976-Hz input path and both show the sustained clear-GCP pattern.
2. Working PROGRAM_A uses the approximately 50-Hz input path and shows only
   the initial clear event.
3. Therefore repetition identifies the 24-Hz packet behavior but cannot
   separate visible from black within that behavior.

A future already-authorized diagnostic comparison should keep the same media
and playback path while changing only output cadence, or compare a known-good
23.976-Hz title against PROGRAM_LABEL. The useful outcome would be whether TCON
status/GPIO and picture outcome change while the GCP pattern stays the same.
No such test is performed or authorized by this offline report itself.

## Limits

- The source timestamps are those saved in the queued HDMI event; the outer
  kernel/vlog timestamps occur a few milliseconds later when the worker
  prints them.
- The exact hardware meanings of receiver register identifiers `0x1120` and
  `0x1124` beyond their decoded use here are not named by this module's
  symbols.
- The merged pending array prevents assigning a row to exactly one of
  received/change/HMON pending sources.
- The static route identifies status `0x10` by its vendor `CLEAR_AVMUTE`
  branch and format string; it does not establish HDMI-source intent.
- No retained row is a transport acknowledgement from the panel controller,
  and absence of this row would not prove absence of AVMUTE handling.
- The rejected capture records remain useful only as explicitly bounded raw
  sidecar evidence; this report does not repair their original observer
  acceptance failures or infer a physical onset time.
