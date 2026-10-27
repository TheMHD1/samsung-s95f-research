# TCON MICOM debug-log backing store, producer, and read semantics

## Scope and conclusion

This is an offline analysis of the exact copied `sdp_tcon.ko`.  No TV, root,
debugfs, GPIO, TCON, network, or live-memory operation was performed.

`/sys/kernel/debug/tcon/tcon_micom_log` is **not a kernel-owned fixed text
cache**.  It exposes a noncached mapping of a reserved shared-memory region
whose payload is populated outside the recovered host-driver code.  The
visible content is controller/firmware startup and message text.  The host
driver treats it as a linear buffer with a 16-bit last-byte index; no circular
ring interpretation is present in the bounded host paths.

The debugfs read does not clear or acknowledge the buffer.  It advances only
the calling file descriptor's `f_pos`; reopening starts at offset zero.  Its
misleadingly named runtime-use helpers do not take a runtime-PM reference:
`tcon_rpm_dev_tryuse` is one state load, and `tcon_rpm_dev_disuse` is a no-op.
Consequently one bounded fresh read is a technically useful, low-interference
diagnostic: positive new text can add evidence.  Identical text or absence of
a fault string cannot establish that no fault/reboot occurred.

## Provenance

| Input | Bytes | SHA-256 |
| --- | ---: | --- |
| `binaries/sdp_tcon.ko` | 226,262 | `9b7c1cb8e2bb8d11e5465a41fa402e71bd8d15a5dabd6b3d76de98a7a42549ee` |
| `overnight/tcon-firmware-log-prefix.txt` | 1,405 | `39b72938ffc5aec8238417fce72cdd131864040dea137a1cbbc5e3191116e846` |
| `overnight/tcon-firmware-log-prefix.json` | 3,213 | `70810157116234fb027d320434f8a4f5ae411d3fc271138706d3d8f2d21fce4a` |

The module is AArch64 relocatable ELF, Build ID
`217c7fcac3a0fa4163e5a407e641ca314b5fd47e`.  The retained log capture is an
authenticated root response with the host-assisted-persistence and global
system-file invariants.  Its overall command had stderr from unrelated
missing `/sys/class/misc` paths; the debugfs pipeline itself nevertheless
returned the retained 1,405 decoded bytes.  This capture has a UTC timestamp
but no matching uptime or owner transition annotation, so its content cannot
be assigned to a particular blackout.

## Backing region

`sdp_tcon_resource_init` (`.text+0x920`, size 1,236) reads four records from
the `sdp_mmap` DT node.  The fourth record is named
`samsung,tcon_info`.  At `0xc84..0xc94` it combines that record's two 32-bit
address cells into a 64-bit runtime base.  It then creates these noncached
mappings:

| Runtime instance field | Physical range relative to `tcon_info` base | Size |
| ---: | ---: | ---: |
| `+0x390` (912) | `+0x00000` | `0x20000` |
| `+0x368` (872) | `+0x20000` | `0x40000` |
| **`+0x378` (888)** | **`+0xa0000`** | **`0x20000`** |
| `+0x370` (880) | `+0xc0000` | `0x30000` |

The third entry is the MICOM log mapping: `devm_ioremap_nocache` at `0xcd4`,
stored at instance+888 at `0xcd8`.  It is unmapped on resource-init failure or
driver removal.  This is a shared reserved-memory window, not a 1,405-byte
allocation made by the debugfs handler.

The log layout used by the host code is:

```text
+0x00  u16 last_data_index
+0x02  u16 host/controller log state
+0x04  byte data[last_data_index + 1]
```

Both the debugfs reader and host log printer load the low 16 bits at `+0` and
treat `index + 1` as the available byte count.  Although the mapping is
128 KiB, that format exposes no more than 65,536 payload bytes through this
index.  A combined 32-bit header value of `0xffffffff` is treated as invalid.

## Exact debugfs read path

The file-operations object is `.rodata+0x1660`, size 264.  Its relevant
relocations are:

- `+0x08` -> `generic_file_llseek`;
- `+0x10` -> `tcon_dbg_tcon_micom_log` at `.text+0x61b0`; and
- `+0x70` -> `simple_open`.

There is no custom release callback.  `simple_open` assigns the inode's
private data to the file; it does not contact the controller.

`tcon_dbg_tcon_micom_log` performs the following bounded sequence:

1. gets the driver instance from file private data and loads instance+888;
2. samples the 16-bit last-data index and rejects the all-ones header;
3. calls `tcon_rpm_dev_tryuse`;
4. checks the caller's file position against the sampled length;
5. copies bytes from mapping+4+position with `__arch_copy_to_user`;
6. advances only `*ppos`; and
7. calls `tcon_rpm_dev_disuse` on both data and EOF paths.

Despite their names, the helper bodies are:

- `.text+0x270`: load the global instance, return its 32-bit state at
  instance+1228;
- `.text+0x280`: return zero.

There is no `sdp_runtime_pm_tryuse`, `getdev`, `disuse`, power, mailbox, I2C,
or controller command in this read path.  A nonzero state makes the reader
fail before copying.  The reader contains no write to the mapped header or
payload, no clear, and no read-to-ack behavior.

The length and payload are not protected by a lock, sequence counter, or
explicit barrier.  If the external producer updates them concurrently, a
read can be a non-atomic snapshot.  That is an evidence-quality limitation,
not a target-side mutation.

The handler also violates the ordinary `read(2)` count contract.  When the
total valid length is at most 4,095 bytes it selects that total rather than
the smaller of the remaining length and the caller's count.  When the total
is larger, a remaining length above 4,095 selects the caller's count without
clamping it to the remaining valid bytes.  Consequently a single 8 KiB or
64 KiB request can copy stale bytes beyond the current last-data index.  A
4,096-byte request is the safe fixed unit for a stable sampled length: while
more than 4,095 valid bytes remain it copies exactly 4,096, and the final
request copies the remaining 1..4,095 bytes.  Reaching EOF then returns zero.
Concurrent producer growth or reinitialization can still make the multi-read
result torn, as already qualified above; fixed-size requests remove the
deterministic oversized-request overcopy, not that external race.

## Producer and lifecycle evidence

A finite direct-reference scan found the syntactic instance+888 references at
`0x1c4`, `0xcd8`, `0xdb8`, `0xe14`, `0xf58`, `0xfbc`, and `0x61c8`.
Adjusted structure bases mean that list is not an alias-complete whole-module
proof.  Within the recovered mapping/read/print paths:

- resource init stores and cleanup/remove loads the mapping pointer;
- `sdp_tcon_frc_micom_log_out_print` reads the current payload and, when the
  last-byte index exceeds 6,000, starts at `index - 6000` (at most 6,001
  payload bytes) and prints it as lines;
- `tcon_dbg_tcon_micom_log` copies payload bytes to userspace; and
- `sdp_tcon_frc_micom_log_out_func` loads the mapping and may store `0x11` to
  header+2 before calling the printer.

That header-state store is the only concrete host-side write recovered in
the selected direct log-buffer paths.  It does not append payload text or
change the low 16-bit data index.  The separate error work and PMIC-status
path call the printer; they do not populate the payload.

No host IRQ handler or mailbox callback that copies characters into this
mapped data area was recovered.  The module's message-box IRQ machinery uses
separate mapped resources.  Given the firmware-origin text and absence of a
bounded host append path, the payload is consistent with direct production by
the external TCON MICOM/firmware into shared memory.  The exact firmware
writer, its update ordering, and its behavior on wrap/reset are outside this
module and remain unproved.

The host printer's arithmetic is linear: it uses the current index and, when
that exceeds 6,000, starts at `index - 6000`.  It has no modulo or ring-head
calculation.  Therefore the copied host code does not support calling this a
circular kernel/UART ring.  Firmware could reset or replace the buffer, but
that possibility is not distinguishable statically here.

`sdp_tcon_debug_init` also clears 0x3ff00 bytes through instance+896.  That is
a different mapping from the MICOM log pointer at instance+888 and must not be
misdescribed as clearing this log.

## What the retained prefix establishes

The 1,405-byte retained prefix begins with:

```text
RHEA_M_TCON_FW_20250103_1715
I2C_M Init
...
TCON Image Info : F77ABU2D20
...
Cold Boot!
...
Main Loop
Total Booting Time (us): 208332
```

It then has repeated `Msgbox ISR In/Out` text and ends with the lone byte `S`
after 68 newlines.  The incomplete final token is consistent with capture
during an append, but one prefix cannot prove that timing; it could simply be
the producer's current terminal byte.

The words `Cold Boot!` are controller startup text already present in the
early retained image.  They are not a timestamped assertion that a controller
reboot occurred during a later physical blackout.

## Practical recommendation

One new bounded read is worthwhile because this is a direct shared-memory
view, not a consumed fixed file.  The region may nevertheless remain stale
when firmware has nothing more to append.  A safe evidence transaction should:

1. pin the same boot, exact module hash/path, debugfs path/type/owner/mode and
   global trace/system-file invariants;
2. open the file once without seeking or writing and issue only fixed
   4,096-byte reads (for example `dd bs=4096 count=16`); do **not** substitute
   one `head -c 8192`, 8 KiB read, or 64 KiB read, because the vendor handler
   can then return stale bytes past its current valid index; bound decoded
   output to 65,536 bytes and retain exact byte count and SHA-256;
3. retain UTC and uptime bracketing and the owner's separately reported panel
   state without inventing subsecond alignment;
4. transfer losslessly (compression is acceptable only with hashes before
   and after decompression); and
5. compare exact common prefix, new suffix, size and full hash against the
   1,405-byte prior artifact offline.

Useful positive outcomes include newly appended fault/protection text or a
changed/reinitialized startup image.  A repeated startup banner after a
time-aligned event would be consistent with log reinitialization, but without
an epoch counter or timestamp it is not by itself proof of a physical MICOM
reboot.  An unchanged file, no keyword, or a torn final line supports no
global absence claim.

No polling loop, write, debug-level change, artificial controller command,
or protection/power action is justified by this analysis.

## Reproduction

Run offline:

```sh
python3 tcon-research/tcon-micom-log-cache-producer-reproduce.py
python3 -O tcon-research/tcon-micom-log-cache-producer-reproduce.py
```

Both modes hash-gate the inputs, verify the exact symbols, relocations,
selected instruction windows and finite direct-reference census, and validate
the retained prefix/capture identity.  The helper is intentionally not a
general alias analysis or firmware-producer proof.
