# Image-1 secondary event-log buffer

Offline static evidence only; no console/TTY, TV, USB, or hardware access.

Selected package `F_RSM1_BN9659934B_COMMON.bin`; image-1 stored FILE = linked VA + `0x40200`.

The common event setter is linked VA `0xc1e0..0xc212` (FILE `0x4c3e0..0x4c412`), slice SHA-256 `f8a6285dd94b3338eff37ded006a2ebff6ecfe7409bef9044f34fd25cdb27102`. It sets image-1 fields `+0x2400=1`, `+0x240e=0`, and `+0x240a=0x1001`, then calls formatter/sink VA `0x1b8c8` twice at VA `0xc206` and `0xc20e`. Both ADR instructions resolve to the same format literal at VA `0xc214`, `rtp_act_%d\\n`.

Sink VA `0x1b8c8..0x1b93e` (FILE `0x5bac8..0x5bb3e` = VA +
`0x40200`) has slice SHA-256
`47abdf7963385a87473920daae5212943303054ceb9ba3df92c3c31928fb545e`.
It formats into stack buffer `sp+0x40`, gets length in `r6`, and writes bytes
into a circular history.

Its literal pool resolves to RAM `0x20200000`: VA `0x1b8fc` reads the write index; VA `0x1b90c` stores the modulo-reduced index; VA `0x1b914` rereads it; VA `0x1b91c` advances it; and VA `0x1b924` writes bytes to `0x2020000c + old_index`. VA `0x1b92e..0x1b934` sets `1` at `0x20200008` as a valid/available flag.

The ring is `0x3c00` bytes at `0x2020000c..0x20203c0b`. The write-index object
at `0x20200000` is a DWORD. At the start of each byte iteration the sink
reduces that DWORD modulo `0x3c00` and stores the remainder, then writes one
byte and increments the index. The conditional branch at VA `0x1b92a` is
`blt 0x1b8fc`, proving per-byte return to the modulo block; records therefore
wrap per byte and do not overrun the nominal ring. The sink’s entire operation
is gated by image-1 logfile flag `+0x2406` bit 0 at VA `0x1b8d6..0x1b8e0`.
The output scratch starts at `sp+0x40` in a `0x1040` frame; the exact formatter
limit is not inferred beyond the retained instructions. The routine does not
persist a record length, so a reader needs the index/flag plus record parsing.

Image-0 has an equivalent logger at linked VA `0x39394`; its DWORD index is
`0x20000e5c` (literal VA `0x393ec`), byte buffer is `0x20205000` (literal VA
`0x393f0`), and ring size is `0xc00`. This path has no corresponding logfile
enable gate in the retained slice. Image-1 mapper VA `0x3084..0x30a0` uses literal `0xe00fdfdc`. Its input range
is `[0x20000000,0x20200000)`, upper bound exclusive. The boundary behavior is
therefore: `0x201fffff` maps by the selected tag offset; `0x20200000` and
`0x2020000c` fall through and return unchanged. The ring base is outside this
mapper range, so it must not be described as `0x4520000c`/`0x4720000c` via this
helper. A direct DMA/read interpretation for `0x20200000` remains unproven.

Run `verify-secondary-event-log-buffer.py` with `PYTHONPATH=/tmp/tcon-capstone` to verify package hash, exact slices, Thumb instructions, literal, and ring arithmetic.
