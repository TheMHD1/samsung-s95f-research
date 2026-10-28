# Existing per-lane eligibility gates before the RTP comparator

The selected firmware already tests two per-lane tables before calling the
ordinary packed-lane comparator. This offers a concrete next observation
without requiring an instruction detour. **Only source qualification and a
read proposal are complete here. No new table was read or changed, no helper
was implemented, and no prevention result is established.**

## Exact source path

The package is the pinned5242880-byte selected asset with SHA256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
Image1 file offset is linkedVA+0x40200. The unpacker calls root getter38fc
atbd6c and saves it inr5 atbd70. Getter38fc loads the pointer slot at
CPU0x200004e0; it does not return a hardcoded root address. The retained final
DM window has this pointer set to0x20010000.

Before each call to comparatorbbbc, all four unrolled lanes use the equivalent
source predicate:

```text
eligible = ((byte[root + 2*lane] & 1) == 0)
           and (byte[0x2000c95c + lane] == 0 or SB != 0)

SB = ((u16[0x200004aa] == 1 or u16[0x200004ac] == 1)
      and byte[0x200004cc] != 0)
```

The primary byte is the low byte of a two-byte-stride entry. Only bit0 is
tested by this gate; other bits/bytes are not established as disposable.
If that bit is set, the code skips that lane's comparator call regardless
of SB. If the bit is clear, a nonzero secondary byte skips the call unless
SB is true. This is an execution eligibility relation, without a recovered
official field name, unit or physical-pixel interpretation.

The primary gate loads arebeb4/bee6/bf22/bf64. Their conditional skip targets
arebee4/bf20/bf62/bf98, respectively, advancing to the next lane/loop tail.
The secondary loads and branches are pinned in `source-qualification.json`,
along with the corresponding comparator callsbedc/bf18/bf5a/bf90 and the
four-lane/six-packed-byte loop increment. These are ordinary pre-comparator
gates, distinct from the later difference threshold, B-band filter, record
publication limit and aggregate fault threshold.

The unpacker checks root+0x2410 operating mode before the ordinary loop;
the recovered path runs only below6. The retained Apps context has operating
mode4, aa0/ac2, xBase0,1920 lanes and2880 packed bytes. Thus its source-derived
SB is0. **Operating mode4 and record/predicate category1 are different fields.**
An initial host check incorrectly required operating mode1 and refused before
generating a proposal; inspection of the captured field and source corrected
that assumption. There was no target operation or relaxed live guard.

## Smallest new data observation

Use lanes568..635, matching the68 lanes already covered by the fixed-reference
decoder. With freshly verified root0x20010000 and xBase0, the fixed proposal is:

| Table | CPU interval start | Bus interval start | Bytes |
|---|---|---|---:|
| Primary two-byte-stride entries |0x20010470|0x47010470|136|
| Secondary lane bytes |0x2000cb94|0x4700cb94|68|

Both complete intervals fit the separately source-qualified image1 SRAM
translator bounds. The proposed target0x101 headers in `fixed-read-plan.json`
add two reads/four bulks and204 bytes to an independently reviewed bounded
capture. They are not dispatched by this audit. Runtime M/root/geometry and
R/N/reference/record context should be retained to avoid treating a later
table value as the historical eligibility at a comparator call.

This window covers the repeated fault-prefix columns and the later clean
572/573 pair. It is not a complete census of all possible qualifying lanes:
the final Apps prefix also contains562/563 outside it, and x equals lane plus
xBase modulo65536. Physical pixel/color mapping remains unknown. A future
capture must preserve that scope instead of declaring every faulting input
covered.

## Before any intervention

Trace table initialization and all relevant writers, bit meanings/lifetime,
reset/reinitialization and a checked restoration mechanism. The low bit's
source effect is positive evidence of skipping a comparator call, not proof
that setting it is an electrically safe repair. Observe the actual table
values first, and distinguish genuine eligibility changes from changed
references or scheduling. There is no proposed persistent patch here.

DX's successful64-byte code fingerprint covered the unpacker prologue, not
these later gate instructions. This body has not yet been live-fingerprinted;
source agreement and record consistency must not be promoted into proof of
historical execution. An eventual diagnostic write needs its own bounded
implementation, actual live-code/context qualifications, exact original-bit
preservation, readback, restoration and an informative control outcome. The
inconclusive earlier40→200→40 test is not evidence that lane exclusion works.

## Offline checks

`audit.py` performs91 explicit source/context checks, including exact decoded
instructions, literal pointers, prior saved-M/R hashes, operating-mode and
geometry distinction, complete interval bounds and alignment. Run it with
`PYTHONPATH=/tmp/tcon-capstone python3 audit.py --check` and the optimized
counterpart in the retained environment. The script imports no root or USB
adapter. It uses explicit exceptions under optimization and emits no raw OEM
instruction bytes. Source anchors and derived headers are research artifacts;
the raw selected asset remains private. The frozen validation and inventory
record actual results separately.
