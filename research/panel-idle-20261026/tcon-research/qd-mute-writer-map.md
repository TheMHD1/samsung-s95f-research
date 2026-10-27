# QD panel-mute writer map (offline, bounded)

## Scope and confidence boundary

This is a static analysis of exactly one copied module,
[`qdf_tcon.ko`](../binaries/qdf_tcon.ko), SHA-256
`97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63`.

No command was sent to the TV for this analysis.  “Panel mute” below means the
driver command with packed command ID `0xf30000000164` (`F3:0x164`), argument
`w1` (0 = unmute, 1 = mute), and helper-lock flag `w2 = 1`.

The inventory is complete for **statically immediate constructions of
`F3:0x164` in `.text` of this exact module**: public mute, initialization,
frame-mode, and Resume.  The immediate-constant scan also finds one read of
this command and one transport-side comparison/logging site; neither sends it.
This is not a claim about dynamically assembled command IDs, other kernel
modules, firmware inside a controller, HDMI sources, or every possible writer
in the whole TV.  The common transport accepts a runtime command ID, so that
wider claim cannot be proved with this immediate-constant scan alone.

Reproduce the bounded evidence without touching a device:

```sh
python3 tcon-research/reproduce-qd-mute-writer-map.py
```

The script hash-checks the module before emitting only the relevant windows.
The existing raw context capture is [`qd-mute-send-context.disasm`](qd-mute-send-context.disasm).

## Exact writer inventory

| Writer / call family | Direct commands | Exact static condition | `m_mute_state` at BSS+0x140 | Failure / cleanup semantics |
| --- | --- | --- | --- | --- |
| `QDFTcon_t_Tcon_SetMute` at `0xce00` | `0xceb4`: requested `w21`; `0xcf7c` and conditional `0xd008`: zero | It first compares requested state with the cache. A changed request reaches `0xceb4`; an unmute path reads back `F3:0x164` and retransmits zero at `0xd008` if the response is nonzero. Early internal guard/error paths exist before these blocks. | At `0xcecc` it writes requested `w21` even if the transport call failed. The zero path writes cache zero at `0xcf94` even if its send failed. | This is the normal requested mute/unmute API. It can claim cached success without physical success. Unmute is more defensive than mute: send zero if needed, read `F3:0x164`, then conditionally send zero again. |
| `QDFTcon_Tcon_InitDevice` at `0xf910` | `0xfea0`: zero | On this initialization route, the object field at offset `0x178` must be nonzero (`0xfdf0`) and its `m_get_temperature` call must return zero (`0xfe4c` fall-through). It then reaches the direct zero command. | `0xfeb4` writes cache zero regardless of send result. | Initialization is a separate lifecycle unmute; it is neither the public SetMute cleanup nor frame-mode cleanup, and it has no readback/retry at this site. |
| `m_tcon_set_frame_mode` at `0x10508` | `0x10584`: one; `0x1073c`: zero | It only brackets frame programming when cached `m_mute_state != 1`; then sends one, waits 50 ms, reads/programs `F3:0x160`, waits as applicable, and attempts zero in the shared cleanup. If cache is already one, it skips the temporary pair. | **No write to BSS+0x140.** This is intentionally a temporary physical mute bracket, not a logical mute-state transition. | Every normal path reached after the temporary mute funnels to `0x10718` cleanup and attempts `F3:0x164=0`; the unmute result is ORed into the function result. Mode-write/read error handling can overwrite the initial mute error. Higher callers hide this result (see below). |
| `QDFTcon_Resume` at `0x10ee8` | `0x11014`: zero | Both the direct Resume route and the returning recovery branch reach this zero write: after recovery at0x1103c, branch0x11050 returns to0x10ff0 and falls through to0x11014. The branch selector is not attributed to a user-visible setting here. | `0x11028` writes cache zero immediately after the send, regardless of transport success. | No readback/retry at this direct Resume site. The recovery branch can first run a temporary frame-mode pair at0x1103c, then this direct zero/cache-clear, assuming callees return. |
| `m_tcon_recovery_frame_mode` at `0x107e8` | Indirectly the frame-mode pair above | It reads current `F3:0x160`. If that read fails, or if reported mode differs from cached `m_tcon_frame_mode` at BSS+0x13c, it calls `m_tcon_set_frame_mode(cached)`. If equal and readable, it returns without a mute command. | It does not itself change BSS+0x140. The delegated frame helper likewise does not. | Returns the delegated helper's result, but several upstream callers then discard it. It is an indirect lifecycle source of a temporary mute/unmute only if its mismatch/read-failure condition is true and cache is not logically muted. |

## Recovery callers discovered in this module

The direct callsites to `m_tcon_recovery_frame_mode` are finite in this module:

| Callsite | Function family | What is established |
| --- | --- | --- |
| `0x10cd4`, `0x10ddc` | `QDFTcon_MonitorTemperatureSensor` | Both can request recovery frame-mode handling. |
| `0x1103c` | `QDFTcon_Resume` | Resume recovery branch, followed by the direct zero at0x11014 through branch0x11050→0x10ff0, assuming callees return. |
| `0x11930` | `m_set_power_control` | Power-control lifecycle can request recovery frame-mode handling. |
| `0x121d4` | `QDFTcon_SetElSensing` | EL-sensing lifecycle can request recovery frame-mode handling. |
| `0x13be8` | `QDFTcon_SetOffSensing` | Off-sensing lifecycle can request recovery frame-mode handling. |

Each of these is an *indirect* writer only under the recovery helper's actual
`F3:0x160` read-failure/mode-mismatch condition and the frame helper's
`m_mute_state != 1` condition.  The labels establish driver subsystem families,
not that any one event occurred during the observed blackout.

There is no direct `bl 0xce00` call in this module's `.text`.  The normal
`SetMute` entry is exported and is therefore expected to be reached through an
operation table or by another module.  This audit maps the complete local
implementation reached once that public entry is called; it does not invent an
unproven list of external API callers.

## Cached-success propagation

The frame-rate route makes a physical failure especially easy to hide:

1. `QDFTcon_SetVRRFrameRate` (`0x112c0`) stores the raw requested rate to BSS+0x134 before it asks frame control to change mode, then returns zero unconditionally.
2. `m_tcon_set_frame_control` (`0x11058`) stores selected frame mode to BSS+0x13c before calling `m_tcon_set_frame_mode`, ignores that function's result, and returns zero.
3. Thus an upstream NewHome/VRR caller can receive success while the temporary unmute (or the mode programming) failed physically.  This does not prove it did fail on the TV; it proves the error can be masked by this path.

The normal public `SetMute` also advances BSS+0x140 after send attempts rather
than only after confirmed readback.  Therefore the logical cache is not proof
of actual panel state.

## Evidence that would discriminate the next capture

Do not infer causation solely from a black screen.  A capture spanning one
controlled transition needs, in timestamp order:

- kernel/driver messages identifying `F3:0x164` transmit and its return code;
- `F3:0x160` reads/writes and the returned current mode;
- `QDFTcon_t_Tcon_SetMute`, `m_tcon_set_frame_mode`,
  `m_tcon_recovery_frame_mode`, and `QDFTcon_Resume` entry/return plus the
  values of BSS+0x140, +0x13c, and +0x134;
- the caller identity/PID already available in the transport's special
  `F3:0x164` logging branch, plus a monotonic timestamp;
- any panel/TCON, display-link, PM, I2C/SPI, or compositor errors in the same
  time window; and
- observation that audio continues while the physical panel is black.

Useful interpretations:

- `F3:0x164=1` without a successful later zero points to a software mute
  bracket/recovery failure.
- No `0x164` traffic but a black panel shifts attention away from this finite
  writer set toward panel/TCON hardware, transport, power, or firmware.
- A zero send with a nonzero transport return followed by cache zero proves the
  driver's cached state is unreliable for that event.
- A recovery call with an `F3:0x160` mismatch ties the event to the frame-mode
  path; a matching readable mode excludes that recovery helper invocation as a
  source of a mute pair.

No persistent workaround is recommended from this evidence alone.  The panel
damage and the symptoms warrant a read-only correlation capture before any
low-level power or gate modification.

## Independent review corrections

Resume recovery and direct unmute are sequential on the recovery branch, not
exclusive alternatives. Also, an attempted zero can be suppressed by the
PVCC guard or the helper's broader suspend/command-skip/TCON-state gates while
returning zero. See [transport findings](qd-command-transport-failure.md).
No I2C emission can be inferred solely from a static callsite or return0.
