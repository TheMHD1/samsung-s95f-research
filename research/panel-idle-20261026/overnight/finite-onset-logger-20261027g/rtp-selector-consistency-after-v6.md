# RTP selector consistency after V6

Recorded 2026-10-27 UTC. This is a bounded offline interpretation of the
already-retained `selector-context-after-v6` read and selected image-1
package. It made no TV, network, root, USB, controller, UI, firmware, reader,
threshold, protection, persistence, or storage operation. It stays within
the ordinary selector/mirror/startup paths and stops where the producer is
not present in those paths.

## Result

The late samples are internally consistent with the ordinary **mode-1,
nonzero-alternate** route:

```text
root anchor R                         0x20010000
CPU-window candidate aa / ac         0 / 2
numeric selector mirror 0x200004c2   1
companion 0x200004c4                  0
ordinary scan-enable byte +0x4d8     0
candidate context +0x6c6/+6c7/+6c8  0x5c / 1 / 3
candidate context +0..+5             70 08 80 07 40 0b
raw word at window +0                396
```

Only selector values exactly equal to one activate predicate mode 4 or 6.
The late `aa=0, ac=2` pair therefore selects ordinary mode 1 if observed at
the predicate tail. With candidate selector byte `+0x6c7=1`, mode 1 chooses
`R+0x24c4`. The earlier late fault-context read returned:

```text
R+0x0f08 = 44
R+0x24c4 = 40
```

Thus `44 > 40` is numerically compatible with the ordinary mode-1,
nonzero-selector predicate. It is **not** a reconstruction of the V6 event:
the score/threshold read and selector read were separate late acquisitions;
the ordinary scan gate is now zero; selector and mode state can change; and
none of these reads captured the compare registers at the taken edge.

The exact candidate bytes are:

```text
70 08 80 07 40 0b 5c 01 03 00 00 00 00 00 00 00
```

This matches all three startup halfwords, the startup equality byte described
below, and the independently sampled numeric selector mirror. It is stronger
multi-field consistency than the former single-byte comparison. It still
does not turn candidate bus `0x47000bc0` into a universally proved live CPU
alias: the live secondary-core tag and a general address-space identity were
not observed, and the two bus reads were sequential.

## Why numeric mirror 1 and companion 0 can coexist

The wrapper name `enable_candidate_raw` is too strong for the complete
lifecycle of `0x200004c4`. VA `0xc250` initially writes it as a Boolean, but
ordinary function VA `0x1c12c` also uses and changes it as a small progress
value.

At VA `0xc27c..0xc2a2`:

```text
new = byte[fixed_context+0x6c7]
old = uint16[0x200004c2]
if new != old:
    uint16[0x200004c2] = new
    uint16[0x200004c4] = (new != 0) ? 1 : 0
```

The equality branch at VA `0xc286` skips both stores. Therefore, once the
numeric mirror already equals one, later calls with selector one do not force
the companion back to one.

VA `0x1c12c` has two direct ordinary callers, VAs `0xb682` and `0xb828`.
Its exact `0x200004c4` lifecycle is:

1. return immediately when `c4==0` (`0x1c134..0x1c138`);
2. return immediately when context `+0x6c7==0`
   (`0x1c13a..0x1c13e`);
3. on either of two qualified paths, increment `c4` and store it at
   `0x1c150` or `0x1c17c`;
4. at `0x1c18e..0x1c19a`, clear `c4` when its value is greater than two.

Consequently an ordinary permitted sequence is:

```text
selector changes to 1:  mirror=1, c4=1
qualified progress:     c4=2, then c4=3, then clear c4=0
selector remains 1:     mirror equality skips c250 reinitialization
result:                 mirror=1, c4=0
```

This is code evidence that the captured pair can coexist; it is not a claim
that this exact sequence was instruction-traced during V6. The finite aligned
literal census finds `0x200004c4` only at VAs `0xb89c`, `0xc2f4`, and
`0x1c1a0`: the first supplies a read-only branch gate at `0xb82c`, the second
supplies the conditional Boolean stores in `0xc250`, and the third supplies
the reads/increments/clear in `0x1c12c`.
This literal census does not exclude a computed-address, indirect, interrupt,
or external reference.

## What can be proved about local byte `+0x6c6`

The candidate byte `+0x6c6` is now `0x5c`. Selected image 1 has exactly one
direct immediate-offset access to fixed context `+0x6c6`: VA `0x1bd90`
loads it. The startup sequence is:

```text
1ba24  call 38e8                         ; AP_EXCO pointer
1ba28  r1 = 0x5c
1ba2a  strb r1,[AP_EXCO,#0x36]
1ba32  call 1bd88

1bd88  call 38f4                         ; fixed context pointer
1bd90  ldrb r0,[fixed_context,#0x6c6]
1bd94  compare r0,0x5c
        return 1 only on equality
```

The application repeats the equality call while it returns zero. This
positively links `AP_EXCO+0x36 = 0x5c` with waiting for fixed-context
`+0x6c6 = 0x5c`, but it does not identify the producer that transfers or
acknowledges the value.

A halfword-aligned selected-image census finds no immediate-offset `STRB`,
`STRH`, or word `STR` whose destination span covers `+0x6c6`. There can still
be a computed-address writer, bulk copy, interrupt, another processor,
later-loaded code, DMA, or external agent. Resolving that next writer leaves
the bounded ordinary direct-reference path, so this report stops rather than
assigning one. The observed `0x5c` is useful correlation, not proof of a
specific updater or physical meaning.

## Timing and state limits

The selector capture occurred around target uptime 119,358 seconds, whereas
the score/threshold context was retained much earlier. The window reads in
each helper were also sequential rather than atomic. In addition:

- `ac=2` is a late ordinary state, not proof that V6 used mode 1;
- `+0x4d8=0` agrees with the documented post-fault ordinary scan gate, so a
  late score need not have continued refreshing;
- `+0x6c7=1` may refresh before that scan gate if the ordinary caller runs;
- raw `396` at window offset zero and context byte `+0x6c8=3` remain unnamed;
- packaged AP_EXCO defaults `+0x3d8=20` and `+0=0` clearly are not the late
  runtime values `1` and `3`, demonstrating why defaults were never live
  anchors.

The strongest conclusion is consistency, not event causality: late mode 1,
selector one, score 44, and threshold 40 form a valid ordinary predicate
combination, while exact event-time mode, selector, aggregate, and threshold
source remain unobserved.

## Reproduction

`rtp-selector-consistency-after-v6.py` pins both retained raw windows, the
earlier late score/threshold windows, selected-package identity, all aligned
`0x200004c4` literals and their literal-load references, the conditional
mirror update, the complete ordinary progress function, the startup
`0x5c` relationship, the unique direct `+0x6c6` load, and the absence of a
direct immediate-width store covering that byte. The store scanner has a
positive control: it must recover the known `STRH +0x6c0` at VA `0x17984`
before accepting the empty `+0x6c6` result. It uses only Python's standard
library:

```sh
python3 rtp-selector-consistency-after-v6.py
python3 -O rtp-selector-consistency-after-v6.py
```
