# AVOC native panel-mute controller — recovered state and reset paths

This is an **offline exact-build** analysis of `binaries/avocd`, SHA-256
`ab450eaf99c793f3c7a9360629b1a1677e9d86dcd74a1f93796b56ba07401de9`.
Addresses are ELF link virtual addresses; the code is Thumb.  The independently
reproducible PLT/call scan is parent-owned
`overnight/trace-avocd-panel-mute.py`, with its raw output retained in
`overnight/avocd-panel-mute-{calls,controller-calls,reset}.txt`.

## Exact native output operation

`ppi_ve_set_panel_mute` has a single AVOC direct call site: PLT `0x1c448`,
called at `0xac2f6` from wrapper `0xac2c8`.

```text
0xac2f0  and r0, r5, #1       # normalize requested state
0xac2f4  movs r1, #0          # fixed second PPI argument
0xac2f6  blx  #0x1c448        # ppi_ve_set_panel_mute
```

The wrapper passes `onoff & 1` and zero.  It has exactly four direct callers:

| caller | recovered action | PPI state |
| --- | --- | --- |
| `0xaff70` | SetBlack's mute branch | `1` |
| `0xb13cc` | SetForceMute(1) | `1` |
| `0xb1404` | SetForceMute(0) | `0` |
| `0xb1550` | ResetBlack unmute branch | `0` |

The PPI return value is captured by the wrapper but neither `SetForceMute` nor
`ResetBlack` uses it to decide whether to update its own state.  Therefore the
controller's cleared state is evidence of an **attempted** unmute, not proof
that AVE, FRC, and TCON completed it.

## Controller bytes and public getters

The controller global is at `0x179434`:

| byte | role established by direct reads/writes | public getter exposure |
| --- | --- | --- |
| `+0` | force-mute intent; written first by SetForceMute | `GetPanelMute` handler `0xaffdc..0xb002c` |
| `+8` | black/mute case; set before a mute request and cleared after unmute attempt | `GetPanelMuteCaseStatus` handler `0xaff84..0xaffc2` |
| `+9` | freeze case; reset independently calls the freeze-clear helper | **not exposed** by either getter |
| `+0x1c,+0x1d` | saved black/freeze snapshots used by the change detector | not exposed |
| `+0x18` | nesting/change counter used by the state-change endpoint | not exposed |

This corrects an important observability limitation: a `GetPanelMute=0` result
means only that the **force-intent** byte is zero.  A
`GetPanelMuteCaseStatus=0` means only that the **black-case** byte is zero.
Neither says whether freeze (`+9`) is clear or whether the downstream native
PPI completed.  The previously observed pair `0/0` is consequently not proof
that panel output is healthy.

The direct getter loads are independently reproducible in the matching binary:

```text
# GetPanelMuteCaseStatus callback
0xaffb6  movw r3,#0x9434; movt r3,#0x17
0xaffc2  ldrb r1,[r3,#8]

# GetPanelMute callback
0xb0014  movw r3,#0x9434; movt r3,#0x17
0xb002c  ldrb r5,[r3]
```

## Mute and reset state machine

`SetForceMute` starts at `0xb13b4`:

```text
0xb13c4  strb r0, [r3]        # global +0 = force intent
0xb13c6  cbz  r0, 0xb1402
0xb13c8  movs r0, #1
0xb13ca  strb r0, [r3,#8]     # global +8 = black case
0xb13cc  bl   0xac2c8         # PPI(1)
...
0xb1402  strb r0, [r3,#8]     # clear black case for force=0
0xb1404  bl   0xac2c8         # PPI(0)
```

`ResetBlack` starts at `0xb152c`.  It first calls eligibility function
`0xafe18`; that function requires force byte `+0 == 0`, controller pointer
`+4 != 0`, initialized field at pointed object `+0x18 != 0`, and its power
field `+0xb8 == 0`.  A failed eligibility check returns without clearing
anything.  On success:

1. If freeze byte `+9` is set, it calls the separate helper at `0xac218` with
   zero and clears `+9`.
2. If black byte `+8` is set, it calls wrapper `0xac2c8` with zero and then
   clears `+8` regardless of the PPI result.

There is no timer in this reset function.  In particular, no claim is made
that the owner's roughly-three-second physical latch corresponds to a fixed
three-second AVOC timeout.

## All direct ResetBlack callers and the NewHome hook

The exact binary has four direct branches to `0xb152c`:

| call site | caller context proved by nearby source-file literal | branch condition / meaning recovered |
| --- | --- | --- |
| `0x6f748` | `video-ctx-event-listener-impl-sec.cpp` | callback unconditionally invokes reset at this point; its event type is not named in the stripped body |
| `0x75b6a` | transition path spanning `avocd_dynamic_peaking.cpp` / `avocd_multi_link_hdr.cpp` | reached only after `0xba6b4` returns nonzero, then helper `0x4c0cc`; exact semantic condition remains unnamed |
| `0xb1654` | `avoc_panel_mute.cpp` controller change endpoint | decrements global `+0x18`, compares current `+8/+9` to snapshots `+0x1c/+0x1d`, resets on either mismatch, then updates the snapshots |
| `0xc174a` | `avoc_new_home.cpp` | invokes ResetBlack only when `sl != 0`; this is `handle-set-new-home` callback `0xc1524`, with `sl` loaded from its incoming value argument |

The last row is the concrete public NewHome link. The registration loop at
`0x7b7c4` reads table entries as `{signal_name, callback}`; entry `0x173c84`
is `{ "handle-set-new-home", 0xc1525 }`. Therefore the managed public
`AvocSetNewHome` route reaches this callback. Its incoming value is preserved
in `sl`, is tested at `0xc1744`, and is forwarded to the AVE NewHome PPI at
`0xc18f8`. The full managed-to-native evidence and its lifecycle-only scope
are recorded in `newhome-ui-native-arguments.md`.

The controller change endpoint at `0xb1630..0xb1662` is a
state-snapshot/nesting mechanism, not an independently identified clock hook:

```text
0xb163e  ldr  r3,[global,#0x18]
0xb1644  subs r3,#1
0xb1646  str  r3,[global,#0x18]
0xb1648  cmp  current_black, saved_black
0xb164c  cmp  current_freeze, saved_freeze
0xb1654  bl   0xb152c           # only after a state mismatch
```

## Consequence for diagnosis

There is a real native NewHome route to an attempted unmute. It remains
insufficient to call it the cause of playback blackouts: the owner did not
report a matching lifecycle event before the Ugoos events, and the API carries
only global NewHome state, not a Home tab. It is therefore a candidate for
FullHome/overlay-correlated flicker or black, not evidence against or for a
particular Home tab.

Any future passive trace should retain timestamps for AVOC NewHome, panel-mute
force/case/freeze logs, and AVE/TCON records.  Do not interpret the two public
getter values alone as a physical-panel or PPI-completion test.
