# Corrected AP_EXCO derived-object provenance

Recorded 2026-10-27 UTC. This is a finite offline trace over the selected
firmware and retained captures. It made no TV, network, USB, controller,
device-node, helper, write, reset, UI, or configuration request. It does not
inspect protection, return/bypass paths, persistent storage, high-bank state,
POFLG, or guards.

## Result

The corrected callback object at CPU `0x200158a8` is a distinct, reset-zeroed
image-0 RAM object. The only positive object-level names recovered are the
registry pair **`MULTI` / `AP_EXCO`**. No source-backed field name or physical
unit was recovered for bytes `+0`, `+1`, or `+0x3d8`.

The finite ordinary paths establish:

| derived offset | positive initialization/update path | limit |
| ---: | --- | --- |
| `+0` | reset zero-fill; ordinary startup explicitly clears it; VA `0x3286c` stores an unnamed caller byte | caller value semantics unresolved |
| `+1` | reset zero-fill; VA `0x35b56` stores an unnamed caller byte | nine direct callers exist, but their value-selection semantics were not followed |
| `+0x3d8` | reset zero-fill; VA `0x2fb44` reads the ordinary AP_EXCO object and stores a boolean after two helper stages | no invocation record; nested targets below `0x2f980` remain unresolved |

The `+0x3d8` relationship is the important positive derivation. Function VA
`0x2fb44` obtains the derived object through getter `0xe76c` and the ordinary
AP_EXCO object through getter `0xe678`. It then:

1. unconditionally calls helper `0x2f5d8` at callsite `0x2fb52`;
2. reads ordinary halfword `+0xca` and conditionally calls helper `0x2f980`;
3. reads ordinary byte `+0xe6` and masks bit 0;
4. reads ordinary halfword `+0x2fc`;
5. stores `1` to derived `+0x3d8` if the **post-helper** values make
   `(+0xe6 & 1) OR +0x2fc` nonzero,
   otherwise stores `0`.

The `+0xca` value gates the helper call; it is not directly ORed into the
stored boolean. Helper `0x2f980` has a directly visible fall-through path at
`0x2f9b2..0x2f9b7` that clears ordinary halfword `+0x2fc`; its nested targets
`0x2f9ba` and `0x2fa38`, and the internal effects of the unconditional
`0x2f5d8` call, are the first unresolved edges. The formula therefore
describes values read after both preceding helper stages, not their inputs.

## Corrected registry object and getter

The selected package is 5 MiB with SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
For image 0, `FILE = VA + 0x200`.

The 28-byte record at FILE `0x3c5b8`, SHA-256
`41dfa8809a435830065f05cbcf22bc20ee9b0f4b4f773e3d49f02f3b04403f66`,
is:

```text
0x0003dd84  -> "MULTI"
0x0003d44b  unnamed
0x00000002  unnamed
0x0003dd8c  -> "AP_EXCO"
0x200158a8  CPU object base
0x000003ec  object extent
0x00000018  unnamed
```

Only the strings, destination, and extent are assigned meanings. Image-0
getter VA `0xe76c` is exactly:

```text
ldr r0, =0x200158a8
bx  lr
```

Its eight bytes have SHA-256
`a971931ca704d394dc4e3ea628440af003c9773be24beb079d5a66a08fefcfc0`.
This getter is distinct from ordinary AP_EXCO getter `0xe678`, which returns
CPU `0x2000ff14`.

## Reset and ordinary startup initialization

The complete selected image-0 scatter table at FILE `0x3e340..0x3e3ff` has
SHA-256
`3f09781583f48d9b429fe8438b06bbd26196b3f673c79e6a2cf7adde356b612d`.
Its final row is:

```text
source 0x3e764, destination 0x20000f4c, length 0x16438, handler 0x1d8
```

The pinned handler begins by zeroing registers, emits repeated 16-byte zero
stores, handles the bounded remainder, and returns. The row covers CPU
`0x20000f4c..0x20017383`; therefore the complete object
`0x200158a8..0x20015c93` resets to zero, including all three fields.

Ordinary startup function VA `0x398c4` directly calls sub-initializer VA
`0x333a8` at callsite `0x39b22`. The 192-byte sub-initializer has SHA-256
`d0e5c3d63a9691982e8a1d475d05260392a4b6298095baef2c5d97369f4646f7`.
It obtains the corrected object through getter `0xe76c` into `r4` and executes
an explicit zero-byte store at object `+0`. This is a positive ordinary
runtime initialization edge, separate from reset scatter.

## Direct `+0` and `+1` setters

VA `0x3286c..0x328a3`, SHA-256
`ccaae391eab8d2cda5b01f181a99308fb799ba9e93923251f3fb29a841616a9d`,
preserves its `r0` input in `r5`, gets the corrected object into `r4`, and
executes `strb r5,[r4,#0]`. Its complete direct caller set is:

```text
0x329f8  0x32a0c  0x32a2e  0x32ab6
```

The function also initializes other bytes in the object, but this bounded
trace does not assign those offsets or caller values field names.

VA `0x35b56..0x35b69`, SHA-256
`50d464ed7f82d179e974c298739548ca77b0fc698dcc6a57e79c48397d8174ce`,
preserves its `r0` input in `r4`, gets the corrected object into `r5`, and
executes `strb r4,[r5,#1]`. Its complete direct caller set is:

```text
0x35c8c  0x35cda  0x35ce4  0x35d14  0x35d1e
0x35d2a  0x35d44  0x35d66  0x35e4e
```

No adjacent literal names either byte. Following every caller's source would
expand beyond the requested finite getter/init/direct-writer pass. These are
therefore positive setter routes with unresolved value semantics, not named
Samsung settings.

## Positive ordinary-to-derived transform

VA `0x2fb44..0x2fb7b`, SHA-256
`f9b94ce545ffc142ac8cbff9d0c4f2c6bcf7146316a59dd32d49814ffb8443a7`,
has one direct caller, `0x13710`. Its exact dataflow is locally bounded:

```text
bl 0xe76c          derived object -> r5
bl 0xe678          ordinary AP_EXCO -> r4
bl 0x2f5d8         unconditional preceding helper
ldrh [r4,+0xca]    gates helper 0x2f980
bl 0x2f980         when +0xca is nonzero; may clear +0x2fc directly
ldrb [r4,+0xe6]
and  bit 0
ldrh [r4,+0x2fc]
orr
normalize nonzero to 1, else 0
strb [r5,+0x3d8]
```

This proves the derived byte is ordinarily computed from ordinary AP_EXCO
state as it exists after the two preceding call stages. It does not prove
when the function ran, what the source fields mean, or what effects the
unresolved helper internals have.

## Why the old `20/0` raw pair is not reused

The earlier accepted raw reads sampled ordinary AP_EXCO ranges:

```text
object +0x000..+0x00f
object +0x3cc..+0x3eb
```

Their immutable SHA-256 values are
`374708fff7719dd5979ec875d56cd2286f6d3cf7ec317a3b25632aab28ec37bb`
and
`f4eec86c76db591f12c003fc318c76418e9455c10f10ad2c40acf0b21010814b`.
The final positive reduction reads ordinary offsets `+0xca`, `+0xe6`, and
`+0x2fc`; the helper also directly writes `+0x2fc` on one path.
None lies in either captured range. The old windows therefore cannot evaluate
the transform and provide no basis for transferring `20/0` into this distinct
derived object. No normalization/default claim is made.

## Corrected retained sample

The later accepted corrected read retained:

```text
pointer +0x0c = 0x450158a8
derived +0     = 3
derived +1     = 10
derived +0x3d8 = 1
```

The base and tail raw SHA-256 values are respectively
`21f2234ff842c398b65210295a7a5e15220503bc73240a0eb68e4b897929db47`
and
`eb1b55a1e4f19a403134f7ddc3a4f7f3853f50ef06cb9b9e74a5659f6183323f`.
The value `1` at `+0x3d8` is numerically compatible with the identified
boolean writer. It does not prove that writer ran, which source operand was
nonzero, or when the value changed. Values `3` and `10` are compatible with
the two byte setters but do not identify their callers or meanings. The
capture is late, sequential evidence, not the V6 event instant.

## Boundary

The finite trace ends at:

- unconditional helper `0x2f5d8`, plus nested targets below helper `0x2f980`
  conditionally gated by ordinary `+0xca`;
- caller-provided values reaching the `+0` and `+1` setters; and
- possible computed or indirect writers not represented by the pinned direct
  getter/store patterns.

It does not claim a complete whole-image writer census, field names, units,
physical cause, current invocation, event-time state, active bank, or a safe
write. No excluded branch was followed merely to close completeness.

`verify-derived-object-provenance.py` pins all coordinates, slices, direct
call sets, scatter coverage, positive transform instructions, retained raw
hashes, and these explicit limits using only Python's standard library. Its
normal and optimized runs must emit byte-identical JSON with
`target_operations:0`.
