# Exact HDMI control implementation: DPMS notification reaches a cached byte

This is a static trace through files copied from the owner's TV. It does not
establish that the path executed during a blackout, and it does not identify
the cause of the damaged panel going dark. No implementation function, ioctl,
factory function, or callback was invoked by this analysis.

## Exact inputs and acquisition boundary

The implementation is
`overnight/serdes-hdmi-control-impl-copy-20261026/libhdmi-control-impl-sec.so.0.1`,
75,882 bytes, SHA-256
`5eaef7e92eac9468bf41073ccece56a64a70339c3056c3ca2b62391171f4d2a1`.
The fixed metadata read observed this exact versioned pathname mapped into
AVOC PID 706, start tick 603, in boot
`00000000-0000-4000-8000-000000000000`, uptime 70333.51..70333.53.
Three fixed chunks were acquired at uptime 70354.21..70354.71. Each raw
authenticated response contains before/after whole-file hashes. Parent replay
of all raw chunks reconstructed the exact retained ELF and manifest metadata.
The mapping observation is a point sample, not a verified runtime callback
binding or proof that any function ran.

The first metadata attempt against unversioned implementation paths exited
one before `stat`, after two silent tests (`test -f` and `test ! -L`); that
capture alone cannot identify which test failed. That result is preserved
under `hdmi-backend-metadata-20261026`; it does not show that the libraries
were absent. A separate fixed metadata read recorded
the symlinks and the identities of both versioned regular files under
`hdmi-backend-versioned-metadata-20261026`. The intermediate `.so.0` symlinks
were not resolved by that capture, so literal loader names are not thereby
bound to the copied versioned files. The input implementation was also
copied separately, but is outside this report's code trace.

Kernel inputs are the existing exact copied `tztv_hdmi_switch.ko`
(`11d9c53a0e08300bb12b1cafd513e3fc6ee84ba1bcd434007e459dce70fa82b6`)
and `tztv_hdmi_switch_api.ko`
(`c586a2601665a778a1e7401cd6b7553e03684f2e4536a282047b17059b7eec97`).

## Positive static chain

1. The implementation's `hdmi_control_impl_set_funcs` (Thumb entry `0x8e79`)
   populates 32 callback slots. Interpreting its bounded straight-line
   literal/GOT-load/store sequence resolves slot `+0x38` to
   `ppi_hdmi_control_set_notify_dpms_type_impl` (Thumb `0x8575`). The wrapper
   in the previously copied `libhdmi-control` calls this slot; the separate
   power-callback report covers its optional RPC call and result combination.
   This is a possible static table construction, not a sampled live table.
2. `ppi_hdmi_control_set_notify_dpms_type_impl` places its argument in a
   four-byte stack payload and constructs a 20-byte extended-control entry.
   `movw r3,#0x9d5` / `movt r3,#0xa0` at `0x8598/0x859c` construct the exact
   control ID **`0x00a009d5`**. The entry's size is four and its payload pointer
   is stored at entry `+0x0c`. The helper call at `0x85aa` is resolved through
   the actual PLT/GOT instructions to `hdmisw_set_ext_ctrls`.
3. `hdmisw_set_ext_ctrls` (Thumb `0x816d`) opens the exact literal
   `/dev/video28`. It sets class `0x00a00000`, count one, and the supplied
   entry pointer in a 24-byte header, then calls `ioctl` with request
   `0xc0185648`. The success/failure/close paths are retained in the listing:
   open failure returns -1; ioctl failure records -1; successful ioctl starts
   with zero result; a close failure also makes the result -1. The outer
   implementation preserves the helper result for return. These are software
   return semantics, not measurements of the physical picture.
4. In the exact switch module, control ID minus base `0x00a00998` is table
   index `0x3d`; the signed-halfword jump-table entry resolves to `.text+1da0`.
   That case reads a payload pointer from control entry `+0x0c`, copies one
   byte into a zero-initialized stack byte, then calls the exact relocated
   `tztv_hdmi_switch_notify_dpms_type`. **The copy helper's return is ignored:**
   notification proceeds with the initialized/result byte regardless of copy
   success. The helper zero-fills an uncopied tail, so a failed one-byte copy
   can still notify zero. Thus a four-byte userspace argument becomes a
   one-byte notification at this kernel boundary. The null-payload branch
   remains outside this bounded case trace. This does not establish that an
   invalid pointer or failed copy occurred on the TV.
5. API `.text+3280` loads `sgHdmi_ops`, checks table and slot `+0x240`, masks
   the argument to eight bits, and calls that slot. A missing table or slot
   returns `-19`. `start_hdmi_switch_driver` publishes the result of
   `hdmiswitch_get_ops`; that getter returns `.data+0xa30+0x180`. The exact
   relocation at `.data+0xdf0` (`0xa30+0x180+0x240`) binds this slot to
   `.text+c958`, **`NotifyDpmsType`**.
6. `NotifyDpmsType` masks the argument and stores it at **`.data+0xa38`**
   (`0xa30+8`). Its only calls are process identity helpers, `printk`, and
   `hdmisw_vlog`; it returns zero. In this bounded function there is no direct
   panel mute, hardware power, private suspend/resume, or MMIO operation.

This distinguishes a DPMS *notification* from proof of a physical panel-off
command. It does not exclude later consumers of the cached byte affecting
policy. Those consumers, the upstream producer/timing, and the incident
alignment remain separate investigation steps. The previously recovered
private suspend/resume IDs `0x00a009be/bf` are different controls; this new
notification route does not prove invocation of either.

## Reproduction and limits

Run [the offline verifier](hdmi-control-dpms-chain-reproduce.py) with
`PYTHONPATH=/tmp/tcon-capstone`. It hash-pins the implementation, both kernel
inputs, and the existing kernel reader. It distinguishes code/literal pools
using this ELF's ARM mapping symbols, resolves all 77 PLT entries by actual
ARM instruction immediates and GOT relocations, reconstructs the 32-slot
builder, checks control/jump-table arithmetic, checks critical kernel
relocations, and equality-checks the
[saved v2 disassembly](hdmi-control-dpms-chain-v2.disasm). The original v1
listing is preserved. Independent review identified the initially omitted
copy-result handling; v2 adds the complete local copy helper and checks that
the notification case does not test its result.

The PLT resolver does not assume fixed-size entries or use relocation ordinal
as a code address. ARM immediate rotations are decoded from the instruction
word, including forms Capstone prints as an immediate plus rotation operand.
Normal/optimized verifier execution and Python compilation passed. Independent
review cleared the corrected v2 source, listing and interpretation. The checker validates the stated landmarks;
manual control-flow review remains necessary for the surrounding return and
policy interpretations. No TV state was changed by the verifier.
