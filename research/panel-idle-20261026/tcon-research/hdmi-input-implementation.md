# Samsung HDMI input implementation: callback table and bounded control paths

## Evidence boundary

This is offline static analysis of
`overnight/serdes-hdmi-input-impl-copy-20261026/libhdmi-input-control-impl-sec.so.0.1`,
29,650 bytes, SHA-256
`5f822a6f297e1d24a65ad8dd4363a1dcf43b7d15f405fa7799ddf20f01410126`.
It is an ELF32 little-endian ARM EABI5 shared object with build ID
`08ec0fc1d8bf51d6aab81b6e60a31a509d8c9daa`; its exported implementation
symbols are Thumb entries (odd symbol values).  `.text` is ELF VA
`0x11bc..0x3b90`.  Mapping symbols, not guessed linear decoding, separate
Thumb code from embedded literal pools.

The evolving source wrapper report `hdmi-backend-binding.md`, grounded in
`libhdmi-control.so.0.1` SHA-256
`067ddb8f639f8e91d02524f0820fb3a56e2d9f174d0f3f75a5dec963f7339410`,
established gated dispatch through table slots `+0x3c`, `+0x44`, and `+0x48`.
This report deliberately does not pin the mutable report filename as if its
earlier bytes were archived; it pins the source ELF identity instead.
This acquired implementation now binds those slots statically.  It does not
establish that the DSO was loaded or that the table was installed in a live
process: neither the accepted PQE baseline point sample (record SHA-256
`5c36124d0d510fff8ac5ff282cfc43c1a70854d065b76da68ad760ceb56482a4`)
nor the later quiescent-PM AVOC map point sample (metadata SHA-256
`7d6a74c59eddc39cbc7ece8480ea1d9ad1d59a13fbe56ac6b5bcd7b9ff0241c3`)
contains this pathname.  Point-sample absence does not exclude a load at
another time or use by another process.

No target, root, network, device, ioctl, getter, setter, key, or control call
was made for this analysis.

## Injection and callback-table binding

`.init_array+4` has an `R_ARM_ABS32` relocation to the exported Thumb function
`hdmi_input_control_inject` (`0x11bd`, symbol size 96).  Its code calls the PLT
binding for `hdmi_input_control_backend_data_inject` at `0x11e8`.  The latter
function (`0x3ab1`, size 224) calls
`ppi_hdmi_input_control_get_backend_data_address` at `0x3af2`; on its success
path it loads the callback-table pointer from returned storage `+4` at
`0x3afc`, calls `hdmi_input_control_impl_set_funcs` at `0x3afe`, and later
stores `0x100` in returned storage word zero at `0x3b24`.  The outer init
function does not branch on an injected status before its finishing log, so
this path is not a proof of successful live publication.

`hdmi_input_control_impl_set_funcs` is exported at odd VA `0x3955`, symbol size
348; its Thumb code is exactly `0x3954..0x3a28`, followed by a literal pool.
Resolving every PC literal through the exact `.rel.dyn` GOT relocation gives
33 four-byte callback slots from `+0x00` through `+0x80`.  The complete mapping
is retained in the saved disassembly.  Relevant entries are:

| slot | implementation | significance |
| ---: | --- | --- |
| `+0x08` | `ppi_hdmi_input_control_start_impl` | stream-on body |
| `+0x0c` | `ppi_hdmi_input_control_stop_impl` | stream-off body |
| `+0x34` | `ppi_hdmi_input_control_get_power_status_impl` | read-only input-status query |
| `+0x3c` | `ppi_hdmi_input_control_set_source_impl` | exact source-wrapper target |
| `+0x44` | `ppi_hdmi_input_control_set_foreground_impl` | exact foreground-wrapper target |
| `+0x48` | `ppi_hdmi_input_control_set_background_impl` | exact background-wrapper target |
| `+0x50` | `ppi_hdmi_input_control_set_hot_plug_impl` | separate private-control setter |

This is a relocation-backed static table identity, not a sampled live table or
a call history.

## Source callback (`+0x3c`)

`ppi_hdmi_input_control_set_source_impl` is exported at odd VA `0x35ed`,
symbol size 276; its bounded Thumb body is `0x35ec..0x36d0`.

- It reads the handle's `+8` file descriptor at `0x3602` and rejects a negative
  descriptor.
- It stores the caller's source argument at handle word `+0` at `0x3608`
  **before** submitting the ioctl.  A later ioctl failure therefore does not
  imply that this userspace cache store was rolled back.
- It loads the handle's switch-port word `+4` and calls exported
  `hdmisw_convert_switchport` at `0x3610`.  That conversion uses both the port
  and still-live source argument and returns the 32-bit value submitted below;
  its static conversion table is not evidence of which live source was used.
- It issues ioctl request `0xc0045627` at `0x365e`, with the converted word by
  address.  This is the ARM32 encoding of `VIDIOC_S_INPUT`.
- Any nonnegative ioctl return is normalized to callback return `0`; a negative
  ioctl result or negative descriptor follows a logging path returning `-1`.

Thus source selection is a concrete userspace-to-video-device control edge.
Nothing here identifies a physical panel state, SerDes state, or successful
runtime call.

## Foreground and background callbacks (`+0x44`, `+0x48`)

The two bodies are deliberately parallel:

| callback | odd symbol / Thumb code | fd field | request | private CID |
| --- | --- | ---: | ---: | ---: |
| foreground | `0x2225` / `0x2224..0x2300` | handle `+0x0c` | `0xc0185648` | `0x00a009bd` |
| background | `0x211d` / `0x211c..0x21f8` | handle `+0x0c` | `0xc0185648` | `0x00a009bc` |

`0xc0185648` is the ARM32 `VIDIOC_S_EXT_CTRLS` encoding.  Each function builds
one control under class word `0x00a00000`, count word `1`, a control size word
`4`, zeroed remaining control/data words, and a pointer to that one control.
The two routines do not forward a distinct caller scalar into the constructed
control; their distinction is the CID.  The static words alone do not justify
guessing the driver's interpretation of the size/union fields.

Both reject a negative handle `+0x0c` descriptor.  Any nonnegative ioctl return
becomes callback return `0`; a negative ioctl result or descriptor produces a
logged `-1`.  They do not read back the resulting hardware or logical state.
The names and two CIDs support a concrete notification/control edge, but do not
prove display power, panel light, mute state, or successful invocation.

## Power-, stream-, and mute-related limits

The table's `get_power_status` body (`0x243d`, size 228; Thumb
`0x243c..0x24f4`) is a query rather than a power setter.  It uses handle `+8`,
zeros a 76-byte tail after an input-index word, issues `0xc050561a`
(`VIDIOC_ENUMINPUT` on this ARM32 ABI), and on success copies the returned
status word at structure offset `+0x38` to the caller's output.  Its return is
`0` on nonnegative ioctl result and `-1` on descriptor/ioctl failure.  A status
bit's meaning still requires the matching ABI and a runtime value; none was
sampled here.

The `start` and `stop` bodies use handle `+0x0c`, an argument word `1`, and
requests `0x40045612` (`VIDIOC_STREAMON`) and `0x40045613`
(`VIDIOC_STREAMOFF`) respectively.  Each normalizes a nonnegative ioctl result
to `0` and errors to `-1`.  Stream start/stop can affect capture delivery but
is not, by itself, a module-power, SerDes-reset, mute, or panel-power operation.

There is no `mute` substring in the exact DSO and no mute-named dynamic symbol.
That bounded naming result is not semantic proof that no opaque private control
could affect sound or picture.  The DSO separately exports `set_hot_plug` and
constructs CID `0x00a00999`; this report does not reinterpret that setter as a
power or mute primitive.

## Private-CID inventory

Across every mapping-symbol-delimited Thumb span of every exported text
function, the verifier inventories straightforward same-register `MOVW` or
`MOV.W` plus nearby `MOVT` constructions in private class `0x00a0xxxx`.  It
finds these exact function/value associations:

| function(s) | CID |
| --- | ---: |
| get resolution | `0x00a00966` |
| get signal status | `0x00a00967` |
| get signal information | `0x00a00968` |
| set resolution | `0x00a0096a` |
| set PC mode | `0x00a0096c` |
| get HDCP status | `0x00a00973` |
| set hot plug | `0x00a00999` |
| is MHL connection | `0x00a0099a` |
| set multi-HDMI config and IR position | `0x00a009a3` |
| set fake resolution | `0x00a009a4` |
| get info packet | `0x00a009ab` |
| get error count | `0x00a009b2` |
| set error count | `0x00a009b5` |
| set background | `0x00a009bc` |
| set foreground | `0x00a009bd` |
| get VRR mode | `0x00a009c0` |
| get HDCP version | `0x00a009c1` |
| set latency level | `0x00a009c3` |

This is a bounded instruction-form census, not a claim that no CID can be
loaded from data, received as an argument, or synthesized by a different
instruction sequence.  The saved listing records every hit and the complete
focused bodies.

## Reproduction and remaining edges

[`hdmi-input-implementation-reproduce.py`](hdmi-input-implementation-reproduce.py)
pins the byte size/hash, ELF identity and text bounds, odd Thumb symbol
identities/sizes, mapping-symbol-delimited full decode, init-array relocation,
all 15 decoded ARM PLT veneers and their computed GOT relocation targets, all
33 GOT-backed callback slots, focused ioctl/field/return
landmarks, the bounded CID census, and absence of a mute-named export/string.
[`hdmi-input-implementation.disasm`](hdmi-input-implementation.disasm) is
exclusive-write generated and must compare byte-for-byte on ordinary and
optimized Python runs.

Unrecovered or unproved edges remain explicit:

- no sampled live binding of this implementation DSO, backend-data pointer, or
  callback table;
- no caller timeline showing source/foreground/background/start/stop use;
- no kernel implementation or private-CID semantic proof beyond the userspace
  words and standard ioctl envelopes;
- no return value, readback, power transition, SerDes transition, mute state,
  emitted light, physical onset, or causal connection to the owner's symptom;
  and
- no completeness claim for CID construction forms outside the verifier's
  bounded instruction census.
