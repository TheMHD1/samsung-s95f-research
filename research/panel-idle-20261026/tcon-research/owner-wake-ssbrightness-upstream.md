# Retained wake `QdSsBrightness=0`: bounded upstream route

This is an offline analysis of the retained AVEMonDIM kernel row at uptime
`73137.318289`, which requested QDF screen-saver brightness zero.  It uses
only `binaries/libave.so.0.1`, SHA-256
`a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777`, and
`binaries/qdf_tcon.ko`, SHA-256
`97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63`.
The bounded instruction evidence is retained in
`owner-wake-ssbrightness-upstream.disasm`. No TV, process-memory, network,
or display-control operation was used.

## What the retained line proves

The QDF log identifies the current kernel task as `AVEMonDIM`; it proves that
the QDF screen-saver brightness routine received logical input zero and took
its lower brightness path. It does **not** identify the particular libave
caller, its object type, the returned transport result, TCON acceptance, or
emitted panel light. The retained trace has no causal physical annotation.

At QDF `QDFTcon_SetQdSsBrightness` `.text+0xec00`, input zero selects numeric
payload zero. Input one instead loads the factory scalar; inputs 101–107 map
to payloads 1–7. The lower `m_set_ss_brightness` path is the ordinary
screen-saver `F3:0xc4` command family, not a DPMS, mute, QD power-control, or
off-sensing call. Its desired-value cache `m_ss_brightness` is written even
when the lower helper reports an error, and an equal later input skips that
helper. Therefore neither a zero line nor an unchanged QDF cache proves a
successful physical change.

The previously retained visibly stable wake also contains the normal `0`/`7`
pattern. That direct counterexample prevents interpreting zero as either a
dark-screen command or a screen-on restore by itself.

## Two statically distinct upstream routes

The requested value reaches the same QDF API from at least two concrete
backend bodies. Their reachability during the retained line is not observed.

| static route | selection/cache behavior | relevance to the retained zero |
| --- | --- | --- |
| `DimmingBackendRoseMQDMNT::t_SetScreenSaver` `0x1cb2d8` | request struct `+0x10 == 0` selects logical zero; nonzero normally selects logical 107 (which QDF maps to payload 7). It caches the selected logical value at its static `+0x158` after the API call without testing the result. | A real concrete zero route, but it requires the MNT backend implementation. |
| `DimmingBackendRoseMQD::t_SetLogoDetection` `0x1c6b50` | reads FRC state through `ave_frc_read_i2c`, derives a boolean-like `sl` with `r2 <= 1`, compares it with a static desired-value cache, and calls the same API with `sl` on a mismatch. The value is then cached. | A real concrete **base RoseMQD** zero-capable route. The exact FRC result and branch execution were not retained. |

The base QDDimming vsync path is more constrained than an earlier generic
“vsync calls screen saver” description suggests. `QDDimming::t_vSyncCallBack`
at `0x17b35c` first requires nonzero `inner+0x39` and `inner+0x5c`, and
`inner+0x1b4 != 1`. It dispatches `m_SetScreenSaver` only when bit 15 of
`inner+0x18c` is set. That member then requires `inner+0x450 != 0`, a
non-null backend at `this+0x10`, and passes the stored configuration value
`inner+0x520` in request `+0x10` to virtual backend slot `+0x200`.

This matters because the accepted passive baseline resolved the active base
object/backend pair as `QDDimming → DimmingBackendRoseMQD`, not MNT. The
RoseMQD vtable address point is `0x5a152c`; its `+0x200` entry is relocation
`0x5a172c`, resolving to inherited
`DimmingBackendInterface::t_SetScreenSaver` at `0x1885b1` (a stub). The MNT
address point’s corresponding `+0x200` entry `0x5a1984` resolves to the
concrete MNT setter at `0x1cb2d9`. Thus the base `m_SetScreenSaver` call alone
does not explain this AVEMonDIM zero under the baseline-resolved RoseMQD
backend. It does not exclude an MNT instance, a changed backend, or the
separate base `t_SetLogoDetection` route at the later retained moment.

The direct-call inventory of the exact brightness API PLT entry finds four
static callers in this ELF: RoseMQD and RoseMQDMNT `t_SetLogoDetection`, MNT
`t_SetScreenSaver`, and the debug-menu function. This is a source-bounded
inventory of direct PLT calls, not a statement that no indirect or external
producer exists. The AVEMonDIM kernel task label is not sufficient to bind any
one of them.

## Read-only discriminator set for a future owner-confirmed black state

No read is requested by this report. If a separately reviewed passive sampler
is used around a confirmed state, the minimum useful distinction is:

1. Revalidate AVOC/process/library identity and read the live dimming panel
   vptr, `this+0x10` backend pointer, and backend vptr. This distinguishes the
   base RoseMQD slot-`+0x200` stub from the MNT concrete setter; it must not
   reuse old addresses.
2. For the base vsync route, retain raw `inner+0x39`, `+0x5c`, `+0x1b4`,
   `+0x18c`, `+0x450`, and `+0x520`. Those are the proved gates/configuration
   feeding its screen-saver request, not picture measurements.
3. Retain the QDF `m_ss_brightness` and factory scalar only if the module and
   mapping identity are independently pinned. They distinguish requested/cache
   values, not lower command acceptance.
4. Pair those passive values with the existing kernel record for the `F3:0xc4`
   request and the separate DPMS/mute/power markers. A lone zero must remain
   ambiguous; the real panel-power path has additional ordered markers.

This source analysis supplies no basis to force zero, force seven, write a
cache, disable screen-saver optimization, clear fault history, or treat the
damaged panel as safely recovered.
