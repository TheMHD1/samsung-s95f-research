# Writer controls and the stock ordinary-gate transition

The selected source contains a stock path that can change the RTP triplet from `0/0/1` to **`0/0/0` without setting the stop or fault words**. Image0 function `0x215bc` clears the ordinary-gate halfword at RTP root+`0x240e`. The dense EO observation is compatible with that path; it does not prove which caller ran, that the controller was idle, or that physical light changed. This finding explains why treating every non-clean triplet as the same unexpected fault can terminate logging before later selector/score changes.

This is a bounded host-only audit of the selected package SHA256 `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`. Image0 file offsets are VA+`0x200`; image1 offsets are VA+`0x40200`. `source-audit.json` contains exact source-range and instruction hashes. The private disassembly is retained under `private/`. No firmware was executed, instrumented or modified. No target, root-adapter or network request was sent.

## The three publisher controls

CPU `0x200004a2` in image1 is a u16 state tested for equality to 1 by the unpacker's trainer and first primary publisher. The known coherent direct stores are:

| Writer | Effect and immediate condition |
|---|---|
| image1 `ba1e`, function `b9f4` | 0→1 when u16 CPU4a0 is 0, root+2468 is 1, and old CPU4a2 is 0. |
| image1 `ba6c`, same function | 3→1 whenever this tail is reached; this resume does not require root2468==1. |
| image1 `b776`, function `b644` | 1→3 when its first captured argument r4 is 0. Other trainer states remain unchanged on this branch. |
| image1 `b924`, function `b8a8` | 1→2 after the publication decision. If root246e!=1, the primary publication loop is skipped but this state transition still occurs. |
| image1 `c238`, function `c220` | Writes 0 after calling `cb2c`. Startup application calls this at `1ba7e`. |

Ten direct PC-literal references to CPU4a2 occur in the examined image1 interval `0..1d6a4`; the five stores above are the coherent uses of those candidates. This is not an exclusion of computed pointers, indirect copies, DMA, other CPUs or externally supplied operations. The decompressed packaged image1 startup value is 0. Runtime `cb2c` clears CPU4a0 and the counters/secondary flags, but does not itself clear CPU4a2; `c220` does that after the call.

The immediate caller chain is image1 `4446→c250→c2e6:b644`. The first call is conditional on the dispatch context's byte+0x48. `c250` derives byte CPU4d8 from `R2400==0 && R240e==1`, updates selector mirrors separately, derives CPU4d7 using R2464 and R2460, and passes CPU4d8/4d7 as the two arguments to `b644`. Thus gate-off can suppress the first argument and reach the pause branch without any R fault word being set. All these values are read sequentially, not atomically.

`b644` skips its normal body when root2460==1, but still reaches the first-argument-zero pause tail. In the normal body, its call `b6ce→b9f4` also requires both arguments nonzero, byte `[getter3a88()+2]` nonzero (getter returns CPU2000a60a), and the preceding halfword tests CPU4d2==0, CPU4b2==1, CPU4d4==0 and CPU4b0==0. Its call `b72e→b8a8` requires both compared row fields equal height−1 and both compared channel fields equal 2. This is a source condition, not proof that a complete scan, physical frame or specific exposure occurred. Raw field addresses are retained to avoid inventing human configuration labels.

Root+2460 has a positive image0 writer. Getter `ef94` returns literal **`0x47010000`**, the image1 RTP root alias. Image0 `a6ac(selector,value)` uses selector `0x30` to store the low16 of its value argument to alias+2460 at `a71e`. If reread value equals 1, `a726` additionally sets **AP_EXCO data+8** to 1; its data getter `e678` returns CPU2000ff14. The immediate caller `11a56` parses two text integers and calls this setter. That caller was inspected, not invoked or exposed as an operation route. No meaning such as a picture setting is assigned to selector0x30.

The selected AP_RTP resource descriptor at image0 VA3cc44 names data alias47012400/length100 and context alias47010000/length2400. AP_EXCO's descriptor positively names data CPU2000ff14. This supplies an actual source relationship between a selected AP_EXCO control helper and an RTP writer; it does not identify the Linux/AVE callback that chose the value.

No equally concrete direct runtime store to root+246e was resolved in this bounded audit. Its known read at image1 b8f6 controls publication at b912. It lies in AP_RTP's 256-byte parameter region, so direct writes are not the only possible delivery mechanism. The packaged root+2460, +2468 and +246e values are all zero; these are startup data values, not a promise about MODE2, persistent configuration or current runtime writers. No new persisted/high-bank route was followed.

Sampled M4a2=0 and R2460/R246e=0 establish source inactivity only at their separate reads. Root2468=0, already present in the existing R window, would additionally exclude the known **zero-to-one arm branch at that read**; it would not exclude a later writer or the 3→1 resume path. These observations support a bounded refusal/readback guard for a diagnostic, not continuous writer quiescence or safe ownership of table bits.

## Ordinary gate R+0x0e: positive non-fault source

The following functions use the same positive RTP alias getter. Stop and fault refer to root2400 and root240a; ordinary gate refers to root240e.

| Path | Exact source effect |
|---|---|
| image0 `21544`, store `21568` | If gate is exactly 0, writes 1. It does not clear stop/fault in this function. |
| image0 `215bc`, store `215fc` | If gate is exactly 1, writes 0. It does not write stop/fault in this function. Before testing the gate, it clears AP_EXCO runtime-context+74 bit28 and sets +7c bit13. On 1→0 it increments AP(e670)+204 as a u16. |
| image0 `37be8` | Second argument exactly 8 or 10 calls `21544`; every other value calls `215bc`. Immediate direct caller is `37d1e`; argument meaning is not resolved here. |
| image0 `1163c` text handler | Distinct string branches can write gate1 or gate0 (`1167c`, `116a2`, `116b6`); separate branches write stop. Not invoked. |
| image1 fault setter `c1e0` | Writes stop1, gate0 and fault1001. This path alone does not explain a stable sampled stop0/fault0/gate0. |

Direct `215bc` caller conditions examined:

- `bc02`, within bbd8: AP_EXCO data+140 nonzero and `(data+156 & 0x180)!=0`; clears +15c and sets +158 before calling.
- `bc3e`, same function: +140 nonzero, mask above equal to zero, and signed comparison +15c<=+15a. It increments +15c and sets +158 before calling. The opposite threshold branch can instead clear +158 and set runtime-context+7c bit13 without calling the gate setter.
- `c7d2`: argument object's double-dereferenced word has bit3 set. It follows several other calls including `357dc(0)`.
- `2fee2`, `32828`, `357ec`: unconditional within their small entered function bodies; invocation predicates outside those functions remain unclosed.
- `37bfc`: numeric second-argument decision described above.

For `bc3e`, both loaded values are zero-extended u16, so the signed BGE has the same ordering as unsigned comparison over that domain. The condition is based on pre-increment values. These are field-level predicates, not human descriptions such as calibration, content policy or panel protection. The source neither identifies the actual EO caller nor proves that ordinary-gate disable is harmless or stationary.

Gate setters contain optional logging through `39394`, conditional on AP_EXCO data+6c. Existing values and log routing must be qualified separately; a reader filter is not a producer enable, and this audit enables nothing. The state-changing calls themselves remain source-only logging candidates.

## Narrow custom logging points and the next observer

The most informative future diagnostic event would be at image0 gate setters `21544/215bc`, before/after the store, retaining caller LR, old/new R triplet, numeric caller argument when available, AP_EXCO runtime flags+74/+7c, and the existing source predicates. It would distinguish stock caller families before the image1 selector/score path. A second event at image1's five CPU4a2 stores would retain old/new state, R2460/2468/246e and CPU4a0. Finally, primary stores b912/c53c plus their controlling values would identify actual publication. A polling logger observes samples, not every store; a hook would still require all unresolved DS allocation, executable-write, ABI/liveness, concurrency and rollback qualifications. No hook or logging helper is implemented here.

A future read-only observer can represent `stop0/fault0/gate0` as a distinct source-compatible **Quiescent observation** while retaining unchanged protocol checks. That name must not imply CPU inactivity. It should require a full Clean baseline before sending the one Left, preserve later Quiescent rows without incrementing clean counters, and keep fault/unknown states separate. An initial Quiescent state should refuse intervention. No acceptance projection should turn the original EO refusal into a successful trial. Malformed transfers, binding drift and every other unexpected RT triplet must retain their current failure behavior. Continued sampling would test the missing temporal path; it would not retrospectively classify which gate writer ran in EO.

## Reproduction and limits

Run `PYTHONPATH=/tmp/tcon-capstone python3 -B audit.py` and its `-O` equivalent, then `python3 -B test_state_model.py` and `python3 -O -B test_state_model.py`. The audit checks 19 fixed source ranges and exact anchors, resource links, startup fields and the bounded literal census. It imports only the pinned pure scatter decoder. The small pure-state tests cover arm/pause/finish and gate transitions, not complete scheduler/cross-core behavior. No tests or report establish a complete writer census, current image execution, atomic capture, electrical safety, physical light, causal fault or fix.
