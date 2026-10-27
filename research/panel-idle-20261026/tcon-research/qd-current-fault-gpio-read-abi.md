# QD current ERR_DET GPIO read: ABI and side-effect boundary

This is an offline reconstruction of the stock ERR_DET fault getter. It does
not access the TV, open a device, issue an ioctl, request a GPIO, or change any
driver state. Its purpose is to decide whether one future, ordinary stock query
while the panel is physically black can add evidence beyond the historical
userspace monitor latch.

## Result

One query is technically usable as a **current raw-GPIO diagnostic**, with
strong qualifications:

* It uses the same ARM32-compatible 16-byte ioctl ABI as the already reviewed
  error-status query, but operation word0 is `0x1d` and returned word1 is a
  signed raw GPIO value.
* It enters the public kernel request path directly, so it does not consult the
  AVE monitor's historical `qd_tcon_off` latch or its retry counters. It also
  does not clear, rearm, or update that latch or those counters.
* It is not passive. On its powered/provider-success path it temporarily
  requests the ERR_DET GPIO, changes it to input direction, reads the raw
  value, and frees it. First use can also resolve and cache the DT GPIO number.
* The reviewed bodies contain no TCON power, runtime-PM, reset, recovery,
  sensing, acknowledgement, or controller-command call. Opening the character
  device has a no-op driver open callback and no driver release callback.
  Generic VFS/module accounting still applies. `gpio_request` is a resource
  ownership/allocation operation and the direction call is a GPIO state
  mutation; this route must not be described as a passive read.
* A successful output zero is ambiguous: QDF writes zero and returns success
  without reaching the provider when its cached TCON-power state is zero. A
  provider sample of raw-low also produces zero. Consequently zero cannot be
  reported as a healthy line or proof that hardware was sampled.
* A nonzero word is not automatically an electrical assertion. The QDF debug
  override can replace the output, and the lower provider ignores the return
  from `gpiod_direction_input` and copies the signed return from
  `gpiod_get_raw_value_cansleep`. A signed-negative raw-read error can therefore
  be returned with ioctl status zero and looks nonzero to the stock monitor.

This query is distinct from operation `0x1f`, whose observed value `0x10` is
the controller status bit labelled `RT Protect` by this AVE build. Operation
`0x1d` does not read that F3 status word or expand what `RT Protect` means.

## Exact sources

| File | SHA-256 | Role |
| --- | --- | --- |
| `binaries/libave.so.0.1` | `a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777` | ARM32 wrapper |
| `binaries/tztv_frc_tcon.ko` | `aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd` | character device and GPIO provider |
| `binaries/tztv_frc_tcon_api.ko` | `3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6` | 16-byte copy and operation dispatch |
| `binaries/qdf_tcon.ko` | `97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63` | cached-power gate, provider and debug selection |

AVE addresses below are ELF virtual addresses; module addresses are offsets in
their named ELF sections. They are not live addresses. The matching
[offline reproducer](qd-current-fault-gpio-read-abi-reproduce.py) hash-gates
these files and checks selected symbols, instructions, relocations, jump-table
arithmetic, and call inventories. It is a bounded landmark/dataflow check, not
an emulator or live callback-pointer proof.

## Userspace and compat ABI

The ioctl request is `0xc010749f`: read/write direction, encoded size16,
type`0x74`, number`0x9f`. The ARM32 AVE function
`ave_tcon_get_err_det_fault(int *)` has symbol value `0x25d01d`, size164, and
Thumb body starting at `0x25d01c`. It initializes request words0/1 to
`{0x1d, 0}`, calls `tcon_ioctl`, copies request word1 to the caller, and only
then checks the signed ioctl return.

A controlled one-shot diagnostic should use four little-endian `uint32`
words:

```text
[ 0x0000001d, 0xa55a5aa5, 0x00000000, 0x00000000 ]
```

Word0 is the operation. Word1 is an output sentinel; words2/3 are opaque and
must remain zero. The managed helper must require ARM32, little endian,
pack4/size16, and word1 offset4 before opening the device. It should record the
four words before and after, open/ioctl/close results and errno separately,
and make exactly one call with no retry. Preserve word1 in both unsigned hex
and signed-int32 form.

`tztv_frc_tcon.ko`'s `fop_tcon_open` at `.text+0x26a8` is only
`mov w0,#0; ret`. Its exact 264-byte fops object at `.rodata+0x890` has
relocations only for owner, native ioctl, compat ioctl, and open; all other raw
slots are zero. The ARM32 compat route passes `(request,user_pointer,1)` to the
same dynamically resolved API callback used by the native route.

The API copies exactly 16 bytes from userspace, dispatches by word0, and copies
the same 16 bytes back. Operation `0x1d` resolves to `.text+0xf198`, loads
interface slot `+0x3d0`, and passes `request+4`. QDF init statically registers
`QDFTcon_GetErrDetFault` into that slot. If the API table or callback is
missing, this case returns zero without changing word1; the sentinel is
therefore necessary.

## QDF outcome matrix

`QDFTcon_GetErrDetFault` is `qdf_tcon.ko:.text+0x5608`, size284. Its bounded
dataflow is:

| Condition | ioctl-facing status | output word | What was sampled |
| --- | ---: | --- | --- |
| API callback was never reached | `0` | sentinel unchanged | nothing demonstrated |
| cached `m_tcon_power_state` at BSS`+4` is zero | `0` | `0` | provider not called |
| provider pointer absent | `-1` | normally `0` | no GPIO sample |
| DT lookup or `gpio_request` fails | negative | normally `0` | no fresh raw value |
| provider returns0 | `0` | raw signed word | raw-read call occurred |

On every powered path, if `m_err_debug` at BSS`+0x28` equals exactly1, QDF
replaces the output with `m_err_det_debug_status` at BSS`+0x11c`. This happens
even after a provider error, although the negative status remains negative.
No override value was read for this static audit.

The minimum honest result classification is therefore:

1. Negative ioctl result: failed; preserve payload and errno but do not call
   word1 a current line state.
2. Ioctl zero with sentinel unchanged: no kernel callback output was shown.
3. Ioctl zero with word1 zero: kernel output was written, but cached-power skip
   and sampled raw-low are not distinguishable from the payload alone.
4. Ioctl zero with word1 one: consistent with a raw-high sample only if the
   exact raw-result log and absence of the debug override are independently
   established.
5. Ioctl zero with any other nonzero/signed-negative word: retain it as a raw
   or debug/error word; do not reduce it to “fault asserted.”

The provider uses `gpiod_get_raw_value_cansleep`, not a polarity-normalizing
consumer getter. This audit does not map raw high/low to connector voltage or
claim that raw high necessarily means panel damage.

## Exact provider side effects

The lower provider is `_tztv_frc_tcon_read_err_det_status` at
`tztv_frc_tcon.ko:.text+0x1af0`, size316:

1. It reads a cached GPIO number at `.data+0xa0`. A negative value triggers a
   lookup of DT property `samsung,err_det` from the stored platform-device
   node and writes the result back to `.data+0xa0`.
2. It calls `gpio_request(gpio,"err_det")` and preserves that return status.
3. On request success it calls `gpio_to_desc`,
   `gpiod_direction_input`, `gpio_to_desc` again, and
   `gpiod_get_raw_value_cansleep`.
4. It stores that last signed return through the caller pointer, calls
   `gpio_free`, and returns the earlier `gpio_request` status.

The direction-input result is discarded. The raw-read result does not become
the provider status. Thus a request-success/read-error combination can appear
as `(ioctl=0, word1=negative)`. The exact body also calls logging helpers, but
no power, PM, controller, recovery, reset, clear, sensing, or acknowledgement
function appears in its relocation-backed call inventory.

First-use DT cache mutation, GPIO ownership, direction change, and release are
the complete direct mutations recovered in this bounded body. Transitive
generic GPIO-core/provider behavior is not closed by these four vendor ELFs.

## Scope for one future query

One deliberate call while the owner freshly reports the panel physically
black can answer a narrow question: did this stock path produce a raw/debug
word at that time, and what was the signed word? It cannot by itself establish
controller health, panel emission, polarity, the cause of the blackout, or
that the line was sampled when output is zero.

Correlate the result with exact same-process kernel logs when available. Keep
the existing historical latch/counters and the operation`0x1f` controller
status as separate evidence. Do not use this getter automatically to trigger
reset/recovery and do not loop or retry it.

Reproduce offline:

```sh
PYTHONPATH=/tmp/tcon-capstone \
  python3 tcon-research/qd-current-fault-gpio-read-abi-reproduce.py
```

