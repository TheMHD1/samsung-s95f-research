# Bounded trace of the newly captured `t[10]` record

This is an offline trace of only the six newly observed ring bytes. It does not
access the TV, authorize another controller transaction, or analyze any
persisted/high-bank/POFLG path.

## Captured fact

The accepted smoke capture has these pinned ring snapshots:

- baseline SHA-256 `25ab379c50fe087d209870c3e69e31ea7a5eabd7ad1fb11cf40b7ff382f165b7`,
  header `(write cursor 5, second cursor 5, flag 0)`;
- post SHA-256 `f0dff6e11caa1da039ae86bc451efc68e3fea5fc1623691d4cbe894bf9afe479`,
  header `(write cursor 11, second cursor 11, flag 0)`.

The non-wrapping cursor span `5..11` in the post ring is exactly
`74 5b 31 30 5d 0a`, or `t[10]\n`. The only other changed bytes are the low
bytes of the two cursor DWORDs. This proves what differs between the two
snapshots. Endpoint snapshots alone cannot exclude an unobserved whole-ring
wrap between reads, so this report does not make that stronger timing claim.

## Exact image-1 format and direct caller

The selected package is
`selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin`, 5 MiB,
SHA-256 `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
For its selected image 1, stored `FILE = linked VA + 0x40200`.

The package contains three byte occurrences of `t[%d]\n\0`, at FILE
`0x374d1`, `0x3e2f1`, and `0x59cd8`. Only FILE `0x59cd8` lies in the selected
image-1 coordinate space used here; it maps to linked VA `0x19ad8`. Its exact
eight retained bytes are `t[%d]\n\0\0`, SHA-256
`94c3ff564a86a2b99f3e154c5eb602894e12c0ed256d7da4223a930ba7189c7b`.

The direct caller is the Thumb function at linked VA `0x198fc..0x19abb`
(FILE `0x59afc..0x59cbb`, 448 bytes), SHA-256
`58d1cf885c6cf3324e505a514d034994049282343a6e3b0936d90225e1f281c1`.
The relevant terminal block is:

```text
19a96  ldr   r0, [pc, #0x3c]   ; literal VA 19ad4 -> 2000045c
19a98  ldrb  r0, [r0]          ; old unsigned byte
19a9a  adds  r0, r0, #1
19a9c  ldr   r1, [pc, #0x34]   ; same literal VA 19ad4
19a9e  strb  r0, [r1]          ; retain low 8 bits
19aa0  mov   r0, r1
19aa2  ldrb  r1, [r0]          ; reload new unsigned byte
19aa4  adr   r0, #0x30         ; VA 19ad8, `t[%d]\n`
19aa6  bl    0x1b8c8           ; gated image-1 formatter/ring sink
```

Thumb PC alignment resolves both loads to literal VA `0x19ad4`, whose word is
RAM address `0x2000045c`. The ADR resolves exactly to format VA `0x19ad8`.
Under the ARM calling convention, the format is in `r0` and the first numeric
argument is in `r1`.

The numeric dataflow is therefore locally exact:

```text
new_byte = (old_byte + 1) & 0xff
formatter("t[%d]\n", zero_extend(new_byte))
```

The selected package therefore supplies a matching image-1 formatter/caller
candidate. The live callback tuple identified the packaged pointer generation;
it did not prove immutable equality or execution of this particular code body.
The captured text alone does not establish that this packaged call site
produced the record.

If this packaged site produced the captured record, the printed decimal `10`
means the reloaded byte passed in `r1` was `10`. Absent an intervening writer or
interrupt during the increment/store/reload sequence, its preceding value on
this path was `9` modulo 256. The text is not an atomic observation of RAM and
does not establish what `t` abbreviates, physical units, or a temperature.

## Surrounding caller behavior

The full function is pinned above; the behavior relevant to reaching this log
site can be reconstructed without naming unknown application concepts:

1. It obtains a base pointer in `r4` from subroutine `0x38f4` and obtains a
   configuration pointer from subroutine `0x391c`.
2. A byte at `r4+0x6c7` selects a halfword divisor from configuration offset
   `0xc2` or `0x122`, stored at `sp+4`.
3. At VA `0x19a06..0x19a20`, it increments the halfword at `r4+0x6e2`, then
   uses `UDIV` and `MLS` to compute its remainder by that divisor. A nonzero
   remainder branches to the epilogue at `0x19aac`; only the zero-remainder
   path can proceed to this log site.
4. Subsequent branches perform other work, and two paths within this function
   reconverge at VA `0x19a96`, where the separate byte at `0x2000045c` is
   incremented and printed.

This bounded trace stops at that direct caller and numeric producer. It does
not assign the accepted event to an upstream invocation site or infer a
human-facing meaning from unrelated uses of the byte.

Run the verifier offline with:

```sh
PYTHONPATH=/tmp/tcon-capstone python3 new-log-format-trace.py
```

It pins the package and capture hashes, exact cursor delta, all format-string
occurrences, FILE/VA mapping, function slices, Thumb instructions, literal
address calculations, and direct numeric dataflow. It performs no writes.
