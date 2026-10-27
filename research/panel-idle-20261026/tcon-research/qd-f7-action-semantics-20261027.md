# Selected-profile F7 action-helper semantics

Offline packaged-image review only; no controller, USB, UART, network, or TV action occurred.

## Result

The finite F7 receive family is an action protocol, not an additional generic
read namespace. Two deeper helpers are concrete: VA `0x1fab0` (file `0x1fcb0`)
builds a small sampled response through helpers including `0x27670` and
`0x20cc0`; VA `0x1fc8c` (file `0x1fe8c`) obtains the RT root, writes
`root+0x2400 = 1`, then calls `0x1f45c` and `0x1f57c`.

That root write is a real state transition. It is not, from these bytes alone,
a proved RT history/latch acknowledgement, reset, panel reset, or power action:
the bounded body does not read/write the saved-history offsets `+0x2466`,
`+0x2484`, `+0x24aa`, or `+0x24ac`, and no recovered response producer copies
them into the F7 result envelope.

## Exact finite dispatch boundary

Image-0 `VA = stored file - 0x200`; input profile SHA-256 is
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
The F7 dispatcher is VA `0x1ece4` / file `0x1eee4`. Its finite table admits
the previously recovered helper slots for `F701`, `F702`, `F703`, `F708`,
`F709`, `F70B`, `F70C`, `F70E`, `F70F`, `F714`, `F715`, and `F716`; remaining
range slots take its status/error path. Its exact 22 TBB bytes, stored at file
`0x1ef3e` with PC base VA `0x1ed3e`, are
`27 2b 33 3b 3b 3b 3b 2f 0b 3b 17 37 3b 13 1f 3b 3b 3b 3b 23 1b 0f`;
each index is `command - 0xf701` and target is `0x1ed3e + 2*entry`.
There is no caller address or length
parameter that turns this into a memory reader.

The sample action returns response values, not a copied RAM window. The RT
root action changes the `+0x2400` byte, whose selected-package default is
zero, but does not establish what its nested calls mean beyond being action
callees. Neither result provides a bounded getter for live RT latch/history.

## Limits

This does not claim all F7 nested-calIee/MMIO semantics, current-flash
identity, current execution, or absence of another undocumented interface.
It does not construct an F7 invocation. The companion checker pins only the
three source slices above.
