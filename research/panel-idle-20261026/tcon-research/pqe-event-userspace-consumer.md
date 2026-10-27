# PQE query-event userspace consumer — bounded offline analysis

## Result

The ARM32 `AVEMonDLSR` thread in the acquired `libave.so.0.1` is the
userspace consumer of `/dev/sdp_pqe_dp` request `0xc004510a`.  Its wrapper
passes a stack-backed 52-byte event record to `ioctl`, returns the kernel
status unchanged, and exposes only record words 0 and 1 as an event type and
value.  The thread dispatches those words **only when the return is zero**.
It calls the wrapper again immediately after each success, draining queued
records until a nonzero return; the observed `-11` (`EAGAIN`) goes back to
`poll` and does not dispatch stale stack contents.

Six event types have concrete userspace branches.  They update picture/HDR,
genre, color-booster, GSR, or dimming state.  Type 3 has a recovered route to
`QDDimming::SetObjectNumber`, a field consumed by the per-vsync Weber-gain
calculation.  That is a supported route into dimming policy.  This bounded
analysis does **not** find a direct mute or power-control call from the
consumer, wrapper, dispatch entry methods, or the recovered type-3 chain.
Deeper virtual/backend effects remain open, so that negative direct-call
finding is not proof that an event can never influence physical output.

“DLSR” is retained as a binary thread/symbol label.  Its expansion was not
recovered and is not guessed here.

## Scope and immutable inputs

This was static and offline.  No TV, device node, network, root command,
process-memory read, setter, key, service, or ioctl was invoked.

| Local artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `binaries/libave.so.0.1` | 6,657,066 | `a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777` |
| `binaries/sdp_pqe_dp.ko` | 319,518 | `2f23cf9256f2cc2b39a2e0afea7a7fc6007bffd3d5efb536aacd695ee4f3967e` |
| `tcon-research/pqe-query-event-analysis.md` | 4,064 | `8c579d30e3e9ba321b05bbbec0ae77c495f7fde03b9d52b5863f3fa46d9f71a6` |
| `overnight/capacity-20261026t1648.onset/meta.txt` | 481,703 | `6ba99636bdedc2f95b287992bae4077933e117a58be115ed323c6ece3abf15c0` |
| `overnight/capacity-20261026t1648.onset/trace` | 11,543,194 | `403d6951854ae14e312d894534a02b1fe42bb59e576ef58fe9ef8a44994058e7` |
| `overnight/capacity-20261026t1648.onset/vlog-after.txt` | 44,427,406 | `0f1a06429c6553591c657fa963dbe5aea5d4863b09affdfc4d1fadd930edb1fb` |

The library is an ELF32 ARM EABI5 shared object, Build ID
`ef063331324ca1d7a770a0590860e2c3d994d776`.  The captured installed path is
`/prd/usr/lib/libave.so.0.1`, and the capture records the same SHA-256 before
and after acquisition.

Addresses below are ELF virtual addresses unless prefixed by `A+` or called
runtime addresses.  Thumb function symbols have bit 0 set.  Thus a symbol
value such as `0x2bcfd5` begins decoding at even address `0x2bcfd4`.  A
normalized half-open byte span is `(symbol_value & ~1)` through that start
plus `st_size`.

In the 90-second capture, AVOC's zero-offset library mapping was
`0xf6b77000-0xf7103000 r-xp`, so load bias `A=0xf6b77000`.  This gives runtime
consumer address `0xf6e33fd5` and wrapper address `0xf6e28259` for that one
process.  These are historical ASLR values, not reusable constants.

## Exact consumer and wrapper

| Function | Thumb symbol / size | Normalized byte span |
| --- | ---: | ---: |
| `pthd_ave_dlsr_pq(void*)` | `0x2bcfd5` / 660 | `[0x2bcfd4,0x2bd268)` |
| `ave_pqe_dlsr_genre_info(int,unsigned*,unsigned*)` | `0x2b1259` / 116 | `[0x2b1258,0x2b12cc)` |
| `VideoEnhancerBuilder::GetInstanceEnhancer()` | `0x093a29` / 60 | `[0x093a28,0x093a64)` |

The consumer establishes its thread name with
`prctl(15,"AVEMonDLSR",...)` at `0x2bcff2..0x2bd006`.  It resolves a
`VideoEnhancer` object, calls virtual slot `+0x1cc` (`CheckNeedDlsr`), and
continues only when that returns zero.  The RoseM-family implementation at
`0x0a1e55` returns zero in this image.

It opens the exact string `/dev/sdp_pqe_dp` at ELF VA `0x5774d0` with the
literal flags value `0x00181002`.  The code only proceeds with `fd > 0`, then
uses a one-element `pollfd`, `events=1` (`POLLIN`), timeout 1000 ms.  No
semantic names are assigned here to the individual `open64` flag bits.

The event wrapper is called at `0x2bd0d0` and, on the queue-drain loop, again
at `0x2bd0f6`.  Its central sequence is:

```text
0x2b1264  sub sp,#0x38              56-byte local allocation
0x2b126a  movw r1,#0x510a
0x2b126e  movt r1,#0xc004           request 0xc004510a
0x2b1276  mov r2,r7                 record at local stack base
0x2b1280  blx 0x8d77c               ioctl@PLT
0x2b1284  ldr r3,[r7]               record word 0
0x2b1286  str r3,[caller_type]
0x2b129c  ldr r3,[r7,#4]            record word 1 for selected types
0x2b129e  str r3,[caller_value]
```

PLT `0x8d77c` resolves to `ioctl`.  The matching kernel implementation copies
a 52-byte output record.  The ARM32 request encodes the four-byte userspace
pointer width, not that record length; the extra four local bytes are the compiler's stack-canary word at
local offset `0x34`, not a 56-byte event.  The wrapper reads:

| Record offset | Width | Consumer-visible use |
| ---: | ---: | --- |
| `+0x00` | 4 | event type, copied unconditionally by the wrapper |
| `+0x04` | 4 | event value for types 0–4 and 10 |
| `+0x08..+0x33` | 44 | not read by this consumer |

The exact 11-entry Thumb jump table at `0x2b1290` is
`06 06 06 06 06 13 13 13 13 13 06`: types 0–4 and 10 copy word 1; types
5–9 and types above 10 set the wrapper's value output to zero.  This does not
establish names or layouts for the remaining 44 bytes.

Crucially, `ioctl`'s return remains in `r0`; the wrapper does not normalize
it.  At `0x2bd0d4..0x2bd0d6` the consumer compares it with zero and branches
back to polling on **every nonzero value**.  Only zero reaches the type
dispatch.  After a dispatched record, control returns to `0x2bd0ca`, calls
the wrapper again without another poll, and repeats until nonzero.  Therefore:

```text
poll readable
  -> query event
       -> return 0: dispatch type/value, query again
       -> return -11 or any other nonzero: do not dispatch, resume poll
```

The wrapper does copy word 0 before its caller checks the return, so its local
outputs may be meaningless after failure.  The caller's zero-only gate is
what makes that harmless on this recovered path.

## Dispatch table and state edges

The consumer stores type at its `sp+0x14`, value at `sp+0x24`, and `pollfd`
at `sp+0x1c`.  These are transient thread-stack locations.

| Type | Value guard in consumer | Exact virtual target | Recovered first-order effect |
| ---: | --- | --- | --- |
| 0 | `value <= 15` | VE vptr `+0x1d0`: `RoseMVideoEnhancer::SetDlsrClass(unsigned)` `0x0a3245` / 128 | If changed, updates static previous value at `0x5a8da8`, follows GOT `0x5a6a28` -> `m_pShm` storage `0x5b24e0` -> state pointer and stores value at that state `+0xb0`, then invokes vptr `+0x428` `m_SetDlsrClass()` |
| 1 | `value <= 6` | VE vptr `+0x1d4`: `AIGenreAddGenre(int)` `0x0b782d` / 26 | Stores shared VE state `+0x45404`; calls `SamPictureMonitor::AIGenreAddGenre` |
| 2 | `value <= 4` | VE vptr `+0x1d8`: `SetHDRBrightnessOptimizer(unsigned)` `0x0a32c5` / 84 | If changed, stores shared VE state `+0xec` and logs the class |
| 3 | none here | `get_dimming_instance()`, then dimming vptr `+0x1c8`: `ave_dimming::SetObjectNumber(int)` `0x152509` / 320 | Calls active dimming-panel vptr `+0x1bc`; on QD, stores object count for Weber-gain calculation |
| 4 | none here | VE vptr `+0x25c`: `AIColorBoosterAddLevel(int)` `0x0b9b3d` / 120 | Stores shared VE state `+0x4d9d0`; calls `SamPictureMonitor::CheckColorBoosterLevel` |
| 10 | none here | VE vptr `+0x268`: `SetGSRFromNPU(int)` `0x0a3aad` / 144 | Caches shared VE state `+0x4d858`; conditionally invokes another VE virtual policy edge |
| other | — | none | ignored, then queue drain continues |

The RoseM, RoseM-MNT, WALL, and EP vtables all resolve the six consumer slots
above to the same named RoseM entry methods.  The builder itself selects and
caches MNT when `get_product_type(1)` is nonzero, otherwise EP when
`get_product_type(0)==4`, otherwise base RoseM.  Static code and the generic
`RoseMVideoEnhancer.cpp` log source do not by themselves prove which subtype
was selected in the captured process.

For type 0, RoseM's vptr `+0x428` relocation resolves to
`RoseMVideoEnhancer::m_SetDlsrClass()` (`0x0ad199`, size 2100); the MNT
override is `0x10b4b5`, size 1920.  These routines reach picture/PQE register
and vendor-interface work through multiple indirect calls.  That deeper
graph was not fully recovered here, so type 0 is not promoted to a
mute/power claim.

For type 2, `SamPictureMonitor::m_SetHDRBrightnessOptimizer()` is at
`0x0dfff1`, size 308, and later reads the shared `+0xec` class.  Its bounded
body contains no direct mute or power action, but later policy consumers of
the shared state were not exhaustively enumerated.

### Type 3 reaches QD dimming policy

`ave_dimming::SetObjectNumber` uses the same exact relocated
`ave_dimming::m_pDimmingPanel` GOT slot at `A+0x5a69ec` documented by the
existing guarded QD observer map.  It invokes the active panel object's vptr
`+0x1bc`.  Both allowed QD vtables resolve that slot to
`QDDimming::SetObjectNumber(int)` (Thumb symbol `0x172d2d`, size 84):

```text
consumer type 3
  -> ave_dimming::SetObjectNumber                 0x152509
     -> active DimmingInterface vptr +0x1bc
        -> QDDimming::SetObjectNumber             0x172d2d
           -> if object+0x18 != 0:
                *(inner+0x45c) = event value      0x172d34
```

The only non-constructor read recovered for `inner+0x45c` is at `0x17940a`
inside `QDDimming::m_CalcWeberGain()` (Thumb symbol `0x1793d1`, size 236).
The object count seeds a 16-byte local block passed to an interface at
`QDDimming+0x10`, vptr slot `+0x1c4`.  On a zero return, three words produced
in that block become inputs `+0x30`, `+0x34`, and `+0x38` to a 64-byte
`ShareWeber_t` block.  The concrete producer behind `QDDimming+0x10` was not
typed in this audit; the object count is therefore a supported input to that
query, not a claimed direct Weber formula operand.

`m_CalcWeberGain` then invokes the QDDimming share object at
`QDDimming+0x8`, vptr slot `+0x90`.  The base `DimmingShare` relocation for
that slot is
`DimmingShare::t_DimmingShare_GetWebberDimming(unsigned*,ShareWeber_t*)`
at `0x237661`, size 528.  Direct callers of `m_CalcWeberGain` include
`QDDimming::t_vSyncCallBack()` (`0x17b35d`, size 864) and the MNT callback
(`0x19b1c9`, size 868).  This establishes a concrete event-to-per-vsync
dimming-policy route.  It does not establish a particular panel-duty result,
visible brightness, blackout, or causal relationship to the owner's symptom.

### Recovered Weber selection, ramp, and nearest output boundary

The input block constructed by `m_CalcWeberGain` is recoverable by offset,
without inventing field names:

| `ShareWeber_t` offset | Source |
| ---: | --- |
| `+0x00` | `inner+0x0c` |
| `+0x04` | `inner+0x460` |
| `+0x08` | `60 * (inner+0x464)` |
| `+0x0c..+0x28` | `inner+0x468`, `+0x46c`, `+0x470`, `+0x474`, `+0x478`, `+0x47c`, `+0x480`, `+0x484` |
| `+0x30,+0x34,+0x38` | words 1–3 returned through the preceding 16-byte interface block |
| `+0x3c` | `inner+0x440` |

`DimmingShare` defaults its target to 1023.  Its two nondefault selections
are exact comparisons:

```text
gate: input+4 == 1
and (input+0 is 0x00010010 or 0x0006000b, or input+0x3c == 1)

if input+0x14 < input+0x38
   and input+0x34 > input+0x1c
   and input+0x30 < input+0x24:
       target = input+0x0c; classification = 2
else if input+0x18 < input+0x38
        and input+0x34 > input+0x20
        and input+0x30 >= input+0x28:
       target = input+0x10; classification = 1
else:
       target = 1023; classification = 0
```

The classification value is used for diagnostics; the target drives the
ramp.  Three named function-local statics are exact ELF objects:

| Static | ELF VA | Historical runtime (`A=0xf6b77000`) |
| --- | ---: | ---: |
| `siWeberGain` | `0x5ad94c` | `0xf712494c` |
| `siPreTargetWeberGain` | `0x5bf6d0` | `0xf71366d0` |
| `siWeberCnt` | `0x5bf6d4` | `0xf71366d4` |

When the target changes, the count resets.  While current gain differs from
target and `count < input+8`, the routine increments count and computes, with
signed integer division at `0x2376ee`:

```text
next = current - ((current - target) * count / (input+8))
```

Otherwise it selects the target directly.  The result is clamped to
`1..1023`, stored both in `siWeberGain` and through the output pointer
`inner+0x458`.  `input+8` is `60 * inner+0x464`; this is an invocation ramp
length, not a proved number of seconds or a calibrated brightness unit.

On the ordinary base-QDDimming branch (`inner+0x38==0`, `inner+0x450!=1`,
`inner+0x188!=1`), `QDDimming::m_SetFinalDuty2D()` reads this Weber result at
`0x1743f2`, combines it with raw fields `inner+0x2a4`, `+0x98`, `+0xf8`, and
`+0xfc` using fixed-point multiply/shift arithmetic, and writes a candidate
to `inner+0xac` at `0x174438`.  Other gate branches bypass that exact Weber
calculation.  The candidate then passes existing minimum/maximum and
AutoPowerOff arithmetic before a backend request; these host scalars are not
physical luminance, voltage, or applied-state proof.

For the historically sampled active base-QDDimming backend, the already
resolved target is `DimmingBackendRoseMQD::t_Set2DFinalDuty(...)` (Thumb
symbol `0x1c6275`, size 252).  It reads the request scalar at argument `+8`.
Only when it differs from `siDimLvl` at ELF `0x5ab958` does it prewrite that
cache and issue both `ave_tcon_api_send_onecommand(0xf30000000128,...)` and
`ave_frc_write_i2c(0x42b48,value)`.  This is the nearest recovered
software-command/transport boundary.  The cache is written before either
call and has no rollback in this function; equal cache and request therefore
show requested software state, not successful transport or panel application.

## Correlation with the retained 90-second capture

The kernel-side audit pairs 4,186 completed fd-27 query calls from TID 1016
`AVEMonDLSR`: 2,093 returns of zero and 2,093 returns of `-11`.  The request
argument is consistently `0xc004510a`, and the output pointer is
`0xf44f94b8`.  The alternating successes and queue-empty returns match the
static drain loop, but do not expose the successful records' contents.

The contemporaneous AVOC map labels
`0xf42fb000-0xf44fb000` as `[tstack: AVEMonDLSR: 1016]`.
`0xf44f94b8` is inside that stack, 0x1b48 bytes below its high boundary.
It is the wrapper's per-call local record, not a static global.  Reading that
address at an arbitrary later time would be racy, can observe a subsequent
call or unrelated stack contents, and cannot reconstruct dequeued records.

The retained vlog contains 44 lines from TID 1016 in
`RoseMVideoEnhancer::SetHDRBrightnessOptimizer`, spanning kernel-time
54767.082 through 54857.840 and logging changed classes 1, 2, and 3.  That is
runtime evidence that successful records reached at least the type-2 branch.
Because the setter logs only when the class changes, 44 is a lower bound on
type-2 state changes, not a count or decoding of all 2,093 successful events.
No retained payload identifies the type/value of the other successful calls.

## Would a small read-only process-memory baseline help?

Yes, but only as contemporaneous **software-state context**, not as an event
capture or a physical-light measurement.

The transient output buffer `0xf44f94b8` is not a useful baseline target.
More stable candidates exist in this exact build:

1. Re-derive `A` from a fresh zero-offset mapping and require the installed
   library hash, boot, PID, executable, complete maps, alignment, and readable
   ranges before any read.
2. Read the builder's exact cached pointer `_ZL10poInstance` at
   `A+0x5adb5c`.  `GetInstanceEnhancer` computes that address directly at
   `0x093a2a..0x093a30`, returns it when nonnull, and otherwise stores one of
   three singleton results there.  Require the pointer to equal one of the
   three static singleton addresses, then require its allowlisted relocated
   vptr.  Candidate singleton objects are base RoseM `A+0x5b21a0`, MNT
   `A+0x5bd6f4`, and EP `A+0x5bdeac`; their vptr address points are
   `A+0x59cbf8`, `A+0x59d51c`, and `A+0x59e030`, respectively.  Follow only
   the selected object's `+0x0c` shared-state pointer.  This VE pointer is a
   different object graph from the QDDimming panel pointer and its
   `A+0x59f2e8`/`A+0x5a094c` vptrs; the two must not be substituted.
3. DLSR uses a distinct static chain: require GOT `A+0x5a6a28` to resolve to
   `m_pShm` storage `A+0x5b24e0`, dereference its range-checked state pointer,
   and read DLSR class at that state `+0xb0`.  Do not assume this pointer is
   identical to the selected VE object's `+0x0c` state pointer; report an
   observed equality only if the paired reads actually match.  The
   previous-class global is separately `A+0x5a8da8`.
4. The direct `this+0x0c` paths can sample HDR brightness optimizer at
   state `+0xec`, AI genre `+0x45404`, GSR `+0x4d858`, and color-booster level
   `+0x4d9d0`.
5. For type 3, reuse the already documented guarded chain: GOT
   `A+0x5a69ec` -> relocated global storage -> active panel -> allowlisted
   QDDimming/QDDimmingMNT vptr -> inner pointer -> `inner+0x45c` object count.
   The two allowed vptrs are `A+0x59f2e8` and `A+0x5a094c`.
6. A focused type-3 policy sample can add `inner+0x458` (current Weber
   output), `inner+0x460..+0x484` (raw policy configuration inputs), the
   three DimmingShare statics above, `inner+0xa8` and `inner+0xac` (working
   duty fields), and, only after independently revalidating the RoseMQD
   backend identity, `A+0x5ab958` (`siDimLvl`).

With the historical `A=0xf6b77000`, examples are
`A+0x5a8da8=0xf711fda8`, `A+0x5a69ec=0xf711d9ec`, and the two allowed QD
vptrs `0xf71162e8` / `0xf711794c`.  They are examples only; a future process
must derive its own mapping and pointers.  Two matching snapshots can bound
obvious races but are not atomic and cannot exclude a change away and back.
These caches also do not reveal which queue record caused a value, whether a
setter later overwrote it, or whether the panel emitted light.  A baseline is
most meaningful when time-aligned with an owner-annotated visible-to-black
transition and retained with its raw reads and guard evidence.

The most useful bounded discriminator is a time-ordered tuple, not one word:

```text
object count inner+0x45c
  -> Weber target/count/current and inner+0x458
  -> working candidates inner+0xac / inner+0xa8
  -> resolved backend requested-value cache A+0x5ab958
```

A coordinated change down that tuple would support this classifier/dimming
policy being active.  Stable policy inputs/gain/duty across an
owner-confirmed visible-to-black transition would weaken this specific
type-3 explanation.  A changed requested-value cache without a corresponding
physical result would expose a software-request-versus-output divergence.
None of those observations alone proves a panel-gate fault: other dimming,
mute, power, transport, or panel-internal paths can operate independently,
and the prewritten backend cache is not applied-state evidence.

## Unrecovered edges and claim limits

- The expansion and product meaning of “DLSR” remain unknown.
- Successful 52-byte event payloads were not captured.  Only the kernel
  dequeue result, pointer, and userspace decoder/dispatch code are known.
- Fields `+0x08..+0x33` have no recovered meaning for this consumer.
- The active VideoEnhancer subtype was not directly sampled in the retained
  trace; the exact cached pointer `A+0x5adb5c` makes a future guarded passive
  subtype read possible, while RoseM-family dispatch slot identity is
  established statically.
- Type 0's large RoseM/MNT `m_SetDlsrClass` implementations and type 10's
  conditional virtual edge contain indirect backend calls not exhaustively
  resolved here.
- A concrete dimming route is established for type 3.  No direct panel-mute,
  TCON power, service, or device-power call was found on the bounded path,
  but downstream dimming policy may still alter output gain or duty.
- Logs prove some type-2 changed-value dispatches, not the type distribution
  or values of all successful dequeues.
- Nothing in this analysis identifies the owner's blackout cause, proves a
  physical state, or constitutes a recovery/repair.

## Reproduction

The companion script hash-gates the ELF, checks 32 symbols, 12 PLT entries,
31 vtable/GOT relocations, 47 instruction landmarks, the exact wrapper jump
table and strings, the captured mapping/hash, and the 44 retained type-2
change logs.  It only reads local files:

```sh
cd ${S95F_EVIDENCE_ROOT}/panel-idle-20261026
PYTHONPATH=/tmp/tcon-capstone python3 tcon-research/pqe-consumer-reproduce.py
```

The expected terminal result is JSON with the exact library SHA, ELF32/ARM
identity, `A=0xf6b77000`, request `0xc004510a`, record size 52, and all checks
passing.  Any hash, address, instruction, relocation, map, or log-count drift
fails closed.
