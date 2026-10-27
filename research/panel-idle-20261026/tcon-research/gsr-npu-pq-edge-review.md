# GSR-from-NPU to RoseM PQ-data edge — independent bounded review

## Result

The copied ARM32 `libave.so.0.1` contains a concrete **static** route from
`RoseMVideoEnhancer::SetGSRFromNPU(int)` to RoseM's PQ-data machinery.  When
the requested GSR class changes, a 32-bit enable word equals 1, and the class
is 1 through 5, the setter loads one of five shared words and invokes virtual
slot `+0x230` with that word and scaler path 0.  Each of the four RoseM-family
vtables in this image relocates that slot to
`RoseMVideoEnhancer::m_SetPQData(int, AVEScalerPath_k)`.

That establishes a compatible-vtable edge, not a live-object binding.  The
active video-enhancer object and its vptr have not been sampled.  In
particular, the previously sampled pointer called `P` is a different
`QDDimming` object whose vptr is `A+0x59f2e8`; it cannot be reused as the
RoseM video-enhancer object.

The selected shared word is used downstream as `iPQIndex`.  It is not a
register value, duty, brightness, or GSR strength proven by this analysis.
On the ordinary valid-index path, `m_WritePQData` calls
`TDDataLoader::SetData` through its PLT entry.  Additional gates can skip that
call, and deeper virtual/data-loader effects were not fully classified here.
Nothing in this static route establishes a power-off, mute, protection trip,
physical-black transition, or causality for the owner's incident.

## Scope and immutable input

This review is offline and read-only.  It did not contact the TV, read live
process memory, invoke an API, or alter any setting.

| Artifact | Bytes | SHA-256 / Build ID |
| --- | ---: | --- |
| `binaries/libave.so.0.1` | 6,657,066 | SHA-256 `a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777` |
| same ELF | — | GNU Build ID `ef063331324ca1d7a770a0590860e2c3d994d776` |

The file is an ELF32 little-endian ARM EABI5 shared object.  Addresses below
are ELF virtual addresses.  Thumb function symbols have bit 0 set, so their
decoded byte range starts at the even address.

| Function | Thumb symbol / size | Function-byte SHA-256 |
| --- | ---: | --- |
| `VideoEnhancerBuilder::GetInstanceEnhancer()` | `0x093a29` / 60 | `93d533f2a785dbae07c6e17ff1726b916d4a3826f4ac6c8a2c88bab4139e8bf8` |
| `RoseMVideoEnhancer::SetGSRFromNPU(int)` | `0x0a3aad` / 144 | `e4652c34c69485c43dcb008336222649982a73d840d7f95ac9148a0d29b39596` |
| `RoseMVideoEnhancer::m_SetPQData(int, AVEScalerPath_k)` | `0x0a6a31` / 392 | `9b8f507b259ff069df1e23608092a94dadcb8fb447424e6c7b9469ba2c356867` |
| `RoseMVideoEnhancer::m_WritePQData(AVEScalerPath_k,int)` | `0x0b9bb5` / 748 | `bff393fe7fe2685bd8cc01b77bb82ebeb1515994c9430aa9fc21369f9ec80847` |
| `TDDataLoader::SetData(unsigned,unsigned,unsigned)` | `0x09dca9` / 1,164 | `b692c0a2e6689134df4744ae30bdea1cd5e67f9d3dffe5bcd7accd7736f5cd48` |

## Exact GSR setter flow

`SetGSRFromNPU` treats `this+0x0c` as its shared-data pointer.  Its first
comparison is:

```text
0x0a3aac  ldr    r3,[r0,#0x0c]
0x0a3aae  add.w  r3,r3,#0x4d800
0x0a3ab2  ldr    r2,[r3,#0x58]       shared+0x4d858, previous class
0x0a3ab4  cmp    r2,r1
0x0a3ab6  bne    0x0a3abc
```

An unchanged class returns 0 without invoking the lower policy method.  For
a changed class, `0x0a3af0..0x0a3afa` reads the **32-bit** word at
`shared+0x4531c` and requires it to equal 1.  The unsigned range check at
`0x0a3b0c..0x0a3b10` accepts only classes 1 through 5.  For an accepted class
`c`, the call sequence is:

```text
0x0a3b12  r6 = c + 0x614
0x0a3b16  r1 = this->vptr
0x0a3b18  r2 = 0                  scaler path argument
0x0a3b1c  r3 = shared + 4*r6
0x0a3b20  r6 = *(r1 + 0x230)
0x0a3b24  r1 = *(r3 + 4)          *(shared + 0x1854 + 4*c)
0x0a3b26  call r6(this,r1,0)
```

Consequently the five selected shared offsets are `+0x1858`, `+0x185c`,
`+0x1860`, `+0x1864`, and `+0x1868`.  The lower functions use this selected
word as an `iPQIndex`: `m_WritePQData` passes it to
`TDDataLoader::GetTabStringLength`, `GetTabString`, and `SetData`, and its
format string labels it `PQIdx`.  The exact table contents were not sampled,
so no semantic name is assigned to any of the five entries.

After the optional call, all changed-input paths converge at `0x0a3afe` and
store the requested class to `shared+0x4d858` at `0x0a3b06`.  The lower call's
return is overwritten, and the public setter returns 0.  Disabled input and
out-of-range changed input are also cached.  This is a real software retry
boundary: a later identical class is suppressed by the initial equality
check even if the lower route was skipped or reported an error.  A later
different class can invoke it again, and a value queued by `m_SetPQData` can
still be drained by another later PQ-data call; this is not universal or
permanent retry suppression.

The constructor at `0x0cfc6c` calls `get_ave_shm` through PLT `0x08ec88`,
adds `0x9c58`, and stores that pointer at object `+0x0c` at
`0x0cfca4..0x0cfcb2`.  This supports the shared-memory interpretation of the
offsets above, but it does not identify the active runtime object.

## Vtable relation and its boundary

Under the ARM Itanium C++ layout used here, an object's vptr is the vtable
address point at symbol `+8`.  Thus object virtual slot `+x` corresponds to
relocation address `vtable_symbol + 8 + x`.  The exact `R_ARM_ABS32`
relocations are:

| Vtable symbol / size | `+0x230` target | `+0x268` target | `+0x528` target |
| --- | --- | --- | --- |
| `RoseMVideoEnhancer` `0x59cbf0` / 1,364 | `0x59ce28` → `m_SetPQData` | `0x59ce60` → `SetGSRFromNPU` | `0x59d120` → `m_WritePQData` |
| `RoseMVideoEnhancerMNT` `0x59d514` / 1,364 | `0x59d74c` → `m_SetPQData` | `0x59d784` → `SetGSRFromNPU` | `0x59da44` → `m_WritePQData` |
| `RoseMVideoEnhancerWALL` `0x59da74` / 1,448 | `0x59dcac` → `m_SetPQData` | `0x59dce4` → `SetGSRFromNPU` | `0x59dfa4` → `m_WritePQData` |
| `RoseMVideoEnhancerEP` `0x59e028` / 1,448 | `0x59e260` → `m_SetPQData` | `0x59e298` → `SetGSRFromNPU` | `0x59e558` → `m_WritePQData` |

This proves the slot relationship for these four static tables.  It does not
prove the live object's vptr was one of them at an incident.  The exact
builder at `0x093a28` caches its selected object in local ELF object
`poInstance` at `0x5adb5c`; its visible choices are MNT, base RoseM, or EP.
That pointer was not included in the prior runtime snapshots.

## Deferred queue and writer behavior

`m_SetPQData` obtains the static pointer
`RoseMVideoEnhancer::m_pShm` through GOT slot `0x5a6a28`; the corresponding
ELF BSS object is `0x5b24e0`.  It reads the word at `m_pShm+0x352f8`:

- When that word is zero, it stores the requested `iPQIndex` in a 20-word
  staging array at `m_pShm+0x35300 + 4*count`.  The count is the word at
  `m_pShm+0x35350`.  After writing slot 19 the code resets the count to zero;
  otherwise it stores the incremented count.  It then returns 0 without
  calling `m_WritePQData`.
- When the word is nonzero and count is positive, it sends staged entries in
  ascending slot order through virtual slot `+0x528`, using the scaler-path
  argument from the current invocation, decrementing the count as it goes.
  It then sends the current `iPQIndex` through the same slot.
- When the word is nonzero and count is not positive, it sends the current
  value directly through slot `+0x528`.

The virtual return at `0x0a6afc` or `0x0a6b80` is not propagated;
`m_SetPQData` returns 0 at `0x0a6a9e` or `0x0a6b82`.  Therefore the outer GSR
setter's success return and cache advance do not prove that a data-loader
write succeeded.

All four RoseM-family tables above relocate `+0x528` to `m_WritePQData`.
That function has further gates which must not be omitted:

- `shared+0x45419 != 0` returns 0 at `0x0b9d82..0x0b9d76` without a
  `TDDataLoader::SetData` call;
- a negative `iPQIndex` reaches an error return of -1;
- a null tab string also reaches an error return of -1;
- on the ordinary valid-index path, PLT `0x08d038` is exactly
  `TDDataLoader::SetData(unsigned,unsigned,unsigned)`.  Calls occur at
  `0x0b9c86`, `0x0b9ca0`, and conditionally at `0x0b9d90/0x0b9da2`.

`m_WritePQData` combines lower statuses for its own return, but
`m_SetPQData` discards that return.  This route also contains an earlier
virtual call at object slot `+0x3b0`; this review does not replace that
indirect edge with a hardware-effect claim.  Existing vlog lines naming
`m_WritePQData` show that the function runs for other PQ indices and callers;
without a correlated `SetGSRFromNPU` event or matching class/index values,
those lines are not evidence that GSR caused the write.

## Nearest bounded read-only observations

A future observation can close the live-binding and queue-state gaps without
invoking any setter:

1. Derive and guard the current AVE load bias `A` from fresh maps and the
   exact on-device file hash.  Read `A+0x5adb5c` (`poInstance`) twice around
   the other fields.  Validate the pointed object and its vptr are mapped and
   that the vptr equals one of the builder's three static address points:
   `A+0x59cbf8`, `A+0x59d51c`, or `A+0x59e030`.
2. From that validated object, read its `+0x0c` shared pointer twice and then
   paired copies of `shared+0x4531c`, the five words
   `shared+0x1858..+0x1868`, and the cached class at
   `shared+0x4d858`.  These reveal the gate, actual class-to-PQ-index table,
   and cached class; they do not reveal that a virtual call ran.
3. Independently read the pointer stored at `A+0x5b24e0`
   (`RoseMVideoEnhancer::m_pShm`) twice, validate its mapping, and read paired
   copies of readiness `+0x352f8`, queue count `+0x35350`, and the 20 staging
   words `+0x35300..+0x3534c`.  Treat count outside 0..19 or pointer/map
   changes as an incomplete snapshot.

The two shared pointers should be retained separately unless the capture
itself demonstrates their relationship; static use in these two functions
is not a license to substitute one unchecked pointer for the other.  Paired
reads are consistency evidence only, not an atomic snapshot and not proof of
physical emission.  Correlation with type-10 queue events, RoseM logs, and
owner-annotated physical state would still be required for incident-level
causality.
