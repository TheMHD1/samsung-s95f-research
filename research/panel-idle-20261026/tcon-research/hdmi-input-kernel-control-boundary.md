# HDMI input handle and kernel-control boundary

## Result and evidence boundary

This offline analysis closes one static device-association question without
claiming a live binding.  The input implementation has two distinct file
descriptor fields:

- handle `+8`, used by `set_source`, is caller-provided or falls back to
  opening `/dev/video28`;
- handle `+0x0c`, used by `set_foreground` and `set_background`, is
  caller-provided or falls back to `/dev/video21` or `/dev/video22`, selected
  by handle word `+4`.

The copied `tztv_hdmi_switch.ko` requests V4L2 video minor 28 at probe.  That
numeric match makes `/dev/video28` the expected switch endpoint when the
registration succeeds at the requested minor, but it is not a live device-node
or open-file proof.  In particular, the foreground/background fallback paths
do **not** open that requested minor.  A caller can override either fallback
with a nonnegative descriptor, and the copied evidence does not identify the
descriptor supplied for an actual handle.

If—and only if—a foreground/background extended-control request is routed to
this exact switch module, the module's branch table sends both private CIDs
`0x00a009bc` and `0x00a009bd` to the default return `-22` (`-EINVAL`).  This is
not evidence that the input DSO is unused, that those callbacks fail on their
actual device, or that an observed UI/source action reaches the proprietary
HDMI power path.

No target, root, network, device, open, ioctl, getter, setter, key, control, or
display action was performed.

## Exact inputs

| artifact | bytes | SHA-256 |
| --- | ---: | --- |
| `overnight/serdes-hdmi-control-copy-20261026/libhdmi-control.so.0.1` | 415,124 | `067ddb8f639f8e91d02524f0820fb3a56e2d9f174d0f3f75a5dec963f7339410` |
| `overnight/serdes-hdmi-input-impl-copy-20261026/libhdmi-input-control-impl-sec.so.0.1` | 29,650 | `5f822a6f297e1d24a65ad8dd4363a1dcf43b7d15f405fa7799ddf20f01410126` |
| `binaries/tztv_hdmi_switch.ko` | 87,934 | `11d9c53a0e08300bb12b1cafd513e3fc6ee84ba1bcd434007e459dce70fa82b6` |

The already reviewed [input implementation report](hdmi-input-implementation.md)
(SHA-256 `c004182e13e96fe4846b5445afd5864ea7b61e51f4bed8d31b0c76b92cf00c07`)
binds callback-table slots `+0x3c`, `+0x44`, and `+0x48` to source,
foreground, and background respectively.  Its source DSO was absent from the
two cited AVOC map point samples; that point-sample absence neither proves the
DSO is unused nor excludes another process or time.

## Wrapper-to-implementation handle construction

The exported wrapper `ppi_hdmi_input_control_create_handle` has odd Thumb
symbol VA `0x47e61205`, size 328.  Its bounded code is
`0x47e61204..0x47e6130c`; the remaining symbol bytes are literals.  It:

1. preserves its four incoming register arguments in `r6`, `r7`, `r8`, and
   `r5` (`0x47e61208..0x47e61210`);
2. allocates 16 bytes (`0x47e61248..0x47e6124a`, with the PLT veneer at
   `0x47e33854` relocation-bound to `malloc`);
3. initializes all four words to `-1` (`0x47e6124e..0x47e61258`);
4. obtains the dynamic input-backend table through the PLT veneer at
   `0x47e33890`, relocation-bound to
   `ppi_hdmi_input_control_get_backend_data`; and
5. calls table slot zero with the allocated handle in `r0`, the first three
   original arguments in `r1..r3`, and the original fourth argument as the
   fifth stack argument (`0x47e6127a..0x47e6128a`).

Thus the implementation receives two pointer-like provisioning arguments: its
register argument `r3` and fifth stack argument.  The wrapper does not itself
choose their descriptor values.  It discards the slot-zero callback return and
returns the allocated handle (`0x47e612da`).  This describes static argument
flow, not an observed caller or a valid live backend table.

## Implementation fallback split

`ppi_hdmi_input_control_create_handle_impl` is odd Thumb symbol VA `0x3441`,
size 316.  Local mapping symbols delimit executable Thumb bytes
`0x3440..0x354c` from the following literal pool.  The function copies its
first two logical values into handle words `+0` and `+4` at `0x3498`, then
handles the descriptors independently.

For handle `+8`, it dereferences register argument `r3`:

- a value other than `-1` is copied directly to handle `+8`
  (`0x349c..0x34a2`);
- a value of `-1` takes `0x350c..0x353a`, calls relocation-proved `open64`
  with pathname `/dev/video28` and flags `0x802`, writes the returned value
  back through that pointer, then stores it at handle `+8`.

For handle `+0x0c`, it dereferences the fifth argument:

- a value other than `-1` is copied directly at `0x34a4..0x34ae`;
- a value of `-1` tests handle word `+4` at `0x34b6..0x34be`.  Value `1`
  selects `/dev/video22`; all other values select `/dev/video21`.  Each path
  calls the same relocation-proved `open64` veneer with flags `0x802`, writes
  the result back through the caller's pointer, and stores it at `+0x0c`.

The three path literals are unique in the exact DSO at VAs `0x42d8`, `0x4310`,
and `0x4320`; their PC-relative loads are resolved in the verifier, rather than
assigned from nearby strings.  An `open64` failure is retained as a negative
descriptor; this create body itself returns zero.  That does not turn a later
callback into success: the callback bodies separately reject negative handle
descriptors and normalize a negative ioctl result to `-1`.

The reviewed implementation report proves that `set_source` reads handle `+8`,
whereas foreground/background read `+0x0c`.  Consequently, the static
`/dev/video28` fallback belongs to source selection, not to the two
foreground/background CIDs.

## Switch endpoint and conditional CID behavior

In `hdmi_switch_probe`, `.text+0x3998`, the call at `0x3ab4` has an exact
`R_AARCH64_CALL26` relocation to `__video_register_device`.  Immediately
before it, `w1` is zero and `w2` is `0x1c` (28) at
`0x3a7c..0x3a80`; the returned status is tested at `0x3ab8..0x3abc`.  This is a
request for minor 28, not proof that a live registration succeeded at that
number, that `/dev/video28` had the expected node identity, or that any process
opened it.

The module publishes `hdmi_switch_vidioc_s_ext_ctrls` through its ioctl-ops
table (`.data+0x288` relocation to `.text+0x23c0`).  That callback checks class
`0x00a00000`, requires nonzero count, and calls local
`hdmi_switch_set_ctrl` at `0x246c`.  The latter computes CID base
`(0xa00 << 12) + 0x998 = 0x00a00998`, range-checks its table index, and
dispatches through signed halfwords based at `.rodata+0`.

The two input-implementation CIDs produce these exact indices and destinations:

| callback CID | index from `0x00a00998` | table halfword | destination | result |
| ---: | ---: | ---: | ---: | ---: |
| background `0x00a009bc` | `0x24` | `10` | `.text+0x1650` | `-22` |
| foreground `0x00a009bd` | `0x25` | `10` | `.text+0x1650` | `-22` |

At `0x1650`, the module executes `mov w20, #-0x16`, copies it to return
register `w0`, restores the frame, and returns.  The adjacent switch-specific
suspend/resume controls are instead indices `0x26/0x27` (CIDs
`0x00a009be/bf`) and lead to different cases.  Similar numbering is not route
equivalence.

This default-return fact applies only after the V4L2 framework routes the exact
request to this switch module.  The fallback foreground/background descriptors
name video minors 21/22, while this module requests 28.  A caller-supplied
nonnegative `+0x0c` descriptor could point elsewhere—including, in principle,
the switch endpoint—but no acquired caller body, runtime handle, fd target, or
ioctl trace proves that binding.

## Reproduction and remaining edge

[The offline verifier](hdmi-input-kernel-control-boundary-reproduce.py) pins all
three source hashes/sizes and ELF classes; symbol values/sizes; exact Thumb and
AArch64 decode coverage; wrapper register/stack argument flow; `malloc`,
backend-data, and `open64` PLT/GOT relocation identities; pathname literals and
PC-relative resolutions; the switch ioctl-ops and registration relocations;
the extended-control route; and both signed-halfword dispatch entries.  It
exclusive-writes or byte-compares
[the saved listing](hdmi-input-kernel-control-boundary.disasm).

```sh
PYTHONPATH=/tmp/tcon-capstone python3 tcon-research/hdmi-input-kernel-control-boundary-reproduce.py
PYTHONPATH=/tmp/tcon-capstone python3 -O tcon-research/hdmi-input-kernel-control-boundary-reproduce.py
PYTHONPATH=/tmp/tcon-capstone python3 -m py_compile tcon-research/hdmi-input-kernel-control-boundary-reproduce.py
```

The unresolved edge is the actual create caller and its two descriptor-pointer
values, followed by a live handle/fd-to-driver binding.  Until that exists, the
static fallback split must not be converted into a claim that the generic input
DSO is active, unused, supported, unsupported, or connected to private PM,
picture loss, sound, mute, panel power, or physical light.
