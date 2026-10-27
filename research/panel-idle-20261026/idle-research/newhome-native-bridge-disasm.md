# Raw native NewHome bridge evidence

Input binaries: matching `Tizen.TV.System.dll` SHA-256
`72056f70facd6433bd696de41ba857c387c22abfdeaa6032d39f0a640acc9065`,
matching `libavoc.so`, and matching `avocd`.

## Managed interop

`Tizen.TV.System.Avoc.Avocd::AvocSetNewHome(int)`, token `06000387`:

```il
IL_0000: nop
IL_0001: ldarg.0
IL_0002: call Interop/Avocd::avoc_set_new_home(System.Int32)
IL_0007: stloc.0
IL_0008: ldloc.0
IL_000d: ret
```

`Interop/Avocd::avoc_set_new_home`, token `06000566`, has P/Invoke module
`/usr/lib/libavoc.so` and entry point `avoc_set_new_home`.

## Generated D-Bus proxy envelope

`libavoc.so` exports `avoc_proxy_call_set_new_home_sync` at Thumb
`0x4726a4cc`. Its literal-derived values are `(i)` and `SetNewHome`:

```text
4726a4cc: push.w {r4,r5,r6,r7,r8,sb,lr}
4726a4d0: mov    r4,r0
4726a4d2: ldr.w  r8,[pc,#0x50]       # PC-relative -> "(i)"
4726a4da: add    r8,pc
...
4726a4ee: ldr    r1,[pc,#0x38]       # PC-relative -> "SetNewHome"
4726a4f4: mov    r0,r4
4726a4f6: add    r1,pc
4726a4fc: blx    0x47254cfc           # generated proxy call machinery
```

The resolved literal addresses are `0x472e6eb4` = `"(i)"` and
`0x472ebe80` = `"SetNewHome"`. This proves the native client transport's
method envelope is a one-integer D-Bus call named `SetNewHome`.

`libavoc` also exports the public P/Invoke target `avoc_set_new_home` at
Thumb `0x472a56fc` (symbol value `0x472a56fd`, size 616). Its entry stores the
incoming `r0` argument unchanged before invoking its internal client/state
machinery:

```text
472a56fe: push.w {r4,r5,r6,r7,r8,sb,sl,fp,lr}
472a571a: mov.w  r3,#-1
472a571e: str    r0,[r7,#4]           # public int argument retained
472a5724: blx    0x472564e4
...
472a57a2: ldr    r1,[r7,#4]           # retained public argument
472a57a4: blx    0x47254378
```

The stripped internal helper at `0x47254378` is not named by the dynamic
symbol table. The exported generated proxy independently proves the exact
method/signature envelope; further static work is needed to prove the precise
internal call edge from this wrapper to that proxy helper rather than merely
the common library implementation.

## Server callback registration and argument use

The matching `avocd` registration loop proves the server endpoint is callback
`0xc1524`; full details are in `newhome-ui-native-arguments.md`. The relevant
value branch is:

```text
000c1528: mov     sl,r2
...
000c1744: cmp.w   sl,#0
000c1748: beq     0xc174e
000c174a: bl      0xb152c              # ResetBlack
...
000c18f6: mov     r0,sl
000c18f8: bl      0xae9b0
000aea10: subs    r0,r4,#0
000aea14: movne   r0,#1
000aea16: blx     0x1cc58              # ppi_ve_set_newhome_inout_state
```
