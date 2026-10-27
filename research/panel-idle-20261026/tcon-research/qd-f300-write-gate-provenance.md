# F300 staged-scalar write gates and their recovered producers

Recorded 2026-10-27 UTC, entirely offline while the owner's playback test is
on hold. No TV/server/network read, root call, capture, command transmission,
helper deployment, register write, or protection change occurred.

## Result and diagnostic implication

The selected packaged controller has an explicit gate before the F300 scalar
setter. The recovered literal-backed producers associate that gate with a
state machine whose own log strings say `Start PTM` / `End PTM`, another
bounded state transition, and selector `0x180`. They do **not** establish that
an RT fault sets the gate or that the gate had any particular value during a
blackout. No expansion or physical meaning of the PTM acronym is inferred.

This explains a concrete measurement gap: a successful host transfer carrying
`F3 00 00 00 01 28` plus scalar does not prove the controller staged that
scalar. A source-backed read of selector `0x128` would return the low ten
bits of the staged RAM field, independently of these setter gates. That would
test acceptance into RAM only. It would not establish physical panel drive,
prove the complete live firmware matches this package, or supply a repair.
The host ioctl route for such a read is under separate offline review; no
new read is armed or authorized by this report.

## Input and reproduction

The input is `overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin`,
5,242,880 bytes, SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
All code addresses below are image-0 linked VAs, **file offset = VA + 0x200**.
Absolute RAM addresses are unchanged.

- [Reproducer](qd-f300-write-gate-reproduce.py), SHA-256
  `4127947c8d7850dc28f345cadc5ccc22862029b3bae065de4c91d6354feae8ee`.
- [Evidence and bounded disassembly](qd-f300-write-gate-evidence.json), 28,184
  bytes, SHA-256 `5981bda42e6e68c618dfbbf73b13c00548a2f325e771394d2c8c7052ccffb3f0`.

Run offline with `PYTHONPATH=/tmp/tcon-capstone python3
qd-f300-write-gate-reproduce.py`. It checks the full input hash, 32 selected
instructions, literal targets and three selector-table destinations, then
emits the retained disassembly slices with individual byte hashes. These are
source consistency checks, not an emulation or physical experiment.

## Exact setter gate

In `0x2c71c`, `r6` is the selector and `r4` the scalar. The byte at RAM
`0x200008e8` is read at `0x2c750..0x2c752`, before the selector dispatch:

| Gate byte / additional condition | Recovered behavior |
| --- | --- |
| `1` | Branch directly to the function return at `0x2c75e`; no selector leaf executes. |
| `2`, halfword `0x2000ff1a` nonzero, selector other than `0x180` | Return before selector dispatch. Thus `0x128` is suppressed. |
| `2`, halfword `0x2000ff1a` zero | Clear the gate byte to zero at `0x2c76c`, then continue. |
| `2`, halfword nonzero, selector `0x180` | Continue into the selector table. |
| Other gate values | Continue into the ordinary alignment/range checks. |

The special halfword is `[getter(0xe678) + 6]`; its root is
`0x2000ff14`, so the effective address is `0x2000ff1a`. This is not the
RT flag at `0x4701240a`, the common error selector, or the staged scalar.
Passing this gate still does not prove every selector is accepted: the
remaining dispatcher applies its own range/alignment and leaf conditions.

## Recovered gate producers

These are coherent code paths using exact literal pointers to
`0x200008e8`. A literal-reference search is not a proof that no computed or
indirect writer exists elsewhere.

| Path | Gate effect and conditions |
| --- | --- |
| `0x96cc..0x96d2` | Unconditionally stores byte `1`. Its recovered caller is `0x57ba`. |
| `0x5798..0x57c4` | Compares bits of common-object `+0x2a` with cached values. A mismatch or nonzero result from `0x555c` prints `Start PTM`, calls `0x96cc`, then sets state byte `0x20000c98` to `3`. This function is reached from `0x4f80` when that state is zero. |
| `0xb654..0xb65a` | Unconditionally stores byte `0`. Called at `0x4fcc` after `End PTM` when state `0x20000c98` equals `0x0c`; that caller also resets the state to zero. |
| `0x2e560..0x2e572` | In another state machine, common-object `+0x3b4 == 0x0c` calls two functions, clears that halfword, and calls the same byte-zero helper `0xb654`. The hardware effects of those other calls are outside this trace. |
| `0x2555c..0x25598` | If common-object halfwords `+0x37a`, `+0x37c`, `+0x37e` agree, differ from the incoming value, and the incoming value is less than `3`, stores the new `+0x37a` value and gate byte `1`. Its recovered caller at `0x2ce04` is in the `F300:0x160` leaf. |
| `F300:0x180`, `0x2ce2a..0x2ce54` | If EXCO-object `+0x0a` is zero, payload `1` sets its `+6` halfword to `1`, calls `0x36a2c`, then sets gate byte `2`. Payload `0` clears the `+6` halfword and gate byte. Other payloads leave this selected path without these stores. |

The selected-profile main loop has direct calls to both `0x2e4ec` and
`0x4f80` at `0x39c10` and `0x39c14`, respectively (outside the bounded
reproducer slices). This identifies a normal execution context, not an
incident-aligned transition. The common-error handler at `0xb660` is adjacent
to the byte-zero helper but adjacency alone does not establish a call or
recovery path. No RT-to-gate edge is claimed.

The selector `0x180` description is a static control-path inventory. It is
not a proposed diagnostic command, and none was sent. Changing this gate
would not by itself prove any protection latch, panel rail or physical fault
was recovered.

## Staged field and distinct reader

The `0x128` write-table target is `0x2cc96`. After the gates it masks the
payload to ten bits and stores the halfword at root `0x2000d71c + 0xa6`,
effective RAM `0x2000d7c2`. The distinct getter case is `0x21c30`:

```text
21c30  ldrh.w r0, [r4, #0xa6]
21c34  ubfx   r0, r0, #0, #0xa
21c38  b      2178e
```

Its prologue gets `r4` from the same `0xef9c` literal-root getter. The
selected case only loads; it has none of the setter's gate tests. The read
dispatcher still updates protocol checksum bookkeeping through `0x5924`,
and the receiver/transmitter updates parser counters. Therefore a read is
not literally free of all controller state changes. It has no recovered
store to this staged scalar or the RT fields in its selected path.

The older [getter-only boundary report](qd-controller-final-duty-rt-boundary.md)
is supplemented by the [write-payload trace](qd-f300-write-payload-dispatch.md).
The recovered [downstream calculations](qd-final-duty-controller-consumers.md)
remain a separate question: observing the RAM field is not evidence that a
hardware application edge executed, or that dimming caused the blackout.

## What remains unproved

No live gate value, incident-time gate transition, accepted scalar readback,
current controller-flash identity, physical output, RT producer connection,
or fault-prevention/recovery result was obtained here. The owner hold remains
in force. The new result narrows a future measurement to acceptance into a
specific controller RAM field without substituting it for fault diagnosis.
