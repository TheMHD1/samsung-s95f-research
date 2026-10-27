# Independent review closure

Reviewed offline on 2026-10-27. No TV, network, USB, device, debugger, UI,
configuration, or target operation was performed.

## Outcome

**PASS — no P1/P2 correction required.**

The reviewed inputs were:

- `lookup-math.md` SHA-256
  `cc95fde76dbe796850679be483cab85267bdd886f7d123efa258ac0d08714a0c`
- `verify-lookup-math.py` SHA-256
  `cd03ae837494aaf1d7198bbcf354fdf008f447835a2bac8836f0849a35cda9b4`

Independent disassembly confirms the reported control and arithmetic order
at `0x19830`: unsigned-halfword endpoint tests, first strictly lower interior
row selection, low-32-bit `MUL`, signed `SDIV`, and the caller's final
`UXTH`. Both direct callers at `0x27bfc` and `0x27c1a` pass count five and the
reported shared-coordinate and selector-table pointers. The proof that a
reachable interior division has positive width follows from the actual
search order even for duplicate or globally unsorted coordinates; count zero
remains unchecked as documented.

The overflow fixture independently evaluates to mathematical product
`4,294,770,690`, signed wrapped product `-196,606`, quotient `-3`, raw result
`0xfffffffd`, and low-halfword result `65533`. An independent enumeration of
all `d=0..1024` values reproduced the four map hashes, including selector
zero's range `64..1023` with 225 unique outputs.

The `16..1023` result bound is correctly restricted to the selected
package's stored tables. Neither the report nor JSON promotes those package
bytes to current runtime table contents, loader execution, selector/event
identity, units, timing, or physical behavior; arbitrary u16 tables retain
the broader wrapped-arithmetic behavior.

Normal and optimized verifier executions produced byte-identical one-line
JSON with SHA-256
`01fb76699e0d498da006f4ba58e365e67570f8372dfde7e4906995042627ca61`.

