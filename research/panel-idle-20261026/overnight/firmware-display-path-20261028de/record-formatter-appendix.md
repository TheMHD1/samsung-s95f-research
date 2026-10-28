# Additive record-formatter interpretation, 2026-10-28

This appendix preserves the initial DE checkpoint. It is a host-only source analysis of the selected official controller package SHA256 `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`. Image1 FILE = linked VA +0x40200. Exact source ranges and hashes are in `record-verification.json`. The source package is byte-identical to the official factory asset independently extracted by DF. This establishes source lineage, not a live executable hash or atomic correspondence with a sampled controller record.

The requested four arrays are **x / y / RGB / c**, using the formatter's labels. They are not four A/B amplitudes. There is a fifth **diff** array. A material correction to the incoming hypothesis is that the x offset is **u16 CPU0x200004c0**, not CPU0x4be. CPU0x4be is a separate u8 log-throttle field. The B sample is retained, but the A sample and the sign of A−B are not retained in these arrays.

| Column | CPU root offset | Conditional SRAM bus address | Store image1 VA | Exact stored value / source label |
|---|---:|---:|---:|---|
| 0 |0x1000|0x47011000|0xc666|`(lane_index + u16[CPU0x200004c0]) & 0xffff`; label x |
| 1 |0x1400|0x47011400|0xc676|low16 of dispatcher argument0; label y |
| 2 |0x1800|0x47011800|0xc686|low16 of dispatcher argument1; label RGB |
| 3 |0x1c00|0x47011c00|0xc696|B 12-bit unpacked sample; label c |
| 4 |0x2000|0x47012000|0xc6a6|low16 absolute difference of selected A and B; **zero for type6**; label diff |

The root getter0x38fc returns CPU0x20010000. DF qualified the source translator's CPU0x20000000..<0x20020000 → bus0x47000000..<0x47020000 mapping. Each array has512 u16 slots (1024 bytes), indexed by the current u32 ordinal for the selected type. A first48-entry sample would be96 bytes per column. This table identifies bounded source candidates; it does not add addresses to a frozen collector or authorize its parser to accept extra captures. The ring atCPU0x20253002 lies outside that SRAM interval, so no bus alias for its header is assumed.

## Caller and argument closure

The formatter0xc5d0 saves arg0→r7, arg1→r6, arg2→r8, arg3→sb; stack arg4→sl and arg5→r4 (type). Its literal at0xc858 labels the arguments RGB, x, y, c, diff and mode. The dataflow is:

1. Dispatcher0xb7ec saves its argument0 as row-like metadata and argument1 as channel-like metadata. The caller0xb6f2..b6fa reads these from CPU0x4d0 and0x4d4. The same orchestrator initializes those fields from selected B header halfword+6 and byte+2, and updates them from CPU0x4b4 and0x4b0 at0xb732..b748. These are exact source labels and widths; the mapping to physical panel coordinates/color order has not been independently established.
2. Ordinary branch0xb87a..b88a calls unpacker0xbd58 with r0=`*[CPU0x494]+8` (selected dynamic A payload), r1=`*[CPU0x498]+8` (dynamic B payload), r2=dispatcher argument0, r3=dispatcher argument1. Conditional branches0xb83a..b850 and0xb862..b878 substitute fixed A payload CPU0x20015000 or0x20015f10. The saved dynamic A pointer therefore does not always identify the actual A input.
3. Unpacker0xbe3a..be88 decodes the incoming r1/B bytes into a temporary u16 array. Its r0/A bytes are decoded into comparator r0 at0xbed4..bedc and the next three lane calls0xbf18/0xbf5a/0xbf90. Comparator0xbbbc receives `(A, B, lane_index, row_metadata, channel_metadata)`.
4. Comparator0xbc20..bc46 computes `abs(A−B)`. Its calls0xbc74/0xbca8/0xbcde/0xbd1e pass formatter `(B, lane_index, row_metadata, channel_metadata, absdiff_or_zero, type)`. Type4 and type1 use absdiff; type6 passes zero. The formatter does not retain the A value. Even B+diff together cannot recover signed A uniquely; mode6 gives no difference information.

This supports CB's existing term “B lanes” for the inclusive rejection band, rather than reversing A/B because the comparator uses a register also named r8. r8 in the formatter is a different saved argument from r8 in its caller.

## Publication and epoch limits

There are three different lifetimes; none supplies an atomic record epoch stamp:

- **Per dispatch:**0xb7f8..b80a zeroes the six u16 source-count slots atCPU0x2000ba40. It does not zero the six u32 ordinals or record arrays. Formatter0xc708..c718 increments the selected source count modulo65536. With ID above its configured publication bound, that increment remains reachable even though further record publication stops.
- **Ordinal reset:**0xca84..cac0 zeroes six u32 ordinals atCPU0x2000ba28 and the six u16 source counts (plus other history state). Direct checked callers include frame-end handler0xb964 and record-initialization0xcb50. This function does not erase any of the five record arrays.
- **Partial record clear:** frame-end handler0xb8a8 clears the first three512-entry arrays only when CPU0x49c is nonzero, then calls ordinal reset unconditionally at0xb964. Initialization0xcb2c calls ordinal reset and clears those same first three arrays at0xcb86..cba6, and zeroes the x-base u16 atCPU0x4c0. **Both checked clear paths leave c and diff unchanged.** Therefore a zero x/y/RGB tuple may coexist with a stale c/diff tuple. Untouched tail entries cannot be assigned to the current epoch from their bytes alone.

The frame-end handler's own message labels it “Frame end”; its orchestrator call0xb72e is conditional on row and channel tests. This proves a software phase boundary, not a physical frame timestamp. No complete reset census, indirect writer exclusion, or live scheduling proof is claimed.

Formatter0xc5f6..c604 rejects publication only when the selected ordinal is **greater than** CPU0x4ca. Thus a bound40 ordinarily allows stores at indices0..40 and leaves ordinal41; it is not a40-entry cap. The separate capacity guard0xc64c limits stores to indices<512; the ordinal increment0xc6aa..c6b8 is outside that guard. Types1,4,6 use their own ordinal slots but write the same five arrays, so changing type can overwrite the same index. No type or epoch is stored in a tuple. The nonaggregate/wait branch0xc752..c780 can subtract source count from an ordinal, another reason not to assume globally monotonic IDs. Existing CB aggregate gate1 bypasses that branch in the sampled source interpretation; that observation is not universal policy.

A sequential five-column read can tear between stores or between scan/reset epochs. A conservative future parser must retain each read's full request/reply bracket, keep raw tuples without inventing validity, and pair record reads with N ordinals/counts, mode/gates, root and descriptor state before and after. Matching brackets do not prove atomicity. A first48 sample covers indices0..47 only; it is sufficient to inspect a frozen ordinal41 candidate but cannot stand in for all512 entries or all earlier records. Current row CPU0x4b4 and descriptor previous/current fields are not a direct B ring-header read, so they cannot silently select the fixed-A branch.

## Verification and handoff

`verify_record_formatter.py` verifies90 exact-source/literal/argument/store/clear landmarks and bounded ambiguity checks in both ordinary and `python3 -O` modes. It records seven source-range hashes without publishing OEM bytes. The private disassembly is retained under0700/0600 and excluded from public metadata. There were zero TV/root/network operations and zero OEM executions.

The concrete next capture candidate, if centrally integrated and independently qualified, is five fixed96-byte SRAM record windows plus already qualified counters/mode/root/descriptor brackets. Four windows alone still identify c, but lose the retained diff. No new collector, firmware setting, log producer flag, reset, or intervention is supplied by this appendix.
