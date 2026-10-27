# OCIF AckPolling is a one-byte zero write, not a read

This report is static analysis of a copied module. The analysis invoked no
getter, callback, I²C transaction, module load, or display control. The module
was acquired separately through bounded, passive authenticated file reads.

| Input | SHA-256 |
|---|---|
| `overnight/serdes-ack-copy-20261026/sdp_ocl_jp.ko` | `e5a064da2cfbd37194f5e97463c3519126a09aedaf4b3c95107b08ab0680aa2c` |
| Pinned exact-ELF reader | `8c97cb7cfed4b0e8694725e7017625b363b772f132ad3aaae32ccd699de28c67` |

Addresses are section-relative ARM64 ELF offsets.

## Definition and export

`SDP_OCL_I2C_AckPolling` is a defined global function at `.text+0x6898`, size
104. Its `__ksymtab` relocation is at `0xf0`; thus it is an actual exported
provider, rather than merely a matching string or an inferred callback target.

## Exact message layout

The function copies its `w0` argument into `w1`, derives
`addr = (w0 >> 1) & 0x7fff` at `0x68b8`, and constructs one stack message at
`sp+0x30`:

| `struct i2c_msg` member | Static construction |
|---|---|
| `addr` (`u16`, +0) | `strh w1,[sp,#0x30]` |
| `flags` (`u16`, +2) | low half of `0x00010000` stored at `sp+0x32`: zero |
| `len` (`u16`, +4) | high half of that word: one |
| `buf` (+8) | `sp+0x2f`, whose one byte is set to zero |

It passes `x1=sp+0x30`, `w2=1` to `i2c_transfer(ahb_adap, x1, 1)` at
`0x68e0`, under `ocl_i2c_mutex` (`mutex_lock`/`mutex_unlock`). The standard
Linux v5.4 UAPI defines `I2C_M_RD` as flag bit `0x0001`; this vendor message
sets flags to zero. Under that ABI it is therefore one data byte **written to**
the selected slave, specifically zero, rather than a read. The vendor module
itself does not inspect a returned data byte.

The input values used by the already traced caller map to bus addresses:
`0x54 → 0x2a`, `0x78 → 0x3c`, and `0x80 → 0x40`. They are not operation codes
inside this provider.

References: [Linux v5.4 `struct i2c_msg` and `I2C_M_RD`](https://raw.githubusercontent.com/torvalds/linux/v5.4/include/uapi/linux/i2c.h),
[Linux v5.4 I²C core](https://raw.githubusercontent.com/torvalds/linux/v5.4/drivers/i2c/i2c-core-base.c).
Those upstream sources explain the public ABI; they are not proof that this
TV's running I²C core/adapter completed this transfer.

## Return and state limits

After `i2c_transfer`, the function saves raw `w0` to `w19` and returns it
unchanged at `0x68f0`. It contains no retry loop, message-count comparison,
cache write, reset action, or byte-value interpretation. The existing OCIF
caller accepts any non-negative return before setting its own `+0xb8` cache,
so zero is not rejected there. This must not be reworded as a verified device
acknowledgement, a lock measurement, or fault-protection disablement.

## Adapter provenance

`ahb_adap` is `.bss+0x10`, size 8. In the local
`sdp_ocl_platform_i2c_init` (`.text.unlikely+0x2c`, size 1116), a configuration
base is module `.bss+0` in `x19`; it loads a configuration pointer from
`[x19+8]` at `0xec`, then its adapter index from `[configuration+8]` at
`0xf0`. It calls `i2c_get_adapter` at `0xf4` and stores the returned pointer
directly at module `.bss+0x10` at `0xf8`. This is the static
initialization path to the global consumed by AckPolling. The actual index,
adapter pointer, and whether initialization succeeded were not captured.

## Correction retained

An earlier preliminary interpretation called this a one-byte read. That was
wrong: `struct i2c_msg` places `flags` at offset +2 and `len` at +4, so the
little-endian `0x00010000` store makes `flags=0,len=1`; with the buffer byte
initialized to zero it is a one-byte zero write. No live callback was made
while correcting this, and this result does not justify disabling protections
or changing device state.

## Reproduction

```sh
PYTHONPATH=/tmp/tcon-capstone python3 ocif-ack-polling-reproduce.py
PYTHONPATH=/tmp/tcon-capstone python3 -O ocif-ack-polling-reproduce.py
```

`--write-disassembly` creates the saved listing exclusively; default mode
verifies that listing and never overwrites it.
