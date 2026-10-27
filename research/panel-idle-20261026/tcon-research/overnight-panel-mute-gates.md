# AVOC panel-mute route: exact QD unmute-gate analysis

Scope: offline disassembly of the copied matching `libave.so.0.1`,
`tztv_frc_tcon_api.ko`, and `qdf_tcon.ko`. No D-Bus setter, PPI entry point,
ioctl, I2C command, GPIO, or TV setting was invoked. This document prepares a
diagnostic candidate only; it is not an instruction to issue a mute pulse.

## Result in one sentence

The ordinary public AVOC **unmute** route (`SetPanelMute(0)`) is not proved to
be a cached no-op when QDF's cached mute state is already zero: QDF first asks
the TCON for live mute status (`F3 80 00 00 01 64`) and re-sends mute-zero if
that reply is non-zero. It is a traced stock output-gate
reassertion candidate that does not deliberately request an off/on power
cycle—but it is not a panel-recovery command and its efficacy is unproven.

## Both AVE boolean arguments, as actually used

`impl_set_panel_mute` is at `libave:.text+0x2a3ca0` and dispatches the two
incoming values unchanged through AVE's initialized implementation vtable.
`VideoEnhancerImpl::set_panel_mute(bool,bool)` at `0x29eb74` copies its first
PPI value to `r4` and second to `r5`, then calls:

```text
ave_api_set_panel_mute(r4, r5)     // PLT target 0x8ce1c
```

Within `ave_api_set_panel_mute(int on_off, int second)` (`0x277790`):

* `on_off` is copied into `r5` and is the value sent to both the FRC and TCON
  operations. It is the real mute/unmute selector.
* `second` is copied into `r8`, but **does not flow to either**
  `ave_frc_api_set_panel_mute(int)` or
  `ave_tcon_api_set_panel_mute(int)`. It is passed only as the second
  argument of the current dimming-instance virtual callback.
* On the QD-specific `QDDimming::SetPanelMute(int,int)` implementation
  (`0x171bf0`), only its first value is consumed: when initialized it stores
  it at inner-state offset `+0x11c`; the second value is not read. This method
  emits logging and returns zero; it does not call the QDF mute command.

Therefore there is no evidence that AVE's second Boolean is a QDF/TCON
"force-unmute" or recovery flag. Its exact *AVOC caller-level* name cannot be
assigned from the stripped daemon alone, so this report intentionally does not
call it `force`.

## Exact AVE ordering and guards

The relevant Thumb branches in `ave_api_set_panel_mute` are:

```text
0x27782e  r0 = on_off; if (on_off != 0) goto 0x2778e6
0x277834  ave_tcon_api_set_panel_mute(0)
0x277846  ave_frc_api_set_panel_mute(0)
...
0x2778e6  ave_frc_api_set_panel_mute(1)
0x2778ec  ave_tcon_api_set_panel_mute(1)
```

Thus the normal path does TCON then FRC for an unmute, and FRC then TCON for a
mute. The special shared-state branch at `0x27781e–0x27782c` compares an
opaque shared field at `+0xd50` with `0x905`; if equal, it uses the alternate
unmute order FRC then TCON (`0x27793e–0x27794a`). The matching binary supplies
no type information for that field. It is evidence of a model/configuration
guard, **not** evidence that it is a panel-type guard.

There is no `QDFTcon_t_Tcon_SetMute` branch on OLED model, panel part number,
content/APL, thermal state, error-detect state, PMIC status, or recovery mode.
Its guards are only its normal initialization/readiness state and its local
cached mute state. This does not make it safe to bypass any of those other
systems; it simply limits what this one call controls.

## Kernel route: public AVE request to QDF callback

The TCON leg is fully resolved rather than inferred from strings:

```text
ave_tcon_api_set_panel_mute(on_off)        libave 0x2527cc
  -> tcon_ioctl(0xc004748c, &on_off)       libave PLT 0x8df5c
  -> fop_tcon_ioctl_export                 tztv_frc_tcon_api 0x3048
     command 0xc004748c → jump-table case 0x3f08
  -> copy 4-byte on_off value
  -> TCON_SetMute(on_off)                  tztv_frc_tcon_api 0xe198
  -> registered TCON callback slot +0x60
  -> QDFTcon_t_Tcon_SetMute(on_off)        qdf_tcon 0xce00
```

The jump-table mapping is exact: the `0xc0047404`-based case index for
`0xc004748c` is `0x88`; the `.rodata` signed-halfword at that index resolves
the handler destination to `0x3f08`, whose direct call relocation names
`TCON_SetMute`. `TCON_SetMute` loads and calls callback slot `+0x60` when the
TCON API object is registered. QDF's module initialization table supplies
`QDFTcon_t_Tcon_SetMute` to that slot (`qdf_tcon:.init.text` relocations
`0x364/0x368`, followed by `map_tcon_functions`).

The distinct FRC leg uses `frc_ioctl(0xc0046606, &on_off)`. It is not a TCON
power or reset operation.

## Why cached QDF mute=0 is insufficient to call this a no-op

The relevant AArch64 control flow in `QDFTcon_t_Tcon_SetMute` is:

```text
qdf_tcon:0xce3c  read m_mute_state (+0x140)
qdf_tcon:0xcf20  desired on_off == 0 path
qdf_tcon:0xcf4c  if cached mute != 0: send F3 00 00 00 01 64, payload 0
qdf_tcon:0xcf98  read F3 80 00 00 01 64 into a byte initialised to 0xff
qdf_tcon:0xcfdc  if reply == 0: skip re-send
qdf_tcon:0xd008  otherwise send F3 00 00 00 01 64, payload 0
qdf_tcon:0xd01c  read F3 80 00 00 00 20, then ...21 and ...22
```

So an `on_off=0` request with cached state zero still performs the `0x164`
read and can emit a real TCON mute-zero command if the reply says non-zero.
It then performs the three status reads. Conversely, a zero reply does not
produce the extra mute-zero write. This is a reassertion/check behavior, not a
hardware reset, rail cycle, error-counter clear, or recovery monitor change.

`on_off=1` sends the QD `…0164` payload one only when the cached state differs
from one. It is an actual output blanking action. A diagnostic must therefore
never turn `1` on merely to make a later `0` call happen.

## Bounded diagnostic candidate for the next observed black state

Only after a **physically confirmed black state** and a recorded baseline of
the already-public AVOC getters (`GetPanelMute=0`, `GetPanelMuteCaseStatus=0`),
a single public `SetPanelMute(0)` could answer a narrow question: does the
stock TCON mute-status reassertion restore emission when the high-level AVOC
state is already unmuted?

Required boundaries:

1. One `0` request only—no `1 → 0` pulse, repetition, renewal, raw ioctl,
   private PPI call, factory write, fault-monitor modification, or power
   control.
2. Record the API result and the two public getters after the request; use a
   bounded passive QD trace only if already enabled by the parent, to learn
   whether `…0164` was re-sent.
3. Treat no change as a negative result for this gate only. A physical recovery
   would be evidence for a stale/mismatched mute state, not proof that the
   damaged panel or its other failures are repaired.

The owner has authorized diagnosis and testing; this offline agent performed no TV operation. The parent must coordinate the physical observation before running this candidate, because no recovery can be established from software flags alone. This requests the existing unmuted state and still changes the output-control path. The AVOC controller can discard lower errors, so public ret0 is not proof of successful lower I/O; preserve the trace and physical outcome.
