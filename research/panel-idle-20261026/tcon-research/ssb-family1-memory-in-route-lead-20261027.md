# Vendor bulk family1: addressed-memory IN lead

Recorded 2026-10-27 UTC. Parent offline disassembly of the selected profile, SHA-256 `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`. No USB request was issued. All code addresses are linked image0 VA; FILE = VA + `0x200`.

## Positive local dataflow

The validator at VA `0x29258` explicitly accepts target `0x101` at `0x292de..0x292e6`. It extracts the high family at `0x29266`; the `<16MiB` address/range checks at `0x29382..0x293ae` apply only to family2. This is not an allowed-memory-range validator for family1.

After the header target is reduced to its low operation, operation1 at `0x290f6..0x29106` passes `r2 = state+4` (the decoded caller address) and `r3 = *(u32*)0x2000054c` (the clamped current length) into the USB IN scheduler `0x8054`. Its optional additive sum reads that same address. This differs from operation3's eMMC storage leaf and is a candidate for reading controller RAM directly.

The potential address remap can be bounded more precisely than an unknown runtime flag:

- Validator `0x29270..0x29282` stores one at RAM `0x20000570` for family0 and zero for any other family.
- The literals at VA `0x293b4` (FILE `0x295b4`) and VA `0x29224` (FILE `0x29424`) both contain `0x20000570`.
- Consequently, for a `0x101` header the remap test at VA `0x290c8..0x290d4` sees the validator's zero and skips helper `0xefa4`, unless an additional concurrent writer intervenes.

That establishes a selected-header direct-address path. It does not validate arbitrary RAM, MMIO, DMA accessibility or current executable identity.

## Unresolved execution gate: do not send the header yet

The parser at VA `0x28f24` first sets RAM byte `0x20000571 = 2` at `0x28f44..0x28f48`, through its literal at VA `0x291f0` / FILE `0x293f0`. Before current-length setup and operation dispatch, VA `0x290d6..0x290de` tests that same byte and returns early if it is still two.

This matters for **both** operation1 memory IN and operation3 eMMC read. Following a branch's local transfer arguments does not establish that ordinary header processing reaches it. The owner authorization does not resolve this code question. A deferred execution path, phase setter or enabling condition must be reconstructed before treating a one-header live transaction as ready.

Exact raw `0x20000571` words in image0 are at FILE `0xf348`, `0x28edc`, `0x290ec`, and `0x293f0`. The literal at FILE `0xf348` belongs to helper `0xefa4`'s tail: VA `0xf13c..0xf140` also writes two on a selected fallback. This literal census is a navigation aid, not a complete writer/alias census.

Parent follow-up decoded the whole bounded `0xefa4..0xf148` helper: that same byte selects its two mapping modes. Zero selects the first map, one the second, and other values return without a useful mapped source. The helper also writes two on invalid selections. Thus “deferred execution” is only one hypothesis; it is not an established mechanism. The unconditional parser store of two may instead leave transfer operations unavailable in this packaged path. A proven later setter or alternate execution path is still missing. This finding also qualifies the earlier eMMC report's local-branch feasibility statement.

If the execution gate is resolved, the smallest informative candidate would be a fixed read of the already reconstructed descriptor RAM, rather than an arbitrary scan. That could validate protocol address behavior against known bytes before any RT-window or firmware-image access. No such packet was constructed for execution or sent in this block. No existing generic read helper was retargeted.
