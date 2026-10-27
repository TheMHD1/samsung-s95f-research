# W fixed ordinary-input read: independent address review

Root independently checked these geometries offline before target execution.
This report qualifies address/extent, not the future helper source, runtime
ABI, live core-PC, event timing, physical meaning, or code writability.

| Read | Bus start | Bytes | Exclusive end | Header, LE target/address/length |
| --- | --- | ---: | --- | --- |
| pointer neighborhood | 470002c0 | 32 | 470002e0 | 01010000c002004720000000 |
| ordinary AP_EXCO prefix | 4500ff14 | 824 | 4501024c | 0101000014ff004538030000 |
| derived AP_EXCO object | 450158a8 | 1004 | 45015c94 | 01010000a8580145ec030000 |

Source is the selected5242880-byte package with SHA256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
Root decoded ordinary row10 at FILE3ccbc+10*28 as name3dd8c,
destination2000ff14, extent33a. Therefore824bytes reads a prefix of the
826-byte object, omitting two unused trailing bytes. The read does not extend
into the next ordinary object at2001024e.

Root separately decoded FILE3c5b8 as the MULTI/AP_EXCO record whose destination
is200158a8 and extent3ec. The derived read ends exactly at that allocation's
exclusive end. No MMIO, code, flash or unallocated padding is included.

The mapper qualified in N maps these selector0 CPU RAM destinations by
adding25000000. Image1 startup uses selector0 lookups for these other objects.
The accepted O pointer window has c4=4500ff14, c8=4501024e and cc=450158a8,
matching this layout. The new helper must first retain its own32-byte pointer
response and require at least c4/cc to match before either dependent request.
Pointer disagreement is a semantic refusal in a known-ready transport phase,
not permission to substitute another address or retry.

The pointer neighborhood is inside the separately reproduced image1 initial
RAM allocation. Both ordinary/derived destination mappings have prior live
short-window reads. The new larger prefixes remain inside their positively
described allocations. All addresses and lengths are multiples of four;
there is no caller-supplied address, length or target.

The ordinary prefix covers ca/cc/ce, e0/e2/e4/e6, 10a/10c/116, 2cc/2ce,
2d0..2fc and300..306. The derived object includes0/1 and3d8. These are
sequential late samples, not an atomic event-time predicate. Even equality
between the sampled composite and derived3d8 establishes only numerical
consistency under the selected-code reconstruction.

Address review passes for this fixed read-only proposal. It authorizes no
write, code modification, threshold/protection change, reset or flash, and
does not replace independent source/runtime review.
