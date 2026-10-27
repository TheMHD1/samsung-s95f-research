# USB CDC ingress versus the AP_RTP logical reader

Recorded 2026-10-27 UTC. This is bounded offline analysis of one retained
factory profile. It made no TV, root, network, USB, UART, controller, I2C,
EEPROM, updater, or firmware call. It does not provide a command to send.

## Result

There is an exact firmware-local, one-halfword route to the AP_RTP live field:
the generic reader at image-0 linked VA `0x637c` maps logical address
`0x21000a`, count one 16-bit word, to fixed window address **`0x4701240a`**.
One of its three direct callers contains an exact one-word read branch and is
installed in a text-command table.

That is **not** a proved USB CDC command. The command parser feeding those
handlers is positively bound to controller-local UART MMIO base
`0x40152000`:

* one mode polls that MMIO directly; and
* the other consumes a 512-byte software ring whose only direct producer is
  an interrupt body reading the same MMIO block.

The recovered CDC bulk-OUT worker instead receives into the independent
`USBSerial` state/buffer. In a bounded direct-call and exact-literal census,
the CDC region has no edge to the UART line parser, its table dispatcher, or
its byte-ring producer. It also contains none of the UART MMIO/ring literals.
Computed and indirect edges are not excluded by that negative census, but no
positive CDC-to-command-parser bridge exists in retained evidence.

Accordingly, there is no source-backed, bounded **USB** read command ready to
use for `0x21000a`. The missing edge is precise: CDC endpoint-`0x01` receive
completion to the `0x40152000` line parser (or to an equivalent dispatcher)
is not recovered. No command bytes, token grammar, DTR sequence, endpoint
operation, or invocation is proposed here.

## Pinned inputs and coordinate convention

| input | SHA-256 |
| --- | --- |
| selected 5 MiB profile `F_RSM1_BN9659934B_COMMON.bin` | `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0` |
| `qd-config-rtp-table-load.md` | `0da4998c58fa503ab8d934b9e250e57566908ef8a80f8d1dc7814aeedd34f29b` |
| its reproducer | `53d684819074e69838f66900b61aa72ba81e49b6e1b3f9c4c8cd6847c72250b3` |
| corrected USB callback report | `76d4e621adc811d3f00bb59c41e89434d8cde2c15a7932af56cee0f91f9ec633` |
| USB output/receive-boundary report | `a14f5280bd15244ac702d5f1fb9131b42be74504722be3a7bdf3d81f80e5ba50` |
| image-1 RT input-provenance report | `6ca8f906ed75288816a852a57b196b9667fe2db61a2ab41e659bcbd626225dac` |

For image 0, linked VA equals stored file offset minus `0x200`. RAM and MMIO
addresses are not shifted. The packaged image remains evidence about the
selected asset, not proof that every byte equals current controller flash.

## Exact AP_RTP read arithmetic

Table row 14 at stored file `0x3ce44` is:

| field | value |
| --- | ---: |
| name | `AP_RTP` |
| first destination / length | `0x47012400` / `0x100` |
| second destination / length | `0x47010000` / `0x2400` |
| first / second logical base | `0x210000` / `0x210400` |

The generic reader at file `0x657c` compares the address high halfword to a
table row. For a low halfword below the first limit, it copies from
`first_destination + low`; it multiplies its count argument by two before
the copy. Therefore:

```text
logical 0x21000a, count 1 word
  -> low 0x000a < 0x0100
  -> 0x47012400 + 0x000a
  -> 0x4701240a, 2 bytes
```

The selected package initializes those two bytes to zero at file
`0x18380a`. That packaged default is not a runtime value. The separately
recovered image-1 local event writes `0x1001` to its own `0x2001240a`; an
image-1-to-image-0 live-window alias is still not proved, so this read would
not by itself establish which producer changed the fixed window.

The reader is not a safe arbitrary-memory primitive: its second-region and
gap bounds are incomplete. The one-word `0x21000a` arithmetic is bounded by
the first region, but that does not supply a transport.

## All three direct callers

A halfword-aligned direct-`BL` census over image 0 gives exactly:

| stored call | linked call | bounded role |
| ---: | ---: | --- |
| `0x11258` | `0x11058` | variable-count branch in the table handler labelled `bin` |
| `0x1168c` | `0x1148c` | count-one branch in the table handler labelled `param` |
| `0x2a4f8` | `0x2a2f8` | count-one type-2 entry in an 11-entry internal `TCDATA` sampler |

No raw Thumb pointer to VA `0x637c` occurs in image 0. This closes direct
callers, not computed indirect calls.

At file `0x11686..0x11690`, the count-one branch sets output to a local
halfword, sets count to one, passes its parsed address in `r0`, and calls the
generic reader. The command table at file `0x3d334` has 28-byte rows; it binds
the exact handler pointer `0x0001121d` to the exact `param` label. A sibling
row binds pointer `0x00010f0d` to `bin`, whose selected branch divides its
parsed byte count by two before the same reader call.

Those facts prove handler installation and an exact read branch. They do not
turn a label into a USB protocol. The larger handlers contain multiple
branches, and this report deliberately does not synthesize their textual
grammar or an invocation. The selected one-word basic block reads/copies and
formats output; no EEPROM/update/reset/write operation appears in that basic
block. Parser-buffer and output activity would still occur if some ingress
invoked it.

The third call is different. It walks an internal 11-entry RAM table,
performs a one-word generic read for entries of type two, caches the result,
and later participates in `TCDATA` formatting. Its only direct caller is the
periodic path at stored file `0x138f2`. This is not an address selected from
CDC RX. Retained bytes do not positively bind a table entry to `0x21000a`,
so the existence of TCDATA USB output is not evidence that it exposes the RT
field.

## Positive ingress: local UART, twice

The line parser is linked VA `0x16fc0`, stored file `0x171c0`. It accumulates
bytes, handles backspace/newline/escape and calls dispatcher VA `0x17084` on
newline. The dispatcher walks the 28-byte table rooted at linked VA
`0x3d134` (stored file `0x3d334`), compares the token, loads handler pointer
at row `+0x18`, and performs `BLX`.

Its input source is not inferred from a label:

* literal `0x200153f8` selects the input mode;
* when the mode byte is `0xfa`, VA `0x16fd0` loads literal `0x40152000` and
  calls the byte-read helper directly;
* otherwise VA `0x16fdc` calls VA `0xf484`, which pops from the 512-byte ring
  at `0x200155f8` using indices `0x20000e12` and `0x20000e14`; and
* the ring writer at VA `0x21084` has exactly one direct caller, file
  `0x16168`. That interrupt body reads status at `0x40152000+0x24`, reads the
  byte at `+0x28`, then writes the ring.

Thus polling and interrupt modes converge on the same controller-local UART
peripheral. This is a dataflow proof, not a guess based on the `bin` or
`param` strings. It also does not prove that this UART is externally wired or
host-accessible.

## CDC receive boundary and the missing bridge

The independently recovered CDC object uses data-OUT endpoint `0x01` and a
receive buffer at `USBSerial state+0x14`. The receive worker at VA `0x29afc`
(file `0x29cfc`) submits at most `0x40` bytes and completion updates its own
producer/consumer fields before re-priming. DTR rising can clear those fields
and submit receive work, so DTR is state-changing rather than a passive
prerequisite.

For the bounded mixed-code interval file `0x28000..0x2bfff` containing the
CDC data implementation:

* there is no direct `BL` to line parser `0x16fc0`, dispatcher `0x17084`, or
  UART ring writer `0x21084`;
* no exact literal `0x40152000`, `0x200155f8`, `0x20000e0e`, `0x20000e12`,
  or `0x20000e14` occurs; and
* the generic-reader call at file `0x2a4f8` is the internal TCDATA sampler
  described above, not a CDC RX consumer.

This bounded negative does not prove the whole firmware has no computed,
callback, DMA, or external bridge. It identifies exactly what is absent from
the recovered path: no received CDC byte is shown entering the UART command
buffer or causing its dispatch. The corrected line-coding callback likewise
provides only an optional baud hook initialized to zero; it is not such a
data bridge.

## Diagnostic conclusion

The source establishes a valuable target-side primitive: one halfword at
logical `0x21000a` would read fixed image-0 window `0x4701240a` without an
EEPROM/update operation in the selected read branch. It does **not** establish
a safe host route to that primitive:

1. the positive command ingress is a separate UART at `0x40152000`;
2. CDC OUT to that parser is missing;
3. current controller execution and UART wiring are unproved;
4. DTR/line-coding are host writes with local state effects; and
5. even a returned halfword would be a fixed-window observation, not proof of
   the image-1 producer, physical RT cause, panel state, or repair.

Consequently no USB device open, bind, control transfer, bulk write/read, or
controller command is technically justified by this route. The smallest
remaining source gap is a positive callback/dataflow from CDC OUT completion
to the UART parser or a distinct supported dispatcher that reaches the same
one-word branch. Without it, any USB command would be guessed.

## Reproduction

Run locally only:

```sh
python3 tcon-research/qd-usb-ap-rtp-logical-read-route-reproduce.py
python3 -O tcon-research/qd-usb-ap-rtp-logical-read-route-reproduce.py
```

The checker pins the complete asset, canonical vector, AP_RTP row and
arithmetic, all three direct reader calls, handler/table entries, UART parser
and IRQ-ring literals, CDC-region negative census, and nine stored-byte slice
hashes. Its negative census is explicitly bounded and does not claim whole-
program nonexistence.

| stored range | SHA-256 |
| --- | --- |
| reader `0x657c..0x660f` | `7ebc90f811630e1be84808d2dbac850e4c067c0643066714ef5a75b2b0f11b16` |
| variable handler `0x110f0..0x112cf` | `983fa30e28e1fc9d65f3462c83d0197c206a4974bb06cf0bbc25dfe4fb3cf781` |
| one-word handler `0x1121c..0x114e3` | `c96d66e5344391dbb1ca086bc392515f568d10bba8e87fab8f7c1af820383d09` |
| UART ring pop `0xf684..0xf6e7` | `bcb70af7e0d9a47e8f4cdb24fe75178e3acc7dea2e9ee795ecfc3c7bb35b96f4` |
| UART IRQ `0x16150..0x161af` | `36481610ccd6b4ba52a651eeee74d51136092e35d95dd9fdb53105170629274e` |
| parser/dispatch `0x171c0..0x172df` | `421faef06466558f0101d6d61002d6b00ffde43603f88088526326f9ba65782c` |
| CDC RX worker `0x29cfc..0x29da1` | `95f2b8b66c1a603d4d7b0d7868e5c387f0788086efc88be823b516408c725959` |
| TCDATA sampler `0x2a4bc..0x2a57b` | `d7f1d435c2de376b329bec1d282935f0f5d3572906bb1970e541b32f5c9255f6` |
| command-table excerpt `0x3d334..0x3d3bb` | `2b11956856f2b33086e9969b9fd0fe7a25865a37b9722114a54fa33d7e323b10` |
