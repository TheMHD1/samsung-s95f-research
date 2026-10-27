# Offline trace of `[RTP]Frame end`, `[RTP:NORMAL][365]`, and `t[1]`

Recorded 2026-10-27 UTC. This is a read-only trace of the newly recovered v3
volatile-log delta and the selected packaged image. It made no TV, USB, root,
or network request. It does not inspect or propose any persisted/high-bank,
POFLG, threshold, or protection modification.

## Captured facts

The recovered control-v3 native outcome is terminal and accepted: its fixed
16-transfer sequence returned the logger gate from zero to one to zero, the
restored RT snapshot matched, and its bounded observation ran from controller
uptime `114277.96` to `114298.04` (about 20.08 seconds). Its secondary-ring
snapshots are:

- baseline: 15,372 bytes, SHA-256
  `f0dff6e11caa1da039ae86bc451efc68e3fea5fc1623691d4cbe894bf9afe479`,
  header `(write 11, read 11, flag 0)`;
- post: 15,372 bytes, SHA-256
  `2c8dd511a958a9f8a8f550c60d5add4f2bfd772f71f8958f5463d6a4b71d0833`,
  header `(write 67, read 67, flag 0)`.

The non-wrapping post-ring span `11..67` is exactly the retained 56-byte file
`control-smoke-v3-log-delta.bin`, SHA-256
`1995fceeb887265d21610bda20b0f8c792ee1e12b4a587f6c8361fd9f3c4b9ac`:

```text
t[10]
t[11]
[RTP]Frame end
t[12]
[RTP:NORMAL][365]
t[1]
```

That ordering and those bytes are observed facts. The static attributions below
are matching packaged-code provenance, not proof that every observed line was
emitted by the identified packaged body.

## Corrected package coordinates

The selected 5 MiB package is
`selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin`, SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
For selected image 1, the corrected mapping is:

```text
stored FILE offset = linked VA + 0x40200
```

RAM addresses such as `0x200004a0` and `0x2000045c` are CPU data addresses;
the package FILE bias must not be added to them.

| Object | linked VA | stored FILE | Evidence |
| --- | ---: | ---: | --- |
| shared RTP orchestrator | `0xb644..0xb797` | `0x4b844..0x4b997` | slice SHA `77eaad94857db91496e71c80e7dd23f9509519fa5b0da7b2eac7a0119fba4ffa` |
| frame function | `0xb8a8..0xb975` | `0x4baa8..0x4bb75` | slice SHA `a40c6da321991212c63a8de7b9aca3e7c65edbdf0ac9c75ba1ed62ac5d290395` |
| `[RTP]Frame end\n` | `0xb97c` | `0x4bb7c` | exact 16-byte C string |
| status function | `0xb9f4..0xbaf1` | `0x4bbf4..0x4bcf1` | slice SHA `e93aa53bdc7874bf76c29f7b641cbc5c5d06950063cde8de05bf155bba4ba311` |
| `[RTP:%s][%d]\n` | `0xbb48` | `0x4bd48` | exact 16-byte C string |
| mode mapper | `0x1b72c..0x1b75f` | `0x5b92c..0x5b95f` | slice SHA `48bd50484704a49f0017da91cc1965d235670fed9d7d591e3943b55bbdf6ea7d` |
| `NORMAL`, `ONSEN`, `IO` strings | `0x1b74c` | `0x5b94c` | exact 20-byte string group |
| `t` reset function | `0x19730..0x1976b` | `0x59930..0x5996b` | slice SHA `df9db491b11307030ba93e788a9b38a28548f102fb5e265e39ef4977f1623731` |
| transition function | `0x1976c..0x198fb` | `0x5996c..0x59afb` | slice SHA `b0dd92041c3ffce8908ec5e8740948e51df7e12e383c4ae02701d1ee20b50327` |
| `t[%d]\n` producer | `0x198fc..0x19abb` | `0x59afc..0x59cbb` | slice SHA `58d1cf885c6cf3324e505a514d034994049282343a6e3b0936d90225e1f281c1` |

All Thumb code starts above are even linked VAs. Direct `BL` sites below are
also reported as even instruction addresses, not Thumb pointers with bit zero
set artificially.

## `[RTP]Frame end` producer

The frame function at VA `0xb8a8` loads the byte addressed by a literal at VA
`0xb978`; that literal is RAM address `0x2000049c`. At `0xb8b4` it skips the
block if the byte is zero. Otherwise it:

```text
b8b6  movs  r0,#0
b8b8  ldr   r1,[pc,#0xbc]  ; literal b978 -> 2000049c
b8ba  strb  r0,[r1]        ; clear byte
b8bc  adr   r0,#0xbc       ; b97c, `[RTP]Frame end\n`
b8be  bl    1b8c8          ; existing gated formatter/ring sink
```

The only halfword-aligned direct `BL` encoding to this frame function in the
selected image is at VA `0xb72e` (FILE `0x4b92e`), inside the shared RTP
orchestrator.

This supports only a narrow label interpretation: a nonzero internal byte was
cleared while the packaged code emitted the literal “Frame end.” It does not
identify a display frame, an OLED electrical cycle, a fault, or a physical
blackout without runtime/body identity and incident-aligned evidence.

## What `NORMAL` and `365` mean in this packaged body

The status function selects a small integer code in `r5`:

- RAM halfword `0x200004ac == 1` selects code `6`;
- otherwise, RAM halfword `0x200004aa == 1` selects code `4`;
- otherwise it selects code `1`.

It calls the mode mapper at VA `0x1b72c`, which maps code `1` to `NORMAL`, code
`4` to `ONSEN`, and code `6` to `IO`. Thus packaged text `NORMAL` means only
that neither of the two tested selector halfwords equaled one at that selection
point. This trace does not assign a product-facing or physical meaning to the
mode names.

The numeric argument has a separate, exact dataflow:

```text
baae  ldr   r0,[pc,#0x44]  ; literal baf4 -> RAM 200004a0
bab0  ldrh  r2,[r0]        ; unsigned current halfword
bab2  mov   r1,r6          ; selected mode string
bab4  adr   r0,#0x90       ; bb48, `[RTP:%s][%d]\n`
bab6  bl    1b8c8
```

Under the ARM calling convention, the format is in `r0`, `NORMAL` is in `r1`,
and the decimal argument is the zero-extended halfword in `r2`. Therefore, if
this packaged call produced the captured line, `365` is exactly the value read
from RAM halfword `0x200004a0` before the formatter call. It is not a line
number, error code, temperature, elapsed milliseconds, or panel-health value
on the evidence available.

Only after logging does this function increment the same halfword, store and
reload it, compare it with `0x270f` (9999), and replace it with one if it is
greater. Starting from the supplied value 365, this path stores 366; the
`>9999 -> 1` branch is not taken. Consequently, the following observed `t[1]`
is not the status counter wrapping or resetting.

The only halfword-aligned direct `BL` encoding to the status function is at VA
`0xb6ce` (FILE `0x4b8ce`) in the same shared RTP orchestrator. In a single
linear invocation, that status call precedes the conditional frame-function
call at `0xb72e`. The capture contains `Frame end` before the status line, so
the two observed records cannot be naively assigned to one uninterrupted
invocation of that packaged orchestrator. Separate invocations or other runtime
interleaving remain possible.

## Distinct control flow consistent with `t[1]`

The `t[%d]\n` producer uses a different counter: byte RAM `0x2000045c`. Its
terminal block at VA `0x19a96` loads the byte, adds one, truncates/stores it with
`STRB`, reloads it unsigned into `r1`, and calls the same formatter with
`t[%d]\n`. This is the already pinned `t` dataflow.

The packaged reset function at VA `0x19730` writes zero to that exact byte:

```text
19754  movs  r0,#0
19758  ldr   r1,[pc,#0x0c] ; literal 19768 -> RAM 2000045c
1975a  strb  r0,[r1]
```

An exact halfword-aligned direct-call census finds two reset calls, at VAs
`0x4460` and `0x197da`. The latter is inside transition function `0x1976c`; it
is taken when the function's combined transition value in `sb` is nonzero.
There are likewise two direct calls to the `t` producer, at VAs `0x4454` and
`0x17b8e`.

One packaged top-level sequence is particularly relevant:

```text
444a  bl    1976c          ; transition function, may call reset at 197da
444e  movs  r2,#0
4450  mov   r1,r2
4452  mov   r0,r2
4454  bl    198fc          ; t producer
```

If the transition condition caused `0x197da -> 0x19730`, byte `0x2000045c`
was zero on return; a subsequent producer tail would increment it to one and
emit `t[1]`. This is an exact packaged control-flow candidate consistent with
the observed reset from `t[12]` to `t[1]`. It is not proof that this path ran:
the other `t` caller lacks that adjacent reset, the transition call is
conditional internally, and the observation contains text rather than a PC or
RAM snapshot at each line.

## Evidence boundary

The selected package has the exact strings, literals, callers, RAM addresses,
and numeric dataflows needed to generate the observed sequence. Existing live
callback evidence associates runtime state with this packaged pointer
generation, but it does not establish immutable equality of the entire
executing image or prove that these particular packaged bodies emitted the v3
records. No full executing-binary hash or incident-aligned PC trace exists.

Accordingly, the strongest bounded conclusions are:

1. `365` matches the pre-increment unsigned halfword at `0x200004a0` in the
   packaged status producer; that producer would next store 366.
2. `t[1]` uses the distinct byte at `0x2000045c` and is consistent with a
   separately packaged reset-to-zero followed by increment-and-log.
3. `Frame end`, `NORMAL`, `365`, and `t[1]` do not by themselves establish a
   panel fault, display-module restart, protection action, or blackout cause.

Run the offline verifier with:

```sh
PYTHONPATH=/tmp/tcon-capstone python3 rtp-normal-log-trace.py
```

It pins the package and capture identities, corrected FILE/VA coordinates,
function slices, Thumb instructions and direct calls, literal/ADR arithmetic,
the two distinct counters, and the bounded reset candidate. It performs no
writes or target operations.
