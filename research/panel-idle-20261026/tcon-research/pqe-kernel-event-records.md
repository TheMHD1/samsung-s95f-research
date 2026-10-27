# PQE kernel event records returned by `QUERY_EVENT`

## Scope and exact input

This is an offline instruction and relocation audit of the matching acquired
module:

- `binaries/sdp_pqe_dp.ko`
- size: 319,518 bytes
- SHA-256: `2f23cf9256f2cc2b39a2e0afea7a7fc6007bffd3d5efb536aacd695ee4f3967e`
- GNU build ID: `1d4424027efcce137710a64fbc7e19485e798290`
- ELF: AArch64 relocatable object; `.text` is at file offset `0x80`

Addresses below are unrelocated `.text` offsets. Add `0x80` for their file
offsets. No TV call, ioctl, register access, or patch was performed.

## Shared queue and the 52-byte userspace ABI

`get_pqe_data` (`.text+0x310`) resolves to `g_pqe_data` at `.bss+0x60`.
All six producers below pass `g_pqe_data+0x27150` to `_queue_push`. The query
uses the same object through relocations at `0xfb4/0xfb8` to
`.bss+0x271b0`, which is also `g_pqe_data+0x27150`.

The queue layout proven by `_queue_init`, `_queue_push`, and `_queue_pop` is:

```text
queue + 0x00000  s32 producer index (initially -1, then 0..999)
queue + 0x00004  s32 consumer index (initially 0, then 0..999)
queue + 0x00008  1000 records, 0xa0/160 bytes each
queue + 0x27108  spinlock used by push/pop
```

`_queue_push` (`0x1c38`, file `0x1cb8`) copies exactly `0xa0` bytes from its
record argument and advances/wraps the producer index at 999. `_queue_pop`
(`0x1cc8`, file `0x1d48`) copies exactly `0xa0` bytes into its caller's
buffer and advances/wraps the consumer index. It returns `-2` when the
producer index is still `-1`, `-11` when the producer and consumer indices
are equal, and zero after a copy.

`_query_event` (`0x0fa0`, file `0x1020`) allocates a 160-byte local record at
`sp+0x20`, calls `_queue_pop` at `0x0fbc` (named `R_AARCH64_CALL26`), and
calls `__arch_copy_to_user` at `0x1054` (named `R_AARCH64_CALL26`) with a
literal length of `0x34`, or 52 bytes. It returns the saved `_queue_pop`
result; it does not use the copy-to-user return as its result. Native ioctl
`0xc008510a` reaches it at `0x1150`; the ARM32 compat ioctl observed in the
trace, `0xc004510a`, reaches it at `0x1834`.

For a successful pop of a record made by any of the six named producers, the
52 user-visible bytes are therefore:

```text
bytes  0..3   producer tag, little-endian u32
bytes  4..7   producer-specific payload, little-endian u32
bytes  8..51  no defining store in the named producer before its 160-byte copy
```

That last row is a code fact, not a claim that the bytes have any particular
runtime value. Each producer allocates exactly a 160-byte record area in its
stack frame and explicitly defines only its first eight bytes before passing
it to `_queue_push`; there is no memset. The remaining bytes come from prior
stack contents unless a build/runtime mechanism outside these instructions
initializes them.

There is a second boundary on empty/error returns: `_query_event` does not
initialize its own local record before `_queue_pop`, and still reaches the
52-byte copy for a valid userspace destination after `_queue_pop` returns
`-11` or `-2`. Consequently, on those returns even bytes 0..7 are not a fresh
event. This static path is a potential stack-data exposure, but actual bytes
were not captured and no claim is made about their values. Callers must use
the ioctl return before interpreting the record.

## Producer tags and payloads

The first word is established as a producer discriminator by six independent
named producers: each writes a distinct constant at record offset zero and a
producer result at offset four immediately before calling the same
`_queue_push`. No type declaration or formal C enum survived in the ELF, so
the table calls these values **tags**, not recovered source enum names.

| producer | `.text` / file offset | record local | tag at +0 | payload at +4 |
|---|---:|---:|---:|---|
| `_dlsr_queue_event` | `0x95b8` / `0x9638` | `sp+0x10` | `0` | raw word from `g_pqe_data+0x9c6f4` |
| `_gsr_queue_event` | `0x95e8` / `0x9668` | `sp+0x10` | `10` | raw word from `g_pqe_data+0x9c728` |
| `_genre_queue_event` | `0xc5f0` / `0xc670` | `sp+0x50` | `1` | computed genre result `0..6`, also stored at `g_pqe_data+0x138eec` |
| `_hdr_classifier_queue_event` | `0xf928` / `0xf9a8` | `sp+0x70` | `2` | computed HDR class `0..4`, also stored at `g_pqe_data+0x160074` |
| `_object_count_queue_event` | `0xff18` / `0xff98` | `sp+0x20` | `3` | low eight bits of the word addressed by the pointer at `g_pqe_data+0x1871f0` |
| `_ai_color_booster_queue_event` | `0x104d0` / `0x10550` | `sp+0x20` | `4` | low 24 bits of the word addressed by the pointer at `g_pqe_data+0x298cc8` |

The decisive stores/calls are:

- DLSR: `stp wzr,w2,[sp,#0x10]` at `0x95d8`; `_queue_push` relocation
  `0x95dc`.
- GSR: `mov w3,#10`, `stp w3,w2,[sp,#0x10]` at `0x95f8/0x960c`;
  `_queue_push` relocation `0x9610`.
- Genre: `str w1,[sp,#0x50]` with `w1=1` at `0xc620..0xc62c`, result
  `str w25,[sp,#0x54]` at `0xc720`, and `_queue_push` relocation `0xc724`.
- HDR classifier: `str w22,[sp,#0x70]` with `w22=2` at
  `0xf95c..0xf968`, selected result `str w22,[sp,#0x74]` at `0xfa88`, and
  `_queue_push` relocation `0xfa8c`.
- Object count: `str w1,[sp,#0x20]` with `w1=3` at `0xff44..0xff48`,
  low-byte result `str w1,[sp,#0x24]` at `0xff64..0xff68`, and
  `_queue_push` relocation `0xff88`.
- AI color booster: `str w1,[sp,#0x20]` with `w1=4` at
  `0x104fc..0x10500`, low-24-bit result `str w1,[sp,#0x24]` at
  `0x1051c..0x10520`, and `_queue_push` relocation `0x10540`.

These mappings identify how a successfully captured record can be decoded.
The existing syscall trace contains only the ioctl argument pointer and
return, not the pointed-to 52 bytes, so none of its successful dequeues can
yet be assigned to one of these producers.

## Direct side effects of the producer paths

The queue operation itself mutates only queue memory and the consumer query
advances its queue index. The named paths divide into three bounded groups:

- `_dlsr_queue_event` and `_gsr_queue_event` call only `get_pqe_data` and
  `_queue_push`. They load one state word and enqueue it. They contain no
  register write, panel-power, mute, brightness, or backlight call.
- `_object_count_queue_event` and `_ai_color_booster_queue_event` bracket a
  shared-result read and queue push with `pqe_rpm_dev_tryuse` /
  `pqe_rpm_dev_disuse`. Those wrappers call the PQE device's generic runtime
  PM use/disuse hooks when present. The producers contain no PQ register
  write and no named panel-power, mute, or brightness operation. Generic PQE
  runtime PM reference management is not evidence of OLED-panel power state.
- `_genre_queue_event` and `_hdr_classifier_queue_event` are **not**
  side-effect-free record wrappers. Genre reads `0x07002d60` and writes full
  words to PQE registers `0x07002d64` and `0x07002d68` before queueing its
  class. HDR classifier performs masked writes to `0x07002d74` (masks
  `0x00ff0000`, `0x0000ff00`, `0x000000ff`) and `0x07002d78` (masks
  `0x00ff0000`, `0x7f000000`) before queueing its class. The exact named
  relocations are the two `pqe_reg_writel` calls at `0xc6f8/0xc70c` and five
  `pqe_reg_writel_mask` calls at `0xf9d4/0xf9f0/0xfa0c/0xfa20/0xfa74`.

Those Genre/HDR writes prove direct picture-quality register programming,
not a direct panel-power operation. There is no call from any of these six
functions to the QD/TCON power, panel mute, OLED maintenance, or brightness
interfaces identified elsewhere in this investigation. Conversely, a PQE
register write can alter rendered pixel processing, so this static audit does
not prove that it has no visible or luminance consequence. It establishes
only that no direct panel-power/brightness primitive is present in these
producer functions.

The caller `sdp_pqe_dp_dlsr_update` is broader than the small
`_dlsr_queue_event` wrapper and performs separate DLSR/QSR register and
memory programming before it calls the wrapper. That upstream algorithm is
not reclassified as side-effect-free by the wrapper finding.

## Limits

- This is exact static code/relocation evidence for one matching module, not
  a live record capture or proof that each producer ran during the incident.
- The producer tag proves origin, not physical screen state or panel output.
- A zero query return proves that one record was dequeued; it does not prove
  that userspace interpreted it, that register programming was accepted by
  downstream hardware, or that pixels emitted light.
- The register addresses above are the logical addresses passed to the
  module's `pqe_reg_*` helpers. They are not asserted to be physical bus
  addresses or named brightness registers.
