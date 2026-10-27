# QD mute/frame-mode concurrency audit

## Scope and result

This is an offline, static audit of the copied `qdf_tcon.ko` only.  It made no
TV call, loaded no module, and installed no tracing or instrumentation.  The
input SHA-256 is:

```text
97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63  qdf_tcon.ko
```

**Result:** the temporary `F3:0x164=1` / frame-mode / `F3:0x164=0` sequence in
`m_tcon_set_frame_mode` is **not** one mutex-protected operation.  The exact
same `frc_tcon_mutex` serializes each individually requested transport
operation, and serializes the central frame-mode write/read region, but it is
released before the 50 ms wait and before the final unmute is acquired.  An
ordinary native AVE/QDF `SetMute` request can therefore interleave at those
gaps.  This proves an ordering hazard, not that it caused the observed black
screen.

## The three lock objects are distinct

`readelf -sW` names the objects below; all are 40-byte Linux mutexes in
`.data`.  The wrappers do not use their incoming `x0` argument as a mutex
pointer: they construct these fixed addresses themselves.

| Wrapper | Exact mutex object | Proof |
| --- | --- | --- |
| `frc_comm_lock` / `frc_comm_unlock` | `.data+0x400` (`frc_comm_mutex`) | `0x1648c/0x164ac`, `mutex_lock/unlock` |
| `tcon_comm_lock` / `tcon_comm_unlock` | `.data+0x428` (`tcon_comm_mutex`) | `0x164cc/0x164ec`, then `add #0x28` |
| `frc_tcon_lock` / `frc_tcon_unlock` | `.data+0x450` (`frc_tcon_mutex`) | `0x1650c/0x1652c`, then `add #0x50` |

Consequently the different rodata addresses passed by callers to
`frc_tcon_lock` are logging/context strings, **not different locks**.  The
paths in this report all use `.data+0x450`, hereafter **M**.  No code shown
here takes either of the other two mutexes.

## What `m_send_cmd_with_lock` actually promises

At `0xbbdc` the helper saves its third argument in `w27`. Before considering
that lock, it reads `m_panel_dpms_pvcc_status` (`.bss+0x194`) at `0xbbec` and
ORs it with the payload at `0xbbf0`. For the special selector `F3:0x164`, a
zero payload plus a zero PVCC-status sample branches at `0xbbf4` to `0xbe80`:
the helper logs and returns without attempting the transfer or taking M.

Only when that early-skip condition does not apply does `0xbc04` branch to
`0xbf98` for nonzero `w27`; `0xbf9c` calls `frc_tcon_lock` (M). At every
normal transfer exit `0xbe2c` branches to `0xbfa4` only when `w27` is nonzero;
`0xbfa8` unlocks M. Thus:

* A non-skipped `m_send_cmd_with_lock(..., w2=1)` locks M for that *one helper
  call*. The `F3:0x164`/payload-zero/PVCC-zero case is the exception above.
* `m_send_cmd_with_lock(..., w2=0)` takes no lock itself.
* `m_read_cmd` separately locks and unlocks M (`0x9be4`, `0x9c98`).
* `m_read_cmd_no_lock` is deliberately used where a caller already owns M;
  it is not independently serialized.

This is a per-I2C-command/protocol-helper lock, not a lock covering a caller's
higher-level intent.  It is incorrect to describe every QD I2C transaction as
unlocked, but equally incorrect to infer an atomic mute bracket from `w2=1`.

## Exact frame-mode ordering

`m_tcon_set_frame_mode` starts at `0x10508`.  `m_mute_state` is the ordinary
four-byte BSS object at `.bss+0x140`; it is read at `0x1052c` without M.

When that cached value is not 1, the static sequence is:

```text
10578–1058c  F3:0x164 payload 1; w2=1 → helper acquires/releases M
10594–10598  ft_msleep(50)                       [M is not held]
105d8–105e4  m_read_cmd(F3:0x160) → independently acquires/releases M
105f8         explicit frc_tcon_lock(M), only if read mode != requested mode
10600–1060c  F3:0x160 frame-mode write; w2=0      [caller owns M]
10618–10620  m_read_cmd_no_lock(F3:0x160)          [caller owns M]
10664–1066c  ft_msleep(500) on verify-success path [M remains held]
10698         frc_tcon_unlock(M)
1073c–1074c  attempt F3:0x164 payload 0; w2=w23=1 → helper either
             skips before M if PVCC-status sampled zero, or acquires/releases M
```

If the initial `F3:0x160` read already equals the requested mode, the explicit
`0x105f8–0x10698` region is skipped, but the final temporary unmute still runs
(`w23` remains 1).  If the initial cache was 1, `0x10550 → 0x106b8` sets
`w23=0`, so **both** temporary `0x164` commands are skipped.  The temporary
commands never update `m_mute_state`. The PVCC-status decision for the final
zero attempt is made *before* M is acquired (and can cause no acquisition at
all). This report does not duplicate the separate audit of all PVCC flag
writers; it only records the exact timing of the guard in this operation.

## Interleavings the code permits and forbids

An ordinary public AVE request reaches `QDFTcon_t_Tcon_SetMute` at `0xce00`.
Its real `F3:0x164` sends pass `w2=1` (`0xcebc`, `0xcf80`, `0xd00c`) and hence
use M, but the function never owns M across its decision, send, cache update,
and status reads.  It can therefore run between the frame-mode substeps below:

| Interval in frame-mode path | Native `SetMute` send can run? | Reason |
| --- | --- | --- |
| after temporary mute-one helper returns, during `msleep(50)` | Yes | M was released by the helper before `0x10594` |
| after initial `m_read_cmd` returns, before `0x105f8` | Yes | that read has released M |
| during `0x105f8–0x10698` | No, if it uses `w2=1` | it blocks on the same M; the 500 ms wait remains inside M |
| after `0x10698`, before final mute-zero helper obtains M | Yes | M has been explicitly released; its PVCC guard sample is also outside M |
| after final helper returns | Yes | the frame-mode invocation is over |

The code only proves this protection for call sites that use M.  A direct
`m_send_cmd_with_lock(..., w2=0)` caller is not protected by the helper; the
central frame-mode call is one such caller, but it is safe there because its
immediate caller owns M.  This audit does **not** claim that every other
`w2=0` call site in the module follows that rule, nor that an unobserved
non-QDF writer exists.

## Cached-state race: plausible effect, and its limit

`QDFTcon_t_Tcon_SetMute` reads `m_mute_state` at `0xce3c`, decides whether to
send, then writes the requested cache value after the helper has returned:
`0xcecc` for general changes and `0xcf94` for the cached-one → zero path.
Those are plain `ldr/str` accesses, not an atomic check-and-update under M.
The zero path additionally reads live `0x164` at `0xcfac` and may resend zero
at `0xd008` if the reply is nonzero.  This matches the public native service
path; it is not a synthetic raw-I2C assumption.

Therefore a frame-mode invocation can read cache zero, another thread can set
cache one and send mute-one, and the frame-mode invocation can later issue its
temporary unmute without changing the cache.  That leaves the reverse
mismatch: **hardware requested unmuted while cache says muted**.  Other
interleavings alter which command is last.  The cache does not make the bracket
atomic and it can become stale with respect to the temporary commands.

However, a simple successfully transported ordinary `SetMute(1)` cannot by
itself explain a final *hardware-muted/cache-zero* state: it stores cache one.
For that particular mismatch, the static code has concrete candidates: the
final zero attempt can take the `0xbbf4 → 0xbe80` PVCC-status early-skip and
issue no wire command; alternatively its transfer can fail/be dropped, or a
later writer may not update this cache. The PVCC predicate itself is sampled
outside M, so an interleaving writer can change it before or after the sample;
which writer, if any, did so remains an evidence question for the separate
flag-writer audit. Do not turn this static possibility into incident proof.

## Passive trace: what it can settle

The existing passive trace format includes `TASK-PID`, `TGID`, CPU and a
timestamp for each observed event.  The prior capture demonstrably attributes
stock QD traffic to `AVEMonDIM-1013 (TGID 706)`.  A bounded passive capture
with complete ring accounting and the existing bus-5/address-0x76 decoder can
therefore establish the observed time order and emitting task identity of
`F3:0x164` and `F3:0x160` transactions, including whether another *observed*
task's command falls between them.

It cannot, with the currently shown events alone, prove mutex acquisition or
wait order, link a transfer to a precise instruction/caller, observe an
omitted transfer after buffer loss, prove MCU acceptance, or prove panel light.
The appropriate result label is "observed wire order by task", not
"thread-race proven".  No instrumentation is proposed or installed here.

## Raw-proof reproducer

[`qd-mute-concurrency-proof.sh`](qd-mute-concurrency-proof.sh) is stdout-only
and has no TV/network side effect.  It prints precisely the disassembly and
ELF symbol evidence used above, after first checking the copied module hash.
