# HDMI-control power callbacks and DPMS notification gates

## Scope and evidence

This is an offline, bounded analysis of the copied
`libhdmi-control.so.0.1` (415,124 bytes, SHA-256
`067ddb8f639f8e91d02524f0820fb3a56e2d9f174d0f3f75a5dec963f7339410`),
from `overnight/serdes-hdmi-control-copy-20261026/`.  It does not call the
library, subscribe to anything, send an RPC, or inspect live state.

The companion verifier uses Thumb decoding for five complete code intervals,
pins the file hash, proves the literal arithmetic and selected CFG landmarks,
and resolves all 409 PLT entries from actual ARM veneer instruction words,
GOT slots, and `.rel.plt` records.  It deliberately does not attempt to prove
runtime GOT contents, callback delivery, or live callback-table binding.

Addresses below are ELF virtual addresses.  Symbol values for Thumb functions
are odd; disassembly addresses are the aligned instruction addresses.

## Registration thread

`register_device_callback_thread` has symbol value `0x47e34715` (code
`0x47e34714..0x47e347b8`).  It first calls `pthread_setname_np`, then calls
`LwipcWaitEvent` with `30000` (`0x7530`) at `0x47e34748..0x47e34750`.
Only its zero-return branch (`0x47e34754`) reaches both subscription calls:

| instruction | resolver-derived PLT target | callback pointer materialized in `r0` |
| --- | --- | --- |
| `0x47e34772` | `device_power_subscribe_poweroff@plt`, `0x47e32eec` | `0x47e34595` |
| `0x47e3477c` | `device_power_subscribe_early_wakeup@plt`, `0x47e33180` | `0x47e345dd` |

The callback pointers are not guessed from symbol ordering.  The two signed
literals at `0x47e347d4` and `0x47e347d8`, added to the Thumb architectural PCs
for `add r0, pc` (`0x47e34774` and `0x47e3477e`), respectively produce those
two odd pointers.  `r1` is set from the zero `LwipcWaitEvent` return before
each subscription.  A nonzero wait result branches to the error-log path at
`0x47e3479c` and returns; the static code shown here does not establish why the
event becomes ready or whether either subscription succeeds.

The verifier independently proves these three PLT names as part of a complete
409-entry ARM-veneer/GOT/relocation bijection, not from a fixed PLT-entry
ordinal or a companion report.

## Shared local suspend state

The power-off callback starts at `0x47e34594` (pointer `0x47e34595`).  After a
`__dlog_print` call through the resolver-derived `0x47e333b8` PLT entry, it
materializes `0x47e83150` and writes integer one there:

```
0x47e345ba  ldr r3, [pc, #0x1c]       ; literal at 0x47e345d8
0x47e345be  movs r2, #1
0x47e345c0  add r3, pc                ; architectural PC = 0x47e345c4
0x47e345c2  str r2, [r3]
```

The wake callback starts at `0x47e345dc` (pointer `0x47e345dd`).  It computes
the same `0x47e83150` using literal `0x47e346f8` plus architectural PC
`0x47e34620`, reads it, and only takes its state-clearing path when the value is
nonzero:

```
0x47e3461e  ldr r0, [r3]
0x47e34620  cmp r0, #0
0x47e34622  beq 0x47e346a4            ; no clear / no worker creation
0x47e34624  ldr.w r8, [r3, #4]
0x47e34628  movs r2, #0
0x47e3462a  str r2, [r3]
0x47e3462c  cmp.w r8, #0
0x47e34630  beq 0x47e34676
```

When that `+4` pointer is non-null, the wake callback allocates and constructs
a local closure-like object and calls `0x47e331f4`; it then cleans the object
up.  The receiver behind that PLT entry is not resolved in this bounded audit,
so the code supports only “a worker/closure path is attempted after a recorded
suspend and a non-null `+4` pointer,” not a claim that a hardware wake occurred
or completed.  Both callback paths include `__dlog_print` calls, but this audit
does not attach human-readable string text to those calls without a separate
format-argument proof.

## RPC client gate

`ppi_hdmi_control_rpc_client_set_notify_dpms_type`
(`0x47e38a5c..0x47e38b28`; symbol pointer `0x47e38a5d`) independently computes
the same state address: literal `0x47e38b40` plus the Thumb PC for the `add` at
`0x47e38aa8` equals `0x47e83150`.  It performs two static rejection gates:

1. `ldr r0, [r3,#4]` / `cbz` at `0x47e38aaa..0x47e38aac`: a null `+4` pointer
   follows the log/error path and returns `-1`.
2. It then reads word zero and `cmp r3,#1` at `0x47e38aae..0x47e38ab0`: exactly
   state one follows another log/error path and returns `-1`.

Only after both gates does it invoke the `ExtInServiceClient::SetNotifyDpmsType`
PLT entry at `0x47e38ac0`.  The static result is a local RPC eligibility gate;
it does not prove a peer, a successful remote operation, a source/UI cause, or
a panel effect.

## Public wrapper combines two result paths

`ppi_hdmi_control_set_notify_dpms_type`
(`0x47e624c4..0x47e62568`) first requires a backend and its callback at offset
`+0x38`; absence leads to its documented local error path.  It computes another
library-global address (`0x47e834f4`) and reads byte `+0x10`:

* Zero: skips the RPC call and invokes the local backend callback at `+0x38`.
* Nonzero: calls the RPC client at `0x47e62532`, saves that return in `r4`, then
  still invokes the same local backend callback.

At `0x47e62500`, `orrs r0,r4` combines the local callback return with the saved
RPC return (or zero if the RPC path was skipped).  The subsequently copied
control implementation statically constructs its `+0x38` slot as
`ppi_hdmi_control_set_notify_dpms_type_impl`; that implementation's bounded
notification route is documented in
[hdmi-control-dpms-chain.md](hdmi-control-dpms-chain.md).  This does **not**
prove that the live table has that implementation, that the local call ran, or
what either path did at runtime.

## Limits

The state word and gate logic are concrete static evidence.  They are not
evidence that these callbacks ran in the reported blackout, that they changed
the OLED/panel/TCON, or that their state explains the fault.  Missing runtime
facts include callback-registration outcomes, the state-word contents, the
`+4` object identity and liveness, wrapper byte value, live backend callback
table contents, and all RPC/closure results.  No change is recommended from
this analysis.

The original [v1 listing](hdmi-library-power-callbacks.disasm) is preserved.
The current verifier exclusively writes and equality-checks
[v2](hdmi-library-power-callbacks-v2.disasm), which adds the independently
checked PLT/GOT evidence.
