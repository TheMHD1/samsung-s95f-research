# NewHome argument bridge: proven registration and boolean route

This offline audit uses the matching `avocd`, CSFS, and `Tizen.TV.System.dll`
copies. No TV action was taken.

## Callback identity: registration loop, not table adjacency

The callback table begins at `0x172dd4`. Its consumer is the sole
`g_signal_connect_data` registration loop at `0x7b7c4`:

```text
0x7b78a/0x7b78e  MOVW/MOVT r4,#0x172dd4   # table base
0x7b79a/0x7b7b4  ldr r1,[r4]              # signal name
0x7b7c2          ldr r2,[r4,#4]           # callback
...                add r4,#8               # next entry
```

At the relevant table entry `0x173c84` (offset `0xeb0`, divisible by 8):

```text
0x173c84  0x00107c10  "handle-set-new-home"
0x173c88  0x000c1525  Thumb callback 0xc1524
```

So `0xc1524` is conclusively the `handle-set-new-home` callback. An earlier
adjacency interpretation paired entries in the opposite order; that was wrong
and is superseded by the loop disassembly. The following entry maps
`handle-reset-special-modes` to its own next callback.

## Public and managed ABI

The live AVOC interface declares `SetNewHome(i value) -> (i ret)`.

The matching `Tizen.TV.System.dll` closes CSFS's managed bridge:

```text
CSFS TypeRef: Tizen.TV.System.Avoc.Avocd
  ResolutionScope: Tizen.TV.System, Version=4.4.0.0

Avocd::AvocSetNewHome(int), token 06000387:
  ldarg.0
  call Interop/Avocd::avoc_set_new_home(int)

Interop/Avocd::avoc_set_new_home, token 06000566:
  P/Invoke /usr/lib/libavoc.so, entry avoc_set_new_home
```

CSFS passes `1` from its FullHome/NewHome-on worker and `0` from its off/exit
paths. The relevant worker is
`FSAVMuteControl.<>c__DisplayClass19_0::<AvocSettingForHome>b__0`, token
`060005ef`; it logs `call AvocSetNewHome(1)` and forwards its captured integer.
`NUIApp.OnTerminate` (token `0600013f`) and `AvocSettingOffByAppId` issue
`AvocSetNewHome(0)` when their lifecycle conditions allow it.

This is a global FullHome/NewHome boolean, not an Apps/For You/Live/Settings
tab ID. No CSFS IL call supplies a tab or page identifier to this API.

## Native boolean propagation

The handler captures the incoming third ARM argument in `sl`:

```text
0xc1524  push.w {r4,r5,r6,r7,r8,sb,sl,fp,lr}
0xc1528  mov   sl,r2
...
0xc1744  cmp.w sl,#0
0xc1748  beq   0xc174e
0xc174a  bl    0xb152c       # ResetBlack only for nonzero NewHome
...
0xc18f6  mov   r0,sl
0xc18f8  bl    0xae9b0

0xaea10  subs  r0,r4,#0
0xaea14  movne r0,#1         # normalize nonzero to 1
0xaea16  blx   0x1cc58       # ppi_ve_set_newhome_inout_state
```

Thus `SetNewHome(1)` enters the native branch that attempts `ResetBlack` and
sets AVE/FRC NewHome state; `SetNewHome(0)` takes the complementary off path.
This does not prove that every Settings overlay causes a NewHome transition,
and it does not attribute playback-only blackouts to this route.

## Reproducible evidence

The Cecil metadata probe and its exact output are retained under
`idle-research/metadata-probe/`. Native callback registration is recoverable
from the matching `avocd` using the table base and consumer instructions above.
