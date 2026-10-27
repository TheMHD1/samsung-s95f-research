# Active RoseMQD final-duty cache lifecycle

This is exact-build, offline analysis of copied `libave.so.0.1` SHA-256
`a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777`.
No TV command, process control, memory write, network action, patch or cache
forcing was performed. Runtime had already selected `DimmingBackendRoseMQD`,
not `DimmingBackendRoseMQDMNT`; this does not substitute an MNT implementation.

## Cache identity and neighborhood

The symbol table names ELF VMA `0x5ab958` as the four-byte function-local static
`DimmingBackendRoseMQD::t_Set2DFinalDuty(...)::siDimLvl`. Its initialized data
image value is signed `-1` (`0xffffffff`). A new process image starts there,
but this does not establish the current process lifetime or panel reset state.

VMA `0x5ab948` is a compiler address anchor, not a proven C++ state object.
Its neighboring words are distinct named function-local statics:

| VMA range | Named owners |
| --- | --- |
| `0x5ab948..0x5ab94c` | `m_CheckTmOnOff` factory-temporary statics |
| `0x5ab950..0x5ab954` | `t_SetNPCDimLVL2` statics |
| `0x5ab958` | `t_Set2DFinalDuty::siDimLvl` |
| `0x5ab95c..0x5ab96c` | `t_SetQdSeneDetect` statics |
| `0x5ab970..0x5ab9a4` | `t_SetLogoDetection` statics |
| `0x5ab9a8` | `t_SetNpcLut` static |

A neighboring value change therefore does not itself invalidate final-duty
caching. Runtime cache207 belongs specifically to `siDimLvl`; it is not a
calibrated brightness, voltage, panel state, or aggregate backend state object.

## Direct recovered reference and update

The active function starts at Thumb `0x1c6274`. Its recovered direct cache
materialization uses literal `0x1c6354`, value `0x003e56be`. `add r3,pc` at
`0x1c6286` uses Thumb PC `0x1c628a`, yielding `0x5ab948`; the cache is
`r3+0x10 = 0x5ab958`.

```text
1c629a  ldr   r2,[r3,#0x10]     # read siDimLvl
1c629e  cmp   r2,r8             # candidate from input +8
1c62a0  beq   1c62ca            # equal: no transport calls
1c62ac  str.w r8,[r3,#0x10]     # mismatch: store before I/O
1c62b4  blx   ave_tcon_api_send_onecommand
1c62b8  ldr   r1,[r7]           # mutable local after first call
1c62c4  blx   ave_frc_write_i2c
1c62c8  orrs  r5,r0             # combine caller-visible results
```

The VSYNC caller branches away after final-duty without consuming its return.
This proves pre-I/O caching and equal-value suppression. It does not prove the
function ran, either call emitted a transaction, controller acceptance, or OLED
emission.

The [offline reproducer](qd-rosem-cache-lifecycle-reproduce.py) hash-checks the
ELF, symbol, data initializer, unique literal, PC arithmetic, instructions and
caller edge:

```sh
PYTHONPATH=/tmp/tcon-capstone python3 tcon-research/qd-rosem-cache-lifecycle-reproduce.py
```

## Lifecycle coverage and limits

The exact four-byte literal `0x003e56be` occurs once in the copied image, at
the known final-duty literal pool. That direct PC-relative materialization and
the complete 252-byte `t_Set2DFinalDuty` body identify one read, one conditional
store, and no reset/rollback in that body. The file initializer establishes the
new-process initial value `-1`.

This is not a global writer census. A local symbol does not exclude an
inlined/differently materialized reference, an alias/bulk store, another shared
object, runtime memory corruption, or code outside the copied build. The lack
of a reset in this body also does not prove that power, resume, service restart,
unload, or process re-exec cannot reinitialize it. No static evidence here ties
a Home tab, content density, Ugoos, Live TV, or panel damage to `siDimLvl`.

## Explicit lifecycle methods examined

The active class constructor/destructor and the vtable-selected
`t_SetDimmingCondition`, `t_InitQDDimming`, and `t_SetQdResumeData` methods
were examined alongside the final-duty routine. None contains the unique known
`siDimLvl` address-literal or a direct call to `t_Set2DFinalDuty`.

| Method | Recovered behavior relevant to lifecycle | Cache result |
| --- | --- | --- |
| Constructor `0x1c85a0` | installs RoseMQD vptr and initializes per-instance/shared-memory fields, then may call `t_GetNPCData` | no recovered `siDimLvl` reference or rearm |
| Destructor `0x1c5c54` | restores base-interface vptr and calls base destructor | no recovered cache reference |
| `t_SetDimmingCondition` `0x1c5c8c` | reads factory/configuration inputs and calls NPC-level configuration | no recovered cache reference or final-duty call |
| `t_InitQDDimming` `0x1c5eb8` | reads factory values and sends its own FRC/API setup commands, including F3:012c | no recovered cache reference or final-duty call |
| `t_SetQdResumeData` `0x1c5f48` | walks a 16-entry instance/shared table and sends selected API records | no recovered cache reference or final-duty call |

The data initializer is the only positive initialization evidence recovered for
this exact static: when a fresh `avocd` process maps the library's writable
load segment, its file-backed `.data` supplies `siDimLvl=-1`. This is a normal
process-image fact, not proof that standby/wake, a panel power transition,
`t_InitQDDimming`, or `t_SetQdResumeData` occurs or re-execs `avocd`.

The accompanying reproducer checks only that the unique known cache-literal
bytes are absent from the complete selected lifecycle bodies, and that those
bodies have no direct final-duty call. This is a bounded negative result, not
an exhaustive all-materializations analysis. It cannot rule out an indirect
caller, a differently materialized alias, an external memory writer, a dynamic
replacement, or a re-execution path not observed here.

## What a cache-after-success change would and would not do

If a future vendor/source-level change updated `siDimLvl` only after **both**
existing output calls returned success, a nonzero result from either call would
retain the old value and retry the same candidate later. It would address the
narrow verified issue: a reported failure could not pre-advance this cache and
suppress an equal-candidate retry. It could repeat the first request if it had
succeeded while the second returned an error; duplicate-command safety is not
established.

It cannot prove output success. The lower QDF route has return-zero/no-I2C gates
for suspend, command-skip, and unsuitable cached TCON state. For a different
mute-zero command there is also a PVCC-specific false-success gate. Therefore
even two zero returns can describe suppressed transport rather than controller
acceptance or visible light. Such a change would not repair an electrical
panel/TCON fault, a controller hang returning false success, an unobserved
mute/frame-mode state, or the locally damaged pixels/line.

No cache write, binary patch, forced retry loop, or monitor bypass was deployed.
A useful discriminator remains a time-aligned owner-observed transition with
cache/candidate reads and bounded transport evidence, followed by separate
review of any source-level modification.
