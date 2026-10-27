# RoseMQD QD resume-record replay

## Scope

This is bounded offline analysis of `binaries/libave.so.0.1`, SHA-256
`a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777`.
It concerns the per-instance RoseMQD resume-record table, not the separate
`siDimLvl` final-duty cache described in
[`qd-rosem-cache-lifecycle.md`](qd-rosem-cache-lifecycle.md).  No TV, network,
root, process-memory, device, setter, getter, or ioctl operation occurred.

All addresses are ELF virtual addresses. Thumb symbols carry bit zero; code
addresses below are even.

## Concrete replay table

`DimmingBackendRoseMQD::t_SetQdResumeData()` is at `0x1c5f48`, size 62. It
iterates `i = 0..15`. For every byte exactly equal to one at backend `inner +
0x330 + i`, it loads a 64-bit command at `inner + 0x8a8 + 8*i`, takes a
payload pointer at `inner + 0xee8 + 4*i`, and calls
`ave_tcon_api_send_onecommand(command, payload)`:

```text
if *(uint8_t *)(backend_inner + 0x330 + i) == 1:
    command = *(uint64_t *)(backend_inner + 0x8a8 + 8*i)
    payload = backend_inner + 0xee8 + 4*i
    ave_tcon_api_send_onecommand(command, payload)
```

The code makes index `0x115+i` at `0x1c5f64` and applies the eight-byte stride
at `0x1c5f72`; `0x115*8` is `0x8a8`. The payload address
is formed at `0x1c5f68..0x1c5f6c`. The sender result is discarded and the
routine always returns zero (`0x1c5f7a`, `0x1c5f82`).

The resume body contains no fixed F3:0128 immediate. It replays values already
recorded in enabled slots, so this body alone does not establish that F3:0128,
any other particular command, or any particular value was replayed.

## Concrete producer and ordering

`DimmingBackendRoseMQD::t_DevQdDrv_Write_Data(unsigned long long, int,
unsigned int, int)` at `0x1c7d6c`, size 188, is a concrete table producer. Its
64-bit command arrives in `r2:r3`; because ARM aligns that argument, the signed
index and following payload/enable values are stack arguments. On its normal
index path it stores, in order:

1. command at `backend_inner + 0x8a8 + 8*index`
   (`0x1c7d96..0x1c7daa`);
2. payload word at `backend_inner + 0xee8 + 4*index`
   (`0x1c7dae..0x1c7db0`);
3. enable byte at `backend_inner + 0x330 + index`
   (`0x1c7db4..0x1c7dba`); then
4. immediately calls `ave_tcon_api_send_onecommand(command, &local_payload)`
   at `0x1c7dbe`.

It returns zero without inspecting that sender's return. The only shown range
guard is signed `index > 15` (`0x1c7d90..0x1c7d94`), which logs and returns
`-1`. Therefore the producer does not enforce the intended `0..15` range: a
negative signed index passes this guard. That is a control-flow boundary only,
not evidence that a negative index is reachable or that memory was corrupted.

The record stores precede the immediate send. A failed immediate send can leave
an enabled record for a later replay; neither its zero return nor the replay's
zero return proves transport acceptance or physical panel output. This table
is distinct from the documented stock kernel generic replay table; coherence
between the two has not been proved.

## QDDimming lifecycle route

Base `QDDimming::m_SetResumeData()` (`0x1738a8`, size 44) invokes backend
vtable slot `+0x18c` only when the **QDDimming** inner field `+0x398` equals 1
and its backend pointer `this+0x10` is non-null. It then clears that QDDimming
field. The RoseMQD vtable relocation at `0x5a16b8` binds slot `+0x18c` to the
resume routine, and `0x5a16bc` binds the next slot to the producer.

```text
if qd_inner[0x398] != 1:
    return 0
if qd->backend != NULL:
    backend->vtable[+0x18c](backend)
qd_inner[0x398] = 0
```

This is a static connection to RoseMQD when that vtable is selected. It does
not prove the gate was one, this method ran during the incident, a slot was
enabled, or a command applied. A mapping-symbol-segmented scan found no direct
`BL`/`BLX` instruction to `m_SetResumeData` inside this copied ELF; indirect or
external callers remain possible.

## Initialization and limits

In the selected RoseMQD-constructor branch, calls at `0x1c8624`, `0x1c8634`,
and `0x1c8642` zero respectively `backend_inner+0x8a8` for `0x640` bytes,
`+0xee8` for `0x320`, and `+0x330` for `0xc8`. The 16 replay locations fit
within those regions. The constructor-branch condition and all other writers
are outside this bounded audit.

The companion reproducer hash-checks the binary and verifies symbols,
instruction operands, selected virtual-table relocations, and the absence of a
direct final-duty call in the complete replay body. CFG/ABI interpretation is
manual. It cannot prove live table values, calls, sender acceptance, driver
behavior, or a physical screen state.

```sh
PYTHONPATH=/tmp/tcon-capstone python3 tcon-research/qd-resume-record-reproduce.py
```
