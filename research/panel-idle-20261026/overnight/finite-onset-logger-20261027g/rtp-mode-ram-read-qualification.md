# Independent qualification review: image-1 RTP mode RAM reads

Date: 2026-10-27 UTC  
Scope: offline address/evidence review only; no TV, root, USB, network, UI,
reset, write, or helper implementation

## Result

A future ordinary volatile reader can positively qualify the two mode
halfwords at CPU `0x200004aa/0x200004ac` **only conditionally on the non-A
image-1 mapping**, by returning them in the same small window as the
reset-derived root slot at CPU `0x200004e0`. The prior live read of bus
`0x470004e0` returned the exact expected value `0x20010000`; repeating that
anchor in the same response is materially stronger than reading the two
halfwords alone.

The alternate-threshold byte at CPU `0x20000bc7` is not equally qualified.
It is not itself a mode selector: the selected body uses it to choose the
`fp` source for predicate modes 1 and 6. Static
scatter evidence proves that the CPU byte is allocated image-1 SRAM, and the
non-A mapper arithmetically predicts bus `0x47000bc7`, but there is no
address-specific live anchor near that byte and the actual live core tag has
not been observed. In particular, its reset value is zero, so an all-zero
narrow response would not distinguish the intended secondary SRAM from a
wrong or inert window. A future read can collect that bus byte, but the
current evidence is insufficient to advertise a zero result as positive
identification of CPU `0x20000bc7`.

## P1 — CPU allocation is proved; the bus view remains conditional

The selected image-1 reset scatter table has these relevant records:

```text
CPU 0x20000000, decompressed length 0x4f8
CPU 0x200004f8, zero-fill length 0xdca4
```

Thus:

- `0x200004aa..0x200004ad` and root slot `0x200004e0..0x200004e3` are inside
  the decompressed first record; and
- `0x20000bc7` is inside the zero-filled range
  `0x200004f8..0x2000e19b`.

The first record independently decodes to SHA-256
`76bebfc83f8e286d8ae152749a1aa376d0bc8d3f415f2433d9ca6944506e7ef8`
and sets `*(u32 *)0x200004e0 = 0x20010000`. It initializes both mode
halfwords to zero. The zero-fill establishes allocated CPU storage for the
alternate byte but supplies no distinctive content at that address.

The later bounded mode-provenance trace independently confirms the roles of
these bytes. Ordinary startup explicitly stores zero to both `aa` and `ac`;
later ordinary bodies implement finite `1->3`, `3->1`, and `1->2`
transitions. Predicate mode 4 requires `aa==1`, mode 6 requires
`aa!=1 && ac==1`, and the fallback is mode 1. Separately, callback VA
`0x18c94` calls VA `0x3934`, which mirrors `source_context+0x3d8` into
`0x20000bc7`. That establishes CPU-side purpose and a runtime producer, but
does not establish which USB-visible bus address reaches the CPU byte.

An independent byte comparison confirmed that the stored/current second
slot `0x40000..0x7ffff` is exactly equal to the selected package second slot,
with SHA-256
`56bfea112d161a22f5bee8630c81306bf04fa9d8d3d901c6d8e7cdd89c09dfbf`.
That carries the image-1 scatter and mapper bytes into the copied current
storage. It does not prove that every such byte is executing.

The selected image-1 mapper at VA `0x3084..0x30a6` and the acquired current
image mapper at VA `0x9a48..0x9a6c` both implement this CPU-to-DMA rule for
`[0x20000000,0x20200000)`:

```text
core tag == 0xA : bus = CPU + 0x25000000
core tag != 0xA : bus = CPU + 0x27000000
```

The relevant non-A candidates are therefore:

| CPU address | proposed DMA/bus address |
| ---: | ---: |
| `0x200004aa` | `0x470004aa` |
| `0x200004ac` | `0x470004ac` |
| `0x200004e0` | `0x470004e0` |
| `0x20000bc7` | `0x47000bc7` |

These are mapper outputs, not interchangeable address spellings. Target
`0x101` consumes the supplied DMA/bus address; it does not translate a raw
CPU `0x2000....` address on the host's behalf. The earlier target-`0x101`
read at raw CPU `0x20000580` returned 64 zero bytes and was correctly retained
as inconclusive. A future request must not use `0x200004aa`, `0x200004ac`,
`0x200004e0`, or `0x20000bc7` directly.

The core-tag register at `0xe00fdfdc` has not been sampled. Consequently this
review does not turn the non-A mapper branch into an unconditional statement
about the live secondary core. The earlier target-`0x101` response from bus
`0x470004c0/64`, which contained `0x20010000` at bus `0x470004e0` and
nonzero plausible neighboring state, is the positive empirical anchor for
this particular secondary window. It materially supports the mapping but is
not a live tag measurement or whole-body execution proof.

## P1 — The rooted mode window is the only narrow positively anchored candidate

The best bounded first candidate is:

```text
bus start  0x470004a0
length     0x44 bytes
bus end    0x470004e3 inclusive
```

Its conditional CPU interpretation is `0x200004a0..0x200004e3`. It contains
both mode halfwords and the complete root word in one response. It also
contains the previously observed nonzero neighboring fields at CPU
`0x200004c6/0x200004c8/0x200004ca`, although their runtime values are not
invariants. Acceptance as an image-1 mode sample should require, at minimum:

1. the complete exact response, with no short or transport anomaly;
2. the root word at returned offset `0x40` equal to `0x20010000`; and
3. the mode values reported as same-response volatile values, not reset or
   event-time values.

If the root word does not match, the raw bus bytes remain evidence but the
CPU-field interpretation must be rejected. A `0x47000480/0x80` window would
also contain the fields and root, but it captures more unrelated state and
crosses the decompressed/zero-fill boundary for no evidentiary benefit. A
flags-only window ending before `0x470004e0`, or two separately timed reads of
flags and root, loses the strongest same-response identity check.

This is an address-qualification result, not implementation clearance.
Exact-length native tests, immutable source/build pins, one-shot protocol
interlocks, retained raw output, and no retry after an unknown transfer phase
would still be required before any target use.

## P1 — The alternate-threshold byte still lacks a narrow positive identity test

The smallest natural candidate is:

```text
bus start  0x47000bc0
length     0x10 bytes
candidate alternate byte at returned offset 0x07
```

Every corresponding CPU byte is within the established image-1 zero-fill
allocation, so this is a bounded candidate and not guessed unallocated RAM.
It nevertheless lacks a local positive fingerprint:

- no retained live read covers this address;
- no nonzero reset invariant exists in this window;
- the live non-A core tag is unobserved; and
- a zero alternate byte is expected in reset state and is therefore not
  independently identifying.

The recovered mirror writer at VA `0x3934` makes a nonzero value plausible
after the ordinary callback runs, and it explains why the byte can change
independently of `aa`, `ac`, and root `+0x2410`. It does not close the
CPU-to-bus edge: the writer addresses CPU `0x20000bc7`, not bus
`0x47000bc7`.

A nonzero returned byte would be more informative as runtime state, but by
itself still would not prove the CPU/bus relation. Positive qualification
requires one of the following before interpreting this narrow window as the
image-1 alternate flag:

- a separately established invariant or independently traced nonzero field
  in the same narrow bus window;
- a safe, separately reviewed observation that establishes the relevant
  live secondary core's non-A tag and the applicability of this mapper; or
- another direct, address-specific live bridge for this portion of the
  `0x47000...` SRAM bank.

Reading one contiguous span from `0x470004a0` through `0x47000bc7` would be
`0x728` bytes and would place the root and alternate byte in one response.
That is not recommended as a substitute for missing evidence: it captures
about 1.8 KiB of unrelated volatile state, is not an atomic snapshot, and
still does not directly observe the live core tag. Two narrow windows are the
better acquisition design, with the second explicitly classified as
candidate-only until a local anchor is found.

## P1 — `0x4500...`, raw `0x2000...`, and AP_RTP are not valid substitutes

The tag-A candidate addresses `0x450004aa/0x450004ac/0x450004e0` and
`0x45000bc7` are not a safer fallback. The acquired main image's reset row 0
initializes CPU `0x20000000` for `0xf3c` bytes (the selected main image uses
`0xf4c`), so the same numeric CPU offsets are also populated in the main
bank. The successful `0x45000580` callback read positively identifies a
main/tag-A SRAM view at that location. A plausible value from `0x450004xx`
could therefore be genuine main state while being the wrong image-1 mode
state.

The packaged AP_RTP destinations are exactly
`0x47010000..0x470123ff` and `0x47012400..0x470124ff`. None includes
`0x470004aa`, `0x470004ac`, `0x470004e0`, or `0x47000bc7`. Those mode
candidates must not be justified by widening AP_RTP down to `0x47000000`.
Their only support is the image-1 CPU scatter allocation, the conditional
mapper, and the address-specific secondary-root observation described above.

## Required interpretation limits

- A future result is a late volatile sample, not the V6 event-time mode.
- Separate windows are sequential and not atomic.
- A matching root anchors the local bus block; it does not prove immutable
  running code, boot source, or every address in the whole `0x4700....` bank.
- A zero at bus `0x47000bc7` without a local anchor remains ambiguous.
- No value here establishes For You causality, physical panel darkness, a
  repair, or a safe control change.

## Evidence checked

| artifact | SHA-256 |
| --- | --- |
| `tcon-research/qd-image1-context-initialization.md` | `e885c17d2d1092fd82d761ed4c7b1cd1627bcfa921bfba8027b515918da39c66` |
| `tcon-research/qd-rtp-scan-invocation.md` | `87f99291d8ba6a35e97506eb898eff78c847448bd91d85b4051a19cf60b9b2d7` |
| `executing-image-identity-20261027e/dma-alias-proof.json` | `d4d89f2f1852cf72bbc9e1ad920d55aee7d861ccbd14c9cc0df726b7f2d8f347` |
| `executing-image-identity-20261027e/state-runtime-audit.json` | `0eaa69868337c3bf21b9e5681488b6419a88c1fe05c4033fe2e5e467d3ab9e9b` |
| `firmware-fingerprint-20261027d/progress.md` | `037f07da76637487ca5390e7130117261b9665dbe0943e398dcbf5f0b3031eff` |
| `tcon-research/qd-config-rtp-table-load.md` | `0da4998c58fa503ab8d934b9e250e57566908ef8a80f8d1dc7814aeedd34f29b` |
| `finite-onset-logger-20261027g/rtp-mode-selection-provenance.md` | `1a2783ebf0b93491caffcbb76bc045a30ad0a6879336202ebad13d90d130f607` |
| `finite-onset-logger-20261027g/rtp-mode-selection-provenance.py` | `302d7fc8ada14c4542fbfcfacf812cb3c00be1819ca0f4067e9c8d931c2c5547` |

The last verifier passed with identical JSON under normal Python and
`python3 -O`; it is CPU/source provenance only and is not treated as bus
alias proof.

